import re
import dateutil.parser
from dateutil.relativedelta import relativedelta
import nltk
nltk.download('wordnet')
from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()
nltk.download('punkt_tab')
from nltk.tokenize import word_tokenize
from difflib import SequenceMatcher
from datetime import datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

def score_resume(resume_data, job_profile):
    """
    The main, top-level function that orchestrates the entire resume scoring process,
    and returns a comprehensive dictionary with the final score, detailed breakdowns,
    and individual category scores.
    """
    final_score = 0
    final_breakdown = {}

    # 1. Score Core Impact & Experience (Alignment, Recency, etc.)
    core_impact_score, core_impact_breakdown = score_alignment(resume_data, job_profile)
    final_score += core_impact_score
    final_breakdown['core_impact_and_experience'] = core_impact_breakdown

    # 2. Score Skill & Technology Alignment
    skill_score, skill_breakdown = score_skill_alignment(resume_data, job_profile)
    final_score += skill_score
    final_breakdown['skill_and_tech_alignment'] = skill_breakdown

    # 3. Score Project & Supporting Evidence
    evidence_score, evidence_breakdown = score_projects_and_evidence(resume_data, job_profile)
    final_score += evidence_score
    final_breakdown['projects_and_evidence'] = evidence_breakdown

    # 4. Score Professional Presentation
    presentation_score, presentation_breakdown = score_professional_presentation(resume_data, job_profile)
    final_score += presentation_score
    final_breakdown['professional_presentation'] = presentation_breakdown

    # Construct the final, detailed dictionary exactly as you wanted
    return {
        "total_score": round(final_score),
        "breakdown": final_breakdown,
        "parsed_data": resume_data,
        "core_impact_score": core_impact_score,
        "skill_alignment_score": skill_score,
        "projects_and_evidence_score": evidence_score,
        "professional_presentation_score": presentation_score
    }




action_verbs = {
    # Leadership & Management
    'accelerated', 'administered', 'advanced', 'advised', 'advocated', 'appointed',
    'approved', 'assigned', 'authorized', 'chaired', 'coached', 'commanded',
    'consolidated', 'controlled', 'coordinated', 'cultivated', 'decided', 'delegated',
    'developed', 'directed', 'drove', 'enabled', 'established', 'executed',
    'facilitated', 'founded', 'guided', 'headed', 'influenced', 'initiated',
    'inspired', 'launched', 'led', 'managed', 'motivated', 'orchestrated',
    'organized', 'oversaw', 'pioneered', 'presided', 'prioritized', 'regulated',
    'spearheaded', 'steered', 'strategized', 'supervised', 'transformed',
    
    # Achievement & Results
    'accelerated', 'accomplished', 'achieved', 'advanced', 'amplified', 'attained',
    'boosted', 'delivered', 'demonstrated', 'doubled', 'earned', 'elevated',
    'enhanced', 'exceeded', 'expanded', 'expedited', 'generated', 'improved',
    'increased', 'maximized', 'optimized', 'outperformed', 'progressed',
    'realized', 'reduced', 'strengthened', 'succeeded', 'surpassed', 'tripled',
    'won', 'yielded',
    
    # Technical & Analysis
    'analyzed', 'assessed', 'audited', 'calculated', 'calibrated', 'compiled',
    'computed', 'configured', 'debugged', 'designed', 'detected', 'diagnosed',
    'engineered', 'evaluated', 'examined', 'experimented', 'identified',
    'implemented', 'integrated', 'investigated', 'mapped', 'measured',
    'modeled', 'monitored', 'programmed', 'researched', 'solved', 'tested',
    'troubleshot', 'upgraded', 'validated', 'verified',
    
    # Communication & Collaboration
    'articulated', 'authored', 'collaborated', 'communicated', 'consulted',
    'corresponded', 'counseled', 'debated', 'demonstrated', 'documented',
    'edited', 'explained', 'expressed', 'facilitated', 'influenced',
    'interpreted', 'interviewed', 'lectured', 'mediated', 'negotiated',
    'networked', 'persuaded', 'presented', 'promoted', 'publicized',
    'published', 'recommended', 'reported', 'represented', 'solicited',
    'spoke', 'translated', 'wrote',
    
    # Creative & Innovation
    'adapted', 'brainstormed', 'conceptualized', 'created', 'customized',
    'designed', 'developed', 'devised', 'enacted', 'fashioned', 'formulated',
    'founded', 'illustrated', 'imagined', 'implemented', 'improvised',
    'innovated', 'inspired', 'instituted', 'introduced', 'invented',
    'originated', 'performed', 'planned', 'produced', 'redesigned',
    'revamped', 'revitalized', 'shaped', 'visualized',
    
    # Organization & Detail
    'allocated', 'arranged', 'assembled', 'budgeted', 'catalogued', 'categorized',
    'classified', 'collected', 'compiled', 'completed', 'coordinated',
    'corrected', 'dispersed', 'distributed', 'executed', 'filed', 'implemented',
    'inspected', 'logged', 'maintained', 'monitored', 'operated', 'ordered',
    'organized', 'prepared', 'processed', 'purchased', 'recorded', 'registered',
    'reserved', 'responded', 'reviewed', 'routed', 'scheduled', 'screened',
    'submitted', 'supplied', 'systematized', 'tabulated', 'updated', 'verified'
}   
# qualifications achievements 
achievement_verbs = [
    "accelerated", "boosted", "cut", "drove", "enhanced", "exceeded", "generated",
    "optimized", "streamlined", "transformed", "led", "initiated", "launched",
    "executed", "revamped", "overhauled", "achieved", "surpassed", "secured",
    "managed", "mentored", "solved", "won", "closed", "built", "automated"
]
recognitions = ["awarded", "recognized", "certified", "nominated", "winner", "top performer", 
                    "appreciated", "honored", "commendation", "employee of the month", "ranked"]

