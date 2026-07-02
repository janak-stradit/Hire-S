import asyncio
import os
import sys
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.config.settings import get_settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def seed():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    
    excel_path = ROOT / 'storage' / 'candidate_pool' / 'test_synthetic_candidates.xlsx'
    if not excel_path.exists():
        print("Seed file not found at", excel_path)
        return
        
    print(f"Reading {excel_path}...")
    df = pd.read_excel(excel_path)
    
    # We replace NaN with None for SQL insertion
    df = df.where(pd.notnull(df), None)
    
    async with engine.begin() as conn:
        # Check if already seeded
        res = await conn.execute(text("SELECT count(*) FROM users WHERE role = 'candidate'"))
        count = res.scalar()
        if count > 0:
            print(f"Database already contains {count} candidates. Skipping seed.")
            return
            
        print(f"Seeding {len(df)} candidates into database...")
        
        for idx, row in df.iterrows():
            # Insert User
            await conn.execute(text("""
                INSERT INTO users (id, email, password_hash, role, is_active, created_at, updated_at)
                VALUES (:id, :email, :password_hash, :role, :is_active, NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": row['candidate_id'],
                "email": row['email'],
                "password_hash": row['password_hash'],
                "role": 'candidate',
                "is_active": True
            })
            
            # Insert CandidateProfile
            await conn.execute(text("""
                INSERT INTO candidate_profiles (
                    candidate_id, first_name, last_name, phone, city, state, country,
                    current_company, current_role, total_experience, expected_salary, notice_period,
                    highest_education, linkedin_url, github_url, portfolio_url,
                    profile_completion_percentage, source_type, verification_status,
                    source_reference, agent_processing_allowed, reusable_from_pool
                ) VALUES (
                    :candidate_id, :first_name, :last_name, :phone, :city, :state, :country,
                    :current_company, :current_role, :total_experience, :expected_salary, :notice_period,
                    :highest_education, :linkedin_url, :github_url, :portfolio_url,
                    :profile_completion_percentage, :source_type, :verification_status,
                    :source_reference, TRUE, TRUE
                )
                ON CONFLICT (candidate_id) DO NOTHING
            """), {
                "candidate_id": row['candidate_id'],
                "first_name": row['first_name'],
                "last_name": row['last_name'],
                "phone": str(row['phone']) if row['phone'] else None,
                "city": row['city'],
                "state": row['state'],
                "country": row['country'],
                "current_company": row['current_company'],
                "current_role": row['current_role'],
                "total_experience": float(row['total_experience']) if row['total_experience'] else None,
                "expected_salary": float(row['expected_salary']) if row['expected_salary'] else None,
                "notice_period": row['notice_period'],
                "highest_education": row['highest_education'],
                "linkedin_url": row['linkedin_url'],
                "github_url": row['github_url'],
                "portfolio_url": row['portfolio_url'],
                "profile_completion_percentage": float(row['profile_completion_percentage']) if row['profile_completion_percentage'] else 100,
                "source_type": row['source_type'] or 'synthetic',
                "verification_status": row['verification_status'] or 'PENDING',
                "source_reference": row['source_reference'] or 'seed'
            })
            
            # Insert Resume
            if row['resume_id']:
                await conn.execute(text("""
                    INSERT INTO resumes (resume_id, candidate_id, filename, original_filename, file_size, file_type, storage_path)
                    VALUES (:resume_id, :candidate_id, :filename, :original_filename, :file_size, :file_type, :storage_path)
                    ON CONFLICT (resume_id) DO NOTHING
                """), {
                    "resume_id": row['resume_id'],
                    "candidate_id": row['candidate_id'],
                    "filename": row['filename'],
                    "original_filename": row['original_filename'],
                    "file_size": int(row['file_size']) if row['file_size'] else 0,
                    "file_type": row['file_type'] or 'application/pdf',
                    "storage_path": row['storage_path'] or ''
                })
            
            # Insert ParsedResume
            if row['parsed_resume_id']:
                await conn.execute(text("""
                    INSERT INTO parsed_resumes (
                        parsed_resume_id, resume_id, candidate_id, skills, total_experience_years,
                        education, certifications, projects, sections, raw_text
                    ) VALUES (
                        :parsed_resume_id, :resume_id, :candidate_id, :skills, :total_experience_years,
                        :education, :certifications, :projects, '{}'::jsonb, :raw_text
                    )
                    ON CONFLICT (parsed_resume_id) DO NOTHING
                """), {
                    "parsed_resume_id": row['parsed_resume_id'],
                    "resume_id": row['resume_id'],
                    "candidate_id": row['candidate_id'],
                    "skills": str(row['skills']) if row['skills'] else '',
                    "total_experience_years": float(row['total_experience_years']) if row['total_experience_years'] else 0.0,
                    "education": str(row['education']) if row['education'] else '',
                    "certifications": str(row['certifications']) if row['certifications'] else '',
                    "projects": str(row['projects']) if row['projects'] else '',
                    "raw_text": str(row['raw_text']) if row['raw_text'] else ''
                })
                
    print("Database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
