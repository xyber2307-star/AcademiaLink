# AcademiaLINK Firestore Database Contract

> **Authoritative database source of truth** for backend, frontend, Firebase, AI, and analytics developers.
>
> **Only these 14 top-level collections are approved:** `users`, `students`, `companies`, `institutions`, `skills`, `assessments`, `questions`, `assessment_results`, `evidence`, `opportunities`, `applications`, `learning_paths`, `quiz_attempts`, `chat_sessions`.
>
> No additional top-level collection may be introduced without explicit approval and an update to this document.

## Firestore conventions

Document IDs use the corresponding identifier field: `userId`, `studentId`, `companyId`, `institutionId`, `skillId`, `assessmentId`, `questionId`, `resultId`, `evidenceId`, `opportunityId`, `applicationId`, `learningPathId`, `attemptId`, and `sessionId`.

Types in this contract are Firestore `string`, `integer`, `number`, `boolean`, `timestamp`, arrays, and maps/objects.

Cross-collection relationships are logical ID references; do not create subcollections for them.

The backend is the authority for calculated scores, proficiency, skill gaps, verification state, match scores, permissions, and application rules. Clients must not directly write those authoritative values.

---

# 1. `users`

**Purpose:** Canonical application identity and role record.

| Field | Type | Required | Description |
|---|---|---|---|
| `userId` | string | Yes | Stable unique user identifier; document ID. |
| `name` | string | Yes | User display/full name. |
| `email` | string | Yes | User email. |
| `role` | string | Yes | `student`, `faculty`, `recruiter`, or `admin`. |
| `createdAt` | timestamp | Yes | Server-generated creation time. |

**Relationships:** `students.userId` and `companies.userId` reference `users.userId`.

**Read:** User may read own record; admins may read authorized user records; other roles only receive explicitly exposed fields through backend APIs.

**Write:** Backend only; role changes are admin/backend controlled.

**Validation:** Unique `userId`; normalized valid email; valid role; `createdAt` server-generated; client cannot self-elevate role.

---

# 2. `students`

**Purpose:** Student academic profile and skill associations.

| Field | Type | Required | Description |
|---|---|---|---|
| `studentId` | string | Yes | Unique student identifier; document ID. |
| `userId` | string | Yes | Reference to `users.userId`. |
| `college` | string | Yes | College/institution name. |
| `branch` | string | Yes | Academic branch/program. |
| `semester` | integer | Yes | Current academic semester. |
| `skills` | array<string> | Yes | Skill IDs from `skills.skillId`; this is an association list, not authoritative proficiency. |
| `createdAt` | timestamp | Yes | Server-generated creation time. |
| `updatedAt` | timestamp | Yes | Server-managed last-update time. |

**Relationships:** `userId` → `users.userId`; every `skills[]` → `skills.skillId`.

**Read:** Student own record; authorized faculty for managed students; admins; recruiters only through approved candidate APIs.

**Write:** Backend only; student self-service changes go through authorized APIs.

**Validation:** Valid `studentId`/`userId`; positive institution-valid semester; no duplicate skill IDs; timestamps server-managed. Proficiency must not be inferred solely from `students.skills`.

---

# 3. `companies`

**Purpose:** Company/recruiter organization profile.

| Field | Type | Required | Description |
|---|---|---|---|
| `companyId` | string | Yes | Unique company identifier; document ID. |
| `userId` | string | Yes | Owning recruiter/company user; reference to `users.userId`. |
| `name` | string | Yes | Company name. |
| `profile` | map/object | Yes | Company profile information exposed by backend. |

**Relationships:** `userId` → `users.userId`; `opportunities.companyId` → `companies.companyId`.

**Read:** Authenticated users where company discovery is permitted; owner; admins; students through opportunity discovery.

**Write:** Company/recruiter owner through backend; admin for corrections.

**Validation:** Unique IDs; valid owner; non-empty name; profile is a map; never store credentials or secrets.

---

# 4. `institutions`

**Purpose:** Institution organization metadata for authorization and analytics.

| Field | Type | Required | Description |
|---|---|---|---|
| `institutionId` | string | Yes | Unique institution identifier; document ID. |
| `name` | string | Yes | Institution name. |
| `departments` | array<string> | Yes | Department names/identifiers. |

**Relationships:** Institution context is used by backend authorization and analytics. No institution-membership collection is approved.

**Read:** Students/faculty for their institution; admins; other users only through approved exposure.

**Write:** Admin/backend only.

**Validation:** Unique ID; non-empty name; department strings unique within the document; no credentials/secrets.

---

# 5. `skills`

**Purpose:** Canonical skill taxonomy.

