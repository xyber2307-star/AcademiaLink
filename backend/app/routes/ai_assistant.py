from datetime import datetime, timezone
import logging
import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.firebase import get_db
from app.models import AIChatRequest, AIChatResponse, DataProvenance, UserProfileResponse

logger = logging.getLogger("academialink.ai_assistant")

router = APIRouter(prefix="/ai", tags=["AI Career Assistant"])


def _calculate_grounded_job_gap(student_skills: Dict[str, float], job_data: dict) -> Dict[str, Any]:
    """Deterministically reconciles student skills with job requirements."""
    req_skills = job_data.get("required_skills", [])
    pref_skills = job_data.get("preferred_skills", [])
    min_prof = float(job_data.get("minimum_proficiency", 3.0))

    matched = []
    partial = []
    missing = []

    for req in req_skills:
        req_norm = req.strip().lower()
        found_prof = student_skills.get(req_norm)
        if found_prof is not None:
            if found_prof >= min_prof:
                matched.append({"skill": req, "proficiency": found_prof, "required": min_prof})
            else:
                partial.append({
                    "skill": req,
                    "proficiency": found_prof,
                    "required": min_prof,
                    "gap": round(min_prof - found_prof, 1),
                })
        else:
            missing.append({"skill": req, "proficiency": 0.0, "required": min_prof, "gap": min_prof})

    # Weighted match percentage
    total_weights = len(req_skills) * 1.0 + len(pref_skills) * 0.5
    earned_weights = 0.0
    for req in req_skills:
        p = student_skills.get(req.strip().lower(), 0.0)
        if p >= min_prof:
            earned_weights += 1.0
        elif p > 0:
            earned_weights += (p / min_prof)
    for pref in pref_skills:
        p = student_skills.get(pref.strip().lower(), 0.0)
        if p >= min_prof:
            earned_weights += 0.5
        elif p > 0:
            earned_weights += 0.5 * (p / min_prof)

    score_pct = round((earned_weights / total_weights) * 100) if total_weights > 0 else 0

    return {
        "job_id": job_data.get("job_id", ""),
        "job_title": job_data.get("title", "Unknown Role"),
        "company": job_data.get("company", "Unknown Organization"),
        "minimum_proficiency": min_prof,
        "matched_skills": matched,
        "partial_skills": partial,
        "missing_skills": missing,
        "match_percentage": score_pct,
    }


