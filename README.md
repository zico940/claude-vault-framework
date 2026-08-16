# Claude Vault Framework

업종 무관 지식관리 프레임워크 — Claude Code 스킬. Codex CLI에서도 verify-docs
재검증을 쓸 수 있다(설치 시 사용 CLI를 선택).

한 문장으로: **원본 자료(raw)와 가공된 지식(wiki)을 분리하고, 확인 안 된 사실은
큐에 쌓아 순서대로 캐물으며(uncertainty), 문서가 늘어나도 서로 어긋나지
않는지 기계적으로 재검증(verify-docs)하는** vault를 업종별로 즉석 조립해준다.

---

## 왜 필요한가

AI 에이전트와 여러 세션에 걸쳐 같은 업무 맥락을 공유하다 보면 흔히 이런 문제가 생긴다.

- 에이전트가 모르는 걸 그럴듯하게 추측해서 답한다.
- "확정 필요"라고 적힌 항목을 누군가 임의로 "확정됨"으로 바꿔버린다.
- 문서 A에는 반영됐는데 문서 B에는 낡은 내용이 남아 서로 모순된다.
- 원본 자료(계약서, 회의록 등)를 가공하다 실수로 고쳐버린다.

이 프레임워크는 이 네 가지를 각각 **uncertainty 규칙**, **권장안/답변 완료 구분**,
**verify-docs 재검증**, **raw/wiki 분리**로 막는다. 실제로 겪은 사고를 규칙으로
박아넣은 것이라, 규칙마다 "왜 이게 필요한가"가 명시되어 있다.

---

## 설치

이 저장소를 클론한 뒤 `setup-wizard/` 폴더를 스킬 디렉터리로 복사한다. 별도
설치 명령이나 marketplace 등록 절차는 없다 — 폴더를 아래 위치에 두면 Claude
Code가 자동으로 스킬을 인식한다.

**모든 프로젝트에서 쓰고 싶으면 (사용자 전역)**

```bash
git clone https://github.com/zico940/claude-vault-framework.git
cp -r claude-vault-framework/setup-wizard ~/.claude/skills/setup-wizard
```

**특정 프로젝트에서만 쓰고 싶으면 (프로젝트 로컬)**

```bash
git clone https://github.com/zico940/claude-vault-framework.git
cp -r claude-vault-framework/setup-wizard <프로젝트 경로>/.claude/skills/setup-wizard
```

---

## 사용법

설치 후 대화에서 `"vault 초기 설정해줘"` 또는 `/setup-wizard`라고 말하면
`setup-wizard` 스킬이 아래 순서로 인터뷰한다 (한 번에 하나씩 질문).

| 순서 | 질문 | 답이 없으면 |
|---|---|---|
| 1 | 업종/도메인 (자유 입력, 예: "동네 카페", "법무법인") | — 필수 |
| 2 | 팀 규모 (1인 / 소규모 2~10명 / 조직 10명+) | 안내 문구에만 반영 (실제 권한 제어는 없음) |
| 3 | 고정 제약 (예산, 규정, 인력 등) | 빈 문자열로 두고 `open-questions.md`에 큐로 등록 |
| 4 | 역할 분담 필요 여부 (있으면 역할 이름 나열) | "아니오"면 건너뜀. 미리 정해진 역할 세트는 없음 — 사용자가 부른 이름 그대로 씀 |
| 5 | 사용 CLI (Claude Code만 / Codex만 / 둘 다) | `platform` 값(`claude`/`codex`/`both`)으로 매핑 |

인터뷰가 끝나면 `generate.py`의 `generate_vault(...)`를 호출해 vault(라우터,
규칙, 폴더 구조)를 생성하고, 직후 `verify-docs`의 `check.py`를 1회 실행해
`OK: 6개 검사 통과`를 확인한다.

이 스킬 자신도 프레임워크의 uncertainty 원칙을 따른다 — 인터뷰에서 답이 안
나온 항목은 추측해서 채우지 않고 `tasks/questions/open-questions.md`에 큐로
남긴다.

생성이 끝나면 실무 자료를 `AI-Sessions/raw/`에 넣고 `ingest`라고 말해 가공을
시작하면 된다.

---

## 저장소 구조

