import os
from google import genai
from google.genai import types
import logging
from typing import List, Optional

class GeminiIntegration:
    """Integration with Google Gemini for AI-powered career features"""
    
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "AIzaSyDNPbfVcU-djUmJDqHLmr0if35S-DbwFWQ"))
        
    def generate_learning_roadmap(self, 
                                target_role: str,
                                current_skills: List[str],
                                missing_skills: List[str]) -> Optional[str]:
        """Generate a personalized 3-month learning roadmap"""
        
        prompt = f"""
        Create a detailed 3-month learning roadmap for someone who wants to become a {target_role}.

        Current Skills: {', '.join(current_skills)}
        Skills to Develop: {', '.join(missing_skills[:5])}

        Please structure the roadmap as follows:

        ## Month 1: Foundation Building
        **Week 1:**
        - Learning objectives
        - Recommended resources (courses, books, tutorials)
        - Practical projects

        **Week 2-4:** [Continue similar structure]

        ## Month 2: Skill Development
        [Similar weekly breakdown]

        ## Month 3: Advanced Topics & Portfolio
        [Similar weekly breakdown]

        For each week, include:
        - Specific learning goals
        - Time estimates (hours per week)
        - Recommended resources with links when possible
        - Hands-on projects or exercises
        - Success metrics

        Focus on practical, actionable advice that can be implemented immediately.
        Include both free and paid resources where appropriate.
        """
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            logging.error(f"Error generating learning roadmap: {e}")
            return self._fallback_roadmap(target_role, missing_skills)
    
    def get_career_advice(self, question: str) -> str:
        """Get career advice and guidance"""
        
        system_prompt = """
        You are an expert career coach with 15+ years of experience helping professionals 
        advance their careers. You provide practical, actionable advice on:
        - Resume writing and optimization
        - Interview preparation and techniques
        - Career transitions and planning
        - Professional networking
        - Skill development
        - Salary negotiation
        - Work-life balance
        
        Always provide specific, actionable advice rather than generic responses.
        Use examples and real-world scenarios when helpful.
        Be encouraging but realistic in your guidance.
        """
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=f"{system_prompt}\n\nUser Question: {question}")]
                    )
                ]
            )
            return response.text
        except Exception as e:
            logging.error(f"Error getting career advice: {e}")
            return self._fallback_advice(question)
    
    def analyze_resume_match(self, 
                           resume_text: str, 
                           job_description: str) -> dict:
        """Analyze how well a resume matches a job description"""
        
        prompt = f"""
        Analyze how well this resume matches the job description and provide a detailed assessment:

        JOB DESCRIPTION:
        {job_description}

        RESUME:
        {resume_text}

        Please provide:
        1. Match Score (0-100%)
        2. Matching Skills/Qualifications
        3. Missing Skills/Qualifications
        4. Specific Improvement Recommendations
        5. Keywords to add to resume
        
        Format your response as structured text with clear sections.
        """
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return {"analysis": response.text, "success": True}
        except Exception as e:
            logging.error(f"Error analyzing resume match: {e}")
            return {"analysis": "Unable to analyze resume at this time. Please try again later.", "success": False}
    
    def generate_interview_questions(self, 
                                   job_title: str, 
                                   experience_level: str,
                                   skills: List[str]) -> str:
        """Generate practice interview questions"""
        
        prompt = f"""
        Generate a comprehensive set of interview questions for a {job_title} position 
        at the {experience_level} level, focusing on these skills: {', '.join(skills)}.

        Include:
        1. 5 behavioral questions (STAR method applicable)
        2. 5 technical questions specific to the role
        3. 3 situational questions
        4. 2 questions about career goals and motivation

        For each question, also provide:
        - Brief guidance on how to approach the answer
        - Key points to cover in the response

        Format the response clearly with sections and bullet points.
        """
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            logging.error(f"Error generating interview questions: {e}")
            return self._fallback_interview_questions(job_title)
    
    def get_salary_negotiation_advice(self, 
                                    job_title: str,
                                    experience_level: str,
                                    current_salary: float,
                                    target_salary: float) -> str:
        """Get personalized salary negotiation advice"""
        
        prompt = f"""
        Provide detailed salary negotiation advice for:
        - Job Title: {job_title}
        - Experience Level: {experience_level}
        - Current Salary: ₹{current_salary} LPA
        - Target Salary: ₹{target_salary} LPA

        Include:
        1. Market research recommendations
        2. Negotiation strategies and tactics
        3. How to present your case effectively
        4. What to do if they say no
        5. Non-salary benefits to consider
        6. Common mistakes to avoid
        7. Sample negotiation scripts

        Make it specific to the Indian job market context.
        """
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            logging.error(f"Error getting salary negotiation advice: {e}")
            return "Unable to provide salary negotiation advice at this time. Please try again later."
    
    def _fallback_roadmap(self, target_role: str, missing_skills: List[str]) -> str:
        """Fallback roadmap when Gemini is unavailable"""
        return f"""
        ## 3-Month Learning Roadmap for {target_role}

        ### Month 1: Foundation Building
        **Week 1-2:** Focus on {missing_skills[0] if missing_skills else 'core fundamentals'}
        - Start with online tutorials and documentation
        - Build basic projects to practice
        - Join relevant communities and forums

        **Week 3-4:** Expand to {missing_skills[1] if len(missing_skills) > 1 else 'advanced topics'}
        - Take structured online courses
        - Work on portfolio projects
        - Practice coding challenges

        ### Month 2: Skill Development
        **Week 5-6:** Dive deeper into {missing_skills[2] if len(missing_skills) > 2 else 'practical applications'}
        - Build real-world projects
        - Contribute to open source
        - Network with professionals

        **Week 7-8:** Integration and practice
        - Combine learned skills in projects
        - Mock interviews and assessments
        - Refine your portfolio

        ### Month 3: Advanced Topics & Job Preparation
        **Week 9-10:** Advanced concepts and best practices
        **Week 11-12:** Job search preparation and portfolio finalization

        Note: This is a basic roadmap. For more detailed guidance, please ensure your Gemini API key is configured.
        """
    
    def _fallback_advice(self, question: str) -> str:
        """Fallback advice when Gemini is unavailable"""
        if "resume" in question.lower():
            return """
            Here are some general resume tips:
            
            1. **Keep it concise**: 1-2 pages maximum
            2. **Use action verbs**: Start bullet points with strong action words
            3. **Quantify achievements**: Include numbers and metrics where possible
            4. **Tailor for each job**: Customize your resume for each application
            5. **Proofread carefully**: Check for typos and formatting issues
            
            For more personalized advice, please ensure your Gemini API key is configured.
            """
        elif "interview" in question.lower():
            return """
            General interview preparation tips:
            
            1. **Research the company**: Know their mission, values, and recent news
            2. **Practice common questions**: Prepare STAR method responses
            3. **Prepare questions to ask**: Show genuine interest in the role
            4. **Mock interviews**: Practice with friends or online platforms
            5. **Technical preparation**: Review relevant skills and concepts
            
            For more personalized guidance, please ensure your Gemini API key is configured.
            """
        else:
            return "I'm unable to provide detailed career advice at the moment. Please ensure your Gemini API key is properly configured for personalized guidance."
    
    def optimize_resume_content(self, resume_section: str, content: str, target_role: str = None) -> str:
        """Optimize resume content using AI"""
        
        prompt = f"""
        You are an expert resume writer and career coach. Optimize the following {resume_section} section of a resume.
        
        Current content:
        {content}
        
        {f'Target role: {target_role}' if target_role else ''}
        
        Please:
        1. Make it more impactful and achievement-oriented
        2. Use strong action verbs
        3. Quantify results where possible
        4. Keep it concise and professional
        5. Ensure ATS (Applicant Tracking System) compatibility
        
        Return only the optimized content without explanations.
        """
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            logging.error(f"Error optimizing resume content: {e}")
            return content  # Return original if optimization fails
    
    def _fallback_interview_questions(self, job_title: str) -> str:
        """Fallback interview questions when Gemini is unavailable"""
        return f"""
        ## Sample Interview Questions for {job_title}

        ### Behavioral Questions:
        1. Tell me about a challenging project you worked on
        2. Describe a time when you had to learn something new quickly
        3. How do you handle tight deadlines and pressure?
        4. Give an example of when you worked in a team
        5. Describe a mistake you made and how you handled it

        ### Technical Questions:
        1. Walk me through your technical skills
        2. How do you stay updated with new technologies?
        3. Describe your development process
        4. What's your experience with [relevant technology]?
        5. How do you approach problem-solving?

        ### Situational Questions:
        1. How would you handle conflicting requirements?
        2. What would you do if you disagreed with your manager?
        3. How do you prioritize multiple tasks?

        For more detailed, role-specific questions, please ensure your Gemini API key is configured.
        """
