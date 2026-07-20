(() => {
  const typeNames = { info: '정보 파악', inference: '추론', vocabulary: '어휘' };
  const articleMap = {
    info: [
      ['횡단보도 안전 글', 'literacy-grade3-crosswalk.html'],
      ['식품 날짜 표시 글', 'literacy-grade6-food-date-label.html'],
      ['재난문자 행동 글', 'literacy-grade8-disaster-alert-action.html']
    ],
    inference: [
      ['주말 도서관 운영 글', 'literacy-grade5-weekend-library.html'],
      ['스마트폰 사용 규칙 글', 'literacy-grade7-smartphone-rules.html'],
      ['수리할 권리 글', 'literacy-grade9-right-to-repair.html']
    ],
    vocabulary: [
      ['놀이터 안전 규칙 글', 'literacy-grade3-playground-rules.html'],
      ['플라스틱 포장 글', 'literacy-grade6-plastic-packaging.html'],
      ['추천 설명 글', 'literacy-grade9-recommendation-explanation.html']
    ]
  };

  const escapeHtml = (value) => String(value ?? '').replace(/[&<>'"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
  const stripHtml = (value) => String(value ?? '').replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();

  function findEvidence(passage, correctChoice) {
    const plain = stripHtml(passage);
    const sentences = plain.split(/(?<=[.!?다요])\s+/).filter(Boolean);
    const keywords = stripHtml(correctChoice).replace(/[^가-힣A-Za-z0-9\s]/g, ' ').split(/\s+/).filter(w => w.length >= 2);
    let best = sentences[0] || plain;
    let bestScore = -1;
    for (const sentence of sentences) {
      const score = keywords.reduce((sum, word) => sum + (sentence.includes(word) ? 1 : 0), 0);
      if (score > bestScore) { bestScore = score; best = sentence; }
    }
    return best || plain.slice(0, 180);
  }

  function enhanceCurrentQuestion() {
    const container = document.querySelector('#quiz-container .question-container');
    if (!container) return;
    const questionText = [...container.querySelectorAll('p')].find(p => /^\s*\d+\.\s+\d+\./.test(p.textContent || ''));
    if (questionText) questionText.innerHTML = questionText.innerHTML.replace(/^(\s*\d+\.)\s+\d+\.\s*/, '$1 ');
    document.querySelectorAll('.choice-item').forEach((item, index) => {
      item.setAttribute('role', 'button');
      item.setAttribute('tabindex', '0');
      item.setAttribute('aria-label', `${index + 1}번 선택지`);
      if (!item.dataset.keyboardReady) {
        item.dataset.keyboardReady = '1';
        item.addEventListener('keydown', event => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            item.click();
          }
        });
      }
    });
  }

  function buildReview() {
    if (typeof allQuestions === 'undefined' || typeof userAnswers === 'undefined') return;
    const modal = document.getElementById('result-modal');
    if (!modal) return;
    let review = document.getElementById('answer-review');
    if (!review) {
      review = document.createElement('section');
      review.id = 'answer-review';
      review.className = 'mt-8 border-t border-white/10 pt-7';
      const recommendationBox = document.getElementById('assessment-text')?.parentElement;
      modal.insertBefore(review, recommendationBox || null);
    }

    const totals = { info: 0, inference: 0, vocabulary: 0 };
    const wrong = { info: 0, inference: 0, vocabulary: 0 };
    const items = allQuestions.map((question, index) => {
      totals[question.type] = (totals[question.type] || 0) + 1;
      const selected = userAnswers[index];
      const correct = selected === question.answer;
      if (!correct) wrong[question.type] = (wrong[question.type] || 0) + 1;
      return { question, index, selected, correct };
    });
    const incorrect = items.filter(item => !item.correct);
    const weakest = Object.keys(wrong).sort((a, b) => {
      const rateA = totals[a] ? wrong[a] / totals[a] : 0;
      const rateB = totals[b] ? wrong[b] / totals[b] : 0;
      return rateB - rateA;
    });

    const cards = incorrect.length ? incorrect.map(({question, index, selected}) => {
      const correctChoice = question.choices[question.answer];
      const selectedText = selected === null || selected === undefined ? '선택하지 않음' : `${selected + 1}번 ${question.choices[selected]}`;
      const evidence = findEvidence(question.passage, correctChoice);
      const optionReasons = question.choices.map((choice, choiceIndex) => {
        let reason;
        if (choiceIndex === question.answer) reason = '지문의 정보와 가장 정확히 일치하거나, 글의 논리에 따라 가장 타당하게 추론한 선택지입니다.';
        else if (choiceIndex === selected) reason = '지문에서 직접 뒷받침되지 않거나, 일부 내용을 지나치게 확대·축소한 선택지입니다.';
        else reason = '지문의 핵심 내용과 맞지 않거나 판단에 필요한 근거가 부족합니다.';
        return `<li class="mt-2"><b>${choiceIndex + 1}번</b> ${escapeHtml(stripHtml(choice))}<br><span class="text-gray-400">${reason}</span></li>`;
      }).join('');
      return `<article class="mt-5 rounded-xl border border-white/10 bg-black/20 p-4">
        <p class="text-sm font-bold text-amber-400">${index + 1}번 · ${typeNames[question.type] || question.type}</p>
        <h3 class="mt-2 font-bold text-white">${escapeHtml(stripHtml(question.q).replace(/^\d+\.\s*/, ''))}</h3>
        <p class="mt-3 text-sm text-gray-300"><b>내 답:</b> ${escapeHtml(selectedText)}</p>
        <p class="mt-1 text-sm text-gray-300"><b>정답:</b> ${question.answer + 1}번 ${escapeHtml(stripHtml(correctChoice))}</p>
        <p class="mt-3 rounded-lg bg-white/5 p-3 text-sm leading-6 text-gray-300"><b class="text-amber-300">지문 근거</b><br>${escapeHtml(evidence)}</p>
        <details class="mt-3"><summary class="cursor-pointer font-bold text-amber-300">선택지별 해설 보기</summary><ol class="mt-2 text-sm leading-6 text-gray-300">${optionReasons}</ol></details>
      </article>`;
    }).join('') : '<p class="mt-4 rounded-xl bg-emerald-900/20 p-4 text-sm text-emerald-200">모든 문항을 맞혔습니다. 아래 추천 글에서 더 높은 난도의 근거 평가와 요약 활동에 도전해 보세요.</p>';

    const weakestType = weakest[0] || 'inference';
    const recommendationLinks = (articleMap[weakestType] || articleMap.inference).map(([label, href]) => `<a class="block rounded-lg border border-white/10 px-4 py-3 hover:border-amber-400" href="${href}">${escapeHtml(label)} →</a>`).join('');
    const summary = Object.keys(totals).map(type => {
      const missed = wrong[type] || 0;
      return `<li>${typeNames[type]}: ${totals[type] - missed}/${totals[type]} 정답 · 취약 문항 ${missed}개</li>`;
    }).join('');

    review.innerHTML = `<h2 class="text-2xl font-bold text-white">문항별 진단과 해설</h2>
      <p class="mt-2 text-sm leading-6 text-gray-400">틀린 문제의 정답, 지문 근거와 선택지별 판단 이유를 확인하세요. 이 결과는 학습 참고용이며 표준화 검사나 실제 응시자 평균과 비교한 결과가 아닙니다.</p>
      <ul class="mt-4 rounded-xl bg-white/5 p-4 text-sm leading-7 text-gray-300">${summary}</ul>
      <div>${cards}</div>
      <div class="mt-7"><h3 class="font-bold text-amber-300">${typeNames[weakestType]} 보완 추천 글</h3><div class="mt-3 grid gap-2">${recommendationLinks}</div></div>`;

    const totalScore = document.getElementById('modal-total-score');
    if (totalScore) {
      const correctCount = items.filter(item => item.correct).length;
      totalScore.textContent = `${correctCount} / ${allQuestions.length}`;
    }
  }

  document.querySelectorAll('.avg-marker').forEach(marker => marker.setAttribute('aria-label', '학습 권장 기준 50퍼센트'));
  const avgText = [...document.querySelectorAll('p')].find(p => (p.textContent || '').includes('흰색 막대'));
  if (avgText) avgText.textContent = '*흰색 막대는 실제 응시자 평균이 아닌 학습 권장 기준 50%입니다.';

  const observerTarget = document.getElementById('quiz-container');
  if (observerTarget) new MutationObserver(enhanceCurrentQuestion).observe(observerTarget, { childList: true, subtree: true });
  enhanceCurrentQuestion();
  const gradeButton = document.getElementById('grade-button');
  if (gradeButton) gradeButton.addEventListener('click', () => setTimeout(buildReview, 0));
})();