```
setup-wizard/
  SKILL.md                        — 온보딩 인터뷰 흐름 안내 (스킬 진입점)
  generate.py                     — 인터뷰 답변으로 vault를 생성하는 로직
  verify_docs.py                  — 문서 정합성 검증기 (생성된 vault에 check.py로 배치, 플랫폼 무관)
  verify_docs_SKILL.md            — Claude Code용 검증기 안내 (SKILL.md로 배치)
  verify_docs_AGENTS.md.template  — Codex용 검증기 안내 (AGENTS.md에 append/생성)
  templates/
    CLAUDE.md.template            — vault 지식관리 규칙 원본
    router.md.template            — .claude/CLAUDE.md 라우터 원본
    rules/core/
      file-ops.md                 — 경로/폴더/삭제 규칙
      uncertainty.md               — 모르면 먼저 물어보는 규칙
      open-questions.md            — 확인 필요 사항 큐 관리 규칙
      rule-authoring.md            — 새 규칙 작성 시 자체검증 규칙
```

`generate_vault(..., platform=...)`의 `platform`(`"claude"` / `"codex"` /
`"both"`)에 따라 verify-docs 재검증 트리거의 배치 위치가 갈린다. 검증 로직
(`check.py`) 자체는 두 경우 모두 동일하며, 라우터 파일을 `.claude/CLAUDE.md`와
`AGENTS.md` 양쪽에서 자동 탐지한다.

---

## 생성되는 vault의 동작 원리

`setup-wizard`를 실행하면 대상 디렉터리에 아래 파일들이 만들어진다. 이 문서들이
곧 vault가 따르는 "규칙"이며, 서로 이렇게 맞물려 동작한다.

```
vault-root/
  CLAUDE.md                       ← 지식관리 규칙 원본 (단일 소스)
  .claude/
    CLAUDE.md                     ← 라우터: 규칙 본문 대신 "무엇을 언제 읽을지"만 담음
    rules/core/
      file-ops.md
      uncertainty.md
      open-questions.md
      rule-authoring.md
    skills/verify-docs/
      check.py                    ← 문서 정합성 기계 검증기
      SKILL.md                    ← (platform=claude/both일 때)
  AGENTS.md                       ← (platform=codex/both일 때, verify-docs 안내 append)
  AI-Sessions/
    raw/                          ← 원본 자료, 절대 수정·삭제 금지
    wiki/                         ← 가공된 지식 (sources/concepts/decisions/errors/projects)
    conversations/                ← 세션 인수인계 기록
  tasks/questions/open-questions.md  ← 확인 필요 사항 큐
  log.md                          ← 작업 로그 + self-report flag
```

### 1. 라우터 (`.claude/CLAUDE.md`) — "항상 로드 vs 작업별 로드"

`.claude/CLAUDE.md`는 규칙 본문을 직접 담지 않는다. 대신 두 종류로 나눠 "언제
무엇을 읽을지"만 지시한다.

- **항상 로드**: `file-ops.md`, `uncertainty.md`, `open-questions.md` — 매 세션 필수로 참조.
- **작업별 로드**: 새 규칙 작성 시 `rule-authoring.md`, 재검증 요청 시
  `verify-docs` 스킬, 업종별 추가 규칙(`{{domain_rows}}`)처럼 필요할 때만 로드.

같은 파일이 양쪽에 중복 등재되면 `verify-docs`의 `[router-dup]` 검사가 잡아낸다.

### 2. Raw / Wiki 분리 (`CLAUDE.md`)

- `AI-Sessions/raw/`: 계약서, 회의록, 고객 문의 원문처럼 나중에 근거로 다시
  확인해야 하는 **불변 원본**. 에이전트는 이 안의 파일을 수정하지 않는다.
- `AI-Sessions/wiki/`: raw를 바탕으로 만든 요약·판단·결정·기획 자료. 5개
  카테고리(sources/concepts/decisions/errors/projects)로 나뉜다.
- **저장 필터**: `save`를 실행하기 전 "반복 재사용되는가 / 인수인계에 필요한가
  / 의사결정 근거인가 / 재발 방지용 실패 기록인가 / 팀 공통 규칙인가" 5가지 중
  하나도 해당 없으면 wiki에 저장하지 않는다. 무분별한 저장이 맥락을 오염시키기
  때문이다.

