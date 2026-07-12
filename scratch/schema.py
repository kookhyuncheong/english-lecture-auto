from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Example(BaseModel):
    eng: str
    kor: str
    audio_path: Optional[str] = None

class ExampleGroup(BaseModel):
    grammar_hint: str
    examples: List[Example]

class AbDialogue(BaseModel):
    situation: Optional[str] = None
    dialogue_a: str
    dialogue_b: str
    translation_a: str
    translation_b: str
    audio_path_a: Optional[str] = None
    audio_path_b: Optional[str] = None

class Vocabulary(BaseModel):
    id: str
    word: str
    target_phrase: Optional[str] = None
    base_word: Optional[str] = None
    level: Optional[str] = None
    meaning: str
    english_definition: Optional[str] = None
    english_definition_translation: Optional[str] = None
    sentence_index: Optional[int] = None
    sentence_text: Optional[str] = None
    
    ab_dialogue: Optional[AbDialogue] = None
    example_groups: List[ExampleGroup] = Field(default_factory=list)
    sentence_contextual_translation: Optional[str] = None

class LexiconInstance(BaseModel):
    lexicon_id: str
    target_phrase: Optional[str] = None

class Sentence(BaseModel):
    id: str
    video_id: str
    start_time: str
    end_time: str
    english_text: str
    korean_text: str
    vocab_list: Optional[List[Any]] = Field(default_factory=list)
    lexicon_instances: List[LexiconInstance] = Field(default_factory=list)
    visual_description: Optional[str] = None
    lecture_script: Optional[str] = None

class AnalysisData(BaseModel):
    title: str
    sentences: List[Sentence]
    global_vocab_list: List[Vocabulary]
