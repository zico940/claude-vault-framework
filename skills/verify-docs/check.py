#!/usr/bin/env python3
"""문서 간 정합성 기계 검증기 (읽기 전용).

`tasks/questions/open-questions.md`의 Q번호를 정답 집합으로 두고, vault 문서들이
실체 없는 번호를 현재형으로 가리키는지 등 5가지를 검사한다.

이 스크립트는 **기계적으로 판정 가능한 것만** 다룬다. 두 문서가 같은 사실을
다르게 서술하는 의미적 모순은 잡지 못하며, 그건 SKILL.md의 3단계가 담당한다.

사용법:
    python .claude/skills/verify-docs/check.py     # vault root에서 실행
    python .claude/skills/verify-docs/check.py --self-test
"""
import os
import re
import sys

# Windows 콘솔(cp949 등)에서 findings 출력의 em dash/한글이 UnicodeEncodeError로
# 죽는 걸 막는다. findings가 0건일 땐 이 경로를 안 타서 오래 안 드러났던 결함.
for _stream in (sys.stdout, sys.stderr):
    if getattr(_stream, "encoding", "").lower() not in ("utf-8", "utf8"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

QUEUE = "tasks/questions/open-questions.md"
RULE = ".claude/rules/core/open-questions.md"
LOG = "log.md"
ROUTER = ".claude/CLAUDE.md"

Q_HEADER = re.compile(r"^### (Q\d+)")
# 뒤쪽 \b를 쓰면 안 된다: 파이썬 \b는 유니코드 기준이라 "Q99를"처럼 한글 조사가
# 바로 붙으면 경계가 성립하지 않아 통째로 놓친다. 앞 경계만 확인하고, 뒤는
# 숫자가 더 안 오는지만 본다(Q1이 Q16에 매칭되는 것 방지).
Q_REF = re.compile(r"(?<![A-Za-z0-9])Q\d+(?!\d)")

# log.md의 self-report flag 줄과, 그걸 해소했다고 밝히는 lint 줄.
FLAG_LINE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}) \| flag \| (.+)$")
FLAG_RESOLVED_REF = re.compile(r"flag 해결\(([^)]+)\)")

# 과거 시점 기록 — 그 시점엔 맞는 서술이므로 dangling이어도 정상이다.
# 이 화이트리스트가 없으면 매 실행마다 오탐 10건이 나와 도구가 무시당한다.
HISTORY_FILES = ("log.md",)
HISTORY_DIRS = ("AI-Sessions/wiki/decisions/", "AI-Sessions/wiki/dev-tasks/")
HISTORY_SECTIONS = ("## 변경 이력", "## Log")
# 이미 "삭제됨"이라고 명시한 인용은 추적 가능하므로 결함이 아니다.
HANDLED = ("답변 완료", "삭제됨")

# 외부(vendored) 스킬 — 이 프로젝트의 Q번호 체계와 무관한 제3자 콘텐츠다.
# `.agents/skills/`를 Windows Junction으로 `.claude/skills/`에 연결해 쓰는 경우
# 같은 파일이 두 경로로 중복 스캔되는 문제도 겸해 막는다.
VENDOR_DIRS = (".agents/",)


def norm(path):
    return path.replace("\\", "/")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def is_history_file(rel):
    return rel in HISTORY_FILES or any(rel.startswith(d) for d in HISTORY_DIRS)


def live_lines(text):
    """현재 상태를 서술하는 줄만 (번호, 내용)으로 돌려준다.

    '## 변경 이력' 같은 과거 기록 섹션에 진입하면 그 이후는 전부 건너뛴다.
    """
    out = []
    in_history = False
    for i, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            in_history = any(line.startswith(s) for s in HISTORY_SECTIONS)
        if in_history:
            continue
        if any(h in line for h in HANDLED):
            continue
        out.append((i, line))
    return out


def md_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules")]
        for name in filenames:
            if name.endswith(".md"):
                full = os.path.join(dirpath, name)
                rel = norm(os.path.relpath(full, root))
                if any(rel.startswith(v) for v in VENDOR_DIRS):
                    continue
                yield rel, full


def defined_questions(root):
    text = read(os.path.join(root, QUEUE))
    return {m.group(1) for line in text.splitlines() if (m := Q_HEADER.match(line))}


def check_dangling(root, defined, findings):
    """검사 1: 실체 없는 Q번호를 현재형으로 가리키는 참조."""
    for rel, full in md_files(root):
        # RULE은 검사 대상이 아니라 검사 기준을 적어둔 문서다. 여기 나오는 Q번호는
        # "과거 기록의 예시"로 인용된 것이라 실체가 없는 게 정상이다.
        if is_history_file(rel) or rel == RULE:
            continue
        for lineno, line in live_lines(read(full)):
            for ref in set(Q_REF.findall(line)):
                if ref not in defined:
                    findings.append(
                        f"{rel}:{lineno}: [dangling] {ref} 항목이 없는데 참조함"
                    )


