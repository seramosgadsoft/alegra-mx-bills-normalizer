"""
Adapter to convert Excel row data into invoice analysis structure.
"""
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ExcelAdapter:
    """Adapts Excel data to the structure expected by the invoice processor."""
    
    # Placeholder for account name - user didn't provide it
    DEFAULT_ACCOUNT_NAME = "Mensajería y paquetería" 
    
    @staticmethod
    def to_analyzed_data(excel_data: Dict[str, Any], account_name: str = None) -> Dict[str, Any]:
        """
        Convert Excel row data to analyzed_data structure.
        
        Args:
            excel_data: Dictionary extracted from Excel
            account_name: Name of the accounting account to use
            
        Returns:
            Dictionary matching the structure of Invoice Analyzer output
        """
        # Format date
        date_val = excel_data.get("date")
        formatted_date = None
        if isinstance(date_val, datetime):
            formatted_date = date_val.strftime("%Y-%m-%d")
        else:
            # Try to parse string or leave as is (format_utils might handle it)
            formatted_date = str(date_val) if date_val else None

        # Build items list (single item representing the invoice total)
        # We don't have item details in Excel, so we create one generic item
        subtotal = excel_data.get("subtotal", 0.0)
        
        # Calculate quantity and unit price (1 item)
        item = {
            "description": str(excel_data.get("corte_de_pago", "")),
            "quantity": 1,
            "unit_price": subtotal,
            "total": subtotal,
            "discount": 0,
            "tax_rate": 16.0 if excel_data.get("iva", 0) > 0 else 0.0
        }
        
        # Construct taxes list
        taxes = []
        if excel_data.get("iva", 0) > 0:
            taxes.append({
                "name": "IVA",
                "rate": 16.0,
                "amount": excel_data.get("iva"),
                "type": "transfer"
            })
            
        if excel_data.get("isr", 0) > 0:
            taxes.append({
                "name": "ISR",
                "rate": 0.0, # Rate calculated from amount/base usually, or handled by mapping
                "amount": excel_data.get("isr"),
                "type": "retention"
            })

        return {
            "document_data": {
                "document_information": {
                    "document_id": excel_data.get("uuid"), # Use UUID as document number per requirement? 
                                                         # Or should we look for Folio? 
                                                         # User said "el uuid en la columna AK" and normally we search XML by UUID.
                                                         # In Alegra usually we use Folio as number, but here we might use UUID if Folio is missing.
                                                         # Let's use UUID as document_id for now as it's the unique identifier we have.
                    "total": excel_data.get("total"),
                    "subtotal": subtotal,
                    "document_date": formatted_date,
                    "total_tax": excel_data.get("iva", 0) - excel_data.get("isr", 0),
                    "currency": "MXN", # Assumption
                    "cufe": excel_data.get("uuid") # Store UUID here too
                },
                "issuer": {
                    "id_issuer": excel_data.get("rfc"),
                    "name": "Unknown from Excel" # We verify by RFC in Alegra anyway
                },
                "items": [item],
                "taxes": taxes
            },
            # Extra fields used by format_invoice or Alegra service
            "account_name_override": account_name or ExcelAdapter.DEFAULT_ACCOUNT_NAME
        }
