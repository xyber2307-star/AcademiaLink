"""
Institution registry data source and deterministic search/verification logic.

DESIGN
------
The authoritative institution master data is a versioned, locally-cached dataset
(app/data/institutions_aicte.json) extracted from an official Government of India
source - see scripts/extract_aicte_pdf.py and docs/INSTITUTION_VERIFICATION.md for
provenance, exact source URL, and the refresh procedure.

This module is intentionally the ONLY place that reads that dataset. It is loaded
once into memory at process start (see load()) rather than stored as ~10k Firestore
documents, because:
  - it is read-only reference data, not user data - Firestore gains nothing here and
    a full-collection scan per search would be slow and costly;
  - deterministic substring/token search over ~10k rows in memory is fast and simple;
  - Firestore stays reserved for what it already models: canonical *per-student*
    institution selections (see app/routes/users.py).

NO AI/LLM IS USED ANYWHERE IN THIS MODULE. All matching is deterministic string
normalization and comparison. If a future data source is added (e.g. an AISHE
export), it must be merged into the same dataset shape and re-loaded the same way -
never resolved via free-form model reasoning.
"""
import json
import logging
import os
import re
import threading
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("academialink.institution_data")

_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "institutions_aicte.json")

_STOPWORDS = {"OF", "AND", "&", "THE", "FOR"}


@dataclass(frozen=True)
class InstitutionRecord:
    institution_id: str
    aicte_id: str
    name: str
    normalized_name: str
    acronym: str
    state: Optional[str]
    district: Optional[str]
    city: Optional[str]
    source: str
    source_reference: str
    dataset_date: Optional[str]


class _Registry:
    def __init__(self):
        self._by_id: dict[str, InstitutionRecord] = {}
        self._loaded = False
        self._load_error: Optional[str] = None
        self._lock = threading.Lock()
        self.dataset_meta: dict = {}

    def load(self) -> None:
        with self._lock:
            if self._loaded or self._load_error:
                return
            try:
                with open(_DATA_PATH, encoding="utf-8") as f:
                    payload = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                self._load_error = str(e)
                logger.error("Failed to load institution dataset from %s: %s", _DATA_PATH, e)
                return

            source = payload.get("source", "UNKNOWN")
            source_reference = payload.get("sourceReference", "")
            dataset_date = payload.get("datasetDate")
            self.dataset_meta = {
                "source": source,
                "sourceName": payload.get("sourceName"),
                "sourceReference": source_reference,
                "datasetDate": dataset_date,
                "importedAt": payload.get("importedAt"),
                "recordCount": payload.get("recordCount"),
            }

            for row in payload.get("institutions", []):
                aicte_id = row.get("aicteId")
                if not aicte_id:
                    continue
                institution_id = f"aicte-{aicte_id}"
                record = InstitutionRecord(
                    institution_id=institution_id,
                    aicte_id=aicte_id,
                    name=row.get("name", ""),
                    normalized_name=row.get("normalizedName", ""),
                    acronym=row.get("derivedAcronym", ""),
                    state=row.get("state"),
                    district=row.get("district"),
                    city=row.get("city"),
                    source=source,
                    source_reference=source_reference,
                    dataset_date=dataset_date,
                )
                self._by_id[institution_id] = record

            self._loaded = True
            logger.info("Loaded %d institution records from %s", len(self._by_id), _DATA_PATH)

    @property
    def is_available(self) -> bool:
        return self._loaded and self._load_error is None

    @property
    def record_count(self) -> int:
        return len(self._by_id)

    def get(self, institution_id: str) -> Optional[InstitutionRecord]:
        return self._by_id.get(institution_id)

    def search(self, query: str, limit: int = 20) -> list[InstitutionRecord]:
        norm_query = normalize(query)
        if not norm_query:
            return []
        query_tokens = [t for t in norm_query.split(" ") if t]

        exact_matches: list[InstitutionRecord] = []
        acronym_matches: list[InstitutionRecord] = []
        starts_with_matches: list[InstitutionRecord] = []
        contains_matches: list[InstitutionRecord] = []

        compact_query = norm_query.replace(" ", "")

        for record in self._by_id.values():
            if record.aicte_id == query.strip():
                exact_matches.append(record)
                continue
            if record.normalized_name == norm_query:
                exact_matches.append(record)
                continue
            if compact_query and record.acronym == compact_query:
                acronym_matches.append(record)
                continue
            if record.normalized_name.startswith(norm_query):
                starts_with_matches.append(record)
                continue
            if all(_token_in_record(token, record) for token in query_tokens):
                contains_matches.append(record)

        ordered = exact_matches + acronym_matches + starts_with_matches + contains_matches
        return ordered[:limit]


def normalize(name: str) -> str:
    upper = (name or "").upper()
    upper = re.sub(r"[^\w\s]", " ", upper)
    upper = re.sub(r"\s+", " ", upper).strip()
    return upper


def _token_in_record(token: str, record: InstitutionRecord) -> bool:
    if token in _STOPWORDS:
        return True
    haystacks = [record.normalized_name, record.state or "", record.district or "", record.city or ""]
    return any(token in normalize(h) for h in haystacks)


_registry = _Registry()


def get_registry() -> _Registry:
    """Lazily loads the dataset on first use (safe to call repeatedly / from any request)."""
    if not _registry.is_available and _registry._load_error is None:
        _registry.load()
    return _registry