def check_summary_sync(root, defined, findings):
    """검사 2: 상단 선행 표 ↔ 본문 헤더 ↔ 하단 안내 문구가 같은 집합인지."""
    text = read(os.path.join(root, QUEUE))
    lines = text.splitlines()

    top = set()
    for line in lines:
        if line.startswith("# A."):  # 선행 표는 A 섹션 앞에서 끝난다
            break
        # 첫 칸(**Q16**)만 선행 항목이다. 뒤 칸의 "함께 풀리는 것"은 파생 질문이라
        # 선행 집합에 넣으면 안 된다.
        if line.startswith("|"):
            first = line.split("|")[1] if len(line.split("|")) > 1 else ""
            if "**Q" in first:
                top.update(Q_REF.findall(first))

    for q in sorted(top - defined):
        findings.append(f"{QUEUE}: [summary] 선행 표의 {q}가 본문에 헤더로 없음")

    for i, line in enumerate(lines, 1):
        if "선행 항목" in line and "Q" in line:
            bottom = set(Q_REF.findall(line))
            if bottom != top:
                findings.append(
                    f"{QUEUE}:{i}: [summary] 하단 안내({','.join(sorted(bottom))})가 "
                    f"상단 표({','.join(sorted(top))})와 불일치"
                )
    return top


def listed_docs(root):
    """규칙 파일의 '재검증 대상 문서 목록' 표에 적힌 경로를 뽑는다."""
    text = read(os.path.join(root, RULE))
    section = text.split("## 재검증 대상 문서 목록")[-1].split("\n## ")[0]
    # 표의 행만 읽는다. 같은 섹션의 설명 산문에도 백틱 경로가 나오므로
    # 줄 전체를 훑으면 그것까지 "표에 적힌 경로"로 오인한다.
    paths = set()
    for line in section.splitlines():
        if line.startswith("|"):
            paths.update(re.findall(r"`([^`]+\.md)`", line))
    return paths


def check_list_freshness(root, findings):
    """검사 3: 고정 표가 낡았는지. 이 표가 낡는 게 이 체계의 단일 실패 지점이다."""
    listed = listed_docs(root)
    for rel, full in md_files(root):
        if rel in listed or is_history_file(rel) or rel == RULE:
            continue
        if rel.startswith(".claude/skills/"):
            continue
        # 기준은 "Q번호를 실제로 인용하는가"다. `open-questions` 문자열만 있는 경우는
        # 규칙 파일을 링크한 것일 뿐 Q사실을 복제한 게 아니므로 대상이 아니다.
        if any(Q_REF.search(line) for _, line in live_lines(read(full))):
            findings.append(
                f"{rel}: [list] Q번호를 인용하는데 {RULE} 표에 없음 (표에 추가 필요)"
            )


def check_paths_exist(root, findings):
    """검사 4: 표가 가리키는 경로가 실재하는지."""
    for path in sorted(listed_docs(root)):
        if not os.path.exists(os.path.join(root, path)):
            findings.append(f"{RULE}: [missing] 표가 가리키는 {path}가 존재하지 않음")


def check_unresolved_flags(root, findings):
    """검사 5: log.md에 남긴 self-report flag가 해결되지 않은 채 남아있는지."""
    path = os.path.join(root, LOG)
    if not os.path.exists(path):
        return
    lines = read(path).splitlines()

    resolved = set()
    for line in lines:
        m = FLAG_RESOLVED_REF.search(line)
        if m:
            resolved.add(m.group(1).strip())

    for i, line in enumerate(lines, 1):
        m = FLAG_LINE.match(line)
        if not m:
            continue
        ts, rest = m.group(1), m.group(2)
        if ts not in resolved:
            findings.append(f"{LOG}:{i}: [flag] 미해결 self-report ({ts}): {rest}")


