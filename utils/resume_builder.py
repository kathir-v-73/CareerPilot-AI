from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from io import BytesIO
from typing import Dict, Any
import os

class ResumeBuilder:
    """Build and export professional resumes with AI optimization"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for resume"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='ResumeTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor='#1f77b4',
            spaceAfter=6,
            alignment=TA_CENTER
        ))
        
        # Contact info style
        self.styles.add(ParagraphStyle(
            name='ContactInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=12
        ))
        
        # Section heading style
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor='#1f77b4',
            spaceAfter=6,
            spaceBefore=12
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='ResumeBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
    
    def generate_pdf(self, resume_data: Dict[str, Any]) -> BytesIO:
        """Generate PDF resume from resume data"""
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        story = []
        
        # Name/Title
        name = resume_data.get('name', 'Your Name')
        story.append(Paragraph(name, self.styles['ResumeTitle']))
        story.append(Spacer(1, 6))
        
        # Contact Information
        contact_info = []
        if resume_data.get('email'):
            contact_info.append(resume_data['email'])
        if resume_data.get('phone'):
            contact_info.append(resume_data['phone'])
        if resume_data.get('location'):
            contact_info.append(resume_data['location'])
        if resume_data.get('linkedin'):
            contact_info.append(resume_data['linkedin'])
        
        if contact_info:
            contact_text = ' | '.join(contact_info)
            story.append(Paragraph(contact_text, self.styles['ContactInfo']))
        
        # Professional Summary
        if resume_data.get('summary'):
            story.append(Paragraph('PROFESSIONAL SUMMARY', self.styles['SectionHeading']))
            story.append(Paragraph(resume_data['summary'], self.styles['ResumeBody']))
        
        # Skills
        if resume_data.get('skills'):
            story.append(Paragraph('SKILLS', self.styles['SectionHeading']))
            story.append(Paragraph(resume_data['skills'], self.styles['ResumeBody']))
        
        # Experience
        if resume_data.get('experience'):
            story.append(Paragraph('WORK EXPERIENCE', self.styles['SectionHeading']))
            for exp in resume_data['experience']:
                # Job title and company
                exp_header = f"<b>{exp.get('title', '')}</b> - {exp.get('company', '')}"
                if exp.get('duration'):
                    exp_header += f" ({exp['duration']})"
                story.append(Paragraph(exp_header, self.styles['ResumeBody']))
                
                # Description/achievements
                if exp.get('description'):
                    story.append(Paragraph(exp['description'], self.styles['ResumeBody']))
                story.append(Spacer(1, 6))
        
        # Education
        if resume_data.get('education'):
            story.append(Paragraph('EDUCATION', self.styles['SectionHeading']))
            for edu in resume_data['education']:
                edu_text = f"<b>{edu.get('degree', '')}</b> - {edu.get('institution', '')}"
                if edu.get('year'):
                    edu_text += f" ({edu['year']})"
                story.append(Paragraph(edu_text, self.styles['ResumeBody']))
                if edu.get('details'):
                    story.append(Paragraph(edu['details'], self.styles['ResumeBody']))
                story.append(Spacer(1, 6))
        
        # Projects
        if resume_data.get('projects'):
            story.append(Paragraph('PROJECTS', self.styles['SectionHeading']))
            for proj in resume_data['projects']:
                proj_header = f"<b>{proj.get('name', '')}</b>"
                if proj.get('duration'):
                    proj_header += f" ({proj['duration']})"
                story.append(Paragraph(proj_header, self.styles['ResumeBody']))
                
                if proj.get('description'):
                    story.append(Paragraph(proj['description'], self.styles['ResumeBody']))
                story.append(Spacer(1, 6))
        
        # Certifications
        if resume_data.get('certifications'):
            story.append(Paragraph('CERTIFICATIONS', self.styles['SectionHeading']))
            for cert in resume_data['certifications']:
                cert_text = f"<b>{cert.get('name', '')}</b>"
                if cert.get('issuer'):
                    cert_text += f" - {cert['issuer']}"
                if cert.get('year'):
                    cert_text += f" ({cert['year']})"
                story.append(Paragraph(cert_text, self.styles['ResumeBody']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def create_sample_resume(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Create a sample resume structure from user profile"""
        
        resume_data = {
            'name': 'Your Name',
            'email': 'your.email@example.com',
            'phone': '+91 9876543210',
            'location': user_profile.get('location', 'India'),
            'linkedin': 'linkedin.com/in/yourprofile',
            'summary': f"Experienced professional with expertise in {user_profile.get('skills', 'various technologies')}. {user_profile.get('interests', 'Passionate about technology and innovation.')}",
            'skills': user_profile.get('skills', ''),
            'experience': [
                {
                    'title': 'Software Engineer',
                    'company': 'Company Name',
                    'duration': '2020 - Present',
                    'description': '• Led development of key features\n• Collaborated with cross-functional teams\n• Improved system performance by 30%'
                }
            ],
            'education': [
                {
                    'degree': 'Bachelor of Technology in Computer Science',
                    'institution': 'University Name',
                    'year': '2020',
                    'details': 'CGPA: 8.5/10'
                }
            ],
            'projects': [
                {
                    'name': 'Project Name',
                    'duration': '2023',
                    'description': 'Built a scalable application using modern technologies. Achieved significant user engagement.'
                }
            ],
            'certifications': [
                {
                    'name': 'AWS Certified Solutions Architect',
                    'issuer': 'Amazon Web Services',
                    'year': '2022'
                }
            ]
        }
        
        return resume_data
