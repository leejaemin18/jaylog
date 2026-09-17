# 글별 Rank Math 포커스 키워드를 설정 시도 + 저장 여부 검증 (blog-command의 set-focus 명령).
# 제목의 특징 문구로 글을 식별해 2~3단어 포커스 키워드를 매핑한다(id 하드코딩 X → 안정적).
# Rank Math 메타가 REST로 안 먹히면(되읽기 빈값) 매핑 표를 출력해 수동 입력하게 한다.
import os, json, base64, urllib.request

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
API = "https://jaylog.co.kr/wp-json/wp/v2"

# post id → 포커스 키워드 (정확 매핑, 최우선). 제목 조각 겹침을 피하려 id 기준으로 관리.
ID_MAP = {
    # 초기 글(REST 직접 발행)
    "19": "해외직구 관세 면제", "23": "목록통관 일반통관", "27": "관부가세 계산",
    "28": "개인통관고유부호", "32": "해외직구 합산과세", "40": "통관 배송조회",
    "41": "세관 검사 대상", "42": "HS코드 관세", "44": "전자제품 직구 전파인증",
    "53": "여행자 휴대품 면세", "55": "골프채 직구 관세", "56": "명품 가방 직구",
    "58": "안마의자 직구",
    # drafts 파이프라인 발행 글
    "80": "골프 거리측정기 직구", "92": "통관 지연", "95": "통관 보류",
    "98": "관세 납부 문자", "252": "유니패스 조회", "277": "배송대행지",
    "281": "해외직구 사기", "284": "과오납 환급", "317": "관부가세 포함",
    "321": "예상세액 조회", "325": "개인통관고유부호", "330": "구매대행",
    "333": "언더밸류", "337": "직배송 배대지", "340": "일본직구",
    "343": "중국직구", "351": "쿠팡 로켓직구", "390": "피규어 직구",
    "394": "화장품 직구", "398": "유니패스", "409": "게임기 직구",
    "415": "해외원화결제", "422": "아마존 직구", "428": "직구 통관검사",
    "443": "영양제 직구", "449": "유럽 직구", "458": "의류 직구",
    "532": "특송 관세", "540": "유아용품 직구", "554": "블랙프라이데이 직구",
    "567": "직구 사이즈", "581": "개인통관고유부호", "597": "해외 선물 관세",
    "610": "직구 관세 납부", "624": "직구 파손", "640": "직구 통관 용어",
    "655": "직구 배송기간", "669": "위스키 직구 세금", "696": "해외직구 합산과세",
    "710": "개인통관고유부호", "939": "직구 반품", "946": "해외직구 영양제",
    "956": "가전 직구", "969": "알리 테무 직구",
}

# (제목에 들어있는 특징 문구, 포커스 키워드) — ID_MAP에 없을 때 폴백. 위에서부터 첫 매칭.
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
    ("통관중", "해외직구 통관 지연"),
    ("통관 보류", "통관 보류"),
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
        kw = ID_MAP.get(str(p["id"])) or pick(title)
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
