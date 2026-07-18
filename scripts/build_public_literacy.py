#!/usr/bin/env python3
"""Build the additional Rhodus public literacy articles and discovery files."""

from __future__ import annotations

import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_FILES = sorted((ROOT / "content").glob("literacy_public_articles_*.json"))
PUBLISHED = "2026-07-18"
SITE_UPDATED = "2026-07-19"

EXISTING = [
    {"grade_no": 3, "grade": "초등 3학년", "week": "1주차 월요일", "theme": "교통안전", "title": "학교 앞 횡단보도에서는 뛰지 말아요", "dek": "위험한 까닭과 안전한 행동 순서를 읽고 중심 내용을 찾습니다.", "filename": "literacy-grade3-crosswalk.html"},
    {"grade_no": 4, "grade": "초등 4학년", "week": "1주차 월요일", "theme": "생명 존중", "title": "반려동물은 끝까지 책임져야 합니다", "dek": "반려동물을 맞는 선택에 따르는 책임과 근거를 정리합니다.", "filename": "literacy-grade4-pet-responsibility.html"},
    {"grade_no": 5, "grade": "초등 5학년", "week": "1주차 월요일", "theme": "공공시설", "title": "주말에도 지역 도서관을 충분히 열어야 합니다", "dek": "주장·근거·반론·대안으로 이어지는 사설의 구조를 살펴봅니다.", "filename": "literacy-grade5-weekend-library.html"},
    {"grade_no": 6, "grade": "초등 6학년", "week": "1주차 월요일", "theme": "환경과 소비", "title": "상품의 플라스틱 포장을 줄여야 합니다", "dek": "포장의 필요성과 환경 문제를 함께 고려한 해결책을 찾습니다.", "filename": "literacy-grade6-plastic-packaging.html"},
    {"grade_no": 7, "grade": "중학교 1학년", "week": "1주차 월요일", "theme": "디지털 생활", "title": "교내 스마트폰 사용에는 분명한 규칙이 필요하다", "dek": "학습권과 편리함을 조정하는 규칙의 조건을 분석합니다.", "filename": "literacy-grade7-smartphone-rules.html"},
    {"grade_no": 8, "grade": "중학교 2학년", "week": "1주차 월요일", "theme": "이동권과 복지", "title": "청소년 대중교통비 지원을 확대할 필요가 있다", "dek": "정책을 둘러싼 재정·형평성·사회적 효과를 평가합니다.", "filename": "literacy-grade8-transit-support.html"},
    {"grade_no": 9, "grade": "중학교 3학년", "week": "1주차 월요일", "theme": "인공지능 윤리", "title": "인공지능 활용 과제에는 사용 과정과 출처를 밝혀야 한다", "dek": "공정성·검증·책임의 관점에서 논증의 타당성을 따져 봅니다.", "filename": "literacy-grade9-ai-disclosure.html"},
]


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def short_grade(item: dict) -> str:
    if item.get("short_grade"):
        return item["short_grade"]
    return f'초{item["grade_no"]}' if item["grade_no"] <= 6 else f'중{item["grade_no"] - 6}'


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
        choices = "".join(f"<li>{esc(choice)}</li>" for choice in question["choices"])
        questions.append(
            f'<div class="question"><p>{number}. {esc(question["prompt"])}</p>'
            f'<ol>{choices}</ol><details><summary>정답과 풀이 보기</summary>'
            f'<p class="answer">{esc(question["answer"])}</p></details></div>'
        )
    schema = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": item["title"],
            "datePublished": PUBLISHED,
            "dateModified": PUBLISHED,
            "author": {"@type": "Organization", "name": "로두스 문해력 연구팀"},
            "publisher": {"@type": "Organization", "name": "로두스"},
            "mainEntityOfPage": f'https://www.rhoduss.com/{item["filename"]}',
            "inLanguage": "ko",
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return f'''<!doctype html><html lang="ko"><head>
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5341216668095254" crossorigin="anonymous"></script>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="description" content="{esc(item['description'])}"><link rel="canonical" href="https://www.rhoduss.com/{esc(item['filename'])}">
  <title>{esc(item['title'])} | {esc(item['short_grade'])} 문해력</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800;900&display=swap" rel="stylesheet"><link rel="stylesheet" href="literacy.css">
  <script type="application/ld+json">{schema}</script>
</head><body>
  <header class="site-header"><nav class="nav"><a class="brand" href="index.html">로두스</a><div class="nav-links"><a href="literacy.html">읽기 자료</a><a href="selection.html">문해력 테스트</a><a class="primary" href="subscribe.html">학습지 구독</a></div></nav></header>
  <main><section class="hero"><div class="hero-inner"><p class="eyebrow">{esc(item['grade'])} · {esc(item['theme'])} · {esc(item['week'])}</p><h1>{esc(item['title'])}</h1><p class="dek">{esc(item['dek'])}</p><div class="meta"><span>로두스 문해력 연구팀</span><span>2026.07.18.</span><span>읽기 {item['reading_minutes']}분 · 문제 {item['question_minutes']}분</span></div></div></section>
  <div class="layout"><article class="article"><h2>사설 읽기</h2><div class="passage">
{paragraphs}
  </div><p class="claim">글 전체의 주장: {esc(item['claim'])}</p>
  <h2>문단별 논리 구조</h2><ol class="analysis-list">{analyses}</ol>
  <h2>핵심 어휘</h2><dl class="vocab">{vocab}</dl>
  <h2>읽은 내용 확인하기</h2><div class="practice">{''.join(questions)}</div>
  <p class="editor-note">이 글은 로두스 문해력 연구팀이 학습 목적으로 직접 작성한 창작 사설입니다. 특정 신문 기사나 교과서 본문을 옮기지 않았습니다.</p>
  </article><aside class="sidebar"><div class="side-card"><h2>내 문해력도 확인해 보세요</h2><p>{esc(item['grade'])}용 테스트로 정보 파악·추론·어휘 역량을 점검할 수 있습니다.</p><a href="grade{item['grade_no']}.html">{esc(item['short_grade'])} 무료 테스트</a></div><div class="more"><a href="literacy.html">전체 읽기 자료 보기 →</a><a href="subscribe.html">매일 학습지 구독 안내 →</a></div></aside></div></main>
  <footer class="site-footer"><div class="footer-links"><a href="about.html">운영자 소개</a><a href="editorial-policy.html">콘텐츠 제작 원칙</a><a href="privacy.html">개인정보처리방침</a><a href="terms.html">이용약관</a><a href="contact.html">문의</a><a href="copyright.html">저작권 안내</a></div><p class="footer-copy">로두스 · 문해력 테스트와 매일 읽기 학습<br>© 2026 RODUS. All Rights Reserved.</p></footer>
</body></html>
'''


