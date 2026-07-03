"""
Excel loader for reading invoice data from XLSX files.
"""
import pandas as pd
import logging
from typing import List, Dict, Any
import os

logger = logging.getLogger(__name__)

class ExcelLoader:
    """Loads invoice data from Excel files."""
    
    # Column indices (0-based) based on requirements
    # E: Index 4 (RFC)
    # B: Index 1 (CORTE DE PAGO)
    # AI: Index 34 (IVA 16%)
    # AK: Index 36 (UUID)
    # AM: Index 38 (Date)
    # AN: Index 39 (Subtotal)
    # AO: Index 40 (Total)
    # AP: Index 41 (Retención ISR)
    # AQ: Index 42 (Retención IVA)
    # AT: Index 45 (ISR Retention - legacy, ya no se usa para retención)

    COL_RFC = 4      # E
    COL_IVA = 34     # AI
    COL_UUID = 36    # AK
    COL_DATE = 38    # AM
    COL_SUBTOTAL = 39 # AN
    COL_TOTAL = 40   # AO
    COL_ISR_RET = 41 # AP - monto de retención de ISR
    COL_IVA_RET = 42 # AQ - monto de retención de IVA
    COL_ISR = 45     # AT (legacy)
    
    # Row processing controls (Excel row numbers, 1-based)
    # Febrero 2026: filas 1046-1328 (283 facturas) de la hoja PURCHASE - INVOICE.
    DEFAULT_START_ROW = 1046  # Primera factura del corte de febrero
    DEFAULT_MAX_ROWS = 283  # Facturas del corte de febrero
    
    def __init__(
        self,
        file_path: str,
        sheet_name: str = "PURCHASE - INVOICE",
        start_row: int = None,
        max_rows: int = None,
    ):
        """
        Initialize the Excel loader.
        
        Args:
            file_path: Path to the Excel file
            sheet_name: Name of the sheet to read
            start_row: Excel row number to start processing (1-based)
            max_rows: Maximum number of rows (invoices) to process
        """
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.start_row = start_row if start_row is not None else self.DEFAULT_START_ROW
        self.max_rows = max_rows if max_rows is not None else self.DEFAULT_MAX_ROWS
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Excel file not found: {file_path}")
            
    def load_invoices(self) -> List[Dict[str, Any]]:
        """
        Load invoices from the Excel file.
        
        Returns:
            List of dictionaries containing invoice data
        """
        try:
            logger.info(f"Loading Excel file: {self.file_path}, Sheet: {self.sheet_name}")
            
            # Read Excel file (no header because we use specific indices)
            # We skip the first row (header) manually if needed, or pandas does it.
            # Assuming row 1 is header, data starts at row 2.
            df = pd.read_excel(self.file_path, sheet_name=self.sheet_name, header=None)
            
            invoices = []
            skipped_count = 0
            
            # Iterate through rows, skipping the header (row 0)
            processed_count = 0
            for index, row in df.iterrows():
                if index == 0:  # Skip header
                    continue
                
                # Excel row number is index + 1
                excel_row_num = index + 1
                if excel_row_num < self.start_row:
                    continue
                if self.max_rows is not None and processed_count >= self.max_rows:
                    break
                    
                # Extract data safely
                try:
                    uuid = str(row[self.COL_UUID]).strip() if pd.notna(row[self.COL_UUID]) else ""
                    
                    # Validation for valid UUIDs
                    # If invalid, we still keep it but mark it so Processor can report it
                    if not uuid:
                        # Use a recognizable placeholder so it can be reported
                        uuid = f"INVALID_UUID_ROW_{index + 1}"
                        # We don't skip anymore, we process it to report failure
                        
                    invoice_data = {
                        "uuid": uuid.upper(),
                        "rfc": str(row[self.COL_RFC]).strip() if pd.notna(row[self.COL_RFC]) else "",
                        "corte_de_pago": str(row[self.COL_CORTE_PAGO]) if pd.notna(row[self.COL_CORTE_PAGO]) else "",
                        "date": row[self.COL_DATE],
                        "subtotal": float(row[self.COL_SUBTOTAL]) if pd.notna(row[self.COL_SUBTOTAL]) else 0.0,
                        "total": float(row[self.COL_TOTAL]) if pd.notna(row[self.COL_TOTAL]) else 0.0,
                        "iva": float(row[self.COL_IVA]) if pd.notna(row[self.COL_IVA]) else 0.0,
                        "isr": float(row[self.COL_ISR]) if pd.notna(row[self.COL_ISR]) else 0.0,
                        # Retenciones: ISR en columna AP, IVA en columna AQ
                        "isr_ret": float(row[self.COL_ISR_RET]) if pd.notna(row[self.COL_ISR_RET]) else 0.0,
                        "iva_ret": float(row[self.COL_IVA_RET]) if pd.notna(row[self.COL_IVA_RET]) else 0.0,
                        # Store original row index for reference (excel row is index + 1)
                        "excel_row": index + 1
                    }
                    
                    invoices.append(invoice_data)
                    processed_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error parsing row {index + 1}: {e}")
                    skipped_count += 1
            
            logger.info(f"Loaded {len(invoices)} invoices from Excel. Skipped {skipped_count} rows.")
            return invoices
            
        except Exception as e:
            logger.error(f"Error processing Excel file: {e}", exc_info=True)
            raise
    COL_CORTE_PAGO = 1  # B
