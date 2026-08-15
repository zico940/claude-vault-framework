# Claude Vault Framework 플러그인 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** AURA_v1 vault의 Raw/Wiki 분리 + 다중 검증(verify-docs) + 집요한 데이터 수집(open-questions/uncertainty) 패턴을 업종 무관 형태로 뽑아내, 새 GitHub 저장소 `claude-vault-framework`에 Claude Code 플러그인으로 패키징한다. 설치 후 `/setup-wizard`가 업종을 인터뷰해 그 업종 전용 vault를 즉석 생성한다.

**Architecture:** 새 로컬 디렉터리 `C:\AURA_DEV\V1\claude-vault-framework`를 만들어 독립 git 저장소로 초기화한다. `.claude/rules/core/*.md` 4개 파일은 AURA 참조가 없어 그대로 복사, `open-questions.md`의 AURA 전용 근거 문구 1곳만 플레이스홀더로 치환한다. `verify-docs`(check.py + SKILL.md)는 통째로 이식한다. 신규 `setup-wizard` 스킬이 인터뷰 → 템플릿 치환 → 파일 생성을 담당하며, Python 스크립트(`generate.py`)로 치환 로직을 구현해 SKILL.md는 그 스크립트를 어떻게 부르는지만 안내한다.

**Tech Stack:** Markdown(스킬/규칙 문서), Python 3(verify-docs check.py 이식 및 setup-wizard의 generate.py), Claude Code 플러그인 매니페스트(`.claude-plugin/marketplace.json`), git.

**Spec:** `docs/specs/2026-08-15-vault-framework-plugin-design.md`

## Global Constraints

- 새 저장소는 AURA_v1과 완전히 분리된 독립 GitHub 저장소(`claude-vault-framework`)로 만든다 — AURA_v1 안에 넣지 않는다 (스펙 "아키텍처 > 저장소 분리").
- AURA 고유 내용(우노Q, backend/frontend 폴더 구조, 6개 개발 에이전트)은 절대 이식하지 않는다 (스펙 "이식 기준").
- 업종별 사전 제작 템플릿을 여러 개 만들지 않는다 — `/setup-wizard` 인터뷰 방식 하나로 모든 업종을 커버한다 (스펙 "결정된 사항").
- `.claude/rules/core/*.md` 4개 파일(file-ops, uncertainty, open-questions, rule-authoring)에서 AURA 전용 표현이 남아있으면 안 된다 — 이식 전 반드시 grep으로 확인 (스펙 "검증 방법").
- verify-docs의 6개 검사 로직은 그대로 유지한다 — 이미 텍스트 패턴 기반으로 업종 무관 (스펙 "verify-docs 이식 시 변경점").
- 생성된 vault에서 `python .claude/skills/verify-docs/check.py`가 "OK: 6개 검사 통과"를 출력해야 한다 (스펙 "검증 방법").

---

## Task 1: 새 저장소 뼈대 + 이식 대상 규칙 4종 복사

**Files:**
- Create: `C:\AURA_DEV\V1\claude-vault-framework\.git`(git init 결과)
- Create: `C:\AURA_DEV\V1\claude-vault-framework\templates\rules\core\file-ops.md`
- Create: `C:\AURA_DEV\V1\claude-vault-framework\templates\rules\core\uncertainty.md`
- Create: `C:\AURA_DEV\V1\claude-vault-framework\templates\rules\core\open-questions.md`
- Create: `C:\AURA_DEV\V1\claude-vault-framework\templates\rules\core\rule-authoring.md`
- Create: `C:\AURA_DEV\V1\claude-vault-framework\.gitignore`
- Create: `C:\AURA_DEV\V1\claude-vault-framework\README.md`

**Interfaces:**
- Produces: `templates/rules/core/*.md` — Task 3(generate.py)가 읽어서 치환·복사할 원본 파일들. `open-questions.md`는 `{{도메인_제약}}` 플레이스홀더 1곳을 포함한다.

- [ ] **Step 1: 로컬 디렉터리 생성 및 git 초기화**

```bash
mkdir -p "/c/AURA_DEV/V1/claude-vault-framework"
cd "/c/AURA_DEV/V1/claude-vault-framework"
git init
```

- [ ] **Step 2: .gitignore 작성**

`C:\AURA_DEV\V1\claude-vault-framework\.gitignore`:
```
.env
*.pem
secrets/
__pycache__/
*.pyc
.DS_Store
```

- [ ] **Step 3: file-ops.md, uncertainty.md, rule-authoring.md를 무변경 복사**

AURA_v1의 아래 3개 파일은 grep 결과 AURA 관련 언급이 없다(이미 확인 완료). 내용을 그대로 복사한다.

```bash
mkdir -p "/c/AURA_DEV/V1/claude-vault-framework/templates/rules/core"
cp "/c/AURA_DEV/V1/AURA_v1/.claude/rules/core/file-ops.md" \
   "/c/AURA_DEV/V1/claude-vault-framework/templates/rules/core/file-ops.md"
cp "/c/AURA_DEV/V1/AURA_v1/.claude/rules/core/uncertainty.md" \
   "/c/AURA_DEV/V1/claude-vault-framework/templates/rules/core/uncertainty.md"
cp "/c/AURA_DEV/V1/AURA_v1/.claude/rules/core/rule-authoring.md" \
   "/c/AURA_DEV/V1/claude-vault-framework/templates/rules/core/rule-authoring.md"
```

- [ ] **Step 4: open-questions.md 복사 후 AURA 전용 문구를 플레이스홀더로 치환**

먼저 복사:
```bash
cp "/c/AURA_DEV/V1/AURA_v1/.claude/rules/core/open-questions.md" \
   "/c/AURA_DEV/V1/claude-vault-framework/templates/rules/core/open-questions.md"
```

`templates/rules/core/open-questions.md`에서 아래 원문 줄(규칙 3번 안, "권장안을 반드시 붙인다" 문단)을:

```
   - **권장안을 반드시 붙인다.** 사용자가 "권장안대로 가자"만 답해도 진행 가능해야 한다. 근거는 이 프로젝트의 두 고정 제약(**우노Q 리소스 제약**, **9명 내부용·외부 트래픽 없음**)에 맞춘다.
```

아래로 치환:

```
   - **권장안을 반드시 붙인다.** 사용자가 "권장안대로 가자"만 답해도 진행 가능해야 한다. 근거는 이 프로젝트의 고정 제약({{도메인_제약}})에 맞춘다.
```

