document.addEventListener('DOMContentLoaded', () => {
    // Supabase 클라이언트 초기화
    const SUPABASE_URL = 'https://qlztpnzhfjxljdrmzvis.supabase.co';
    const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFsenRwbnpoZmp4bGpkcm16dmlzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM2MDkyMTQsImV4cCI6MjA5OTE4NTIxNH0.vaH9bLC62CjDipcc2szv39sUDjEH-tCusK5DVKWilag';
    const supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

    // ==========================================================================
    // DOM 요소 선택
    // ==========================================================================
    const vid = document.getElementById('vid');
    const stage = document.getElementById('stage');
    const pfab = document.getElementById('pfab');
    const pfabBtn = document.getElementById('pfabBtn');
    const pfabCur = document.getElementById('pfabCur');
    const pmenu = document.getElementById('pmenu');
    const num = document.getElementById('num');
    const sen = document.getElementById('sen');
    const sko = document.getElementById('sko');
    const rule = document.getElementById('rule');
    const chunk = document.getElementById('chunk');
    const note = document.getElementById('note');
    const noteContent = document.getElementById('noteContent');
    const vocabTab = document.getElementById('vocabTab');
    const noteClose = document.getElementById('noteClose');
    const listenBtn = document.getElementById('listen');
    const micBtn = document.getElementById('mic');
    const sresult = document.getElementById('sresult');

    // ==========================================================================
    // 상태 변수 정의
    // ==========================================================================
    let lectureData = null;       // 로컬 JSON 데이터 저장
    let currentIndex = 0;         // 현재 재생 중인 문장의 인덱스
    let STEP = 2;                 // 기본 단계: 2 (강의듣기)
    let ALLSENTS = [];            // 문장들의 시간 정보와 ID를 담을 배열
    let ALLSIDS = [];             // 문장들의 ID 리스트
    let lecturePaused = false;
    let recording = false;
    let mediaRecorder = null;
    let audioChunks = [];
    const PASS_SCORE = 80;        // 섀도잉 통과 커트라인

    // 난이도별/어휘 인덱스별 컬러 스티커 팔레트 (CSS 변수 매치)
    const PALETTE = ['--w1', '--w2', '--w3', '--w4', '--w5'];

    function getAccentColor(idx) {
        return `var(${PALETTE[idx % PALETTE.length]})`;
    }

    function esc(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    // ==========================================================================
    // 1. 초기 데이터 가져오기 (JSON 로드)
    // ==========================================================================
    async function init() {
        try {
            // 1. Supabase에서 문장 목록 가져오기
            const { data: sentences, error: sError } = await supabaseClient
                .from('sentence')
                .select('*')
                .order('id', { ascending: true });
            
            if (sError) throw sError;

            // 2. Supabase에서 정규화된 사전 데이터 가져오기
            const { data: lexiconData, error: lError } = await supabaseClient
                .from('lexicon')
                .select('*');
            if (lError) throw lError;

            const { data: examplesData, error: eError } = await supabaseClient
                .from('examples')
                .select('*');
            if (eError) throw eError;

            const { data: dialoguesData, error: dError } = await supabaseClient
                .from('dialogues')
                .select('*');
            if (dError) throw dError;

            // 3. 기존 코드와의 호환성을 위해 조립 (lexicon_instances 지원)
            const globalVocabs = lexiconData.map(lex => {
                const vocab = {
                    id: lex.id,
                    word: lex.lemma,
                    meaning: lex.meaning,
                    level: lex.level,
                    english_definition: lex.english_definition,
                    english_definition_translation: lex.english_definition_translation,
                    example_groups: [],
                    ab_dialogue: {}
                };
                
                // Add examples
                const relatedExamples = examplesData.filter(e => e.lexicon_id === lex.id);
                if (relatedExamples.length > 0) {
                    // Group by grammar_hint
                    const groups = {};
                    relatedExamples.forEach(ex => {
                        const hint = ex.grammar_hint || "";
                        if (!groups[hint]) groups[hint] = [];
                        groups[hint].push({
                            eng: ex.english_text,
                            kor: ex.korean_text,
                            tts_url: ex.tts_url
                        });
                    });
                    
                    vocab.example_groups = Object.keys(groups).map(hint => ({
                        grammar_hint: hint,
                        examples: groups[hint]
                    }));
                }

                // Add dialogues
                const dialogue = dialoguesData.find(d => d.lexicon_id === lex.id);
                if (dialogue) {
                    vocab.ab_dialogue = {
                        dialogue_a: dialogue.speaker_a_eng,
                        translation_a: dialogue.speaker_a_kor,
                        dialogue_b: dialogue.speaker_b_eng,
                        translation_b: dialogue.speaker_b_kor
                    };
                }

                return vocab;
            });

            lectureData = {
                title: "동기 부여의 두 가지 유형",
                sentences: sentences || [],
                global_vocab_list: globalVocabs || []
            };
            
            // global_vocab_list에서 vocab_8 (an end in itself)을 찾아서 OALD 스펙으로 보강
            if (lectureData && lectureData.global_vocab_list) {
                const targetVocab = lectureData.global_vocab_list.find(v => v.id === 'vocab_8' || v.word === 'an end in itself');
                if (targetVocab) {
                    targetVocab.meaning = "그 자체로 목적이 되는 것 (수단이 아닌)";
                    targetVocab.english_definition = "a thing that is itself important and not just a part of something more important";
                    targetVocab.english_definition_translation = "그 자체로 중요하며, 단지 더 중요한 다른 것을 위한 수단이 아닌 것";
                    targetVocab.explanation = "이 표현에서 'end'는 '끝'이 아니라 '목적(purpose)'이라는 뜻으로 쓰였습니다. 어떠한 행동을 무언가를 얻기 위한 '수단(means)'으로 하는 것이 아니라, 그 행위 자체가 즐겁고 중요해서 하는 상황을 설명할 때 원어민들이 자주 쓰는 고급 구문입니다.";
                    targetVocab.oald_examples = [
                        {
                            "eng": "For her, shopping had become an end in itself.",
                            "kor": "그녀에게 쇼핑은 그 자체로 목적이 되었다."
                        },
                        {
                            "eng": "For him, travelling had become an end in itself rather than a means of seeing new places.",
                            "kor": "그에게 여행은 새로운 곳을 보기 위한 수단이라기보다는 그 자체로 목적이 되었다."
                        }
                    ];
                }

                // 문장 목록 추출 및 시작/종료 시간 세컨드로 변환
                ALLSENTS = lectureData.sentences.map(s => {
                    s.startSeconds = parseTimestampToSeconds(s.start_time);
                    s.endSeconds = parseTimestampToSeconds(s.end_time);
                    return {
                        sid: s.id,
                        s: s.startSeconds,
                        e: s.endSeconds
                    };
                });
                ALLSIDS = ALLSENTS.map(s => s.sid);

                // URL 개발용 파라미터 파싱 (?sid=01-01&step=2&open_vocab=vocab_1&paused=true)
                const params = new URLSearchParams(window.location.search);
                const devSid = params.get('sid');
                const devStep = params.get('step');
                const devOpenVocab = params.get('open_vocab');
                const devPaused = params.get('paused');

                if (devStep) {
                    STEP = parseInt(devStep, 10);
                }
                
                let startIdx = 0;
                if (devSid) {
                    const found = ALLSENTS.findIndex(s => s.sid === devSid);
                    if (found >= 0) startIdx = found;
                }

                if (devPaused === 'true') {
                    lecturePaused = true;
                }

                currentIndex = startIdx;
                setStep(STEP);

                if (devSid || devStep || devOpenVocab) {
                    hideSlide();
                    loadSentence(currentIndex, true);
                    if (devPaused === 'true') {
                        setTimeout(() => {
                            vid.pause();
                        }, 100);
                    }
                    if (devOpenVocab) {
                        setTimeout(() => {
                            const targetCard = document.getElementById(`wnote-${devOpenVocab}`);
                            if (targetCard) {
                                document.querySelectorAll('.wnote').forEach(c => c.classList.add('hidden'));
                                targetCard.classList.remove('hidden');
                            }
                        }, 200);
                    }
                } else {
                    showTitleSlide(true);
                }
            }
        } catch (error) {
            console.error("초기화 중 오류 발생: ", error);
            setSR("오류: analysis.json 데이터를 로드하지 못했습니다.");
        }
    }

    // 시간 포맷(HH:MM:SS,mmm)을 초(Seconds)로 변환하는 함수
    function parseTimestampToSeconds(ts) {
        const cleanTs = ts.replace('.', ',');
        const parts = cleanTs.split(':');
        const hours = parseInt(parts[0], 10);
        const minutes = parseInt(parts[1], 10);
        const secondsParts = parts[2].split(',');
        const seconds = parseInt(secondsParts[0], 10);
        const milliseconds = parseInt(secondsParts[1] || '0', 10);
        return (hours * 3600) + (minutes * 60) + seconds + (milliseconds / 1000);
    }

    // ==========================================================================
    // 2. 제목 표지 슬라이드 오버레이 제어
    // ==========================================================================
    function showTitleSlide(isCover) {
        let el = document.getElementById('slide');
        if (!el) {
            el = document.createElement('div');
            el.id = 'slide';
            stage.appendChild(el);
        }
        el.className = 'on';

        const title = lectureData ? lectureData.title : '동기 부여의 두 가지 유형';
        
        let footer = '';
        if (isCover) {
            footer = `<div class="startwrap"><button class="startbtn" id="startBtn">▶ 시작</button></div>`;
        } else {
            footer = `<div class="eq" style="display:flex;align-items:flex-end;height:22px;">
                        <span style="background:#1f5fa5;"></span>
                        <span style="background:#1f5fa5;"></span>
                        <span style="background:#1f5fa5;"></span>
                        <span style="background:#1f5fa5;"></span>
                      </div>`;
        }

        el.innerHTML = `
            <div class="wm">EP 01</div>
            <div class="eyebrow">EPISODE 01</div>
            <h1>${esc(title)}</h1>
            <div class="sko">AI 영어 강의 튜터에 오신 것을 환영합니다.</div>
            <div class="srule"></div>
            ${footer}
        `;

        if (isCover) {
            const startBtn = document.getElementById('startBtn');
            if (startBtn) {
                startBtn.addEventListener('click', () => {
                    hideSlide();
                    setStep(1); // 영상보기부터 시작
                });
            }
        }
    }

    function hideSlide() {
        const el = document.getElementById('slide');
        if (el) el.className = '';
    }

    // ==========================================================================
    // 3. 자막 및 단어 렌더링 코어 로직
    // ==========================================================================
    function loadSentence(index, seek = true) {
        currentIndex = index;
        const sentence = lectureData.sentences[index];
        if (!sentence) return;

        // UI 기본 청소
        const subCard = document.getElementById('sub-card');
        if (subCard) subCard.style.opacity = '1'; // 자막 카드 보이기

        note.classList.remove('on');
        if (vocabTab) vocabTab.classList.add('hidden');
        if (noteContent) noteContent.innerHTML = '';
        else note.innerHTML = '';
        chunk.innerHTML = '';
        rule.style.display = 'none';

        // 1. 번호 업데이트
        num.textContent = sentence.index.toString().padStart(2, '0');

        // 2. 한글 자막 업데이트
        sko.textContent = sentence.korean_text || '';

        // 3. 청크(어구) 구조 분석 렌더링 (OALD 노출과 중복되므로 깔끔한 UI를 위해 제거)
        // rule.style.display = 'none';
        // chunk.innerHTML = '';

        // 4. 영어 자막/빈칸 렌더링
        renderEN(sentence);

        // 5. 단어 메모 카드 생성 및 렌더링
        renderNotes(sentence);

        // 6. 재생 시크 이동
        if (seek) {
            // 브라우저의 부동소수점 오차(예: 12.6초가 12.5999초로 지정됨)로 인해 
            // timeupdate 시 이전 자막으로 매칭(무한 초기화)되는 현상을 방지하기 위해 0.05초 추가
            vid.currentTime = sentence.startSeconds + 0.05;
        }

        setSR(STEP === 4 ? '따라 말하면 채점돼요 🎤' : '');
    }

    function renderEN(sentence) {
        if (STEP === 3) {
            renderDictation(sentence);
            return;
        }

        const en = sentence.english_text;
        const instances = sentence.lexicon_instances || [];
        
        if (instances.length === 0) {
            sen.innerHTML = esc(en);
            return;
        }

        let ranges = [];
        instances.forEach((inst, idx) => {
            const t_phrase = inst.target_phrase;
            if (!t_phrase) return;
            const textLower = en.toLowerCase();
            const phraseLower = t_phrase.toLowerCase().trim();
            const startIdx = textLower.indexOf(phraseLower);
            if (startIdx >= 0) {
                ranges.push({
                    s: startIdx,
                    e: startIdx + phraseLower.length,
                    vocabId: inst.lexicon_id,
                    colorIdx: idx
                });
            }
        });

        if (ranges.length === 0) {
            sen.innerHTML = esc(en);
            return;
        }

        ranges.sort((a, b) => a.s - b.s);

        let out = '';
        let last = 0;
        ranges.forEach(r => {
            if (r.s < last) return; // 오버랩 방지
            out += esc(en.slice(last, r.s));
            out += `<span class="hl" data-vocab-id="${r.vocabId}" style="color: ${getAccentColor(r.colorIdx)};">${esc(en.slice(r.s, r.e))}</span>`;
            last = r.e;
        });
        out += esc(en.slice(last));
        sen.innerHTML = out;

        // 클릭 이벤트 등록 -> 자막 클릭 시 해당하는 wnote 카드만 노출
        sen.querySelectorAll('.hl').forEach(hl => {
            hl.addEventListener('click', (e) => {
                e.stopPropagation(); // 비디오 정지 방지
                if (STEP !== 2) return;
                const vocabId = hl.getAttribute('data-vocab-id');
                const targetCards = document.querySelectorAll('.wnote');
                const matchedCard = document.getElementById(`wnote-${vocabId}`);
                
                // 단어장 열기
                note.classList.add('on');
                
                if (matchedCard) {
                    targetCards.forEach(c => c.classList.add('hidden'));
                    matchedCard.classList.remove('hidden');
                }
            });
        });
    }

    // 단어장 서랍 토글 이벤트 등록
    if (vocabTab && noteClose) {
        vocabTab.addEventListener('click', (e) => {
            e.stopPropagation();
            note.classList.add('on');
            vocabTab.classList.add('hidden');
        });
        noteClose.addEventListener('click', (e) => {
            e.stopPropagation();
            note.classList.remove('on');
            vocabTab.classList.remove('hidden');
        });
    }

    // ==========================================================================
    // 4. 받아쓰기 (Step 5: Dictation) 전용 렌더러
    // ==========================================================================
    function renderDictation(sentence) {
        const en = sentence.english_text;
        const instances = sentence.lexicon_instances || [];

        if (instances.length === 0) {
            sen.innerHTML = esc(en);
            return;
        }

        let ranges = [];
        instances.forEach(inst => {
            const t_phrase = inst.target_phrase;
            if (!t_phrase) return;
            const textLower = en.toLowerCase();
            const phraseLower = t_phrase.toLowerCase().trim();
            const startIdx = textLower.indexOf(phraseLower);
            if (startIdx >= 0) {
                ranges.push({
                    s: startIdx,
                    e: startIdx + phraseLower.length,
                    word: en.slice(startIdx, startIdx + phraseLower.length)
                });
            }
        });

        if (ranges.length === 0) {
            sen.innerHTML = esc(en);
            return;
        }

        ranges.sort((a, b) => a.s - b.s);

        let out = '';
        let last = 0;
        ranges.forEach(r => {
            if (r.s < last) return;
            out += `<span class="ctx">${esc(en.slice(last, r.s))}</span>`;
            out += `<input class="blank" data-ans="${esc(r.word)}" autocomplete="off" spellcheck="false">`;
            last = r.e;
        });
        out += `<span class="ctx">${esc(en.slice(last))}</span>`;
        sen.innerHTML = out;

        const inputs = Array.from(sen.querySelectorAll('.blank'));

        function norm(x) {
            return x.trim().toLowerCase().replace(/[^a-z0-9' ]/g, '').replace(/\s+/g, ' ');
        }

        inputs.forEach(inp => {
            // 정답 글자 길이에 맞춰 인풋박스 가로폭 자동 맞춤 계산
            const sz = document.createElement('span');
            sz.textContent = inp.getAttribute('data-ans');
            sz.style.cssText = 'position:absolute;visibility:hidden;white-space:pre;font-family:"Limelight",Georgia,serif;font-size:1.95vw;';
            document.body.appendChild(sz);
            inp.style.width = (sz.offsetWidth + 12) + 'px';
            document.body.removeChild(sz);

            inp.addEventListener('keydown', playTickSound);
            
            inp.addEventListener('input', function() {
                const userVal = norm(this.value);
                const answerVal = norm(this.getAttribute('data-ans'));
                this.classList.remove('done', 'wrong');

                if (userVal === answerVal) {
                    this.classList.add('done');
                    this.value = this.getAttribute('data-ans'); // 원래 대소문자 정답으로 예쁘게 채워넣어줌
                    const currentIdx = inputs.indexOf(this);
                    if (inputs[currentIdx + 1]) {
                        inputs[currentIdx + 1].focus();
                    }

                    // 모든 빈칸 다 채우면 자동 다음 문장으로!
                    if (inputs.every(x => x.classList.contains('done'))) {
                        setSR('🎉 완벽하게 채웠어! 다음 문장으로 이동...');
                        setTimeout(() => {
                            if (STEP === 3) {
                                go(1);
                            }
                        }, 1200);
                    }
                } else if (userVal.length > 0 && userVal.length >= answerVal.length) {
                    this.classList.add('wrong');
                }
            });
        });

        if (inputs[0]) inputs[0].focus();
        playClipOnce(sentence);
    }

    // 타자 또각 소리 효과 (Web Audio API 사용으로 리소스 다운로드 불필요)
    function playTickSound() {
        try {
            window._actx = window._actx || new (window.AudioContext || window.webkitAudioContext)();
            const a = window._actx;
            const o = a.createOscillator();
            const g = a.createGain();
            const t = a.currentTime;
            o.type = 'square';
            o.frequency.value = 580;
            g.gain.setValueAtTime(0.05, t);
            g.gain.exponentialRampToValueAtTime(0.0001, t + 0.03);
            o.connect(g);
            g.connect(a.destination);
            o.start(t);
            o.stop(t + 0.04);
        } catch(e) {}
    }

    // ==========================================================================
    // 5. 우하단 단어 메모지노트 렌더링
    // ==========================================================================
    function renderNotes(sentence) {
        if (STEP !== 2) {
            note.classList.remove('on');
            if (vocabTab) vocabTab.classList.add('hidden');
            if (noteContent) noteContent.innerHTML = '';
            else note.innerHTML = '';
            return;
        }

        const instances = sentence.lexicon_instances || [];
        const matchedVocabs = (lectureData.global_vocab_list || []).filter(v => instances.some(inst => inst.lexicon_id === v.id));
        if (matchedVocabs.length === 0) {
            note.classList.remove('on');
            if (vocabTab) vocabTab.classList.add('hidden');
            if (noteContent) noteContent.innerHTML = '';
            else note.innerHTML = '';
            return;
        }

        // 매칭된 단어가 있으면 스티커 표시
        if (vocabTab) vocabTab.classList.remove('hidden');

        let html = [];
        matchedVocabs.forEach((v, idx) => {
            const accent = getAccentColor(idx);
            
            // OALD 영영정의 박스
            let defHtml = '';
            if (v.english_definition) {
                defHtml = `
                    <div class="def">
                        ${esc(v.english_definition)}
                        ${v.english_definition_translation ? `<div class="defko">${esc(v.english_definition_translation)}</div>` : ''}
                    </div>
                `;
            }
            
            // 영상 원문 매칭 문장 (왼쪽 자막 카드와 중복되므로 제거)
            let sentenceHtml = '';

            // 마크다운 형태의 이탤릭체(*text*)를 HTML <i> 태그로 변환하는 유틸리티
            const parseItalic = (text) => {
                if (!text) return '';
                return text.replace(/\*(.*?)\*/g, '<i style="color:var(--w1); font-weight:600;">$1</i>');
            };

            // 브리태니커 스타일 예문 그룹 (grammar_hint 지원)
            let examplesHtml = '';
            if (v.example_groups && v.example_groups.length > 0) {
                examplesHtml = `
                    <div style="margin-top: 10px; border-top: 1px dashed var(--line); padding-top: 8px;">
                        ${v.example_groups.map(group => {
                            const grammarHint = group.grammar_hint ? `
                                <div class="grammar-hint" style="color: ${accent}; font-style: italic; font-weight: 700; margin-bottom: 6px; font-size: 0.95em;">
                                    ${parseItalic(esc(group.grammar_hint))}
                                </div>
                            ` : '';
                            
                            const exList = group.examples ? group.examples.map(ex => `
                                <div class="turn" style="margin-top: 5px; padding-left: 10px; border-left: 2px solid ${accent};">
                                    <span class="ex-en">${parseItalic(esc(ex.eng))}</span><br>
                                    <span class="ex-ko">${esc(ex.kor)}</span>
                                </div>
                            `).join('') : '';

                            return `
                                <div class="example-group" style="margin-top: 12px;">
                                    ${grammarHint}
                                    ${exList}
                                </div>
                            `;
                        }).join('')}
                    </div>
                `;
            }

            // 카카오톡/iMessage 말풍선 스타일 A/B 대화문
            let convHtml = '';
            if (v.ab_dialogue && v.ab_dialogue.dialogue_a) {
                const d = v.ab_dialogue;
                convHtml = `
                    <div class="conv" style="margin-top: 12px; border-top: 1px dashed var(--line); padding-top: 12px;">
                        <div class="convhead" style="color: ${accent}; font-weight: 600; margin-bottom: 10px; display:flex; justify-content:space-between; align-items:center;">
                            <span>💬 Dialogue Practice</span>
                            ${(d.audio_path_a && d.audio_path_b) ? `<button class="dplay" data-audio-a="${esc(d.audio_path_a)}" data-audio-b="${esc(d.audio_path_b)}" style="background: ${accent}; color: white; border:none; padding: 4px 10px; border-radius: 12px; font-size: 0.85em; cursor:pointer; font-weight:600;">▶ 듣기</button>` : ''}
                        </div>
                        <div class="dialogue-container" style="display:flex; flex-direction:column; gap:10px;">
                            <div class="dialogue-bubble bubble-a" style="align-self: flex-start; background: #ffffff; border: 1px solid var(--line); padding: 10px 14px; border-radius: 18px; border-bottom-left-radius: 4px; max-width: 90%; box-shadow: 0 2px 5px rgba(0,0,0,0.03);">
                                <div style="font-size:0.75em; color:var(--ink3); margin-bottom:4px; font-weight:600;">A</div>
                                <div class="en" style="color:var(--ink);">${esc(d.dialogue_a)}</div>
                                <div class="ko" style="font-size:0.85em; color:var(--ink2); margin-top:4px;">${esc(d.translation_a)}</div>
                            </div>
                            <div class="dialogue-bubble bubble-b" style="align-self: flex-end; background: ${accent}; color: white; padding: 10px 14px; border-radius: 18px; border-bottom-right-radius: 4px; max-width: 90%; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                                <div style="font-size:0.75em; opacity: 0.8; margin-bottom:4px; font-weight:600;">B</div>
                                <div class="en" style="color:white;">${esc(d.dialogue_b)}</div>
                                <div class="ko" style="font-size:0.85em; opacity:0.9; margin-top:4px;">${esc(d.translation_b)}</div>
                            </div>
                        </div>
                    </div>
                `;
            }

            html.push(`
                <div class="wnote hidden" id="wnote-${v.id}" data-ci="${idx}" style="border-top-color: ${accent}; --sticker: ${accent};">
                    <div class="hwline">
                        <div class="hw">${esc(v.base_word || v.word)}</div>
                    </div>
                    <div class="gloss">${esc(v.meaning)}</div>
                    ${defHtml}
                    ${examplesHtml}
                    ${convHtml}
                </div>
            `);
        });

        if (noteContent) {
            noteContent.innerHTML = html.join('');
        } else {
            note.innerHTML = html.join('');
        }
        
        // 자동으로 열리지 않고, 스크린샷과 시연을 위해 탭만 활성화되도록 변경
        // note.classList.add('on');

        // 첫 번째 카드는 기본으로 노출되도록 숨김 해제
        const targetContainer = noteContent || note;
        const firstCard = targetContainer.querySelector('.wnote');
        if (firstCard) {
            firstCard.classList.remove('hidden');
        }

        // 회화 듣기 오디오 바인딩
        targetContainer.querySelectorAll('.dplay').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const pathA = btn.getAttribute('data-audio-a');
                const pathB = btn.getAttribute('data-audio-b');
                if (pathA && pathB) {
                    try {
                        vid.pause(); // 비디오 정지
                        const audioA = new Audio(pathA);
                        const audioB = new Audio(pathB);
                        
                        audioA.play()
                            .then(() => {
                                setSR('🔊 대화 재생 중 (A)...');
                            })
                            .catch(err => {
                                console.error("오디오 A 재생 실패: ", err);
                            });
                            
                        audioA.addEventListener('ended', () => {
                            setSR('🔊 대화 재생 중 (B)...');
                            setTimeout(() => {
                                audioB.play().catch(err => console.error("오디오 B 재생 실패: ", err));
                            }, 300); // 0.3초 여유
                        });
                        
                        audioB.addEventListener('ended', () => {
                            setSR('대화 재생 완료');
                            vid.play().catch(() => {});
                        });
                    } catch (err) {
                        console.error(err);
                    }
                }
            });
        });
    }

    // ==========================================================================
    // 6. 단계(Step 1, 4, 5, 6) 전환 및 FAB 기능 구현
    // ==========================================================================
    function setStep(n) {
        STEP = n;
        stage.setAttribute('data-step', n);

        const order = { 1: 0, 2: 1, 3: 2, 4: 3 };
        const label = { 1: '영상보기', 2: '강의듣기', 3: '받아쓰기', 4: '따라말하기' };
        const cur = order[n];

        // 알약 메뉴 하이라이트 동기화
        document.querySelectorAll('.pmenu .pstep').forEach(btn => {
            const s = parseInt(btn.getAttribute('data-step'), 10);
            btn.classList.toggle('sel', s === n);
            btn.classList.toggle('done', order[s] < cur);
        });

        pfabCur.textContent = label[n] || '';
        pfab.classList.remove('open'); // 선택 시 메뉴 닫기

        hideSlide();
        setSR('');

        if (n === 1) {
            // Step 1: 자막 없이 통째로 비디오 재생
            vid.muted = false;
            vid.currentTime = 0;
            vid.play().catch(() => {});
        } else {
            // 다른 단계로 이동 시 현재 문장 다시 렌더링
            loadSentence(currentIndex, true);
        }
    }

    // 알약 클릭 시 메뉴 열기
    if (pfabBtn && pfab) {
        pfabBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            pfab.classList.toggle('open');
        });
    }

    // 화면 바깥 클릭 시 알약 닫기
    document.addEventListener('click', (e) => {
        if (pfab && !pfab.contains(e.target)) {
            pfab.classList.remove('open');
        }
    });

    // 각 단계 메뉴 클릭 이벤트 바인딩
    document.querySelectorAll('.pmenu .pstep').forEach(btn => {
        btn.addEventListener('click', () => {
            setStep(parseInt(btn.getAttribute('data-step'), 10));
        });
    });

    // ==========================================================================
    // 7. 재생 관련 유틸리티 (원음 재생, 이동)
    // ==========================================================================
    function playClipOnce(sentence) {
        if (!sentence) return;
        vid.muted = false;
        vid.currentTime = sentence.startSeconds;
        
        const onTimeUpdate = () => {
            if (vid.currentTime >= sentence.endSeconds) {
                vid.pause();
                vid.removeEventListener('timeupdate', onTimeUpdate);
            }
        };
        vid.addEventListener('timeupdate', onTimeUpdate);
        vid.play().catch(() => {
            vid.removeEventListener('timeupdate', onTimeUpdate);
        });
    }

    // 좌우 슬라이드/문장 이동
    function go(direction) {
        if (!ALLSENTS.length) return;
        let targetIndex = currentIndex + direction;
        if (targetIndex < 0) targetIndex = 0;
        if (targetIndex >= ALLSENTS.length) targetIndex = ALLSENTS.length - 1;
        
        loadSentence(targetIndex, true);
    }

    // 비디오 실시간 시간 추적
    if (vid) {
        vid.addEventListener('timeupdate', () => {
            if (STEP === 3 || !ALLSENTS.length) return;
            
            const t = vid.currentTime;
            let matchedIdx = -1;
            for (let i = 0; i < ALLSENTS.length; i++) {
                if (t >= ALLSENTS[i].s && t < ALLSENTS[i].e) {
                    matchedIdx = i;
                    break;
                }
            }

            const subCard = document.getElementById('sub-card');
            if (matchedIdx >= 0) {
                if (subCard) subCard.style.opacity = '1';
                if (matchedIdx !== currentIndex) {
                    loadSentence(matchedIdx, false); // 시크(seek)는 건너뛰고 자막과 카드만 교체
                }
            } else {
                // 대사가 없는 빈 구간이면 이전 자막이 계속 떠있지 않도록 투명 처리
                if (subCard) subCard.style.opacity = '0';
            }
        });
    }

    // ==========================================================================
    // 8. 키보드 단축키 핸들러 (Space: 재생/일정, 대괄호: 자막점프)
    // ==========================================================================
    document.addEventListener('keydown', (e) => {
        // 받아쓰기 인풋 입력 중일 때는 전역 단축키 막음
        if (e.target && /^(INPUT|TEXTAREA)$/.test(e.target.tagName)) {
            return;
        }

        if (e.key === 'ArrowRight') {
            e.preventDefault();
            go(1);
        } else if (e.key === 'ArrowLeft') {
            e.preventDefault();
            go(-1);
        } else if (e.key === ' ' || e.code === 'Space') {
            e.preventDefault();
            if (vid.paused) {
                vid.play().catch(() => {});
            } else {
                vid.pause();
            }
        } else if (e.key === '[') {
            e.preventDefault();
            go(-1);
        } else if (e.key === ']') {
            e.preventDefault();
            go(1);
        }
    });

    // ==========================================================================
    // 9. 원음 듣기 및 따라 말하기(섀도잉)
    // ==========================================================================
    if (listenBtn) {
        listenBtn.addEventListener('click', () => {
            const sentence = lectureData.sentences[currentIndex];
            if (!sentence) return;
            
            setSR('🔊 원음 재생 중...');
            playClipOnce(sentence);
        });
    }

    if (micBtn) {
        micBtn.addEventListener('click', async () => {
            if (recording) {
                mediaRecorder.stop();
                return;
            }

            if (!navigator.mediaDevices || !window.MediaRecorder) {
                setSR('이 브라우저는 음성 녹음을 지원하지 않습니다.');
                return;
            }

            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                audioChunks = [];
                mediaRecorder = new MediaRecorder(stream);
                
                mediaRecorder.ondataavailable = (e) => {
                    if (e.data.size > 0) audioChunks.push(e.data);
                };

                mediaRecorder.onstart = () => {
                    recording = true;
                    micBtn.classList.add('rec');
                    micBtn.innerHTML = '<i class="fa-solid fa-microphone-lines"></i> 녹음 중';
                    setSR('지금 말해보세요! 완료되면 다시 마이크 버튼 클릭...');
                };

                mediaRecorder.onstop = async () => {
                    recording = false;
                    micBtn.classList.remove('rec');
                    micBtn.innerHTML = '<i class="fa-solid fa-microphone"></i> 따라 말하기';
                    
                    stream.getTracks().forEach(track => track.stop());
                    setSR('음성을 인식하고 채점하는 중입니다... ⏳');
                    micBtn.disabled = true;

                    try {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                        const response = await fetch('/transcribe', {
                            method: 'POST',
                            body: audioBlob
                        });
                        const result = await response.json();

                        if (result.error) {
                            setSR('음성 인식 서버 오류가 발생했습니다.');
                        } else {
                            const score = calculateShadowingScore(result.text, lectureData.sentences[currentIndex].english_text);
                            const passed = score >= PASS_SCORE;
                            setSR(`<span class="sc ${passed ? 'y' : 'n'}">${score}%</span> ${passed ? '✅ 통과' : '다시 해보기'} · 들린 말: "${esc(result.text)}"`);
                        }
                    } catch (err) {
                        setSR('섀도잉 서버와 통신할 수 없습니다 (FastAPI 서버 상태 확인 요망).');
                    }
                    
                    micBtn.disabled = false;
                };

                mediaRecorder.start();
            } catch (err) {
                setSR('마이크 사용 권한이 필요합니다.');
            }
        });
    }

    // 섀도잉 발음 채점 알고리즘 (두 문장의 유사도 비교)
    function calculateShadowingScore(spoken, target) {
        function normWords(s) {
            return s.toLowerCase()
                .replace(/['’]/g, '')
                .replace(/[^a-z0-9\s]/g, ' ')
                .split(/\s+/)
                .filter(Boolean);
        }

        const T = normWords(target);
        const S = normWords(spoken);
        const n = T.length;
        const m = S.length;
        if (n === 0) return 0;

        // LCS(Longest Common Subsequence) 테이블 빌드
        const dp = Array.from({ length: n + 1 }, () => Array(m + 1).fill(0));
        for (let i = 1; i <= n; i++) {
            for (let j = 1; j <= m; j++) {
                if (T[i - 1] === S[j - 1]) {
                    dp[i][j] = dp[i - 1][j - 1] + 1;
                } else {
                    dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
                }
            }
        }

        return Math.round((dp[n][m] / n) * 100);
    }

    function setSR(html) {
        sresult.innerHTML = html;
    }

    // ==========================================================================
    // 10. 모바일 터치 스와이프 제스처 (왼쪽/오른쪽 쓸어넘기기로 문장 이동)
    // ==========================================================================
    let touchStartX = 0;
    let touchStartY = 0;
    let touchEndX = 0;
    let touchEndY = 0;

    stage.addEventListener('touchstart', (e) => {
        if (e.target && /^(INPUT|TEXTAREA)$/.test(e.target.tagName)) return;
        touchStartX = e.changedTouches[0].screenX;
        touchStartY = e.changedTouches[0].screenY;
    }, { passive: true });

    stage.addEventListener('touchend', (e) => {
        if (e.target && /^(INPUT|TEXTAREA)$/.test(e.target.tagName)) return;
        touchEndX = e.changedTouches[0].screenX;
        touchEndY = e.changedTouches[0].screenY;
        handleSwipeGesture();
    }, { passive: true });

    function handleSwipeGesture() {
        const diffX = touchEndX - touchStartX;
        const diffY = touchEndY - touchStartY;
        
        // 가로 스와이프가 세로 스크롤보다 크고, 최소 50px 이상 쓸어넘겼을 때 작동
        if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
            if (diffX > 0) {
                go(-1); // 오른쪽으로 쓸어넘김 -> 이전 문장
            } else {
                go(1);  // 왼쪽으로 쓸어넘김 -> 다음 문장
            }
        }
    }

    // 시작!
    init();
});
