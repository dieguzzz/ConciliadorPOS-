"""
Servicio de idempotencia para prevenir procesamiento duplicado de uploads.

Cada upload genera:
- upload_id: UUID único
- file_hash: SHA256 del archivo

Si el mismo file_hash ya fue procesado, retorna el resultado anterior.
"""

import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class UploadRecord:
    """Registro de un upload procesado."""
    upload_id: str
    file_hash: str
    filename: str
    processed_at: datetime
    result_summary: Dict[str, Any]  # Resumen del resultado (sin data sensible)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "upload_id": self.upload_id,
            "file_hash": self.file_hash,
            "filename": self.filename,
            "processed_at": self.processed_at.isoformat(),
            "result_summary": self.result_summary
        }


class IdempotencyService:
    """
    Servicio para garantizar idempotencia en uploads.
    Previene procesamiento duplicado del mismo archivo.
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path(__file__).parent.parent / "data" / "upload_records"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._hash_index: Dict[str, str] = {}  # file_hash -> upload_id
        self._load_index()
    
    def _load_index(self) -> None:
        """Carga índice de hashes desde disco."""
        index_file = self.storage_dir / "_hash_index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    self._hash_index = json.load(f)
            except json.JSONDecodeError:
                self._hash_index = {}
    
    def _save_index(self) -> None:
        """Guarda índice de hashes en disco."""
        index_file = self.storage_dir / "_hash_index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(self._hash_index, f, indent=2)
    
    def compute_hash(self, content: bytes) -> str:
        """Calcula SHA256 del contenido."""
        return hashlib.sha256(content).hexdigest()
    
    def generate_upload_id(self) -> str:
        """Genera un nuevo upload_id único."""
        return str(uuid.uuid4())
    
    def check_duplicate(self, file_hash: str) -> Optional[UploadRecord]:
        """
        Verifica si un archivo ya fue procesado.
        
        Returns:
            UploadRecord si existe, None si es nuevo
        """
        if file_hash not in self._hash_index:
            return None
        
        upload_id = self._hash_index[file_hash]
        record_file = self.storage_dir / f"{upload_id}.json"
        
        if not record_file.exists():
            # Índice desactualizado, limpiar
            del self._hash_index[file_hash]
            self._save_index()
            return None
        
        try:
            with open(record_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return UploadRecord(
                    upload_id=data["upload_id"],
                    file_hash=data["file_hash"],
                    filename=data["filename"],
                    processed_at=datetime.fromisoformat(data["processed_at"]),
                    result_summary=data["result_summary"]
                )
        except (json.JSONDecodeError, KeyError):
            return None
    
    def register_upload(
        self,
        upload_id: str,
        file_hash: str,
        filename: str,
        result_summary: Dict[str, Any]
    ) -> UploadRecord:
        """
        Registra un upload procesado.
        
        Args:
            upload_id: ID único del upload
            file_hash: Hash SHA256 del archivo
            filename: Nombre del archivo (sanitizado)
            result_summary: Resumen del resultado (sin data sensible)
            
        Returns:
            UploadRecord creado
        """
        record = UploadRecord(
            upload_id=upload_id,
            file_hash=file_hash,
            filename=filename,
            processed_at=datetime.now(),
            result_summary=result_summary
        )
        
        # Guardar record
        record_file = self.storage_dir / f"{upload_id}.json"
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(record.to_dict(), f, indent=2, ensure_ascii=False)
        
        # Actualizar índice
        self._hash_index[file_hash] = upload_id
        self._save_index()
        
        return record
    
    def get_or_create_upload(
        self,
        content: bytes,
        filename: str
    ) -> tuple[str, str, Optional[UploadRecord]]:
        """
        Verifica si el archivo es duplicado o genera nuevo upload_id.
        
        Returns:
            Tuple of (upload_id, file_hash, existing_record_or_none)
        """
        file_hash = self.compute_hash(content)
        existing = self.check_duplicate(file_hash)
        
        if existing:
            return existing.upload_id, file_hash, existing
        
        new_upload_id = self.generate_upload_id()
        return new_upload_id, file_hash, None
