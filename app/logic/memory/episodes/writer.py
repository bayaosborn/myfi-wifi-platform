"""
Episodic Writer - Writes Intent → Action → Outcome to Supabase Storage
app/logic/memory/episodes/writer.py

Creates one Markdown file per episode with naming:
{date}_{time}_{intent}.md

Example: 2026-01-19_T15-30-45+0300_call.md
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
import pytz

from app.backend.supabase_client import supabase


class EpisodicWriter:
    """
    Writes episodic memory to Supabase Storage
    
    Each episode is stored as a separate Markdown file for:
    - Atomic writes (no race conditions)
    - Intent-based filtering
    - Time-based ordering
    """
    
    BUCKET_NAME = 'episodic-memory'
    
    # Intent types (expandable)
    VALID_INTENTS = {
        'call',
        'email',
        'sms',
        'add-contact',
        'edit-contact',
        # Future intents:
        # 'order-gas',
        # 'order-ride',
        # 'order-food'
    }
    
    def __init__(self, user_id: str):
        """
        Initialize writer for a specific user
        
        Args:
            user_id: User's UUID
        """
        self.user_id = user_id
    
    def write_episode(
        self,
        intent: str,
        action: str,
        outcome: str,
        target: Optional[str] = None,
        target_phone: Optional[str] = None,
        target_email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Write a single episode to storage
        
        Args:
            intent: What user wanted (call, email, sms, order-gas, etc.)
            action: What Logic did (outbound_call_placed, email_sent, etc.)
            outcome: What happened (call_initiated, message_delivered, etc.)
            target: Who/what was targeted (contact name, merchant name)
            target_phone: Phone number (if applicable)
            target_email: Email address (if applicable)
            metadata: Additional context (optional)
        
        Returns:
            True if successful, False otherwise
        
        Example:
            writer.write_episode(
                intent='call',
                action='outbound_call_placed',
                outcome='call_initiated',
                target='Sarah Wanjiku',
                target_phone='0712345678'
            )
        """
        try:
            # Validate intent
            if intent not in self.VALID_INTENTS:
                print(f"⚠️ Unknown intent: {intent}, proceeding anyway")
            
            # Generate filename
            filename = self._generate_filename(intent)
            
            # Generate Markdown content
            content = self._generate_markdown(
                intent=intent,
                action=action,
                outcome=outcome,
                target=target,
                target_phone=target_phone,
                target_email=target_email,
                metadata=metadata
            )
            
            # Upload to Supabase Storage
            success = supabase.upload_file(
                bucket=self.BUCKET_NAME,
                path=self._get_file_path(filename),
                content=content,
                content_type='text/markdown'
            )
            
            if success:
                print(f"✅ Episode written: {filename}")
            else:
                print(f"❌ Failed to write episode: {filename}")
            
            return success
            
        except Exception as e:
            print(f"❌ EpisodicWriter error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _generate_filename(self, intent: str) -> str:
        """
        Generate filename in format: {date}_{time}_{intent}.md
        
        Example: 2026-01-19_T15-30-45+0300_call.md
        
        Args:
            intent: Episode intent type
            
        Returns:
            Formatted filename
        """
        # Get current time in EAT (UTC+3)
        eat_tz = pytz.timezone('Africa/Nairobi')
        now = datetime.now(eat_tz)
        
        # Format: 2026-01-19_T15-30-45+0300_call.md
        date_part = now.strftime('%Y-%m-%d')
        time_part = now.strftime('T%H-%M-%S%z')  # T15-30-45+0300
        
        filename = f"{date_part}_{time_part}_{intent}.md"
        
        return filename
    
    def _get_file_path(self, filename: str) -> str:
        """
        Get full path for file in storage
        
        Structure: users/{user_id}/2026/01/filename.md
        
        Args:
            filename: Generated filename
            
        Returns:
            Full storage path
        """
        # Extract year and month from filename
        # Example: 2026-01-19_T15-30-45+0300_call.md
        date_part = filename.split('_')[0]  # 2026-01-19
        year = date_part.split('-')[0]      # 2026
        month = date_part.split('-')[1]     # 01
        
        path = f"users/{self.user_id}/{year}/{month}/{filename}"
        
        return path
    
    def _generate_markdown(
        self,
        intent: str,
        action: str,
        outcome: str,
        target: Optional[str],
        target_phone: Optional[str],
        target_email: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> str:
        """
        Generate Markdown content for episode
        
        Returns human + LLM readable format
        """
        # Get current time
        eat_tz = pytz.timezone('Africa/Nairobi')
        now = datetime.now(eat_tz)
        
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')
        
        # Build markdown
        lines = [
            f"# Episode: {intent.replace('-', ' ').title()}",
            f"**Date**: {date_str}",
            f"**Time**: {time_str} EAT",
            "",
            "---",
            "",
            "## Summary",
            f"- **Intent**: {intent}",
            f"- **Action**: {action}",
            f"- **Outcome**: {outcome}",
        ]
        
        # Add target info if provided
        if target:
            lines.append(f"- **Target**: {target}")
        
        if target_phone:
            lines.append(f"- **Phone**: {target_phone}")
        
        if target_email:
            lines.append(f"- **Email**: {target_email}")
        
        # Add metadata if provided
        if metadata:
            lines.append("")
            lines.append("## Additional Context")
            for key, value in metadata.items():
                lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        
        # Footer
        lines.append("")
        lines.append("---")
        lines.append(f"*Generated by Logic Episodic Memory System*")
        
        return "\n".join(lines)


# Factory function
def get_episodic_writer(user_id: str) -> EpisodicWriter:
    """Get episodic writer instance for user"""
    return EpisodicWriter(user_id)