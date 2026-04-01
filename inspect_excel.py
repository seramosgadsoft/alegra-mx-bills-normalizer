import pandas as pd
import sys

try:
    file_path = "NIVELACION CHAZKI MX.xlsx"
    sheet_name = "PURCHASE - INVOICE"
    
    # Read the excel file
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
    
    # Print first few rows to identify headers and data
    print(df.head(10))
    
    # Check specific columns mentioned
    # E is index 4, AK is 36, AM is 38, AO is 40, AN is 39, AI is 34, AT is 45 (0-indexed)
    # Let's print row 2 (index 1) assuming row 1 is header
    
except Exception as e:
    print(f"Error reading excel: {e}")