그 외 이 파일의 나머지 내용(규칙 0, 1, 1.5, 2, 4, 5, 절대 규칙, 작업 완료 시 자가 대조, 재검증 대상 문서 목록, 답변 반영 후 재검증)은 이미 업종 무관하므로 그대로 둔다. `## 재검증 대상 문서 목록` 표 안의 `tasks/TASKS.md`, `docs/environments.md`, `docs/project-plan.md`, `docs/mvp-features.md`, `.claude/rules/hardware/unoq-constraints.md` 행은 Task 2에서 별도로 다룬다(이 Task에서는 그대로 둔 채 복사만 완료).

- [ ] **Step 5: 복사 결과에 AURA 전용 문자열이 남아있지 않은지 확인**

```bash
grep -riE "우노Q|아우라|AURA|backend/|frontend/" "/c/AURA_DEV/V1/claude-vault-framework/templates/rules/core/"
```

Expected: 매치 없음(빈 출력). 매치가 나오면 해당 줄을 찾아 제거하거나 플레이스홀더로 바꾼다.

- [ ] **Step 6: README.md 작성**

`C:\AURA_DEV\V1\claude-vault-framework\README.md`:
```markdown
# Claude Vault Framework

업종 무관 지식관리 프레임워크 — Claude Code 플러그인.

Raw/Wiki 분리, 확인되지 않은 사실은 큐에 쌓아 순서대로 캐묻는 인터뷰(uncertainty),
문서 간 정합성 다중 검증(verify-docs)을 뼈대로 삼는다.

## 설치

```
/plugin install claude-vault-framework
```

## 사용

설치 후 `/setup-wizard`를 실행하면 업종·팀 규모·역할을 인터뷰해
해당 업종 전용 vault(라우터, 규칙, 폴더 구조)를 생성한다.

## 구조

- `skills/setup-wizard/` — 온보딩 인터뷰 + vault 생성
- `skills/verify-docs/` — 문서 정합성 기계 검증
- `templates/` — wizard가 채워 넣는 원본 템플릿
```

- [ ] **Step 7: 커밋**

```bash
cd "/c/AURA_DEV/V1/claude-vault-framework"
git add .gitignore README.md templates/
git commit -m "chore: 저장소 뼈대 + 업종 무관 규칙 4종 이식"
```

---

## Task 2: `open-questions.md`와 `rule-authoring.md`를 비개발자도 쓸 수 있게 완전 범용화

**Files:**
- Modify: `C:\AURA_DEV\V1\claude-vault-framework\templates\rules\core\open-questions.md`
- Modify: `C:\AURA_DEV\V1\claude-vault-framework\templates\rules\core\rule-authoring.md`

**Interfaces:**
- Consumes: Task 1에서 생성된 `templates/rules/core/open-questions.md`, `rule-authoring.md`
- Produces: AURA 고유 파일 경로·사건 인용이 전혀 없고, 존재하지 않는 파일(`spec-management.md`, `tasks/TASKS.md`)을 참조하지 않으며, 섹션 목록이 generate.py가 실제로 만드는 빈 큐와 일치하는 버전. Task 4(generate.py)가 그대로 복사해 vault에 배치한다.

**이 Task가 고치는 모순 (비개발자 관점 재검토에서 발견, 2026-08-15):**
1. 재검증 표에 AURA 전용 파일 5개(`tasks/TASKS.md`, `docs/environments.md`, `docs/project-plan.md`, `docs/mvp-features.md`, `unoq-constraints.md`)가 남아있음 → 프레임워크엔 이 파일들이 없어 `[missing]` 오류가 난다.
2. "참고: project-plan.md와 mvp-features.md는..." 문단이 AURA 전용 문서를 직접 인용.
3. **`[[.claude/rules/dev/spec-management.md]]` 참조 2곳(규칙 2번, 의존 줄)** — 이 파일은 프레임워크에 이식되지 않으므로 dangling 참조.
4. **"🚨 절대 규칙" 섹션 전체가 `tasks/TASKS.md`를 전제로 서술됨** — generate.py는 TASKS.md를 만들지 않으므로 죽은 규칙.
5. **규칙 0번의 섹션 목록(`B. 개발 프로세스`/`C. 제품 범위·UX`/`E. 기능 디테일` 등)이 소프트웨어 개발 전용이고, generate.py가 만드는 빈 큐(`A. 인프라·운영`/`B. 업무 프로세스`/`C. 범위·데이터`)와 서로 다름** — 규칙과 실제 생성물이 정면 충돌.
6. **`rule-authoring.md`의 배경 설명이 AURA 내부 사건("paused-work.md 신설 시 2026-08-15...")을 그대로 인용** — 다른 업종 사용자는 이해 불가.

- [ ] **Step 1: 현재 표 내용을 확인**

```bash
grep -n "재검증 대상 문서 목록" -A 15 "/c/AURA_DEV/V1/claude-vault-framework/templates/rules/core/open-questions.md"
```

- [ ] **Step 2: 표를 업종 무관 뼈대(공통 파일만)로 교체**

`## 재검증 대상 문서 목록 (고정)` 섹션의 표 부분(`| 문서 | 이 문서가 담는 것 |` 헤더부터 그 다음 문단 시작 전까지)을 찾아 아래로 교체한다. 원본 문서엔 AURA 전용 파일(`docs/environments.md`, `tasks/TASKS.md`, `.claude/rules/hardware/unoq-constraints.md` 등)이 들어있으므로, wizard가 생성하는 공통 파일만 남긴다:

```markdown
| 문서 | 이 문서가 담는 것 |
|---|---|
| `tasks/questions/open-questions.md` | 원본 큐 |
| `log.md` | 작업 로그 — 과거 Q번호 인용이 남아있을 수 있음. 로그는 과거 시점 기록이므로 값 자체를 고치지 않되, 이번에 반영한 변경 사항을 새 줄로 추가했는지 확인 |

이 업종/프로젝트에서 실무 원본 문서(예: 환경설정, 제품 기획, 팀 운영 규칙)를 새로 만들면,
그 문서가 Q번호나 "확정"류 표현을 담게 되는 순간 이 표에 먼저 추가한다. 표에 추가하지
않고 방치하면 `verify-docs` 스크립트가 `[list]`로 잡아낸다.
```

- [ ] **Step 3: 나머지 문단에서 AURA 전용 예시 문구 확인**

같은 섹션 아래 "새 문서가 open-questions.md와 같은 사실을 언급하게 되면..." 문단과 "참고: docs/project-plan.md와 docs/mvp-features.md는..." 문단은 AURA 고유 파일명을 예시로 들고 있다. 후자 문단("**참고**: `docs/project-plan.md`와...")은 AURA 전용 문서를 직접 언급하므로 삭제한다.

- [ ] **Step 4: 규칙 0번의 섹션 목록을 generate.py가 만드는 빈 큐와 일치시킨다 (모순 5)**

