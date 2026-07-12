---
name: mwld_vocab_refinement
description: "MWLD API와 웹 스크린샷 교차 검증을 통한 무결점 단어 정제 및 analysis.json 적재 워크플로우"
---

# MWLD 단어 정제 프로세스 (MWLD Vocab Refinement Workflow)

이 스킬은 영상 대본에서 추출된 단어를 Merriam-Webster Learner's Dictionary (MWLD, 현 Britannica Dictionary) 기준으로 완벽하게 정제하여 `analysis.json`에 적재하는 프로세스를 정의합니다. AI 에이전트(무중력쌤)는 항상 아래의 4단계 워크플로우를 엄격하게 준수해야 합니다.

## 1. 사전 준비 및 타겟팅 (Targeting)
- 사용자가 정제할 단어(예: "loom")와 해당 단어가 쓰인 영상 대본(Context)을 제공하면 작업을 시작합니다.
- 학생들에게 혼란을 주지 않기 위해, **반드시 영상 문맥에서 쓰인 딱 하나의 뜻(Target Sense)만을 추출 대상으로 삼습니다.** 전체 뜻을 모두 나열하지 않습니다.

## 2. API 원본 데이터 박제 (Data Fetch & Archive)
- 브라우저 스크래핑을 통한 데이터 수집은 일절 금지합니다.
- 프로젝트 루트의 `scratch/fetch_mwld_api.py` 스크립트를 실행하여 MWLD API를 호출합니다.
- 반환된 원본 JSON 데이터 전체(모든 Sense 포함)를 `processed/raw_dict/{단어}_mwld.json` 파일에 '진실의 원천(SSOT)'으로 영구 보존(박제)합니다. 이미 박제된 파일이 있다면 API를 호출하지 않고 해당 로컬 파일을 우선적으로 읽습니다.

## 3. 웹 스크린샷 교차 검증 (Visual Ground Truth)
- `browser_subagent` 도구를 사용하여 Britannica Dictionary 사이트에 접속합니다.
- 웹사이트의 렌더링 화면을 캡처하여, Target Sense가 실제 웹에서 어떻게 포맷팅(굵은 글씨, 기울임꼴 등)되어 있는지 시각적 레퍼런스를 확보합니다.

## 4. 번역 및 데이터 가공 (Translation & Formatting)
에이전트는 확보한 JSON 원본 텍스트와 스크린샷을 대조하여 아래의 원칙에 따라 데이터 구조(JSON)를 가공합니다.

- **번역의 분리**:
  - **사전 번역 (뜻, 예문 번역)**: 영상 맥락을 배제하고 정보량 등가성에 입각한 객관적 '사전식 어투'로 번역.
  - **문맥 번역 (`sentence_contextual_translation`)**: 영상 대본 번역 시에는 영상의 시각적 묘사를 100% 반영하여 '문맥 맞춤 번역' 적용.
- **스키마 룰**:
  - `explanation` (해설) 필드 삭제.
  - `patterns` 구조를 제거하고, 브리태니커 웹사이트 구조와 100% 동일한 **`example_groups` 배열**을 사용.
    - 문법 힌트가 있으면 `"grammar_hint": "often + *to*"` 형태로 넣고, 없으면 `null`로 처리.
  - 굵은 글씨 등 포맷팅은 마크다운(`**text**`나 `*text*`)으로 처리.
  - `level` (난이도): 에이전트가 단어 수준을 분석하여 자체적으로 부여 (예: C1, B2).
  - `ab_dialogue` (회화 예문): 일상 회화에서 쓰임새가 높은 고급 어휘에 한하여 창작.

## 5. 사용자 검수 및 Supabase 최종 적재 (Review & DB Push)
- **로컬 `analysis.json` 파일에 모든 단어를 누적하여 저장하지 않습니다.** (파일 비대화 방지)
- 가공이 완료된 해당 단어의 JSON 포맷을 채팅창(혹은 Artifact)에 **원문 그대로(Verbatim) 출력**하여 사용자에게 보여줍니다.
- 사용자와 함께 번역 퀄리티와 포맷을 리뷰 및 수정한 뒤, **최종 승인이 떨어지면 Supabase 클라우드 DB의 단어 테이블에 직접 Insert(적재)** 합니다.
