from datetime import datetime, timezone
import logging
import re
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

import uuid
from app.auth import get_current_user
from app.firebase import get_db
from app.models import (
    PROFICIENCY_LEVELS,
    AssessmentHistoryItem,
    AssessmentQuestion,
    AssessmentResultResponse,
    AssessmentSubmission,
    DataProvenance,
    QuizDetailResponse,
    QuizQuestionResponse,
    QuizResultResponse,
    QuizSubmissionRequest,
    SkillCreate,
    SkillEvidence,
    SkillResponse,
    SkillUpdate,
    UserProfileResponse,
)
from app.rate_limit import check_user_rate_limit
from app.routes.notifications import create_notification
from firebase_admin import firestore as fb_firestore

logger = logging.getLogger("academialink.skills")


def _bump_taxonomy_popularity(db, skill_name: str) -> None:
    """
    Best-effort: increments the canonical taxonomy skill's real usage counter whenever a
    student adds or is assessed on it, so 'popular skills' reflects actual system usage,
    never an editorial/arbitrary ranking. Never raises - a taxonomy miss must not break
    the student-facing skill/assessment flow.
    """
    try:
        name_low = skill_name.strip().lower()
        matches = list(db.collection("skills").where("active", "==", True).stream())
        for doc in matches:
            data = doc.to_dict() or {}
            if str(data.get("name", "")).strip().lower() == name_low or name_low in [
                a.strip().lower() for a in (data.get("aliases") or [])
            ]:
                doc.reference.update({"popularity": fb_firestore.Increment(1)})
                return
    except Exception as e:
        logger.warning("Could not bump taxonomy popularity for '%s': %s", skill_name, e)

router = APIRouter(prefix="/skills", tags=["Student Skills & Assessment"])