현재 규칙 0번은 소프트웨어 개발 전용 섹션 목록을 지시하는데, 이 프레임워크의 `generate.py`(Task 4)는 다른 섹션(`A. 인프라·운영` / `B. 업무 프로세스` / `C. 범위·데이터`)으로 빈 큐를 만든다. 규칙과 생성물이 어긋나면 규칙이 죽는다. 아래 원문 줄을:

```
0. **우선순위: 인프라/환경 확인이 기능 스펙 확인보다 먼저다.** 실서버 접속 방법·실제 설치된 것·하드웨어/인프라 스펙, 배포 경로·프로세스 관리 방식, dev/prod 환경 종류, 언어/프레임워크처럼 "무엇을 만들지"를 시작하기 전에 반드시 알아야 하는 항목을 기능별 스펙 질문(인증 방식, 저장 위치 등)보다 먼저 정리하고 먼저 묻는다.
   `tasks/questions/open-questions.md`는 아래 섹션 순서를 유지한다:
   `0. 먼저 답해주세요(선행)` → `A. 인프라·운영` → `B. 개발 프로세스` → `C. 제품 범위·UX` → `D. 데이터·규정` → `E. 기능 디테일` → `F. AI 협업·에이전트 운영` → `G. 프로젝트 운영·라이프사이클`
```

아래로 교체한다:

```
0. **우선순위: 기반 환경 확인이 세부 사항 확인보다 먼저다.** "무엇을 어떻게 굴릴 것인가"(어디에 무엇이 있는지, 무엇을 이미 쓰고 있는지, 누가 무엇을 담당하는지)를 세부 질문(개별 항목의 형식·저장 위치 등)보다 먼저 정리하고 먼저 묻는다. 기반이 안 정해지면 세부를 정해도 나중에 다 뒤집힌다.
   `tasks/questions/open-questions.md`는 아래 섹션 순서를 유지한다:
   `0. 먼저 답해주세요(선행)` → `A. 인프라·운영` → `B. 업무 프로세스` → `C. 범위·데이터`
   이 업종에서 위 3개로 부족하면 섹션을 추가해도 되지만, "선행 질문이 맨 위"라는 순서 원칙은 유지한다.
```

- [ ] **Step 5: 존재하지 않는 파일 참조 2곳을 제거한다 (모순 3)**

`spec-management.md`는 AURA 전용 문서이며 이 프레임워크에 이식되지 않는다. 참조가 남으면 dangling이다.

(a) 규칙 2번의 마지막 줄에서:
```
   - 답변 내용을 원본 문서에 반영한다 (원본 문서는 [[.claude/rules/dev/spec-management.md]] 매트릭스 기준으로 정한다). 반영 시 그 문서에 이미 있는 동일 항목의 기존 표기(대소문자, 날짜 형식 등)와 충돌하지 않는지 대조 후 적는다.
```
→ 아래로 교체:
```
   - 답변 내용을 원본 문서에 반영한다 (그 사실을 "원본으로 담는 문서"가 어디인지는 이 vault의 문서 구성에 따라 정한다 — 같은 사실을 두 문서에 각각 적으면 나중에 어긋난다). 반영 시 그 문서에 이미 있는 동일 항목의 기존 표기(대소문자, 날짜 형식 등)와 충돌하지 않는지 대조 후 적는다.
```

(b) 문서 맨 끝 의존 줄에서:
```
의존: [[.claude/CLAUDE.md]], [[.claude/rules/core/uncertainty.md]], [[.claude/rules/dev/spec-management.md]], [[.claude/rules/core/file-ops.md]]
```
→ 아래로 교체:
```
의존: [[.claude/CLAUDE.md]], [[.claude/rules/core/uncertainty.md]], [[.claude/rules/core/file-ops.md]]
```

- [ ] **Step 6: "🚨 절대 규칙" 섹션에서 `tasks/TASKS.md` 전제를 제거한다 (모순 4)**

이 섹션의 핵심 메시지("에이전트가 제안한 권장안 ≠ 사용자가 실제로 답한 것")는 프레임워크의 가장 중요한 안전장치이므로 **삭제하지 않는다.** 다만 존재하지 않는 `tasks/TASKS.md`를 판단 기준으로 삼는 서술만 일반화한다. `## 🚨 절대 규칙: 권장안(✅)과 답변 완료(답변 완료:)는 다르다` 헤더부터 그 다음 `## 작업 완료 시 자가 대조` 헤더 직전까지를 통째로 아래로 교체한다:

```markdown
## 🚨 절대 규칙: 권장안(✅)과 답변 완료(답변 완료:)는 다르다

**절대 혼동 금지.** 이 프레임워크에서 가장 자주 나는 사고다.

| 구분 | 표기법 | 의미 | 사실로 쓸 수 있는가? |
|---|---|---|---|
| **권장안** | `✅ 권장: {안} ({근거})` | 에이전트가 제안한 것. 사용자가 아직 승인하지 않음 | ❌ **아니오. 이것만으로는 사실이 아니다** |
| **답변 완료** | `**답변 완료**: {사용자가 입력한 실제 값}` | 사용자가 **실제로 답변한 것**. 확정된 사실 | ✅ **가능. 원본 문서에 반영한다** |

**적용 규칙:**
- 어떤 문서에 "XXX 확정 필요"라고 적혀 있으면, 그건 아직 확정되지 않은 것이다. open-questions.md에 권장안(✅)만 있는 상태일 수 있다.
- 권장안을 본 후 "사용자가 이것에 동의했다"고 임의로 판단하고 다른 문서를 "확정됨"으로 바꾸면 안 된다.
- 어떤 문서든 "확정 필요"를 "확정됨"으로 바꾸려면 **반드시** open-questions.md에 `**답변 완료**: ...` 표기가 있어야 한다. 그 표기를 보지 못했으면 사용자에게 먼저 확인한다.
- 의심스러우면: 그 사실을 담는 원본 문서에 값이 이미 기록되어 있는가? → 기록되어 있으면 확정된 것. 없으면 미확정.

**체크리스트 (매번 확인):**
1. "확정 필요"로 표기된 항목을 수정하려 할 때: open-questions.md에서 해당 Q번호를 grep해서 `**답변 완료**:` 줄이 있는지 확인한다.
2. 없으면? → 사용자에게 질문하거나, 권장안일 뿐이라고 명시하고 진행하지 않는다.
3. 권장안을 근거로 다른 문서를 고치면 안 된다.
```

- [ ] **Step 7: `rule-authoring.md`의 AURA 내부 사건 인용을 일반화한다 (모순 6)**

`templates/rules/core/rule-authoring.md`의 `## 배경` 섹션 전체를 아래로 교체한다 (규칙 본문 1~4번과 의존 줄은 그대로 둔다):