| Field | Type | Required | Description |
|---|---|---|---|
| `skillId` | string | Yes | Unique skill identifier; document ID. |
| `name` | string | Yes | Canonical skill name. |
| `category` | string | Yes | Skill category. |
| `description` | string | Yes | Skill description. |

**Relationships:** Referenced by student skill associations, assessments, questions, evidence skill context, opportunities, and learning paths.

**Read:** Authenticated users according to API policy.

**Write:** Admin/backend only.

**Validation:** Unique `skillId` and normalized name; non-empty name/category/description; referenced IDs must remain stable.

---

# 6. `assessments`

**Purpose:** Assessment definitions and ordered question references.

| Field | Type | Required | Description |
|---|---|---|---|
| `assessmentId` | string | Yes | Unique assessment identifier; document ID. |
| `skillId` | string | Yes | Primary skill assessed; reference to `skills.skillId`. |
| `title` | string | Yes | Assessment title. |
| `description` | string | Yes | Assessment description. |
| `difficulty` | string | Yes | Approved difficulty level. |
| `questionIds` | array<string> | Yes | Ordered `questions.questionId` references. |

**Relationships:** `skillId` → `skills.skillId`; each `questionIds[]` → `questions.questionId`; `assessment_results.assessmentId` → `assessments.assessmentId`; `quiz_attempts.quizId` resolves to an `assessmentId` because no separate `quizzes` collection is approved.

**Read:** Students may read active assessment content without answer keys; faculty/admin may read authorized full definitions.

**Write:** Admin/backend only.

**Validation:** Skill/question references valid; deterministic question order; valid difficulty; only complete active assessments may accept submissions; correct answers never exposed to students.

---

# 7. `questions`

**Purpose:** Question bank entries used by assessments.

| Field | Type | Required | Description |
|---|---|---|---|
| `questionId` | string | Yes | Unique question identifier; document ID. |
| `skillId` | string | Yes | Tested skill; reference to `skills.skillId`. |
| `question` | string | Yes | Question text. |
| `options` | array<object> | Yes | Structured answer options with stable option identifiers and display text. |
| `correctAnswer` | string | Yes | Correct option identifier; backend/admin-only in student-facing reads. |
| `difficulty` | string | Yes | Question difficulty. |
| `explanation` | string | Yes | Explanation for review/feedback. |

**Relationships:** `skillId` → `skills.skillId`; referenced by `assessments.questionIds[]`.

**Read:** Students get question/options without `correctAnswer`; faculty/admin can read the complete record.

**Write:** Admin/backend only.

**Validation:** Valid skill reference; unique option IDs; `correctAnswer` must match an option; non-empty question/explanation; answer key never exposed to unauthorized users.

---

# 8. `assessment_results`

**Purpose:** Historical assessment outcomes and backend-calculated proficiency.

| Field | Type | Required | Description |
|---|---|---|---|
| `resultId` | string | Yes | Unique result identifier; document ID. |
| `studentId` | string | Yes | Reference to `students.studentId`. |
| `assessmentId` | string | Yes | Reference to `assessments.assessmentId`. |
| `score` | number | Yes | Backend-calculated percentage, 0–100. |
| `proficiency` | integer | Yes | Backend-calculated level: 1 novice, 2 developing, 3 competent, 4 proficient, 5 advanced. |
| `createdAt` | timestamp | Yes | Server-generated submission/result time. |

**Relationships:** `studentId` → students; `assessmentId` → assessments. Results feed backend skill-gap and learning-path logic.

**Read:** Student own; authorized faculty; admins; recruiters only through approved candidate APIs.

**Write:** Backend only.

**Validation:** `score` 0–100; `proficiency` 1–5; valid references; values generated from submitted answers; historical results should be auditable rather than silently overwritten.

---

# 9. `evidence`

**Purpose:** Student-submitted evidence that can be reviewed by faculty.

| Field | Type | Required | Description |
|---|---|---|---|
| `evidenceId` | string | Yes | Unique evidence identifier; document ID. |
| `studentId` | string | Yes | Reference to `students.studentId`. |
| `type` | string | Yes | Approved evidence type, e.g. project/certificate/internship. |
| `title` | string | Yes | Evidence title. |
| `description` | string | Yes | Evidence description. |
| `fileUrl` | string | Yes | Approved storage file URL/reference. |
| `status` | string | Yes | `pending`, `approved`, or `rejected`. |
| `reviewedBy` | string | Optional | Reviewer `users.userId`, after review. |
| `reviewedAt` | timestamp | Optional | Review timestamp, after review. |

**Relationships:** `studentId` → `students.studentId`; `reviewedBy` → `users.userId`; evidence skill context is handled by backend API/domain logic without adding a collection.