metric_patterns = [
    r'\d+%',  # Percentages
    r'\$\d+(?:,\d{3})*(?:\.\d{2})?[kmb]?',  # Money amounts
    r'\d+(?:,\d{3})*\s*(?:k|K|million|M|billion|B|crore|lakh|thousand)',  # Large numbers
    r'\d+\+?\s*(?:users?|clients?|customers?|people|employees|team members?)',  # People metrics
    r'\d+\+?\s*(?:projects?|products?|campaigns?|leads?|deals?|sales?)',  # Work metrics
    r'(?:increased?|improved?|enhanced?|boosted?|grew?|raised?)\s+(?:by\s+)?\d+%',  # Performance increases
    r'(?:reduced?|decreased?|cut|lowered?|saved?)\s+(?:by\s+)?\d+%',  # Performance reductions
    r'(?:reduced?|cut|saved?)\s+\$?\d+',  # Cost savings
    r'\d+x\s+(?:faster|improvement|increase|growth)',  # Multiplier improvements
    r'(?:managed?|oversaw|led)\s+\$?\d+(?:,\d{3})*(?:[kmb]|\s+(?:million|thousand))?',  # Budget management
    r'(?:within|under|ahead of)\s+(?:budget|schedule|timeline)',  # Efficiency metrics
    r'(?:exceeded?|surpassed?|outperformed?)\s+(?:target|goal|quota|benchmark)',  # Goal achievement
]

lemmatized_action_verbs = {lemmatizer.lemmatize(v, pos='v') for v in action_verbs}
lemmatized_achievement_verbs = {lemmatizer.lemmatize(v, pos='v') for v in achievement_verbs}
lemmatized_recognitions = {lemmatizer.lemmatize(v, pos='v') for v in recognitions}

