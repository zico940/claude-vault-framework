---
type: design
date: 2026-08-15
status: confirmed
---

# Claude Vault Framework — 업종 무관 지식관리 플러그인 설계

## Summary

현재 AURA_v1 vault에서 검증된 "Raw/Wiki 분리 + 다중 검증(verify-docs) + 집요한 데이터 수집(open-questions/uncertainty) + 업종별 라우터·역할 분담" 패턴을, AURA 프로젝트 전용 내용(우노Q, backend/frontend 폴더 구조, 6개 개발 에이전트)과 분리해 **Claude Code 플러그인**으로 재포장한다. 설치 후 `/setup-wizard`가 업종·팀 규모·운영 환경을 인터뷰해 그 업종에 맞는 라우터·규칙·폴더 구조를 생성한다.

## Context

AURA_v1 vault는 "여러 AI 에이전트와 사람이 같은 업무 맥락을 공유하는 안정적 비즈니스 프로세스"를 목표로 설계됐고, 실제로 두 차례 모순(Q26 미반영, paused-work 자기모순)을 겪고 이를 원인 분류(A: 대화 중 확정 사실 미반영, B: 새 규칙 자기모순)해서 재발 방지 체계(open-questions 규칙 1.5, rule-authoring.md, verify-docs 검사 6종)까지 만든 상태다. 이 설계 자체가 다른 업종에도 재사용 가능한 값을 가진다고 판단해, 배포 형태(프롬프트/스킬/플러그인)를 분석하고 플러그인 방식으로 설계한다.

의도한 결과: AURA 개발자는 지금처럼 AURA_v1 vault를 계속 쓰고, 이 설계와 별개로 **범용 프레임워크만 뽑아낸 새 GitHub 저장소**를 하나 만들어 그 위에서 다른 업종 사용자가 `/plugin install` 한 번으로 같은 패턴을 자기 업종에 적용할 수 있게 한다.

## 결정된 사항 (사용자 답변)

- 배포 대상: 개발자용(플러그인 그대로)과 비개발자용(더 쉬운 형태)을 계층 분리. **이번 스펙은 1계층(플러그인)만 다룬다.**
- 핵심 가치 3가지(raw/wiki+검증, 집요한 질문 수집, 업종별 라우터+역할 분담) 전부 동일 비중으로 이식.
- 배포 형태 우선순위: **Claude Code 플러그인**부터 만들고 확장.
- 업종별 맞춤화: **설치 직후 온보딩 마법사**(`/setup-wizard`)가 인터뷰해서 생성. 미리 만든 업종별 템플릿 여러 개를 준비하지 않는다.
- 범용화 범위: **AURA 고유 내용(우노Q, backend/frontend, 6개 에이전트)은 전부 제외**. 프레임워크 뼈대만 이식.

## 아키텍처

### 저장소 분리

새 GitHub 저장소 `claude-vault-framework`(가칭, private로 시작)를 별도로 만든다. AURA_v1 저장소 안에 넣지 않는다 — 이유: AURA_v1은 `.claude/rules/core/git.md`에 따라 이미 "AURA 개발 코드" 전용으로 범위가 고정돼 있고([[.claude/rules/core/file-ops.md]] 폴더 역할 원칙과 동일 이유), 프레임워크는 AURA와 독립적인 생명주기(다른 업종 사용자가 이슈/PR을 낼 수 있음)를 가지므로 애초에 다른 저장소여야 충돌이 없다.

### 디렉터리 구조

```
claude-vault-framework/
├── .claude-plugin/
│   └── marketplace.json          # 플러그인 메타데이터, 버전
├── skills/
│   ├── setup-wizard/
│   │   └── SKILL.md              # 신규 — 온보딩 인터뷰 + 파일 생성
│   └── verify-docs/
│       ├── SKILL.md              # AURA_v1의 것을 업종 무관 표현으로 재작성
│       └── check.py              # 로직은 이미 업종 무관 — 경로만 상수화해 이식
├── templates/
│   ├── CLAUDE.md.template        # vault 지식관리 규칙 (raw/wiki, save filter, self-report flag)
│   ├── router.md.template        # .claude/CLAUDE.md 라우터 뼈대 — "항상 로드"는 고정, "작업별 로드"는 wizard가 채움
│   └── rules/core/
│       ├── file-ops.md           # 이미 업종 무관 (경로 규칙, raw 불변)
│       ├── uncertainty.md        # 이미 업종 무관
│       ├── open-questions.md     # 이미 업종 무관 (규칙 1.5, 자가대조 포함)
│       └── rule-authoring.md     # 이미 업종 무관
└── README.md
```