# Deterministic assessment question bank with server-side answer keys
ASSESSMENT_QUESTION_BANK: Dict[str, List[dict]] = {
    "python": [
        {
            "id": "py_1",
            "question": "What is the time complexity of looking up a key in a standard Python dictionary on average?",
            "options": ["O(1)", "O(n)", "O(log n)", "O(n^2)"],
            "correctIndex": 0,
        },
        {
            "id": "py_2",
            "question": "Which Python mechanism is used to implement a generator function?",
            "options": ["return", "yield", "async", "lambda"],
            "correctIndex": 1,
        },
        {
            "id": "py_3",
            "question": "What does the Python GIL (Global Interpreter Lock) primarily restrict?",
            "options": [
                "Memory allocation per process",
                "Execution of multiple native Python bytecodes simultaneously across threads",
                "Asynchronous I/O operations",
                "Importing C extensions",
            ],
            "correctIndex": 1,
        },
        {
            "id": "py_4",
            "question": "In Python, which built-in function returns an iterator of tuples pairing elements from multiple iterables?",
            "options": ["enumerate()", "zip()", "map()", "filter()"],
            "correctIndex": 1,
        },
        {
            "id": "py_5",
            "question": "What is the output of isinstance(True, int) in Python?",
            "options": ["False", "True", "TypeError", "None"],
            "correctIndex": 1,
        },
    ],
    "react": [
        {
            "id": "rc_1",
            "question": "What is the primary purpose of React's virtual DOM reconciliation algorithm?",
            "options": [
                "Directly overwrite innerHTML on every render",
                "Efficiently calculate the minimal set of changes required to update the actual DOM",
                "Compile JSX into WebAssembly",
                "Bypass browser rendering pipelines completely",
            ],
            "correctIndex": 1,
        },
        {
            "id": "rc_2",
            "question": "When should the useEffect cleanup function be returned?",
            "options": [
                "Before the initial render",
                "When subscriptions, timers, or event listeners need to be cancelled before unmount or re-execution",
                "Only during server-side rendering",
                "Never, React automatically cleans up all side-effects",
            ],
            "correctIndex": 1,
        },
        {
            "id": "rc_3",
            "question": "What happens when you call useState setter with the exact same primitive value as current state?",
            "options": [
                "React throws an error",
                "React bails out of re-rendering the component subtree",
                "Component enters an infinite render loop",
                "React forces a full DOM re-mount",
            ],
            "correctIndex": 1,
        },
        {
            "id": "rc_4",
            "question": "Which hook is specifically designed to memoize an expensive calculation result between renders?",
            "options": ["useCallback", "useMemo", "useRef", "useTransition"],
            "correctIndex": 1,
        },
        {
            "id": "rc_5",
            "question": "What is the key rule when using React hooks?",
            "options": [
                "Must be called inside loops and conditional statements",
                "Must be called only at the top level of React function components or custom hooks",
                "Must be defined inside class methods",
                "Must be asynchronous functions",
            ],
            "correctIndex": 1,
        },
    ],
    "general": [
        {
            "id": "gen_1",
            "question": "In relational databases, which property ensures that a transaction is completely finished or completely undone?",
            "options": ["Atomicity", "Consistency", "Isolation", "Durability"],
            "correctIndex": 0,
        },
        {
            "id": "gen_2",
            "question": "What HTTP status code represents an unauthorized request due to missing or invalid authentication credentials?",
            "options": ["400", "401", "403", "404"],
            "correctIndex": 1,
        },
        {
            "id": "gen_3",
            "question": "Which data structure uses LIFO (Last-In, First-Out) ordering?",
            "options": ["Queue", "Stack", "Binary Tree", "Linked List"],
            "correctIndex": 1,
        },
        {
            "id": "gen_4",
            "question": "What is the primary benefit of containerization with Docker compared to traditional virtual machines?",
            "options": [
                "Runs a full guest OS kernel for every container",
                "Shares the host OS kernel and provides lightweight process isolation with low overhead",
                "Cannot be deployed to cloud platforms",
                "Eliminates the need for networking",
            ],
            "correctIndex": 1,
        },
        {
            "id": "gen_5",
            "question": "In Git, which command creates a new branch and immediately switches to it?",
            "options": ["git checkout -b <branch>", "git merge <branch>", "git commit -m <branch>", "git push -u <branch>"],
            "correctIndex": 0,
        },
    ],
    "sql": [
        {
            "id": "sql_1",
            "question": "Which SQL clause is used to filter rows AFTER aggregation (e.g. after a GROUP BY)?",
            "options": ["WHERE", "HAVING", "FILTER", "ORDER BY"],
            "correctIndex": 1,
        },
        {
            "id": "sql_2",
            "question": "Which JOIN returns all rows from the left table and matched rows from the right table, with NULLs where there is no match?",
            "options": ["INNER JOIN", "LEFT JOIN", "CROSS JOIN", "RIGHT JOIN"],
            "correctIndex": 1,
        },
        {
            "id": "sql_3",
            "question": "What does a PRIMARY KEY constraint guarantee for a column?",
            "options": [
                "Values can repeat but not be NULL",
                "Values must be unique and NOT NULL",
                "Values must be sorted ascending",
                "Values must be foreign keys in another table",
            ],
            "correctIndex": 1,
        },
        {
            "id": "sql_4",
            "question": "Which SQL command permanently removes a table and its structure from the database?",
            "options": ["DELETE", "TRUNCATE", "DROP", "REMOVE"],
            "correctIndex": 2,
        },
        {
            "id": "sql_5",
            "question": "What is the primary purpose of a database index?",
            "options": [
                "Enforce foreign key relationships",
                "Speed up data retrieval at the cost of extra storage and slower writes",
                "Encrypt column data",
                "Automatically back up the table",
            ],
            "correctIndex": 1,
        },
    ],
    "javascript": [
        {
            "id": "js_1",
            "question": "What does the strict equality operator (===) check that the loose equality operator (==) does not?",
            "options": [
                "Nothing, they behave identically",
                "It also checks that the operand types match, without type coercion",
                "It only works on numbers",
                "It checks object references only",
            ],
            "correctIndex": 1,
        },
        {
            "id": "js_2",
            "question": "What is a closure in JavaScript?",
            "options": [
                "A syntax error handler",
                "A function that retains access to its lexical scope's variables even after the outer function has returned",
                "A way to close a network connection",
                "A CSS-in-JS technique",
            ],
            "correctIndex": 1,
        },
        {
            "id": "js_3",
            "question": "Which keyword declares a block-scoped variable that cannot be reassigned?",
            "options": ["var", "let", "const", "static"],
            "correctIndex": 2,
        },
        {
            "id": "js_4",
            "question": "What does Array.prototype.map() return?",
            "options": [
                "The original array, mutated in place",
                "A new array with the results of calling a function on every element",
                "A single accumulated value",
                "A boolean indicating if any element matches",
            ],
            "correctIndex": 1,
        },
        {
            "id": "js_5",
            "question": "In the JavaScript event loop, when do microtasks (e.g. resolved Promise callbacks) run relative to macrotasks (e.g. setTimeout)?",
            "options": [
                "After all macrotasks in the queue",
                "Before the next macrotask, once the current call stack is empty",
                "At the exact same time as macrotasks",
                "Only after the page fully reloads",
            ],
            "correctIndex": 1,
        },
    ],
    "git": [
        {
            "id": "git_1",
            "question": "What is the difference between 'git fetch' and 'git pull'?",
            "options": [
                "They are identical commands",
                "git fetch downloads remote changes without merging; git pull fetches and merges into the current branch",
                "git pull only works on the main branch",
                "git fetch deletes local commits",
            ],
            "correctIndex": 1,
        },
        {
            "id": "git_2",
            "question": "What does 'git rebase' do differently from 'git merge'?",
            "options": [
                "Rebase deletes the feature branch immediately",
                "Rebase rewrites commit history by replaying commits on top of another base, instead of creating a merge commit",
                "Rebase only works with remote repositories",
                "Rebase and merge behave identically",
            ],
            "correctIndex": 1,
        },
        {
            "id": "git_3",
            "question": "Which file tells Git which files/directories to ignore from version control?",
            "options": [".gitconfig", ".gitignore", ".gitattributes", "git.ignore"],
            "correctIndex": 1,
        },
        {
            "id": "git_4",
            "question": "What does 'git cherry-pick <commit>' do?",
            "options": [
                "Deletes the specified commit from history",
                "Applies the changes from a specific commit onto the current branch",
                "Creates a new empty branch",
                "Reverts all commits after the specified one",
            ],
            "correctIndex": 1,
        },
        {
            "id": "git_5",
            "question": "What is a 'detached HEAD' state in Git?",
            "options": [
                "A corrupted repository that must be re-cloned",
                "When HEAD points directly to a commit instead of a branch reference, so new commits won't belong to any branch",
                "A branch with no commits",
                "The default state after 'git init'",
            ],
            "correctIndex": 1,
        },
    ],
    "cybersecurity": [
        {
            "id": "cyb_1",
            "question": "What does the 'confidentiality' principle in the CIA triad refer to?",
            "options": [
                "Ensuring data is accurate and unaltered",
                "Ensuring data is accessible only to authorized parties",
                "Ensuring systems remain available during an attack",
                "Ensuring data is backed up regularly",
            ],
            "correctIndex": 1,
        },
        {
            "id": "cyb_2",
            "question": "What is the primary purpose of multi-factor authentication (MFA)?",
            "options": [
                "Replace passwords entirely with biometrics",
                "Require two or more independent credentials to verify identity, reducing risk from a single compromised factor",
                "Encrypt data at rest",
                "Speed up login by skipping password checks",
            ],
            "correctIndex": 1,
        },
        {
            "id": "cyb_3",
            "question": "What distinguishes a phishing attack from a brute-force attack?",
            "options": [
                "Phishing tries every possible password; brute-force tricks users into revealing credentials",
                "Phishing tricks users into revealing credentials via deception; brute-force systematically guesses credentials",
                "They are the same attack with different names",
                "Phishing only targets servers, never individuals",
            ],
            "correctIndex": 1,
        },
        {
            "id": "cyb_4",
            "question": "What is the main purpose of a firewall in a network?",
            "options": [
                "Encrypt all outgoing emails",
                "Monitor and control incoming/outgoing network traffic based on defined security rules",
                "Automatically patch operating system vulnerabilities",
                "Store user passwords securely",
            ],
            "correctIndex": 1,
        },
        {
            "id": "cyb_5",
            "question": "What is the goal of a penetration test?",
            "options": [
                "To cause maximum damage to production systems",
                "To simulate real-world attacks under authorization in order to find and report exploitable vulnerabilities before attackers do",
                "To install antivirus software",
                "To train employees on phishing awareness only",
            ],
            "correctIndex": 1,
        },
    ],
    "machine learning": [
        {
            "id": "ml_1",
            "question": "What is 'overfitting' in a machine learning model?",
            "options": [
                "The model performs poorly on both training and test data",
                "The model learns the training data too closely, including noise, and generalizes poorly to new data",
                "The model trains faster than expected",
                "The model uses too few features",
            ],
            "correctIndex": 1,
        },
        {
            "id": "ml_2",
            "question": "What is the main difference between supervised and unsupervised learning?",
            "options": [
                "Supervised learning requires no data at all",
                "Supervised learning uses labeled data to learn a mapping to known outputs; unsupervised learning finds patterns in unlabeled data",
                "Unsupervised learning is always more accurate",
                "They are the same technique",
            ],
            "correctIndex": 1,
        },
        {
            "id": "ml_3",
            "question": "Why is a train/validation/test split used when building a model?",
            "options": [
                "To make training slower on purpose",
                "To fairly evaluate generalization performance and tune hyperparameters without leaking test data into training",
                "It is only needed for deep learning models",
                "To reduce the total amount of data needed",
            ],
            "correctIndex": 1,
        },
        {
            "id": "ml_4",
            "question": "What does a confusion matrix summarize for a classification model?",
            "options": [
                "The model's training time and memory usage",
                "The counts of true positives, true negatives, false positives, and false negatives",
                "The learning rate schedule",
                "The number of features used",
            ],
            "correctIndex": 1,
        },
        {
            "id": "ml_5",
            "question": "What is the purpose of regularization (e.g. L1/L2) in a model?",
            "options": [
                "To increase model complexity for better fit",
                "To penalize large weights and reduce overfitting, improving generalization",
                "To speed up data loading",
                "To convert categorical features to numeric",
            ],
            "correctIndex": 1,
        },
    ],
}

