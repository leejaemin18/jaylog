# 발행 전 AI 티 게이트 — drafts/의 각 초안 본문을 humanize-korean 스코어러로 점수화.
# im-not-ai(Humanize KR, MIT)의 결정적 지표(metrics_v2 + route_hint)를 재사용한다.
# 비차단: AI 티가 강하면 ::warning:: 만 남기고 파이프라인은 계속 진행(하루 발행 흐름 보호).
# route_hint: light=깨끗 / standard=티 섞임(humanize 권장) / heavy=AI 슬롭 밀집(humanize 필수).
import os, re, sys, glob

import yaml

SKILL = os.path.join(os.path.dirname(__file__), "..", "..",
                     ".claude", "skills", "humanize-korean")
sys.path.insert(0, os.path.abspath(os.path.join(SKILL, "references")))
sys.path.insert(0, os.path.abspath(os.path.join(SKILL, "scripts")))


def strip_html(h):
    h = re.sub(r"(?is)<script.*?</script>", " ", h)
    h = re.sub(r"(?is)<style.*?</style>", " ", h)
    text = re.sub(r"(?s)<[^>]+>", " ", h)
    text = text.replace("&nbsp;", " ")
    return re.sub(r"[ \t]+\n", "\n", re.sub(r"[ \t]{2,}", " ", text)).strip()


# --- jaylog 고정밀 어휘 티 스캐너 (taxonomy S1/S2 중 오탐 적은 것만 선별) ---
# 좋은 글엔 거의 안 나오는 것들. 관세·통관 정보글 문맥에서 정상어와 잘 안 겹치게 골랐다.
S1_IDIOMS = [  # 한 번만 나와도 AI 확신 (D 관용구)
    "결론적으로", "종합하면", "종합적으로", "시사하는 바", "시사하는바",
    "주목할 만하다", "주목할만하다", "라 할 수 있다", "라고 할 수 있다",
    "라 할 수 있습니다", "라고 할 수 있습니다", "중요한 의미를 가지", "다름 아니다",
]
S2_PATTERNS = {  # 반복되면 티 (정규식, per-문서 카운트)
    "번역투 ~를 통해": r"(?:를|을)\s*통해",
    "번역투 ~에 있어서": r"에\s*있어서?",
    "번역투 가지고 있다": r"(?:가지|갖)고\s*있",
    "이중피동 ~되어진/지게된": r"되어지|지게\s*된다",
    "문두 접속사(또한/따라서/그리고)": r"(?m)^\s*(?:<[^>]+>)*\s*(?:또한|따라서|그리고|하지만|즉|나아가)[\s,]",
}


def lexical_tells(text):
    s1 = {p: text.count(p) for p in S1_IDIOMS if p in text}
    s1_total = sum(s1.values())
    s2 = {name: len(re.findall(rx, text)) for name, rx in S2_PATTERNS.items()}
    s2 = {k: v for k, v in s2.items() if v}
    mech = sum(1 for w in ("첫째", "둘째", "셋째", "넷째") if w in text)  # 기계적 병렬
    return {"s1": s1, "s1_total": s1_total, "s2": s2,
            "s2_total": sum(s2.values()), "mechanical_list": mech}


def score(text):
    import metrics_v2
    from prepare_monolith_input import compute_route_hint
    m = metrics_v2.compute_all_v2(text, genre="blog")
    m.update(compute_route_hint(m))
    m["lexical_tells"] = lexical_tells(text)
    return m


def main():
    drafts = [d for d in sorted(glob.glob("drafts/*.md")) if not d.endswith(".gitkeep")]
    if not drafts:
        print("게이트: 처리할 초안 없음")
        return
    for path in drafts:
        try:
            txt = open(path, encoding="utf-8").read()
            mm = re.match(r"^---\n(.*?)\n---\n(.*)$", txt, re.S)
            body = mm.group(2) if mm else txt
            plain = strip_html(body)
            m = score(plain)
            hint = m.get("route_hint", "?")
            iv = (m.get("v2_interference_index") or {}).get("weighted_total")
            iv_s = f"{iv:.2f}" if isinstance(iv, (int, float)) else "?"
            lt = m["lexical_tells"]
            print(f"[{os.path.basename(path)}] route_hint={hint} 간섭지수={iv_s} | "
                  f"S1관용구={lt['s1_total']} S2번역투={lt['s2_total']} 기계적병렬={lt['mechanical_list']}")
            if lt["s1"]:
                print(f"    S1(무조건 제거): {lt['s1']}")
            if lt["s2"]:
                print(f"    S2(반복 시 제거): {lt['s2']}")
            # 게이트 판정: S1 관용구 1개↑ · 기계적 병렬 3개↑ · S2 6개↑ · route heavy → 경고
            hit = (lt["s1_total"] >= 1 or lt["mechanical_list"] >= 3
                   or lt["s2_total"] >= 6 or hint == "heavy")
            if hit:
                print(f"::warning file={path}::AI 티 감지 "
                      f"(S1={lt['s1_total']} 병렬={lt['mechanical_list']} S2={lt['s2_total']} route={hint}) "
                      f"— 발행 전 /humanize-korean 으로 윤문 권장")
        except Exception as e:
            print(f"::warning file={path}::humanize 게이트 스코어 실패(건너뜀) — {e}")


if __name__ == "__main__":
    main()
