# wordpress-snippets — 워드프레스에 직접 붙이는 코드 (REST로는 못 하는 것)

REST API로는 글·이미지·페이지만 다룰 수 있어서, 사이트 루트 파일(`/llms.txt`)이나
robots 같은 건 워드프레스 쪽에 코드를 한 번 심어야 한다. 여기 파일들이 그 용도.

## llms-txt.php — 답변엔진용 사이트 요약 (`/llms.txt`)
Orca의 `llms.txt`(GEO) 개념을 워드프레스로 이식. ChatGPT·Perplexity·Claude 등이 우리 사이트가
무엇이고 어떤 글이 있는지 HTML 파싱 없이 이해하게 해준다. 발행글이 늘면 자동 반영(12시간 캐시).

**설치(한 번):** 관리자 → WPCode → Add Snippet → PHP Snippet → `llms-txt.php`의 `<?php` 이후 내용
붙여넣기 → Auto Insert / Run Everywhere → Save & Activate.
확인: https://jaylog.co.kr/llms.txt 접속 → 글 목록이 텍스트로 나오면 성공.

## 답변엔진 크롤러 허용 (robots) — 대부분 이미 OK
GPTBot·ClaudeBot·PerplexityBot·Google-Extended 등은 워드프레스/Rank Math 기본 robots에서
차단되지 않으므로 보통 손댈 필요 없다. 확인만: 관리자 → Rank Math → General Settings → Edit robots.txt
에서 위 봇을 `Disallow` 하는 줄이 없는지 보면 된다(없으면 그대로 두기).
