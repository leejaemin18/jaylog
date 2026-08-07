# 전 글 공통 SEO 보강 (blog-command의 seo-boost 명령).
# Rank Math '아웃바운드 링크 없음' 해결: 고지문의 '관세청'을 관세청 공식 사이트 dofollow 링크로 변환.
# 이미 customs.go.kr 링크가 있으면 건너뜀. 발행·예약 글 전체 대상.
import os, json, base64, urllib.request

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
API = "https://jaylog.co.kr/wp-json/wp/v2"
LINK = '<a href="https://www.customs.go.kr" target="_blank" rel="noopener">관세청</a>'

# 고지문에 흔히 쓰인 표기들 — 첫 매칭만 링크로 교체
PATTERNS = ["관세청(국번없이 125)", "관세청(국번 없이 125)", "관세청 125", "관세청(☎125)"]


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
        posts += wp(f"/posts?status={status}&per_page=100&context=edit&_fields=id,title,content")
    done = skip = miss = 0
    for p in posts:
        raw = p["content"]["raw"]
        title = p["title"]["raw"][:30]
        # 계산기엔 'customs.go.kr'가 '글자'로만 있음 → 진짜 <a> 링크가 있을 때만 건너뜀
        if '<a href="https://www.customs.go.kr' in raw:
            skip += 1
            continue
        new = raw
        for pat in PATTERNS:
            if pat in new:
                # '관세청' 부분만 링크로 (뒤의 (국번없이 125) 등은 유지)
                new = new.replace(pat, pat.replace("관세청", LINK, 1), 1)
                break
        if new == raw:
            # 고지문 패턴이 없으면 본문 첫 '관세청' 하나라도 링크
            if "관세청" in new:
                new = new.replace("관세청", LINK, 1)
        if new != raw:
            wp(f"/posts/{p['id']}", "POST", {"content": new})
            done += 1
            print(f"🔗 외부링크 추가: id {p['id']} | {title}")
        else:
            miss += 1
            print(f"::warning::id {p['id']} '{title}' — '관세청' 문구가 없어 링크 못 넣음 (수동 확인)")
    print(f"완료: 링크 추가 {done}건 / 이미 있음 {skip}건 / 못함 {miss}건 / 전체 {len(posts)}건")


if __name__ == "__main__":
    main()