# Maps a canonical taxonomy skill slug to the ASSESSMENT_QUESTION_BANK key used for its
# question set, for cases where the bank's historical key name differs from the skill slug.
SKILL_SLUG_TO_BANK_KEY: Dict[str, str] = {
    "software_engineering": "general",
    "machine_learning": "machine learning",
}


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower())
    return slug.strip("_")


def resolve_bank_key(skill_name: str) -> Optional[str]:
    """
    Resolves a raw skill name to a REAL question-bank key, or None if no fact-checked
    question bank exists for it yet. Never silently substitutes an unrelated bank (e.g. the
    old 'general' fallback) so a student can't be scored on questions that don't match the
    skill they selected.
    """
    direct = skill_name.strip().lower()
    if direct in ASSESSMENT_QUESTION_BANK:
        return direct
    slug = _slugify(skill_name)
    mapped = SKILL_SLUG_TO_BANK_KEY.get(slug)
    if mapped and mapped in ASSESSMENT_QUESTION_BANK:
        return mapped
    if slug in ASSESSMENT_QUESTION_BANK:
        return slug
    return None


def serialize_skill(doc_id: str, data: dict) -> SkillResponse:
    """Helper to convert Firestore skill document dict to SkillResponse model."""
    proficiency = int(data.get("proficiency", 3))
    # Constrain proficiency to 1..5
    proficiency = max(1, min(5, proficiency))
    level = PROFICIENCY_LEVELS.get(proficiency, "Intermediate")
    score = proficiency * 20

    evidence_dict = data.get("evidence")
    evidence_obj = None
    if evidence_dict and isinstance(evidence_dict, dict):
        evidence_obj = SkillEvidence(**evidence_dict)

    return SkillResponse(
        skillId=doc_id,
        id=doc_id,
        name=data.get("name", "Skill"),
        category=data.get("category", "Technical"),
        proficiency=proficiency,
        level=level,
        score=score,
        required=data.get("required", 75),
        source=data.get("source", "manual"),
        evidence=evidence_obj,
        verified=bool(data.get("verified", evidence_obj.verified if evidence_obj else False)),
        trend=int(data.get("trend", 0)),
        createdAt=data.get("createdAt"),
        updatedAt=data.get("updatedAt"),
    )


