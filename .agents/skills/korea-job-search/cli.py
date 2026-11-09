#!/usr/bin/env python3
"""Official-first Korea job-search bridge for the bundled job-searcher integration."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INTEGRATION = REPO_ROOT / "integrations" / "job-searcher"

SOURCES: dict[str, dict[str, str]] = {
    "work24": {"skill": "work24-collect", "mode": "enterprise_member_api", "label": "고용24(승인된 기업회원 전용)"},
    "naver": {"skill": "naver-recruit-collect", "mode": "first_party_api", "label": "네이버 채용"},
    "toss": {"skill": "toss-career-collect", "mode": "first_party_api", "label": "토스 채용"},
    "coupang": {"skill": "coupang-collect", "mode": "first_party_ats", "label": "쿠팡 채용"},
    "apple": {"skill": "apple-jobs-collect", "mode": "first_party_page", "label": "Apple Jobs"},
    "sap": {"skill": "sap-jobs-collect", "mode": "first_party_page", "label": "SAP Jobs"},
    "worldjobplus": {"skill": "worldjobplus-collect", "mode": "public_government_page", "label": "월드잡플러스"},
    "weworkremotely": {"skill": "weworkremotely-collect", "mode": "public_rss", "label": "We Work Remotely"},
    "jobkorea": {"skill": "jobkorea-collect", "mode": "public_page_opt_in", "label": "잡코리아"},
    "saramin": {"skill": "saramin-collect", "mode": "public_page_opt_in", "label": "사람인"},
    "wanted": {"skill": "wanted-collect", "mode": "public_page_opt_in", "label": "원티드"},
    "jumpit": {"skill": "jumpit-collect", "mode": "public_page_opt_in", "label": "점핏"},
    "rallit": {"skill": "rallit-collect", "mode": "public_page_opt_in", "label": "랠릿"},
    "incruit": {"skill": "incruit-collect", "mode": "public_page_opt_in", "label": "인크루트"},
}
DEFAULT_SOURCES = ("naver", "toss", "coupang")
OPT_IN_MODES = {"public_page_opt_in"}


def integration_root() -> Path:
    override = os.environ.get("JOB_SEARCHER_ROOT")
    return Path(override).expanduser().resolve() if override else DEFAULT_INTEGRATION


def parse_sources(values: list[str] | None) -> list[str]:
    if not values:
        env_value = os.environ.get("KOREA_JOB_SOURCES")
        values = [env_value] if env_value else list(DEFAULT_SOURCES)
    selected: list[str] = []
    for value in values:
        for item in value.split(","):
            key = item.strip().lower()
            if not key:
                continue
            if key not in SOURCES:
                raise ValueError(f"지원하지 않는 소스: {key}. 'sources' 명령으로 목록을 확인하세요.")
            if key not in selected:
                selected.append(key)
    return selected


def collector_path(root: Path, source: str) -> Path:
    return root / "skills" / SOURCES[source]["skill"] / "collect.py"


def collector_command(root: Path, source: str, args: argparse.Namespace) -> list[str]:
    command = [sys.executable, str(collector_path(root, source)), "--query", args.query, "--limit", str(args.limit), "--timeout", str(args.timeout)]
    if source == "work24":
        for value in args.region:
            command.extend(("--region", value))
        for value in args.occupation:
            command.extend(("--occupation", value))
        for value in args.employment:
            command.extend(("--employment", value))
        if args.career:
            command.extend(("--career", args.career))
        if args.min_career_months is not None:
            command.extend(("--min-career-months", str(args.min_career_months)))
        if args.max_career_months is not None:
            command.extend(("--max-career-months", str(args.max_career_months)))
        if args.education:
            command.extend(("--education", args.education))
        if args.jobage in (1, 3, 7, 14, 30):
            command.extend(("--jobage", str(args.jobage)))
    return command


def execute_collector(root: Path, source: str, args: argparse.Namespace) -> tuple[str, list[dict[str, Any]], str | None]:
    path = collector_path(root, source)
    if not path.is_file():
        return source, [], f"수집기 파일이 없습니다: {path}"
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        completed = subprocess.run(
            collector_command(root, source, args), cwd=root, env=env,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=max(args.timeout + 10, 20), check=False,
        )
    except subprocess.TimeoutExpired:
        return source, [], f"{args.timeout + 10}초 안에 완료되지 않았습니다"
    if completed.returncode != 0:
        message = completed.stderr.strip().splitlines()[-1] if completed.stderr.strip() else f"exit {completed.returncode}"
        return source, [], message
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return source, [], f"JSON 출력 해석 실패: {exc}"
    if not isinstance(payload, list):
        return source, [], "수집기 출력이 JobPosting 배열이 아닙니다"
    return source, [row for row in payload if isinstance(row, dict)], None


def normalize(row: dict[str, Any], source: str) -> dict[str, Any] | None:
    title = str(row.get("title") or "").strip()
    url = str(row.get("url") or "").strip()
    if not title or not url:
        return None
    external_id = str(row.get("external_id") or "").strip()
    if not external_id:
        external_id = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    posted = row.get("posted_at")
    posted_date = str(posted)[:10] if posted else None
    return {
        "id": f"{source}:{external_id}",
        "title": title,
        "company": row.get("company"),
        "location": row.get("location"),
        "date": posted_date,
        "url": url,
        "description": row.get("snippet"),
        "deadline": row.get("deadline"),
        "deadlineDate": row.get("deadline_date"),
        "status": row.get("status") or "unknown",
        "employmentType": row.get("employment_type"),
        "salary": row.get("salary"),
        "source": source,
    }


def recent_enough(row: dict[str, Any], days: int | None) -> bool:
    if not days or not row.get("date"):
        return True
    try:
        return date.fromisoformat(row["date"]) >= date.today() - timedelta(days=days)
    except ValueError:
        return True


def run_search(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    root = integration_root()
    if not root.is_dir():
        return {"meta": {"count": 0, "errors": {"integration": f"job-searcher 통합 경로가 없습니다: {root}. git submodule update --init --recursive를 실행하세요."}}, "results": []}, 1
    selected = parse_sources(args.source)
    opt_in = [name for name in selected if SOURCES[name]["mode"] in OPT_IN_MODES]
    if opt_in and not args.allow_public_pages:
        names = ", ".join(opt_in)
        raise ValueError(f"공개 검색 페이지 소스({names})는 --allow-public-pages로 명시적으로 선택해야 합니다. 각 사이트의 최신 이용조건을 먼저 확인하세요.")

    gathered: list[dict[str, Any]] = []
    errors: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=min(4, len(selected))) as pool:
        futures = {pool.submit(execute_collector, root, source, args): source for source in selected}
        for future in as_completed(futures):
            source, rows, error = future.result()
            if error:
                errors[source] = error
                continue
            for row in rows:
                normalized = normalize(row, source)
                if normalized and recent_enough(normalized, args.jobage):
                    gathered.append(normalized)

    unique: dict[str, dict[str, Any]] = {}
    for row in gathered:
        unique.setdefault(row["url"], row)
    results = sorted(unique.values(), key=lambda row: (row.get("date") or "", row["title"]), reverse=True)[: args.limit]
    payload = {
        "meta": {
            "count": len(results),
            "sources": selected,
            "errors": errors,
            "policy": "official-first; public-page collectors require explicit opt-in",
        },
        "results": results,
    }
    return payload, 1 if not results and errors else 0


def render_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "검색 결과가 없습니다."
    headers = ("소스", "공고", "회사", "지역", "등록일")
    widths = (12, 34, 22, 18, 10)
    def line(values: tuple[str, ...]) -> str:
        return "  ".join(str(value or "-")[:width].ljust(width) for value, width in zip(values, widths))
    output = [line(headers), "-" * (sum(widths) + 8)]
    for row in rows:
        output.append(line((row["source"], row["title"], row.get("company") or "-", row.get("location") or "-", row.get("date") or "-")))
    return "\n".join(output)


def render_plain(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "검색 결과가 없습니다."
    blocks = []
    for row in rows:
        blocks.append("\n".join((row["title"], f"  {row.get('company') or '-'} · {row.get('location') or '-'} · {row.get('date') or '-'}", f"  {row['url']}")))
    return "\n\n".join(blocks)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="한국 채용 통합 검색(job-searcher 브리지)")
    sub = parser.add_subparsers(dest="command", required=True)
    search = sub.add_parser("search", help="여러 한국 채용 소스를 공식 경로 우선으로 검색")
    search.add_argument("--query", "-q", required=True)
    search.add_argument("--source", action="append", help="기본값 naver,toss,coupang. work24는 승인된 기업회원만 명시적으로 지정")
    search.add_argument("--allow-public-pages", action="store_true", help="공개 검색 페이지 수집기를 명시적으로 허용")
    search.add_argument("--region", action="append", default=[])
    search.add_argument("--occupation", action="append", default=[])
    search.add_argument("--employment", action="append", default=[])
    search.add_argument("--career")
    search.add_argument("--min-career-months", type=int)
    search.add_argument("--max-career-months", type=int)
    search.add_argument("--education")
    search.add_argument("--jobage", type=int, default=14)
    search.add_argument("--limit", "-n", type=int, default=20)
    search.add_argument("--timeout", type=int, default=25)
    search.add_argument("--format", choices=("json", "table", "plain"), default="json")
    sub.add_parser("sources", help="지원 소스와 접근 방식을 JSON으로 표시")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "sources":
        print(json.dumps({name: metadata for name, metadata in SOURCES.items()}, ensure_ascii=False, indent=2))
        return 0
    if args.limit < 1 or args.limit > 100:
        print(json.dumps({"error": "--limit은 1~100이어야 합니다", "code": "BAD_ARG"}, ensure_ascii=False), file=sys.stderr)
        return 1
    try:
        payload, code = run_search(args)
    except ValueError as exc:
        print(json.dumps({"error": str(exc), "code": "BAD_ARG"}, ensure_ascii=False), file=sys.stderr)
        return 1
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif args.format == "table":
        print(render_table(payload["results"]))
    else:
        print(render_plain(payload["results"]))
    if payload["meta"].get("errors"):
        print(json.dumps({"warnings": payload["meta"]["errors"]}, ensure_ascii=False), file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
