from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Optional, Tuple

from ..models.opportunity import OpportunityData, Qualification


def _clean_line(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _is_bullet(raw: str) -> bool:
    raw = raw.lstrip()
    return bool(re.match(r"^(\-|\*|•|\d+[\).\]])\s+", raw))


def _strip_bullet(raw: str) -> str:
    raw = raw.lstrip()
    raw = re.sub(r"^(\-|\*|•|\d+[\).\]])\s+", "", raw)
    return _clean_line(raw)


class OpportunityParser:
    """
    Simple heuristic parser. It exists to keep the pipeline running.
    Compatible with run_pipeline calling:
      OpportunityParser(client, config, logger)
      parser.save_requirements_json(opp_data, Path(config.opps_dir))
    """

    def __init__(self, *args, **kwargs):
        # run_pipeline passes (client, config, logger). We do not require them here.
        pass

    def parse_opportunity(self, opportunity_path, text: str) -> OpportunityData:
        if isinstance(opportunity_path, str):
            opportunity_path = Path(opportunity_path)

        opportunity_id = opportunity_path.stem
        title = self._infer_title(text) or opportunity_path.stem

        required, preferred = self._extract_requirements(text)

        req_objs = [
            Qualification(
                id=str(i + 1),
                text=req,
                category="general",
                is_required=True,
            )
            for i, req in enumerate(required)
        ]

        pref_objs = [
            Qualification(
                id=f"P{i + 1}",
                text=req,
                category="general",
                is_required=False,
            )
            for i, req in enumerate(preferred)
        ]

        return OpportunityData(
            opportunity_id=opportunity_id,
            title=title,
            agency=None,
            due_date=None,
            required_qualifications=req_objs,
            preferred_qualifications=pref_objs,
            source_file=str(opportunity_path.name),
        )

    # Alias (in case run_pipeline calls parse instead of parse_opportunity)
    def parse(self, opportunity_path, text: str) -> OpportunityData:
        return self.parse_opportunity(opportunity_path, text)

    def save_requirements_json(self, opportunity: OpportunityData, opps_dir: Path) -> Path:
        """
        run_pipeline expects this method. It writes:
          <opps_dir>/<opportunity_id>/requirements.json
        """
        opps_dir = Path(opps_dir)
        out_dir = opps_dir / str(opportunity.opportunity_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "requirements.json"

        payload = {
            "opportunity_id": opportunity.opportunity_id,
            "title": opportunity.title,
            "agency": opportunity.agency,
            "due_date": opportunity.due_date,
            "source_file": opportunity.source_file,
            "required_qualifications": [
                {"id": q.id, "text": q.text, "category": q.category, "is_required": True}
                for q in opportunity.required_qualifications
            ],
            "preferred_qualifications": [
                {"id": q.id, "text": q.text, "category": q.category, "is_required": False}
                for q in opportunity.preferred_qualifications
            ],
        }

        out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return out_path

    def _infer_title(self, text: str) -> Optional[str]:
        for raw in text.splitlines():
            line = _clean_line(raw)
            if not line:
                continue
            if len(line) < 4:
                continue
            low = line.lower()
            if low in {"statement of work", "sow", "request for proposal", "rfp"}:
                continue
            return line[:140]
        return None

    def _extract_requirements(self, text: str) -> Tuple[List[str], List[str]]:
        required: List[str] = []
        preferred: List[str] = []

        mode: Optional[str] = None  # "required" | "preferred" | None

        for raw in text.splitlines():
            line = _clean_line(raw)
            if not line:
                continue

            low = line.lower()

            if "required" in low and "preferred" not in low and len(line) <= 80:
                mode = "required"
                continue
            if "preferred" in low and len(line) <= 80:
                mode = "preferred"
                continue

            if _is_bullet(raw):
                item = _strip_bullet(raw)
                if not item or len(item) < 3:
                    continue
                if mode == "preferred":
                    preferred.append(item)
                else:
                    required.append(item)

        if not required and not preferred:
            for raw in text.splitlines():
                line = _clean_line(raw)
                if not line or len(line) < 6:
                    continue
                low = line.lower()
                if low.startswith("required:"):
                    required.append(_clean_line(line.split(":", 1)[1]))
                elif low.startswith("preferred:"):
                    preferred.append(_clean_line(line.split(":", 1)[1]))

        def dedupe(items: List[str]) -> List[str]:
            seen = set()
            out: List[str] = []
            for x in items:
                k = x.lower()
                if k in seen:
                    continue
                seen.add(k)
                out.append(x)
            return out

        return dedupe(required)[:50], dedupe(preferred)[:50]
