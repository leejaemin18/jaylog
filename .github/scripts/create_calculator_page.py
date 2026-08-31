# 관부가세 계산기 전용 WP 페이지를 생성/갱신한다 (blog-command: create-calculator-page).
# 각 글은 인라인 계산기 대신 이 페이지로 버튼 링크 → 중복 위젯 복붙 신호 제거(애드센스 대응).
# 페이지 자체도 설명을 충분히 넣어 '얇은 페이지'가 되지 않게 한다.
# 결과 링크/ID를 review/calc-page.txt 에 기록(다른 세션이 링크를 알 수 있게).
import os, json, base64, re, urllib.request

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
BASE = "https://jaylog.co.kr/wp-json/wp/v2"
SLUG = "gwanbuga-calculator"

WIDGET = open("assets/tax-calculator.html", encoding="utf-8").read()

INTRO = (
    '<p>해외직구를 하다 보면 가장 먼저 궁금한 것이 "이거 세금 얼마나 나올까?"입니다. '
    '아래 계산기에 물품 가격·배송비·환율만 넣으면 예상 관세와 부가세를 바로 보여드립니다. '
    '발송 국가와 품목만 정확히 고르면 됩니다. (2026년 기준)</p>\n'
)

HOWTO = (
    '<h2 class="wp-block-heading">계산 결과, 이렇게 읽으세요</h2>\n'
    '<p>계산기는 <strong>면세 여부부터</strong> 판정합니다. 미국에서 오는 일반 물품은 200달러, '
    '그 밖의 나라나 목록통관이 안 되는 품목(건강기능식품·화장품 등)은 150달러가 기준입니다. '
    '이 금액을 넘으면 <strong>초과분이 아니라 전체 금액</strong>에 관세가 붙고, '
    '여기에 다시 부가세 10%가 더해집니다. 이 구조를 자세히 알고 싶으면 '
    '<a href="https://jaylog.co.kr/?p=27">관부가세 계산법 완벽 정리</a>를, '
    '면세 기준이 왜 나라마다 다른지는 '
    '<a href="https://jaylog.co.kr/?p=19">관세 면제 기준 150달러</a>를 참고하세요.</p>\n'
    '<h2 class="wp-block-heading">계산기 숫자와 실제 고지액이 다를 수 있는 이유</h2>\n'
    '<p>이 계산기는 품목별 대표 세율로 계산합니다. 실제 세액은 세관이 매기는 '
    '정확한 품목분류(HS코드)와 신고 시점 환율(관세청 고시환율)에 따라 조금 달라질 수 있습니다. '
    '큰 금액을 앞두고 있다면 계산기로 대략을 잡은 뒤, '
    '<a href="https://www.customs.go.kr" target="_blank" rel="noopener">관세청</a> 예상세액 조회나 '
    '국번없이 125로 최종 확인하는 것을 권합니다.</p>\n'
    '<h2 class="wp-block-heading">세금 말고 통관 자체가 궁금하다면</h2>\n'
    '<p>전파인증에 걸리는지, 목록통관이 되는지, 수량 한도나 검역은 없는지 등 '
    '세금 외의 통관 걸림돌까지 한 번에 확인하려면 '
    '<a href="https://jaylog.co.kr/customs-wizard/"><strong>직구 통관 종합 진단</strong></a>을 이용해 보세요. '
    '나라·품목·금액만 고르면 면세 여부부터 인증·검역·개별소비세·합산과세까지 근거와 함께 짚어 드립니다.</p>\n'
)

CONTENT = INTRO + WIDGET + "\n" + HOWTO


def wp(path, method="GET", data=None):
    req = urllib.request.Request(
        BASE + path, method=method,
        headers={"Authorization": "Basic " + AUTH, "Content-Type": "application/json"},
        data=json.dumps(data).encode() if data else None)
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.load(res)


def main():
    existing = wp(f"/pages?slug={SLUG}&status=publish,draft&_fields=id")
    payload = {"title": "관부가세 계산기 — 해외직구 예상 세금 바로 계산",
               "slug": SLUG, "status": "publish", "content": CONTENT}
    if existing:
        pid = existing[0]["id"]
        r = wp(f"/pages/{pid}", "POST", payload)
        print(f"♻️ 계산기 페이지 갱신: id {pid}")
    else:
        r = wp("/pages", "POST", payload)
        print(f"✅ 계산기 페이지 생성: id {r['id']}")
    link = r["link"]
    pid = r["id"]
    stable = f"https://jaylog.co.kr/?page_id={pid}"
    os.makedirs("review", exist_ok=True)
    with open("review/calc-page.txt", "w", encoding="utf-8") as f:
        f.write(f"id={pid}\nlink={link}\nstable={stable}\n")
    print(f"링크: {link}\n안정링크: {stable}")


if __name__ == "__main__":
    main()