**Read:** Student own; authorized faculty; admins; recruiters only through approved verified-evidence APIs.

**Write:** Student can submit through backend; faculty/admin can review through backend; clients may not directly set review state.

**Validation:** Ownership from authentication; approved type; file reference from approved storage; new records start `pending`; review fields server-generated; client cannot write `approved`.

---

# 10. `opportunities`

**Purpose:** Recruitment opportunities created by companies.

| Field | Type | Required | Description |
|---|---|---|---|
| `opportunityId` | string | Yes | Unique opportunity identifier; document ID. |
| `companyId` | string | Yes | Reference to `companies.companyId`. |
| `title` | string | Yes | Opportunity title. |
| `description` | string | Yes | Opportunity description. |
| `requiredSkills` | array<object> | Yes | Required skill definitions. Each item references a `skillId` and a minimum proficiency; approved backend schema may also carry an optional weight. |
| `deadline` | timestamp | Yes | Application deadline. |
| `createdAt` | timestamp | Yes | Server-generated creation time. |

**Relationships:** `companyId` → `companies.companyId`; `requiredSkills[].skillId` → `skills.skillId`; `applications.opportunityId` → `opportunities.opportunityId`.

**Read:** Students open/discoverable opportunities; recruiter owner; admins; other roles only when explicitly authorized.

**Write:** Recruiter/company owner through backend; admin for administrative operations.

**Validation:** Valid company/skill references; minimum proficiency 1–5; deadline must be valid and future when opened; `createdAt` server-generated; authoritative match scores are not stored here.

---

# 11. `applications`

**Purpose:** Student application records, including the backend-generated match score.

| Field | Type | Required | Description |
|---|---|---|---|
| `applicationId` | string | Yes | Unique application identifier; document ID. |
| `studentId` | string | Yes | Reference to `students.studentId`. |
| `opportunityId` | string | Yes | Reference to `opportunities.opportunityId`. |
| `matchScore` | number | Yes | Backend-generated match score at application time. |
| `status` | string | Yes | Approved state such as `submitted`, `shortlisted`, `rejected`, `withdrawn`. |
| `createdAt` | timestamp | Yes | Server-generated creation time. |

**Relationships:** `studentId` → students; `opportunityId` → opportunities.

**Read:** Student own; recruiter for their opportunities; admins; faculty only where explicitly authorized.

**Write:** Student creates/withdraws through backend; recruiter updates recruiter-controlled states; admin corrections; clients cannot directly set `matchScore`.

**Validation:** Authenticated student ownership; valid opportunity; opportunity accepting applications; no duplicate active application; backend-generated score; approved status values; server-generated timestamp.

---

# 12. `learning_paths`

**Purpose:** Backend-generated learning plans for closing a student's skill gap.

| Field | Type | Required | Description |
|---|---|---|---|
| `learningPathId` | string | Yes | Unique learning-path identifier; document ID. |
| `studentId` | string | Yes | Reference to `students.studentId`. |
| `skillId` | string | Yes | Target skill; reference to `skills.skillId`. |
| `currentLevel` | integer | Yes | Backend-derived current proficiency, 1–5. |
| `targetLevel` | integer | Yes | Target proficiency, 1–5. |
| `gap` | integer | Yes | Backend-calculated level gap. |
| `steps` | array<object> | Yes | Ordered backend-generated learning steps. |
| `createdAt` | timestamp | Yes | Server-generated creation time. |

**Relationships:** `studentId` → students; `skillId` → skills. Current level derives from authoritative assessment state.

**Read:** Student own; authorized faculty; admins; not directly recruiter-readable by default.

**Write:** Backend only unless a future approved authoring workflow is added through backend authorization.

**Validation:** Levels 1–5; `targetLevel >= currentLevel`; `gap = targetLevel - currentLevel`; valid references; deterministic step ordering; client cannot overwrite calculated `gap`.

---

# 13. `quiz_attempts`

**Purpose:** Student quiz/assessment attempt history and backend-calculated score.

| Field | Type | Required | Description |
|---|---|---|---|
| `attemptId` | string | Yes | Unique attempt identifier; document ID. |
| `studentId` | string | Yes | Reference to `students.studentId`. |
| `quizId` | string | Yes | Logical quiz identifier; because no `quizzes` collection is approved, it resolves to `assessments.assessmentId` when the quiz is an assessment. |
| `answers` | array<object> | Yes | Submitted answers using backend-approved question/option identifiers. |
| `score` | number | Yes | Backend-calculated score, normally 0–100. |
| `createdAt` | timestamp | Yes | Server-generated attempt time. |

**Relationships:** `studentId` → students; `quizId` → assessments when applicable; answer question IDs → questions.

