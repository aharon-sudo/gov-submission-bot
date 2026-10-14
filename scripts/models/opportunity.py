"""Opportunity data models"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Qualification:
    """A single qualification/requirement"""
    id: str
    text: str
    category: str
    is_required: bool


@dataclass
class OpportunityData:
    """Structured opportunity data"""
    opportunity_id: str
    title: str
    agency: Optional[str]
    due_date: Optional[str]
    required_qualifications: List[Qualification]
    preferred_qualifications: List[Qualification]
    source_file: str

    def all_qualifications(self) -> List[Qualification]:
        """Get all qualifications (required + preferred)"""
        return self.required_qualifications + self.preferred_qualifications

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'opportunity_id': self.opportunity_id,
            'title': self.title,
            'agency': self.agency,
            'due_date': self.due_date,
            'required_qualifications': [
                {
                    'id': q.id,
                    'text': q.text,
                    'category': q.category,
                    'is_required': q.is_required
                }
                for q in self.required_qualifications
            ],
            'preferred_qualifications': [
                {
                    'id': q.id,
                    'text': q.text,
                    'category': q.category,
                    'is_required': q.is_required
                }
                for q in self.preferred_qualifications
            ],
            'source_file': self.source_file
        }

    @staticmethod
    def from_dict(data: dict) -> 'OpportunityData':
        """Create from dictionary"""
        return OpportunityData(
            opportunity_id=data['opportunity_id'],
            title=data['title'],
            agency=data.get('agency'),
            due_date=data.get('due_date'),
            required_qualifications=[
                Qualification(**q) for q in data.get('required_qualifications', [])
            ],
            preferred_qualifications=[
                Qualification(**q) for q in data.get('preferred_qualifications', [])
            ],
            source_file=data.get('source_file', '')
        )
