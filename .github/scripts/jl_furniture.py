# 글 공통 '가구' — 목차(TOC) + 하단 편집자(운영자) 박스.
# site_structure.py(기존 글 일괄 적용), publish_draft.py(새 글), apply_revisions.py(수정본)가 공유한다.
# 마커(<!--jl-toc-->…<!--/jl-toc-->, <!--jl-editor-->…<!--/jl-editor-->)로 감싸 멱등:
# 이미 들어간 글에 다시 돌리면 기존 블록을 지우고 새로 넣는다(문구 수정도 일괄 반영 가능).
# 워드프레스 wpautop가 깨뜨리지 않게 각 블록은 빈 줄 없는 한 줄 HTML로 넣는다.
import re, html

OWNER = "제이"
EDITOR_URL = "https://jaylog.co.kr/editor/"
POLICY_URL = "https://jaylog.co.kr/editorial-policy/"
CONTACT_URL = "https://jaylog.co.kr/contact/"

TOC_RE = re.compile(r"\n?<!--jl-toc-->.*?<!--/jl-toc-->\n?", re.S)
EDITOR_RE = re.compile(r"\n?<!--jl-editor-->.*?<!--/jl-editor-->\n?", re.S)
H2_RE = re.compile(r"<h2(\s[^>]*)?>(.*?)</h2>", re.S | re.I)
SUMMARY_RE = re.compile(r'<div class="geo-summary".*?</div>', re.S)

EDITOR_BOX = (
    '<!--jl-editor-->'
    '<aside class="jl-editor" style="margin:2.4em 0 0;padding:20px 22px;border:1px solid #e3e6ec;'
    'border-radius:14px;background:#f8f9fb;line-height:1.75;">'
    '<p style="margin:0 0 6px;font-size:13px;font-weight:700;letter-spacing:.04em;color:#6b7385;">이 글을 정리한 사람</p>'
    f'<p style="margin:0 0 8px;font-size:17px;font-weight:800;color:#1f2a44;">'
    f'<a href="{EDITOR_URL}" style="color:#1f2a44;text-decoration:none;">{OWNER}</a>'
    ' <span style="font-size:14px;font-weight:600;color:#6b7385;">· 제이로그 운영자</span></p>'
    '<p style="margin:0 0 10px;font-size:15px;color:#3a4150;">해외직구·통관 규정을 처음 직구하는 분도 따라올 수 있게 풀어 씁니다. '
    '관세율·면세 기준 같은 수치는 관세청과 법령 등 공식 자료로 확인하고, 글 안에 출처를 함께 적습니다.</p>'
    '<p style="margin:0 0 10px;font-size:14px;">'
    f'<a href="{EDITOR_URL}" style="color:#2c4a8a;font-weight:700;">운영자 소개</a> · '
    f'<a href="{POLICY_URL}" style="color:#2c4a8a;font-weight:700;">편집 원칙</a> · '
    f'<a href="{CONTACT_URL}" style="color:#2c4a8a;font-weight:700;">틀린 내용 제보하기</a></p>'
    '<p style="margin:0;font-size:13px;color:#7a8191;">규정이 바뀌거나 오류가 확인되면 본문을 고치고 수정일을 갱신합니다.</p>'
    '</aside>'
    '<!--/jl-editor-->'
)


def _plain(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def add_furniture(body, min_h2=3):
    """본문에 목차와 편집자 박스를 넣어 돌려준다(멱등).
    - h2에 id가 없으면 sec-1, sec-2… 를 붙인다(목차 앵커).
    - h2가 min_h2개 미만이면 목차는 생략(짧은 글에 목차는 군더더기).
    - 목차 위치: 상단 '한눈 요약' 박스 바로 뒤, 없으면 맨 앞.
    - 편집자 박스: 본문 맨 끝."""
    body = TOC_RE.sub("\n", body)
    body = EDITOR_RE.sub("\n", body).rstrip()

    items, n = [], 0

    def tag_h2(m):
        nonlocal n
        attrs, inner = m.group(1) or "", m.group(2)
        label = _plain(inner)
        if not label:
            return m.group(0)
        n += 1
        idm = re.search(r'\sid="([^"]+)"', attrs)
        if idm:
            hid = idm.group(1)
        else:
            hid = f"sec-{n}"
            attrs = f' id="{hid}"' + attrs
        items.append((hid, label))
        return f"<h2{attrs}>{inner}</h2>"

    body = H2_RE.sub(tag_h2, body)

    if len(items) >= min_h2:
        lis = "".join(
            f'<li style="margin:2px 0;"><a href="#{hid}" style="color:#2c4a8a;text-decoration:none;">'
            f'{html.escape(label)}</a></li>' for hid, label in items)
        toc = ('<!--jl-toc-->'
               '<nav class="jl-toc" aria-label="목차" style="margin:0 0 1.8em;padding:16px 20px;'
               'border:1px solid #e3e6ec;border-radius:12px;background:#fff;">'
               '<p style="margin:0 0 6px;font-size:15px;font-weight:800;color:#1f2a44;">이 글의 목차</p>'
               f'<ol style="margin:0;padding-left:20px;font-size:15px;line-height:1.8;">{lis}</ol>'
               '</nav>'
               '<!--/jl-toc-->')
        sm = SUMMARY_RE.search(body)
        if sm:
            body = body[:sm.end()] + "\n" + toc + "\n" + body[sm.end():].lstrip("\n")
        else:
            body = toc + "\n" + body

    return body + "\n" + EDITOR_BOX + "\n"
