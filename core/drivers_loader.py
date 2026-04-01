"""
Excel loader for reading provider data from DRIVERS.xlsx.
"""
import pandas as pd
import logging
from typing import List, Dict, Any, Optional
import os
import re

logger = logging.getLogger(__name__)


# Mapping from Excel regime names to Alegra API regime codes
REGIME_MAPPING = {
    "régimen general de ley personas morales": "GENERAL_REGIME_OF_MORAL_PEOPLE_LAW",
    "régimen simplificado de confianza": "REGIME_OF_TRUST",
    "régimen de incorporación fiscal": "SIMPLIFIED_REGIME",
    # These don't have exact matches, default to NO_REGIME
    "régimen de las personas físicas con actividades empresariales y profesionales": "NO_REGIME",
    "régimen de las actividades empresariales con ingresos a través de plataformas tecnológicas": "NO_REGIME",
    "régimen de sueldos y salarios e ingresos asimilados a salarios": "NO_REGIME",
}

DEFAULT_REGIME = "NO_REGIME"


def normalize_regime(regime_text: str) -> str:
    """
    Normalize regime text from Excel to Alegra API code.
    
    Args:
        regime_text: Raw regime text from Excel
        
    Returns:
        Alegra API regime code
    """
    if not regime_text:
        return DEFAULT_REGIME
    
    # Clean the text: lowercase, strip whitespace and quotes
    cleaned = regime_text.strip().lower()
    cleaned = cleaned.strip('"').strip()
    
    # Try exact match first
    if cleaned in REGIME_MAPPING:
        return REGIME_MAPPING[cleaned]
    
    # Try partial match
    for excel_regime, api_regime in REGIME_MAPPING.items():
        if excel_regime in cleaned or cleaned in excel_regime:
            return api_regime
    
    logger.warning(f"Unknown regime '{regime_text}', defaulting to {DEFAULT_REGIME}")
    return DEFAULT_REGIME


def normalize_phone(phone_text: str) -> str:
    """
    Normalize phone number - keep only digits.
    
    Args:
        phone_text: Raw phone text from Excel
        
    Returns:
        Cleaned phone number (digits only)
    """
    if not phone_text:
        return ""
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', str(phone_text))
    return digits_only


class DriversLoader:
    """Loads provider data from DRIVERS.xlsx."""

    # Column indices (0-based) for "Hoja 1" sheet
    # A: RFC, B: Nombre/Razon social, C: Correo, D: Direccion
    # E: Codigo postal, F: Regimen, G: Telefono
    COL_RFC = 0       # A
    COL_NAME = 1      # B
    COL_EMAIL = 2     # C
    COL_ADDRESS = 3   # D
    COL_ZIP_CODE = 4  # E
    COL_REGIME = 5    # F
    COL_PHONE = 6     # G

    DEFAULT_SHEET = "Hoja 1"

    def __init__(self, file_path: str, sheet_name: str = None):
        self.file_path = file_path
        self.sheet_name = sheet_name or self.DEFAULT_SHEET
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Excel file not found: {file_path}")

    def load_drivers(self) -> List[Dict[str, Any]]:
        """Load providers from the Excel file."""
        try:
            logger.info(f"Loading DRIVERS Excel: {self.file_path}, Sheet: {self.sheet_name}")
            df = pd.read_excel(self.file_path, sheet_name=self.sheet_name, header=None)
            drivers: List[Dict[str, Any]] = []

            for index, row in df.iterrows():
                if index == 0:
                    # Skip header row
                    continue

                excel_row = index + 1
                rfc = str(row[self.COL_RFC]).strip() if pd.notna(row[self.COL_RFC]) else ""
                name = str(row[self.COL_NAME]).strip() if pd.notna(row[self.COL_NAME]) else ""
                email = str(row[self.COL_EMAIL]).strip() if pd.notna(row[self.COL_EMAIL]) else ""
                address = str(row[self.COL_ADDRESS]).strip() if pd.notna(row[self.COL_ADDRESS]) else ""
                zip_code = str(row[self.COL_ZIP_CODE]).strip() if pd.notna(row[self.COL_ZIP_CODE]) else ""
                regime_raw = str(row[self.COL_REGIME]).strip() if pd.notna(row[self.COL_REGIME]) else ""
                phone_raw = str(row[self.COL_PHONE]).strip() if pd.notna(row[self.COL_PHONE]) else ""

                # Normalize regime and phone
                regime = normalize_regime(regime_raw)
                phone = normalize_phone(phone_raw)

                # Clean zip code (remove .0 if it came from Excel as number)
                if zip_code.endswith('.0'):
                    zip_code = zip_code[:-2]

                drivers.append(
                    {
                        "excel_row": excel_row,
                        "rfc": rfc,
                        "name": name,
                        "email": email,
                        "address": address,
                        "zip_code": zip_code,
                        "regime": regime,
                        "phone": phone,
                    }
                )

            logger.info(f"Loaded {len(drivers)} provider rows from DRIVERS.xlsx")
            return drivers
        except Exception as e:
            logger.error(f"Error processing DRIVERS Excel file: {e}", exc_info=True)
            raise