```markdown
## 배경
"세션 시작 시 확인하라" 같은 상시성 지시를 담은 규칙 파일을 만들면서, 정작 그 파일을
상시 로드 목록이 아닌 트리거 로드 목록에만 등록하면 그 지시는 영영 실행되지 않는다.
새 규칙을 쓸 때 "내용이 맞는가"만 확인하고 "이게 실제로 언제 읽히는가"를 확인하지 않으면
생기는 자기모순이며, 실제로 겪은 사고다.
```

- [ ] **Step 8: 치환 결과 전체 재확인**

```bash
cd "/c/AURA_DEV/V1/claude-vault-framework"
echo "=== AURA 전용 파일 경로 잔존 확인 (매치 없어야 함) ==="
grep -rn "docs/environments.md\|docs/project-plan.md\|docs/mvp-features.md\|unoq-constraints\|tasks/TASKS.md\|spec-management" templates/rules/core/
echo "=== AURA 고유명사 잔존 확인 (매치 없어야 함) ==="
grep -rniE "우노Q|아우라|AURA|paused-work|backend/|frontend/|hardware/" templates/rules/core/
echo "=== 섹션 목록 일치 확인 (A. 인프라·운영 / B. 업무 프로세스 / C. 범위·데이터 가 나와야 함) ==="
grep -n "B. 업무 프로세스" templates/rules/core/open-questions.md
```

Expected: 앞의 두 grep은 매치 없음(빈 출력), 마지막 grep은 1건 매치.

- [ ] **Step 9: 커밋**

```bash
cd "/c/AURA_DEV/V1/claude-vault-framework"
git add templates/rules/core/open-questions.md templates/rules/core/rule-authoring.md
git commit -m "refactor: 비개발자 사용 가능하도록 규칙 완전 범용화 (dangling 참조·죽은 규칙·섹션 불일치 제거)"
```

---

## Task 3: verify-docs 스킬 이식

**Files:**
- Create: `C:\AURA_DEV\V1\claude-vault-framework\skills\verify-docs\check.py`
- Create: `C:\AURA_DEV\V1\claude-vault-framework\skills\verify-docs\SKILL.md`

**Interfaces:**
- Produces: `skills/verify-docs/check.py` — vault root에서 `python .claude/skills/verify-docs/check.py` 형태로 실행되는 것을 전제로 하는 스크립트(경로 상수는 vault 내부 상대경로라 이식 시 변경 불필요). `--self-test` 플래그로 자체 검증 가능.

- [ ] **Step 1: check.py를 그대로 복사**

AURA_v1의 `.claude/skills/verify-docs/check.py`는 코드/주석에 AURA 고유 문자열이 없음을 이미 확인했다(경로 상수 `QUEUE`, `RULE`, `LOG`, `ROUTER`는 전부 vault 표준 상대경로). 그대로 복사한다.

```bash
mkdir -p "/c/AURA_DEV/V1/claude-vault-framework/skills/verify-docs"
cp "/c/AURA_DEV/V1/AURA_v1/.claude/skills/verify-docs/check.py" \
   "/c/AURA_DEV/V1/claude-vault-framework/skills/verify-docs/check.py"
```

- [ ] **Step 2: 이식 후 AURA 전용 문자열이 없는지 확인**

```bash
grep -riE "우노Q|아우라|AURA" "/c/AURA_DEV/V1/claude-vault-framework/skills/verify-docs/check.py"
```

Expected: 매치 없음.

- [ ] **Step 3: self-test 실행해 스크립트가 원본과 동일하게 동작하는지 확인**

```bash
cd "/c/AURA_DEV/V1/claude-vault-framework"
python skills/verify-docs/check.py --self-test
```

Expected: `self-test OK: 검출 5종 + 오탐 방지 4종 통과`

- [ ] **Step 4: SKILL.md 작성 (AURA_v1 버전에서 업종 무관 표현으로 재작성)**

`C:\AURA_DEV\V1\claude-vault-framework\skills\verify-docs\SKILL.md`:
```markdown
---
name: verify-docs
description: 사용자가 "재검증", "검증", "재검증해줘", "문서 확인", "충돌 확인", "정합성 체크", "lint"라고 말하면 즉시 이 스킬을 사용한다. 또한 open-questions 항목을 2개 이상 반영했거나 여러 문서에 걸친 사실을 수정한 뒤 문서 간 충돌·낡은 서술을 확인할 때도 사용한다.
---

# verify-docs — 문서 정합성 재검증

데이터가 누적·수정되면서 같은 사실이 여러 문서에 어긋나게 남는 것을 막는다.

**핵심 원칙: 전체 재독 금지.** 스크립트가 지목한 줄만 열어서 고친다. 검증 범위를
즉흥적으로 넓히면 새 불일치가 계속 나온다 — 덜 읽어서가 아니라 범위를 넓혀서다.

## 1단계 — 기계 검증

vault root에서:

```bash
python .claude/skills/verify-docs/check.py
```

`OK: 6개 검사 통과`면 1단계 끝. 발견 항목이 있으면 `파일:줄번호: [분류] 내용` 형식으로 나온다.

| 분류 | 의미 | 조치 |
|---|---|---|
| `[dangling]` | 실체 없는 Q번호를 **현재형으로** 가리킴 | 실제 반영 위치를 찾아 `(답변 완료/삭제됨 — {위치})`로 바꾸거나, 낡은 서술이면 최신 사실로 교체 |
| `[summary]` | 상단 선행 표 ↔ 본문 헤더 ↔ 하단 안내가 불일치 | 본문을 진실로 보고 요약 쪽을 맞춘다 |
| `[list]` | Q번호를 인용하는 문서가 재검증 대상 표에 없음 | `.claude/rules/core/open-questions.md` 표에 그 파일을 추가 |
| `[missing]` | 표가 가리키는 경로가 실재하지 않음 | 경로 오타 수정 또는 표에서 제거 |
| `[flag]` | `log.md`에 남은 미해결 self-report | 내용을 확인해 실제로 조치하고, `log.md`에 `flag 해결(원래 타임스탬프): 조치 요약` 줄을 추가 |
| `[router-dup]` | `.claude/CLAUDE.md`에서 같은 규칙 파일이 "항상 로드"와 "작업별 로드" 양쪽에 중복 등재됨 | 상시성 지시가 있으면 "항상 로드"만 유지하고 "작업별 로드"에서 제거 |

과거 기록(`log.md`, 각 문서의 `## 변경 이력`)은 의도적으로 검사에서 제외된다 — 그 시점엔
맞는 서술이므로 고치면 역사가 왜곡된다. (단, `log.md`의 `flag` 줄만은 예외로 별도 검사한다.)