def check_router_duplicate(root, findings):
    """검사 6: 라우터의 "항상 로드"와 "작업별 로드" 표에 같은 파일이 중복 등재됐는지.

    paused-work.md 신설(2026-08-15) 당시, 상시 로드해야 지켜지는 지시를 담은 파일을
    실수로 "작업별 로드"에만 넣었던 사례의 재발 방지. 여기서는 그 반대 방향(중복 등재)만
    기계로 잡는다 — "어느 쪽에 있어야 맞는가"는 사람 판단 영역이라 다루지 않는다.
    """
    path = os.path.join(root, ROUTER)
    if not os.path.exists(path):
        return
    text = read(path)
    if "## 항상 로드" not in text or "## 작업별 로드" not in text:
        return
    always_section = text.split("## 항상 로드", 1)[1].split("## 작업별 로드", 1)[0]
    rest = text.split("## 작업별 로드", 1)[1]
    per_task_section = rest.split("\n## ", 1)[0]

    # "항상 로드"는 최상위 리스트 항목(`- \`경로\` — 설명`)의 로드 대상 파일만 센다.
    # 설명문 안에서 다른 파일 경로를 언급하는 것(예: "이 규칙은 X를 큐로 관리")까지
    # 세면, 그 언급된 경로가 "작업별 로드" 표에도 있을 때 오탐이 난다 — 그건
    # "규칙은 상시 로드, 규칙이 다루는 데이터 파일은 트리거 로드"라는 정상 패턴이다.
    always = set(
        m.group(1)
        for line in always_section.splitlines()
        if line.startswith("- ")
        for m in [re.match(r"- `([^`]+\.md)`", line)]
        if m
    )
    per_task = set(re.findall(r"`([^`]+\.md)`", per_task_section))

    for dup in sorted(always & per_task):
        findings.append(
            f"{ROUTER}: [router-dup] {dup}가 '항상 로드'와 '작업별 로드' 양쪽에 중복 등재됨"
        )


def run(root):
    findings = []
    defined = defined_questions(root)
    check_dangling(root, defined, findings)
    check_summary_sync(root, defined, findings)
    check_list_freshness(root, findings)
    check_paths_exist(root, findings)
    check_unresolved_flags(root, findings)
    check_router_duplicate(root, findings)
    return findings


def self_test():
    """가짜 vault를 만들어 알려진 결함이 실제로 검출되는지 확인한다."""
    import shutil
    import tempfile

    root = tempfile.mkdtemp()
    try:
        for d in ("tasks/questions", ".claude/rules/core", "docs"):
            os.makedirs(os.path.join(root, d))

        def w(rel, text):
            with open(os.path.join(root, rel), "w", encoding="utf-8") as f:
                f.write(text)

        w(QUEUE, "# 0. 먼저\n| **Q1** | 질문 |\n\n# A. 인프라\n### Q1 — 있음\n")
        w(RULE, f"## 재검증 대상 문서 목록\n| `{QUEUE}` | 큐 |\n| `docs/gone.md` | 없는 파일 |\n")
        # "Q99를" — 한글 조사가 붙은 형태. 뒤쪽 \b를 쓰면 여기서 놓친다(회귀 방지).
        w("docs/live.md", "Q99를 지금 확인해야 함\n")
        w("log.md",
          "2026-01-01 | save | Q98 처리함\n"
          "2026-02-01 09:00 | flag | [read-fail] AGENTS.md를 못 읽음 | AGENTS.md\n"
          "2026-02-02 10:00 | lint | flag 해결(2026-02-01 09:00): 재확인 완료 | [[AGENTS.md]]\n"
          "2026-03-01 09:00 | flag | [rule-skip] 브랜치 규칙 확인 못 함 | .claude/rules/core/git.md\n")
        w("docs/hist.md", "## 변경 이력\n- Q97 반영\n")
        w(
            ROUTER,
            "## 항상 로드\n\n- `.claude/rules/core/dup-example.md` — 예시\n\n"
            "## 작업별 로드\n\n"
            "| 작업 | 파일 |\n|---|---|\n"
            "| 예시 | `.claude/rules/core/dup-example.md` |\n"
            "| 정상 | `.claude/rules/core/ok-example.md` |\n\n"
            "## 절대 규칙\n",
        )

        found = run(root)
        blob = "\n".join(found)

        assert "Q99" in blob, f"현재형 dangling 미검출: {found}"
        assert "Q98" not in blob, f"log.md 오탐(과거 기록): {found}"
        assert "Q97" not in blob, f"변경 이력 오탐: {found}"
        assert "gone.md" in blob, f"없는 경로 미검출: {found}"
        assert "docs/live.md: [list]" in blob, f"표 누락 미검출: {found}"
        assert "2026-03-01 09:00" in blob and "[flag]" in blob, f"미해결 flag 미검출: {found}"
        assert "2026-02-01 09:00" not in blob, f"해결된 flag 오탐: {found}"
        assert "dup-example.md" in blob and "[router-dup]" in blob, f"라우터 중복 미검출: {found}"
        assert "ok-example.md" not in blob, f"라우터 중복 오탐(단독 등재): {found}"
        print("self-test OK: 검출 5종 + 오탐 방지 4종 통과")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    if "--self-test" in sys.argv:
        self_test()
        return 0

    root = os.getcwd()
    if not os.path.exists(os.path.join(root, QUEUE)):
        print(f"vault root에서 실행하세요 ({QUEUE}를 찾을 수 없음)", file=sys.stderr)
        return 2

    findings = run(root)
    if not findings:
        print("OK: 6개 검사 통과")
        return 0

    for f in findings:
        print(f)
    print(f"\n{len(findings)}건 발견 — 위 항목만 열어서 고치세요 (전체 재독 불필요)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