def card(item: dict) -> str:
    return (
        f'<a class="archive-card" href="{esc(item["filename"])}">'
        f'<span class="grade">{esc(item["grade"])} · {esc(item["theme"])}</span>'
        f'<h2>{esc(item["title"])}</h2><p>{esc(item["dek"])}</p>'
        '<span class="go">글과 해설 읽기 →</span></a>'
    )


def build_archive(items: list[dict]) -> str:
    sections = []
    for week in ["1주차 월요일", "1주차 목요일", "2주차 월요일", "2주차 목요일"]:
        cards = "\n".join(card(item) for item in items if item["week"] == week)
        sections.append(f'<section class="archive-week"><div class="week-heading"><p>{week}</p><h2>학년별 신문 사설 읽기</h2></div><div class="archive-grid">{cards}</div></section>')
    return f'''<!doctype html><html lang="ko"><head>
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5341216668095254" crossorigin="anonymous"></script>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="초등 3학년부터 중학교 3학년까지 학년별로 읽는 로두스 창작 사설 28편과 문단 분석, 핵심 어휘, 확인 문제입니다."><link rel="canonical" href="https://www.rhoduss.com/literacy.html"><title>학년별 문해력 읽기 자료 28편 | 로두스</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800;900&display=swap" rel="stylesheet"><link rel="stylesheet" href="literacy.css">
</head><body>
  <header class="site-header"><nav class="nav"><a class="brand" href="index.html">로두스</a><div class="nav-links"><a href="literacy.html">읽기 자료</a><a href="selection.html">문해력 테스트</a><a class="primary" href="subscribe.html">학습지 구독</a></div></nav></header>
  <main><section class="archive-hero"><p class="eyebrow">RODUS OPEN LIBRARY</p><h1>학년별 문해력 읽기 자료</h1><p class="dek">로두스가 직접 쓴 사설형 글 28편을 읽고 문단의 기능, 주제문, 핵심 어휘와 내용을 차근차근 확인하세요. 아래 자료는 별도 로그인 없이 모두 읽을 수 있습니다.</p><div class="meta"><span>대상 초3–중3</span><span>총 28편</span><span>정보 파악·추론·어휘 통합</span></div></section>
  <div class="archive">{''.join(sections)}</div></main>
  <footer class="site-footer"><div class="footer-links"><a href="about.html">운영자 소개</a><a href="editorial-policy.html">콘텐츠 제작 원칙</a><a href="privacy.html">개인정보처리방침</a><a href="terms.html">이용약관</a><a href="contact.html">문의</a><a href="copyright.html">저작권 안내</a></div><p class="footer-copy">로두스 · 문해력 테스트와 매일 읽기 학습<br>© 2026 RODUS. All Rights Reserved.</p></footer>
</body></html>
'''


