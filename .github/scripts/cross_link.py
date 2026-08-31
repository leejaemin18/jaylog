# 주제가 겹치는 글을 서로 보완 관계로 연결한다 (blog-command: cross-link).
# 삭제 대신 상호 링크로 '규정편↔체크리스트편'처럼 묶어 중복 인상 완화. 멱등(마커).
import os, re, json, base64, urllib.request

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
API = "https://jaylog.co.kr/wp-json/wp/v2"

# pid: (다른 글 안내 문구, 대상 pid, 대상 링크 텍스트)
NOTES = {
    43:  ("이 글은 <strong>규정과 초과 시 처리</strong>를 자세히 설명합니다. 핵심만 빠르게 확인하려면",
           443, "영양제 직구 체크리스트"),
    443: ("이 글은 <strong>핵심만 짚는 체크리스트</strong>입니다. 규정과 초과 시 어떻게 되는지 자세히 보려면",
           43, "건강기능식품 6병 규정"),
}


def wp(path, method="GET", data=None):
    req = urllib.request.Request(
        API + path, method=method,
        headers={"Authorization": "Basic " + AUTH, "Content-Type": "application/json"},
        data=json.dumps(data).encode() if data else None)
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.load(res)


def note_html(lead, tgt, txt):
    return (f'<!--xlink-->\n<p style="margin:1.6em 0;padding:12px 16px;border:1px solid #dbe6d8;'
            f'border-left:4px solid #7fb389;border-radius:10px;background:#eef7f0;font-size:14.5px;'
            f'line-height:1.7;">👉 {lead} <a href="https://jaylog.co.kr/?p={tgt}"><strong>{txt}</strong></a>'
            f'를 참고하세요.</p>\n')


def main():
    for pid, (lead, tgt, txt) in NOTES.items():
        try:
            p = wp(f"/posts/{pid}?context=edit&_fields=id,content")
            raw = p["content"]["raw"]
            if "<!--xlink-->" in raw:
                print(f"건너뜀 {pid}: 이미 연결됨"); continue
            note = note_html(lead, tgt, txt)
            if "<!--jaylog-tools-->" in raw:
                new = raw.replace("<!--jaylog-tools-->", note + "<!--jaylog-tools-->", 1)
            else:
                m = re.search(r'<h2[^>]*>\s*자주 묻는 질문', raw)
                pos = m.start() if m else len(raw)
                new = raw[:pos] + note + raw[pos:]
            wp(f"/posts/{pid}", "POST", {"content": new})
            print(f"✅ 상호 링크 삽입: {pid} → {tgt}")
        except Exception as e:
            print(f"::warning::{pid} 실패 — {e}")


if __name__ == "__main__":
    main()
