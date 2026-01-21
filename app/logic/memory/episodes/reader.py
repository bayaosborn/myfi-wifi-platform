"""
Episodic Reader - Reads episodic memory from Supabase Storage
app/logic/memory/episodes/reader.py

Supports:
- Time-based filtering (today, yesterday, last_week)
- Intent-based filtering (call, email, sms, order-gas, etc.)
- Time-of-day filtering (morning, afternoon, evening)
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pytz
import re

from app.backend.supabase_client import supabase


class EpisodicReader:
    """
    Reads episodic memory from Supabase Storage
    
    Filters episodes by intent, time scope, and time of day
    """
    
    BUCKET_NAME = 'episodic-memory'
    
    def __init__(self, user_id: str):
        """
        Initialize reader for a specific user
        
        Args:
            user_id: User's UUID
        """
        self.user_id = user_id
        self.eat_tz = pytz.timezone('Africa/Nairobi')
    
    def read_recent_episodes(
        self,
        intent_filter: Optional[str] = None,
        time_scope: str = 'today',
        time_of_day: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Read recent episodes with optional filtering
        
        Args:
            intent_filter: Filter by intent (call, email, sms, order-gas, etc.)
            time_scope: Time range (today, yesterday, last_week, all)
            time_of_day: Filter by time (morning, afternoon, evening, night)
            limit: Maximum episodes to return
            
        Returns:
            List of episode dictionaries with parsed data
        
        Example:
            reader.read_recent_episodes(
                intent_filter='call',
                time_scope='yesterday',
                time_of_day='evening',
                limit=5
            )
        """
        try:
            # 1. Determine date range
            date_range = self._get_date_range(time_scope)
            
            # 2. List all files in date range
            all_files = self._list_files_in_range(date_range)
            
            # 3. Filter by intent
            if intent_filter:
                filtered_files = [
                    f for f in all_files 
                    if f'_{intent_filter}.md' in f['name']
                ]
            else:
                filtered_files = all_files
            
            # 4. Filter by time of day
            if time_of_day:
                filtered_files = self._filter_by_time_of_day(
                    filtered_files, 
                    time_of_day
                )
            
            # 5. Sort by timestamp (newest first)
            filtered_files = sorted(
                filtered_files,
                key=lambda x: x['name'],
                reverse=True
            )[:limit]
            
            # 6. Download and parse episodes
            episodes = []
            for file_info in filtered_files:
                episode = self._parse_episode_file(file_info)
                if episode:
                    episodes.append(episode)
            
            print(f"✅ Read {len(episodes)} episodes (intent={intent_filter}, scope={time_scope})")
            
            return episodes
            
        except Exception as e:
            print(f"❌ EpisodicReader error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def search_episodes(
        self,
        query: str,
        intent_filter: Optional[str] = None,
        time_scope: str = 'all',
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search episodes by content
        
        Args:
            query: Search query (searches in target, action, metadata)
            intent_filter: Filter by intent
            time_scope: Time range
            limit: Max results
            
        Returns:
            List of matching episodes
        """
        try:
            # Get episodes in time range
            episodes = self.read_recent_episodes(
                intent_filter=intent_filter,
                time_scope=time_scope,
                limit=100  # Get more for searching
            )
            
            # Filter by query
            query_lower = query.lower()
            matching = []
            
            for episode in episodes:
                # Search in target, action, and metadata
                searchable_text = ' '.join([
                    str(episode.get('target', '')),
                    str(episode.get('action', '')),
                    str(episode.get('metadata', {}))
                ]).lower()
                
                if query_lower in searchable_text:
                    matching.append(episode)
            
            return matching[:limit]
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def get_context_for_recall(
        self,
        user_query: str
    ) -> str:
        """
        Get contextual episodes for a recall query
        
        Args:
            user_query: User's recall question
                       e.g., "Who did I call yesterday evening?"
        
        Returns:
            Formatted context string for Logic
        """
        try:
            # Parse query to extract intent, time scope, time of day
            intent = self._extract_intent_from_query(user_query)
            time_scope = self._extract_time_scope_from_query(user_query)
            time_of_day = self._extract_time_of_day_from_query(user_query)
            
            # Get relevant episodes
            episodes = self.read_recent_episodes(
                intent_filter=intent,
                time_scope=time_scope,
                time_of_day=time_of_day,
                limit=5
            )
            
            if not episodes:
                return "No matching episodes found in memory."
            
            # Format as context
            context_lines = ["## Recent Episodes:"]
            
            for ep in episodes:
                context_lines.append(
                    f"- **{ep['date']} {ep['time']}**: {ep['intent'].title()} - "
                    f"{ep['target'] or 'Unknown'} ({ep['outcome']})"
                )
            
            return "\n".join(context_lines)
            
        except Exception as e:
            print(f"❌ Context generation error: {e}")
            return "Unable to retrieve memory context."
    
    # ==================== HELPER METHODS ====================
    
    def _get_date_range(self, time_scope: str) -> List[str]:
        """
        Get list of dates to search based on time scope
        
        Returns:
            List of date strings (YYYY-MM-DD)
        """
        now = datetime.now(self.eat_tz)
        
        if time_scope == 'today':
            return [now.strftime('%Y-%m-%d')]
        
        elif time_scope == 'yesterday':
            yesterday = now - timedelta(days=1)
            return [yesterday.strftime('%Y-%m-%d')]
        
        elif time_scope == 'last_week':
            dates = []
            for i in range(7):
                date = now - timedelta(days=i)
                dates.append(date.strftime('%Y-%m-%d'))
            return dates
        
        elif time_scope == 'last_month':
            dates = []
            for i in range(30):
                date = now - timedelta(days=i)
                dates.append(date.strftime('%Y-%m-%d'))
            return dates
        
        else:  # 'all'
            # Just search current month for now
            # (Could expand to full year if needed)
            dates = []
            for i in range(30):
                date = now - timedelta(days=i)
                dates.append(date.strftime('%Y-%m-%d'))
            return dates
    
    def _list_files_in_range(
        self, 
        dates: List[str]
    ) -> List[Dict[str, Any]]:
        """
        List all episode files within date range
        
        Args:
            dates: List of date strings
            
        Returns:
            List of file info dicts from storage
        """
        all_files = []
        
        for date_str in dates:
            # Extract year and month from date
            year = date_str[:4]
            month = date_str[5:7]
            
            # Build path
            path = f"users/{self.user_id}/{year}/{month}"
            
            # List files
            files = supabase.list_files(
                bucket=self.BUCKET_NAME,
                path=path,
                limit=1000
            )
            
            # Filter for this specific date
            date_files = [
                f for f in files 
                if f['name'].startswith(date_str)
            ]
            
            all_files.extend(date_files)
        
        return all_files
    
    def _filter_by_time_of_day(
        self,
        files: List[Dict[str, Any]],
        time_of_day: str
    ) -> List[Dict[str, Any]]:
        """
        Filter files by time of day
        
        Args:
            files: List of file info
            time_of_day: 'morning', 'afternoon', 'evening', 'night'
        
        Returns:
            Filtered file list
        """
        time_ranges = {
            'morning': (6, 12),    # 06:00 - 11:59
            'afternoon': (12, 17), # 12:00 - 16:59
            'evening': (17, 21),   # 17:00 - 20:59
            'night': (21, 6)       # 21:00 - 05:59
        }
        
        if time_of_day not in time_ranges:
            return files
        
        start_hour, end_hour = time_ranges[time_of_day]
        
        filtered = []
        for file_info in files:
            # Extract hour from filename
            # Example: 2026-01-20_T15-30-45+0300_call.md
            filename = file_info['name']
            match = re.search(r'_T(\d{2})-\d{2}-\d{2}', filename)
            
            if match:
                hour = int(match.group(1))
                
                # Handle night wrap-around
                if time_of_day == 'night':
                    if hour >= 21 or hour < 6:
                        filtered.append(file_info)
                else:
                    if start_hour <= hour < end_hour:
                        filtered.append(file_info)
        
        return filtered
    
    def _parse_episode_file(
        self, 
        file_info: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Download and parse episode file
        
        Args:
            file_info: File metadata from storage
        
        Returns:
            Parsed episode dict or None if failed
        """
        try:
            # Build full path
            filename = file_info['name']
            
            # Extract year/month from filename
            date_part = filename.split('_')[0]
            year = date_part[:4]
            month = date_part[5:7]
            
            path = f"users/{self.user_id}/{year}/{month}/{filename}"
            
            # Download file
            content = supabase.download_file(
                bucket=self.BUCKET_NAME,
                path=path
            )
            
            if not content:
                return None
            
            # Parse filename
            parsed = self._parse_filename(filename)
            
            # Parse Markdown content
            parsed_content = self._parse_markdown(content)
            
            # Merge
            episode = {**parsed, **parsed_content}
            
            return episode
            
        except Exception as e:
            print(f"⚠️ Failed to parse episode {file_info.get('name')}: {e}")
            return None
    
    def _parse_filename(self, filename: str) -> Dict[str, Any]:
        """
        Parse episode filename
        
        Example: 2026-01-20_T15-30-45+0300_call.md
        
        Returns:
            {
                'date': '2026-01-20',
                'time': '15:30:45',
                'timezone': '+0300',
                'intent': 'call',
                'filename': '...'
            }
        """
        parts = filename.replace('.md', '').split('_')
        
        if len(parts) >= 3:
            date = parts[0]
            time_part = parts[1].replace('T', '')
            time_formatted = time_part[:2] + ':' + time_part[3:5] + ':' + time_part[6:8]
            timezone = time_part[8:] if len(time_part) > 8 else '+0300'
            intent = parts[2]
            
            return {
                'date': date,
                'time': time_formatted,
                'timezone': timezone,
                'intent': intent,
                'filename': filename
            }
        
        return {
            'date': 'unknown',
            'time': 'unknown',
            'timezone': '+0300',
            'intent': 'unknown',
            'filename': filename
        }
    
    def _parse_markdown(self, content: str) -> Dict[str, Any]:
        """
        Parse Markdown content to extract episode data
        
        Returns:
            {
                'action': '...',
                'outcome': '...',
                'target': '...',
                'target_phone': '...',
                'metadata': {...}
            }
        """
        result = {
            'action': None,
            'outcome': None,
            'target': None,
            'target_phone': None,
            'target_email': None,
            'metadata': {}
        }
        
        # Extract fields using regex
        action_match = re.search(r'\*\*Action\*\*:\s*(.+)', content)
        if action_match:
            result['action'] = action_match.group(1).strip()
        
        outcome_match = re.search(r'\*\*Outcome\*\*:\s*(.+)', content)
        if outcome_match:
            result['outcome'] = outcome_match.group(1).strip()
        
        target_match = re.search(r'\*\*Target\*\*:\s*(.+)', content)
        if target_match:
            result['target'] = target_match.group(1).strip()
        
        phone_match = re.search(r'\*\*Phone\*\*:\s*(.+)', content)
        if phone_match:
            result['target_phone'] = phone_match.group(1).strip()
        
        email_match = re.search(r'\*\*Email\*\*:\s*(.+)', content)
        if email_match:
            result['target_email'] = email_match.group(1).strip()
        
        # Extract metadata section
        metadata_section = re.search(
            r'## Additional Context\n(.+?)(?=---|\Z)', 
            content, 
            re.DOTALL
        )
        
        if metadata_section:
            metadata_text = metadata_section.group(1)
            # Parse metadata lines
            for line in metadata_text.split('\n'):
                if '**' in line:
                    match = re.search(r'\*\*(.+?)\*\*:\s*(.+)', line)
                    if match:
                        key = match.group(1).strip().lower().replace(' ', '_')
                        value = match.group(2).strip()
                        result['metadata'][key] = value
        
        return result
    
    def _extract_intent_from_query(self, query: str) -> Optional[str]:
        """Extract intent from user query"""
        query_lower = query.lower()
        
        intents = {
            'call': ['call', 'called', 'phone'],
            'email': ['email', 'emailed', 'sent email'],
            'sms': ['text', 'sms', 'message', 'texted'],
            'order-gas': ['gas', 'order gas', 'refill'],
            'order-ride': ['ride', 'taxi', 'uber']
        }
        
        for intent, keywords in intents.items():
            if any(kw in query_lower for kw in keywords):
                return intent
        
        return None
    
    def _extract_time_scope_from_query(self, query: str) -> str:
        """Extract time scope from user query"""
        query_lower = query.lower()
        
        if 'today' in query_lower or 'this morning' in query_lower or 'this afternoon' in query_lower:
            return 'today'
        elif 'yesterday' in query_lower:
            return 'yesterday'
        elif 'last week' in query_lower or 'past week' in query_lower:
            return 'last_week'
        elif 'last month' in query_lower:
            return 'last_month'
        else:
            return 'last_week'  # Default
    
    def _extract_time_of_day_from_query(self, query: str) -> Optional[str]:
        """Extract time of day from user query"""
        query_lower = query.lower()
        
        if 'morning' in query_lower:
            return 'morning'
        elif 'afternoon' in query_lower:
            return 'afternoon'
        elif 'evening' in query_lower:
            return 'evening'
        elif 'night' in query_lower:
            return 'night'
        else:
            return None


# Factory function
def get_episodic_reader(user_id: str) -> EpisodicReader:
    """Get episodic reader instance for user"""
    return EpisodicReader(user_id)