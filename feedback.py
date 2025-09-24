import streamlit as st

# --- Helper function for Core Impact & Experience ---
def provide_core_impact_feedback(score_data, job_profile):
    st.markdown("### ⭐ Core Impact & Experience")
    core_score = score_data.get("core_impact_score", 0)
    core_breakdown = score_data.get("breakdown", {}).get('core_impact_and_experience', {})
    quant_achievements = core_breakdown.get('quantifiable_achievements', {}).get('quantifiable_achievements', [])
    total_exp_details = core_breakdown.get('total_experience', {})

    st.progress(core_score / 45.0)

    if core_score >= 35:
        st.success(f"**Score: {core_score}/45 (Excellent)**")
        st.write("Your resume excels at showing tangible impact. Recruiters can immediately see the value you've delivered through well-quantified achievements and relevant experience. This is what top-tier resumes look like.")
    elif core_score >= 25:
        st.info(f"**Score: {core_score}/45 (Good)**")
        st.write("You have a solid experience section. To elevate it to the next level, focus on adding more specific metrics to every bullet point. Instead of 'Improved system performance,' try 'Improved system performance by 15% by implementing a new caching strategy.'")
    else:
        st.warning(f"**Score: {core_score}/45 (Needs Improvement)**")
        st.write("This is the most critical area to focus on. Your resume needs to more clearly demonstrate the *impact* of your work. Every bullet point in your experience section should ideally start with a strong action verb and include a number, percentage, or dollar amount.")

    st.markdown(f"**- Quantifiable Achievements Found:** `{len(quant_achievements)}` impactful statements detected.")
    if not total_exp_details.get('total_relevant_experience', False):
         st.markdown(f"**- Experience Requirement:** Your resume does not currently meet the minimum experience of `{job_profile.get('min_experience', 0)}` years. Focus on highlighting transferable skills and project work.")


# --- Helper function for Skill & Technology Alignment ---
def provide_skill_alignment_feedback(score_data, job_profile):
    st.markdown("### 🛠️ Skill & Technology Alignment")
    skill_score = score_data.get("skill_alignment_score", 0)
    skill_breakdown = score_data.get("breakdown", {}).get('skill_and_tech_alignment', {})
    required_found = set(skill_breakdown.get('skill_usage', []))
    required_total = set(job_profile.get('required_skills', []))
    missing_skills = required_total - required_found

    st.progress(skill_score / 25.0)

    if skill_score >= 20:
        st.success(f"**Score: {skill_score}/25 (Excellent)**")
        st.write("Your skills are a fantastic match for this role. You've not only listed the right technologies but also shown how you've used them in your work history and projects.")
    elif skill_score >= 15:
        st.info(f"**Score: {skill_score}/25 (Good)**")
        st.write("You have a strong set of relevant skills. To improve, make sure your most critical skills (like those in the 'Required Skills' list) are mentioned directly in your experience or project bullet points, not just in a general skills list.")
    else:
        st.warning(f"**Score: {skill_score}/25 (Needs Improvement)**")
        st.write("Your resume needs to be more closely tailored to the skills required for this specific job. Carefully review the job description and ensure every required skill you possess is explicitly mentioned.")

    if missing_skills:
        st.markdown("**Priority Action:** Add the following required skills if you have experience with them:")
        for skill in list(missing_skills)[:3]:
            st.markdown(f"- `{skill}`")

# --- Helper function for Projects & Supporting Evidence ---
def provide_projects_evidence_feedback(score_data):
    st.markdown("### 📂 Projects & Supporting Evidence")
    evidence_score = score_data.get("projects_and_evidence_score", 0)
    evidence_breakdown = score_data.get("breakdown", {}).get('projects_and_evidence', {})
    online_presence = evidence_breakdown.get('online_presence', {})

    st.progress(evidence_score / 15.0)

    if evidence_score >= 12:
        st.success(f"**Score: {evidence_score}/15 (Excellent)**")
        st.write("You do a great job of building trust and demonstrating your skills through high-quality projects and a professional online presence. This shows passion and initiative beyond just a job title.")
    else:
        st.warning(f"**Score: {evidence_score}/15 (Needs Improvement)**")
        st.write("This section is your chance to prove your skills. Strengthen it by adding a dedicated 'Projects' section. For each project, include a link (GitHub/live demo), the technologies used, and a clear, quantified description of what you built and achieved.")

    if not online_presence.get('linkedin') or not online_presence.get('github'):
        st.markdown("**Quick Win:** Add links to your LinkedIn and GitHub profiles in your contact information section. It's a standard practice that recruiters expect.")

# --- Helper function for Professional Presentation ---
def provide_presentation_feedback(score_data):
    st.markdown("### 📄 Professional Presentation")
    presentation_score = score_data.get("professional_presentation_score", 0)
    presentation_breakdown = score_data.get("breakdown", {}).get('professional_presentation', {})
    word_count = presentation_breakdown.get('word_count', 0)
    errors = presentation_breakdown.get('grammar_errors', 0)

    st.progress(presentation_score / 15.0)

    if presentation_score >= 12:
        st.success(f"**Score: {presentation_score}/15 (Excellent)**")
        st.write("Your resume is clean, professional, and easy for a recruiter to scan. This makes a great first impression.")
    else:
        st.warning(f"**Score: {presentation_score}/15 (Needs Improvement)**")
        st.write("The presentation of your resume needs polish. Small details matter and signal professionalism. Focus on consistency in formatting and proofread multiple times to eliminate all errors.")

    if isinstance(errors, int) and errors > 0:
        st.markdown(f"**- Proofreading:** `{errors}` grammar or spelling issues were found. Use a tool like Grammarly to find and fix them.")
    if word_count > 600:
         st.markdown(f"**- Conciseness:** Your resume is `{word_count}` words long. Aim for under 600 words to ensure it's a quick and impactful read for a busy recruiter.")

# --- Master Feedback Function ---
def provide_comprehensive_feedback(score_data: dict, job_profile: dict):
    """
    The main orchestrator that calls the individual feedback modules to build a full report.
    """
    provide_core_impact_feedback(score_data, job_profile)
    st.markdown("---")
    provide_skill_alignment_feedback(score_data, job_profile)
    st.markdown("---")
    provide_projects_evidence_feedback(score_data)
    st.markdown("---")
    provide_presentation_feedback(score_data)