@router.get("/me", response_model=List[SkillResponse], summary="Get authenticated student's skills")
async def get_my_skills(current_user: UserProfileResponse = Depends(get_current_user)):
    """Retrieve all skills from the authenticated student's subcollection: users/{uid}/skills"""
    try:
        db = get_db()
        skills_ref = db.collection("users").document(current_user.uid).collection("skills")
        docs = skills_ref.stream()

        skills = []
        for doc in docs:
            d = doc.to_dict() or {}
            skills.append(serialize_skill(doc.id, d))
        return skills
    except Exception as e:
        logger.error("Error retrieving skills for user %s: %s", current_user.uid, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve skills: {str(e)}",
        )


@router.post("/me", response_model=SkillResponse, status_code=status.HTTP_201_CREATED, summary="Add a new skill")
async def add_my_skill(
    skill_in: SkillCreate,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Add a new skill to the authenticated student's subcollection: users/{uid}/skills.
    Validates proficiency scale: 1=Beginner, 2=Basic, 3=Intermediate, 4=Advanced, 5=Expert.
    """
    try:
        db = get_db()
        skills_ref = db.collection("users").document(current_user.uid).collection("skills")

        now_iso = datetime.now(timezone.utc).isoformat()
        skill_dict = skill_in.model_dump()

        # Evidence security: self-claimed evidence is unverified by default
        if skill_dict.get("evidence"):
            skill_dict["evidence"]["verified"] = False
            skill_dict["verified"] = False
        else:
            skill_dict["verified"] = False

        skill_dict["createdAt"] = now_iso
        skill_dict["updatedAt"] = now_iso
        skill_dict["trend"] = 0
        skill_dict["score"] = skill_in.proficiency * 20
        skill_dict["required"] = 75

        # Create new document in users/{uid}/skills/{skillId}
        new_doc_ref = skills_ref.document()
        skill_dict["skillId"] = new_doc_ref.id
        new_doc_ref.set(skill_dict)
        _bump_taxonomy_popularity(db, skill_in.name)

        logger.info("Added skill '%s' for user %s (ID: %s)", skill_in.name, current_user.uid, new_doc_ref.id)
        return serialize_skill(new_doc_ref.id, skill_dict)
    except Exception as e:
        logger.error("Error adding skill for user %s: %s", current_user.uid, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add skill: {str(e)}",
        )


@router.put("/me/{skill_id}", response_model=SkillResponse, summary="Update an existing skill")
async def update_my_skill(
    skill_id: str,
    skill_update: SkillUpdate,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Update a skill document in users/{uid}/skills/{skill_id}.
    A student can only modify their own skills.
    """
    try:
        db = get_db()
        skill_doc_ref = db.collection("users").document(current_user.uid).collection("skills").document(skill_id)
        doc = skill_doc_ref.get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill with ID '{skill_id}' not found for current user",
            )

        update_payload = {k: v for k, v in skill_update.model_dump(exclude_unset=True).items()}
        if "proficiency" in update_payload and update_payload["proficiency"] is not None:
            update_payload["score"] = update_payload["proficiency"] * 20
        update_payload["updatedAt"] = datetime.now(timezone.utc).isoformat()

        skill_doc_ref.set(update_payload, merge=True)

        fresh_doc = skill_doc_ref.get()
        data = fresh_doc.to_dict() or {}
        return serialize_skill(fresh_doc.id, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating skill %s for user %s: %s", skill_id, current_user.uid, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update skill: {str(e)}",
        )


