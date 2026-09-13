"""
One-off pass to bring every remaining legacy skill doc (pre-dating this taxonomy work) up to
the full schema: subcategory, type, aliases, relatedSkills, parentSkill, assessmentAvailable,
active, source, version, popularity, createdAt/updatedAt. Idempotent - only fills MISSING
fields, never overwrites a value an admin or the original seed already set.
"""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.firebase import initialize_firebase, get_db
from app.data.skills_taxonomy_seed import build_taxonomy_entries
from seed_skills_taxonomy import slugify, ASSESSMENT_AVAILABLE_SLUGS

# Best-effort category remap for old narrow category labels -> new discipline categories,
# used only for legacy docs whose name doesn't match a taxonomy entry.
OLD_CATEGORY_REMAP = {
    "Programming": "Computer Science & Software",
    "Web": "Computer Science & Software",
    "Data": "AI & Data",
    "Tools": "Computer Science & Software",
    "Soft Skills": "Soft Skills",
    "soft": "Soft Skills",
    "technical": "Computer Science & Software",
    "domain": "Healthcare & Life Sciences",  # all unmatched 'domain' legacy docs happen to be health/life-science
    "research": "Education & Research",
}

OLD_TYPE_REMAP = {
    "Programming": "technical", "Web": "technical", "Data": "technical", "Tools": "tool",
    "Soft Skills": "soft", "soft": "soft", "technical": "technical", "domain": "domain",
    "research": "domain",
}


def main():
    initialize_firebase()
    db = get_db()

    taxonomy_by_name = {}
    for name, category, subcategory, type_, aliases in build_taxonomy_entries():
        taxonomy_by_name[name.strip().lower()] = (name, category, subcategory, type_, aliases, slugify(name))

    now_iso = datetime.now(timezone.utc).isoformat()
    enriched = 0

    for doc in db.collection("skills").stream():
        data = doc.to_dict() or {}
        needs_fields = [f for f in ("subcategory", "type", "aliases", "relatedSkills", "parentSkill",
                                     "assessmentAvailable", "active", "source", "version", "popularity",
                                     "createdAt", "updatedAt") if f not in data]
        old_category = data.get("category")
        category_needs_fix = old_category in OLD_CATEGORY_REMAP

        if not needs_fields and not category_needs_fix:
            continue

        name_lower = str(data.get("name", "")).strip().lower()
        match = taxonomy_by_name.get(name_lower)

        update = {}
        if match:
            _, category, subcategory, type_, aliases, slug = match
            update["subcategory"] = data.get("subcategory") or subcategory
            update["type"] = data.get("type") or type_
            update["aliases"] = data.get("aliases") or aliases
            update["assessmentAvailable"] = data.get("assessmentAvailable", slug in ASSESSMENT_AVAILABLE_SLUGS)
            if category_needs_fix:
                update["legacyCategory"] = old_category
                update["category"] = category
        else:
            update["subcategory"] = data.get("subcategory")
            update["type"] = data.get("type") or OLD_TYPE_REMAP.get(old_category, "domain")
            update["aliases"] = data.get("aliases") or []
            update["assessmentAvailable"] = data.get("assessmentAvailable", False)
            if category_needs_fix:
                update["legacyCategory"] = old_category
                update["category"] = OLD_CATEGORY_REMAP.get(old_category, "Uncategorized")

        update["relatedSkills"] = data.get("relatedSkills") or []
        update["parentSkill"] = data.get("parentSkill")
        update["active"] = data.get("active", True)
        update["source"] = data.get("source") or "legacy_enriched"
        update["version"] = data.get("version", 1)
        update["popularity"] = data.get("popularity", 0)
        update["createdAt"] = data.get("createdAt") or now_iso
        update["updatedAt"] = now_iso

        db.collection("skills").document(doc.id).set(update, merge=True)
        enriched += 1
        print(f"Enriched '{data.get('name')}' (id={doc.id})")

    print(f"\nTotal docs enriched: {enriched}")


if __name__ == "__main__":
    main()