# function to score alignment
def score_alignment(resume_data, job_profile):
    """
    This is the main orchestrator function. It calls all the individual
    scoring functions and combines their results.
    """
    total_alignment_score = 0
    alignment_breakdown = {}

    # 1. Score Quantifiable Achievements
    quant_score, quant_breakdown = score_quantifiable_achievements(resume_data, job_profile)
    total_alignment_score += quant_score
    alignment_breakdown['quantifiable_achievements'] = quant_breakdown

    # 2. Score Experience Relevance (Fresher vs. Experienced)
    #    (Assuming you make the small change to its return value)
    relevance_score, relevance_breakdown = score_experience_relevance(resume_data, job_profile)
    total_alignment_score += relevance_score
    alignment_breakdown['experience_relevance'] = relevance_breakdown

    # 3. Score Recency
    recency_score, recency_breakdown = score_recency(resume_data)
    total_alignment_score += recency_score
    alignment_breakdown['recency'] = recency_breakdown

    # 4. Score Total Years of Experience
    exp_score, exp_breakdown = score_total_experience(resume_data, job_profile)
    total_alignment_score += exp_score
    alignment_breakdown['total_experience'] = exp_breakdown

    # Return the combined results
    return total_alignment_score, alignment_breakdown


# function to score total experience
def score_total_experience(resume_data, job_profile):
    exp_score = 0
    exp_breakdown = {
        "total_relevant_experience": False
    }
    text = "\n".join(sum(resume_data.values(), []))
    date_range_pattern = re.findall(
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*(?:–|-|to)\s*(?:Present|(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})",
        text,
        re.IGNORECASE
    )

    total_months = 0
    for match in re.finditer(
        r"((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\s*(–|-|to)\s*((Present)|(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})",
        text,
        re.IGNORECASE,
    ):
        try:
            start_str = match.group(1)
            end_str = match.group(4)

            start = dateutil.parser.parse(start_str)
            end = dateutil.parser.parse("today") if "present" in end_str.lower() else dateutil.parser.parse(end_str)

            delta = relativedelta(end, start)
            total_months += delta.years * 12 + delta.months
        except:
            continue

    # Convert months to years
    total_years = round(total_months / 12, 1)
    min_exp = job_profile.get("min_experience", 0)

    if total_years >= min_exp:
        exp_breakdown["total_relevant_experience"] = True
        exp_score += 10

    return exp_score, exp_breakdown
    
    
# function to score quantifiable achievements
def score_quantifiable_achievements(resume_data, job_profile):
    quant_achievements_score = 0
    quant_breakdown = {
        "quantifiable_achievements": []
    }
    
    text = "\n".join(sum(resume_data.values(), [])) # join all values of resume_data into a single string
    lines = text.split("\n")
    achievement_lines = []
    for line in lines:
        clean_line = re.sub(r'[^\w\s]', '', line).lower()
        clean_line_tokenized = word_tokenize(clean_line)
        clean_line_lemmatized = [lemmatizer.lemmatize(word) for word in clean_line_tokenized]
        words_in_line = set(clean_line_lemmatized)
        metric_found = any(re.search(pattern, line) for pattern in metric_patterns)
        if not words_in_line.isdisjoint(lemmatized_action_verbs) and not words_in_line.isdisjoint(lemmatized_achievement_verbs) and metric_found and not words_in_line.isdisjoint(lemmatized_recognitions):
            quant_achievements_score += 20
            achievement_lines.append(line)
        elif not words_in_line.isdisjoint(lemmatized_action_verbs) and not words_in_line.isdisjoint(lemmatized_achievement_verbs) and metric_found:
            quant_achievements_score += 18
            achievement_lines.append(line)
        elif not words_in_line.isdisjoint(lemmatized_action_verbs) and not words_in_line.isdisjoint(lemmatized_achievement_verbs):
            quant_achievements_score += 15
            achievement_lines.append(line)
        elif not words_in_line.isdisjoint(lemmatized_achievement_verbs) and metric_found:
            quant_achievements_score += 12
            achievement_lines.append(line)
        elif not words_in_line.isdisjoint(lemmatized_action_verbs) and metric_found:
            quant_achievements_score += 10
            achievement_lines.append(line)
        elif not words_in_line.isdisjoint(lemmatized_action_verbs):
            quant_achievements_score += 5
            achievement_lines.append(line)
        elif not words_in_line.isdisjoint(lemmatized_achievement_verbs):
            quant_achievements_score += 7
            achievement_lines.append(line)
        elif metric_found:
            quant_achievements_score += 3
            achievement_lines.append(line)
    quant_breakdown["quantifiable_achievements"] = achievement_lines
    return quant_achievements_score, quant_breakdown
    
    
