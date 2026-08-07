# 애드센스 신뢰 페이지(소개·문의·면책고지)를 워드프레스에 생성하는 스크립트.
# blog-command의 create-pages 명령이 실행. 같은 슬러그 페이지가 있으면 건너뜀.
import os, json, base64, urllib.request

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
API = "https://jaylog.co.kr/wp-json/wp/v2"
EMAIL = "leejaemin18@gmail.com"

PAGES = [
    {
        "slug": "about",
        "title": "제이로그 소개",
        "content": f"""
<p>제이로그는 <strong>해외직구와 수입 통관</strong>을 쉽게 풀어 설명하는 정보 블로그입니다. 관세가 얼마나 나오는지, 통관은 왜 멈췄는지, 어떤 물건은 몇 개까지 들여올 수 있는지 — 직구할 때마다 헷갈리는 문제들을 한국 규정 기준으로 정리합니다.</p>

<h2 class="wp-block-heading">누가 운영하나요</h2>
<p>운영자 <strong>제이(Jay)</strong>는 국제물류 업계에서 일하며 수입 화물과 통관 현장을 가까이에서 접하고 있습니다. 일하면서 "이건 다들 모르고 손해 보는구나" 싶었던 것들을 일반 소비자의 눈높이로 정리하는 것이 이 블로그의 출발점입니다.</p>

<h2 class="wp-block-heading">무엇을 다루나요</h2>
<ul>
<li>해외직구 관세·부가세 기준과 계산 방법 (글마다 간단 계산기 제공)</li>
<li>통관 절차, 지연·보류 등 문제 상황별 대처법</li>
<li>건강기능식품·전자제품·명품 등 품목별 반입 규정</li>
<li>세관 사칭 사기 등 소비자 보호 정보</li>
</ul>

<h2 class="wp-block-heading">편집 원칙</h2>
<ul>
<li>관세율·면세기준 등 수치는 관세청 등 공식 출처를 기준으로 하고, 기준 연도를 글에 명시합니다.</li>
<li>규정이 바뀌면 기존 글도 확인하여 수정합니다. 모든 글에는 발행일과 수정일이 표시됩니다.</li>
<li>과장·낚시성 표현을 쓰지 않고, 확인되지 않은 정보는 싣지 않습니다.</li>
<li>본 블로그의 글은 일반 정보 제공 목적이며, 개별 사안은 관세청(국번없이 125) 또는 관세사 상담을 권합니다.</li>
</ul>

<p>내용 오류 제보나 궁금한 주제 제안은 언제든 <a href="/contact/">문의하기</a>로 보내주세요. 블로그를 더 정확하게 만드는 데 큰 도움이 됩니다.</p>
""",
    },
    {
        "slug": "contact",
        "title": "문의하기",
        "content": f"""
<p>제이로그에 궁금한 점, 글 내용의 오류 제보, 다뤄줬으면 하는 주제 제안을 환영합니다.</p>

<h2 class="wp-block-heading">이메일 문의</h2>
<p>아래 주소로 보내주시면 확인 후 답변드립니다. (보통 2~3일 이내)</p>
<p><strong>📧 {EMAIL}</strong></p>

<h2 class="wp-block-heading">이런 문의를 받습니다</h2>
<ul>
<li>글 내용 중 잘못된 정보나 바뀐 규정 제보</li>
<li>다뤄줬으면 하는 직구·통관 주제 제안</li>
<li>제휴·광고 관련 문의</li>
</ul>

<p>※ 개별 통관 건에 대한 상담은 관세청 고객센터(국번없이 125) 또는 관세사를 통하시는 것이 정확하고 빠릅니다. 블로그 문의로는 일반적인 정보 안내만 가능한 점 양해 부탁드립니다.</p>
""",
    },
    {
        "slug": "disclaimer",
        "title": "면책고지",
        "content": """
<p>제이로그(jaylog.co.kr)의 모든 콘텐츠는 일반 정보 제공을 목적으로 작성되었습니다. 이용에 앞서 아래 내용을 확인해 주세요.</p>

<h2 class="wp-block-heading">정보의 성격</h2>
<p>본 블로그의 글은 작성 시점의 공개된 규정과 자료를 바탕으로 하며, 법률·세무 자문이 아닙니다. 관세율, 면세 기준, 통관 요건 등은 법령 개정에 따라 변경될 수 있으며, 블로그는 이를 순차적으로 반영하지만 항상 최신 상태임을 보장하지는 않습니다.</p>

<h2 class="wp-block-heading">책임의 한계</h2>
<p>개별 수입 건의 세액과 통관 가능 여부는 물품, 신고 내용, 세관 판단에 따라 달라질 수 있습니다. 본 블로그의 정보(간이 계산기 결과 포함)를 근거로 한 의사결정의 결과에 대해 운영자는 법적 책임을 지지 않습니다. 중요한 사안은 반드시 관세청(국번없이 125) 또는 관세사를 통해 확인하시기 바랍니다.</p>

<h2 class="wp-block-heading">외부 링크와 광고</h2>
<p>본 블로그는 공식 기관 사이트 등 외부 링크를 포함할 수 있으며, 링크된 사이트의 내용에 대해서는 책임지지 않습니다. 향후 광고가 게재되는 경우, 광고는 콘텐츠의 편집 방향에 영향을 주지 않습니다.</p>

<h2 class="wp-block-heading">저작권</h2>
<p>본 블로그의 글과 이미지는 저작권의 보호를 받습니다. 출처를 밝힌 부분 인용은 가능하지만, 전문 복제·재게시는 허용하지 않습니다.</p>
""",
    },
]


def wp(path, method="GET", data=None):
    req = urllib.request.Request(
        API + path, method=method,
        headers={"Authorization": "Basic " + AUTH, "Content-Type": "application/json"},
        data=json.dumps(data).encode() if data else None)
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.load(res)


def main():
    existing = {p["slug"] for p in wp("/pages?per_page=100&_fields=slug&status=publish,draft")}
    for page in PAGES:
        if page["slug"] in existing:
            print(f"이미 있음: /{page['slug']}/ — 건너뜀")
            continue
        r = wp("/pages", "POST", {
            "title": page["title"], "slug": page["slug"],
            "content": page["content"].strip(), "status": "publish",
        })
        print(f"✅ 페이지 생성: {r['title']['rendered']} → {r['link']}")


if __name__ == "__main__":
    main()
