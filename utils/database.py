import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import json
from typing import Optional, Dict, List, Any

class Database:
    """Database utility for CareerPilot AI"""
    
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        if not self.database_url:
            self.database_url = None
            self.initialized = False
        else:
            self.initialized = True
            try:
                self.init_db()
            except Exception as e:
                print(f"Warning: Could not initialize database: {e}")
    
    @contextmanager
    def get_connection(self):
        """Get a database connection context manager"""
        if not self.initialized or not self.database_url:
            raise ValueError("Database not initialized")
        conn = psycopg2.connect(self.database_url)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def is_available(self) -> bool:
        """Check if database is available"""
        return self.initialized and self.database_url is not None
    
    def init_db(self):
        """Initialize database tables (removed job_applications table)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table for profile storage
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(100) UNIQUE NOT NULL,
                    skills TEXT,
                    experience_level VARCHAR(50),
                    interests TEXT,
                    location VARCHAR(100),
                    salary_min INTEGER,
                    salary_max INTEGER,
                    industry VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Email preferences table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_preferences (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(100) UNIQUE NOT NULL,
                    email VARCHAR(200),
                    job_alerts BOOLEAN DEFAULT TRUE,
                    roadmap_reminders BOOLEAN DEFAULT TRUE,
                    weekly_digest BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            
            cursor.close()
    
    def save_user_profile(self, user_id: str, profile: Dict[str, Any]) -> bool:
        """Save or update user profile"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO users (user_id, skills, experience_level, interests, location, salary_min, salary_max, industry, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    skills = EXCLUDED.skills,
                    experience_level = EXCLUDED.experience_level,
                    interests = EXCLUDED.interests,
                    location = EXCLUDED.location,
                    salary_min = EXCLUDED.salary_min,
                    salary_max = EXCLUDED.salary_max,
                    industry = EXCLUDED.industry,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                user_id,
                profile.get('skills', ''),
                profile.get('experience_level', ''),
                profile.get('interests', ''),
                profile.get('location', ''),
                profile.get('salary_min', 0),
                profile.get('salary_max', 0),
                profile.get('industry', '')
            ))
            
            cursor.close()
            return True
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by user_id"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT user_id, skills, experience_level, interests, location, 
                       salary_min, salary_max, industry, created_at, updated_at
                FROM users 
                WHERE user_id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            return dict(result) if result else None
    
    def save_email_preferences(self, user_id: str, email: str, preferences: Dict[str, bool]) -> bool:
        """Save email notification preferences"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO email_preferences 
                (user_id, email, job_alerts, roadmap_reminders, weekly_digest)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    email = EXCLUDED.email,
                    job_alerts = EXCLUDED.job_alerts,
                    roadmap_reminders = EXCLUDED.roadmap_reminders,
                    weekly_digest = EXCLUDED.weekly_digest
            """, (
                user_id,
                email,
                preferences.get('job_alerts', True),
                preferences.get('roadmap_reminders', True),
                preferences.get('weekly_digest', True)
            ))
            
            cursor.close()
            return True
    
    def get_email_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get email notification preferences"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT email, job_alerts, roadmap_reminders, weekly_digest
                FROM email_preferences 
                WHERE user_id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            return dict(result) if result else None