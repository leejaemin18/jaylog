# 직구 통관 진단 마법사 전용 WP 페이지 생성/갱신 (blog-command: create-wizard-page).
# 나라·품목·금액을 고르면 면세 여부·인증/검역 리스크·통관 유형·주의점을 한 번에 진단하고
# 관련 심화글로 연결하는 인터랙티브 도구 — 다른 직구 블로그에 없는 독자 가치 자산(애드센스 저가치 대응).
# 결과 링크/ID를 review/wizard-page.txt 에 기록.
import os, json, base64, urllib.request

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
BASE = "https://jaylog.co.kr/wp-json/wp/v2"
SLUG = "customs-wizard"

WIDGET = open("assets/customs-wizard.html", encoding="utf-8").read()

INTRO = (
    '<p>해외직구를 하다 보면 “이거 세금은 얼마지?”뿐 아니라 “전파인증에 걸리진 않을까?”, '
    '“이 품목은 목록통관이 되나?”, “통관부호는 꼭 있어야 하나?”처럼 궁금한 게 한둘이 아닙니다. '
    '아래 진단 도구에 <strong>어디서 오는지·무슨 품목인지·얼마짜리인지</strong>만 고르면, '
    '면세 여부부터 인증·검역 걸림 여부, 통관 유형, 놓치기 쉬운 주의점까지 한 번에 짚어 드립니다. (2026년 기준)</p>\n'
)

HOWTO = (
    '<h2 class="wp-block-heading">이 진단 도구가 확인해 주는 것</h2>\n'
    '<ul>\n'
    '<li><strong>면세·과세 판정</strong> — 발송 방식(미국 특송·국제우편·그 밖의 나라)과 품목에 따라 '
    '150달러/200달러 기준을 자동으로 적용하고, 넘으면 예상 세금까지 계산합니다.</li>\n'
    '<li><strong>인증·검역 리스크</strong> — 무선기기 전파인증(KC), 건강기능식품 수량 한도, '
    '화장품·향수 규정, 전기제품 안전기준, 식품 검역처럼 품목별로 걸릴 수 있는 지점을 미리 알려줍니다.</li>\n'
    '<li><strong>통관 유형·통관부호·합산과세</strong> — 목록통관인지 일반통관인지, 개인통관고유부호가 필요한지, '
    '같은 날 여러 건이 합산과세되는지까지 함께 확인합니다.</li>\n'
    '</ul>\n'
    '<h2 class="wp-block-heading">면세 기준이 헷갈리는 이유 — 한 장으로 정리</h2>\n'
    '<p>같은 물건이라도 <strong>어느 나라에서, 어떤 방법으로, 무슨 품목으로</strong> 들어오느냐에 따라 '
    '면세 기준이 달라집니다. 미국에서 특송으로 오는 자가사용 물품만 한미 FTA 특례로 200달러까지 면세이고, '
    '그 밖에는 모두 150달러가 기준입니다. 다만 미국발이라도 건강기능식품·식품·화장품처럼 '
    '목록통관이 안 되는 품목은 150달러로 내려갑니다.</p>\n'
    '<div style="overflow-x:auto;margin:1.2em 0;">'
    '<table style="width:100%;border-collapse:collapse;font-size:15px;">'
    '<thead><tr style="background:#f3ead2;color:#6b5320;">'
    '<th style="padding:10px 12px;text-align:left;">상황</th><th style="padding:10px 12px;text-align:left;">면세 기준</th></tr></thead>'
    '<tbody>'
    '<tr><td style="padding:9px 12px;border-top:1px solid #eee;">미국발 · 특송 · 목록통관 품목</td><td style="padding:9px 12px;border-top:1px solid #eee;"><strong>200달러</strong></td></tr>'
    '<tr><td style="padding:9px 12px;border-top:1px solid #eee;">미국발 · 국제우편(EMS)</td><td style="padding:9px 12px;border-top:1px solid #eee;">150달러</td></tr>'
    '<tr><td style="padding:9px 12px;border-top:1px solid #eee;">미국발이지만 건기식·식품 등 목록통관 배제</td><td style="padding:9px 12px;border-top:1px solid #eee;">150달러</td></tr>'
    '<tr><td style="padding:9px 12px;border-top:1px solid #eee;">중국·일본·유럽 등 그 밖의 나라</td><td style="padding:9px 12px;border-top:1px solid #eee;">150달러</td></tr>'
    '</tbody></table></div>\n'
    '<p>정확한 세액이 궁금하면 <a href="https://jaylog.co.kr/gwanbuga-calculator/">관부가세 계산기</a>로 '
    '금액을 넣어 계산하고, 면세 기준의 자세한 배경은 '
    '<a href="https://jaylog.co.kr/?p=19">관세 면제 기준 150달러·미국 200달러</a>에서 확인하세요.</p>\n'
    '<h2 class="wp-block-heading">진단 결과와 실제 통관이 다를 수 있는 이유</h2>\n'
    '<p>이 도구는 대표 기준으로 방향을 잡아 주는 참고용입니다. 실제 세액과 통관 처리는 세관이 매기는 '
    '품목분류(HS코드), 신고 시점의 고시환율, 수량·성분에 따라 달라질 수 있습니다. 큰 금액이거나 애매한 품목이면 '
    '<a href="https://www.customs.go.kr" target="_blank" rel="noopener">관세청</a> 예상세액 조회나 '
    '국번없이 125로 최종 확인하시길 권합니다.</p>\n'
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
    payload = {"title": "직구 통관 진단 — 면세·인증·통관 한 번에 확인",
               "slug": SLUG, "status": "publish", "content": CONTENT}
    if existing:
        pid = existing[0]["id"]
        r = wp(f"/pages/{pid}", "POST", payload)
        print(f"♻️ 진단 마법사 페이지 갱신: id {pid}")
    else:
        r = wp("/pages", "POST", payload)
        print(f"✅ 진단 마법사 페이지 생성: id {r['id']}")
    link = r["link"]
    pid = r["id"]
    stable = f"https://jaylog.co.kr/?page_id={pid}"
    os.makedirs("review", exist_ok=True)
    with open("review/wizard-page.txt", "w", encoding="utf-8") as f:
        f.write(f"id={pid}\nlink={link}\nstable={stable}\n")
    print(f"링크: {link}\n안정링크: {stable}")


if __name__ == "__main__":
    main()
