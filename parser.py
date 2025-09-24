import pdfplumber
import os
from docx import Document
import spacy
import re
import json
from spacy.matcher import Matcher

# Load a larger spaCy model for better performance, if available
try:
    nlp = spacy.load("en_core_web_lg")
except OSError:
    print("Large model not found, falling back to small model. For better accuracy, run: python -m spacy download en_core_web_lg")
    nlp = spacy.load("en_core_web_sm")

# --- SKILL LOADING ---
def load_skills_from_json(file_path: str) -> list:
    """Loads a comprehensive list of skills from a structured JSON file."""
    with open(file_path, 'r') as f:
        skills_data = json.load(f)
    
    # Flatten the hierarchical JSON into a single list of skills
    all_skills = set()
    for category in skills_data.values():
        if isinstance(category, list):
            for skill in category:
                all_skills.add(skill)
        elif isinstance(category, dict):
            for sub_category in category.values():
                for skill in sub_category:
                    all_skills.add(skill)
    return sorted(list(all_skills))

# Load skills from our new JSON file
all_known_skills = load_skills_from_json("skills.json")


# --- CORE TEXT EXTRACTION ---

def extract_text(file_path: str) -> str:
    """Extracts raw text from a PDF or DOCX file."""
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    if ext == ".pdf":
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    elif ext == ".docx":
        doc = Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    else:
        raise ValueError("Unsupported file format: Must be a .pdf or .docx")
    
    return clean_text(text)

def clean_text(text: str) -> str:
    """Cleans the extracted text by removing strange characters and formatting."""
    text = text.replace('\t', ' ') # Replace tabs with spaces
    # Remove control characters but preserve line breaks
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Remove custom bullet points or icons that often appear in resumes
    text = re.sub(r'[\uf0b7\uf0a7\uf075]', '', text) 
    # Normalize whitespace
    text = re.sub(r'\s*\n\s*', '\n', text) # Remove spaces around newlines
    text = re.sub(r' +', ' ', text) # Condense multiple spaces
    return text.strip()

# --- STRUCTURED DATA EXTRACTION ---

def parse_resume(text: str) -> dict:
    """
    Main function to parse the resume text and extract structured data.
    This is the primary orchestrator.
    """
    sections = extract_sections(text)
    
    # Initialize the data dictionary
    parsed_data = {
        "name": None,
        "email": None,
        "phone": None,
        "links": [],
        "professional_summary": [],
        "work_experience": [],
        "education": [],
        "skills": [],
        "projects": [],
        "achievements": [],
        "certifications": []
    }

    # --- Extracting Contact Info and Name ---
    # We use the text *before* the first section header for contact info
    first_section_index = text.find(list(sections.keys())[0]) if sections else len(text)
    header_text = text[:first_section_index]

    parsed_data["name"] = extract_name(header_text)
    parsed_data["email"] = extract_email(header_text)
    parsed_data["phone"] = extract_phone(header_text)
    parsed_data["links"] = extract_links(header_text)
    
    # --- Extracting Content from Sections ---
    # A recruiter wants to see the summary right away.
    parsed_data["professional_summary"] = sections.get("professional summary", sections.get("summary", []))
    
    # The most critical part: structured work experience
    experience_text = "\n".join(sections.get("work experience", sections.get("experience", [])))
    parsed_data["work_experience"] = extract_structured_experience(experience_text)

    parsed_data["education"] = sections.get("education", [])
    parsed_data["projects"] = sections.get("projects", [])
    parsed_data["achievements"] = sections.get("achievements", [])
    parsed_data["certifications"] = sections.get("certifications", [])
    
    # Extract skills using the known list and context
    # This now uses the skills loaded from skills.json
    skills_section_text = "\n".join(sections.get("skills", sections.get("technical skills", [])))
    parsed_data["skills"] = extract_skills(skills_section_text, all_known_skills)

    return parsed_data

def extract_sections(text: str) -> dict:

    section_headers = [
        "professional summary", "summary", "objective",
        "work experience", "experience", "employment history",
        "education",
        "skills", "technical skills",
        "projects",
        "achievements", "awards",
        "certifications", "licenses & certifications"
    ]
    
    sections = {}
    current_section = "header" # Start in a default 'header' section
    sections[current_section] = []

    for line in text.split('\n'):
        line_lower = line.lower().strip()

        # Check if the line is a header
        is_header = False
        for header in section_headers:
            # A header is a line that contains the header text, and is usually short.
            if header in line_lower and len(line_lower) < 30:
                current_section = header
                if current_section not in sections:
                    sections[current_section] = []
                is_header = True
                break
        
        if not is_header and line.strip():
            sections[current_section].append(line.strip())
            
    return sections

def extract_name(text: str) -> str:
    """Extracts the candidate's name using spaCy's NER and regex fallbacks."""
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text.strip()
    
    # Regex fallback: Look for a capitalized name pattern
    match = re.search(r"^([A-Z][a-z]+)\s+([A-Z][a-z]+)", text)
    if match:
        return match.group(0)
    return None

def extract_email(text: str) -> str:
    """Finds the first valid email address."""
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    return match.group(0) if match else None

def extract_phone(text: str) -> str:
    """Finds the first valid phone number."""
    # This pattern is more robust for different formats
    match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    return match.group(0) if match else None

def extract_links(text: str) -> list:
    """Extracts LinkedIn, GitHub, and other portfolio links."""
    links = []
    patterns = {
        "linkedin": r'linkedin\.com/in/[\w-]+',
        "github": r'github\.com/[\w-]+',
        "portfolio": r'http[s]?://[\w\.-]+' # Generic website
    }
    for link_type, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            links.append({"type": link_type, "url": match})
    return links
    
def extract_structured_experience(text: str) -> list:
    """
    The "Plus Ultra" upgrade. This function finds distinct jobs and
    parses out the title, company, dates, and description.
    """
    experience = []
    # Split the text into chunks that likely represent a single job
    job_chunks = re.split(r'\n(?=[A-Z][a-z\s]+)', text) # Split on lines that look like job titles

    for chunk in job_chunks:
        if not chunk.strip():
            continue
            
        job = {}
        # Date patterns are the most reliable anchors
        date_match = re.search(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})\s*[-–to]+\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|Present|Current)', chunk, re.IGNORECASE)
        
        if date_match:
            job['start_date'] = date_match.group(1)
            job['end_date'] = date_match.group(2)
            # The text before the date is likely title and company
            header_part = chunk[:date_match.start()].strip()
            # The text after is the description
            job['description'] = chunk[date_match.end():].strip().split('\n')
            
            # Try to split the header into Title and Company
            header_lines = header_part.split('\n')
            job['title'] = header_lines[0].strip()
            job['company'] = header_lines[1].strip() if len(header_lines) > 1 else None
        else:
            # If no date is found, we can't structure it reliably
            job['title'] = None
            job['company'] = None
            job['dates'] = None
            job['description'] = chunk.strip().split('\n')
            
        experience.append(job)
        
    return experience

# --- SKILL EXTRACTION ---

def extract_skills(text: str, known_skills: list) -> list:
    """Finds skills from a known list using robust regex matching."""
    found_skills = set()
    for skill in known_skills:
        # Use word boundaries to match whole words only (e.g., "Java" not "JavaScript")
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text, re.IGNORECASE):
            found_skills.add(skill)
    return sorted(list(found_skills))
