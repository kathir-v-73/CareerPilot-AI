import pandas as pd
import numpy as np
from typing import Dict, List, Any
from collections import Counter
import plotly.express as px
import plotly.graph_objects as go

class MarketInsights:
    """Generate market intelligence and insights from job data"""
    
    def __init__(self, jobs_df: pd.DataFrame):
        self.jobs_df = jobs_df.copy()
    
    def generate_insights(self) -> Dict[str, Any]:
        """Generate comprehensive market insights"""
        
        insights = {
            'top_skills': self._get_top_skills(),
            'salary_insights': self._get_salary_insights(),
            'experience_distribution': self._get_experience_distribution(),
            'trending_roles': self._get_trending_roles(),
            'skills_salary_correlation': self._get_skills_salary_correlation()
        }
        
        return insights
    
    def _get_top_skills(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most in-demand skills"""
        skill_counter = Counter()
        
        for skills_str in self.jobs_df['skills'].dropna():
            skills = [skill.strip() for skill in str(skills_str).split(',') if skill.strip()]
            skill_counter.update(skills)
        
        top_skills = skill_counter.most_common(limit)
        
        return [
            {'skill': skill, 'count': count}
            for skill, count in top_skills
        ]
    
    def _get_salary_insights(self) -> Dict[str, Any]:
        """Get salary distribution and insights"""
        salary_data = {}
        
        if 'salary_max' in self.jobs_df.columns:
            salary_max = self.jobs_df['salary_max'].dropna()
            
            salary_data = {
                'average_max_salary': float(salary_max.mean()),
                'median_max_salary': float(salary_max.median()),
                'salary_percentiles': {
                    '25th': float(salary_max.quantile(0.25)),
                    '50th': float(salary_max.quantile(0.5)),
                    '75th': float(salary_max.quantile(0.75)),
                    '90th': float(salary_max.quantile(0.9))
                },
                'salary_by_experience': self._salary_by_experience()
            }
        
        return salary_data
    
    def _salary_by_experience(self) -> List[Dict[str, Any]]:
        """Get salary distribution by experience level"""
        if 'experience_level' not in self.jobs_df.columns or 'salary_max' not in self.jobs_df.columns:
            return []
        
        exp_salary = self.jobs_df.groupby('experience_level')['salary_max'].agg(['mean', 'median', 'count']).reset_index()
        
        return [
            {
                'experience_level': row['experience_level'],
                'average_salary': float(row['mean']),
                'median_salary': float(row['median']),
                'job_count': int(row['count'])
            }
            for _, row in exp_salary.iterrows()
        ]
    
    def _get_experience_distribution(self) -> Dict[str, int]:
        """Get distribution of jobs by experience level"""
        if 'experience_level' not in self.jobs_df.columns:
            return {}
        
        exp_dist = self.jobs_df['experience_level'].value_counts()
        return {level: int(count) for level, count in exp_dist.items()}
    
    def _get_trending_roles(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Get trending job roles"""
        role_counts = self.jobs_df['job_title'].value_counts().head(limit)
        
        return [
            {
                'job_title': role,
                'count': int(count),
                'avg_salary': float(self.jobs_df[self.jobs_df['job_title'] == role]['salary_max'].mean()) 
                            if 'salary_max' in self.jobs_df.columns else 0
            }
            for role, count in role_counts.items()
        ]
    
    def _get_skills_salary_correlation(self) -> List[Dict[str, Any]]:
        """Get skills that correlate with higher salaries"""
        if 'salary_max' not in self.jobs_df.columns:
            return []
        
        skill_salaries = {}
        
        for _, row in self.jobs_df.iterrows():
            if pd.notna(row['skills']) and pd.notna(row['salary_max']):
                skills = [skill.strip() for skill in str(row['skills']).split(',') if skill.strip()]
                for skill in skills:
                    if skill not in skill_salaries:
                        skill_salaries[skill] = []
                    skill_salaries[skill].append(row['salary_max'])
        
        # Calculate average salary for each skill (with minimum occurrences)
        skill_avg_salaries = []
        for skill, salaries in skill_salaries.items():
            if len(salaries) >= 3:  # At least 3 occurrences
                avg_salary = np.mean(salaries)
                skill_avg_salaries.append({
                    'skill': skill,
                    'average_salary': float(avg_salary),
                    'job_count': len(salaries)
                })
        
        # Sort by average salary
        skill_avg_salaries.sort(key=lambda x: x['average_salary'], reverse=True)
        
        return skill_avg_salaries[:15]  # Top 15 highest-paying skills
    
    def get_market_summary(self) -> Dict[str, Any]:
        """Get a concise market summary"""
        insights = self.generate_insights()
        
        summary = {
            'total_jobs': len(self.jobs_df),
            'total_companies': self.jobs_df['company'].nunique() if 'company' in self.jobs_df.columns else 0,
            'total_locations': self.jobs_df['location'].nunique(),
            'top_skill': insights['top_skills'][0]['skill'] if insights['top_skills'] else 'N/A',
            'avg_salary': insights['salary_insights'].get('average_max_salary', 0)
        }
        
        return summary
    
    def create_skills_demand_chart(self) -> go.Figure:
        """Create a chart showing skills demand"""
        top_skills = self._get_top_skills(15)
        
        if not top_skills:
            return go.Figure()
        
        skills_df = pd.DataFrame(top_skills)
        
        fig = px.bar(
            skills_df,
            x='count',
            y='skill',
            orientation='h',
            title='Most In-Demand Skills',
            labels={'count': 'Number of Job Postings', 'skill': 'Skills'},
            color='count',
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(
            height=500,
            yaxis={'categoryorder': 'total ascending'}
        )
        
        return fig
    
    def create_salary_trends_chart(self) -> go.Figure:
        """Create salary trends chart by experience level"""
        salary_by_exp = self._salary_by_experience()
        
        if not salary_by_exp:
            return go.Figure()
        
        salary_df = pd.DataFrame(salary_by_exp)
        
        fig = px.line(
            salary_df,
            x='experience_level',
            y='average_salary',
            title='Average Salary by Experience Level',
            labels={'average_salary': 'Average Salary (LPA)', 'experience_level': 'Experience Level'},
            markers=True
        )
        
        fig.update_layout(height=400)
        
        return fig
    
    def get_skill_recommendations(self, user_skills: List[str]) -> List[Dict[str, Any]]:
        """Get skill recommendations based on current skills"""
        top_skills = self._get_top_skills(50)
        skill_names = [skill['skill'] for skill in top_skills]
        
        user_skills_lower = [skill.lower() for skill in user_skills]
        
        recommendations = []
        for skill_data in top_skills:
            skill_name = skill_data['skill']
            if skill_name.lower() not in user_skills_lower:
                # Check if it's related to existing skills
                related = any(
                    existing.lower() in skill_name.lower() or skill_name.lower() in existing.lower()
                    for existing in user_skills
                )
                
                recommendations.append({
                    'skill': skill_name,
                    'demand_count': skill_data['count'],
                    'related_to_existing': related,
                    'priority': 'High' if related and skill_data['count'] > 10 else 'Medium'
                })
        
        # Sort by relevance and demand
        recommendations.sort(key=lambda x: (x['related_to_existing'], x['demand_count']), reverse=True)
        
        return recommendations[:10]