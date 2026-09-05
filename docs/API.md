# AcademiaLINK API Contract

> Status: **authoritative frontend/backend contract**
>
> This document defines the target `/api/...` contract requested for AcademiaLINK. These routes are documented here but are **not implemented by this documentation task**.
>
> **Database contract note:** `docs/DATABASE.md` does not currently exist in the repository, so this document does not introduce a persistence schema of its own. Where the current backend already has domain models, the documented fields follow those models. Future implementation work must reconcile any newly approved persistence fields with the database contract before changing this API.

## 1. Conventions

### Base URL

Development:

```text
http://localhost:8000
```

All application endpoints in this contract use the `/api` prefix.

### Authentication

Authenticated requests use:

```http
Authorization: Bearer <Firebase ID token>
```

Firebase token verification is handled by the backend authentication layer. In local development, the current backend also supports development authentication headers; those are not part of this frontend contract.

### Roles

The platform defines four roles:

| Role | Value |
|---|---|
| Student | `student` |
| Faculty | `faculty` |
| Recruiter | `recruiter` |
| Admin | `admin` |

The backend is authoritative for role checks and resource ownership.

### Common errors

| HTTP | Meaning |
|---|---|
| `400` | Invalid business request |
| `401` | Missing/invalid authentication |
| `403` | Authenticated but not allowed |
| `404` | Resource not found |
| `409` | Business conflict |
| `422` | Request validation failed |
| `500` | Internal server error |

Validation failures use the backend error structure:

```json
{
  "detail": "Request validation failed",
  "errors": []
}
```

Business errors use:

```json
{
  "detail": "Human-readable error"
}
```

---

# 2. System

## GET `/api/health`

**Purpose:** Liveness/health check for the frontend, development environment, and deployment probes.

**Authentication:** None.

**Allowed roles:** Public.

**Parameters:** None.

**Request body:** None.

**Success — `200 OK`:**

```json
{
  "status": "ok"
}
```

**Errors:** Normally none; infrastructure failures may produce `500`.

**Validation:** None.

---

# 3. Student

All `/api/student/*` endpoints require an authenticated **Student** and operate on the authenticated student's own record. The backend must not accept a client-supplied student ID to select another student's resource.

## GET `/api/student/profile`

**Purpose:** Return the authenticated student's profile.

**Authentication:** Required.

**Allowed roles:** `student`.

**Parameters:** None.

**Request body:** None.

**Success — `200 OK`:**

The response uses the current student-profile fields already present in the backend domain model:

```json
{
  "id": "student-123",
  "student_id": "student-123",
  "experience_months": 12,
  "education": "B.Tech Computer Science"
}
```

**Errors:** `401`, `403`, `404`, `500`.

**Validation:** The authenticated identity determines the student. No arbitrary student ID is accepted.

## PUT `/api/student/profile`

**Purpose:** Create or replace the authenticated student's career-profile fields used by downstream matching.

**Authentication:** Required.

**Allowed roles:** `student`.

**Parameters:** None.

**Request body:**

```json
{
  "experience_months": 12,
  "education": "B.Tech Computer Science"
}
```

`experience_months` is a non-negative integer. `education` may be `null`.

**Success — `200 OK`:**

```json
{
  "id": "student-123",
  "student_id": "student-123",
  "experience_months": 12,
  "education": "B.Tech Computer Science"
}
```

**Errors:** `401`, `403`, `422`, `500`.

**Validation:**
- `experience_months >= 0`.
- The backend supplies the authoritative `student_id`.
- The client cannot change ownership of the profile.

## GET `/api/student/skills`

**Purpose:** Return the authenticated student's authoritative assessed skill state.

**Authentication:** Required.

**Allowed roles:** `student`.

**Parameters:** None.

**Request body:** None.

**Success — `200 OK`:**

Each item follows the current `StudentSkill` domain representation:

```json
[
  {
    "id": "student-123:python",
    "student_id": "student-123",
    "skill_id": "python",
    "proficiency": 4,
    "score": 72.5,
    "verified_evidence_count": 2,
    "last_assessed_at": "2026-09-05T10:30:00Z"
  }
]
```

