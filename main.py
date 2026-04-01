"""
Main entry point for Mexico Bills Normalization system (Updated for Excel Support).
"""
import logging
import sys
import os
import argparse
import warnings
from typing import List

# Suppress openpyxl warning about default style
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config_loader import ConfigLoader
from core.uuid_loader import UUIDLoader
from core.xml_file_searcher import XMLFileSearcher
from core.invoice_processor import InvoiceProcessor
from core.excel_loader import ExcelLoader
from core.drivers_loader import DriversLoader
from core.provider_processor import ProviderProcessor
from services.mexico_invoice_analyzer import MexicoInvoiceAnalyzer
from services.mexico_alegra_service import MexicoAlegraService
from utils.report_generator import ReportGenerator, ProviderReportGenerator
from models.models import ProcessingResult, ProcessingSource, ProviderProcessingResult


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mexico_normalization.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main execution function with argument parsing."""
    parser = argparse.ArgumentParser(description="Mexico Bills Normalization System")
    parser.add_argument(
        "--mode", 
        choices=["txt", "excel", "providers"], 
        default="txt",
        help="Processing mode: 'txt' for UUID list + XML Analysis, 'excel' for Excel Spreadsheet, 'providers' for DRIVERS.xlsx"
    )
    parser.add_argument(
        "--file", 
        help="Input file path (uuids.txt or excel file)",
        default=None
    )
    
    args = parser.parse_args()
    
    # Determine input file based on mode if not specified
    input_file = args.file
    if not input_file:
        if args.mode == "txt":
            input_file = "uuids.txt"
        elif args.mode == "excel":
            input_file = "NIVELACION CHAZKI MX.xlsx"
        else:  # providers
            input_file = "DRIVERS.xlsx"
    
    logger.info("="*70)
    logger.info(f"Starting Mexico Bills Normalization Process - Mode: {args.mode.upper()}")
    logger.info("="*70)
    
    try:
        # Step 1: Load configuration
        logger.info("Loading configuration...")
        config_loader = ConfigLoader("config.json")
        alegra_config = config_loader.get_alegra_config("MX")
        
        if not alegra_config or not alegra_config.get("endpoint"):
            logger.error("Mexico Alegra configuration not found in config.json")
            sys.exit(1)
            
        # Step 2: Initialize services
        logger.info("Initializing services...")
        xml_searcher = XMLFileSearcher("bills")
        analyzer = MexicoInvoiceAnalyzer()
        alegra_service = MexicoAlegraService(alegra_config)
        processor = InvoiceProcessor(analyzer, alegra_service)
        
        results: List[ProcessingResult] = []
        
        # Step 3: Process based on mode
        if args.mode == "txt":
            logger.info(f"Loading UUIDs from {input_file}...")
            uuid_loader = UUIDLoader(input_file)
            uuids = uuid_loader.load_uuids()
            
            if not uuids:
                logger.error(f"No valid UUIDs found in {input_file}")
                sys.exit(1)
            
            logger.info(f"Parsed {len(uuids)} UUIDs to process")
            
            for idx, uuid in enumerate(uuids, 1):
                logger.info(f"\n[{idx}/{len(uuids)}] Processing UUID: {uuid}")
                # Search XML
                search_result = xml_searcher.search_by_uuid(uuid)
                # Process
                result = processor.process_invoice(uuid, search_result)
                results.append(result)
                
                # Log immediate result
                if result.status.value == "SUCCESS":
                    logger.info(f"✅ SUCCESS: {uuid} → Alegra ID: {result.alegra_invoice_id}")
                else:
                    logger.warning(f"❌ {result.status.value}: {uuid} - {result.error_message}")
                    
        elif args.mode == "excel":
            logger.info(f"Loading Excel data from {input_file}...")
            excel_loader = ExcelLoader(input_file)
            invoices = excel_loader.load_invoices()
            
            if not invoices:
                logger.error("No valid invoices found in Excel file")
                sys.exit(1)
                
            logger.info(f"Loaded {len(invoices)} invoices from Excel")
            
            for idx, invoice_data in enumerate(invoices, 1):
                uuid = invoice_data.get("uuid")
                logger.info(f"\n[{idx}/{len(invoices)}] Processing Excel Row {invoice_data.get('excel_row')}: {uuid}")
                
                # Process using Excel pipeline
                result = processor.process_invoice_from_excel(invoice_data, xml_searcher)
                results.append(result)
                
                # Log immediate result
                source_indicator = "📄+📎" if result.file_path else "📄"
                if result.status.value == "SUCCESS":
                    logger.info(f"✅ SUCCESS {source_indicator}: {uuid} → Alegra ID: {result.alegra_invoice_id}")
                else:
                    logger.warning(f"❌ {result.status.value}: {uuid} - {result.error_message}")

        elif args.mode == "providers":
            logger.info(f"Loading providers from {input_file}...")
            drivers_loader = DriversLoader(input_file)
            drivers = drivers_loader.load_drivers()

            if not drivers:
                logger.error("No valid providers found in DRIVERS.xlsx")
                sys.exit(1)

            logger.info(f"Loaded {len(drivers)} providers from Excel")
            provider_processor = ProviderProcessor(alegra_service)
            provider_results: List[ProviderProcessingResult] = []

            for idx, row in enumerate(drivers, 1):
                logger.info(f"\n[{idx}/{len(drivers)}] Processing DRIVERS Row {row.get('excel_row')}: {row.get('rfc')}")
                result = provider_processor.process_provider_row(row)
                provider_results.append(result)

                if result.status.value == "SUCCESS":
                    logger.info(f"✅ SUCCESS: {result.rfc} → {result.action} (Alegra ID: {result.alegra_contact_id})")
                elif result.status.value == "INVALID_DATA":
                    logger.warning(f"⚠️ INVALID DATA: Row {result.excel_row} - {result.error_message}")
                else:
                    logger.warning(f"❌ ERROR: Row {result.excel_row} - {result.error_message}")

            logger.info("\nGenerating provider reports...")
            provider_report_generator = ProviderReportGenerator("reports")
            report_files = provider_report_generator.generate_reports(provider_results, formats=["json", "csv", "html"])

            logger.info("\n📄 Provider reports generated:")
            for format_name, filepath in report_files.items():
                logger.info(f"  - {format_name.upper()}: {filepath}")

            logger.info("\n" + "="*70)
            logger.info("Provider Process Completed")
            logger.info("="*70)
            return
        
        # Step 4: Generate reports
        logger.info("\nGenerating reports...")
        report_generator = ReportGenerator("reports")
        report_files = report_generator.generate_reports(results, formats=["json", "csv", "html"])
        
        logger.info("\n📄 Reports generated:")
        for format_name, filepath in report_files.items():
            logger.info(f"  - {format_name.upper()}: {filepath}")
        
        logger.info("\n" + "="*70)
        logger.info("Process Completed")
        logger.info("="*70)
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
