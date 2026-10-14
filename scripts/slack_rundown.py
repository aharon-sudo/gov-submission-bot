from __future__ import annotations

from dataclasses import asdict
from datetime import date
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple


def _chunk(text: str, limit: int = 3500) -> List[str]:
    # Slack safe chunking (keeps under hard limit)
    chunks = []
    cur = ""
    for line in text.splitlines(True):
        if len(cur) + len(line) > limit:
            chunks.append(cur)
            cur = ""
        cur += line
    if cur:
        chunks.append(cur)
    return chunks


def _fmt_job(job: Dict[str, Any]) -> str:
    emp = job.get("employer") or "Unknown employer"
    title = job.get("title") or "Unknown title"
    s = job.get("start") or "Unknown"
    e = job.get("end") or "Unknown"
    return f"{emp} | {title} | {s}–{e}"


def _safe(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def build_slack_rundown(
    opp: Any,
    candidate_name: str,
    match_summary: Dict[str, Any],
    per_req: List[Dict[str, Any]],
    bundle_dir: str,
) -> List[str]:
    """
    Returns list of Slack message chunks.
    per_req: list of dicts shaped like:
      {
        "req_id": "...",
        "req_text": "...",
        "is_required": True/False,
        "months": int|None,
        "status": "meets"|"partial"|"not_evidenced"|"unknown_dates",
        "jobs": [ {employer,title,start,end,months} ... ],
        "evidence": ["exact quote", ...],
        "notes": ["flag", ...]
      }
    """

    required = [r for r in per_req if r.get("is_required")]
    preferred = [r for r in per_req if not r.get("is_required")]

    def count_status(items, key):
        return sum(1 for r in items if r.get("status") == key)

    req_total = len(required)
    pref_total = len(preferred)

    req_meets = count_status(required, "meets")
    req_partial = count_status(required, "partial")
    req_none = count_status(required, "not_evidenced")
    req_unknown = count_status(required, "unknown_dates")

    pref_meets = count_status(preferred, "meets")
    pref_partial = count_status(preferred, "partial")

    score = match_summary.get("match_percent")
    gaps = match_summary.get("critical_gaps", [])

    title = getattr(opp, "title", None) or getattr(opp, "opportunity_id", "Opportunity")
    source = getattr(opp, "source_file", None)

    lines = []
    lines.append("📦 *Submission Rundown*")
    lines.append(f"Opp: `{_safe(title)}`")
    if source:
        lines.append(f"Source file: `{source}`")
    lines.append(f"Candidate: `{candidate_name}`")
    if score is not None:
        lines.append(f"Match score: `{score:.1f}%`")
    lines.append(f"Bundle: `{bundle_dir}`")
    lines.append("")
    lines.append("*Coverage*")
    lines.append(f"- Required: `{req_meets}/{req_total} meets`, `{req_partial} partial`, `{req_none} no-evidence`, `{req_unknown} unknown-months`")
    lines.append(f"- Preferred: `{pref_meets}/{pref_total} meets`, `{pref_partial} partial`")
    lines.append("")

    lines.append("*Required Qualifications (months + proof)*")
    if not required:
        lines.append("- None detected (parser issue)")
    else:
        for r in required[:20]:
            rt = _safe(r.get("req_text", ""))
            months = r.get("months")
            mtxt = f"{months} months" if isinstance(months, int) else "Unknown months"
            lines.append(f"{r.get('req_id','')}) {rt}")
            lines.append(f"Months: `{mtxt}` | Status: `{r.get('status')}`")
            jobs = r.get("jobs") or []
            if jobs:
                lines.append("Proof roles:")
                for j in jobs[:5]:
                    lines.append(f"- {_fmt_job(j)} ({j.get('months','?')} mo)")
            ev = r.get("evidence") or []
            if ev:
                lines.append("Evidence:")
                for q in ev[:3]:
                    lines.append(f'- "{_safe(q)}"')
            notes = r.get("notes") or []
            if notes:
                lines.append("Notes: " + ", ".join(_safe(n) for n in notes[:5]))
            lines.append("")

    lines.append("*Preferred Qualifications (months + proof)*")
    if not preferred:
        lines.append("- None detected")
    else:
        for r in preferred[:10]:
            rt = _safe(r.get("req_text", ""))
            months = r.get("months")
            mtxt = f"{months} months" if isinstance(months, int) else "Unknown months"
            lines.append(f"{r.get('req_id','')}) {rt}")
            lines.append(f"Months: `{mtxt}` | Status: `{r.get('status')}`")
            ev = r.get("evidence") or []
            if ev:
                lines.append("Evidence:")
                for q in ev[:2]:
                    lines.append(f'- "{_safe(q)}"')
            lines.append("")

    lines.append("*Critical gaps*")
    if gaps:
        for g in gaps[:20]:
            lines.append(f"- {_safe(str(g))}")
    else:
        # fallback based on statuses
        for r in required:
            if r.get("status") in {"not_evidenced", "unknown_dates"}:
                lines.append(f"- {_safe(r.get('req_text',''))} ({r.get('status')})")
    lines.append("")
    lines.append("*Next action*")
    lines.append("Reply `submit` if you want to proceed, or tell the candidate what to add to the resume for the missing requirements.")

    return _chunk("\n".join(lines))