`proficiency` is the backend-owned level enum:

```text
1 NOVICE
2 DEVELOPING
3 COMPETENT
4 PROFICIENT
5 ADVANCED
```

**Errors:** `401`, `403`, `500`.

**Validation:** Skill score and proficiency are backend-calculated. React must not recalculate or overwrite them.

## GET `/api/student/gaps`

**Purpose:** Return skills where the student's current proficiency is below the applicable required level.

**Authentication:** Required.

**Allowed roles:** `student`.

**Parameters:** None.

**Request body:** None.

**Success — `200 OK`:**

```json
{
  "gaps": [
    {
      "skill_id": "python",
      "required_level": 4,
      "current_level": 2,
      "score": 35
    }
  ]
}
```

The current backend gap representation uses:
- `skill_id`
- `required_level`
- `current_level`
- `score`

**Errors:** `401`, `403`, `500`.

**Validation:** Gap membership and levels are calculated by the backend. The frontend does not calculate gaps.

## GET `/api/student/learning-path`

**Purpose:** Return the student's backend-generated learning path for addressing identified skill gaps.

**Authentication:** Required.

**Allowed roles:** `student`.

**Parameters:** None.

**Request body:** None.

**Success — `200 OK`:**

The response schema is **implementation-defined pending an approved learning-path persistence/domain model**. This contract intentionally does not invent database fields because `docs/DATABASE.md` is not currently present.

The response must represent the backend-generated path and its ordering; it must not be treated as a frontend-authored curriculum.

**Errors:** `401`, `403`, `404`, `500`.

**Validation:** The backend remains authoritative for the gaps used to generate the path.

---

# 4. Assessments

## GET `/api/assessments`

**Purpose:** List active assessments available to the authenticated user.

**Authentication:** Required.

**Allowed roles:** `student`, `faculty`, `admin` as permitted by implementation policy.

**Parameters:** None.

**Request body:** None.

**Success — `200 OK`:**

Each assessment follows the existing domain representation:

```json
[
  {
    "id": "assessment-python-1",
    "title": "Python Fundamentals",
    "description": "Core Python assessment",
    "questions": [
      {
        "id": "q1",
        "skill_id": "python",
        "prompt": "What is ...?",
        "options": {
          "A": "Option A",
          "B": "Option B"
        },
        "correct_option": "A",
        "points": 1
      }
    ],
    "active": true
  }
]
```

**Errors:** `401`, `403`, `500`.

**Validation:** Inactive assessments are not offered as active assessment work.

## GET `/api/assessments/{id}`

**Purpose:** Return one assessment for presentation before submission.

**Authentication:** Required.

**Allowed roles:** `student`, `faculty`, `admin` as permitted by implementation policy.

**Path parameters:**
- `id` — assessment identifier.

**Request body:** None.

**Success — `200 OK`:** Same assessment object shape as above.

**Errors:** `401`, `403`, `404`, `500`.

**Validation:** The assessment must exist. Inactive assessments must not be submitted.

## POST `/api/assessments/{id}/submit`

**Purpose:** Submit answers and let the backend calculate the authoritative assessment score and per-skill scores.

**Authentication:** Required.

**Allowed roles:** `student`.

**Path parameters:**
- `id` — assessment identifier.

**Request body:**

```json
{
  "answers": [
    {
      "question_id": "q1",
      "option": "A"
    },
    {
      "question_id": "q2",
      "option": "C"
    }
  ]
}
```

**Success — `200 OK`:**

The current backend returns an `AssessmentResult`:

```json
{
  "id": "result-uuid",
  "student_id": "student-123",
  "assessment_id": "assessment-python-1",
  "score": 75,
  "skill_scores": {
    "python": 80,
    "data-structures": 60
  },
  "submitted_at": "2026-09-05T10:30:00Z"
}
```

**Errors:** `401`, `403`, `404`, `422`, `500`.

