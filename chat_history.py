"""
Chat History Persistence for PAGie
===================================

Handles saving and loading chat history to persist across page refreshes.
Also manages input history for arrow key navigation.

MULTI-USER SUPPORT:
- Each user session gets a unique session ID from Streamlit
- Chat histories are stored per-session to prevent mixing
- Files: chat_history_{session_id}.json, input_history_{session_id}.json
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib


def get_session_id() -> str:
    """
    Get a unique session ID for the current user that persists across page refreshes.
    
    Uses browser localStorage to maintain the same session ID even when the page
    is refreshed, ensuring chat history continuity.
    
    Returns:
        Unique session identifier string
    """
    import streamlit as st
    from streamlit.components.v1 import html
    import uuid
    import time
    
    # Check if we already have a session ID in memory
    if 'user_session_id' in st.session_state:
        return st.session_state.user_session_id
    
    # Generate a unique key for this app instance
    storage_key = "pagie_session_id"
    
    # Try to get session ID from localStorage using JavaScript
    # This will persist across page refreshes
    session_id_html = f"""
    <script>
        // Try to get existing session ID from localStorage
        let sessionId = localStorage.getItem('{storage_key}');
        
        // If no session ID exists, generate a new one
        if (!sessionId) {{
            sessionId = Math.random().toString(36).substring(2, 10);
            localStorage.setItem('{storage_key}', sessionId);
        }}
        
        // Send session ID to Streamlit (via query parameter update)
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('session_id') !== sessionId) {{
            // Update URL without page reload
            const newUrl = window.location.pathname + '?session_id=' + sessionId;
            window.history.replaceState(null, '', newUrl);
        }}
        
        // Also try to communicate back via parent
        if (window.parent && window.parent.postMessage) {{
            window.parent.postMessage({{type: 'session_id', value: sessionId}}, '*');
        }}
    </script>
    """
    
    # Inject the JavaScript (only once)
    if 'session_id_injected' not in st.session_state:
        html(session_id_html, height=0)
        st.session_state.session_id_injected = True
    
    # Try to read session ID from URL parameter (updated by JavaScript)
    query_params = st.query_params
    if 'session_id' in query_params:
        session_id = query_params['session_id']
        st.session_state.user_session_id = session_id
        return session_id
    
    # Fallback: Generate a new session ID if localStorage hasn't loaded yet
    # This will be replaced on next rerun when localStorage loads
    if 'temp_session_id' not in st.session_state:
        st.session_state.temp_session_id = str(uuid.uuid4())[:8]
    
    return st.session_state.temp_session_id


class ChatHistoryManager:
    """Manages persistent chat history storage with multi-user support."""
    
    def __init__(self, base_path: str = "./data/sessions"):
        """
        Initialize the chat history manager.
        
        Args:
            base_path: Base directory for storing session files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.session_id = get_session_id()
        self.history_file = self.base_path / f"chat_history_{self.session_id}.json"
    
    def save_history(self, messages: List[Dict[str, Any]]) -> None:
        """
        Save chat history to disk for this session.
        
        Args:
            messages: List of message dictionaries with role, content, sources
        """
        try:
            history_data = {
                "session_id": self.session_id,
                "last_updated": datetime.now().isoformat(),
                "messages": messages
            }
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error saving chat history: {e}")
    
    def load_history(self) -> List[Dict[str, Any]]:
        """
        Load chat history from disk for this session.
        
        Returns:
            List of message dictionaries, or empty list if no history exists
        """
        try:
            if not self.history_file.exists():
                return []
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            
            # Verify this is the correct session
            if history_data.get("session_id") != self.session_id:
                return []
                
            return history_data.get("messages", [])
            
        except Exception as e:
            print(f"Error loading chat history: {e}")
            return []
    
    def clear_history(self) -> None:
        """Delete the chat history file for this session."""
        try:
            if self.history_file.exists():
                self.history_file.unlink()
        except Exception as e:
            print(f"Error clearing chat history: {e}")
    
    @staticmethod
    def cleanup_old_sessions(base_path: str = "./data/sessions", days_old: int = 7) -> int:
        """
        Clean up session files older than specified days.
        
        Args:
            base_path: Base directory containing session files
            days_old: Remove files older than this many days
            
        Returns:
            Number of files deleted
        """
        try:
            from datetime import timedelta
            import time
            
            session_dir = Path(base_path)
            if not session_dir.exists():
                return 0
            
            cutoff_time = time.time() - (days_old * 86400)
            deleted = 0
            
            for file_path in session_dir.glob("*.json"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    deleted += 1
            
            return deleted
            
        except Exception as e:
            print(f"Error cleaning up old sessions: {e}")
            return 0


class InputHistoryManager:
    """Manages user input history for arrow key navigation with multi-user support."""
    
    def __init__(self, base_path: str = "./data/sessions", max_history: int = 50):
        """
        Initialize input history manager.
        
        Args:
            base_path: Base directory for storing session files
            max_history: Maximum number of inputs to remember
        """
        self.max_history = max_history
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.session_id = get_session_id()
        self.history_file = self.base_path / f"input_history_{self.session_id}.json"
    
    def add_input(self, user_input: str) -> None:
        """
        Add a user input to history for this session.
        
        Args:
            user_input: The user's input text
        """
        if not user_input or not user_input.strip():
            return
        
        try:
            history = self.load_inputs()
            
            # Remove duplicate if exists
            if user_input in history:
                history.remove(user_input)
            
            # Add to beginning
            history.insert(0, user_input)
            
            # Trim to max size
            history = history[:self.max_history]
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "session_id": self.session_id,
                    "inputs": history
                }, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error saving input history: {e}")
    
    def load_inputs(self) -> List[str]:
        """
        Load input history from disk for this session.
        
        Returns:
            List of previous inputs (newest first)
        """
        try:
            if not self.history_file.exists():
                return []
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Verify this is the correct session
            if data.get("session_id") != self.session_id:
                return []
                
            return data.get("inputs", [])
            
        except Exception as e:
            print(f"Error loading input history: {e}")
            return []
    
    def clear_inputs(self) -> None:
        """Clear all input history for this session."""
        try:
            if self.history_file.exists():
                self.history_file.unlink()
        except Exception as e:
            print(f"Error clearing input history: {e}")
