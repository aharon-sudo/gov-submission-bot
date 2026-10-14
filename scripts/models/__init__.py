"""Data models for the pipeline"""

from .opportunity import Qualification, OpportunityData
from .resume import Resume
from .match_result import RequirementMatch, MatchResult
from .bundle import BundleInfo

__all__ = [
    'Qualification',
    'OpportunityData',
    'Resume',
    'RequirementMatch',
    'MatchResult',
    'BundleInfo',
]