def _grounded_rule_advisor(
    user_message: str,
    student_profile: dict,
    skills_list: List[dict],
    learning_paths: List[dict],
    evidence_list: List[dict],
    job_analysis: Optional[Dict[str, Any]],
) -> str:
    """
    Deterministic Grounded Advisory Engine:
    Answers user queries strictly based on genuine Firestore data.
    Never invents, hallucinates, or estimates unrecorded skills.
    """
    msg_lower = user_message.lower().strip()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # 1. Strongest / Best Skills query
    if any(k in msg_lower for k in ["strongest", "best skill", "top skill", "highest"]):
        if not skills_list:
            return "Data unavailable: You do not currently have any recorded skills in your profile. Please add skills or take a skill assessment first."
        sorted_skills = sorted(skills_list, key=lambda s: float(s.get("proficiency", 0)), reverse=True)
        top3 = sorted_skills[:3]
        lines = [f"- **{s.get('name')}**: Proficiency Level {s.get('proficiency')}/5 ({s.get('proficiency_level', 'Proficient')})" for s in top3]
        return (
            f"Based on your verified profile, your strongest skills are:\n\n"
            + "\n".join(lines)
            + f"\n\nTotal skills recorded: {len(skills_list)}. Maintain these competencies with ongoing project evidence."
        )

    # 2. Submitted Evidence query
    if any(k in msg_lower for k in ["evidence", "certificate", "portfolio", "project submission"]):
        if not evidence_list:
            return "Data unavailable: You have not submitted any portfolio evidence or certificates yet. You can submit project repositories, certificates, or papers under the Portfolio tab."
        lines = []
        for e in evidence_list[:5]:
            status_tag = e.get("verification_status", "pending").capitalize()
            lines.append(f"- **{e.get('title')}** ({e.get('evidence_type')}): Status is **{status_tag}**")
        return (
            f"You have submitted {len(evidence_list)} evidence item(s):\n\n"
            + "\n".join(lines)
            + "\n\nVerified items have been reviewed by faculty mentors and contribute to your credible readiness score."
        )

    # 3. Learning Path query
    if any(k in msg_lower for k in ["learning path", "roadmap", "curriculum", "modules"]):
        if not learning_paths:
            return "Data unavailable: You do not currently have any active learning paths enrolled. You can generate or enroll in a targeted learning path from the Learning Path recommendations tab."
        lines = []
        for lp in learning_paths[:3]:
            pct = lp.get("completion_percentage", 0)
            status_lp = lp.get("status", "active")
            target = lp.get("target_role") or lp.get("title", "Skill Advancement")
            lines.append(f"- **{target}**: {pct}% complete ({status_lp})")
        return (
            f"Your current learning path status:\n\n"
            + "\n".join(lines)
            + "\n\nKeep progressing through the assigned milestones to close your competency gaps."
        )

    # 4. Job-specific or Match queries
    if job_analysis:
        title = job_analysis["job_title"]
        comp = job_analysis["company"]
        pct = job_analysis["match_percentage"]
        matched = job_analysis["matched_skills"]
        partial = job_analysis["partial_skills"]
        missing = job_analysis["missing_skills"]

        if any(k in msg_lower for k in ["missing", "what am i missing", "lack"]):
            if not missing and not partial:
                return f"Great news! For **{title}** at **{comp}**, you meet or exceed all required proficiencies (Match score: {pct}%)."
            lines = []
            for m in missing:
                lines.append(f"- **{m['skill']}**: Completely missing (Requires level {m['required']}/5)")
            for p in partial:
                lines.append(f"- **{p['skill']}**: Current level {p['proficiency']}/5 (Requires level {p['required']}/5, gap: {p['gap']})")
            return (
                f"Skill gaps identified for **{title}** at **{comp}** (Current match: {pct}%):\n\n"
                + "\n".join(lines)
                + "\n\nRecommendation: Enroll in targeted learning milestones for these specific competencies."
            )

        if any(k in msg_lower for k in ["improve first", "focus", "priority"]):
            if missing:
                top_priority = missing[0]["skill"]
                return (
                    f"For **{title}** at **{comp}**, your top priority to improve first is **{top_priority}** because it is a mandatory requirement that is currently missing from your profile. "
                    f"Acquiring level {missing[0]['required']}/5 proficiency in {top_priority} will yield the highest increase to your match score ({pct}%)."
                )
            elif partial:
                top_partial = partial[0]["skill"]
                return (
                    f"For **{title}** at **{comp}**, your primary focus should be upgrading **{top_partial}** from level {partial[0]['proficiency']} to {partial[0]['required']}. "
                    f"This will close your largest active gap ({partial[0]['gap']} points)."
                )
            return f"You meet all core requirements for **{title}** at **{comp}** ({pct}% match). Consider enhancing preferred skills to strengthen your application."

        if any(k in msg_lower for k in ["why", "low", "score"]):
            reasons = []
            if missing:
                reasons.append(f"{len(missing)} required skill(s) missing ({', '.join(m['skill'] for m in missing)})")
            if partial:
                reasons.append(f"{len(partial)} skill(s) below required threshold ({', '.join(p['skill'] for p in partial)})")
            if not reasons:
                reasons.append("Your skills match the core requirements well.")
            return (
                f"Your match score for **{title}** at **{comp}** is **{pct}%** because: "
                + "; ".join(reasons)
                + ". Closing the missing requirements will directly raise your score."
            )

    # 5. General Skill Gap / What to focus on
    if any(k in msg_lower for k in ["skill gap", "gap", "improve", "focus on next", "recommend"]):
        if not skills_list:
            return "Data unavailable: You haven't added any skills to your profile yet. Add your current competencies so I can analyze gaps against market demand."
        # Check if student has low proficiency skills
        low_skills = [s for s in skills_list if float(s.get("proficiency", 0)) < 3.0]
        if low_skills:
            focus = low_skills[0]["name"]
            prof = low_skills[0]["proficiency"]
            return (
                f"Based on your profile, you have {len(skills_list)} recorded skills. "
                f"Your lowest verified proficiency is **{focus}** (Level {prof}/5). "
                f"Focusing on raising {focus} to Level 3.0 (Intermediate) will immediately bolster your cross-industry readiness."
            )
        return (
            f"You have {len(skills_list)} recorded skills with solid baseline proficiencies (all >= 3.0). "
            "To progress further, select a target job opportunity or generate a learning path to identify advanced domain-specific competencies."
        )

    # Default overview
    skills_count = len(skills_list)
    lp_count = len(learning_paths)
    ev_count = len(evidence_list)
    return (
        f"Hello {student_profile.get('name', 'Student')}! I am your AI Career Assistant. "
        f"Your current profile status:\n"
        f"- **Recorded Skills**: {skills_count}\n"
        f"- **Active Learning Paths**: {lp_count}\n"
        f"- **Submitted Evidence**: {ev_count}\n\n"
        "You can ask me questions like:\n"
        "- *'Which of my skills are strongest?'*\n"
        "- *'What evidence have I submitted?'*\n"
        "- *'What should I focus on next?'*\n"
        "- *'What skills am I missing for this job?'* (with job selected)"
    )