def build_sitemap(items: list[dict]) -> str:
    entries = [
        ("", "weekly", "1.0", SITE_UPDATED), ("literacy.html", "weekly", "1.0", SITE_UPDATED),
        ("selection.html", "monthly", "0.9", PUBLISHED), ("subscribe.html", "weekly", "0.8", PUBLISHED),
    ]
    entries += [
        ("about.html", "monthly", "0.6", SITE_UPDATED),
        ("editorial-policy.html", "monthly", "0.6", SITE_UPDATED),
        ("privacy.html", "yearly", "0.5", SITE_UPDATED),
        ("terms.html", "yearly", "0.5", SITE_UPDATED),
        ("contact.html", "yearly", "0.5", SITE_UPDATED),
        ("copyright.html", "yearly", "0.5", SITE_UPDATED),
    ]
    entries += [(item["filename"], "monthly", "0.9", PUBLISHED) for item in items]
    entries += [(f"grade{grade}.html", "monthly", "0.8", PUBLISHED) for grade in range(3, 10)]
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
<rss version="2.0"><channel><title>로두스 학년별 문해력 읽기</title><link>https://www.rhoduss.com/literacy.html</link><description>초등 3학년부터 중학교 3학년까지 문단 분석·주제문·어휘·확인 문제가 포함된 창작 사설 28편</description><language>ko</language><lastBuildDate>Sat, 18 Jul 2026 06:00:00 +0900</lastBuildDate>
{chr(10).join(entries)}
</channel></rss>
'''


def main() -> None:
    articles = []
    for data_file in DATA_FILES:
        articles.extend(json.loads(data_file.read_text(encoding="utf-8")))
    for article in articles:
        (ROOT / article["filename"]).write_text(build_article(article), encoding="utf-8")
    all_items = EXISTING + articles
    (ROOT / "literacy.html").write_text(build_archive(all_items), encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(build_sitemap(all_items), encoding="utf-8")
    (ROOT / "rss.xml").write_text(build_rss(all_items), encoding="utf-8")
    print(f"Built {len(articles)} new articles; archive now contains {len(all_items)} articles.")


if __name__ == "__main__":
    main()
