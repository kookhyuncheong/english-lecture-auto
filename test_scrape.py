import urllib.request
import re

url = "https://www.ldoceonline.com/dictionary/english-korean/aspire"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

req = urllib.request.Request(url, headers=headers)
try:
    print(f"변장 헤더를 사용하여 '{url}' 접속을 시도하는 중...")
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
        print(f"다운로드 성공! 페이지 크기: {len(html)} 글자")
        
        # 1. '열망하다'라는 한글 단어가 페이지 소스 내에 있는지 찾기
        print("\n[한글 번역 매칭 검사]")
        korean_matches = re.findall(r'[^<>]*열망하다[^<>]*', html)
        if korean_matches:
            for i, m in enumerate(korean_matches[:5], 1):
                print(f" {i}. {m.strip()}")
        else:
            print(" '열망하다'를 찾지 못했습니다.")

        # 2. 'aspire'가 포함된 HTML 태그 내부 텍스트 찾기
        print("\n['aspire' 구문/패턴 매칭 검사]")
        # 괄호 안의 글자를 제외하고 텍스트만 매칭
        pattern_matches = re.findall(r'>([^<]*aspire[^<]*)<', html)
        valid_patterns = []
        for p in pattern_matches:
            clean_p = p.strip()
            if clean_p and len(clean_p) > 2 and clean_p not in valid_patterns:
                valid_patterns.append(clean_p)
                
        if valid_patterns:
            for i, p in enumerate(valid_patterns[:10], 1):
                print(f" {i}. {p}")
        else:
            print(" 'aspire' 구문을 찾지 못했습니다.")

except Exception as e:
    print("접속 에러 발생:", e)
