# 본문 이미지가 없는 옛날 글에 이미지 1장씩 생성·삽입 (blog-command의 add-body-images 명령).
# 각 이미지 alt에 포커스 키워드 포함 → SEO '이미지 alt' 항목 충족.
# 한 글이 실패(결제한도 등)해도 나머지는 계속 진행. 이미 본문 <img> 있으면 건너뜀.
import os, re, io, json, base64, urllib.request

from PIL import Image

WP_PW = os.environ["WP_APP_PASSWORD"]
OPENAI_KEY = os.environ["OPENAI_API_KEY"]
AUTH = base64.b64encode(f"claude:{WP_PW}".encode()).decode()
API = "https://jaylog.co.kr/wp-json/wp/v2"
STYLE = ("글의 핵심을 보여주는 본문 이미지. 가로형 실사풍. 럭셔리한 다크 네이비+골드 톤, "
         "시네마틱 조명, 프리미엄 광고 품질. 텍스트는 넣지 말 것(숫자만 허용). 브랜드 로고 금지. ")

# id → (장면 묘사, alt 문장[=포커스 키워드 포함])
JOBS = {
    19: ("검은 대리석 위 황동 저울 — 한쪽엔 크래프트 택배상자, 다른쪽엔 달러 지폐 다발과 큰 금색 숫자 150.", "해외직구 관세 면제 기준 150달러를 상징하는 저울과 택배상자"),
    23: ("두 갈래로 나뉜 통로, 왼쪽은 빠른 초록 통로 오른쪽은 검사대가 있는 통로, 각 통로에 택배상자.", "목록통관과 일반통관 두 갈래를 보여주는 통관 통로"),
    27: ("고급 책상 위 계산기와 영수증, 크래프트 택배상자, 금색 동전 몇 닢.", "관부가세 계산을 상징하는 계산기와 택배상자"),
    28: ("스마트폰 화면의 본인인증 장면과 카드 형태의 개인 식별번호 카드, 옆에 택배상자.", "개인통관고유부호 발급을 상징하는 스마트폰 인증 화면"),
    32: ("같은 날 도착한 여러 개의 크래프트 택배상자가 하나의 큰 저울 위에 합쳐지는 장면.", "해외직구 합산과세를 상징하는 여러 택배상자와 저울"),
    40: ("공항 물류센터 컨베이어벨트 위를 지나는 택배상자와 단계별 체크포인트 불빛.", "통관 단계별 배송조회를 보여주는 물류 컨베이어"),
    41: ("세관 X-ray 검사대를 통과하는 크래프트 택배상자, 스캐너의 은은한 빛.", "세관 검사대를 통과하는 택배상자"),
    42: ("같은 디자인의 운동화 두 켤레에 서로 다른 코드 태그가 달려 있는 장면.", "HS코드에 따라 관세가 달라지는 물건"),
    43: ("검은 대리석 저울 위에 나란히 놓인 영양제 병 6개.", "건강기능식품 직구 6병 규정을 보여주는 영양제 병"),
    44: ("노트북과 스마트폰 옆에 금색 KC 인증 마크와 전파 신호 아이콘.", "전자제품 직구 전파인증을 상징하는 KC 마크"),
    53: ("공항 세관 신고대 위에 놓인 고급 여행가방과 면세점 쇼핑백.", "여행자 휴대품 면세를 상징하는 공항 세관대"),
    55: ("스포트라이트 아래 고급 골프 드라이버 세트와 관세 영수증.", "골프채 직구 관세를 상징하는 골프 클럽"),
    56: ("선물 리본이 달린 고급 핸드백과 그 옆의 관세 영수증.", "명품 가방 직구 선물과 관세"),
    58: ("고급 안마의자와 그 옆의 금색 KC 인증 마크, 전기 플러그.", "안마의자 직구와 전기용품 인증"),
    59: ("약병 여러 개와 처방전 서류, 뒤로 흐릿한 세관 검사대.", "해외 의약품 직구를 상징하는 약병과 처방전"),
    80: ("고급 골프 레이저 거리측정기와 GPS 시계, 금색 전파 신호 아이콘.", "골프 거리측정기 직구와 전파인증"),
}


def wp(path, method="GET", data=None, raw=None, ctype="application/json", extra=None):
    headers = {"Authorization": "Basic " + AUTH, "Content-Type": ctype}
    if extra:
        headers.update(extra)
    body = raw if raw is not None else (json.dumps(data).encode() if data else None)
    req = urllib.request.Request(API + path, method=method, headers=headers, data=body)
    with urllib.request.urlopen(req, timeout=120) as res:
        return json.load(res)


def openai_image(prompt):
    payload = {"model": "gpt-image-2", "prompt": prompt, "size": "1536x1024", "quality": "high"}
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations", method="POST",
        headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
        data=json.dumps(payload).encode())
    try:
        with urllib.request.urlopen(req, timeout=300) as res:
            out = json.load(res)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"OpenAI HTTP {e.code}: {e.read()[:200].decode('utf-8','replace')}") from None
    return base64.b64decode(out["data"][0]["b64_json"])


def insert(body, fig):
    parts = re.split(r"(?=<h2)", body)
    if len(parts) >= 3:  # 첫 섹션(도입) 다음, 두 번째 h2 앞
        return parts[0] + parts[1] + fig + "".join(parts[2:])
    m = re.search(r"</p>", body)
    return body[:m.end()] + fig + body[m.end():] if m else fig + body


def main():
    done, failed, skip = 0, [], 0
    for pid, (scene, alt) in JOBS.items():
        try:
            p = wp(f"/posts/{pid}?context=edit&_fields=id,title,content")
            raw = p["content"]["raw"]
            if "<img" in raw:
                skip += 1
                print(f"이미 이미지 있음: id {pid} — 건너뜀")
                continue
            png = openai_image(STYLE + scene)
            img = Image.open(io.BytesIO(png)).convert("RGB")
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=88, optimize=True)
            media = wp("/media", "POST", raw=buf.getvalue(), ctype="image/jpeg",
                       extra={"Content-Disposition": f'attachment; filename="post{pid}-body.jpg"'})
            # 미디어 alt 텍스트도 설정
            wp(f"/media/{media['id']}", "POST", {"alt_text": alt})
            fig = f'<figure class="wp-block-image size-large"><img src="{media["source_url"]}" alt="{alt}"/></figure>'
            wp(f"/posts/{pid}", "POST", {"content": insert(raw, fig)})
            done += 1
            print(f"🖼️ 본문이미지 추가: id {pid} | media {media['id']} | alt='{alt}'")
        except Exception as e:
            failed.append(pid)
            print(f"::warning::id {pid} 실패 — {e}")
    print(f"\n완료: 추가 {done} / 건너뜀 {skip} / 실패 {len(failed)}" + (f" {failed}" if failed else ""))
    if failed:
        print("실패분은 크레딧 확인 후 add-body-images 다시 실행하면 이어서 처리됩니다(이미 된 글은 건너뜀).")


if __name__ == "__main__":
    main()