# function to score experience relevance
def score_experience_relevance(resume_data, job_profile):
    relevence_score = 0
    relevence_breakdown = {
        "exp_relevence": False
    }
    if resume_data.get("experience") or resume_data.get("work_experience") != []:
        target_job = job_profile.get("title")
        exp_list1 = resume_data.get("work_experience", []) # Defaults to [] if key is missing
        exp_list2 = resume_data.get("experience", [])
        text = "\n".join(exp_list1 + exp_list2)
        best_score = 0
        for line in text.split("\n"):
            current_score = (SequenceMatcher(None, line.lower(), target_job.lower()).ratio())*10
            if current_score > best_score:
                best_score = current_score
    else:
        exp_list1 = resume_data.get("projects", [])
        exp_list2 = resume_data.get("achievements", [])
        text = "\n".join(exp_list1 + exp_list2)
        keywords = job_profile.get("keywords", []) +job_profile.get("required_skills", [])
        matched_keywords = {kw for kw in keywords if kw.lower() in text.lower()}
        best_score = min(len(matched_keywords) * 2, 10)
    exp_relevence_score = best_score
    relevence_breakdown["exp_relevence"] = True
    return relevence_score, relevence_breakdown


# function to score recency
def score_recency(resume_data):
    recency_score = 0
    recency_breakdown = {
        "recency": []
    }
    text = "\n".join(sum(resume_data.values(), []))
    today = datetime.now()
    date_ranges = re.findall(
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\s*[-–to]+\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|Present|Current)",
        text,
        re.IGNORECASE
    )

    if not date_ranges:
        recency_score = 0 # No dates found, low score.

    # 3. Extract all the end dates from the matches.
    end_dates_str = [match[1] for match in date_ranges]

    # 4. Check for the "Present" keyword. If it exists, the resume is current.
    if any("present" in s.lower() or "current" in s.lower() for s in end_dates_str):
        recency_score += 5 # Full points for being currently employed.
        return recency_score, recency_breakdown

    # 5. If not "Present", parse the date strings into date objects.
    end_dates = [parse(s) for s in end_dates_str]

    # 6. Find the most recent (latest) date from the list.
    latest_end_date = max(end_dates)

    # 7. Calculate the gap between today and the last job.
    gap = relativedelta(today, latest_end_date)
    gap_in_years = gap.years + (gap.months / 12.0)

    # 8. Return a score based on the size of the gap.
    if gap_in_years <= 1:
        recency_score += 5 # Excellent (less than 1-year gap)
    elif gap_in_years <= 3:
        recency_score += 3 # Okay (1 to 3-year gap)
    else:
        recency_score += 1 # Concerning (more than 3-year gap)

    recency_breakdown["recency"] = end_dates_str
    return recency_score, recency_breakdown

