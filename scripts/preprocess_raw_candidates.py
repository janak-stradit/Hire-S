import argparse
import json
import csv
import pandas as pd
from datetime import datetime, timezone
import uuid
import os

# Standard HireX Candidate Schema
# We dynamically load this from the synthetic candidates file to ensure future-proofing.
TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'storage', 'candidate_pool', 'test_synthetic_candidates.xlsx')

def get_hirex_columns(template_path=TEMPLATE_PATH):
    """Dynamically read the exact expected columns from the current HireX schema."""
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}. Ensure it exists.")
    df = pd.read_excel(template_path)
    return list(df.columns)

def load_data(filepath):
    """Detect format and load data into a list of dictionaries."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.json':
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return [data]
            return data
    elif ext == '.csv':
        df = pd.read_csv(filepath)
        return df.to_dict('records')
    elif ext == '.txt':
        # Fallback for raw text, treating entire file as one candidate's raw text
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        return [{"raw_text": text, "email": f"unknown_{uuid.uuid4().hex[:8]}@example.com"}]
    else:
        raise ValueError(f"Unsupported file format: {ext}")

def run_ai_extraction(raw_candidate):
    """
    FUTURE PLACEHOLDER: Integrate AI Extraction here.
    For example, call ScrapeGraphAI or an LLM API (OpenAI/Gemini) to extract 
    structured fields from `raw_text` or unstructured fields.
    """
    # Currently a no-op, but structured to return an enriched dictionary
    extracted_data = {
        "skills": raw_candidate.get("skills", ""),
        "projects": raw_candidate.get("projects", ""),
        "total_experience_years": raw_candidate.get("total_experience_years", 0),
        "education": raw_candidate.get("education", ""),
        "summary": raw_candidate.get("summary", "")
    }
    return extracted_data

def preprocess_candidate(raw_candidate, required_columns):
    candidate_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Extract AI fields (stubbed for now, ready for future)
    ai_enriched_data = run_ai_extraction(raw_candidate)
    
    # Map fields with fallbacks
    email = raw_candidate.get('email', f"{candidate_id}@generated.local")
    
    mapped = {
        'candidate_id': candidate_id,
        'resume_id': str(uuid.uuid4()),
        'parsed_resume_id': str(uuid.uuid4()),
        'email': email,
        'password_hash': 'unsupported_external',
        'role': 'candidate',
        'is_active': True,
        'created_at': now,
        'first_name': raw_candidate.get('first_name', raw_candidate.get('name', '').split(' ')[0] if raw_candidate.get('name') else ''),
        'last_name': raw_candidate.get('last_name', ' '.join(raw_candidate.get('name', '').split(' ')[1:]) if raw_candidate.get('name') else ''),
        'phone': raw_candidate.get('phone', ''),
        'city': raw_candidate.get('city', ''),
        'state': raw_candidate.get('state', ''),
        'country': raw_candidate.get('country', ''),
        'domain': raw_candidate.get('domain', ''),
        'level': raw_candidate.get('level', ''),
        'current_company': raw_candidate.get('current_company', raw_candidate.get('company', '')),
        'current_role': raw_candidate.get('current_role', raw_candidate.get('job_title', '')),
        'total_experience': ai_enriched_data.get('total_experience_years', 0),
        'expected_salary': 0,
        'notice_period': '',
        'highest_education': ai_enriched_data.get('education', ''),
        'linkedin_url': raw_candidate.get('linkedin_url', ''),
        'github_url': raw_candidate.get('github_url', ''),
        'portfolio_url': raw_candidate.get('portfolio_url', ''),
        'profile_completion_percentage': 80,
        'filename': 'external_source.txt',
        'original_filename': 'external_source.txt',
        'file_size': 0,
        'file_type': 'text/plain',
        'storage_path': '',
        'uploaded_at': now,
        'skills': ai_enriched_data.get('skills', ''),
        'total_experience_years': ai_enriched_data.get('total_experience_years', 0),
        'education': ai_enriched_data.get('education', ''),
        'certifications': raw_candidate.get('certifications', ''),
        'projects': ai_enriched_data.get('projects', ''),
        'summary': ai_enriched_data.get('summary', ''),
        'raw_text': raw_candidate.get('raw_text', json.dumps(raw_candidate)),
        'parsed_at': now,
        'application_status': 'IMPORTED',
        'applied_at': now,
        'resume': '',
        'source_type': raw_candidate.get('source_type', 'external_platform'),
        'verification_status': 'pending',
        'source_reference': raw_candidate.get('source_reference', ''),
        # Critical settings for HireX workflow
        'agent_processing_allowed': True,
        'preferred_work_mode': raw_candidate.get('preferred_work_mode', 'hybrid'),
        'willing_to_relocate': raw_candidate.get('willing_to_relocate', False),
        'preferred_locations': raw_candidate.get('preferred_locations', ''),
        'industry_domain': raw_candidate.get('industry_domain', ''),
        'profile_last_updated_at': raw_candidate.get('profile_last_updated_at', now),
        'profile_refresh_cycle_days': 30
    }
    
    # Ensure no missing columns and only valid columns
    for col in required_columns:
        if col not in mapped:
            mapped[col] = ''
    
    # Filter out any unexpected columns
    final_mapped = {k: v for k, v in mapped.items() if k in required_columns}
            
    return final_mapped

def main():
    parser = argparse.ArgumentParser(description="Preprocess raw candidate data into HireX standardized format")
    parser.add_argument('--input', required=True, help="Path to raw input file (.json, .csv, .txt)")
    parser.add_argument('--output', required=True, help="Path to output excel file (.xlsx)")
    args = parser.parse_args()
    
    print(f"Loading HireX schema template from {TEMPLATE_PATH}...")
    hirex_columns = get_hirex_columns()
    print(f"Loaded {len(hirex_columns)} expected columns.")

    print(f"Loading raw data from {args.input}...")
    raw_data = load_data(args.input)
    print(f"Loaded {len(raw_data)} candidates.")
    
    processed = []
    for row in raw_data:
        processed.append(preprocess_candidate(row, hirex_columns))
        
    df = pd.DataFrame(processed, columns=hirex_columns)
    df.to_excel(args.output, index=False)
    print(f"Successfully exported {len(processed)} candidates to {args.output}")

if __name__ == "__main__":
    main()
