from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

class RowState(str, Enum):
    """
    Explicit states for processed rows.
    Crucial for financial safety: only RAW_VALID can be auto-conciliated.
    """
    RAW_PREVIEW = "RAW_PREVIEW"   # Raw data, unvalidated. Display only.
    RAW_PARTIAL = "RAW_PARTIAL"   # Missing critical fields (e.g. only 2 of 3). Requires correction.
    RAW_INVALID = "RAW_INVALID"   # Validation failed (e.g. bad format). Rejected.
    RAW_VALID   = "RAW_VALID"     # All fields valid + HIGH confidence. Ready for pipeline.

class ConfidenceLevel(str, Enum):
    """
    Confidence gating levels.
    """
    HIGH = "HIGH"      # ≥70% - Safe for auto-accept
    MEDIUM = "MEDIUM"  # 40-70% - Requires human review & confirmation
    LOW = "LOW"        # <40%   - Preview only, manual mapping required

class ValidationStatus(str, Enum):
    """Status of the validation process"""
    SUCCESS = "SUCCESS"
    WARNING = "WARNING" 
    ERROR = "ERROR"

@dataclass
class FieldEvidence:
    """
    Audit trail for why a column was selected.
    """
    column: str                 # Column name/letter (e.g. "C" or "monto_usd")
    confidence: float          # 0-100 score
    method: str                # NAME | CONTENT | POSITIONAL | PROFILE_MATCH
    evidence: str              # Specifics (e.g. "regex match: dd/mm/yyyy", "keyword: 'Crédito'")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "column": self.column,
            "confidence": self.confidence,
            "method": self.method,
            "evidence": self.evidence
        }

@dataclass
class ParserDecisionReport:
    """
    Structured report for auditing parser decisions.
    No raw sensitive data allowed here.
    """
    upload_id: str
    file_hash: str
    sheet: str
    header_row: int
    field_evidence: Dict[str, FieldEvidence]
    confidence_level: ConfidenceLevel
    rows_by_state: Dict[RowState, int]
    profile_matched: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "upload_id": self.upload_id,
            "file_hash": self.file_hash,
            "sheet": self.sheet,
            "header_row": self.header_row,
            "field_evidence": {k: v.to_dict() for k, v in self.field_evidence.items()},
            "confidence_level": self.confidence_level.value,
            "rows_by_state": {k.value: v for k, v in self.rows_by_state.items()},
            "profile_matched": self.profile_matched,
            "warnings": self.warnings
        }

@dataclass
class ApprovalEvent:
    """
    Audit trail for MEDIUM confidence approvals.
    Required for financial compliance.
    """
    event_id: str
    approved_by: str          # user_id of approver (Finanzas/Admin role)
    approved_at: datetime
    upload_id: str
    profile_id: str
    snapshot: Dict[str, Any]  # header_row + mapping + sample_rows_hash
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat(),
            "upload_id": self.upload_id,
            "profile_id": self.profile_id,
            "snapshot": self.snapshot
        }

@dataclass
class ParserProfile:
    """
    Stored fingerprint for known file formats.
    When matched, confidence is boosted to HIGH.
    """
    profile_id: str
    source_type: str           # YAPPY | BANCO_GENERAL | CLAVE_VISA | etc.
    bank_name: Optional[str]
    file_pattern: str          # regex for filename matching
    sheet_name: str
    header_row: int
    column_mapping: Dict[str, int]  # {"fecha": 0, "descripcion": 2, "monto": 5}
    created_by: str
    approved_at: datetime
    approval_event_id: str     # Reference to ApprovalEvent
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "source_type": self.source_type,
            "bank_name": self.bank_name,
            "file_pattern": self.file_pattern,
            "sheet_name": self.sheet_name,
            "header_row": self.header_row,
            "column_mapping": self.column_mapping,
            "created_by": self.created_by,
            "approved_at": self.approved_at.isoformat(),
            "approval_event_id": self.approval_event_id
        }
