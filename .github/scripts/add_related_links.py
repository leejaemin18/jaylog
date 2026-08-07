# 내부링크가 부족한 글에 '함께 읽으면 좋은 글' 블록을 넣는다 (blog-command의 add-related 명령).
# 고지문 앞에 삽입, 이미 블록이 있으면 건너뜀. 발행글 대상.
import os, json, base64, urllib.request

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
API = "https://jaylog.co.kr/wp-json/wp/v2"
MARK = "함께 읽으면 좋은 글"
NOTICE = "<p><em>본 글은 일반 정보"

# 내부링크 0개였던 글 → 관련 발행글 2개 (id, 앵커텍스트)
RELATED = {
    19: [(27, "관부가세 계산법 완벽 정리"), (23, "목록통관 vs 일반통관 차이")],
    32: [(19, "관세 면제 기준 150달러"), (27, "관부가세 계산법 완벽 정리")],
    42: [(27, "관부가세 계산법 완벽 정리"), (19, "관세 면제 기준 150달러")],
    55: [(80, "골프 거리측정기 직구와 전파인증"), (27, "관부가세 계산법 완벽 정리")],
    58: [(44, "전자제품 직구와 전파인증(KC)"), (27, "관부가세 계산법 완벽 정리")],
}


def wp(path, method="GET", data=None):
    req = urllib.request.Request(
        API + path, method=method,
        headers={"Authorization": "Basic " + AUTH, "Content-Type": "application/json"},
        data=json.dumps(data).encode() if data else None)
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.load(res)


def main():
    done = 0
    for pid, links in RELATED.items():
        p = wp(f"/posts/{pid}?context=edit&_fields=id,title,content")
        raw = p["content"]["raw"]
        if MARK in raw:
            print(f"이미 있음: id {pid} — 건너뜀")
            continue
        items = "".join(f'<li><a href="https://jaylog.co.kr/?p={i}">{t}</a></li>' for i, t in links)
        block = f'<h2 class="wp-block-heading">{MARK}</h2>\n<ul>{items}</ul>\n'
        new = raw.replace(NOTICE, block + NOTICE, 1) if NOTICE in raw else raw + "\n" + block
        wp(f"/posts/{pid}", "POST", {"content": new})
        done += 1
        print(f"🔗 관련글 블록 추가: id {pid} | {p['title']['raw'][:28]} → {[i for i,_ in links]}")
    print(f"완료: {done}건")


if __name__ == "__main__":
    main()