### 3. Uncertainty — 모르면 먼저 물어본다 (`rules/core/uncertainty.md`)

핵심은 **"계획/문서에 적힌 내용"과 "실제로 확인된 현황"을 항상 구분**하는 것.
실제 배포 상태, `TBD`/`미정` 표시된 값, 존재 여부가 불확실한 파일, 해석이
갈리는 요구사항을 만나면 추측하지 않고 사용자에게 먼저 묻는다.

가장 중요한 세부 규칙 — **권장안(✅)과 답변 완료는 다르다**:

| 구분 | 표기 | 의미 | 사실로 쓸 수 있는가 |
|---|---|---|---|
| 권장안 | `✅ 권장: {안} ({근거})` | 에이전트 제안, 미승인 | ❌ 아니오 |
| 답변 완료 | `**답변 완료**: {실제 값}` | 사용자가 실제로 답변한 것 | ✅ 예 |

에이전트의 권장안만 보고 다른 문서를 "확정됨"으로 바꾸는 것은 금지된다. 이건
실제로 발생했던 사고를 막기 위한 규칙이다.

### 4. Open-Questions 큐 (`rules/core/open-questions.md`)

확인 안 된 사실을 발견할 때마다 즉석 질문으로 흘려보내지 않고
`tasks/questions/open-questions.md`에 아래 형식으로 쌓는다.

```
### Q{n} — {제목}  [지금 필요 | {기능} 착수 시]
- 배경: 어느 문서의 어떤 공백에서 나왔는지
- 경우의 수: a. ... b. ...
- ✅ 권장: {안} ({근거})
- 막고 있는 것: 이 답이 없으면 진행 못 하는 작업
- 반영 대상: {문서 경로}
```

- 질문이 완전히 해소되면 **삭제**한다 (완료 표시만 하고 남겨두지 않는다).
- 일부만 확정되면 `**답변 완료**: ...`를 추가하고 잔여 질문만 남긴다.
- 사용자가 질문을 다시 받지 않고 대화 중 관련 사실을 이미 확정/실행했다면
  그것도 "답변"으로 취급하고 즉시 반영한다 — 답변이 왔는데 큐가 갱신 안 된 채
  방치되는 사고를 막기 위한 규칙이다.
- 문서 맨 위 "0. 먼저 답해주세요" 섹션에는 다른 질문을 막고 있는 **선행 질문**만
  모아 답변 우선순위를 제시한다. 기반 환경(무엇이 어디 있는지, 누가 뭘 담당하는지)이
  세부 사항보다 항상 먼저다.

### 5. verify-docs — 문서 정합성 재검증

문서가 늘어나고 수정되면서 같은 사실이 여러 문서에 어긋나게 남는 걸 막는
기계 검증기다. `"재검증"`, `"검증"`, `"충돌 확인"`, `"lint"`라고 말하거나
open-questions 항목을 2개 이상 반영한 뒤 실행한다.

```bash
python .claude/skills/verify-docs/check.py
```

`check.py`가 잡는 6가지 검사:

| 분류 | 의미 | 조치 |
|---|---|---|
| `[dangling]` | 실체 없는 Q번호를 현재형으로 가리킴 | 실제 반영 위치로 교체하거나 낡은 서술을 최신화 |
| `[summary]` | 상단 표 ↔ 본문 헤더 ↔ 하단 안내 불일치 | 본문을 진실로 보고 요약을 맞춤 |
| `[list]` | Q번호를 인용하는 문서가 재검증 대상 표에 없음 | `open-questions.md` 표에 그 파일 추가 |
| `[missing]` | 표가 가리키는 경로가 실재하지 않음 | 경로 수정 또는 표에서 제거 |
| `[flag]` | `log.md`의 미해결 self-report | 조치 후 `flag 해결(원 타임스탬프): ...` 줄 추가 |
| `[router-dup]` | 라우터에서 "항상 로드"·"작업별 로드" 중복 등재 | "항상 로드"만 남기고 제거 |

**핵심 원칙은 전체 재독 금지** — 스크립트가 지목한 `파일:줄번호`만 열어서
고친다. 검증 범위를 즉흥적으로 넓히면 새 불일치가 계속 나온다.

