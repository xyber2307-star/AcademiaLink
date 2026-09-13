# Institution / College Verification

Deterministic, backend-authoritative verification of a student's college/institution
against an official Government of India dataset. **No AI/LLM is used to decide whether
an institution is legitimate** - every decision is a plain lookup against a versioned
local dataset.

## 1. Authoritative data source

| | |
|---|---|
| **Source** | All India Council for Technical Education (AICTE) - Institute Permanent ID List |
| **Reference URL** | https://www.aicte.gov.in/downloads/Institute_List.pdf |
| **Dataset date** | 2013-09-18 (per the PDF's own document metadata - this is the only version of this list that AICTE currently publishes for direct download; see "Known limitations" below) |
| **Records** | 10,295 institutions after de-duplication by AICTE Permanent ID |
| **Fields provided by the source** | AICTE Permanent ID, Institute Name, State, District, City |
| **Local dataset file** | `backend/app/data/institutions_aicte.json` |
| **License** | Government of India open-data publication (AICTE), used as an official reference list |

### Why AICTE instead of AISHE

The task's preferred source was AISHE (All India Survey on Higher Education). AISHE's
institution-level master list is **not available as a clean, directly downloadable or
API-accessible dataset** without registering an account on data.gov.in (the AISHE catalog
there requires login for its "Data API" / "Zip Download" actions, and the resources listed
are per-topic annual survey extracts - e.g. "Examination Results of Colleges, 2015-16" -
not a single clean institution-master file with a stable code). Creating third-party
accounts on the user's behalf is out of scope for this change, so no AISHE data was used.
No value in this system was fabricated to work around that gap.

AICTE's Institute Permanent ID List **is** a real, official, directly-downloadable
Government of India dataset, and it is exactly on-topic for this feature: it enumerates
engineering, pharmacy, management, and polytechnic institutions - the AICTE-regulated
technical-education institutions students most often need to verify (the worked example
in the original spec, "VJIT", resolves correctly against this exact dataset - see
`backend/test_institution_verification_module.py::test_search_by_aicte_id`).

### Known limitations (disclosed, not hidden)

- **Vintage**: the AICTE PDF's own metadata dates it 2013-09-18. AICTE does not currently
  publish a newer machine-readable master list at a stable public URL. This means: an
  institution that opened, closed, or was renamed after 2013 will not match correctly.
  A `NOT_VERIFIED` result therefore means "not found in this specific, dated registry" -
  never "does not exist" or "is fake". The UI and API wording reflect this deliberately.
- **Scope**: AICTE only covers technical/professional institutions (engineering, pharmacy,
  management, architecture, polytechnics). A purely liberal-arts college or a university
  outside AICTE's regulatory scope will correctly show `NOT_VERIFIED` even if it is a real,
  legitimate institution - this is a genuine registry-coverage gap, not a bug.
- **No live API**: there is no official live search API for this data. The registry is a
  locally-cached, versioned snapshot (see "Refresh procedure" below), not a real-time feed.

### Refresh procedure

1. Download the current list from the reference URL above (or a newer official AICTE
   publication, if AICTE later republishes one at a different URL - update the URL here
   when that happens).
2. `pip install -r backend/scripts/requirements-import.txt`
3. `python backend/scripts/extract_aicte_pdf.py --pdf <downloaded.pdf> --out backend/app/data/institutions_aicte.json --dataset-date <YYYY-MM-DD>`
4. Restart the backend - `app/services/institution_data.py` loads the dataset once at
   process startup (see the `lifespan` hook in `app/main.py`).

This is a manual, controlled process by design (per the task's own instructions not to
invent an automatic live-refresh mechanism that doesn't actually exist).

## 2. Architecture

```
React (InstitutionSearchInput)
      |  GET /api/institutions/search?q=...
      v
FastAPI (app/routes/institutions.py)
      |
      v
app/services/institution_data.py   <-- in-memory index, loaded from the JSON dataset
      |
      v
backend/app/data/institutions_aicte.json   (versioned, source-labeled, see above)
```

```
React (EditProfileModal -> "Select" a search result)
      |  PUT /api/users/me  { institution_id: "aicte-1-5354121" }
      v
FastAPI (app/routes/users.py::update_my_profile)
      |  looks up institution_id in the SAME registry above
      |  - not found -> 400 (rejected, never silently accepted)
      |  - found     -> derives institution/institutionCode/State/District/
      |                 verificationStatus="VERIFIED"/verificationSource/lastVerifiedAt
      v
Firestore  users/{uid}   (merged, same document as every other profile field)
```

**Why the registry itself isn't a Firestore collection**: it is read-only reference data
(~10k rows), not user data. Storing it as ~10k Firestore documents would add write/read
cost and Firestore has no native full-text search, so every search would need either a
full collection scan or a second search service anyway. It is loaded once into memory at
process start instead - fast, deterministic, and the dataset's provenance/version is a
single JSON file that's trivial to diff and audit. The **per-student selection** (which
institution they picked) is exactly what lives in Firestore, in the existing `users/{uid}`
document - not a new/duplicate collection.

## 3. Institution schema (`backend/app/data/institutions_aicte.json`)

```json
{
  "source": "AICTE",
  "sourceName": "All India Council for Technical Education - Institute Permanent ID List",
  "sourceReference": "https://www.aicte.gov.in/downloads/Institute_List.pdf",
  "datasetDate": "2013-09-18",
  "importedAt": "<ISO timestamp of last extraction run>",
  "recordCount": 10295,
  "institutions": [
    {
      "aicteId": "1-5354121",
      "name": "VIDYA JYOTHI INSTITUTE OF TECHNOLOGY",
      "state": "Andhra Pradesh",
      "district": "RANGAREDDI",
      "city": "HYDERABAD",
      "normalizedName": "VIDYA JYOTHI INSTITUTE OF TECHNOLOGY",
      "derivedAcronym": "VJIT"
    }
  ]
}
```

`normalizedName` and `derivedAcronym` are deterministic transforms of `name` computed at
extraction time (uppercase, punctuation stripped, first letters of significant words) -
**not** a fabricated alias list. No field is invented that the source doesn't provide;
there is deliberately no `institutionType` or `universityAffiliation` field, because the
AICTE list doesn't provide those as structured values.

`institutionId` (used everywhere in the API) is derived as `f"aicte-{aicteId}"` and is
never independently persisted - it's a stable function of the source id.

## 4. Verification statuses

Only statuses the implementation actually supports exist:

| Status | Meaning | Shown as |
|---|---|---|
| `VERIFIED` | `institution_id` matched a record in the AICTE registry | "Institution registry verified · Source: AICTE" + AICTE ID, state, district |
| `NOT_VERIFIED` | Free-text institution with no registry selection, or a cleared selection | "Not Verified" (never "Fake") |
| `SOURCE_UNAVAILABLE` | The registry failed to load (returned by search only) | "Verification temporarily unavailable." |

`PENDING_VERIFICATION` was deliberately not implemented - lookups are synchronous and
instantaneous against the in-memory index, so there is no actual pending state to report.

**Program-level approval is a separate claim that this system does not make.** Every
verified-institution response includes `programLevelApprovalChecked: false` /
"Program-level approval not checked." - registry verification confirms the institution is
listed in AICTE's Institute Permanent ID List, not that a specific course/program at that
institution holds current approval.

## 5. Institution search

`GET /api/institutions/search?q=<query>` (auth required, rate-limited per-user via the
existing `check_user_rate_limit(uid, "institution_search")`, same tiered/configurable
system as every other endpoint - see `app/rate_limit.py`).

Deterministic matching (`app/services/institution_data.py`), in priority order:
1. Exact AICTE Permanent ID match.
2. Exact normalized-name match.
3. Exact match against the institution's own **deterministically-derived** acronym (e.g.
   "VJIT" matches "Vidya Jyothi Institute of Technology" because that acronym was computed
   from the real stored name at import time - not looked up in an invented alias table).