## 2단계 — 지목된 항목만 수정

1단계 출력의 파일:줄번호만 연다. 출력에 없는 파일은 열지 않는다.

## 3단계 — 의미 검증 (고정 질문 3개만)

스크립트는 "번호가 실재하는가"만 안다. "두 문서가 같은 사실을 다르게 말하는가"는 못 잡으므로
아래 3개만 확인한다. **범위를 여기서 더 넓히지 않는다.**

1. 이번에 바꾼 사실을 다른 문서가 다르게 서술하는가? → 확정한 키워드로 검증 대상 표의 문서만 grep.
2. 실무 원본 문서(예: 팀이 쓰는 상태 추적 문서)가 이미 확정된 것을 아직 "확정 필요"라고 하는가?
3. `log.md`에 이번 변경 줄을 추가했는가?

## 4단계 — 기록

수정이 있었으면 `log.md`에 한 줄 남긴다:

```text
YYYY-MM-DD | lint | verify-docs 실행: {발견/수정 요약} | [[고친 파일들]]
```

## 한계

기계적 오류(dangling 참조, 표 누락, 요약 불일치)는 완전히 잡는다. 하지만 두 문서가 같은
사실을 서로 다르게 서술하는 의미적 모순은 3단계의 사람 판단에 달려 있다. 100% 자동 보장이
아니며, 새 문서가 생기면 `[list]` 검사가 표 갱신을 요구하는 방식으로만 추적된다.

