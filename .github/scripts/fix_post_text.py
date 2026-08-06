# 등록된 글의 본문 문구를 교정하는 스크립트 (blog-command의 fix-posts 명령).
# FIXES에 글 id → [(찾을 문구, 바꿀 문구)] 를 적고 실행하면 해당 글만 수정된다.
# 교정 이력은 이 파일의 git 히스토리가 그대로 기록이 된다.
import os, json, base64, urllib.request

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
API = "https://jaylog.co.kr/wp-json/wp/v2"

FIXES = {
    95: [  # 통관 보류 글 — 실존 인물처럼 읽히는 사례를 가상 예시 화법으로 교정 (2026-08-06 수칙 반영)
        (
            "<p>실제 사례를 하나 보겠습니다. 60대 김 씨는 미국 사이트에서 25만 원짜리 등산화를 샀는데 판매자가 인보이스에 'shoes $50'라고만 적어 보냈습니다. 세관은 가격이 의심된다며 보류를 걸었고, 김 씨는 카드 승인 문자와 주문 화면을 특송업체에 보냈습니다. 결제액 기준으로 세금을 내고 사흘 뒤 통관이 풀렸습니다. 여기서 교훈은 두 가지입니다. 판매자의 엉터리 신고는 내 잘못이 아니어도 내 시간을 뺏고, <strong>실제 결제 증빙만 있으면 반드시 풀린다</strong>는 것입니다.</p>",
            "<p>예를 들어 이런 경우를 보겠습니다. 미국 사이트에서 25만 원짜리 등산화를 샀는데 판매자가 인보이스에 'shoes $50'라고만 적어 보냈다고 해보지요. 세관은 가격이 의심된다며 보류를 걸고, 구매자가 카드 승인 문자와 주문 화면을 특송업체에 보내면 결제액 기준으로 세금을 낸 뒤 며칠 안에 통관이 풀리는 식입니다. 여기서 교훈은 두 가지입니다. 판매자의 엉터리 신고는 내 잘못이 아니어도 내 시간을 뺏고, <strong>실제 결제 증빙만 있으면 풀린다</strong>는 것입니다.</p>",
        ),
    ],
}


def wp(path, method="GET", data=None):
    req = urllib.request.Request(
        API + path, method=method,
        headers={"Authorization": "Basic " + AUTH, "Content-Type": "application/json"},
        data=json.dumps(data).encode() if data else None)
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.load(res)


def main():
    for pid, pairs in FIXES.items():
        p = wp(f"/posts/{pid}?context=edit&_fields=id,title,content")
        raw = p["content"]["raw"]
        changed = 0
        for old, new in pairs:
            if old in raw:
                raw = raw.replace(old, new, 1)
                changed += 1
            else:
                print(f"::warning::id {pid}: 찾을 문구가 본문에 없음 (이미 수정됐거나 문구 불일치)")
        if changed:
            wp(f"/posts/{pid}", "POST", {"content": raw})
            print(f"✏️ 교정 완료: id {pid} | {p['title']['raw'][:30]} ({changed}건)")
        else:
            print(f"변경 없음: id {pid}")


if __name__ == "__main__":
    main()