**Validation:**
- Assessment must exist and be active.
- Question IDs must belong to the assessment.
- Duplicate question answers are rejected.
- The backend calculates total and skill-level scores.
- The backend updates authoritative student-skill proficiency.

---

# 5. Evidence

## POST `/api/evidence`

**Purpose:** Submit student evidence for a skill.

**Authentication:** Required.

**Allowed roles:** `student`.

**Request body:**

```json
{
  "skill_id": "python",
  "title": "Backend API Project",
  "description": "FastAPI project demonstrating API design",
  "storage_path": "evidence/student-123/project.pdf",
  "url": null
}
```

Current evidence fields are:
- `student_id` — supplied by authentication/backend
- `skill_id`
- `title`
- `description`
- `storage_path` optional
- `url` optional
- `status`
- review metadata
- submission timestamp

**Success — `200 OK`:**

```json
{
  "id": "evidence-uuid",
  "student_id": "student-123",
  "skill_id": "python",
  "title": "Backend API Project",
  "description": "FastAPI project demonstrating API design",
  "storage_path": "evidence/student-123/project.pdf",
  "url": null,
  "status": "pending",
  "reviewed_by": null,
  "review_comment": null,
  "submitted_at": "2026-09-05T10:30:00Z",
  "reviewed_at": null
}
```

**Errors:** `401`, `403`, `422`, `500`.

**Validation:** Evidence ownership comes from authentication; clients cannot submit evidence on behalf of another student.

## GET `/api/evidence`

**Purpose:** List evidence owned by the authenticated student.

**Authentication:** Required.

**Allowed roles:** `student`.

**Parameters:** None.

**Request body:** None.

**Success — `200 OK`:** Array of evidence objects using the schema above.

**Errors:** `401`, `403`, `500`.

**Validation:** Only the authenticated student's evidence is returned.

## GET `/api/faculty/evidence`

**Purpose:** List evidence available for authorized faculty review.

**Authentication:** Required.

**Allowed roles:** `faculty`, `admin`.

**Parameters:** Implementation may later add institution/status filters; they are not part of this contract yet.

**Request body:** None.

**Success — `200 OK`:** Array of evidence records.

**Errors:** `401`, `403`, `500`.

**Validation:** Faculty access must be restricted to students/evidence the faculty member is authorized to manage. Admins may operate institution-wide according to authorization policy.

## POST `/api/faculty/evidence/{id}/review`

**Purpose:** Approve or reject submitted student evidence.

**Authentication:** Required.

**Allowed roles:** `faculty`, `admin`.

**Path parameters:**
- `id` — evidence identifier.

**Request body:**

```json
{
  "status": "approved",
  "review_comment": "Evidence verified against project submission."
}
```

Allowed evidence states:

```text
pending
approved
rejected
```

**Success — `200 OK`:**

```json
{
  "id": "evidence-uuid",
  "student_id": "student-123",
  "skill_id": "python",
  "title": "Backend API Project",
  "description": "FastAPI project demonstrating API design",
  "storage_path": "evidence/student-123/project.pdf",
  "url": null,
  "status": "approved",
  "reviewed_by": "faculty-456",
  "review_comment": "Evidence verified against project submission.",
  "submitted_at": "2026-09-05T10:30:00Z",
  "reviewed_at": "2026-09-05T11:00:00Z"
}
```

**Errors:** `401`, `403`, `404`, `409`, `422`, `500`.

**Validation:**
- Evidence must exist.
- Reviewer must be authorized for the student/evidence.
- Approved evidence contributes to the student's verified-evidence state.
- Duplicate approval is a conflict.

---

# 6. Opportunities and Applications

## GET `/api/opportunities`

**Purpose:** List currently discoverable opportunities.

**Authentication:** Required.

**Allowed roles:** `student`, `recruiter`, `admin`.

**Parameters:** None initially.

**Request body:** None.

**Success — `200 OK`:**

Each opportunity follows the existing domain representation:

