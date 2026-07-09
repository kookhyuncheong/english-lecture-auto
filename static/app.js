document.addEventListener('DOMContentLoaded', () => {
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
            const response = await fetch('/processed/01_motivation/analysis.json?v=' + new Date().getTime());
            if (!response.ok) {
                throw new Error("분석 데이터 파일을 불러오지 못했습니다.");
            }
            lectureData = await response.json();
            
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
                        sid: `01-${s.index.toString().padStart(2, '0')}`,
                        index: s.index,
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
        note.classList.remove('on');
        note.innerHTML = '';
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
            vid.currentTime = sentence.startSeconds;
        }

        setSR(STEP === 4 ? '따라 말하면 채점돼요 🎤' : '');
    }

    // 표제어나 base_word를 문장 내 실제 텍스트 형태에 맞춰 찾아주는 헬퍼
    function findHighlightRange(sentenceText, vocab) {
        const text = sentenceText.toLowerCase();
        
        // 0. target_phrase가 존재하면 해당 텍스트 통째로 100% 매칭 시도 (우선순위 1위)
        if (vocab.target_phrase) {
            let target = vocab.target_phrase.toLowerCase();
            let idx = text.indexOf(target);
            if (idx >= 0) return { start: idx, length: target.length };
        }

        // 1. exact word match 먼저 매칭 시도 (예: "an end in itself")
        let word = vocab.word.toLowerCase();
        let cleanWord = vocab.word.replace(/\(.*?\)/g, '')
                                  .replace(/to be\/do something/gi, '')
                                  .replace(/to do something/gi, '')
                                  .replace(/something/gi, '')
                                  .trim().toLowerCase();
        
        let idx = text.indexOf(cleanWord);
        if (idx >= 0) return { start: idx, length: cleanWord.length };

        // 2. base_word가 있으면 그것으로 매칭 후 형태소(접미사) 경계 확장
        if (vocab.base_word) {
            let base = vocab.base_word.toLowerCase();
            idx = text.indexOf(base);
            if (idx >= 0) {
                let endIdx = idx + base.length;
                while (endIdx < text.length && /[a-zA-Z]/.test(text[endIdx])) {
                    endIdx++;
                }
                
                // 표제어에 'to be'가 포함되고 문장에서 단어 바로 뒤에 'to be'가 따라나오면 범위에 포함
                const remainingText = text.slice(endIdx).trim();
                if (vocab.word.includes('to be') && remainingText.startsWith('to be')) {
                    const toBePos = text.indexOf('to be', endIdx);
                    endIdx = toBePos + 5;
                }
                return { start: idx, length: endIdx - idx };
            }
        }
        return null;
    }

    function renderEN(sentence) {
        if (STEP === 3) {
            renderDictation(sentence);
            return;
        }

        const en = sentence.english_text;
        const matchedVocabs = (lectureData.global_vocab_list || []).filter(v => v.sentence_index === sentence.index);
        
        if (matchedVocabs.length === 0) {
            sen.innerHTML = esc(en);
            return;
        }

        let ranges = [];
        matchedVocabs.forEach((v, idx) => {
            const range = findHighlightRange(en, v);
            if (range) {
                ranges.push({ s: range.start, e: range.start + range.length, vocab: v, colorIdx: idx });
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
            out += `<span class="hl" data-vocab-id="${r.vocab.id}" style="color: ${getAccentColor(r.colorIdx)};">${esc(en.slice(r.s, r.e))}</span>`;
            last = r.e;
        });
        out += esc(en.slice(last));
        sen.innerHTML = out;

        // 클릭 이벤트 등록 -> 자막 클릭 시 해당하는 wnote 카드만 노출
        sen.querySelectorAll('.hl').forEach(hl => {
            hl.addEventListener('click', () => {
                if (STEP !== 2) return;
                const vocabId = hl.getAttribute('data-vocab-id');
                const targetCards = document.querySelectorAll('.wnote');
                const matchedCard = document.getElementById(`wnote-${vocabId}`);
                
                if (matchedCard) {
                    const isShown = !matchedCard.classList.contains('hidden');
                    targetCards.forEach(c => c.classList.add('hidden'));
                    if (!isShown) {
                        matchedCard.classList.remove('hidden');
                    }
                }
            });
        });
    }

    // ==========================================================================
    // 4. 받아쓰기 (Step 5: Dictation) 전용 렌더러
    // ==========================================================================
    function renderDictation(sentence) {
        const en = sentence.english_text;
        const matchedVocabs = (lectureData.global_vocab_list || []).filter(v => v.sentence_index === sentence.index);

        if (matchedVocabs.length === 0) {
            sen.innerHTML = esc(en);
            return;
        }

        let ranges = [];
        matchedVocabs.forEach(v => {
            const range = findHighlightRange(en, v);
            if (range) {
                ranges.push({ s: range.start, e: range.start + range.length, word: en.slice(range.start, range.start + range.length) });
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
            note.innerHTML = '';
            return;
        }

        const matchedVocabs = (lectureData.global_vocab_list || []).filter(v => v.sentence_index === sentence.index);
        if (matchedVocabs.length === 0) {
            note.classList.remove('on');
            note.innerHTML = '';
            return;
        }

        let html = [];
        matchedVocabs.forEach((v, idx) => {
            const accent = getAccentColor(idx);
            
            // OALD 영영정의 박스 (단백하고 심플한 디자인)
            let defHtml = '';
            if (v.english_definition) {
                defHtml = `
                    <div style="font-size: 0.8vw; color: var(--ink); margin-top: 0.6vw; line-height: 1.4;">
                        ${esc(v.english_definition)}
                        ${v.english_definition_translation ? `<div style="font-size: 0.75vw; color: var(--ink2); margin-top: 2px;">${esc(v.english_definition_translation)}</div>` : ''}
                    </div>
                `;
            }

            // A/B 대화 예시 (Dialogue Practice - 추후 배치를 위해 화면 노출 보류)
            let convHtml = '';
            /*
            if (v.ab_dialogue && v.ab_dialogue.dialogue_a) {
                const d = v.ab_dialogue;
                convHtml = `
                    <div class="conv" style="margin-top: 10px; border-top: 1px dashed var(--line); padding-top: 8px;">
                        <div class="convhead" style="color: ${accent}">
                            <span>💬 Dialogue Practice</span>
                            ${d.audio_path ? `<button class="dplay" data-audio="${esc(d.audio_path)}" style="border-color: ${accent}; color: ${accent};">▶ 듣기</button>` : ''}
                        </div>
                        <div class="turn">
                            <span class="sp">A.</span> <span class="en">${esc(d.dialogue_a)}</span><br>
                            <span class="ko">${esc(d.translation_a)}</span>
                        </div>
                        <div class="turn">
                            <span class="sp">B.</span> <span class="en">${esc(d.dialogue_b)}</span><br>
                            <span class="ko">${esc(d.translation_b)}</span>
                        </div>
                    </div>
                `;
            }
            */

            // OALD 패턴 및 예문 리스트 (헤더 없이 단백하게 분리)
            let patternsHtml = '';
            if (v.patterns && v.patterns.length > 0) {
                patternsHtml = `
                    <div style="margin-top: 10px; border-top: 1px dashed var(--line); padding-top: 8px;">
                        ${v.patterns.map(pat => {
                            const patText = esc(pat.pattern);
                            const patTrans = pat.pattern_translation ? ` : <span style="font-weight:500; color:var(--ink2); font-size: 0.78vw;">${esc(pat.pattern_translation)}</span>` : '';
                            
                            const examplesList = pat.examples ? pat.examples.map(ex => `
                                <div class="turn" style="margin-top: 5px; padding-left: 10px; border-left: 2px solid ${accent};">
                                    <span class="en" style="font-weight:600; color:var(--ink);">${esc(ex.eng)}</span><br>
                                    <span class="ko" style="font-size:0.72vw; color:var(--ink3);">${esc(ex.kor)}</span>
                                </div>
                            `).join('') : '';

                            return `
                                <div style="margin-top: 8px;">
                                    <div style="font-size: 0.8vw; font-weight: 700; color: ${accent};">
                                        ▶ ${patText}${patTrans}
                                    </div>
                                    ${examplesList}
                                </div>
                            `;
                        }).join('')}
                    </div>
                `;
            } else if (v.oald_examples && v.oald_examples.length > 0) {
                // 이전 레거시 평탄화 포맷용 예외 처리
                patternsHtml = `
                    <div class="conv" style="margin-top: 8px; border-top: 1px dashed #e2d7c4; padding-top: 8px;">
                        <div class="convhead" style="color: ${accent}">
                            <span>📚 Oxford Examples</span>
                        </div>
                        ${v.oald_examples.map(ex => `
                            <div class="turn" style="margin-top: 6px;">
                                <span class="en" style="font-weight:600; color:var(--ink);">${esc(ex.eng)}</span><br>
                                <span class="ko" style="font-size:0.7vw; color:var(--ink3);">${esc(ex.kor)}</span>
                            </div>
                        `).join('')}
                    </div>
                `;
            }

            html.push(`
                <div class="wnote hidden" id="wnote-${v.id}" data-ci="${idx}" style="border-top-color: ${accent}; --sticker: ${accent};">
                    <div class="hwline">
                        <div class="hw">${esc(v.word)}</div>
                    </div>
                    <div class="gloss">${esc(v.meaning)}</div>
                    ${defHtml}
                    ${patternsHtml}
                    ${convHtml}
                </div>
            `);
        });

        note.innerHTML = html.join('');
        note.classList.add('on');

        // 첫 번째 카드는 기본으로 노출
        const firstCard = note.querySelector('.wnote');
        if (firstCard) {
            firstCard.classList.remove('hidden');
        }

        // 회화 듣기 오디오 바인딩
        note.querySelectorAll('.dplay').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const audioPath = btn.getAttribute('data-audio');
                if (audioPath) {
                    try {
                        vid.pause(); // 비디오 정지
                        const audio = new Audio(audioPath);
                        audio.play()
                            .then(() => {
                                setSR('🔊 대화 예문 재생 중...');
                            })
                            .catch(err => {
                                console.error("오디오 재생 실패: ", err);
                            });
                        audio.addEventListener('ended', () => {
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
            if (STEP === 1 || STEP === 3 || !ALLSENTS.length) return;
            
            const t = vid.currentTime;
            let matchedIdx = -1;
            for (let i = 0; i < ALLSENTS.length; i++) {
                if (t >= ALLSENTS[i].s && t < ALLSENTS[i].e) {
                    matchedIdx = i;
                    break;
                }
            }

            if (matchedIdx >= 0 && matchedIdx !== currentIndex) {
                loadSentence(matchedIdx, false); // 시크(seek)는 건너뛰고 자막과 카드만 교체
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

    // 시작!
    init();
});