@router.delete("/me/{skill_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a skill")
async def delete_my_skill(
    skill_id: str,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Delete a skill document from users/{uid}/skills/{skill_id}.
    A student can only delete their own skills.
    """
    try:
        db = get_db()
        skill_doc_ref = db.collection("users").document(current_user.uid).collection("skills").document(skill_id)
        doc = skill_doc_ref.get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill with ID '{skill_id}' not found for current user",
            )
        skill_doc_ref.delete()
        logger.info("Deleted skill %s for user %s", skill_id, current_user.uid)
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting skill %s for user %s: %s", skill_id, current_user.uid, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete skill: {str(e)}",
        )


# ===================== ASSESSMENT APIS =====================

@router.get("/assessment/questions", response_model=List[AssessmentQuestion], summary="Get assessment questions for a skill")
async def get_assessment_questions(
    skill: str = Query("python", max_length=150, description="Skill name to assess (e.g. python, react, general)"),
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """Returns assessment questions without server-side answer keys."""
    bank_key = resolve_bank_key(skill)
    if bank_key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No assessment is available yet for '{skill}'. You can still self-declare this skill with evidence.",
        )
    questions = ASSESSMENT_QUESTION_BANK[bank_key]

    return [
        AssessmentQuestion(
            id=q["id"],
            question=q["question"],
            options=q["options"],
            difficulty=i + 1,
        )
        for i, q in enumerate(questions)
    ]


@router.post("/assessment", response_model=AssessmentResultResponse, summary="Submit skill assessment and calculate proficiency")
async def evaluate_assessment(
    submission: AssessmentSubmission,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Deterministic Assessment Evaluation:
    Evaluates submitted answers against standard answer keys.
    Deterministic Scoring:
      0-1 correct -> Proficiency 1 (Beginner, 20%)
      2 correct   -> Proficiency 2 (Basic, 40%)
      3 correct   -> Proficiency 3 (Intermediate, 60%)
      4 correct   -> Proficiency 4 (Advanced, 80%)
      5 correct   -> Proficiency 5 (Expert, 100%)
    Stores the assessed skill in the student's subcollection users/{uid}/skills/{skillId}
    with verified evidence.
    """
    await check_user_rate_limit(current_user.uid, "assessment_submit")
    bank_key = resolve_bank_key(submission.skillName)
    if bank_key is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No assessment is available yet for '{submission.skillName}'. You can still self-declare this skill with evidence via POST /api/skills/me.",
        )
    questions = ASSESSMENT_QUESTION_BANK[bank_key]
    total_questions = len(questions)

    # Map question answers
    answer_map = {a.questionId: a.selectedOption for a in submission.answers}

    correct_count = 0
    for q in questions:
        qid = q["id"]
        if qid in answer_map and answer_map[qid] == q["correctIndex"]:
            correct_count += 1

    # Deterministic proficiency calculation
    if correct_count <= 1:
        proficiency = 1
    elif correct_count == 2:
        proficiency = 2
    elif correct_count == 3:
        proficiency = 3
    elif correct_count == 4:
        proficiency = 4
    else:
        proficiency = 5

    level = PROFICIENCY_LEVELS[proficiency]
    score_percentage = round((correct_count / total_questions) * 100) if total_questions > 0 else 20
    explanation = (
        f"Answered {correct_count} of {total_questions} questions correctly ({score_percentage}%), "
        f"demonstrating {level} proficiency (Level {proficiency}/5)."
    )

    now_iso = datetime.now(timezone.utc).isoformat()
    db = get_db()
    skill_slug = "skill_" + submission.skillName.strip().lower().replace(" ", "_").replace("/", "_")
    skill_ref = db.collection("users").document(current_user.uid).collection("skills").document(skill_slug)
    existing_snap = skill_ref.get()

    previous_prof = None
    final_prof = proficiency
    preserved_verified = False

    if existing_snap.exists:
        existing_data = existing_snap.to_dict() or {}
        previous_prof = float(existing_data.get("proficiency", 1.0))
        is_faculty_verified = existing_data.get("source") in ["faculty_verified", "mentor_verified"] or existing_data.get("faculty_approved", False)
        # Requirement: Do NOT silently overwrite manually verified skill proficiency or approved evidence
        if is_faculty_verified or (existing_data.get("verified", False) and previous_prof > proficiency):
            final_prof = previous_prof
            preserved_verified = True

    level = PROFICIENCY_LEVELS[proficiency]
    score_percentage = round((correct_count / total_questions) * 100) if total_questions > 0 else 20
    explanation = (
        f"Answered {correct_count} of {total_questions} questions correctly ({score_percentage}%), "
        f"demonstrating {level} proficiency (Level {proficiency}/5)."
    )
    if preserved_verified:
        explanation += f" Preserved previously verified proficiency of Level {final_prof}/5."

    evidence_data = {
        "type": "assessment",
        "title": f"AcademiaLINK {submission.skillName} Assessment",
        "description": explanation,
        "verified": True,
        "issuedBy": "AcademiaLINK Assessment Engine",
        "issueDate": now_iso,
    }

    skill_payload = {
        "skillId": skill_slug,
        "name": submission.skillName,
        "category": submission.category,
        "proficiency": final_prof,
        "score": final_prof * 20,
        "required": 75,
        "source": "assessment" if not preserved_verified else existing_data.get("source", "assessment"),
        "evidence": evidence_data,
        "verified": True,
        "updatedAt": now_iso,
    }
    if not existing_snap.exists:
        skill_payload["createdAt"] = now_iso
        skill_payload["trend"] = 0

    skill_ref.set(skill_payload, merge=True)
    _bump_taxonomy_popularity(db, submission.skillName)
    stored_doc = skill_ref.get()

    # Store assessment in user's assessment history
    assessment_id = f"asmt_{uuid.uuid4().hex[:12]}"
    history_record = {
        "assessment_id": assessment_id,
        "skill_name": submission.skillName,
        "category": submission.category,
        "score_percentage": float(score_percentage),
        "assessed_proficiency": float(proficiency),
        "correct_count": correct_count,
        "total_questions": total_questions,
        "timestamp": now_iso,
        "provenance": {
            "source": "deterministic_assessment_engine",
            "data_status": "verified",
            "retrieved_at": now_iso,
            "is_test_data": False,
        },
    }
    db.collection("users").document(current_user.uid).collection("assessment_history").document(assessment_id).set(history_record)

    # Trigger notification
    create_notification(
        db,
        current_user.uid,
        "assessment_completed",
        f"Skill Assessment Completed: {submission.skillName}",
        f"You scored {score_percentage}% ({correct_count}/{total_questions}) on {submission.skillName}. Assessed proficiency: Level {proficiency}/5.",
        related_id=assessment_id,
    )

    skill_response = serialize_skill(skill_slug, stored_doc.to_dict() or {})

    return AssessmentResultResponse(
        skillName=submission.skillName,
        category=submission.category,
        proficiency=final_prof,
        level=level,
        scorePercentage=score_percentage,
        totalQuestions=total_questions,
        correctCount=correct_count,
        explanation=explanation,
        skill=skill_response,
    )


