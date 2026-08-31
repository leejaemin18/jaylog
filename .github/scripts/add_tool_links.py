# 전 글에 '관련 도구'(진단·계산기) 박스를 삽입 (blog-command: add-tool-links).
# 흩어진 글들을 도구와 연결해 하나의 레퍼런스 시스템으로 → 도어웨이/쿠키커터 인상 완화(애드센스).
# 주제별로 안내 문구·버튼 순서를 다르게 해 획일감을 피하고, 멱등(마커로 중복 방지).
import os, re, json, base64, html, urllib.request

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
API = "https://jaylog.co.kr/wp-json/wp/v2"
MARK = "<!--jaylog-tools-->"
WIZ = "https://jaylog.co.kr/customs-wizard/"
CALC = "https://jaylog.co.kr/gwanbuga-calculator/"

BTN_WIZ = (f'<a href="{WIZ}" style="display:inline-block;padding:11px 20px;border-radius:10px;'
           'background:linear-gradient(135deg,#c9a44a,#e8c56f);color:#16233f;font-weight:700;'
           'font-size:14.5px;text-decoration:none;">🧭 통관 진단</a>')
BTN_CALC = (f'<a href="{CALC}" style="display:inline-block;padding:11px 20px;border-radius:10px;'
            'background:#fff;border:1px solid #c9a44a;color:#16233f;font-weight:700;'
            'font-size:14.5px;text-decoration:none;">💰 관부가세 계산기</a>')

# (카테고리별) 제목 이모지/문구/버튼순서
VARIANTS = {
    "tax":   ("💰 내 물건 세금, 바로 계산해 보세요",
              "이 글에서 다룬 세금, 내 물건 기준으로 직접 계산할 수 있어요. 면세인지 과세인지, 고가품이면 개별소비세까지 확인하세요.",
              [BTN_CALC, BTN_WIZ]),
    "cert":  ("🧭 이 품목, 통관에 걸리나 진단해 보세요",
              "전파인증·검역·수량 한도 같은 품목별 걸림돌을 내 상황에 맞춰 한 번에 확인할 수 있어요.",
              [BTN_WIZ, BTN_CALC]),
    "proc":  ("🧭 내 통관 상황, 미리 짚어보세요",
              "내 물건이 무엇에 걸릴 수 있는지, 세금은 얼마인지 결제·발송 전에 미리 진단해 보세요.",
              [BTN_WIZ, BTN_CALC]),
    "def":   ("🧭 결제 전 30초, 직접 확인해 보세요",
              "내 물건이 면세인지, 무엇에 걸리는지 도구로 먼저 확인하면 대부분의 실수를 피할 수 있어요.",
              [BTN_WIZ, BTN_CALC]),
}

CERT = ("전파인증", "인증", "건강기능식품", "건기식", "영양제", "화장품", "향수",
        "전자제품", "전자", "게임기", "플스", "스위치", "안마의자", "마사지건",
        "거리측정기", "6병")
PROC = ("통관검사", "통관중", "통관 보류", "보류", "유니패스", "조회", "배송조회",
        "배대지", "배송대행", "반출", "지연", "멈췄")
TAX = ("관세", "관부가세", "계산", "면세", "세금", "부가세", "합산과세",
       "개별소비세", "DDP", "환급", "과오납", "DCC", "간이세율", "명품", "가방", "골프채")


def wp(path, method="GET", data=None):
    req = urllib.request.Request(
        API + path, method=method,
        headers={"Authorization": "Basic " + AUTH, "Content-Type": "application/json"},
        data=json.dumps(data).encode() if data else None)
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.load(res)


def category(title):
    for k in CERT:
        if k in title:
            return "cert"
    for k in PROC:
        if k in title:
            return "proc"
    for k in TAX:
        if k in title:
            return "tax"
    return "def"


def box(cat):
    head, lead, btns = VARIANTS[cat]
    return (f'\n{MARK}\n<div style="margin:2.2em 0;padding:18px 20px;border:1px solid #e6ddc7;'
            'border-left:4px solid #c9a44a;border-radius:12px;background:#fbf8f1;">'
            f'<div style="font-weight:800;color:#16233f;font-size:16px;margin-bottom:7px;">{head}</div>'
            f'<p style="margin:0 0 13px;font-size:14.5px;color:#4a4a4a;line-height:1.7;">{lead}</p>'
            f'<div style="display:flex;flex-wrap:wrap;gap:10px;">{btns[0]}{btns[1]}</div></div>\n')


def insert_point(raw):
    # 삽입 위치: 관련글 h2 → 고지문(<em>) → FAQ h2 순으로 가장 먼저 나오는 곳 앞
    idxs = []
    for pat in (r'<h2[^>]*>\s*(?:함께 읽으면|관련 글|이어서 보면|함께 보면)',
                r'<p[^>]*>\s*<em>',
                r'<h2[^>]*>\s*자주 묻는 질문'):
        m = re.search(pat, raw)
        if m:
            idxs.append(m.start())
    return min(idxs) if idxs else len(raw)


def main():
    posts = wp("/posts?status=publish&per_page=100&context=edit&_fields=id,title,content")
    upd = skip = 0
    for p in sorted(posts, key=lambda x: x["id"]):
        raw = p["content"]["raw"]
        if MARK in raw:
            skip += 1
            continue
        title = html.unescape(p["title"]["rendered"])
        cat = category(title)
        pos = insert_point(raw)
        new = raw[:pos] + box(cat) + raw[pos:]
        wp(f"/posts/{p['id']}", "POST", {"content": new})
        upd += 1
        print(f"  [{p['id']}] {cat:4s} ← {title[:34]}")
    print(f"✅ 도구 박스 삽입: {upd}건 / 건너뜀(이미 있음): {skip}건 / 전체 {len(posts)}")


if __name__ == "__main__":
    main()