@router.post("/chat", response_model=AIChatResponse, summary="Chat with AI Career Assistant")
async def chat_with_assistant(
    request: AIChatRequest,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    POST /api/ai/chat
    Secure advisory chat grounded strictly in real student Firestore data.
    Derived student identity from verified Firebase ID token.
    Advisory only: Never mutates student or platform records.
    """
    db = get_db()
    uid = current_user.uid

    # 1. Fetch real student skills
    skills_docs = db.collection("users").document(uid).collection("skills").stream()
    skills_list = []
    skills_dict = {}
    for doc in skills_docs:
        d = doc.to_dict() or {}
        name = d.get("name", "")
        prof = float(d.get("proficiency", 1.0))
        skills_list.append({
            "name": name,
            "proficiency": prof,
            "proficiency_level": d.get("level", "Intermediate"),
            "category": d.get("category", "Technical"),
            "verified": d.get("verified", False),
        })
        if name:
            skills_dict[name.strip().lower()] = prof

    # 2. Fetch real learning paths
    lp_docs = db.collection("users").document(uid).collection("learning_paths").stream()
    learning_paths = [d.to_dict() or {} for d in lp_docs]

    # 3. Fetch real evidence
    ev_docs = db.collection("users").document(uid).collection("evidence").stream()
    evidence_list = [d.to_dict() or {} for d in ev_docs]

    # 4. If job_id provided, fetch real job
    job_analysis = None
    if request.job_id:
        job_doc = db.collection("jobs").document(request.job_id).get()
        if job_doc.exists:
            job_analysis = _calculate_grounded_job_gap(skills_dict, job_doc.to_dict() or {})

    # 5. Check if optional GEMINI_API_KEY is available in environment
    gemini_key = os.getenv("GEMINI_API_KEY")
    reply_text = ""
    provider_used = "grounded_rule_engine"

    if gemini_key:
        try:
            # We can use Google GenAI SDK or Gemini REST API if key is valid
            from google import genai
            client = genai.Client(api_key=gemini_key)

            context_prompt = f"""You are the AcademiaLINK AI Career Advisor.
Student: {current_user.name}
Recorded Skills: {skills_list}
Learning Paths: {learning_paths}
Evidence: {evidence_list}
Job Context: {job_analysis if job_analysis else 'None specified'}

CRITICAL INSTRUCTIONS:
- You must ONLY use the real facts provided above.
- NEVER invent, hallucinate, or assume unrecorded skills, jobs, or evidence.
- If data is not present in the context, explicitly inform the student that data is unavailable.
- Answer the student's question clearly and actionably: {request.message}
"""
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=context_prompt,
            )
            if response and response.text:
                reply_text = response.text
                provider_used = "gemini"
        except Exception as e:
            logger.warning("Gemini API call failed (%s); falling back to grounded rule engine.", e)

    # If no LLM configured or call failed, use our deterministic grounded engine
    if not reply_text:
        reply_text = _grounded_rule_advisor(
            user_message=request.message,
            student_profile=current_user.model_dump(),
            skills_list=skills_list,
            learning_paths=learning_paths,
            evidence_list=evidence_list,
            job_analysis=job_analysis,
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    return AIChatResponse(
        reply=reply_text,
        grounded_data={
            "skills_count": len(skills_list),
            "learning_paths_count": len(learning_paths),
            "evidence_count": len(evidence_list),
            "job_analyzed": job_analysis["job_title"] if job_analysis else None,
            "job_match_score": job_analysis["match_percentage"] if job_analysis else None,
        },
        timestamp=now_iso,
        provider=provider_used,
        data_available=bool(skills_list or learning_paths or evidence_list or job_analysis),
        provenance=DataProvenance(
            source="academialink_grounded_advisor",
            data_status="available" if (skills_list or learning_paths or evidence_list) else "unavailable",
            retrieved_at=now_iso,
            is_test_data=False,
        ),
    )
