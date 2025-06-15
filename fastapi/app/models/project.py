# Project models are defined in chat.py due to their close relationship with chat functionality
# This file exists to maintain the expected structure

from .chat import Project, ProjectKnowledge

__all__ = ["Project", "ProjectKnowledge"] 