# function to score skill and technology alignment
def score_skill_alignment(resume_data, job_profile):

    skill_alignment_score = 0
    skill_alignment_breakdown = {
        "skill_usage": [],
        "preferred_skills": [],
        "keywords": [],
    }
    text = "\n".join(sum(resume_data.values(), [])).lower()
    exp_text = " ".join(resume_data.get("work_experience", []) + resume_data.get("experience", []))
    project_text = " ".join(resume_data.get("projects", []))
    content_text = (exp_text + " " + project_text).lower()
    
    skill_text = " ".join(resume_data.get("skills", [])).lower()
    
    all_text = content_text + " " + skill_text
    
    # for fair scoring 
    master_found_skills = set() # set used to prevent duplication
    
    # The Doormen's separate clipboards (for the breakdown)
    required_found = set()
    preferred_found = set()
    keywords_found = set()
    
    required_skills = job_profile.get("required_skills", [])
    skill_score = 0 
    
    for skill in required_skills:
        if skill.lower() in content_text and skill.lower() not in master_found_skills:
            skill_score += 2
            master_found_skills.add(skill.lower())
            required_found.add(skill.lower())
        elif skill.lower() in skill_text and skill.lower() not in master_found_skills:
            skill_score += 1
            master_found_skills.add(skill.lower())
            required_found.add(skill.lower())
    total_skill_score = min(skill_score, 15)
            
    skill_alignment_breakdown["skill_usage"] = list(required_found)
    skill_alignment_score += total_skill_score
    
    preferred_skills = job_profile.get("preferred_skills", [])
    preferred_skill_score = 0
    
    for skill in preferred_skills:
        if skill.lower() in all_text and skill.lower() not in master_found_skills:
            preferred_skill_score += 1
            master_found_skills.add(skill.lower())
            preferred_found.add(skill.lower())
    total_preferred_skill_score = min(preferred_skill_score, 5)
    skill_alignment_breakdown["preferred_skills"] = list(preferred_found)
    skill_alignment_score += total_preferred_skill_score
          
    keywords = job_profile.get("keywords", []) + job_profile.get("job_specific_keywords", [])
    keyword_score = 0
    
    for keyword in keywords:
        if keyword.lower() in text and keyword.lower() not in master_found_skills:
            keyword_score += 1
            master_found_skills.add(keyword.lower())
            keywords_found.add(keyword.lower())
    total_keyword_score = min(keyword_score, 10)
    skill_alignment_breakdown["keywords"] = list(keywords_found)
    skill_alignment_score += total_keyword_score
    
    return skill_alignment_score, skill_alignment_breakdown
    

def score_projects_and_evidence (resume_data, job_profile):
    content_score = 0
    content_breakdown = {
        "online_presence": [],
        "education_certificates": [],
        "projects": []
    }
    
   

    all_text = "\n".join(sum(resume_data.values(), [])).lower()
    # Online Presence  
    online_presence_score = 0
    found_links = {}

    # Check for a LinkedIn profile
    if re.search(r"linkedin\.com/in/[\w-]+", all_text):
        online_presence_score += 1
        found_links['linkedin'] = True

    # Check for a GitHub profile (often worth more)
    if re.search(r"github\.com/[\w-]+", all_text):
        online_presence_score += 1
        found_links['github'] = True

    # Bonus point for showing GitHub is actively used
    if all_text.count("github.com") > 1:
        online_presence_score += 1

    # Cap the score for this section at its max value
    final_online_score = min(online_presence_score, 3)

    content_breakdown["online_presence"] = found_links
    content_score += final_online_score
    
    # Education and Certificates
    edu_text = " ".join(resume_data.get("education", [])).lower()
    cert_text = " ".join(resume_data.get("certifications", [])).lower()
    edu_cert_score = 0
    found_edu = False
    found_cert = False
    keword = job_profile.get("edu_keywords", [])
    cert = job_profile.get("relevant_certs", [])
    for edu in keword:
        if edu.lower() in edu_text:
            edu_cert_score += 1
            found_edu = True
    
    for certi in cert:
        if certi.lower() in cert_text:
            edu_cert_score += 1
            found_cert = True
    final_edu_cert_score = min(edu_cert_score, 5)
    content_breakdown["education_certificates"] = [found_edu, found_cert]
    content_score += final_edu_cert_score
    
    # projects
    projects_list = resume_data.get("projects", [])
    project_score = 0
    analyzed_projects = [] # For the breakdown

    
    for project in projects_list:
        quality_points = 0
        project_analysis = {"description": project[:50] + "..."} # Save a snippet for the report

        # 1. Check for a link
        if re.search(r"http[s]?://", project.lower()) or ("github" in project.lower() or "live app" in project.lower()):
            quality_points += 1
            project_analysis['has_link'] = True

        # 2. Check for a tech stack
        if "technologies" in project.lower() or "built with" in project.lower() or "skills_applied" in project.lower():
            quality_points += 1
            project_analysis['has_tech_stack'] = True

        # 3. Check for an outcome verb (using our old achievement_verbs list)
        if any(verb in project.lower() for verb in achievement_verbs + action_verbs):
            quality_points += 1
            project_analysis['has_outcome_verb'] = True

        # If a project is well-described (2 or 3 quality points), award a score
        if quality_points >= 2:
            project_score += 3 # Give 3 points for each high-quality project

        analyzed_projects.append(project_analysis)

    # Cap the total project score and add it to the main score
    final_project_score = min(project_score, 7)
    content_score += final_project_score
    content_breakdown["projects"] = analyzed_projects

    return content_score, content_breakdown
    