@router.get("/quiz/{skill_name}", response_model=QuizDetailResponse, summary="Get quiz questions for a skill")
async def get_quiz_for_skill(
    skill_name: str,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Returns multiple-choice quiz questions for a specific skill.
    Never exposes correctIndex to prevent client-side answer cheating.
    """
    bank_key = resolve_bank_key(skill_name)
    if bank_key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No assessment is available yet for '{skill_name}'. You can still self-declare this skill with evidence.",
        )
    raw_questions = ASSESSMENT_QUESTION_BANK[bank_key]
    questions = [
        QuizQuestionResponse(
            id=q["id"],
            question=q["question"],
            options=q["options"],
            skill=skill_name,
        )
        for q in raw_questions
    ]
    return QuizDetailResponse(
        skill_name=skill_name,
        total_questions=len(questions),
        questions=questions,
        provenance=DataProvenance(source="assessment_question_bank"),
    )


@router.post("/quiz/submit", response_model=QuizResultResponse, summary="Submit quiz and calculate proficiency")
async def submit_quiz(
    submission: QuizSubmissionRequest,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Evaluates quiz submission deterministically:
    - Score percentage = correct / total
    - Map percentage to 1-5 proficiency scale
    - Record in assessment history
    - Preserve verified proficiencies
    """
    await check_user_rate_limit(current_user.uid, "assessment_submit")
    bank_key = resolve_bank_key(submission.skill_name)
    if bank_key is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No assessment is available yet for '{submission.skill_name}'. You can still self-declare this skill with evidence via POST /api/skills/me.",
        )
    questions = ASSESSMENT_QUESTION_BANK[bank_key]
    total_questions = len(questions)

    correct_count = 0
    for q in questions:
        qid = q["id"]
        if qid in submission.answers and submission.answers[qid] == q["correctIndex"]:
            correct_count += 1

    # Deterministic proficiency calculation (1-5 scale)
    if correct_count <= 1:
        assessed_proficiency = 1.0
    elif correct_count == 2:
        assessed_proficiency = 2.0
    elif correct_count == 3:
        assessed_proficiency = 3.0
    elif correct_count == 4:
        assessed_proficiency = 4.0
    else:
        assessed_proficiency = 5.0

    score_percentage = round((correct_count / total_questions) * 100, 1) if total_questions > 0 else 20.0

    now_iso = datetime.now(timezone.utc).isoformat()
    db = get_db()
    skill_slug = "skill_" + submission.skill_name.strip().lower().replace(" ", "_").replace("/", "_")
    skill_ref = db.collection("users").document(current_user.uid).collection("skills").document(skill_slug)
    existing_snap = skill_ref.get()

    previous_prof = None
    final_prof = assessed_proficiency
    preserved_verified = False

    if existing_snap.exists:
        existing_data = existing_snap.to_dict() or {}
        previous_prof = float(existing_data.get("proficiency", 1.0))
        is_verified = existing_data.get("verified", False) or existing_data.get("source") in ["faculty_verified", "mentor_verified"]
        if is_verified and previous_prof > assessed_proficiency:
            final_prof = previous_prof
            preserved_verified = True

    level = PROFICIENCY_LEVELS[int(round(final_prof))]
    explanation = (
        f"Answered {correct_count} of {total_questions} questions correctly ({score_percentage}%). "
        f"Assessed proficiency: Level {assessed_proficiency}/5. "
        + (f"Preserved previously verified proficiency of Level {final_prof}/5." if preserved_verified else f"Skill proficiency updated to Level {final_prof}/5 ({level}).")
    )

    # Save to user skills
    skill_payload = {
        "skillId": skill_slug,
        "name": submission.skill_name,
        "category": submission.category,
        "proficiency": final_prof,
        "score": final_prof * 20,
        "required": 75,
        "source": "assessment" if not preserved_verified else existing_data.get("source", "assessment"),
        "verified": True,
        "updatedAt": now_iso,
    }
    if not existing_snap.exists:
        skill_payload["createdAt"] = now_iso
        skill_payload["trend"] = 0
    skill_ref.set(skill_payload, merge=True)
    _bump_taxonomy_popularity(db, submission.skill_name)

    # Record assessment history
    assessment_id = f"asmt_{uuid.uuid4().hex[:12]}"
    history_record = {
        "assessment_id": assessment_id,
        "skill_name": submission.skill_name,
        "category": submission.category,
        "score_percentage": score_percentage,
        "assessed_proficiency": assessed_proficiency,
        "correct_count": correct_count,
        "total_questions": total_questions,
        "timestamp": now_iso,
        "provenance": {
            "source": "deterministic_assessment_engine",
            "data_status": "verified",
            "retrieved_at": now_iso,
            "is_test_data": False,
        },
    }
    db.collection("users").document(current_user.uid).collection("assessment_history").document(assessment_id).set(history_record)

    # Dispatch notification
    create_notification(
        db,
        current_user.uid,
        "assessment_completed",
        f"Assessment Completed: {submission.skill_name}",
        f"You scored {score_percentage}% ({correct_count}/{total_questions}) on {submission.skill_name}.",
        related_id=assessment_id,
    )

    return QuizResultResponse(
        assessment_id=assessment_id,
        skill_name=submission.skill_name,
        category=submission.category,
        total_questions=total_questions,
        correct_count=correct_count,
        score_percentage=score_percentage,
        assessed_proficiency=assessed_proficiency,
        previous_proficiency=previous_prof,
        current_proficiency=final_prof,
        preserved_verified=preserved_verified,
        explanation=explanation,
        timestamp=now_iso,
        provenance=DataProvenance(source="deterministic_assessment_engine", data_status="verified"),
    )


@router.get("/assessments/history", response_model=List[AssessmentHistoryItem], summary="Get assessment history for current student")
async def get_assessment_history(
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """Retrieve historical assessment results for the authenticated student."""
    db = get_db()
    docs = db.collection("users").document(current_user.uid).collection("assessment_history").stream()
    items = []
    for doc in docs:
        d = doc.to_dict() or {}
        if not d.get("assessment_id"):
            d["assessment_id"] = doc.id
        items.append(AssessmentHistoryItem(**d))

    items.sort(key=lambda x: x.timestamp or "", reverse=True)
    return items


@router.get("/categories", response_model=List[str], summary="List supported skill categories")
async def get_skill_categories():
    """Returns available skill classification categories."""
    return ["Technical", "Soft", "Domain", "Tools"]