4. Normalized-name prefix match.
5. Token-containment match (every query word must appear somewhere in the name/state/
   district/city).

Results are capped at 20 and always presented as candidates for the student to pick from
explicitly - **the system never auto-selects a fuzzy match**, per the task's requirement.
A query with no matches returns `200` with `results: []`, never an error and never a "fake
college" label.

## 6. How AI is excluded from the decision

There is no AI/LLM call anywhere in `app/services/institution_data.py`,
`app/routes/institutions.py`, or the institution-handling branch of
`app/routes/users.py::update_my_profile`. Matching is plain Python string normalization
and comparison against the static dataset described above. The existing AI Career
Assistant feature elsewhere in the app is architecturally incapable of writing to
`institutionVerificationStatus` - that field is only ever set by the server-side lookup
in `update_my_profile`, and `UserProfileUpdate` (the request schema, `extra="forbid"`)
doesn't even accept it as an input field.

## 7. Firestore changes

`users/{uid}` gains these fields (all derived server-side only - see `app/models.py`'s
`UserProfileBase`/`UserProfileUpdate` comments):

```
institution_id                    - "aicte-<permanentId>" once a registry selection is made
institutionCode                   - the AICTE Permanent ID
institutionState / institutionDistrict
institutionVerificationStatus     - VERIFIED | NOT_VERIFIED | SOURCE_UNAVAILABLE | null
institutionVerificationSource     - "AICTE" | null
institutionLastVerifiedAt         - ISO timestamp | null
```

