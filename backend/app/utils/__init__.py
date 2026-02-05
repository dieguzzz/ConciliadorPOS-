# Utils package
"""
Utility modules for the ConciliadorPOS backend.
"""

# Parser types (enums, dataclasses)
from app.utils.parser_types import (
    RowState,
    ConfidenceLevel,
    FieldEvidence,
    ParserDecisionReport,
    ApprovalEvent,
    ParserProfile,
    ValidationStatus
)

# Validators and normalizers
from app.utils.validators import (
    normalize_amount,
    normalize_date,
    clean_amount,
    clean_date,
    validate_dataframe,
    normalize_text
)

# Column detection
from app.utils.column_detector import (
    ColumnDetector,
    normalize_column_name,
    fuzzy_match_score,
    is_likely_date_column,
    is_likely_amount_column,
    is_likely_text_column
)

# File reading
from app.utils.file_reader import read_file

# Parser profiles (fingerprinting)
from app.utils.parser_profiles import (
    ParserProfileStore,
    ApprovalEventStore,
    create_profile_from_approval,
    compute_file_hash
)

# Idempotency
from app.utils.idempotency import (
    IdempotencyService,
    UploadRecord
)

__all__ = [
    # Types
    'RowState', 'ConfidenceLevel', 'FieldEvidence', 'ParserDecisionReport',
    'ApprovalEvent', 'ParserProfile', 'ValidationStatus',
    # Validators
    'normalize_amount', 'normalize_date', 'clean_amount', 'clean_date',
    'validate_dataframe', 'normalize_text',
    # Column detection
    'ColumnDetector', 'normalize_column_name', 'fuzzy_match_score',
    'is_likely_date_column', 'is_likely_amount_column', 'is_likely_text_column',
    # File reading
    'read_file',
    # Profiles
    'ParserProfileStore', 'ApprovalEventStore', 'create_profile_from_approval',
    'compute_file_hash',
    # Idempotency
    'IdempotencyService', 'UploadRecord'
]