```json
[
  {
    "id": "opp-123",
    "recruiter_id": "recruiter-456",
    "company_name": "ACME",
    "title": "Backend Intern",
    "description": "Build APIs",
    "status": "open",
    "required_skills": [
      {
        "skill_id": "python",
        "minimum_level": 3,
        "weight": 1
      }
    ],
    "min_experience_months": 0,
    "education_keywords": [
      "computer science"
    ],
    "created_at": "2026-09-05T10:00:00Z"
  }
]
```

**Errors:** `401`, `403`, `500`.

**Validation:** Closed opportunities are not included in the normal discoverable list.

## POST `/api/opportunities`

**Purpose:** Create an opportunity and define its required competencies.

**Authentication:** Required.

**Allowed roles:** `recruiter`.

**Request body:**

```json
{
  "company_name": "ACME",
  "title": "Backend Intern",
  "description": "Build APIs",
  "required_skills": [
    {
      "skill_id": "python",
      "minimum_level": 3,
      "weight": 1
    }
  ],
  "min_experience_months": 0,
  "education_keywords": [
    "computer science"
  ],
  "status": "draft"
}
```

**Success — `200 OK`:** Newly created opportunity object.

**Errors:** `401`, `403`, `409`, `422`, `500`.

**Validation:**
- `min_experience_months >= 0`.
- Required-skill weight must be positive.
- Minimum proficiency must be a defined `SkillLevel`.
- `status` must be one of `draft`, `open`, `closed`.
- `recruiter_id` comes from authentication.

## GET `/api/opportunities/{id}`

**Purpose:** Return one opportunity.

**Authentication:** Required.

**Allowed roles:** `student`, `recruiter`, `admin`.

**Path parameters:**
- `id` — opportunity identifier.

**Request body:** None.

**Success — `200 OK`:** Opportunity object.

**Errors:** `401`, `403`, `404`, `500`.

**Validation:** Recruiters may access their own opportunity records; admins have administrative access; students may access discoverable opportunities.

## POST `/api/opportunities/{id}/apply`

**Purpose:** Submit an application for the authenticated student.

**Authentication:** Required.

**Allowed roles:** `student`.

**Path parameters:**
- `id` — opportunity identifier.

**Request body:** None.

**Success — `200 OK`:**

Application shape follows the existing domain model:

```json
{
  "id": "application-uuid",
  "opportunity_id": "opp-123",
  "student_id": "student-123",
  "status": "submitted",
  "applied_at": "2026-09-05T11:10:00Z"
}
```

**Errors:** `401`, `403`, `404`, `409`, `500`.

**Validation:**
- Opportunity must exist.
- Opportunity must be `open`.
- Student cannot submit a duplicate active application.
- Student identity comes from authentication.

---

# 7. Recruiter

## GET `/api/recruiter/candidates`

**Purpose:** Return candidates available to the authenticated recruiter for recruitment workflows.

**Authentication:** Required.

**Allowed roles:** `recruiter`, `admin`.

**Parameters:** No mandatory query parameters in the initial contract.

**Request body:** None.

**Success — `200 OK`:**

The exact candidate-list response shape is **implementation-defined pending the approved candidate-view schema**. It must be based on persisted student/profile/skill data and backend-generated matching—not frontend-calculated values.

**Errors:** `401`, `403`, `500`.

**Validation:** Recruiters may only access candidates through opportunities they are authorized to manage.

## GET `/api/recruiter/candidates/{id}`

**Purpose:** Return detailed recruitment information for one candidate.

**Authentication:** Required.

**Allowed roles:** `recruiter`, `admin`.

**Path parameters:**
- `id` — student/candidate identifier.

**Request body:** None.

**Success — `200 OK`:** Candidate details, including only backend-authorized information and authoritative skill/matching data.

The exact aggregate response shape is implementation-defined pending the approved candidate-view schema.

**Errors:** `401`, `403`, `404`, `500`.

**Validation:** Recruiter authorization must be enforced server-side.

---

# 8. Admin

## GET `/api/admin/analytics`

**Purpose:** Return institution-level competency, assessment, evidence, and skill-gap analytics.