import requests
def grammar_check(text):
    url = "https://api.languagetool.org/v2/check"
    data = {
        'text': text[:2000],  # limit text length
        'language': 'en-US'
    }
    try:
        response = requests.post(url, data=data)
        result = response.json()
        matches = result.get("matches", [])
        return len(matches)
    except Exception as e:
        print("Grammar API failed:", e)
        return None
    
# Function to score professional presentation
def score_professional_presentation(resume_data, job_profile):
    """
    Scores the overall professionalism of the resume based on its formatting,
    clarity, conciseness, and grammar.
    """
    presentation_score = 0
    presentation_breakdown = {}
    
    
    all_raw_text = "\n".join(sum(resume_data.values(), []))

    # --- 1. Clarity & Readability (Max 5 points) ---
    clarity_score = 0
    # Check for bullet points
    if re.search(r"^\s*[–•●*-]\s+", all_raw_text, re.MULTILINE):
        clarity_score += 2
        presentation_breakdown['uses_bullet_points'] = True

    # Check for key section headers
    headers = ["education", "experience", "skills", "projects"]
    found_headers = [h for h in headers if h in all_raw_text.lower()]
    if len(found_headers) >= 3:
        clarity_score += 2
        presentation_breakdown['has_clear_sections'] = True
    
    presentation_score += min(clarity_score, 5)

    # --- 2. Conciseness & Length (Max 5 points) ---
    conciseness_score = 0
    # First, get the total years of experience from our other function
    # Note: We only need the breakdown value here, not the score.
    _, exp_breakdown = score_total_experience(resume_data, job_profile)
    total_years = exp_breakdown.get("total_years", 0) # Assumes your function provides this
    
    word_count = len(all_raw_text.split())
    presentation_breakdown['word_count'] = word_count

    if total_years < 10: # Ideal for 1-page resumes
        if word_count <= 600:
            conciseness_score = 5
        elif word_count <= 800:
            conciseness_score = 3
    else: # Ideal for 2-page resumes
        if word_count <= 1000:
            conciseness_score = 5
        elif word_count <= 1200:
            conciseness_score = 3
            
    presentation_score += conciseness_score

    # --- 3. Grammar & Spelling (Max 5 points) ---
    from language_tool_python import LanguageTool
    grammar_score = 0
    text = all_raw_text

    errors = grammar_check(text)
    if errors is not None:
        presentation_breakdown["grammar_errors"] = errors
        if errors <= 2:
            grammar_score += 5
        elif errors <= 5:
            grammar_score += 3
        elif errors <= 10:
            grammar_score += 1
    else:
        presentation_breakdown["grammar_errors"] = "API failed"
        grammar_score += 2
    presentation_score += grammar_score
    
    return presentation_score, presentation_breakdown
