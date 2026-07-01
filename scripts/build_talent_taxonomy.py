"""Compile Talent OS role and skill references into a HireX-owned runtime artifact."""

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Resumes"
OUTPUT = ROOT / "hirex" / "data" / "talent_taxonomy.json"


def load_json(name: str):
    return json.loads((SOURCE / name).read_text(encoding="utf-8-sig"))


def source_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    taxonomy = load_json("skill_taxonomy.json")
    roles = load_json("roles_strategy.json")
    profiles = load_json("skill_profiles.json")
    if "cloud_devops_core" not in profiles:
        profiles["cloud_devops_core"] = {
            **profiles["cloud_core"],
            **profiles["devops_core"],
        }
    skills = dict(taxonomy["skills"])

    seed_text = (SOURCE / "skills_seed.sql").read_text(encoding="utf-8-sig")
    seed_pairs = re.findall(r"\('((?:''|[^'])+)',\s*'((?:''|[^'])+)'\)", seed_text)
    canonical_index = {record["canonical"].casefold(): key for key, record in skills.items()}
    added_from_sql = 0
    for raw_name, raw_category in seed_pairs:
        name = raw_name.replace("''", "'").strip()
        category = raw_category.replace("''", "'").strip()
        if name.casefold() in canonical_index:
            continue
        key = re.sub(r"[^a-z0-9]+", "_", name.casefold()).strip("_")
        if not key or key in skills:
            continue
        skills[key] = {
            "canonical": name,
            "aliases": [],
            "category": category.casefold().replace("/", "_").replace(" ", "_"),
            "families": [],
            "related_skills": [],
            "importance": "medium",
            "source": "skills_seed.sql",
        }
        canonical_index[name.casefold()] = key
        added_from_sql += 1

    invalid_roles = [name for name, value in roles.items() if not isinstance(value, dict)]
    missing_profiles = sorted({
        value.get("skill_profile_id") for value in roles.values()
        if value.get("skill_profile_id") and value.get("skill_profile_id") not in profiles
    })
    if invalid_roles or missing_profiles:
        raise ValueError(
            f"Invalid role records={len(invalid_roles)}, missing skill profiles={missing_profiles}"
        )

    artifact = {
        "version": "1.0.0-hirex",
        "generated_at": datetime.now(UTC).isoformat(),
        "source_files": {
            name: source_digest(SOURCE / name)
            for name in ("skill_taxonomy.json", "skills_seed.sql", "roles_strategy.json", "skill_profiles.json")
        },
        "stats": {
            "skills": len(skills),
            "aliases": sum(len(value.get("aliases", [])) for value in skills.values()),
            "roles": len(roles),
            "skill_profiles": len(profiles),
            "sql_seed_skills_added": added_from_sql,
            "repaired_profiles": ["cloud_devops_core"],
        },
        "skills": skills,
        "roles": roles,
        "skill_profiles": profiles,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(artifact, ensure_ascii=True, separators=(",", ":")), encoding="utf-8")
    print(json.dumps(artifact["stats"], indent=2))
    print(f"Compiled taxonomy: {OUTPUT}")


if __name__ == "__main__":
    main()
