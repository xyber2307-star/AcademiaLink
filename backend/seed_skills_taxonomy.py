"""
Idempotent seed script for the canonical Skill Taxonomy (Firestore collection 'skills').

Safe to re-run: upserts by slug, never duplicates, never overwrites admin edits to skills that
already exist unless --force is passed. Run with:

    ./venv/Scripts/python.exe seed_skills_taxonomy.py
"""
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.firebase import initialize_firebase, get_db
from app.data.skills_taxonomy_seed import build_taxonomy_entries

# Skills with a real, hand-written, fact-checked question bank in app/routes/skills.py.
# Every other skill is assessable only via self-declaration/evidence until a real bank
# is written for it - we do not fabricate assessments for skills we can't verify.
ASSESSMENT_AVAILABLE_SLUGS = {
    "python", "react", "sql", "javascript", "git", "cybersecurity",
    "machine_learning", "software_engineering",
}


def slugify(name: str) -> str:
    slug = name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")


def main(force: bool = False):
    initialize_firebase()
    db = get_db()
    entries = build_taxonomy_entries()

    # Load every existing skill's name + aliases (regardless of doc id) so we never create a
    # name-level duplicate under a different id - not just a slug-level one.
    existing_names_lower = set()
    for doc in db.collection("skills").stream():
        data = doc.to_dict() or {}
        n = str(data.get("name") or "").strip().lower()
        if n:
            existing_names_lower.add(n)
        for alias in data.get("aliases") or []:
            existing_names_lower.add(str(alias).strip().lower())

    seen_slugs = set()
    seen_names_lower = set()
    duplicates = []
    created = 0
    skipped_existing = 0
    now_iso = datetime.now(timezone.utc).isoformat()

    batch = db.batch()
    batch_count = 0

    for name, category, subcategory, type_, aliases in entries:
        slug = slugify(name)
        name_lower = name.strip().lower()

        if slug in seen_slugs or name_lower in seen_names_lower or name_lower in existing_names_lower:
            duplicates.append(name)
            continue
        seen_slugs.add(slug)
        seen_names_lower.add(name_lower)
        for alias in aliases:
            seen_names_lower.add(alias.strip().lower())

        doc_ref = db.collection("skills").document(slug)

        if not force:
            existing = doc_ref.get()
            if existing.exists:
                skipped_existing += 1
                continue

        payload = {
            "name": name,
            "category": category,
            "subcategory": subcategory,
            "type": type_,
            "description": "",
            "aliases": aliases,
            "relatedSkills": [],
            "parentSkill": None,
            "assessmentAvailable": slug in ASSESSMENT_AVAILABLE_SLUGS,
            "active": True,
            "source": "seed_v1",
            "version": 1,
            "popularity": 0,
            "createdAt": now_iso,
            "updatedAt": now_iso,
        }
        batch.set(doc_ref, payload)
        batch_count += 1
        created += 1

        if batch_count >= 400:
            batch.commit()
            batch = db.batch()
            batch_count = 0

    if batch_count > 0:
        batch.commit()

    total_docs = len(list(db.collection("skills").stream()))

    print(f"Taxonomy entries defined: {len(entries)}")
    print(f"Newly created:            {created}")
    print(f"Skipped (already exist):  {skipped_existing}")
    print(f"Duplicate names skipped:  {len(duplicates)} -> {duplicates}")
    print(f"Total skills in Firestore 'skills' collection now: {total_docs}")


if __name__ == "__main__":
    force = "--force" in sys.argv
    main(force=force)
