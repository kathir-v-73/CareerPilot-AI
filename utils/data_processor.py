import pandas as pd
import numpy as np
import re
from typing import List, Dict, Any

class DataProcessor:
    """Processes raw job data into structured format for analysis"""
    
    def __init__(self):
        self.processed_data = None
    
    def process_jobs(self, jobs_data: List[Dict]) -> pd.DataFrame:
        """Process raw job data into cleaned DataFrame"""
        df = pd.DataFrame(jobs_data)
        
        # Clean and standardize job titles
        df['job_title'] = df['job_title'].apply(self._clean_job_title)
        
        # Process salary information
        df = self._process_salary(df)
        
        # Process experience requirements
        df = self._process_experience(df)
        
        # Clean and standardize skills
        df['skills'] = df['skills'].apply(self._clean_skills)
        
        # Clean location
        df['location'] = df['location'].apply(self._clean_location)
        
        # Add posting date if not present
        if 'posted_date' not in df.columns:
            df['posted_date'] = pd.Timestamp.now()
        
        return df
    
    def _clean_job_title(self, title: str) -> str:
        """Clean and standardize job titles"""
        if pd.isna(title):
            return "Not Specified"
        
        # Remove extra spaces and standardize
        title = re.sub(r'\s+', ' ', str(title).strip())
        
        # Capitalize properly
        title = title.title()
        
        return title
    
    def _process_salary(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract and process salary information"""
        def extract_salary_range(salary_str):
            if pd.isna(salary_str):
                return np.nan, np.nan
            
            # Convert to string and clean
            salary_str = str(salary_str).lower()
            
            # Extract numbers (assuming in lakhs)
            numbers = re.findall(r'(\d+(?:\.\d+)?)', salary_str)
            
            if len(numbers) >= 2:
                return float(numbers[0]), float(numbers[1])
            elif len(numbers) == 1:
                val = float(numbers[0])
                return val, val * 1.2  # Assume 20% range
            else:
                return np.nan, np.nan
        
        # Apply salary extraction
        if 'salary' in df.columns:
            df[['salary_min', 'salary_max']] = df['salary'].apply(
                lambda x: pd.Series(extract_salary_range(x))
            )
        else:
            # Create default salary ranges based on experience if not present
            df['salary_min'] = np.random.uniform(3, 15, len(df))
            df['salary_max'] = df['salary_min'] * np.random.uniform(1.2, 2.0, len(df))
        
        return df
    
    def _process_experience(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract and process experience requirements"""
        def extract_experience_range(exp_str):
            if pd.isna(exp_str):
                return np.nan, np.nan
            
            exp_str = str(exp_str).lower()
            numbers = re.findall(r'(\d+)', exp_str)
            
            if len(numbers) >= 2:
                return int(numbers[0]), int(numbers[1])
            elif len(numbers) == 1:
                val = int(numbers[0])
                return val, val + 2
            else:
                return 0, 2  # Default for entry level
        
        if 'experience' in df.columns:
            df[['exp_min', 'exp_max']] = df['experience'].apply(
                lambda x: pd.Series(extract_experience_range(x))
            )
        else:
            # Generate experience ranges
            df['exp_min'] = np.random.choice([0, 1, 2, 3, 5, 8], len(df))
            df['exp_max'] = df['exp_min'] + np.random.choice([2, 3, 4, 5], len(df))
        
        # Map to experience levels
        def get_experience_level(exp_min, exp_max):
            avg_exp = (exp_min + exp_max) / 2 if not (pd.isna(exp_min) or pd.isna(exp_max)) else 2
            if avg_exp <= 2:
                return "Entry Level (0-2 years)"
            elif avg_exp <= 5:
                return "Mid Level (3-5 years)"
            elif avg_exp <= 10:
                return "Senior Level (6-10 years)"
            else:
                return "Expert Level (10+ years)"
        
        df['experience_level'] = df.apply(
            lambda row: get_experience_level(row.get('exp_min'), row.get('exp_max')), 
            axis=1
        )
        
        return df
    
    def _clean_skills(self, skills_str: str) -> str:
        """Clean and standardize skills"""
        if pd.isna(skills_str):
            return ""
        
        skills_str = str(skills_str)
        
        # Split by common delimiters and clean
        skills = re.split(r'[,;|]', skills_str)
        cleaned_skills = []
        
        for skill in skills:
            skill = skill.strip().title()
            if len(skill) > 1:  # Filter out single characters
                cleaned_skills.append(skill)
        
        return ', '.join(cleaned_skills)
    
    def _clean_location(self, location: str) -> str:
        """Clean and standardize location"""
        if pd.isna(location):
            return "Not Specified"
        
        location = str(location).strip()
        
        # Standardize common city names
        location_mapping = {
            'bengaluru': 'Bangalore',
            'mumbai': 'Mumbai',
            'delhi': 'Delhi',
            'hyderabad': 'Hyderabad',
            'pune': 'Pune',
            'chennai': 'Chennai',
            'kolkata': 'Kolkata',
            'gurgaon': 'Gurgaon',
            'noida': 'Noida'
        }
        
        location_lower = location.lower()
        for key, value in location_mapping.items():
            if key in location_lower:
                return value
        
        return location.title()
    
    def get_unique_skills(self, df: pd.DataFrame) -> List[str]:
        """Extract all unique skills from the dataset"""
        all_skills = set()
        
        for skills_str in df['skills'].dropna():
            skills = [skill.strip() for skill in str(skills_str).split(',') if skill.strip()]
            all_skills.update(skills)
        
        return sorted(list(all_skills))
    
    def get_job_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate basic statistics about the job dataset"""
        stats = {
            'total_jobs': len(df),
            'unique_companies': df['company'].nunique() if 'company' in df.columns else 0,
            'unique_locations': df['location'].nunique(),
            'avg_salary_min': df['salary_min'].mean() if 'salary_min' in df.columns else 0,
            'avg_salary_max': df['salary_max'].mean() if 'salary_max' in df.columns else 0,
            'experience_distribution': df['experience_level'].value_counts().to_dict() if 'experience_level' in df.columns else {},
            'top_skills': self._get_top_skills(df, top_n=10)
        }
        
        return stats
    
    def _get_top_skills(self, df: pd.DataFrame, top_n: int = 10) -> List[str]:
        """Get the most frequently mentioned skills"""
        skill_counts = {}
        
        for skills_str in df['skills'].dropna():
            skills = [skill.strip() for skill in str(skills_str).split(',') if skill.strip()]
            for skill in skills:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        # Sort by frequency and return top N
        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
        return [skill for skill, count in sorted_skills[:top_n]]
