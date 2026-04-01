"""
Data models and type definitions for the Mexico Bills Normalization system.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class ProcessingStatus(Enum):
    """Enumeration of all possible processing statuses."""
    SUCCESS = "SUCCESS"
    UUID_NOT_FOUND = "UUID_NOT_FOUND"
    MULTIPLE_FILES_FOUND = "MULTIPLE_FILES_FOUND"
    ANALYZER_ERROR = "ANALYZER_ERROR"
    PROVIDER_NOT_FOUND_ERP = "PROVIDER_NOT_FOUND_ERP"
    DUPLICATE_INVOICE = "DUPLICATE_INVOICE"
    ALEGRA_CREATE_ERROR = "ALEGRA_CREATE_ERROR"
    ATTACHMENT_ERROR = "ATTACHMENT_ERROR"
    XML_READ_ERROR = "XML_READ_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    INVALID_DATA = "INVALID_DATA"


class ProcessingSource(Enum):
    """Source of invoice data."""
    XML_FILE = "XML_FILE"
    EXCEL = "EXCEL"


class ProcessingSource(Enum):
    """Source of invoice data."""
    XML_FILE = "XML_FILE"
    EXCEL = "EXCEL"


@dataclass
class ProcessingResult:
    """Result of processing a single UUID."""
    uuid: str
    status: ProcessingStatus
    source: ProcessingSource = ProcessingSource.XML_FILE
    file_path: Optional[str] = None
    month: Optional[str] = None
    alegra_invoice_id: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    additional_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "uuid": self.uuid,
            "status": self.status.value,
            "source": self.source.value,
            "file_path": self.file_path,
            "month": self.month,
            "alegra_invoice_id": self.alegra_invoice_id,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
            **self.additional_info
        }


@dataclass
class FileSearchResult:
    """Result of searching for an XML file by UUID."""
    uuid: str
    found: bool
    file_paths: List[str] = field(default_factory=list)
    months: List[str] = field(default_factory=list)
    
    @property
    def is_unique(self) -> bool:
        """Check if exactly one file was found."""
        return len(self.file_paths) == 1
    
    @property
    def has_duplicates(self) -> bool:
        """Check if multiple files were found."""
        return len(self.file_paths) > 1
    
    @property
    def single_file_path(self) -> Optional[str]:
        """Get the single file path if unique."""
        return self.file_paths[0] if self.is_unique else None
    
    @property
    def single_month(self) -> Optional[str]:
        """Get the single month if unique."""
        return self.months[0] if self.is_unique else None


@dataclass
class ReportSummary:
    """Summary statistics for the processing report."""
    total_uuids: int = 0
    successful: int = 0
    failed: int = 0
    not_found: int = 0
    multiple_files: int = 0
    provider_not_found: int = 0
    duplicate_invoice: int = 0
    analyzer_error: int = 0
    alegra_error: int = 0
    other_errors: int = 0
    
    def to_dict(self) -> Dict[str, int]:
        """Convert the summary to a dictionary."""
        return {
            "total_uuids": self.total_uuids,
            "successful": self.successful,
            "failed": self.failed,
            "not_found": self.not_found,
            "multiple_files": self.multiple_files,
            "provider_not_found": self.provider_not_found,
            "duplicate_invoice": self.duplicate_invoice,
            "analyzer_error": self.analyzer_error,
            "alegra_error": self.alegra_error,
            "other_errors": self.other_errors
        }


class ProviderProcessingStatus(Enum):
    """Statuses for provider/driver processing."""
    SUCCESS = "SUCCESS"
    INVALID_DATA = "INVALID_DATA"
    ERROR = "ERROR"


@dataclass
class ProviderProcessingResult:
    """Result of processing a single provider row."""
    excel_row: int
    rfc: str
    name: str
    email: str
    address: str
    status: ProviderProcessingStatus
    action: str
    zip_code: str = ""
    regime: str = "NO_REGIME"
    phone: str = ""
    alegra_contact_id: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    additional_info: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "excel_row": self.excel_row,
            "rfc": self.rfc,
            "name": self.name,
            "email": self.email,
            "address": self.address,
            "zip_code": self.zip_code,
            "regime": self.regime,
            "phone": self.phone,
            "status": self.status.value,
            "action": self.action,
            "alegra_contact_id": self.alegra_contact_id,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
            **self.additional_info
        }


@dataclass
class ProviderReportSummary:
    """Summary statistics for provider processing."""
    total_rows: int = 0
    processed_ok: int = 0
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    invalid_data: int = 0
    errors: int = 0

    def to_dict(self) -> Dict[str, int]:
        return {
            "total_rows": self.total_rows,
            "processed_ok": self.processed_ok,
            "created": self.created,
            "updated": self.updated,
            "unchanged": self.unchanged,
            "invalid_data": self.invalid_data,
            "errors": self.errors
        }