**Read:** Student own; authorized faculty; admins; not directly recruiter-readable.

**Write:** Student creates attempts through backend; backend calculates score.

**Validation:** Authenticated ownership; valid quiz/assessment; question IDs belong to referenced assessment; no duplicate answers for the same question; score 0–100 and backend-generated; server timestamp.

---

# 14. `chat_sessions`

**Purpose:** Persistent AI Career & Skill Copilot sessions for students.

| Field | Type | Required | Description |
|---|---|---|---|
| `sessionId` | string | Yes | Unique session identifier; document ID. |
| `studentId` | string | Yes | Reference to `students.studentId`. |
| `messages` | array<object> | Yes | Ordered conversation messages using the backend-approved message schema. |
| `createdAt` | timestamp | Yes | Server-generated creation time. |
| `updatedAt` | timestamp | Yes | Server-managed last-update time. |

**Relationships:** `studentId` → students. AI context may be derived from backend skill/profile state; chat history is not the authority for those values.

**Read:** Student own; admin only under authorized operational/support workflows; no recruiter/faculty access by default.

**Write:** Student through backend AI API; backend service persists the session.

**Validation:** Authenticated ownership; chronological message ordering; approved message roles; non-empty content; timestamps server-managed; never store credentials/tokens/API keys in messages.

---

# Cross-collection relationship map

```text
users
 ├── students.userId
 ├── companies.userId
 └── evidence.reviewedBy

institutions
 └── institution context used by authorization/analytics

skills
 ├── students.skills[]
 ├── assessments.skillId
 ├── questions.skillId
 ├── opportunities.requiredSkills[].skillId
 └── learning_paths.skillId

assessments
 ├── assessments.questionIds[]
 ├── assessment_results.assessmentId
 └── quiz_attempts.quizId

questions
 └── assessments.questionIds[]

students
 ├── assessment_results.studentId
 ├── evidence.studentId
 ├── applications.studentId
 ├── learning_paths.studentId
 ├── quiz_attempts.studentId
 └── chat_sessions.studentId

companies
 └── opportunities.companyId

opportunities
 └── applications.opportunityId
```

# Access-control rules

### Students
Students can access their own student data, assessment results, evidence, applications, learning paths, quiz attempts, and chat sessions, plus permitted skills, assessments, and discoverable opportunities. They cannot directly write score, proficiency, verification, match-score, reviewer, or other backend-authoritative fields.

### Faculty
Faculty can access only students they are authorized to manage, including relevant student profiles, assessment results, evidence, learning paths, and competency information. Cross-institution access is prohibited unless explicitly granted by backend policy.

### Recruiters
Recruiters can access their company, their opportunities, candidate data exposed through recruitment APIs, and applications for their opportunities. They cannot directly modify student proficiency, evidence verification, or match scores.

### Admins
Admins can access authorized institution/platform management data, including institutions, skills, assessments, evidence review, and analytics according to backend policy.

# Consistency and transaction rules

Where a business operation changes multiple related documents, the backend should use Firestore atomic/batched operations or transactions where needed.

**Assessment submission:** result persistence and corresponding authoritative proficiency updates must be consistent.

**Evidence review:** review state and downstream verified-evidence state must be consistent.

**Application creation:** the stored `matchScore` must be generated from the same authoritative student/opportunity state used for the application decision.

# Expected indexes

Expected query patterns may require Firestore composite indexes, including:

- `assessment_results`: `studentId` + `assessmentId`
- `evidence`: `studentId` + `status`
- `opportunities`: `companyId` + `deadline`
- `applications`: `studentId` + `opportunityId`
- `applications`: `opportunityId` + `status`
- `learning_paths`: `studentId` + `skillId`
- `quiz_attempts`: `studentId` + `quizId`
- `chat_sessions`: `studentId` + `updatedAt`

Indexes must be added to approved collections only. Do not create a collection just to optimize a query.

# Source-of-truth rules

1. The frontend consumes backend-approved data; it does not own database truth.
2. FastAPI is the business authority for scores, proficiency, gaps, verification, matching, permissions, and application rules.
3. Firebase Authentication is the identity authority; the backend maps identity to application role and ownership.
4. Firestore is the persistence authority for the 14 approved collections.
5. No additional top-level collection may be created without explicit approval and an update to this document.
6. Field names and semantics must not be silently changed.
7. Any schema change must update this document and the API contract together before dependent implementation.
8. Historical assessment, evidence, and application state must remain auditable.
9. Firestore security rules must enforce ownership boundaries and must not rely on frontend checks.
10. Secrets, service-account credentials, access tokens, and API keys must never be stored in these application collections.
