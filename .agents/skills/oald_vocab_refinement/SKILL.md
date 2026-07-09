---
name: oald_vocab_refinement
description: Oxford Advanced Learner's Dictionary (OALD)를 기반으로 영어 단어를 정밀 분석하고 Supabase DB 및 로컬 파일에 적재하는 프로세스를 정의합니다.
---

# OALD 단어 정제 및 데이터베이스 적재 워크플로우

이 스킬은 AI 영어 강의 튜터 프로젝트에서 새로운 단어 카드를 제작하고 데이터베이스에 동기화할 때 에이전트가 반드시 수행해야 하는 행동 절차를 규정합니다.

## 1. 사전 상태 및 로그인 검증 단계
1. **OALD 접속**: 브라우저 로봇(`browser_subagent`)을 띄워 OALD 정의 페이지(`https://www.oxfordlearnersdictionaries.com/definition/english/<target_word>`)에 접속합니다.
2. **로그인 상태 확인**: 화면 우측 상단이나 헤더 영역에 로그인 완료 상태(로그아웃 버튼 등)인지 또는 로그인 요청 상태(Sign in 버튼 노출)인지 확인합니다.
3. **사용자 로그인 협업**: 
   - 만약 로그인이 되어 있지 않다면, 브라우저 주소를 로그인 페이지(`https://www.oxfordlearnersdictionaries.com/account/login`)로 이동시킵니다.
   - 사용자에게 **"국현아, OALD 로그인이 안 되어 있으니 크롬 창에서 로그인 먼저 진행해 줘!"**라고 알린 뒤, 사용자가 로그인을 완료할 때까지 실행을 대기합니다.

## 2. 어휘 분석 및 시안 작성 단계
1. **콘텐츠 분석**: OALD 사전에서 단어의 뜻, CEFR 난이도 레벨(C1/C2 우선), 대표 영영 정의, 예문 및 문법적 패턴(Patterns)을 추출합니다.
2. **비주얼 맥락 대조**: 반드시 로컬 비디오 파일(`static/video.mp4`)을 직접 재생하여 화면에 나오는 동작, 사물, 화자의 표정을 실시간 대조하여 문맥에 어울리는 최적의 한국어 번역어를 채택합니다.
3. **가공 계획서 발행**: 아래 규격에 맞게 가공 계획서(`implementation_plan.md`)를 발행하여 사용자의 승인을 기다립니다.

## 3. 데이터 동기화 및 적재 단계
1. **로컬 파일 반영**: 사용자의 승인(`Approve` / `Proceed`)을 득한 후, 로컬 `processed/01_motivation/analysis.json` 파일의 `global_vocab_list`에 적재합니다.
2. **Supabase 동기화**: `migrate_to_supabase.py` 스크립트를 작동시켜 Supabase 클라우드 데이터베이스에 실시간 적재합니다.
3. **배포 및 검증**: 깃허브에 코드를 푸시하여 Vercel 실시간 배포가 끝난 뒤, 브라우저 로봇으로 실제 사이트에서 카드 렌더링이 잘 되는지 확인하고 최종 완료 보고합니다.