기계 검사 뒤에는 사람이 판단하는 3단계 의미 검증(다른 문서가 같은 사실을
다르게 서술하는가 / 실무 문서가 이미 확정된 걸 "확정 필요"로 남겨뒀는가 /
`log.md`에 이번 변경을 기록했는가)만 고정으로 확인한다. 두 문서가 같은 사실을
다르게 말하는 **의미적 모순**은 기계가 100% 잡지 못하는 한계가 있다 — 그래서
사람 판단이 필요한 지점을 이 3개로 최소화해둔 것이다.

과거 기록(`log.md`, 각 문서의 `## 변경 이력`)은 그 시점엔 맞는 서술이므로
검사 대상에서 제외된다. 단 `log.md`의 미해결 `flag` 줄만은 예외로 검사한다.

검사기 자체가 의심스러우면:

```bash
python .claude/skills/verify-docs/check.py --self-test
```

### 6. Self-Report Flag (`CLAUDE.md`)

작업 중 파일을 못 읽었거나, 규칙을 알면서도 못 지켰거나, 어떤 문서가 최신인지
확신이 안 서는 상황을 만나면 조용히 넘어가지 않고 `log.md`에 아래 형식으로
남긴다.

```
YYYY-MM-DD HH:mm | flag | [read-fail|rule-skip|stale?] 한 줄 설명 | 영향받는 파일/규칙 경로
```

해결되면:

```
YYYY-MM-DD HH:mm | lint | flag 해결(원래 flag 줄의 YYYY-MM-DD HH:mm): 조치 요약 | [[고친 파일들]]
```

`verify-docs`의 `[flag]` 검사가 미해결 flag를 기계적으로 찾아낸다.

### 7. rule-authoring — 새 규칙을 쓸 때 자체검증

`.claude/rules/**` 아래 새 규칙 파일을 추가하거나 로드 방식을 바꿀 때 저장
전에 확인하는 체크리스트:

1. **로드 시점 자기 추적**: "항상", "세션 시작 시" 같은 상시성 지시가
   실제로 상시 로드 경로에 있는가? 트리거 로드에만 있으면 그 지시는 죽은
   지시다.
2. **중복 등재 확인**: 같은 규칙 파일이 "항상 로드"·"작업별 로드" 양쪽에
   없는가.
3. **참조 무결성**: Q번호처럼 나중에 바뀌는 값보다 안정적인 사실을 인용한다.
4. **verify-docs 재실행**: 새 문서가 Q번호나 "확정"류 표현을 담으면
   재검증 대상 표에 추가한다.

이 규칙은 "세션 시작 시 확인하라"는 상시 지시를 트리거 로드에만 등록해
영영 실행되지 않았던 실제 사고를 막기 위해 존재한다.

### 8. Codex 지원 (`platform` 옵션)

`generate_vault(..., platform=...)`가 받는 값:

- `"claude"`: `.claude/skills/verify-docs/SKILL.md`로 트리거 배치.
- `"codex"`: `AGENTS.md`에 verify-docs 안내문을 append(없으면 새로 생성).
- `"both"`: 둘 다 배치.

검증 로직(`check.py`)은 플랫폼과 무관하게 항상 동일하게 동작하며, 라우터
파일을 `.claude/CLAUDE.md`와 `AGENTS.md` 양쪽에서 자동으로 찾는다. 즉 CLI가
바뀌어도 검증 결과는 달라지지 않는다 — 안내문이 어디 적혀 있느냐만 다르다.

---

## 문서 작성 포맷

새 wiki 문서는 가능하면 아래 프론트매터 형식을 따른다.

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

## 위키링크 규칙

문서 간 링크(`[[...]]`)는 반드시 **vault root 기준 절대 경로**로 쓴다. 예:
`[[.claude/rules/core/file-ops.md]]`. `../CLAUDE.md` 같은 상대경로는 Obsidian이
vault root 기준으로 해석하기 때문에 깨진다 — 특히 `.claude/rules/` 아래 문서에서
`../CLAUDE.md`는 루트 `CLAUDE.md`와 `.claude/CLAUDE.md` 중 어느 쪽인지 모호해진다.
