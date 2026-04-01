"""
Invoice processor - Main orchestrator for processing Mexican invoices.
"""
import logging
from typing import Optional
from models.models import ProcessingResult, ProcessingStatus, FileSearchResult
from services.mexico_invoice_analyzer import MexicoInvoiceAnalyzer
from services.mexico_alegra_service import MexicoAlegraService
from core.xml_file_searcher import XMLFileSearcher


logger = logging.getLogger(__name__)


class InvoiceProcessor:
    """Main processor for handling the complete invoice processing pipeline."""
    
    def __init__(
        self,
        analyzer: MexicoInvoiceAnalyzer,
        alegra_service: MexicoAlegraService
    ):
        """
        Initialize the invoice processor.
        
        Args:
            analyzer: Mexico Invoice Analyzer instance
            alegra_service: Mexico Alegra Service instance
        """
        self.analyzer = analyzer
        self.alegra_service = alegra_service
    
    def process_invoice(
        self,
        uuid: str,
        search_result: FileSearchResult
    ) -> ProcessingResult:
        """
        Process a single invoice through the complete pipeline.
        
        Args:
            uuid: Invoice UUID
            search_result: Result from searching for the XML file
            
        Returns:
            ProcessingResult with status and details
        """
        logger.info(f"Processing UUID: {uuid}")
        
        # Step 1: Verify file was found
        if not search_result.found:
            logger.warning(f"UUID not found: {uuid}")
            return ProcessingResult(
                uuid=uuid,
                status=ProcessingStatus.UUID_NOT_FOUND,
                error_message="No XML file found containing this UUID"
            )
        
        # Step 2: Check for multiple files
        if search_result.has_duplicates:
            logger.warning(f"Multiple files found for UUID: {uuid}")
            return ProcessingResult(
                uuid=uuid,
                status=ProcessingStatus.MULTIPLE_FILES_FOUND,
                error_message=f"Found {len(search_result.file_paths)} files",
                additional_info={
                    "file_paths": search_result.file_paths,
                    "months": search_result.months
                }
            )
        
        # Get the single file path
        file_path = search_result.single_file_path
        month = search_result.single_month
        
        # Step 3: Analyze XML file
        logger.info(f"Analyzing XML file: {file_path}")
        analyzed_data = self.analyzer.analyze_xml_file(file_path)
        
        if not analyzed_data:
            logger.error(f"Failed to analyze XML file: {file_path}")
            return ProcessingResult(
                uuid=uuid,
                status=ProcessingStatus.ANALYZER_ERROR,
                file_path=file_path,
                month=month,
                error_message="Invoice Analyzer failed to process XML file"
            )
        
        # Step 4: Extract issuer ID
        issuer_id = self.analyzer.extract_issuer_id(analyzed_data)
        
        if not issuer_id:
            logger.error(f"Failed to extract issuer ID from analyzed data")
            return ProcessingResult(
                uuid=uuid,
                status=ProcessingStatus.SYSTEM_ERROR,
                file_path=file_path,
                month=month,
                error_message="Could not extract issuer ID from invoice data"
            )
        
        # Step 5: Verify provider exists in Alegra
        logger.info(f"Verifying provider: {issuer_id}")
        provider_info = self.alegra_service.verify_provider_exists(issuer_id)
        
        if not provider_info:
            logger.warning(f"Provider not found in Alegra: {issuer_id}")
            return ProcessingResult(
                uuid=uuid,
                status=ProcessingStatus.PROVIDER_NOT_FOUND_ERP,
                file_path=file_path,
                month=month,
                error_message=f"Provider {issuer_id} not found in Alegra"
            )
        
        # Step 6: Check for duplicate invoice
        document_id = analyzed_data.get("document_data", {}).get(
            "document_information", {}
        ).get("document_id")
        
        provider_id = provider_info.get("id")
        
        logger.info(f"Checking for duplicate invoice: {document_id}")
        is_duplicate = self.alegra_service.check_duplicate_invoice(
            document_id, provider_id
        )
        
        if is_duplicate:
            logger.warning(f"Duplicate invoice detected: {document_id}")
            return ProcessingResult(
                uuid=uuid,
                status=ProcessingStatus.DUPLICATE_INVOICE,
                file_path=file_path,
                month=month,
                error_message=f"Invoice {document_id} already exists in Alegra"
            )
        
        # Step 7: Create invoice in Alegra
        logger.info(f"Creating invoice in Alegra: {document_id}")
        invoice_data = self.alegra_service.create_invoice(
            analyzed_data=analyzed_data,
            provider_info=provider_info,
            xml_file_path=file_path
        )
        
        if not invoice_data:
            logger.error(f"Failed to create invoice in Alegra: {document_id}")
            return ProcessingResult(
                uuid=uuid,
                status=ProcessingStatus.ALEGRA_CREATE_ERROR,
                file_path=file_path,
                month=month,
                error_message="Failed to create invoice in Alegra"
            )
        
        invoice_id = invoice_data.get("id")
        
        # Step 8: Attach XML file to invoice
        logger.info(f"Attaching XML file to invoice: {invoice_id}")
        attachment_success = self.alegra_service.attach_file_to_invoice(
            invoice_id, file_path
        )
        
        if not attachment_success:
            logger.warning(f"Failed to attach XML file to invoice: {invoice_id}")
            # Invoice was created, but attachment failed - still count as partial success
            return ProcessingResult(
                uuid=uuid,
                status=ProcessingStatus.ATTACHMENT_ERROR,
                file_path=file_path,
                month=month,
                alegra_invoice_id=str(invoice_id),
                error_message="Invoice created but XML attachment failed"
            )
        
        # Step 9: Add UUID as comment
        uuid_comment = f"UUID: {uuid}"
        self.alegra_service.add_comment_to_invoice(invoice_id, uuid_comment)
        
        # Add Automation Attribution Comment
        self.alegra_service.add_comment_to_invoice(invoice_id, "Generado automáticamente por Adsoft")
        
        # Success!
        logger.info(f"Successfully processed invoice: {uuid} (Alegra ID: {invoice_id})")
        return ProcessingResult(
            uuid=uuid,
            status=ProcessingStatus.SUCCESS,
            file_path=file_path,
            month=month,
            alegra_invoice_id=str(invoice_id)
        )

    def process_invoice_from_excel(self, excel_data: dict, xml_searcher: XMLFileSearcher) -> ProcessingResult:
        """
        Process a single invoice from Excel data.
        
        Args:
            excel_data: Dictionary containing invoice data from Excel
            xml_searcher: Searcher to find associated XML file
            
        Returns:
            ProcessingResult object
        """
        from models.models import ProcessingSource
        from services.excel_adapter import ExcelAdapter

        uuid = excel_data.get("uuid")
        logger.info(f"Processing Excel Invoice: {uuid}")
        
        # Default result
        result = ProcessingResult(
            uuid=uuid,
            status=ProcessingStatus.SYSTEM_ERROR,
            source=ProcessingSource.EXCEL
        )
        
        # Check for invalid data marker from ExcelLoader
        if uuid.startswith("INVALID_UUID_ROW_"):
            result.status = ProcessingStatus.INVALID_DATA
            result.error_message = "Row skipped: Missing or invalid UUID in Excel"
            return result
        
        try:
            # 1. Search for XML file (for attachment only)
            search_result = xml_searcher.search_by_uuid(uuid)
            
            xml_file_path = None
            if search_result.found and search_result.is_unique:
                xml_file_path = search_result.single_file_path
                result.file_path = xml_file_path
                result.month = search_result.single_month
                logger.info(f"XML found for attachment: {xml_file_path}")
            elif search_result.has_duplicates:
                return ProcessingResult(
                    uuid=uuid,
                    status=ProcessingStatus.MULTIPLE_FILES_FOUND,
                    source=ProcessingSource.EXCEL,
                    file_path="; ".join(search_result.file_paths),
                    error_message=f"Multiple XML files found: {len(search_result.file_paths)}"
                )
            else:
                logger.warning(f"No XML file found for UUID {uuid} (will process without attachment)")
                result.status = ProcessingStatus.UUID_NOT_FOUND # Temporarily, will allow success if invoice creation works
            
            # 2. Adapt Excel Data
            analyzed_data = ExcelAdapter.to_analyzed_data(excel_data)
            provider_rfc = excel_data.get("rfc")
            
            # 3. Verify Provider Exists
            provider_info = self.alegra_service.verify_provider_exists(provider_rfc)
            
            if not provider_info:
                logger.warning(f"Provider not found for RFC {provider_rfc}")
                result.status = ProcessingStatus.PROVIDER_NOT_FOUND_ERP
                result.error_message = f"Provider with RFC {provider_rfc} not found in Alegra"
                return result
                
            logger.info(f"Provider found: {provider_info.get('name')} (ID: {provider_info.get('id')})")
            
            # 4. Check Duplicate Invoice
            is_duplicate = self.alegra_service.check_duplicate_invoice(uuid, provider_info.get('id'))
            
            if is_duplicate:
                logger.warning(f"Duplicate invoice found: {uuid}")
                result.status = ProcessingStatus.DUPLICATE_INVOICE
                result.error_message = "Invoice already exists in Alegra"
                return result
            
            # 5. Create Invoice
            try:
                invoice_result = self.alegra_service.create_invoice(
                    analyzed_data, 
                    provider_info, 
                    xml_file_path
                )
                
                if not invoice_result:
                    raise Exception("Alegra service returned None")

                result.alegra_invoice_id = invoice_result.get("id")
                result.status = ProcessingStatus.SUCCESS
                result.error_message = None 
                
                if xml_file_path:
                    logger.info(f"Invoice created successfully: {result.alegra_invoice_id} with attachment")
                    logger.info(f"Invoice created successfully: {result.alegra_invoice_id} WITHOUT attachment")
                    result.error_message = "Processed successfully but XML file was not found/attached"
                
                # Add Comments
                invoice_id = result.alegra_invoice_id
                
                # 1. UUID Comment
                self.alegra_service.add_comment_to_invoice(invoice_id, f"UUID: {uuid}")
                
                # 2. Automation Attribution Comment
                self.alegra_service.add_comment_to_invoice(invoice_id, "Generado automáticamente por Adsoft")
                
            except Exception as e:
                logger.error(f"Error creating invoice for {uuid}: {e}")
                if "Warning: Invoice created but failed to attach XML" in str(e):
                    result.status = ProcessingStatus.ATTACHMENT_ERROR
                    result.error_message = str(e)
                else:
                    result.status = ProcessingStatus.ALEGRA_CREATE_ERROR
                    result.error_message = str(e)
            
            return result

        except Exception as e:
            logger.error(f"Error processing Excel invoice {uuid}: {e}", exc_info=True)
            return ProcessingResult(
                uuid=uuid,
                status=ProcessingStatus.SYSTEM_ERROR,
                source=ProcessingSource.EXCEL,
                error_message=str(e)
            )
