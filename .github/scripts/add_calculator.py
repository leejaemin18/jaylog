# 글 성격에 맞게 관부가세 계산기를 정리하는 스크립트 (blog-command의 add-calculator 명령).
# - KEEP에 있는 글: 주제에 맞는 품목이 미리 선택된 계산기를 고지문 앞에 삽입 (기존 것은 교체)
# - KEEP에 없는 글: 계산기 제거 (세금 계산과 무관한 글)
import os, re, json, base64, urllib.request

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
API = "https://jaylog.co.kr/wp-json/wp/v2"
NOTICE = "<p><em>본 글은 일반 정보"
SNIPPET = open("assets/tax-calculator.html", encoding="utf-8").read()
CALC_RE = re.compile(r"\s*<!--jaylog-tax-calc-->.*?</script>", re.S)

# 품목 프리셋: 0 일반 / 1 의류·신발 / 2 가방·액세서리 / 3 건기식 / 4 화장품·향수 / 5 전자(0%) / 6 전자(8%)
KEEP = {
    19: 0,   # 150달러 면세 기준
    23: 0,   # 목록통관 vs 일반통관
    27: 0,   # 관부가세 계산법
    32: 0,   # 합산과세
    42: 0,   # HS코드
    43: 3,   # 건강기능식품 6병
    44: 6,   # 전자제품 KC
    55: 0,   # 골프채
    56: 2,   # 명품 가방
    58: 6,   # 안마의자·마사지건
    80: 6,   # 골프 거리측정기
    98: 0,   # 관세 문자·납부
    113: 0,  # 반품 관세환급
}


def wp(path, method="GET", data=None):
    req = urllib.request.Request(
        API + path, method=method,
        headers={"Authorization": "Basic " + AUTH, "Content-Type": "application/json"},
        data=json.dumps(data).encode() if data else None)
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.load(res)


def main():
    posts = []
    for status in ("publish", "future"):
        posts += wp(f"/posts?status={status}&per_page=100&context=edit&_fields=id,title,content,status")
    added = removed = kept = 0
    for p in posts:
        raw = p["content"]["raw"]
        title = p["title"]["raw"][:30]
        stripped = CALC_RE.sub("", raw)
        if p["id"] in KEEP:
            snip = SNIPPET.replace('data-preset="0"', f'data-preset="{KEEP[p["id"]]}"')
            if NOTICE in stripped:
                new = stripped.replace(NOTICE, snip + "\n" + NOTICE, 1)
            else:
                new = stripped + "\n" + snip
            if new != raw:
                wp(f"/posts/{p['id']}", "POST", {"content": new})
                added += 1
                print(f"✅ 계산기 적용(품목 {KEEP[p['id']]}): id {p['id']} | {title}")
            else:
                kept += 1
        else:
            if stripped != raw:
                wp(f"/posts/{p['id']}", "POST", {"content": stripped})
                removed += 1
                print(f"➖ 계산기 제거: id {p['id']} | {title}")
    print(f"완료: 적용/교체 {added}건, 제거 {removed}건, 변경없음 {kept}건 / 전체 {len(posts)}건")


if __name__ == "__main__":
    main()
