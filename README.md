# 제이로그 (jaylog.co.kr) 블로그 운영 저장소

해외직구·수입 통관 정보 블로그. **구글 애드센스 승인 → 수익화**가 목표. 타깃 **50대**.
Claude가 REST API로 글을 직접 작성·발행하고, GitHub Actions가 썸네일 생성·예약·유지보수를 자동화한다.

> 새 세션은 **`인수인계.md` → `CLAUDE.md`** 순서로 읽으면 전체 맥락을 이어받는다.

## 어떻게 돌아가나 (클라우드 완전 자동)

```
drafts/글.md 커밋(push)
      │  publish-draft.yml (main의 drafts/**.md 감시)
      ▼
① 썸네일·본문이미지 생성(OpenAI gpt-image-2)  ─ 실패해도 글은 텍스트로 등록('썸네일필요' 표시)
② GEO 렌더: 상단 '한눈 요약' + 하단 FAQ + FAQPage JSON-LD (geo_render.py)
③ 계산기 버튼(세금글) · 태그 · 발췌 세팅
④ 워드프레스 등록 → 하루 1개 예약 큐 맨 뒤 (schedule: auto)
⑤ 초안을 published/로 이동 + 작성현황.md 기록
      │
      ▼  wp-cron-ping.yml (매시간) — 방문자 없어도 예약글 제때 발행
```

PC가 꺼져 있어도, 폰만 있어도 동작한다. 폰 관리는 `blog-command.yml` (아래 명령 표).

## 폴더·파일 구성
| 경로 | 내용 |
|---|---|
| `CLAUDE.md` | 작업 규칙 (동기화·글쓰기·발행·GEO). 모든 세션이 따른다 |
| `인수인계.md` | 현재 상태 요약 — 새 세션 첫 읽기 |
| `agents/jaylog-writer.md` | 글쓰기 에이전트 상세 규칙(SEO/GEO·썸네일·구조) |
| `글계획.md` / `작성현황.md` | 글 주제 계획 / 작성·발행 기록 |
| `wp-api-config.md` | 사이트·연동 개요 (비밀키 제외) |
| `drafts/` | 발행 대기 초안(md). 형식은 CLAUDE.md 참고 |
| `published/` | 등록 완료된 초안(추적용, `등록됨: post NNN` 주석) |
| `geo/backfill.json` | 기존 글 GEO 소급용 데이터(글 id별 요약·FAQ) |
| `pages/` | 소개·문의·개인정보 등 신뢰 페이지 원본 |
| `review/` | 라이브 글/페이지/감사 결과 덤프(품질 평가용, WP에서 내려받음) |
| `wordpress-snippets/` | REST로 못 하는 워드프레스용 코드(예: `/llms.txt` 스니펫) |
| `research/` | 지식iN 글감 조사 결과 |
| `.github/scripts/` · `.github/workflows/` | 자동화 스크립트·워크플로 |
| `secrets.local.md` | 🔒 비밀키. **커밋 금지**(.gitignore). 템플릿: `secrets.local.example.md` |

## GitHub Actions (워크플로)
| 워크플로 | 트리거 | 하는 일 |
|---|---|---|
| `publish-draft.yml` | drafts/ 푸시 · 수동 | 초안 → 썸네일+GEO+등록+예약 |
| `wp-cron-ping.yml` | 매시간 | 예약발행 깨우기 |
| `blog-command.yml` | 수동(폰) | 아래 명령 표 |
| `backfill-geo.yml` | 수동 | 기존 글에 GEO 소급 적용(멱등) |
| `add-images.yml` | 수동(file 입력) | 텍스트로 등록된 글에 이미지 채우기 |
| `kin-research.yml` | 수동(키워드) | 지식iN 글감 수집 |

## 폰 명령 (`blog-command.yml` → Run workflow)
| 명령 | 하는 일 |
|---|---|
| `status` | 발행/예약/초안 개수·목록 |
| `publish-one` | 가장 오래된 초안 1개 즉시 발행 |
| `schedule-queue` | 초안 전부 하루 1개씩 예약 |
| `publish-ids` / `trash-posts` | 지정 글 즉시 발행 / 휴지통 |
| `seo-audit` · `set-focus` · `seo-boost` · `add-related` | SEO 점검·보강 |
| `geo-audit` | **전 글 GEO(요약+FAQ) 적용 현황 점검** → review/geo-audit.txt |
| `backfill-geo` | **기존 글에 GEO 소급 적용** |
| `add-body-images` | 옛 글에 본문 이미지 생성·삽입 |
| `create-pages` · `enhance-pages` · `create-calculator-page` | 신뢰 페이지·계산기 페이지 |
| `site-audit` · `export-content` | 사이트 감사 · 본문 덤프(review/) |

## SEO와 GEO
- **SEO**(검색 순위): Rank Math 기반. 포커스 키워드·아웃바운드 링크·내부링크·발췌.
- **GEO**(답변엔진 인용): 글마다 `answer_summary`(상단 한눈 요약) + `faq`(하단 FAQ + FAQPage JSON-LD).
  ChatGPT·Perplexity·구글 AI개요가 우리 글을 인용하게 하는 구조. drafts 프론트매터에 채우면 자동 렌더.
  선택: `wordpress-snippets/llms-txt.php`(답변엔진용 사이트 요약 `/llms.txt`).

## 새 PC/세션에서 시작
1. 저장소 클론 → `secrets.local.example.md`를 `secrets.local.md`로 복사 후 실제 키 채우기
2. `agents/jaylog-writer.md`를 `.claude/agents/`에 복사(선택)
3. Claude에게 "제이로그 이어서" — `인수인계.md`+`CLAUDE.md`가 맥락을 준다.

## 운영 원칙 (상세는 CLAUDE.md)
- 하루 1개 발행 · main 브랜치에만 커밋 · 비밀키 커밋 금지 · 주제 사전 허가제
- 글: 50대 타깃, 획일감 금지, h2 3~5개, 공백제외 1,700자+, 표/리스트, 요약·FAQ 필수
