# file-ops

- 경로는 vault root 기준으로 쓴다 (예: `AI-Sessions/wiki/decisions/거래처-선정.md`, `.claude/rules/core/file-ops.md`).
- 문서 간 위키링크(대괄호 2겹)도 **반드시 vault root 기준 경로**로 쓴다 — 예: 대괄호 안에 `.claude/rules/core/file-ops.md`. 상대경로(`../CLAUDE.md`, `./uncertainty.md` 형태)는 Obsidian이 vault root 기준으로 해석하므로 링크가 깨진다.
- 특히 `.claude/rules/` 아래 문서에서 `../CLAUDE.md`는 루트 `CLAUDE.md`(vault 지식관리 규칙)와 `.claude/CLAUDE.md`(프로젝트 라우터) 중 어느 쪽인지도 모호하다. 항상 둘 중 하나를 vault root 경로로 명시한다.
- 폴더 역할: 각 폴더는 정해진 역할만 담는다 (예: 코드/문서/설정을 폴더별로 분리). 역할 밖 파일을 넣지 않는다.
- 관계없는 폴더/파일 발견 시 임의 삭제 금지. 사용자에게 삭제 여부를 먼저 물어보고 승인 후 삭제.
- `AI-Sessions/raw/` 파일은 수정·삭제하지 않는다 (원본 불변 규칙, `CLAUDE.md` Core Rule 2). 이 규칙을 기계적으로도 강제하고 싶으면(파일 수정을 실제로 막는 훅) 별도로 설정한다 — 기본 배포에는 포함되어 있지 않다.
- 애매한 CRUD(생성/조회/수정/삭제) 요청은 실행 전 반드시 사용자에게 확인한다.
- 폴더를 새로 만들면 영어 이름을 쓰고, 그 폴더의 `README.md`에 관리 파일 목록을 갱신한다 (라우터 역할).

의존: [[.claude/CLAUDE.md]]
