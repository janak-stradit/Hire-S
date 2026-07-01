from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "talent_taxonomy.json"


def normalize_label(value: str) -> str:
    return re.sub(r"[^a-z0-9+#]+", " ", value.casefold()).strip()


class TalentTaxonomy:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.version = payload["version"]
        self.stats = payload["stats"]
        self.skills = payload["skills"]
        self.roles = payload["roles"]
        self.skill_profiles = payload["skill_profiles"]
        self._skill_lookup: dict[str, str] = {}
        for record in self.skills.values():
            canonical = record["canonical"]
            for label in [canonical, *record.get("aliases", [])]:
                normalized = normalize_label(label)
                if normalized:
                    self._skill_lookup.setdefault(normalized, canonical)
        self._ordered_labels = sorted(self._skill_lookup, key=len, reverse=True)
        alternatives = "|".join(re.escape(label) for label in self._ordered_labels)
        self._skill_pattern = re.compile(rf"(?<![a-z0-9])(?:{alternatives})(?![a-z0-9])")
        self._role_lookup = {normalize_label(role): role for role in self.roles}

    def canonicalize_skill(self, value: str) -> str | None:
        return self._skill_lookup.get(normalize_label(value))

    def extract_skills(self, text: str) -> list[str]:
        normalized_text = normalize_label(text)
        found: set[str] = set()
        for match in self._skill_pattern.finditer(normalized_text):
            found.add(self._skill_lookup[match.group(0)])
        return sorted(found, key=str.casefold)

    def get_role(self, role: str) -> dict[str, Any] | None:
        canonical = self._role_lookup.get(normalize_label(role))
        return self.roles.get(canonical) if canonical else None

    def role_keywords(self, role: str) -> tuple[list[str], list[str]]:
        strategy = self.get_role(role)
        if not strategy:
            return [], []
        return (
            list(dict.fromkeys(strategy.get("primary_keywords", []))),
            list(dict.fromkeys(strategy.get("secondary_keywords", []))),
        )

    def role_skill_profile(self, role: str) -> dict[str, list[str]]:
        strategy = self.get_role(role)
        if not strategy:
            return {}
        return self.skill_profiles.get(strategy.get("skill_profile_id"), {})


@lru_cache(maxsize=1)
def get_taxonomy() -> TalentTaxonomy:
    if not DATA_PATH.exists():
        raise RuntimeError(
            "Compiled talent taxonomy is missing; run python scripts/build_talent_taxonomy.py"
        )
    return TalentTaxonomy(json.loads(DATA_PATH.read_text(encoding="utf-8")))
