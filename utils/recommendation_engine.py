import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any
import re

class RecommendationEngine:
    """Job recommendation engine using TF-IDF and cosine similarity"""
    
    def __init__(self, jobs_df: pd.DataFrame):
        self.jobs_df = jobs_df.copy()
        self.tfidf_vectorizer = None
        self.job_vectors = None
        self._prepare_data()
    
    def _prepare_data(self):
        """Prepare data for recommendation engine"""
        # Combine relevant text fields for matching
        self.jobs_df['combined_text'] = self.jobs_df.apply(self._combine_job_features, axis=1)
        
        # Create TF-IDF vectors
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
        
        # Fit and transform job descriptions
        self.job_vectors = self.tfidf_vectorizer.fit_transform(
            self.jobs_df['combined_text'].fillna('')
        )
    
    def _combine_job_features(self, row) -> str:
        """Combine job features into a single text for matching"""
        features = []
        
        # Add job title (with higher weight)
        if pd.notna(row.get('job_title')):
            features.append(str(row['job_title']) * 2)  # Weight job title more
        
        # Add skills
        if pd.notna(row.get('skills')):
            features.append(str(row['skills']))
        
        # Add company (optional context)
        if pd.notna(row.get('company')):
            features.append(str(row['company']))
        
        # Add any description or requirements if available
        if pd.notna(row.get('description')):
            features.append(str(row['description']))
        
        return ' '.join(features)
    
    def get_recommendations(self, 
                          user_skills: List[str],
                          location: str = None,
                          experience_level: str = None,
                          salary_min: float = None,
                          salary_max: float = None,
                          top_n: int = 10) -> pd.DataFrame:
        """Get job recommendations based on user profile"""
        
        # Create user profile vector
        user_profile = ' '.join(user_skills)
        user_vector = self.tfidf_vectorizer.transform([user_profile])
        
        # Calculate similarity scores
        similarity_scores = cosine_similarity(user_vector, self.job_vectors)[0]
        
        # Add similarity scores to dataframe
        recommendations_df = self.jobs_df.copy()
        recommendations_df['compatibility_score'] = similarity_scores
        
        # Apply filters
        recommendations_df = self._apply_filters(
            recommendations_df,
            location=location,
            experience_level=experience_level,
            salary_min=salary_min,
            salary_max=salary_max
        )
        
        # Sort by compatibility score
        recommendations_df = recommendations_df.sort_values(
            'compatibility_score', 
            ascending=False
        ).head(top_n)
        
        # Add match explanation
        recommendations_df['match_explanation'] = recommendations_df.apply(
            lambda row: self._generate_match_explanation(row, user_skills), 
            axis=1
        )
        
        return recommendations_df
    
    def _apply_filters(self,
                      df: pd.DataFrame,
                      location: str = None,
                      experience_level: str = None,
                      salary_min: float = None,
                      salary_max: float = None) -> pd.DataFrame:
        """Apply filters to job recommendations"""
        
        filtered_df = df.copy()
        
        # Location filter
        if location and location != "Any":
            if location == "Remote":
                filtered_df = filtered_df[
                    filtered_df['location'].str.contains('Remote', case=False, na=False)
                ]
            else:
                filtered_df = filtered_df[
                    (filtered_df['location'] == location) |
                    (filtered_df['location'].str.contains('Remote', case=False, na=False))
                ]
        
        # Experience level filter
        if experience_level:
            # Extract years from experience level
            exp_years = self._extract_experience_years(experience_level)
            if exp_years is not None:
                filtered_df = filtered_df[
                    (filtered_df['exp_min'] <= exp_years) & 
                    (filtered_df['exp_max'] >= exp_years)
                ]
        
        # Salary filter
        if salary_min is not None and salary_max is not None:
            filtered_df = filtered_df[
                (filtered_df['salary_max'] >= salary_min) &
                (filtered_df['salary_min'] <= salary_max)
            ]
        
        return filtered_df
    
    def _extract_experience_years(self, experience_level: str) -> int:
        """Extract years from experience level string"""
        if "Entry" in experience_level:
            return 1
        elif "Mid" in experience_level:
            return 4
        elif "Senior" in experience_level:
            return 8
        elif "Expert" in experience_level:
            return 12
        return None
    
    def _generate_match_explanation(self, job_row, user_skills: List[str]) -> str:
        """Generate explanation for why a job matches"""
        explanations = []
        
        # Check skill matches
        job_skills_str = str(job_row.get('skills', '')).lower()
        matching_skills = []
        
        for skill in user_skills:
            if skill.lower() in job_skills_str:
                matching_skills.append(skill)
        
        if matching_skills:
            explanations.append(f"Matching skills: {', '.join(matching_skills[:3])}")
        
        # Check title match
        job_title = str(job_row.get('job_title', '')).lower()
        title_keywords = [skill.lower() for skill in user_skills if len(skill) > 3]
        
        for keyword in title_keywords:
            if keyword in job_title:
                explanations.append(f"Title contains '{keyword}'")
                break
        
        if not explanations:
            explanations.append("General profile match")
        
        return " | ".join(explanations[:2])
    
    def analyze_skill_gaps(self, user_skills: List[str], target_role: str) -> Dict[str, Any]:
        """Analyze skill gaps for a target role"""
        
        # Filter jobs by target role
        role_jobs = self.jobs_df[
            self.jobs_df['job_title'].str.contains(target_role, case=False, na=False)
        ]
        
        if role_jobs.empty:
            # If no exact matches, use broader search
            keywords = target_role.lower().split()
            for keyword in keywords:
                role_jobs = self.jobs_df[
                    self.jobs_df['job_title'].str.contains(keyword, case=False, na=False)
                ]
                if not role_jobs.empty:
                    break
        
        # Extract required skills from role jobs
        required_skills = set()
        for skills_str in role_jobs['skills'].dropna():
            skills = [skill.strip() for skill in str(skills_str).split(',') if skill.strip()]
            required_skills.update([skill.lower() for skill in skills])
        
        # Normalize user skills
        user_skills_lower = [skill.lower() for skill in user_skills]
        
        # Find gaps
        missing_skills = []
        existing_skills = []
        
        for req_skill in required_skills:
            found = False
            for user_skill in user_skills_lower:
                if (user_skill in req_skill or req_skill in user_skill or 
                    self._skills_similar(user_skill, req_skill)):
                    existing_skills.append(req_skill.title())
                    found = True
                    break
            
            if not found:
                missing_skills.append(req_skill.title())
        
        # Count skill frequency to prioritize
        skill_counts = {}
        for skills_str in role_jobs['skills'].dropna():
            skills = [skill.strip().lower() for skill in str(skills_str).split(',') if skill.strip()]
            for skill in skills:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        # Sort missing skills by frequency (most required first)
        missing_skills_with_counts = [
            (skill, skill_counts.get(skill.lower(), 0)) 
            for skill in missing_skills
        ]
        missing_skills_sorted = [
            skill for skill, count in sorted(missing_skills_with_counts, 
                                           key=lambda x: x[1], reverse=True)
        ]
        
        return {
            'target_role': target_role,
            'total_role_jobs': len(role_jobs),
            'existing_skills': list(set(existing_skills)),
            'missing_skills': missing_skills_sorted,
            'skill_match_percentage': len(existing_skills) / max(len(required_skills), 1) * 100
        }
    
    def _skills_similar(self, skill1: str, skill2: str) -> bool:
        """Check if two skills are similar"""
        # Simple similarity check
        if len(skill1) < 3 or len(skill2) < 3:
            return skill1 == skill2
        
        # Check if one is contained in the other
        return (skill1 in skill2 or skill2 in skill1 or
                abs(len(skill1) - len(skill2)) <= 2)
    
    def get_similar_jobs(self, job_id: int, top_n: int = 5) -> pd.DataFrame:
        """Get jobs similar to a specific job"""
        if job_id >= len(self.jobs_df):
            return pd.DataFrame()
        
        # Get similarity with all other jobs
        job_vector = self.job_vectors[job_id:job_id+1]
        similarities = cosine_similarity(job_vector, self.job_vectors)[0]
        
        # Get top similar jobs (excluding the job itself)
        similar_indices = np.argsort(similarities)[::-1][1:top_n+1]
        
        similar_jobs = self.jobs_df.iloc[similar_indices].copy()
        similar_jobs['similarity_score'] = similarities[similar_indices]
        
        return similar_jobs
    
    def get_trending_skills(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get trending skills based on recent job postings"""
        
        # For this implementation, we'll use skill frequency as a proxy for trending
        skill_counts = {}
        
        for skills_str in self.jobs_df['skills'].dropna():
            skills = [skill.strip() for skill in str(skills_str).split(',') if skill.strip()]
            for skill in skills:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        # Sort by frequency
        trending_skills = [
            {'skill': skill, 'count': count, 'trend': 'up'}
            for skill, count in sorted(skill_counts.items(), 
                                     key=lambda x: x[1], reverse=True)[:20]
        ]
        
        return trending_skills
