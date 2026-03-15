import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

class ChatHistoryManager:
    """Manage AI chat history for users"""
    
    def __init__(self):
        self.history_file = "chat_history.json"
        self._init_storage()
    
    def _init_storage(self):
        """Initialize the storage file if it doesn't exist"""
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w') as f:
                json.dump({}, f)
    
    def _load_history(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load chat history from file"""
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_history(self, history: Dict[str, List[Dict[str, Any]]]):
        """Save chat history to file"""
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def save_chat(self, user_id: str, title: str, summary: str, chat_type: str = "coach") -> int:
        """Save a chat conversation to history"""
        history = self._load_history()
        
        if user_id not in history:
            history[user_id] = []
        
        # Create chat entry
        chat_entry = {
            'id': len(history[user_id]) + 1,
            'title': title,
            'summary': summary,
            'chat_type': chat_type,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'full_conversation': []  # Can be extended to store full conversation
        }
        
        history[user_id].append(chat_entry)
        self._save_history(history)
        
        return chat_entry['id']
    
    def get_chat_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all chat history for a user"""
        history = self._load_history()
        return history.get(user_id, [])
    
    def delete_chat(self, chat_id: int, user_id: str = None) -> bool:
        """Delete a specific chat entry"""
        history = self._load_history()
        
        if user_id:
            # Delete for specific user
            if user_id in history:
                history[user_id] = [chat for chat in history[user_id] if chat['id'] != chat_id]
                self._save_history(history)
                return True
        else:
            # Search across all users (for admin purposes)
            for user in history:
                history[user] = [chat for chat in history[user] if chat['id'] != chat_id]
            self._save_history(history)
            return True
        
        return False
    
    def search_chats(self, user_id: str, keyword: str) -> List[Dict[str, Any]]:
        """Search chat history by keyword"""
        history = self.get_chat_history(user_id)
        
        return [
            chat for chat in history
            if keyword.lower() in chat['title'].lower() or 
               keyword.lower() in chat['summary'].lower()
        ]
    
    def get_chat_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary statistics of user's chat history"""
        history = self.get_chat_history(user_id)
        
        if not history:
            return {
                'total_chats': 0,
                'coach_chats': 0,
                'roadmap_chats': 0,
                'last_chat': None
            }
        
        coach_chats = len([c for c in history if c['chat_type'] == 'coach'])
        roadmap_chats = len([c for c in history if c['chat_type'] == 'roadmap'])
        
        return {
            'total_chats': len(history),
            'coach_chats': coach_chats,
            'roadmap_chats': roadmap_chats,
            'last_chat': max(history, key=lambda x: x['timestamp'])['timestamp']
        }
    
    def export_chats(self, user_id: str) -> str:
        """Export chat history as JSON string"""
        history = self.get_chat_history(user_id)
        return json.dumps(history, indent=2)
    
    def clear_user_history(self, user_id: str) -> bool:
        """Clear all chat history for a user"""
        history = self._load_history()
        
        if user_id in history:
            history[user_id] = []
            self._save_history(history)
            return True
        
        return False