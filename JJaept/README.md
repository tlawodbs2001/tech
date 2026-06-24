# JJaept

JJaept 프로젝트의 콘텐츠와 운영 자료를 관리합니다.

## 폴더 구조

- `content/lifestyle/`: 자취·원룸·생활지식 블로그 콘텐츠
- `content/stock-reports/`: 개인 참고용 증권 리포트
- `images/`: 대표 이미지와 썸네일
- `drafts/`: 검수 전 초안
- `published/`: 게시 완료본
- `content-index.json`: 콘텐츠 상태 및 경로 인덱스
- `automation/`: 콘텐츠 생성 스크립트와 실행 상태
- `.github/workflows/jjaept-content.yml`: GitHub Actions 예약 실행 워크플로

## 자동 생성 일정

GitHub Actions의 cron은 UTC 기준입니다.

| 한국 시간 | 콘텐츠 | UTC cron |
| --- | --- | --- |
| 매일 09:00 | 개인 참고용 증권 리포트 | `0 0 * * *` |
| 매일 09:30 | 생활지식 콘텐츠 1~5번 큐 | `30 0 * * *` |
| 매일 14:00 | 생활지식 콘텐츠 6~10번 큐 | `0 5 * * *` |

## 최초 설정

1. GitHub 저장소 `Settings` → `Secrets and variables` → `Actions`로 이동합니다.
2. `New repository secret`을 선택합니다.
3. 이름을 `OPENAI_API_KEY`로 지정하고 OpenAI API 키를 저장합니다.
4. 필요할 때만 Repository variables에 아래 값을 추가합니다.
   - `OPENAI_TEXT_MODEL`: 기본값은 `gpt-5.2`
   - `OPENAI_IMAGE_MODEL`: 기본값은 `gpt-image-2`
5. `Actions` 탭에서 **JJaept 콘텐츠 자동 생성** 워크플로를 수동 실행해 첫 동작을 검증합니다.

> API 키는 코드, Markdown 파일, 커밋 메시지, Actions 로그에 넣지 않습니다. GitHub Secret에만 저장합니다.

## 생성 결과

- 생활 콘텐츠: `JJaept/content/lifestyle/YYYY/MM/`
- 증권 리포트: `JJaept/content/stock-reports/YYYY/MM/`
- 대표 이미지: `JJaept/images/YYYY/MM/`
- 생성 상태와 이력: `JJaept/content-index.json`, `JJaept/automation/state.json`

생성물은 기본적으로 `draft` 상태로 저장합니다. 게시 전 사실·가격·법률·건강 관련 내용을 검수한 뒤 `published/`로 옮겨 사용합니다.

## 운영 원칙

- 콘텐츠는 Markdown 형식으로 저장합니다.
- 파일명은 `YYYY-MM-DD-주제.md` 형식을 사용합니다.
- 이미지 파일은 같은 날짜와 주제 식별자를 사용합니다.
- 민감정보, 토큰, 비밀번호, API 키는 저장하지 않습니다.
- 비용이 발생할 수 있는 모델·이미지 생성은 사용량과 예산을 확인한 뒤 사용합니다.
