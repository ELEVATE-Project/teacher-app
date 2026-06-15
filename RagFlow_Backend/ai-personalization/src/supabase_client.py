# TODO : Clear this out. 
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path

current_dir = Path(__file__).parent
dotenv_path = current_dir.parent.parent.parent / '.env'
load_dotenv(dotenv_path=dotenv_path)


class SupabaseDB:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY_PYTHON")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY_PYTHON must be set in .env file")
        
        self.client: Client = create_client(url, key)
    
    def get_teachers_by_cluster(self, cluster_id):
        """Fetch all teachers in a cluster using 'cluster' column"""
        try:
            response = self.client.table('teachers').select('*').eq('cluster', cluster_id).execute()
            return response.data
        except Exception as e:
            print(f"Error fetching cluster teachers: {e}")
            return []
    
    def get_issue_competency_mappings(self):
        """Fetch all issue-to-competency keyword mappings"""
        try:
            response = self.client.table('issue_competency_mapping').select('*').execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error loading mappings: {e}")
            return []
        
    def get_teacher_issues(self, teacher_id):
        """Fetch all issues mapped to a specific teacher."""
        try:
            response = self.client.table('issues').select('*').eq('teacher_id', teacher_id).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching teacher issues: {e}")
            return []

    def get_issue_by_id(self, issue_id: str):
        """Fetch a single issue by its unique ID."""
        try:
            response = self.client.table('issues').select('*').eq('id', issue_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error fetching issue by ID: {e}")
            return None
    
    # Backward compatibility alias
    def get_teacher_feedback(self, teacher_id):
        """
        DEPRECATED: Legacy method - use get_teacher_issues instead
        This method is no longer used (teacher-app removed)
        """
        return self.get_teacher_issues(teacher_id)
    
    def get_cluster_issues(self, cluster_id):
        """Fetch all issues from a cluster"""
        try:
            response = self.client.table('issues')\
                .select('*')\
                .eq('cluster', cluster_id)\
                .execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching cluster issues: {e}")
            return []
    
    # Backward compatibility alias
    def get_cluster_feedback(self, cluster_id):
        """Legacy method: use get_cluster_issues instead"""
        return self.get_cluster_issues(cluster_id)
    
    def get_base_training_module(self, module_id):
        """Fetch base module/resource content for personalization pipeline."""
        try:
            response = self.client.table('training_modules').select('*').eq('id', module_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error fetching module: {e}")
            return None
    
    def save_personalized_training(self, teacher_id, module_id, personalized_content, metadata):
        """Save personalized training assignment"""
        try:
            data = {
                'teacher_id': teacher_id,
                'module_id': module_id,
                'personalized_content': personalized_content,
                'adaptation_metadata': metadata,
                'status': 'assigned',
                'completion_percentage': 0
            }
            response = self.client.table('personalized_training').insert(data).execute()
            return response.data
        except Exception as e:
            print(f"Error saving personalized training: {e}")
            return None
    
    # Backward compatibility alias 
    def get_feedback_by_id(self, feedback_id: str):
        """
        DEPRECATED: Legacy method - use get_issue_by_id instead
        This method is no longer used (teacher-app removed)
        """
        return self.get_issue_by_id(feedback_id)

    def initialize_default_mappings(self):
        """Initialize default keyword mappings if table is empty"""
        try:
            existing = self.client.table('issue_competency_mapping').select('count', count='exact').execute()
            
            if existing.count == 0:
                print("Initializing default issue_competency_mapping data...")
                
                default_mappings = [
                    {'issue_keyword': 'behavior', 'competency_area': 'classroom_management', 'confidence_score': 0.85},
                    {'issue_keyword': 'discipline', 'competency_area': 'classroom_management', 'confidence_score': 0.85},
                    {'issue_keyword': 'classroom management', 'competency_area': 'classroom_management', 'confidence_score': 0.95},
                    {'issue_keyword': 'students talking', 'competency_area': 'classroom_management', 'confidence_score': 0.80},
                    {'issue_keyword': 'noise', 'competency_area': 'classroom_management', 'confidence_score': 0.75},
                    {'issue_keyword': 'disruption', 'competency_area': 'classroom_management', 'confidence_score': 0.85},
                    {'issue_keyword': 'curriculum', 'competency_area': 'content_knowledge', 'confidence_score': 0.80},
                    {'issue_keyword': 'content', 'competency_area': 'content_knowledge', 'confidence_score': 0.75},
                    {'issue_keyword': 'subject matter', 'competency_area': 'content_knowledge', 'confidence_score': 0.85},
                    {'issue_keyword': 'syllabus', 'competency_area': 'content_knowledge', 'confidence_score': 0.80},
                    {'issue_keyword': 'teaching methods', 'competency_area': 'pedagogy', 'confidence_score': 0.85},
                    {'issue_keyword': 'pedagogy', 'competency_area': 'pedagogy', 'confidence_score': 0.95},
                    {'issue_keyword': 'lesson planning', 'competency_area': 'pedagogy', 'confidence_score': 0.85},
                    {'issue_keyword': 'active learning', 'competency_area': 'pedagogy', 'confidence_score': 0.85},
                    {'issue_keyword': 'assessment', 'competency_area': 'pedagogy', 'confidence_score': 0.75},
                    {'issue_keyword': 'technology', 'competency_area': 'technology_usage', 'confidence_score': 0.85},
                    {'issue_keyword': 'computer', 'competency_area': 'technology_usage', 'confidence_score': 0.80},
                    {'issue_keyword': 'digital tools', 'competency_area': 'technology_usage', 'confidence_score': 0.90},
                    {'issue_keyword': 'projector', 'competency_area': 'technology_usage', 'confidence_score': 0.75},
                    {'issue_keyword': 'software', 'competency_area': 'technology_usage', 'confidence_score': 0.80},
                    {'issue_keyword': 'engagement', 'competency_area': 'student_engagement', 'confidence_score': 0.85},
                    {'issue_keyword': 'participation', 'competency_area': 'student_engagement', 'confidence_score': 0.80},
                    {'issue_keyword': 'motivation', 'competency_area': 'student_engagement', 'confidence_score': 0.85},
                    {'issue_keyword': 'attention', 'competency_area': 'student_engagement', 'confidence_score': 0.75},
                    {'issue_keyword': 'focus', 'competency_area': 'student_engagement', 'confidence_score': 0.75},
                    {'issue_keyword': 'interest', 'competency_area': 'student_engagement', 'confidence_score': 0.80},
                ]
                
                for mapping in default_mappings:
                    try:
                        self.client.table('issue_competency_mapping').insert(mapping).execute()
                    except Exception as e:
                        print(f"Error inserting mapping {mapping['issue_keyword']}: {e}")
                
                print(f"✓ Initialized {len(default_mappings)} default mappings")
            else:
                print(f"✓ Database already has {existing.count} mappings")
        except Exception as e:
            print(f"Error initializing mappings: {e}")


# Initialize global instance
db = SupabaseDB()
