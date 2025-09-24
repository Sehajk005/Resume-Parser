import streamlit as st
import tempfile
import shutil
import os
from parser import extract_text, parse_resume
from new_scoring import score_resume
from feedback import provide_comprehensive_feedback
from utils import load_job_profiles

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Intelligent Resume Parser", layout="wide", page_icon="🚀")

# --- LOAD RESOURCES ---
try:
    job_profiles = load_job_profiles()
except FileNotFoundError as e:
    st.error(f"Fatal Error: {e}. Please make sure 'job_profile.json' and 'skills.json' are in the same directory.")
    st.stop()
except Exception as e:
    st.error(f"An error occurred while loading resources: {e}")
    st.stop()

# --- HEADER ---
st.title("🚀 Intelligent Resume Parser")
st.markdown("AI-powered resume analysis for recruiters and job seekers, built with a modern, evidence-based scoring engine.")
st.markdown("---")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Navigation")
    user_type = st.radio("Select Your Role:", ["HR / Recruiter", "Job Seeker"], key="user_role")
    
    st.markdown("---")
    st.header("Available Role Archetypes")
    for category, roles in job_profiles.items():
        st.markdown(f"**{category}**: {len(roles)} roles")

# --- MAIN APP LOGIC ---

# 1. HR / Recruiter Flow
if user_type == "HR / Recruiter":
    st.header("Advanced Candidate Evaluation System")
    
    col1, col2 = st.columns(2)
    with col1:
        job_level = st.selectbox("Select Candidate Level", list(job_profiles.keys()), key="hr_job_level")
    with col2:
        job_roles = list(job_profiles.get(job_level, {}).keys())
        job_category = st.selectbox("Select Job Role", job_roles, key="hr_job_role")
    
    selected_profile = job_profiles.get(job_level, {}).get(job_category)
    
    if selected_profile:
        with st.expander(f"View Requirements for {job_category}"):
            st.markdown(f"**Title:** {selected_profile.get('title', 'N/A')}")
            st.markdown(f"**Minimum Experience:** {selected_profile.get('min_experience', 0)} years")
            req_col, pref_col = st.columns(2)
            req_col.markdown("**Required Skills:**\n" + "\n".join([f"- {s}" for s in selected_profile.get("required_skills", [])]))
            pref_col.markdown("**Preferred Skills:**\n" + "\n".join([f"- {s}" for s in selected_profile.get("preferred_skills", [])]))

    uploaded_files = st.file_uploader(
        "Upload Candidate Resumes",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        help="Upload multiple resumes for batch processing and ranking."
    )
    
    if st.button("🔍 Evaluate Resumes", type="primary") and uploaded_files:
        if not selected_profile:
            st.error("Please select a valid job role before evaluating.")
        else:
            progress_bar = st.progress(0, text="Initializing evaluation...")
            results = []
            
            for i, resume_file in enumerate(uploaded_files):
                progress_bar.progress((i + 1) / len(uploaded_files), text=f"Processing {resume_file.name}...")
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(resume_file.name)[1]) as tmp:
                    shutil.copyfileobj(resume_file, tmp)
                    tmp_path = tmp.name
                
                try:
                    raw_text = extract_text(tmp_path)
                    parsed_data = parse_resume(raw_text)
                    score_data = score_resume(parsed_data, selected_profile)
                    results.append({"name": resume_file.name, "score": score_data["total_score"], "details": score_data})
                except Exception as e:
                    st.warning(f"Could not process {resume_file.name}. Error: {e}")
                finally:
                    os.unlink(tmp_path)
            
            progress_bar.empty()
            
            if results:
                st.success(f"Evaluation complete! Processed {len(results)} resumes.")
                sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
                
                for rank, result in enumerate(sorted_results, 1):
                    with st.expander(f"#{rank}: **{result['name']}** — Score: {result['score']}/100", expanded=(rank <= 3)):
                        st.subheader("Score Breakdown")
                        score_details = result['details']
                        cols = st.columns(4)
                        cols[0].metric("Core Impact & Experience", f"{score_details['core_impact_score']}/45")
                        cols[1].metric("Skill Alignment", f"{score_details['skill_alignment_score']}/25")
                        cols[2].metric("Projects & Evidence", f"{score_details['projects_and_evidence_score']}/15")
                        cols[3].metric("Presentation", f"{score_details['professional_presentation_score']}/15")

                        with st.container():
                            st.subheader("Parsed Information")
                            st.json(score_details['parsed_data'], expanded=False)

# 2. Job Seeker Flow
elif user_type == "Job Seeker":
    st.header("Personal Resume Optimizer")

    col1, col2 = st.columns(2)
    with col1:
        job_level = st.selectbox("Select Your Experience Level", list(job_profiles.keys()), key="seeker_job_level")
    with col2:
        job_roles = list(job_profiles.get(job_level, {}).keys())
        job_category = st.selectbox("Select Your Target Job Role", job_roles, key="seeker_job_role")
        
    selected_profile = job_profiles.get(job_level, {}).get(job_category)
    
    uploaded_file = st.file_uploader(
        "Upload Your Resume",
        type=["pdf", "docx"],
        help="Upload your resume to get an AI-powered analysis and score."
    )

    if st.button("🚀 Analyze My Resume", type="primary") and uploaded_file:
        if not selected_profile:
            st.error("Please select a valid job role before analyzing.")
        else:
            with st.spinner("Our AI is reviewing your resume... This may take a moment."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                    shutil.copyfileobj(uploaded_file, tmp)
                    tmp_path = tmp.name
                
                try:
                    raw_text = extract_text(tmp_path)
                    parsed_data = parse_resume(raw_text)
                    score_data = score_resume(parsed_data, selected_profile)
                    
                    # --- Display Results ---
                    score = score_data['total_score']
                    st.markdown("### Your Resume Score")
                    
                    if score >= 80:
                        st.success(f"**Excellent Fit! Your score is {score}/100**")
                    elif score >= 65:
                        st.info(f"**Good Fit! Your score is {score}/100**")
                    else:
                        st.warning(f"**Needs Improvement. Your score is {score}/100**")

                    # Generate and display the detailed, AI-powered feedback
                    provide_comprehensive_feedback(score_data, selected_profile)

                except Exception as e:
                    st.error(f"An error occurred during analysis: {e}")
                finally:
                    os.unlink(tmp_path)


