#!/usr/bin/env python3
"""Build Rhodus public literacy articles, archive, sitemap, and RSS."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_FILES = sorted((ROOT / "content").glob("literacy_public_articles_*.json"))
PUBLISHED = "2026-07-18"
SITE_UPDATED = "2026-07-20"
OG_IMAGE = "https://www.rhoduss.com/og-literacy.svg"

EXISTING = [
    {"grade_no": 3, "grade": "초등 3학년", "week": "1주차 월요일", "theme": "교통안전", "title": "학교 앞 횡단보도에서는 뛰지 말아요", "dek": "위험한 까닭과 안전한 행동 순서를 읽고 중심 내용을 찾습니다.", "filename": "literacy-grade3-crosswalk.html"},
    {"grade_no": 4, "grade": "초등 4학년", "week": "1주차 월요일", "theme": "생명 존중", "title": "반려동물은 끝까지 책임져야 합니다", "dek": "반려동물을 맞는 선택에 따르는 책임과 근거를 정리합니다.", "filename": "literacy-grade4-pet-responsibility.html"},
    {"grade_no": 5, "grade": "초등 5학년", "week": "1주차 월요일", "theme": "공공시설", "title": "주말에도 지역 도서관을 충분히 열어야 합니다", "dek": "주장·근거·반론·대안으로 이어지는 사설의 구조를 살펴봅니다.", "filename": "literacy-grade5-weekend-library.html"},
    {"grade_no": 6, "grade": "초등 6학년", "week": "1주차 월요일", "theme": "환경과 소비", "title": "상품의 플라스틱 포장을 줄여야 합니다", "dek": "포장의 필요성과 환경 문제를 함께 고려한 해결책을 찾습니다.", "filename": "literacy-grade6-plastic-packaging.html"},
    {"grade_no": 7, "grade": "중학교 1학년", "week": "1주차 월요일", "theme": "디지털 생활", "title": "교내 스마트폰 사용에는 분명한 규칙이 필요하다", "dek": "학습권과 편리함을 조정하는 규칙의 조건을 분석합니다.", "filename": "literacy-grade7-smartphone-rules.html"},
    {"grade_no": 8, "grade": "중학교 2학년", "week": "1주차 월요일", "theme": "이동권과 복지", "title": "청소년 대중교통비 지원을 확대할 필요가 있다", "dek": "정책을 둘러싼 재정·형평성·사회적 효과를 평가합니다.", "filename": "literacy-grade8-transit-support.html"},
    {"grade_no": 9, "grade": "중학교 3학년", "week": "1주차 월요일", "theme": "인공지능 윤리", "title": "인공지능 활용 과제에는 사용 과정과 출처를 밝혀야 한다", "dek": "공정성·검증·책임의 관점에서 논증의 타당성을 따져 봅니다.", "filename": "literacy-grade9-ai-disclosure.html"},
]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def short_grade(item: dict) -> str:
    if item.get("short_grade"):
        return item["short_grade"]
    return f'초{item["grade_no"]}' if item["grade_no"] <= 6 else f'중{item["grade_no"] - 6}'


def answer_note(answer: str) -> str:
    paragraph = re.search(r"(\d+)문단", answer)
    if paragraph:
        evidence = f'{paragraph.group(1)}문단에서 정답 선택지와 같은 뜻의 문장을 확인하세요.'
    elif "마지막" in answer:
        evidence = "마지막 문단의 결론과 앞 문단의 근거를 함께 확인하세요."
    elif "글 전체" in answer or "모든 문단" in answer:
        evidence = "첫 문단의 문제 제기와 마지막 문단의 결론이 같은 방향을 가리키는지 확인하세요."
    else:
        evidence = "본문에서 선택지와 같은 의미를 가진 문장을 찾아 앞뒤 문맥과 함께 확인하세요."
    return (
        f'<p class="answer-note"><b>정답 근거</b> {esc(evidence)}<br>'
        '<b>오답 검토</b> 본문에 없는 단정, 일부 내용의 지나친 확대·축소, '
        '원인과 결과의 뒤바뀜을 확인하세요.</p>'
    )


def extra_questions(item: dict, start: int) -> str:
    analyses = item["analysis"]
    claim = item["claim"]
    word, meaning = item["vocab"][0]
    first_summary = analyses[0]
    last_summary = analyses[-1]
    middle_summary = " ".join(analyses[1:-1]) or first_summary
    grade = item["grade_no"]

    if grade <= 4:
        labels = ["핵심 내용 확인", "문단 이어 읽기", "까닭 추론", "낱말 문맥 적용", "근거 살피기", "한 문장 요약"]
        relation_prompt = "첫 문단과 마지막 문단은 어떻게 이어지나요?"
        inference_prompt = "가운데 문단의 내용이 글쓴이의 생각을 어떻게 도와주는지 설명해 보세요."
    elif grade <= 6:
        labels = ["핵심 주장 확인", "문단 관계", "근거 추론", "어휘 문맥 적용", "반론·근거 평가", "서술형 요약"]
        relation_prompt = "1문단의 문제 제기와 마지막 문단의 결론은 어떤 관계인가요?"
        inference_prompt = "중간 문단의 정보가 글 전체의 주장을 어떻게 뒷받침하는지 설명하세요."
    else:
        labels = ["논지 확인", "논증 구조", "추론", "문맥 어휘", "반론·재반박", "한 문장 요약"]
        relation_prompt = "서론의 문제 제기와 결론의 주장이 논증 구조에서 어떤 관계를 이루는지 설명하세요."
        inference_prompt = "중간 문단의 근거가 결론의 타당성을 높이는 방식을 분석하세요."

    questions = [
        f'''<div class="question enriched-question"><span class="question-type">{labels[0]}</span><p>{start}. 글 전체의 주장으로 가장 적절한 내용을 한 문장으로 쓰세요.</p><details><summary>예시 답안과 근거 보기</summary><p class="answer">{esc(claim)}</p><p class="answer-note"><b>근거 문단</b> 첫 문단에서 문제를 제기하고 마지막 문단에서 해결 방향이나 실천을 강조합니다.</p></details></div>''',
        f'''<div class="question enriched-question"><span class="question-type">{labels[1]}</span><p>{start + 1}. {esc(relation_prompt)}</p><ol><li>서로 관계없이 다른 주제를 설명한다.</li><li>첫 문단에서 문제를 제기하고 마지막 문단에서 주장이나 해결 방향을 제시한다.</li><li>첫 문단의 주장을 마지막 문단에서 완전히 취소한다.</li><li>두 문단 모두 사례만 나열하고 결론은 제시하지 않는다.</li></ol><details><summary>정답과 문단 근거 보기</summary><p class="answer">정답 ②. 1문단은 ‘{esc(first_summary)}’, 마지막 문단은 ‘{esc(last_summary)}’의 역할을 합니다.</p><p class="answer-note"><b>오답 검토</b> ①·④는 문단 기능을 무시하고, ③은 두 문단의 방향을 반대로 판단한 선택지입니다.</p></details></div>''',
        f'''<div class="question enriched-question"><span class="question-type">{labels[2]}</span><p>{start + 2}. {esc(inference_prompt)}</p><details><summary>예시 답안과 근거 보기</summary><p class="answer">중간 문단은 {esc(middle_summary)} 이를 통해 마지막 문단의 주장인 ‘{esc(claim)}’이 구체적인 이유와 방법을 갖춘 주장임을 보여 줍니다.</p><p class="answer-note"><b>근거 문단</b> 2문단부터 마지막 전 문단까지의 설명을 순서대로 연결해 보세요.</p></details></div>''',
        f'''<div class="question enriched-question"><span class="question-type">{labels[3]}</span><p>{start + 3}. ‘{esc(word)}’의 문맥상 뜻을 쓰고, 그 뜻이 드러나는 본문 문장을 찾아 적으세요.</p><details><summary>예시 답안 보기</summary><p class="answer">‘{esc(word)}’는 ‘{esc(meaning)}’라는 뜻입니다. 본문에서 이 낱말이 쓰인 문장과 앞뒤 문장을 함께 읽으면 구체적인 뜻을 확인할 수 있습니다.</p><p class="answer-note"><b>어휘 학습</b> 사전 뜻만 외우지 말고 글 속 대상·행동·상황과 연결해 설명하세요.</p></details></div>''',
        f'''<div class="question enriched-question"><span class="question-type">{labels[4]}</span><p>{start + 4}. 글의 주장에 반대하는 사람이 제기할 수 있는 우려를 한 가지 쓰고, 본문의 근거를 활용해 답하세요.</p><details><summary>예시 답안과 평가 기준 보기</summary><p class="answer">예상 반론은 “이 실천은 시간·비용·불편을 늘릴 수 있다.”입니다. 이에 대해 중간 문단의 구체적인 이유와 실천 방법을 들어 불편을 줄이면서도 주장한 목적을 달성할 수 있다고 재반박할 수 있습니다.</p><p class="answer-note"><b>평가 기준</b> 반론이 실제로 주장과 충돌하는지, 재반박이 본문의 근거를 사용했는지 확인하세요.</p></details></div>''',
        f'''<div class="question enriched-question"><span class="question-type">{labels[5]}</span><p>{start + 5}. 이 글을 처음 읽는 친구도 핵심을 이해할 수 있도록 한 문장으로 요약하세요.</p><details><summary>예시 답안과 채점 기준 보기</summary><p class="answer">{esc(claim)}</p><p class="answer-note"><b>채점 기준</b> 주제 대상, 글쓴이의 판단, 중요한 이유나 조건 중 두 가지 이상이 들어가야 합니다.</p></details></div>''',
    ]
    return (
        '<div class="learning-map"><b>학습 문항 구성</b><span>핵심 내용 2 · 문단 관계·추론 2 · '
        '어휘 1 · 근거 평가 1 · 서술형 2 이상</span></div>' + "".join(questions)
    )


def build_article(item: dict) -> str:
    paragraphs = "\n".join(
        f'      <p><span class="num">[{number}]</span>{esc(paragraph)}</p>'
        for number, paragraph in enumerate(item["paragraphs"], 1)
    )
    analyses = "".join(
        f'<li><b>{number}문단</b><span>{esc(summary)}</span></li>'
        for number, summary in enumerate(item["analysis"], 1)
    )
    vocab = "".join(
        f'<div><dt>{esc(word)}</dt><dd>{esc(meaning)}</dd></div>'
        for word, meaning in item["vocab"]
    )
    questions = []
    for number, question in enumerate(item["questions"], 1):
        choices = "".join(f"<li>{esc(choice)}</li>" for choice in question.get("choices", []))
        questions.append(
            f'<div class="question"><p>{number}. {esc(question["prompt"])}</p>'
            f'<ol>{choices}</ol><details><summary>정답과 풀이 보기</summary>'
            f'<p class="answer">{esc(question["answer"])}</p>{answer_note(question["answer"])}</details></div>'
        )
    questions.append(extra_questions(item, len(item["questions"]) + 1))

    schema = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": item["title"],
            "datePublished": PUBLISHED,
            "dateModified": SITE_UPDATED,
            "author": {"@type": "Organization", "name": "로두스 문해력 연구팀", "url": "https://www.rhoduss.com/about.html"},
            "publisher": {"@type": "Organization", "name": "로두스", "url": "https://www.rhoduss.com/", "logo": {"@type": "ImageObject", "url": OG_IMAGE}},
            "image": OG_IMAGE,
            "mainEntityOfPage": f'https://www.rhoduss.com/{item["filename"]}',
            "inLanguage": "ko",
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    question_minutes = max(int(item["question_minutes"]), 12)
    return f'''<!doctype html><html lang="ko"><head>
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5341216668095254" crossorigin="anonymous"></script>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="description" content="{esc(item['description'])}"><link rel="canonical" href="https://www.rhoduss.com/{esc(item['filename'])}">
  <title>{esc(item['title'])} | {esc(item['short_grade'])} 문해력</title>
  <meta property="og:type" content="article"><meta property="og:title" content="{esc(item['title'])} | 로두스"><meta property="og:description" content="본문·문단 분석·어휘·9개 이상의 학습 문항과 근거 해설을 제공합니다."><meta property="og:image" content="{OG_IMAGE}">
  <link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800;900&display=swap" rel="stylesheet"><link rel="stylesheet" href="literacy.css">
  <script type="application/ld+json">{schema}</script>
</head><body>
  <header class="site-header"><nav class="nav"><a class="brand" href="index.html">로두스</a><div class="nav-links"><a href="literacy.html">읽기 자료</a><a href="selection.html">문해력 테스트</a><a class="primary" href="subscribe.html">학습지 구독</a></div></nav></header>
  <main><section class="hero"><div class="hero-inner"><p class="eyebrow">{esc(item['grade'])} · {esc(item['theme'])} · {esc(item['week'])}</p><h1>{esc(item['title'])}</h1><p class="dek">{esc(item['dek'])}</p><div class="meta"><span>로두스 문해력 연구팀</span><span>초판 2026.07.18. · 검수 2026.07.20.</span><span>읽기 {item['reading_minutes']}분 · 문제 {question_minutes}분</span></div></div></section>
  <div class="layout"><article class="article"><h2>사설 읽기</h2><div class="passage">
{paragraphs}
  </div><p class="claim">글 전체의 주장: {esc(item['claim'])}</p>
  <h2>문단별 논리 구조</h2><ol class="analysis-list">{analyses}</ol>
  <h2>핵심 어휘</h2><dl class="vocab">{vocab}</dl>
  <h2>읽은 내용 확인하기</h2><div class="practice">{''.join(questions)}</div>
  <p class="editor-note">이 글은 로두스 문해력 연구팀이 학습 목적으로 직접 작성한 창작 사설입니다. 특정 신문 기사나 교과서 본문을 옮기지 않았습니다.</p>
  </article><aside class="sidebar"><div class="side-card"><h2>내 문해력도 확인해 보세요</h2><p>{esc(item['grade'])}용 테스트로 정보 파악·추론·어휘 역량을 점검하고 문항별 해설을 확인할 수 있습니다.</p><a href="grade{item['grade_no']}.html">{esc(item['short_grade'])} 무료 테스트</a></div><div class="more"><a href="literacy.html">전체 읽기 자료 보기 →</a><a href="subscribe.html">학습지 구독 안내 →</a></div></aside></div></main>
  <footer class="site-footer"><div class="footer-links"><a href="about.html">운영자 소개</a><a href="editorial-policy.html">콘텐츠 제작 원칙</a><a href="privacy.html">개인정보처리방침</a><a href="terms.html">이용약관</a><a href="contact.html">문의</a><a href="copyright.html">저작권 안내</a></div><p class="footer-copy">로두스 · 문해력 테스트와 하루 한 편 읽기 학습<br>© 2026 RODUS. All Rights Reserved.</p></footer>
</body></html>
'''


def card(item: dict) -> str:
    return (
        f'<a class="archive-card" href="{esc(item["filename"])}">'
        f'<span class="grade">{esc(item["grade"])} · {esc(item["theme"])}</span>'
        f'<h2>{esc(item["title"])}</h2><p>{esc(item["dek"])}</p>'
        '<span class="go">글·문단 분석·문항 해설 읽기 →</span></a>'
    )


def build_archive(items: list[dict]) -> str:
    sections = []
    for week in ["1주차 월요일", "1주차 목요일", "2주차 월요일", "2주차 목요일"]:
        cards = "\n".join(card(item) for item in items if item["week"] == week)
        sections.append(f'<section class="archive-week"><div class="week-heading"><p>{week}</p><h2>학년별 신문 사설 읽기</h2></div><div class="archive-grid">{cards}</div></section>')
    return f'''<!doctype html><html lang="ko"><head>
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5341216668095254" crossorigin="anonymous"></script>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="초등 3학년부터 중학교 3학년까지 학년별로 읽는 로두스 창작 사설 28편과 문단 분석, 핵심 어휘, 근거 해설 문항입니다."><link rel="canonical" href="https://www.rhoduss.com/literacy.html"><title>학년별 문해력 읽기 자료 28편 | 로두스</title>
  <meta property="og:type" content="website"><meta property="og:title" content="학년별 문해력 읽기 자료 28편 | 로두스"><meta property="og:description" content="본문·문단 분석·어휘·근거 평가·서술형 요약 활동을 제공합니다."><meta property="og:image" content="{OG_IMAGE}">
  <link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800;900&display=swap" rel="stylesheet"><link rel="stylesheet" href="literacy.css">
</head><body>
  <header class="site-header"><nav class="nav"><a class="brand" href="index.html">로두스</a><div class="nav-links"><a href="literacy.html">읽기 자료</a><a href="selection.html">문해력 테스트</a><a class="primary" href="subscribe.html">학습지 구독</a></div></nav></header>
  <main><section class="archive-hero"><p class="eyebrow">RODUS OPEN LIBRARY</p><h1>학년별 문해력 읽기 자료</h1><p class="dek">하루 한 편씩 학습할 수 있도록 로두스가 직접 쓴 사설형 글 28편을 제공합니다. 문단의 기능, 주제문, 핵심 어휘, 추론·근거 평가·서술형 요약까지 한 화면에서 학습하세요.</p><div class="meta"><span>대상 초3–중3</span><span>총 28편</span><span>글마다 9개 이상의 학습 문항</span></div></section>
  <div class="archive">{''.join(sections)}</div></main>
  <footer class="site-footer"><div class="footer-links"><a href="about.html">운영자 소개</a><a href="editorial-policy.html">콘텐츠 제작 원칙</a><a href="privacy.html">개인정보처리방침</a><a href="terms.html">이용약관</a><a href="contact.html">문의</a><a href="copyright.html">저작권 안내</a></div><p class="footer-copy">로두스 · 문해력 테스트와 하루 한 편 읽기 학습<br>© 2026 RODUS. All Rights Reserved.</p></footer>
</body></html>
'''


def build_sitemap(items: list[dict]) -> str:
    entries = [
        ("", "weekly", "1.0", SITE_UPDATED),
        ("literacy.html", "weekly", "1.0", SITE_UPDATED),
        ("selection.html", "monthly", "0.9", SITE_UPDATED),
        ("subscribe.html", "weekly", "0.8", SITE_UPDATED),
        ("about.html", "monthly", "0.6", SITE_UPDATED),
        ("editorial-policy.html", "monthly", "0.6", SITE_UPDATED),
        ("privacy.html", "yearly", "0.5", SITE_UPDATED),
        ("terms.html", "yearly", "0.5", SITE_UPDATED),
        ("contact.html", "yearly", "0.5", SITE_UPDATED),
        ("copyright.html", "yearly", "0.5", SITE_UPDATED),
    ]
    entries += [(item["filename"], "monthly", "0.9", SITE_UPDATED) for item in items]
    entries += [(f"grade{grade}.html", "monthly", "0.8", SITE_UPDATED) for grade in range(3, 10)]
    urls = "\n".join(
        f'  <url><loc>https://www.rhoduss.com/{path}</loc><lastmod>{lastmod}</lastmod><changefreq>{freq}</changefreq><priority>{priority}</priority></url>'
        for path, freq, priority, lastmod in entries
    )
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n'


def build_rss(items: list[dict]) -> str:
    entries = []
    for item in reversed(items):
        entries.append(
            f'  <item><title>{esc(item["title"])} | {esc(short_grade(item))}</title>'
            f'<link>https://www.rhoduss.com/{esc(item["filename"])}</link>'
            f'<description>{esc(item["dek"])}</description>'
            f'<pubDate>Sat, 18 Jul 2026 06:00:00 +0900</pubDate>'
            f'<guid>https://www.rhoduss.com/{esc(item["filename"])}</guid></item>'
        )
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>로두스 학년별 문해력 읽기</title><link>https://www.rhoduss.com/literacy.html</link><description>초등 3학년부터 중학교 3학년까지 문단 분석·주제문·어휘·근거 해설 문항이 포함된 창작 사설 28편</description><language>ko</language><lastBuildDate>Mon, 20 Jul 2026 12:00:00 +0900</lastBuildDate>
{chr(10).join(entries)}
</channel></rss>
'''


def main() -> None:
    articles: list[dict] = []
    for data_file in DATA_FILES:
        articles.extend(json.loads(data_file.read_text(encoding="utf-8")))
    for article in articles:
        (ROOT / article["filename"]).write_text(build_article(article), encoding="utf-8")
    all_items = EXISTING + articles
    (ROOT / "literacy.html").write_text(build_archive(all_items), encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(build_sitemap(all_items), encoding="utf-8")
    (ROOT / "rss.xml").write_text(build_rss(all_items), encoding="utf-8")
    print(f"Built {len(articles)} enriched articles; archive contains {len(all_items)} articles.")


if __name__ == "__main__":
    main()
