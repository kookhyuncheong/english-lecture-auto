import urllib.request
import urllib.parse
import re
from bs4 import BeautifulSoup

def crawl_longman_patterns(word):
    """
    롱맨 영한사전 사이트(ldoceonline.com)에서 해당 단어의 
    모든 문형 패턴(Patternbox) 또는 기본 번역 뜻(TRAN)을 크롤링하여 리스트로 반환합니다.
    """
    word = word.strip().lower()
    # 공백은 하이픈(-)으로 처리하여 URL 생성
    url_word = urllib.parse.quote(word.replace(" ", "-"))
    url = f"https://www.ldoceonline.com/dictionary/english-korean/{url_word}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            html = response.read()
            
        soup = BeautifulSoup(html, 'html.parser')
        patterns = []
        
        # 1. <span class="Patternbox"> 또는 <span class="inline Patternbox"> 찾기 (구문 패턴 영역)
        pattern_boxes = soup.find_all(class_='Patternbox')
        for box in pattern_boxes:
            pattern_el = box.find(class_='PATTERN')
            if not pattern_el:
                continue
            pattern_text = pattern_el.get_text().strip()
            
            translation_el = box.find(class_='Translation')
            if not translation_el:
                continue
            translation_text = translation_el.get_text().strip()
            
            # 불필요한 줄바꿈 및 다중 공백 제거
            translation_text = re.sub(r'\s+', ' ', translation_text)
            
            # 패턴 및 번역 정리
            patterns.append({
                "pattern": pattern_text,
                "meaning": translation_text
            })
            
        # 2. 패턴 상자가 하나도 없으면 (일반 단어일 경우) 일반 번역 뜻(TRAN) 긁어오기
        if not patterns:
            # 롱맨 사전에서 일반 번역 뜻을 포함하는 class인 'TRAN' 또는 'BOXTRAN' 추적
            trans = soup.find_all(class_='TRAN')
            meanings = []
            for t in trans:
                text = t.get_text().strip()
                # 자잘한 특수문자나 알파벳 제외하고 실질적인 한글 단어 위주로 필터링
                text = re.sub(r'\s+', ' ', text)
                if text and len(text) > 1 and text not in meanings:
                    meanings.append(text)
            
            if meanings:
                # 콤마로 연결하여 하나의 기본 패턴 형태로 가공
                patterns.append({
                    "pattern": word,
                    "meaning": ", ".join(meanings[:3])  # 너무 많으면 지저분하므로 최대 3개까지만
                })
                
        # 크롤링 결과 로깅
        if patterns:
            print(f"[Crawl Success] '{word}': {len(patterns)}개의 패턴/뜻 발견")
        else:
            print(f"[Crawl Empty] '{word}': 사전 데이터를 찾을 수 없음")
            
        return patterns

    except Exception as e:
        print(f"[Crawl Error] '{word}' 크롤링 중 에러 발생: {e}")
        return []

# 로컬 테스트용
if __name__ == "__main__":
    # 대표적인 패턴 단어 테스트
    print(crawl_longman_patterns("aspire"))
    print("="*40)
    # 일반 단어 테스트
    print(crawl_longman_patterns("professional"))
