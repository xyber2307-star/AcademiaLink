"""
One-off cleanup: resolves name-level duplicate skill docs created because the initial seed run
only deduped against itself, not against the small pre-existing 'skills' collection (29 legacy
docs from before this taxonomy work, e.g. python/react/git/sql/java/dsa/ml-basics/communication
plus several random-ID docs like Leadership, Teamwork, Machine Learning, Data Analysis, etc.).

For each duplicate pair (same name, different doc id), keeps the ORIGINAL legacy doc (predates
this work) and enriches it with the new taxonomy schema fields (category/subcategory/type/
aliases/assessmentAvailable/active/source/version/popularity) computed from our taxonomy seed
entry, then deletes the newly-created slug-doc duplicate. Idempotent and safe to re-run.
"""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.firebase import initialize_firebase, get_db
from app.data.skills_taxonomy_seed import build_taxonomy_entries
from seed_skills_taxonomy import slugify, ASSESSMENT_AVAILABLE_SLUGS


def main():
    initialize_firebase()
    db = get_db()

    entries_by_slug = {}
    for name, category, subcategory, type_, aliases in build_taxonomy_entries():
        entries_by_slug[slugify(name)] = (name, category, subcategory, type_, aliases)

    docs = list(db.collection("skills").stream())
    from collections import defaultdict
    by_name = defaultdict(list)
    for d in docs:
        data = d.to_dict() or {}
        name_lower = (data.get("name") or "").strip().lower()
        by_name[name_lower].append((d.id, data))

    now_iso = datetime.now(timezone.utc).isoformat()
    resolved = 0

    for name_lower, group in by_name.items():
        if len(group) < 2:
            continue

        # Identify the legacy doc (createdAt missing/older, i.e. not from our seed_v1 run)
        legacy = [g for g in group if g[1].get("source") != "seed_v1"]
        seeded = [g for g in group if g[1].get("source") == "seed_v1"]

        if not legacy or not seeded:
            print(f"SKIP '{name_lower}': could not classify legacy vs seeded (group={[g[0] for g in group]})")
            continue

        legacy_id, legacy_data = legacy[0]
        seeded_id, seeded_data = seeded[0]

        taxonomy_entry = entries_by_slug.get(seeded_id)
        if not taxonomy_entry:
            print(f"SKIP '{name_lower}': no taxonomy entry found for seeded slug '{seeded_id}'")
            continue

        _, category, subcategory, type_, aliases = taxonomy_entry

        enrichment = {}
        if not legacy_data.get("subcategory"):
            enrichment["subcategory"] = subcategory
        if not legacy_data.get("type"):
            enrichment["type"] = type_
        if not legacy_data.get("aliases"):
            enrichment["aliases"] = aliases
        if "relatedSkills" not in legacy_data:
            enrichment["relatedSkills"] = []
        if "parentSkill" not in legacy_data:
            enrichment["parentSkill"] = None
        if "assessmentAvailable" not in legacy_data:
            enrichment["assessmentAvailable"] = seeded_id in ASSESSMENT_AVAILABLE_SLUGS
        if "active" not in legacy_data:
            enrichment["active"] = True
        if not legacy_data.get("source"):
            enrichment["source"] = "legacy_enriched"
        if "version" not in legacy_data:
            enrichment["version"] = 1
        if "popularity" not in legacy_data:
            enrichment["popularity"] = 0
        if not legacy_data.get("createdAt"):
            enrichment["createdAt"] = now_iso
        enrichment["updatedAt"] = now_iso
        # Preserve the legacy category value as 'legacyCategory' if it doesn't match our
        # discipline-category scheme, but only set our canonical 'category' if missing.
        if not legacy_data.get("category") or legacy_data.get("category") in ("technical", "tool", "soft", "domain", "research", "Programming", "Web", "Data", "Tools", "Soft Skills"):
            enrichment["legacyCategory"] = legacy_data.get("category")
            enrichment["category"] = category

        db.collection("skills").document(legacy_id).set(enrichment, merge=True)
        db.collection("skills").document(seeded_id).delete()
        resolved += 1
        print(f"Resolved '{name_lower}': kept legacy doc '{legacy_id}' (enriched), deleted duplicate '{seeded_id}'")

    print(f"\nTotal duplicate groups resolved: {resolved}")
    total_after = len(list(db.collection("skills").stream()))
    print(f"Total skills in Firestore 'skills' collection now: {total_after}")


if __name__ == "__main__":
    main()
