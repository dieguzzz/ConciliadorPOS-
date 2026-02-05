"""
Parser Profiles - Sistema de fingerprinting para formatos conocidos.

Cuando un archivo MEDIUM confidence es aprobado por un usuario con rol Finanzas/Admin,
se guarda un ParserProfile. Próximos archivos que matchean el profile suben a HIGH.
"""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from app.utils.parser_types import (
    ParserProfile,
    ApprovalEvent,
    ConfidenceLevel,
    FieldEvidence
)


# Directorio para almacenar profiles (en producción usar DB)
PROFILES_DIR = Path(__file__).parent.parent / "data" / "parser_profiles"


def compute_file_hash(content: bytes) -> str:
    """
    Calcula hash SHA256 del contenido del archivo.
    """
    return hashlib.sha256(content).hexdigest()


def compute_sample_hash(sample_rows: List[Dict]) -> str:
    """
    Calcula hash de las primeras filas para fingerprinting.
    """
    sample_str = json.dumps(sample_rows, sort_keys=True, default=str)
    return hashlib.sha256(sample_str.encode()).hexdigest()[:16]


def match_filename_pattern(filename: str, pattern: str) -> bool:
    """
    Verifica si un nombre de archivo matchea un patrón regex.
    """
    try:
        return bool(re.match(pattern, filename, re.IGNORECASE))
    except re.error:
        return False


class ParserProfileStore:
    """
    Almacén de perfiles de parser.
    En producción, esto debería usar una base de datos.
    """
    
    def __init__(self, profiles_dir: Optional[Path] = None):
        self.profiles_dir = profiles_dir or PROFILES_DIR
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self._profiles_cache: Dict[str, ParserProfile] = {}
        self._load_profiles()
    
    def _load_profiles(self) -> None:
        """Carga perfiles desde disco."""
        for profile_file in self.profiles_dir.glob("*.json"):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    profile = ParserProfile(
                        profile_id=data["profile_id"],
                        source_type=data["source_type"],
                        bank_name=data.get("bank_name"),
                        file_pattern=data["file_pattern"],
                        sheet_name=data["sheet_name"],
                        header_row=data["header_row"],
                        column_mapping=data["column_mapping"],
                        created_by=data["created_by"],
                        approved_at=datetime.fromisoformat(data["approved_at"]),
                        approval_event_id=data["approval_event_id"]
                    )
                    self._profiles_cache[profile.profile_id] = profile
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading profile {profile_file}: {e}")
    
    def find_matching_profile(
        self,
        filename: str,
        sheet_name: str,
        header_row: int,
        column_mapping: Dict[str, int]
    ) -> Optional[ParserProfile]:
        """
        Busca un profile que matchee con los parámetros dados.
        
        Args:
            filename: Nombre del archivo
            sheet_name: Nombre de la hoja
            header_row: Fila del header detectada
            column_mapping: Mapeo de columnas detectado
            
        Returns:
            ParserProfile si hay match, None si no
        """
        for profile in self._profiles_cache.values():
            # Check filename pattern
            if not match_filename_pattern(filename, profile.file_pattern):
                continue
            
            # Check sheet name (case-insensitive)
            if profile.sheet_name.lower() != sheet_name.lower():
                continue
            
            # Check header row (allow ±1 tolerance)
            if abs(profile.header_row - header_row) > 1:
                continue
            
            # Check column mapping (at least same number of columns)
            if set(profile.column_mapping.keys()) != set(column_mapping.keys()):
                continue
            
            # Profile matches!
            return profile
        
        return None
    
    def save_profile(self, profile: ParserProfile) -> None:
        """
        Guarda un profile en disco y cache.
        """
        profile_path = self.profiles_dir / f"{profile.profile_id}.json"
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
        self._profiles_cache[profile.profile_id] = profile
    
    def list_profiles(self, source_type: Optional[str] = None) -> List[ParserProfile]:
        """
        Lista todos los profiles, opcionalmente filtrados por source_type.
        """
        profiles = list(self._profiles_cache.values())
        if source_type:
            profiles = [p for p in profiles if p.source_type == source_type]
        return profiles


class ApprovalEventStore:
    """
    Almacén de eventos de aprobación para auditoría.
    """
    
    def __init__(self, events_dir: Optional[Path] = None):
        self.events_dir = events_dir or (PROFILES_DIR.parent / "approval_events")
        self.events_dir.mkdir(parents=True, exist_ok=True)
    
    def save_event(self, event: ApprovalEvent) -> None:
        """
        Guarda un evento de aprobación.
        """
        event_path = self.events_dir / f"{event.event_id}.json"
        with open(event_path, 'w', encoding='utf-8') as f:
            json.dump(event.to_dict(), f, indent=2, ensure_ascii=False)
    
    def get_event(self, event_id: str) -> Optional[ApprovalEvent]:
        """
        Recupera un evento de aprobación por ID.
        """
        event_path = self.events_dir / f"{event_id}.json"
        if not event_path.exists():
            return None
        
        try:
            with open(event_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return ApprovalEvent(
                    event_id=data["event_id"],
                    approved_by=data["approved_by"],
                    approved_at=datetime.fromisoformat(data["approved_at"]),
                    upload_id=data["upload_id"],
                    profile_id=data["profile_id"],
                    snapshot=data["snapshot"]
                )
        except (json.JSONDecodeError, KeyError):
            return None


def create_profile_from_approval(
    source_type: str,
    filename: str,
    sheet_name: str,
    header_row: int,
    column_mapping: Dict[str, int],
    field_evidence: Dict[str, FieldEvidence],
    sample_rows: List[Dict],
    approved_by: str,
    upload_id: str,
    bank_name: Optional[str] = None
) -> tuple[ParserProfile, ApprovalEvent]:
    """
    Crea un ParserProfile y ApprovalEvent cuando un usuario aprueba un formato MEDIUM.
    
    Returns:
        Tuple of (ParserProfile, ApprovalEvent)
    """
    import uuid
    
    profile_id = str(uuid.uuid4())[:8]
    event_id = str(uuid.uuid4())
    now = datetime.now()
    
    # Generar patrón de filename basado en el nombre actual
    # Ej: "Estado_Cuenta_BGral_Enero_2025.xlsx" -> "Estado_Cuenta.*\.xlsx"
    base_name = Path(filename).stem
    extension = Path(filename).suffix
    # Simplificar a patrón básico
    pattern = f".*{extension.replace('.', '\\.')}$"
    
    # Crear snapshot para auditoría
    snapshot = {
        "header_row": header_row,
        "column_mapping": column_mapping,
        "sample_rows_hash": compute_sample_hash(sample_rows),
        "field_evidence": {k: v.to_dict() for k, v in field_evidence.items()},
        "original_filename": filename
    }
    
    # Crear ApprovalEvent
    approval_event = ApprovalEvent(
        event_id=event_id,
        approved_by=approved_by,
        approved_at=now,
        upload_id=upload_id,
        profile_id=profile_id,
        snapshot=snapshot
    )
    
    # Crear ParserProfile
    profile = ParserProfile(
        profile_id=profile_id,
        source_type=source_type,
        bank_name=bank_name,
        file_pattern=pattern,
        sheet_name=sheet_name,
        header_row=header_row,
        column_mapping=column_mapping,
        created_by=approved_by,
        approved_at=now,
        approval_event_id=event_id
    )
    
    return profile, approval_event
