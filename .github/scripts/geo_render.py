# GEO(답변엔진 인용) 렌더 로직 — Orca 구조 이식.
# 상단 '한눈 요약'(answerSummary) + 하단 FAQ 섹션 + FAQPage JSON-LD.
# publish_draft.py(신규 초안)와 backfill_geo.py(기존 글 소급)가 공유한다.
import json


def render_geo(body, meta):
    """body(HTML)에 GEO 구조를 주입해 돌려준다.
    - answer_summary: 본문 맨 위 골드 박스(한눈 요약) — 답변엔진이 그대로 인용하기 좋게.
    - faq: 하단 '자주 묻는 질문' 섹션 + FAQPage JSON-LD(구조화 데이터).
    JSON-LD는 '<' 문자가 없는 한 줄로 넣어 워드프레스 wpautop가 깨뜨리지 못하게 한다.
    이미 주입된 글(geo-summary/FAQPage 존재)은 중복 삽입하지 않는다(멱등)."""
    summary = str(meta.get("answer_summary", "")).strip()
    if summary and "geo-summary" not in body:
        sm = ('<div class="geo-summary" style="margin:0 0 1.4em;padding:14px 18px;'
              'border-left:4px solid #c9a44a;background:#f7f4ec;border-radius:6px;'
              f'font-size:15.5px;line-height:1.7;"><strong>한눈 요약</strong><br>{summary}</div>')
        body = sm + "\n" + body
    faq = meta.get("faq") or []
    if faq and "FAQPage" not in body:
        items, ld = "", []
        for it in faq:
            q = str(it.get("q", "")).replace("<", "").replace(">", "").strip()
            a = str(it.get("a", "")).replace("<", "").replace(">", "").strip()
            if not q or not a:
                continue
            items += f"<p><strong>Q. {q}</strong><br>{a}</p>\n"
            ld.append({"@type": "Question", "name": q,
                       "acceptedAnswer": {"@type": "Answer", "text": a}})
        if items:
            jsonld = json.dumps({"@context": "https://schema.org", "@type": "FAQPage",
                                 "mainEntity": ld}, ensure_ascii=False, separators=(",", ":"))
            block = ('<h2 class="wp-block-heading">자주 묻는 질문</h2>\n' + items
                     + '<script type="application/ld+json">' + jsonld + "</script>\n")
            notice = "<p><em>본 글은 일반 정보"
            if notice in body:
                body = body.replace(notice, block + notice, 1)
            else:
                body += "\n" + block
    return body
