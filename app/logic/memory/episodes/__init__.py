"""
Episodic Memory System for Logic
app/logic/memory/episodes/__init__.py

Provides Intent → Action → Outcome memory as Markdown files in Supabase Storage.
"""

from .writer import EpisodicWriter
from .reader import EpisodicReader

__all__ = ['EpisodicWriter', 'EpisodicReader']