**이식 기준**: `.claude/rules/core/*.md` 4개 파일은 지금 이미 AURA 관련 언급이 없어 그대로 템플릿화 가능(코드 검토로 확인 필요 — 구현 단계에서 재확인). `.claude/rules/dev/*.md`, `.claude/rules/hardware/*.md`, `.claude/agents/*.md`는 전부 AURA 전용이라 이식하지 않는다.

### setup-wizard 스킬

**트리거**: 플러그인 설치 후 사용자가 `/setup-wizard` 실행 (자동 실행 아님 — 설치만 하고 나중에 준비되면 돌릴 수도 있어야 함).

**동작 순서**:
1. 인터뷰 — 한 번에 하나씩, 객관식 우선 (AskUserQuestion 패턴과 동일):
   - 업종/도메인 (자유 입력)
   - 팀 규모 (1인 / 소규모 / 조직)
   - 운영 환경에서 민감정보 기준 (고객 개인정보 다루는지 등)
   - 역할 분담이 필요한지 (필요하면 어떤 역할들 — 자유 입력, AURA의 backend-dev 같은 고정 목록 강제하지 않음)
2. 답변을 바탕으로 `templates/*.template`의 플레이스홀더(`{{업종}}`, `{{팀규모}}` 등)를 치환해 실제 파일 생성:
   - `CLAUDE.md`, `.claude/CLAUDE.md`(라우터), `.claude/rules/core/*.md`(무치환 복사)
   - `AI-Sessions/raw/`, `AI-Sessions/wiki/{sources,concepts,decisions,errors,projects}/`
   - `tasks/questions/open-questions.md`(빈 큐 형식만)
3. `verify-docs` 스킬/check.py를 그대로 복사.
4. 마지막에 "이제 실무 데이터를 넣기 시작하면 됩니다" 안내 + 첫 `save`/`ingest` 명령 예시 제공.

**인터뷰에서 확정 안 된 값은 TBD로 남기고 open-questions.md에 큐로 등록** — AURA vault의 uncertainty.md 원칙을 wizard 자신도 지킨다(자기 자신도 "확인 안 된 건 추측하지 않는다"는 이 프레임워크의 규칙을 따름).

### verify-docs 이식 시 변경점

현재 `check.py`의 `ROUTER = ".claude/CLAUDE.md"`, Q번호 정규식, "재검증 대상 문서 목록" 파싱 로직은 이미 텍스트 패턴 기반이라 업종 무관이다. 이식 시 확인할 것: 코드/주석에 "AURA"·"우노Q" 같은 하드코딩 문자열이 없는지 grep으로 확인(구현 단계 작업, 지금 시점엔 없을 것으로 추정되나 확정 안 됨 — TBD).

### 이번 범위에서 하지 않는 것

- **업종별 사전 제작 템플릿 다수 준비** — wizard 인터뷰 방식으로 대체(사용자 결정).
- **AURA 6개 에이전트(backend-dev 등) 이식** — 업종마다 필요한 역할이 다르므로 뼈대만 남기고 wizard가 사용자 답변으로 채우게 함.
- **비개발자용 경량 배포(2계층)** — 플러그인이 자리잡은 뒤 별도 스펙으로 재검토.
- **marketplace.json을 공개 marketplace에 등록** — 저장소 자체를 private로 시작하며, 공개 배포 여부는 이번 스펙 밖.
- **pretooluse-guard.py 같은 훅 이식** — AURA의 훅은 raw 삭제 차단, force-push 차단 등 AURA 특유 위험 패턴에 맞춰져 있음. 프레임워크 공통 훅(raw 폴더 불변 보호 정도)만 최소로 남길지는 구현 단계에서 코드 확인 후 결정 (TBD).

## 검증 방법

- `/plugin install`로 새 저장소를 로컬에 설치 후 `/setup-wizard` 실행, 가상의 업종(예: "동네 카페")으로 인터뷰를 끝까지 진행해 라우터·규칙·폴더가 실제로 생성되는지 확인.
- 생성된 vault에서 `python .claude/skills/verify-docs/check.py`를 실행해 AURA_v1과 동일하게 "OK: N개 검사 통과"가 나오는지 확인.
- 생성된 `.claude/rules/core/*.md`에 "AURA", "우노Q", "backend/frontend" 등 AURA 전용 문자열이 섞여있지 않은지 grep으로 확인.