검사기 자체가 의심스러우면: `python .claude/skills/verify-docs/check.py --self-test`
```

- [ ] **Step 5: 커밋**

```bash
cd "/c/AURA_DEV/V1/claude-vault-framework"
git add skills/verify-docs/
git commit -m "feat: verify-docs 스킬 이식 (업종 무관 6개 검사)"
```

---

## Task 4: setup-wizard용 generate.py 작성 (템플릿 치환 + vault 생성 로직)

**Files:**
- Create: `C:\AURA_DEV\V1\claude-vault-framework\skills\setup-wizard\generate.py`
- Test: `C:\AURA_DEV\V1\claude-vault-framework\skills\setup-wizard\test_generate.py`

**Interfaces:**
- Consumes: `templates/rules/core/*.md`(Task 1, 2), `templates/CLAUDE.md.template`(이 Task Step 1에서 작성), `templates/router.md.template`(이 Task Step 2에서 작성)
- Produces: 함수 `generate_vault(target_dir: str, domain: str, constraints: str) -> list[str]` — 생성된 파일의 상대경로 목록을 반환한다. `skills/setup-wizard/SKILL.md`(Task 5)가 이 스크립트를 CLI로 호출하는 방법을 안내한다.

- [ ] **Step 1: CLAUDE.md 템플릿 작성**

`C:\AURA_DEV\V1\claude-vault-framework\templates\CLAUDE.md.template`:
```markdown
# CLAUDE.md — Vault 레벨 규칙

이 파일은 Claude Code가 이 {{domain}} 업무 vault에서 일할 때 따라야 하는 업무 규약입니다.

목표는 개인 메모장이 아니라, 여러 AI 에이전트와 사람이 같은 업무 맥락을 공유할 수 있는 안정적인 비즈니스 프로세스를 만드는 것입니다.

**단일 소스 원칙:** 이 문서가 vault 지식관리 규칙의 원본이다. 규칙을 바꿀 때는 이 파일만 수정한다.

## Core Operating Rules

1. 작업을 시작하기 전에 `index.md`, `log.md`, 관련 `AI-Sessions/wiki/` 문서를 먼저 확인한다.
2. `AI-Sessions/raw/` 안의 원본 자료는 수정하거나 삭제하지 않는다.
3. 가공된 지식, 결정, 에러, 프로젝트 문서는 `AI-Sessions/wiki/` 아래에 저장한다.
4. 세션 인수인계가 필요하면 `AI-Sessions/conversations/`에 저장한다.
5. 중요한 저장 작업 후에는 `index.md`와 `log.md`를 갱신한다.
6. 사용자가 명시적으로 원하지 않는 한 민감정보, 토큰, 비밀번호, 고객 개인정보를 저장하지 않는다.

## 명령 키워드

- `save`: 현재 작업 맥락을 저장한다.
- `ingest`: raw 자료를 wiki 자료로 가공한다.
- `query`: 기존 wiki와 log를 참조한다.
- `lint`: vault 구조와 규칙 위반을 점검한다.

## Raw / Wiki Separation

`AI-Sessions/raw/`는 불변 자료 저장소다. 여기에는 원본 자료(계약서, 회의록, 고객 문의 원문 등)처럼
나중에 근거로 다시 확인해야 하는 자료를 둔다.

에이전트는 raw 파일을 수정하지 않는다. raw 내용을 바탕으로 요약, 판단, 결정, 기획 자료를 만들 때는
반드시 `AI-Sessions/wiki/` 아래에 별도 문서를 만든다.

## Wiki Categories

- `AI-Sessions/wiki/sources/`: raw 자료를 요약하고 출처 맥락을 정리한 문서
- `AI-Sessions/wiki/concepts/`: 반복해서 쓰는 개념, 용어, 프레임워크
- `AI-Sessions/wiki/decisions/`: 의사결정, 결정 근거, 결정권자, 날짜
- `AI-Sessions/wiki/errors/`: 실패한 접근, 다시 반복하면 안 되는 실수
- `AI-Sessions/wiki/projects/`: 프로젝트별 진행 맥락과 산출물

## Save Filter

무분별한 저장은 맥락 오염을 만든다. `save`를 실행하기 전에 아래 조건을 확인한다.

1. 이 정보가 향후 실무에 반복해서 재사용될 데이터인가?
2. 다른 에이전트나 동료가 업무를 이어받기 위해 반드시 읽어야 하는가?
3. 의사결정의 근거와 결정권자를 나중에 추적할 필요가 있는가?
4. 실패한 방식이라 다시 시도하면 안 되는 리스크 정보인가?
5. 팀 전체가 맞추어야 하는 공통 규칙인가?

하나도 만족하지 않는 일회성 답변, 감상, 사소한 표현 변경은 wiki에 저장하지 않는다.

## Self-Report Flag (미해결 사항 기록)

작업 중 아래 상황을 만나면 조용히 넘어가지 않고 `log.md`에 flag 줄을 남긴다:

- 읽어야 할 파일을 못 읽었거나 접근할 수 없었다
- 따라야 할 규칙/절차가 있다는 건 알지만 이번엔 못 지켰거나 건너뛰었다
- 어떤 문서·사실이 최신인지 확신이 서지 않는다

형식:
```text
YYYY-MM-DD HH:mm | flag | [read-fail|rule-skip|stale?] 한 줄 설명 | 영향받는 파일/규칙 경로
```

해결되면 새 줄을 추가한다:
```text
YYYY-MM-DD HH:mm | lint | flag 해결(원래 flag 줄의 YYYY-MM-DD HH:mm): 조치 요약 | [[고친 파일들]]
```

`verify-docs` 스킬의 `check.py`가 미해결 flag를 기계적으로 찾아낸다.

## Document Format

새 wiki 문서는 가능하면 아래 형식을 따른다.

```markdown
---
type: decision | source | concept | error | project
date: YYYY-MM-DD
status: draft | active | superseded
source: optional
---

# 제목

## Summary

## Context

## Details

## Links
```

## Completion Rule

작업이 끝나면 다음을 보고한다.

- 읽은 주요 파일
- 수정하거나 생성한 파일
- 저장 필터 적용 결과
- 다음 세션에서 이어갈 때 먼저 볼 문서
```

- [ ] **Step 2: 라우터 템플릿 작성**

`C:\AURA_DEV\V1\claude-vault-framework\templates\router.md.template`:
```markdown
# CLAUDE.md — 라우터

이 파일은 규칙 본문을 담지 않는다. 작업 유형에 맞는 파일만 열어서 읽는다.

This router assumes the working directory is the vault root (current folder).

## 항상 로드

- `.claude/rules/core/file-ops.md` — 경로/폴더/삭제 규칙
- `.claude/rules/core/uncertainty.md` — 모르면 반드시 먼저 물어본다
- `.claude/rules/core/open-questions.md` — 확인 필요 사항은 `tasks/questions/open-questions.md`에 큐로 기록·관리

## 작업별 로드

| 작업 | 로드할 파일 |
|---|---|
| 새 규칙 파일 작성·수정 | `.claude/rules/core/rule-authoring.md` |
| 확인 필요(미확정) 항목 조회/기록 | `tasks/questions/open-questions.md` |
| **"재검증"/"검증"/"충돌 확인"/"lint"** 라고 하면 | `verify-docs` 스킬 실행 (되묻지 말고 바로) |
| 여러 문서에 걸친 사실 수정 후 정합성 검증 | `verify-docs` 스킬 실행 |
{{domain_rows}}

## 절대 규칙 (요약, 상세는 rules/ 참조)

- 애매하면 반드시 사용자에게 먼저 물어본다.
- **실제 현황을 확인한 적 없으면 "모른다"고 명시하고 먼저 물어본다 — 계획/문서 내용을 실제 현황처럼 답하지 않는다.**
- 삭제는 항상 승인 후에만 한다.
{{domain_absolute_rules}}

줄 수가 늘어나면 이 라우터를 더 쪼갤 것.
```

`{{domain_rows}}`, `{{domain_absolute_rules}}`는 wizard 인터뷰에서 "역할 분담" 답변이 있을 때만 채워지는 자리이며, 없으면 빈 문자열로 치환된다(Step 4 참고).

- [ ] **Step 3: generate.py의 실패하는 테스트 작성**

`C:\AURA_DEV\V1\claude-vault-framework\skills\setup-wizard\test_generate.py`:
```python
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(__file__))
from generate import generate_vault  # noqa: E402


def test_generate_vault_creates_core_files():
    target = tempfile.mkdtemp()
    try:
        created = generate_vault(
            target_dir=target,
            domain="동네 카페",
            constraints="1인 운영, 외부 고객 데이터 없음",
        )
        assert "CLAUDE.md" in created
        assert ".claude/CLAUDE.md" in created
        assert ".claude/rules/core/file-ops.md" in created
        assert ".claude/rules/core/uncertainty.md" in created
        assert ".claude/rules/core/open-questions.md" in created
        assert ".claude/rules/core/rule-authoring.md" in created
        assert ".claude/skills/verify-docs/check.py" in created
        assert "tasks/questions/open-questions.md" in created

        for d in (
            "AI-Sessions/raw",
            "AI-Sessions/wiki/sources",
            "AI-Sessions/wiki/concepts",
            "AI-Sessions/wiki/decisions",
            "AI-Sessions/wiki/errors",
            "AI-Sessions/wiki/projects",
        ):
            assert os.path.isdir(os.path.join(target, d)), f"{d} 폴더가 생성되지 않음"

        with open(os.path.join(target, "CLAUDE.md"), encoding="utf-8") as f:
            assert "동네 카페" in f.read()

        with open(
            os.path.join(target, ".claude/rules/core/open-questions.md"), encoding="utf-8"
        ) as f:
            content = f.read()
            assert "1인 운영, 외부 고객 데이터 없음" in content
            assert "{{도메인_제약}}" not in content
    finally:
        shutil.rmtree(target, ignore_errors=True)


def test_generate_vault_verify_docs_passes():
    """generate_vault가 만든 vault에서 이식된 check.py가 통과하는지 확인."""
    import subprocess

    target = tempfile.mkdtemp()
    try:
        generate_vault(target_dir=target, domain="법무법인", constraints="비밀유지 의무")
        result = subprocess.run(
            [sys.executable, ".claude/skills/verify-docs/check.py"],
            cwd=target,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "OK" in result.stdout
    finally:
        shutil.rmtree(target, ignore_errors=True)


if __name__ == "__main__":
    test_generate_vault_creates_core_files()
    test_generate_vault_verify_docs_passes()
    print("generate.py 테스트 통과")
```

- [ ] **Step 4: 테스트 실행해 실패 확인**

```bash
cd "/c/AURA_DEV/V1/claude-vault-framework/skills/setup-wizard"
python test_generate.py
```

Expected: `ModuleNotFoundError: No module named 'generate'` (아직 generate.py가 없음)

- [ ] **Step 5: generate.py 구현**

`C:\AURA_DEV\V1\claude-vault-framework\skills\setup-wizard\generate.py`:
```python
#!/usr/bin/env python3
"""setup-wizard 인터뷰 답변을 받아 업종 전용 vault를 생성한다.

이 스크립트는 파일 생성만 담당한다. 인터뷰(질문 순서, 문구)는
SKILL.md가 대화형으로 진행하고, 답변을 모은 뒤 이 스크립트를 호출한다.
"""
import os
import shutil

FRAMEWORK_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CORE_RULE_FILES = ("file-ops.md", "uncertainty.md", "open-questions.md", "rule-authoring.md")


def _write(target_dir, rel_path, content):
    full = os.path.join(target_dir, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def _read_template(rel_path):
    with open(os.path.join(FRAMEWORK_ROOT, rel_path), encoding="utf-8") as f:
        return f.read()


def generate_vault(target_dir, domain, constraints, domain_rows="", domain_absolute_rules=""):
    """업종 전용 vault를 target_dir에 생성한다.

    Args:
        target_dir: vault를 생성할 디렉터리(이미 존재해야 함).
        domain: 업종/도메인 이름 (예: "동네 카페").
        constraints: 이 업무의 고정 제약 (예: "1인 운영, 외부 고객 데이터 없음").
            open-questions.md의 권장안 근거 문구에 들어간다.
        domain_rows: 라우터 "작업별 로드" 표에 추가할 줄(없으면 빈 문자열).
        domain_absolute_rules: 라우터 "절대 규칙"에 추가할 줄(없으면 빈 문자열).

    Returns:
        생성된 파일의 target_dir 기준 상대경로 목록.
    """
    created = []

    # 1. CLAUDE.md (vault 지식관리 규칙)
    claude_md = _read_template("templates/CLAUDE.md.template").replace("{{domain}}", domain)
    _write(target_dir, "CLAUDE.md", claude_md)
    created.append("CLAUDE.md")

    # 2. .claude/CLAUDE.md (라우터)
    router = (
        _read_template("templates/router.md.template")
        .replace("{{domain_rows}}", domain_rows)
        .replace("{{domain_absolute_rules}}", domain_absolute_rules)
    )
    _write(target_dir, ".claude/CLAUDE.md", router)
    created.append(".claude/CLAUDE.md")

    # 3. .claude/rules/core/*.md
    for name in CORE_RULE_FILES:
        content = _read_template(f"templates/rules/core/{name}")
        if name == "open-questions.md":
            content = content.replace("{{도메인_제약}}", constraints)
        _write(target_dir, f".claude/rules/core/{name}", content)
        created.append(f".claude/rules/core/{name}")

    # 4. verify-docs 스킬 이식
    verify_docs_src = os.path.join(FRAMEWORK_ROOT, "skills", "verify-docs")
    verify_docs_dst = os.path.join(target_dir, ".claude", "skills", "verify-docs")
    os.makedirs(verify_docs_dst, exist_ok=True)
    for fname in ("check.py", "SKILL.md"):
        shutil.copy(os.path.join(verify_docs_src, fname), os.path.join(verify_docs_dst, fname))
        created.append(f".claude/skills/verify-docs/{fname}")

    # 5. tasks/questions/open-questions.md (빈 큐)
    queue = (
        "# open-questions — 확인 필요 사항 큐\n\n"
        "절차: [[.claude/rules/core/open-questions.md]]\n\n"
        "## 0. 먼저 답해주세요(선행)\n\n"
        "(현재 없음)\n\n"
        "## A. 인프라·운영\n\n"
        "## B. 업무 프로세스\n\n"
        "## C. 범위·데이터\n\n"
    )
    _write(target_dir, "tasks/questions/open-questions.md", queue)
    created.append("tasks/questions/open-questions.md")

    # 6. log.md, index.md (빈 시작 파일)
    _write(target_dir, "log.md", "# log\n\n작업 로그. 형식: `YYYY-MM-DD HH:mm | command | 내용 | 링크`\n")
    created.append("log.md")
    _write(target_dir, "index.md", f"# {domain} 업무 vault\n\n## 최근 문서\n\n(아직 없음)\n")
    created.append("index.md")

    # 7. AI-Sessions 폴더 뼈대
    for sub in ("raw", "wiki/sources", "wiki/concepts", "wiki/decisions", "wiki/errors", "wiki/projects"):
        os.makedirs(os.path.join(target_dir, "AI-Sessions", sub), exist_ok=True)

    return created
```

- [ ] **Step 6: 테스트 재실행해 통과 확인**

```bash
cd "/c/AURA_DEV/V1/claude-vault-framework/skills/setup-wizard"
python test_generate.py
```

Expected: `generate.py 테스트 통과`

- [ ] **Step 7: 커밋**

```bash
cd "/c/AURA_DEV/V1/claude-vault-framework"
git add templates/CLAUDE.md.template templates/router.md.template \
  skills/setup-wizard/generate.py skills/setup-wizard/test_generate.py
git commit -m "feat: setup-wizard generate.py — 업종 전용 vault 생성 로직"
```

---

## Task 5: setup-wizard SKILL.md (인터뷰 대화 흐름)

**Files:**
- Create: `C:\AURA_DEV\V1\claude-vault-framework\skills\setup-wizard\SKILL.md`

**Interfaces:**
- Consumes: `skills/setup-wizard/generate.py`의 `generate_vault(target_dir, domain, constraints, domain_rows, domain_absolute_rules)` 함수 시그니처(Task 4).

- [ ] **Step 1: SKILL.md 작성**

`C:\AURA_DEV\V1\claude-vault-framework\skills\setup-wizard\SKILL.md`:
```markdown
---
name: setup-wizard
description: 사용자가 "/setup-wizard"를 실행하거나 "vault 초기 설정", "업종 설정", "온보딩 시작"이라고 말하면 이 스킬을 사용한다. 이 플러그인을 처음 설치한 직후, 그 업종에 맞는 vault(라우터, 규칙, 폴더 구조)를 생성할 때 쓴다.
---

# setup-wizard — 업종 전용 vault 온보딩

이 스킬은 claude-vault-framework 플러그인 설치 직후 1회 실행하는 것을 전제로 한다.
목표는 "raw/wiki 분리 + 다중 검증 + 확인 안 된 사실은 캐물어서 큐에 쌓는" 프레임워크를
사용자의 실제 업종에 맞게 즉석에서 조립하는 것이다.

**이 스킬 자신도 프레임워크의 uncertainty 원칙을 따른다** — 인터뷰에서 답이 안 나온 항목은
추측해서 채우지 않고 vault 생성 후 `tasks/questions/open-questions.md`에 큐로 남긴다.

## 인터뷰 순서 (한 번에 하나씩 질문)

1. **업종/도메인**: "어떤 업종·업무에서 쓸 vault인가요?" (자유 입력, 예: "동네 카페", "법무법인", "1인 프리랜서 디자이너")
2. **팀 규모**: 1인 / 소규모(2~10명) / 조직(10명+) — 이후 raw/wiki 접근 권한 안내 문구에 반영(이번 버전은 안내만, 실제 권한 제어는 하지 않음).
3. **고정 제약**: "이 업무에서 절대 바뀌지 않는 제약이 있나요? (예산, 규정, 인력 등)" — 자유 입력. 답이 "모르겠다"면 빈 문자열로 두고 open-questions.md에 큐로 남긴다.
4. **역할 분담 필요 여부**: "이 업무에 여러 역할(예: 주문 담당, 재고 담당)이 있고 그것마다 다른 규칙을 적용하고 싶나요?"
   - "아니오"면 5번으로 진행.
   - "예"면 역할 이름을 나열받아 라우터 "작업별 로드" 표에 들어갈 줄(`domain_rows`)과 "절대 규칙"에 들어갈 줄(`domain_absolute_rules`)을 함께 구성한다. 이 스킬은 역할 목록을 강제하지 않는다 — 미리 정해둔 고정 역할 세트를 만들지 않고, 사용자가 부른 이름 그대로 표에 적는다.

## 실행

답변을 모은 뒤, vault root(현재 작업 디렉터리)를 대상으로 스크립트를 호출한다:

```bash
python <plugin-install-path>/skills/setup-wizard/generate.py
```

이 스크립트는 CLI 인자를 직접 받지 않는다 — 에이전트가 `generate_vault()` 함수를
아래 시그니처로 직접 호출하는 파이썬 한 줄을 실행하는 방식을 쓴다:

```bash
python -c "
import sys; sys.path.insert(0, r'<plugin-install-path>/skills/setup-wizard')
from generate import generate_vault
created = generate_vault(
    target_dir='.',
    domain='<1번 답변>',
    constraints='<3번 답변, 없으면 빈 문자열>',
    domain_rows='<4번에서 구성한 표 줄, 없으면 빈 문자열>',
    domain_absolute_rules='<4번에서 구성한 절대 규칙 줄, 없으면 빈 문자열>',
)
print(f'{len(created)}개 파일 생성 완료')
"
```

## 마무리

1. `constraints`가 빈 문자열이었으면, `tasks/questions/open-questions.md`에 "고정 제약 미확인" 항목을 하나 추가한다 (형식은 `.claude/rules/core/open-questions.md` 규칙 3번 참고).
2. 생성 직후 `python .claude/skills/verify-docs/check.py`를 1회 실행해 "OK: 6개 검사 통과"를 확인한다.
3. 사용자에게 안내: "vault가 생성됐습니다. 이제 실무 자료를 `AI-Sessions/raw/`에 넣고 `ingest`라고 말하면 가공을 시작합니다. 확인이 더 필요한 항목은 `tasks/questions/open-questions.md`에 쌓여 있으니 먼저 훑어보세요."
```

- [ ] **Step 2: 커밋**

```bash
cd "/c/AURA_DEV/V1/claude-vault-framework"
git add skills/setup-wizard/SKILL.md
git commit -m "feat: setup-wizard SKILL.md — 온보딩 인터뷰 흐름"
```

---

## Task 6: 플러그인 매니페스트 작성 및 엔드투엔드 검증

**Files:**
- Create: `C:\AURA_DEV\V1\claude-vault-framework\.claude-plugin\marketplace.json`

**Interfaces:**
- Consumes: Task 3(`skills/verify-docs/`), Task 5(`skills/setup-wizard/`) — 두 스킬 디렉터리가 실재해야 매니페스트가 유효하다.

- [ ] **Step 1: marketplace.json 작성**

`C:\AURA_DEV\V1\claude-vault-framework\.claude-plugin\marketplace.json`:
```json
{
  "name": "claude-vault-framework",
  "version": "0.1.0",
  "description": "업종 무관 지식관리 프레임워크 — Raw/Wiki 분리, 다중 검증(verify-docs), 온보딩 인터뷰(setup-wizard)",
  "skills": [
    "skills/setup-wizard",
    "skills/verify-docs"
  ]
}
```

- [ ] **Step 2: 엔드투엔드 수동 검증 — 가상 업종으로 generate_vault 실행**

```bash
mkdir -p /tmp/test-cafe-vault
cd "/c/AURA_DEV/V1/claude-vault-framework"
python -c "
import sys; sys.path.insert(0, 'skills/setup-wizard')
from generate import generate_vault
created = generate_vault(
    target_dir='/tmp/test-cafe-vault',
    domain='동네 카페',
    constraints='1인 운영, 예산 월 20만원 이내',
)
print(f'{len(created)}개 파일 생성 완료')
for f in created:
    print(f)
"
```

Expected: 파일 목록에 `CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/rules/core/*.md` 4개, `.claude/skills/verify-docs/check.py`, `.claude/skills/verify-docs/SKILL.md`, `tasks/questions/open-questions.md`, `log.md`, `index.md` 총 10개가 출력된다.

- [ ] **Step 3: 생성된 vault에서 verify-docs 실행**

```bash
cd /tmp/test-cafe-vault
python .claude/skills/verify-docs/check.py
```

Expected: `OK: 6개 검사 통과`

- [ ] **Step 4: 생성된 vault에 AURA 전용 문자열이 없는지 최종 확인**

```bash
grep -riE "우노Q|아우라|AURA|backend/|frontend/" /tmp/test-cafe-vault -r
```

Expected: 매치 없음(빈 출력).

- [ ] **Step 5: 임시 테스트 vault 정리**

```bash
rm -rf /tmp/test-cafe-vault
```

- [ ] **Step 6: 커밋**

```bash
cd "/c/AURA_DEV/V1/claude-vault-framework"
git add .claude-plugin/marketplace.json
git commit -m "feat: 플러그인 매니페스트 추가"
```

---

## 이번 계획에서 하지 않는 것 (스펙 "이번 범위에서 하지 않는 것" 그대로 유지)

- GitHub에 실제로 `claude-vault-framework` 저장소를 만들고 push하는 것 — 로컬 git 저장소까지만. 원격 저장소 생성·push는 사용자 승인 후 별도 단계로 진행한다([[.claude/rules/core/git.md]]의 "저장소 생성/push는 사용자 승인" 원칙을 그대로 적용).
- 업종별 사전 제작 템플릿 다수 준비.
- AURA 6개 에이전트 이식.
- 비개발자용 경량 배포(2계층).
- marketplace.json을 공개 marketplace에 등록.
- pretooluse-guard.py 같은 훅 이식.

## 검증 방법 (요약)

1. Task 1 Step 5, Task 3 Step 2, Task 6 Step 4의 grep 검증 — AURA 전용 문자열이 결과물에 전혀 없어야 한다.
2. Task 3 Step 3 — `check.py --self-test`가 원본과 동일하게 통과해야 한다.
3. Task 4 Step 6 — `generate.py`의 자체 테스트(`test_generate.py`)가 통과해야 한다(이 테스트 안에서 실제로 이식된 `check.py`를 서브프로세스로 돌려 "OK"를 확인하므로 이중 검증이 된다).
4. Task 6 Step 3 — 가상 업종("동네 카페")으로 생성한 vault에서 `verify-docs`가 "OK: 6개 검사 통과"를 출력해야 한다.