The pre-existing `institution` (free-text display name) and `institution_id` fields were
reused rather than duplicated - `institution_id` previously existed but had no real
semantics; it is now the canonical selection key. No new collection was created for
student data; no second Firestore project or database was introduced.

## 8. API endpoints

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /api/institutions/search?q=` | required | Search the registry; returns candidates |
| `GET /api/institutions/{institutionId}` | required | Fetch one registry record by id |
| `PUT /api/users/me` (existing endpoint, extended) | required | Select an institution via `institution_id`, or set free-text `institution` |

No duplicate profile-update endpoint was created - the existing `PUT /api/users/me` (used
by every role's profile edit already) now derives institution fields server-side when
`institution_id` is present, per the task's instruction to reuse existing endpoints.

## 9. Security model

- `UserProfileUpdate` never accepts `institutionVerificationStatus`, `institutionCode`,
  `institutionState`, `institutionDistrict`, or `institutionVerificationSource` as input
  fields at all - `extra="forbid"` rejects any request that includes them with `422`,
  regardless of value. A client cannot forge a verified status.
- `institution_id` sent by the client is **always** looked up against the server-side
  registry before anything is persisted. An id with no match is rejected with `400` - it
  is never stored, and the profile is left unchanged.
- If the registry failed to load, a selection attempt is rejected with `503` rather than
  silently marking anything verified or falling back to trusting client-sent data.
- `PUT /api/users/me` only ever writes to `users/{current_user.uid}` - there is no request
  shape that lets a user modify another user's institution fields (existing behavior,
  re-verified for this feature in `test_institution_verification_module.py`).

## 10. Tests

`backend/test_institution_verification_module.py` (12 tests, all passing):
registry loads; search requires auth; case-insensitive/partial search; exact AICTE-ID
search; nonexistent query returns empty (not an error); an intentionally generic query
returns multiple ambiguous candidates; selecting a valid institution persists canonical
fields and survives a reload (checked via both the API and a direct Firestore read);
an invalid `institution_id` is rejected with 400; free-text-only input is stored as
`NOT_VERIFIED`; a client cannot forge verification fields (422); single-institution
lookup for a real id and a 404 for an unknown one; a second user's profile write cannot
leak into the first user's document.

Also manually verified end-to-end in a live browser session against the running dev
servers: registered a real test account, searched "VJIT", selected the single matching
candidate ("Vidya Jyothi Institute of Technology"), saved, and confirmed the "Institution
Verified" badge with AICTE ID/state/district persisted after a full page reload - then
deleted the test account and its Firestore document.
