"""
Processor for creating/updating providers from DRIVERS.xlsx.
"""
import logging
from typing import Dict, Any, Optional
from services.mexico_alegra_service import MexicoAlegraService
from models.models import ProviderProcessingResult, ProviderProcessingStatus

logger = logging.getLogger(__name__)


class ProviderProcessor:
    """Processor for provider upsert flow."""

    def __init__(self, alegra_service: MexicoAlegraService):
        self.alegra_service = alegra_service

    @staticmethod
    def _normalize(text: str) -> str:
        return (text or "").strip().lower()

    def process_provider_row(self, row: Dict[str, Any]) -> ProviderProcessingResult:
        rfc = (row.get("rfc") or "").strip().upper()
        name = (row.get("name") or "").strip()
        email = (row.get("email") or "").strip()
        address = (row.get("address") or "").strip()
        zip_code = (row.get("zip_code") or "").strip()
        regime = (row.get("regime") or "NO_REGIME").strip()
        phone = (row.get("phone") or "").strip()
        excel_row = row.get("excel_row")

        result = ProviderProcessingResult(
            excel_row=excel_row,
            rfc=rfc,
            name=name,
            email=email,
            address=address,
            zip_code=zip_code,
            regime=regime,
            phone=phone,
            status=ProviderProcessingStatus.ERROR,
            action="error"
        )

        if not rfc or not name:
            result.status = ProviderProcessingStatus.INVALID_DATA
            result.action = "skipped"
            result.error_message = "Missing RFC or Name"
            return result

        try:
            # 1) Search by RFC
            contact = self.alegra_service.find_contact_by_identification(rfc)

            # 2) If not found, search by Name (exact, case-insensitive)
            if not contact:
                contact = self.alegra_service.find_contact_by_name(name)

            if contact:
                update_result = self.alegra_service.update_contact_if_needed(
                    contact=contact,
                    rfc=rfc,
                    name=name,
                    email=email,
                    address=address,
                    zip_code=zip_code,
                    regime=regime,
                    phone=phone
                )
                result.alegra_contact_id = update_result.get("id")
                result.action = update_result.get("action", "updated")
                if not update_result.get("success", True) or result.action == "error":
                    result.status = ProviderProcessingStatus.ERROR
                    result.error_message = "Failed to update contact"
                else:
                    result.status = ProviderProcessingStatus.SUCCESS
                return result

            # 3) Create if not found
            created = self.alegra_service.create_contact(
                rfc=rfc,
                name=name,
                email=email,
                address=address,
                zip_code=zip_code,
                regime=regime,
                phone=phone
            )
            if not created:
                result.status = ProviderProcessingStatus.ERROR
                result.action = "error"
                result.error_message = "Failed to create contact"
                return result

            result.status = ProviderProcessingStatus.SUCCESS
            result.action = "created"
            result.alegra_contact_id = created.get("id")
            return result

        except Exception as e:
            logger.error(f"Error processing provider row {excel_row}: {e}", exc_info=True)
            result.status = ProviderProcessingStatus.ERROR
            result.action = "error"
            result.error_message = str(e)
            return result
