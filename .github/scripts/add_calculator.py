# 발행·예약된 모든 글 말미(고지문 앞)에 관부가세 계산기 위젯을 삽입하는 스크립트.
# 이미 계산기가 있는 글(마커 jaylog-tax-calc)은 건너뛴다. blog-command.yml의 add-calculator 명령이 실행.
import os, json, base64, urllib.request

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
API = "https://jaylog.co.kr/wp-json/wp/v2"
MARK = "jaylog-tax-calc"
NOTICE = "<p><em>본 글은 일반 정보"
SNIPPET = open("assets/tax-calculator.html", encoding="utf-8").read()


def wp(path, method="GET", data=None):
    req = urllib.request.Request(
        API + path, method=method,
        headers={"Authorization": "Basic " + AUTH, "Content-Type": "application/json"},
        data=json.dumps(data).encode() if data else None)
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.load(res)


def main():
    posts = []
    for status in ("publish", "future"):
        posts += wp(f"/posts?status={status}&per_page=100&context=edit&_fields=id,title,content,status")
    done = skipped = 0
    for p in posts:
        raw = p["content"]["raw"]
        title = p["title"]["raw"][:35]
        if MARK in raw:
            skipped += 1
            continue
        if NOTICE in raw:  # 고지문 바로 앞에 삽입
            new = raw.replace(NOTICE, SNIPPET + "\n" + NOTICE, 1)
        else:
            new = raw + "\n" + SNIPPET
        wp(f"/posts/{p['id']}", "POST", {"content": new})
        done += 1
        print(f"✅ 계산기 삽입: id {p['id']} ({p['status']}) | {title}")
    print(f"완료: 삽입 {done}건 / 이미 있음 {skipped}건 / 전체 {len(posts)}건")
    # 스크립트 태그가 저장 과정에서 잘려나가지 않았는지 1건 검증
    if done:
        check = wp(f"/posts?status=publish&per_page=1&_fields=id,content")[0]
        if "<script" in check["content"]["rendered"]:
            print("검증 OK: 계산기 스크립트가 본문에 살아 있음")
        else:
            print("::warning::렌더링된 본문에 <script>가 없음 — 워드프레스가 스크립트를 제거했을 수 있음. 계정 권한(unfiltered_html) 확인 필요")


if __name__ == "__main__":
    main()
