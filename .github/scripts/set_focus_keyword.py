# 글별 Rank Math 포커스 키워드를 설정 시도 + 저장 여부 검증 (blog-command의 set-focus 명령).
# 제목의 특징 문구로 글을 식별해 2~3단어 포커스 키워드를 매핑한다(id 하드코딩 X → 안정적).
# Rank Math 메타가 REST로 안 먹히면(되읽기 빈값) 매핑 표를 출력해 수동 입력하게 한다.
import os, json, base64, urllib.request

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
API = "https://jaylog.co.kr/wp-json/wp/v2"

# (제목에 들어있는 특징 문구, 포커스 키워드) — 위에서부터 첫 매칭
RULES = [
    ("150달러", "해외직구 관세 면제"),
    ("목록통관", "목록통관 일반통관"),
    ("관부가세 계산", "관부가세 계산"),
    ("개인통관고유부호", "개인통관고유부호"),
    ("합산과세", "해외직구 합산과세"),
    ("HS코드", "HS코드 관세"),
    ("배송조회", "통관 배송조회"),
    ("세관 검사", "세관 검사 대상"),
    ("건강기능식품", "건강기능식품 직구"),
    ("전파인증(KC)", "전자제품 직구 전파인증"),
    ("여행", "여행자 휴대품 면세"),
    ("골프채", "골프채 직구 관세"),
    ("안마의자", "안마의자 직구"),
    ("골프 거리측정기", "골프 거리측정기 직구"),
    ("명품 가방", "명품 가방 직구"),
    ("처방약", "해외 의약품 직구"),
    ("통관중", "해외직구 통관 지연"),
    ("통관 보류", "통관 보류"),
    ("관세 내라는 문자", "관세 납부 방법"),
]


def wp(path, method="GET", data=None):
    req = urllib.request.Request(
        API + path, method=method,
        headers={"Authorization": "Basic " + AUTH, "Content-Type": "application/json"},
        data=json.dumps(data).encode() if data else None)
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.load(res)


def pick(title):
    for frag, kw in RULES:
        if frag in title:
            return kw
    return None


def main():
    posts = []
    for status in ("publish", "future"):
        posts += wp(f"/posts?status={status}&per_page=100&_fields=id,title")
    ok = fail = nomatch = 0
    table = []
    for p in posts:
        title = p["title"]["rendered"]
        kw = pick(title)
        if not kw:
            nomatch += 1
            print(f"::warning::매칭 안 됨: id {p['id']} | {title[:35]}")
            continue
        table.append((p["id"], kw, title[:34]))
        try:
            wp(f"/posts/{p['id']}", "POST", {"meta": {"rank_math_focus_keyword": kw}})
            back = wp(f"/posts/{p['id']}?_fields=meta").get("meta", {})
            saved = back.get("rank_math_focus_keyword", "")
            if saved == kw:
                ok += 1
                print(f"✅ 설정됨: id {p['id']} | {kw}")
            else:
                fail += 1
                print(f"⚠️ 저장 안 됨(REST 미지원): id {p['id']} | 설정하려던 값: {kw}")
        except Exception as e:
            fail += 1
            print(f"⚠️ 오류: id {p['id']} | {kw} | {e}")
    print(f"\n완료: 자동설정 {ok} / 실패 {fail} / 매칭없음 {nomatch}")
    if fail:
        print("\n===== 수동 입력용 표 (id | 포커스 키워드 | 제목) =====")
        for pid, kw, t in table:
            print(f"{pid} | {kw} | {t}")


if __name__ == "__main__":
    main()