**Authentication:** Required.

**Allowed roles:** `admin`.

**Parameters:** The initial contract has no mandatory query parameters.

**Request body:** None.

**Success — `200 OK`:**

The current backend analytics service already represents these values:

```json
{
  "institution_id": "institution-123",
  "student_count": 120,
  "assessed_student_count": 98,
  "verified_evidence_count": 240,
  "average_assessment_score": 67.4,
  "skill_gaps": [
    {
      "skill_id": "python",
      "student_count": 42,
      "average_score": 51.2,
      "average_proficiency": 2.7
    }
  ]
}
```

**Errors:** `401`, `403`, `500`.

**Validation:** Analytics must be computed by the backend from authoritative persisted data.

---

# 9. AI Career & Skill Copilot

## POST `/api/ai/chat`

**Purpose:** Provide a conversational career/skill assistant grounded in the student's backend skill profile.

**Authentication:** Required.

**Allowed roles:** `student`.

**Request body:**

```json
{
  "message": "What should I improve for backend internships?"
}
```

**Success — `200 OK`:**

The initial AI service contract supports an answer plus backend-derived context. The response envelope is:

```json
{
  "answer": "Your current backend profile shows 4 assessed skills. Prioritize the lowest-proficiency skills and strengthen them with verified evidence.",
  "context": {
    "skills": [
      {
        "skill_id": "python",
        "score": 72,
        "proficiency": 4
      }
    ]
  }
}
```

**Errors:** `401`, `403`, `422`, `500`, and provider/configuration errors when an external AI provider is enabled.

**Validation:**
- `message` must be non-empty.
- Student identity is derived from authentication.
- The AI receives backend-controlled profile context.
- The AI must not become authoritative for proficiency, gap, verification, or matching calculations.

---

# 10. Backend Authority Rules

The following are non-negotiable API rules:

1. React must not calculate or persist authoritative assessment scores.
2. React must not calculate or persist authoritative proficiency levels.
3. React must not calculate authoritative skill gaps.
4. React must not approve or reject evidence.
5. React must not calculate authoritative candidate match scores.
6. React must not determine authorization or role permissions.
7. Every protected resource is authorized by the FastAPI backend.
8. Student ownership is derived from authentication, not a client-supplied student identifier.
9. Recruiter ownership is derived from authentication and opportunity ownership.
10. Faculty access must respect the backend's institution/student authorization boundary.
11. AI output is advisory; backend domain calculations remain authoritative.
12. Database/persistence changes must remain aligned with the separately approved database contract.

# 11. Route Summary

| Method | Route | Primary role |
|---|---|---|
| GET | `/api/health` | Public |
| GET | `/api/student/profile` | Student |
| PUT | `/api/student/profile` | Student |
| GET | `/api/student/skills` | Student |
| GET | `/api/student/gaps` | Student |
| GET | `/api/student/learning-path` | Student |
| GET | `/api/assessments` | Authenticated |
| GET | `/api/assessments/{id}` | Authenticated |
| POST | `/api/assessments/{id}/submit` | Student |
| POST | `/api/evidence` | Student |
| GET | `/api/evidence` | Student |
| GET | `/api/faculty/evidence` | Faculty/Admin |
| POST | `/api/faculty/evidence/{id}/review` | Faculty/Admin |
| GET | `/api/opportunities` | Authenticated |
| POST | `/api/opportunities` | Recruiter |
| GET | `/api/opportunities/{id}` | Authenticated |
| POST | `/api/opportunities/{id}/apply` | Student |
| GET | `/api/recruiter/candidates` | Recruiter/Admin |
| GET | `/api/recruiter/candidates/{id}` | Recruiter/Admin |
| GET | `/api/admin/analytics` | Admin |
| POST | `/api/ai/chat` | Student |

# 12. Implementation Status

This document is a contract only. **No endpoint implementation is requested as part of this documentation step.**

The current backend implementation still contains its earlier `/api/v1/*` route surface; the `/api/...` routes above are the target contract for the subsequent implementation work.
