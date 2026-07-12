import json
import os
import wave
import sys
from google import genai
from google.genai import types

def load_env():
    env_path = ".env"
    api_key = None
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip('"').strip("'")
                    break
    return api_key

def save_wave(filename, pcm, channels=1, rate=24000, sample_width=2):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)

def determine_voices(client, situation, dialogue_a, dialogue_b):
    prompt = f"""
Given the following situation and dialogue, determine the most natural gender (male/female) and a brief emotional style/tone for Speaker A and Speaker B.
Situation: {situation}
Speaker A: {dialogue_a}
Speaker B: {dialogue_b}

Respond strictly in JSON format like this:
{{
  "speaker_a": {{
    "gender": "male or female",
    "style": "Brief style description (e.g. enthusiastic, concerned, professional)"
  }},
  "speaker_b": {{
    "gender": "male or female",
    "style": "Brief style description"
  }}
}}
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Error determining voices: {e}")
        # Default fallback
        return {
            "speaker_a": {"gender": "male", "style": "neutral"},
            "speaker_b": {"gender": "female", "style": "neutral"}
        }

def generate_audio(client, text, gender, style, output_path):
    # Gemini 3.1 Flash TTS available voices:
    # Male options: "Charon", "Zephyr"
    # Female options: "Kore", "Aoede"
    voice_name = "Charon" if gender == "male" else "Aoede"
    
    prompt = f"[{style}] {text}"
    print(f"Generating TTS for: '{text}' (Voice: {voice_name}, Style: {style})")
    
    config = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=voice_name
                )
            )
        ),
    )

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-tts-preview",
            contents=prompt,
            config=config
        )
        audio_data = response.candidates[0].content.parts[0].inline_data.data
        save_wave(output_path, audio_data)
        print(f"Saved audio to {output_path}")
        return True
    except Exception as e:
        print(f"Error generating audio: {e}")
        return False

def main():
    api_key = load_env()
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env")
        sys.exit(1)
        
    client = genai.Client(api_key=api_key)
    
    data_dir = "processed/01_motivation"
    audio_dir = os.path.join(data_dir, "audio")
    os.makedirs(audio_dir, exist_ok=True)
    
    analysis_path = os.path.join(data_dir, "analysis.json")
    with open(analysis_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    for vocab in data.get("global_vocab_list", []):
        if "ab_dialogue" in vocab:
            ab = vocab["ab_dialogue"]
            
            # Skip if already generated (unless forcing regenerate)
            if "audio_path_a" in ab and "audio_path_b" in ab:
                pass # For now, let's regenerate to test the new style
                
            situation = ab.get("situation", "")
            dialogue_a = ab.get("dialogue_a", "")
            dialogue_b = ab.get("dialogue_b", "")
            
            if not dialogue_a or not dialogue_b:
                continue
                
            print(f"\nProcessing dialogue for vocab: {vocab['word']}")
            
            # 1. Determine voices
            voices = determine_voices(client, situation, dialogue_a, dialogue_b)
            print(f"Determined voices: {voices}")
            
            # 2. Generate Audio A
            path_a = f"{audio_dir}/{vocab['id']}_dialogue_a.wav"
            success_a = generate_audio(client, dialogue_a, voices["speaker_a"]["gender"], voices["speaker_a"]["style"], path_a)
            if success_a:
                ab["audio_path_a"] = f"{path_a}"
                
            # 3. Generate Audio B
            path_b = f"{audio_dir}/{vocab['id']}_dialogue_b.wav"
            success_b = generate_audio(client, dialogue_b, voices["speaker_b"]["gender"], voices["speaker_b"]["style"], path_b)
            if success_b:
                ab["audio_path_b"] = f"{path_b}"
                
    # Save updated json
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print("\nTTS Generation Complete! Updated analysis.json")

if __name__ == "__main__":
    main()
