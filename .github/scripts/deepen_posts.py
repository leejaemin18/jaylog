# 얇은 글에 중복 없는 실용 섹션을 삽입해 깊이를 더한다 (blog-command: deepen-posts).
# 통째 재작성이 아니라 섹션만 추가 → 기존 이미지·FAQ·도구박스 보존. 멱등(글별 마커).
import os, re, json, base64, urllib.request

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
API = "https://jaylog.co.kr/wp-json/wp/v2"

H2S = ('<h2 class="wp-block-heading" style="font-size:1.4em;font-weight:800;color:#33352f;'
       'margin:2.1em 0 .7em;line-height:1.5;"><span style="background:linear-gradient('
       'transparent 60%,#ffe89e 60%);padding:0 3px;">{t}</span></h2>')
H2P = '<h2 class="wp-block-heading">{t}</h2>'

SECTIONS = {
 409: '<!--deep-409-->\n' + H2S.format(t="사놓고 못 쓰는 실수 — 전압·플러그·지역") +
   '<p style="line-height:1.85;">세금과 전파인증을 통과해도, 막상 받고 나서 못 쓰면 소용없습니다. 게임기 직구에서 실제로 당황하는 지점을 짚어둘게요.</p>'
   '<ul>'
   '<li><strong>전압·플러그</strong> — 플레이스테이션5는 100~240V 프리볼트라 전압은 문제없지만, 미국판은 미국식 플러그라 <strong>변환 어댑터</strong>가 필요합니다. 닌텐도 스위치 어댑터도 대부분 프리볼트지만 구형·서드파티 제품은 표기를 꼭 확인하세요.</li>'
   '<li><strong>지역·언어</strong> — 스위치는 지역락이 없어 미국판·일본판 모두 한글 지원 게임을 구동할 수 있지만, eShop 구매는 계정 지역을 따릅니다. 플스5도 디스크는 사실상 지역 제한이 없으나 일부 콘텐츠·결제는 계정 지역 기준입니다.</li>'
   '<li><strong>정식 A/S</strong> — 해외판은 국내 공식 A/S가 제한될 수 있어, 고장 시 자가 부담이나 해외 발송이 필요할 수 있습니다.</li>'
   '</ul>\n',
 394: '<!--deep-394-->\n' + H2P.format(t="직구 화장품, 통관됐다고 안심은 금물") +
   '<p>수량 기준을 지켜 통관이 됐더라도, 직구 화장품은 정식 수입 화장품과 성격이 다릅니다. 몇 가지는 미리 알아두는 게 좋아요.</p>'
   '<ul>'
   '<li><strong>안전·표시 검증을 거치지 않습니다</strong> — 정식 수입품과 달리 국내 표시기준·안전성 확인 절차를 거치지 않으므로, 성분과 유통기한은 스스로 확인해야 합니다.</li>'
   '<li><strong>기능성 화장품도 소량만</strong> — 미백·주름개선·자외선차단 같은 기능성 제품도 자가사용 소량은 통관되지만, 판매하거나 수량이 많으면 정식 수입 대상이 됩니다.</li>'
   '<li><strong>여러 브랜드 대량 구매는 오해받기 쉽습니다</strong> — 색조·스킨케어를 브랜드별로 잔뜩 담으면 판매 목적으로 보여 통관이 보류될 수 있습니다.</li>'
   '<li><strong>향수 외 인화성 품목</strong> — 네일 리무버, 일부 헤어·바디 스프레이도 인화성으로 분류돼 항공 배송이 제한될 수 있습니다.</li>'
   '</ul>\n',
 390: '<!--deep-390-->\n' + H2P.format(t="피규어 직구의 진짜 복병 — 부피 배송비와 파손") +
   '<p>세금 계산만큼 신경 써야 할 게 배송입니다. 피규어·프라모델은 특성상 여기서 예상 밖 비용이 생기기 쉬워요.</p>'
   '<ul>'
   '<li><strong>부피무게로 배송비가 뜁니다</strong> — 큰 상자는 실제 무게가 아니라 부피무게로 요금이 매겨져, 국제배송비가 물품값에 육박하기도 합니다. 이 배송비는 면세 판단에는 빠지지만, 과세 대상이 되면 과세가격에 포함돼 세금을 키웁니다.</li>'
   '<li><strong>대형 스케일은 배송비만 수만 원대</strong> — 1/4 스케일 등 대형 제품은 배송비만으로도 부담이 커, 총비용을 미리 계산해 보는 게 좋습니다.</li>'
   '<li><strong>파손 대비</strong> — 배송 중 파손이 잦은 품목이라, 배송대행지 검수·추가 완충·보험 옵션을 확인해 두세요.</li>'
   '<li><strong>예약판매(프리오더) 주의</strong> — 결제와 실제 발송 시점이 몇 달 차이 나면, 통관은 <strong>발송 시점</strong>의 환율과 규정을 따릅니다.</li>'
   '</ul>\n',
}


def wp(path, method="GET", data=None):
    req = urllib.request.Request(
        API + path, method=method,
        headers={"Authorization": "Basic " + AUTH, "Content-Type": "application/json"},
        data=json.dumps(data).encode() if data else None)
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.load(res)


def main():
    for pid, sec in SECTIONS.items():
        try:
            p = wp(f"/posts/{pid}?context=edit&_fields=id,content")
            raw = p["content"]["raw"]
            if f"<!--deep-{pid}-->" in raw:
                print(f"건너뜀 {pid}: 이미 심화됨"); continue
            if "<!--jaylog-tools-->" in raw:
                new = raw.replace("<!--jaylog-tools-->", sec + "<!--jaylog-tools-->", 1)
            else:
                m = re.search(r'<h2[^>]*>\s*자주 묻는 질문', raw)
                pos = m.start() if m else len(raw)
                new = raw[:pos] + sec + raw[pos:]
            wp(f"/posts/{pid}", "POST", {"content": new})
            print(f"✅ 심화 삽입: {pid}")
        except Exception as e:
            print(f"::warning::{pid} 실패 — {e}")


if __name__ == "__main__":
    main()
