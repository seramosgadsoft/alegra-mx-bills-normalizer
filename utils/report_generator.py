"""
Report generator for creating processing reports in multiple formats.
"""
import json
import csv
import os
from datetime import datetime
from typing import List, Dict, Any
import logging
from models.models import (
    ProcessingResult,
    ReportSummary,
    ProcessingStatus,
    ProcessingSource,
    ProviderProcessingResult,
    ProviderReportSummary,
    ProviderProcessingStatus,
)


logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates detailed processing reports in multiple formats."""
    
    STATUS_LABELS_ES = {
        ProcessingStatus.SUCCESS: "Exitoso",
        ProcessingStatus.UUID_NOT_FOUND: "UUID no encontrado",
        ProcessingStatus.MULTIPLE_FILES_FOUND: "Archivos multiples",
        ProcessingStatus.ANALYZER_ERROR: "Error de analisis",
        ProcessingStatus.PROVIDER_NOT_FOUND_ERP: "Proveedor no encontrado",
        ProcessingStatus.DUPLICATE_INVOICE: "Factura duplicada",
        ProcessingStatus.ALEGRA_CREATE_ERROR: "Error al crear en Alegra",
        ProcessingStatus.ATTACHMENT_ERROR: "Error en adjunto",
        ProcessingStatus.XML_READ_ERROR: "Error al leer XML",
        ProcessingStatus.SYSTEM_ERROR: "Error del sistema",
        ProcessingStatus.INVALID_DATA: "Datos invalidos",
    }
    
    SOURCE_LABELS_ES = {
        ProcessingSource.XML_FILE: "XML",
        ProcessingSource.EXCEL: "Excel",
    }
    
    STATUS_LABELS_ES_BY_VALUE = {
        status.value: label for status, label in STATUS_LABELS_ES.items()
    }
    
    def __init__(self, output_dir: str = "reports"):
        """
        Initialize the report generator.
        
        Args:
            output_dir: Directory where reports will be saved
        """
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_reports(
        self,
        results: List[ProcessingResult],
        formats: List[str] = ["json", "csv", "html"]
    ) -> dict:
        """
        Generate reports in multiple formats.
        
        Args:
            results: List of processing results
            formats: List of formats to generate (json, csv, html)
            
        Returns:
            Dictionary with paths to generated report files
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_files = {}
        
        # Calculate summary statistics
        summary = self._calculate_summary(results)
        
        # Generate each requested format
        if "json" in formats:
            json_path = self._generate_json_report(results, summary, timestamp)
            report_files["json"] = json_path
        
        if "csv" in formats:
            csv_path = self._generate_csv_report(results, timestamp)
            report_files["csv"] = csv_path
        
        if "html" in formats:
            html_path = self._generate_html_report(results, summary, timestamp)
            report_files["html"] = html_path
        
        # Print console summary
        self._print_console_summary(summary, results)
        
        return report_files
    
    def _calculate_summary(self, results: List[ProcessingResult]) -> ReportSummary:
        """Calculate summary statistics from results."""
        summary = ReportSummary()
        summary.total_uuids = len(results)
        
        for result in results:
            if result.status == ProcessingStatus.SUCCESS:
                summary.successful += 1
            elif result.status == ProcessingStatus.UUID_NOT_FOUND:
                summary.not_found += 1
            elif result.status == ProcessingStatus.MULTIPLE_FILES_FOUND:
                summary.multiple_files += 1
            elif result.status == ProcessingStatus.PROVIDER_NOT_FOUND_ERP:
                summary.provider_not_found += 1
            elif result.status == ProcessingStatus.DUPLICATE_INVOICE:
                summary.duplicate_invoice += 1
            elif result.status == ProcessingStatus.ANALYZER_ERROR:
                summary.analyzer_error += 1
            elif result.status in [
                ProcessingStatus.ALEGRA_CREATE_ERROR,
                ProcessingStatus.ATTACHMENT_ERROR
            ]:
                summary.alegra_error += 1
            else:
                summary.other_errors += 1
        
        summary.failed = (
            summary.total_uuids - summary.successful
        )
        
        return summary
    
    def _generate_json_report(
        self,
        results: List[ProcessingResult],
        summary: ReportSummary,
        timestamp: str
    ) -> str:
        """Generate JSON report."""
        filename = f"processing_report_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        report_data = {
            "generado_en": datetime.now().isoformat(),
            "resumen": self._summary_to_dict_es(summary),
            "resultados": [self._result_to_dict_es(result) for result in results]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON report generated: {filepath}")
        return filepath
    
    def _generate_csv_report(
        self,
        results: List[ProcessingResult],
        timestamp: str
    ) -> str:
        """Generate CSV report."""
        filename = f"processing_report_{timestamp}.csv"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                "UUID",
                "Estado",
                "Origen",
                "Ruta de archivo",
                "Mes",
                "ID Factura Alegra",
                "Mensaje de error",
                "Marca de tiempo"
            ])
            
            # Write data rows
            for result in results:
                writer.writerow([
                    result.uuid,
                    self.STATUS_LABELS_ES.get(result.status, result.status.value),
                    self.SOURCE_LABELS_ES.get(result.source, result.source.value) if hasattr(result, "source") else "XML",
                    result.file_path or "",
                    result.month or "",
                    result.alegra_invoice_id or "",
                    result.error_message or "",
                    result.timestamp
                ])
        
        logger.info(f"CSV report generated: {filepath}")
        return filepath
    
    def _generate_html_report(
        self,
        results: List[ProcessingResult],
        summary: ReportSummary,
        timestamp: str
    ) -> str:
        """Generate HTML report."""
        filename = f"processing_report_{timestamp}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        # Generate HTML content
        html_content = self._create_html_content(results, summary, timestamp)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {filepath}")
        return filepath
    
    def _create_html_content(
        self,
        results: List[ProcessingResult],
        summary: ReportSummary,
        timestamp: str
    ) -> str:
        """Create HTML content for the report."""
        # Group results by status
        results_by_status = {}
        for result in results:
            status = result.status.value
            if status not in results_by_status:
                results_by_status[status] = []
            results_by_status[status].append(result)
        
        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de Normalizacion de Facturas Mexico - {timestamp}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }}
        .stat-card.success {{ background-color: #d4edda; border-left: 4px solid #28a745; }}
        .stat-card.failed {{ background-color: #f8d7da; border-left: 4px solid #dc3545; }}
        .stat-card.warning {{ background-color: #fff3cd; border-left: 4px solid #ffc107; }}
        .stat-card.info {{ background-color: #d1ecf1; border-left: 4px solid #17a2b8; }}
        .stat-label {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
            position: sticky;
            top: 0;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .status-badge {{
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 0.85em;
            font-weight: bold;
            display: inline-block;
        }}
        .status-SUCCESS {{ background-color: #28a745; color: white; }}
        .status-UUID_NOT_FOUND {{ background-color: #6c757d; color: white; }}
        .status-MULTIPLE_FILES_FOUND {{ background-color: #ffc107; color: black; }}
        .status-PROVIDER_NOT_FOUND_ERP {{ background-color: #fd7e14; color: white; }}
        .status-DUPLICATE_INVOICE {{ background-color: #17a2b8; color: white; }}
        .status-ANALYZER_ERROR {{ background-color: #dc3545; color: white; }}
        .status-ALEGRA_CREATE_ERROR {{ background-color: #dc3545; color: white; }}
        .status-ATTACHMENT_ERROR {{ background-color: #ffc107; color: black; }}
        .section {{
            margin: 30px 0;
        }}
        .collapsible {{
            cursor: pointer;
            padding: 10px;
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            margin-top: 10px;
        }}
        .collapsible:hover {{
            background-color: #e9ecef;
        }}
        .content {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }}
        .content.active {{
            max-height: 2000px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🇲🇽 Reporte de Normalizacion de Facturas Mexico</h1>
        <p><strong>Generado:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <h2>📊 Resumen de procesamiento</h2>
        <div class="summary">
            <div class="stat-card info">
                <div class="stat-label">Total de UUID</div>
                <div class="stat-value">{summary.total_uuids}</div>
            </div>
            <div class="stat-card success">
                <div class="stat-label">Exitosas</div>
                <div class="stat-value">{summary.successful}</div>
            </div>
            <div class="stat-card failed">
                <div class="stat-label">Fallidas</div>
                <div class="stat-value">{summary.failed}</div>
            </div>
            <div class="stat-card warning">
                <div class="stat-label">No encontradas</div>
                <div class="stat-value">{summary.not_found}</div>
            </div>
            <div class="stat-card warning">
                <div class="stat-label">Archivos multiples</div>
                <div class="stat-value">{summary.multiple_files}</div>
            </div>
            <div class="stat-card warning">
                <div class="stat-label">Proveedor no encontrado</div>
                <div class="stat-value">{summary.provider_not_found}</div>
            </div>
            <div class="stat-card info">
                <div class="stat-label">Duplicadas</div>
                <div class="stat-value">{summary.duplicate_invoice}</div>
            </div>
        </div>
"""
        
        # Add sections for each status
        for status, status_results in results_by_status.items():
            html += f"""
        <div class="section">
            <div class="collapsible" onclick="toggleSection('{status}')">
                <h3 style="margin: 0;">
                    <span class="status-badge status-{status}">{self.STATUS_LABELS_ES_BY_VALUE.get(status, status)}</span>
                    ({len(status_results)} elementos)
                </h3>
            </div>
            <div id="{status}" class="content">
                <table>
                    <thead>
                        <tr>
                            <th>UUID</th>
                            <th>Ruta de archivo</th>
                            <th>Mes</th>
                            <th>ID Alegra</th>
                            <th>Detalles</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            
            for result in status_results:
                file_display = result.file_path.split('/')[-1] if result.file_path else "-"
                details = result.error_message or "-"
                
                html += f"""
                        <tr>
                            <td><code>{result.uuid}</code></td>
                            <td title="{result.file_path or ''}">{file_display}</td>
                            <td>{result.month or "-"}</td>
                            <td>{result.alegra_invoice_id or "-"}</td>
                            <td>{details}</td>
                        </tr>
"""
            
            html += """
                    </tbody>
                </table>
            </div>
        </div>
"""
        
        html += """
    </div>
    <script>
        function toggleSection(id) {
            const content = document.getElementById(id);
            content.classList.toggle('active');
        }
        
        // Expand successful section by default
        document.addEventListener('DOMContentLoaded', function() {
            const successSection = document.getElementById('SUCCESS');
            if (successSection) {
                successSection.classList.add('active');
            }
        });
    </script>
</body>
</html>
"""
        
        return html
    
    def _print_console_summary(
        self,
        summary: ReportSummary,
        results: List[ProcessingResult]
    ):
        """Print summary to console."""
        print("\n" + "="*70)
        print("📊 RESUMEN DE PROCESAMIENTO".center(70))
        print("="*70)
        print(f"\n{'Total de UUID:':<30} {summary.total_uuids:>10}")
        print(f"{'✅ Exitosas:':<30} {summary.successful:>10}")
        print(f"{'❌ Fallidas:':<30} {summary.failed:>10}")
        print(f"\n{'Desglose de fallas:':<30}")
        print(f"{'  - No encontradas:':<30} {summary.not_found:>10}")
        print(f"{'  - Archivos multiples:':<30} {summary.multiple_files:>10}")
        print(f"{'  - Proveedor no encontrado:':<30} {summary.provider_not_found:>10}")
        print(f"{'  - Factura duplicada:':<30} {summary.duplicate_invoice:>10}")
        print(f"{'  - Error de analisis:':<30} {summary.analyzer_error:>10}")
        print(f"{'  - Error en Alegra:':<30} {summary.alegra_error:>10}")
        print(f"{'  - Otros errores:':<30} {summary.other_errors:>10}")
        print("\n" + "="*70 + "\n")
        
        # Show sample of failures if any
        if summary.failed > 0:
            print("❌ Muestra de UUID fallidos (primeros 5):")
            count = 0
            for result in results:
                if result.status != ProcessingStatus.SUCCESS and count < 5:
                    label = self.STATUS_LABELS_ES.get(result.status, result.status.value)
                    print(f"  - {result.uuid}: {label}")
                    if result.error_message:
                        print(f"    → {result.error_message}")
                    count += 1
            print()

    def _summary_to_dict_es(self, summary: ReportSummary) -> Dict[str, int]:
        return {
            "total_uuid": summary.total_uuids,
            "exitosas": summary.successful,
            "fallidas": summary.failed,
            "no_encontradas": summary.not_found,
            "archivos_multiples": summary.multiple_files,
            "proveedor_no_encontrado": summary.provider_not_found,
            "facturas_duplicadas": summary.duplicate_invoice,
            "error_analisis": summary.analyzer_error,
            "error_alegra": summary.alegra_error,
            "otros_errores": summary.other_errors
        }
    
    def _result_to_dict_es(self, result: ProcessingResult) -> Dict[str, Any]:
        base = {
            "uuid": result.uuid,
            "estado": self.STATUS_LABELS_ES.get(result.status, result.status.value),
            "origen": self.SOURCE_LABELS_ES.get(result.source, result.source.value),
            "ruta_archivo": result.file_path,
            "mes": result.month,
            "id_factura_alegra": result.alegra_invoice_id,
            "mensaje_error": result.error_message,
            "marca_de_tiempo": result.timestamp,
        }
        base.update(result.additional_info)
        return base


class ProviderReportGenerator:
    """Generates provider processing reports in multiple formats."""

    STATUS_LABELS_ES = {
        ProviderProcessingStatus.SUCCESS: "Exitoso",
        ProviderProcessingStatus.INVALID_DATA: "Datos invalidos",
        ProviderProcessingStatus.ERROR: "Error",
    }

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_reports(
        self,
        results: List[ProviderProcessingResult],
        formats: List[str] = ["json", "csv", "html"]
    ) -> dict:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_files = {}
        summary = self._calculate_summary(results)

        if "json" in formats:
            report_files["json"] = self._generate_json_report(results, summary, timestamp)
        if "csv" in formats:
            report_files["csv"] = self._generate_csv_report(results, timestamp)
        if "html" in formats:
            report_files["html"] = self._generate_html_report(results, summary, timestamp)

        self._print_console_summary(summary, results)
        return report_files

    def _calculate_summary(self, results: List[ProviderProcessingResult]) -> ProviderReportSummary:
        summary = ProviderReportSummary()
        summary.total_rows = len(results)
        for result in results:
            if result.status == ProviderProcessingStatus.SUCCESS:
                summary.processed_ok += 1
                if result.action == "created":
                    summary.created += 1
                elif result.action == "updated":
                    summary.updated += 1
                elif result.action == "unchanged":
                    summary.unchanged += 1
            elif result.status == ProviderProcessingStatus.INVALID_DATA:
                summary.invalid_data += 1
            else:
                summary.errors += 1
        return summary

    def _generate_json_report(
        self,
        results: List[ProviderProcessingResult],
        summary: ProviderReportSummary,
        timestamp: str
    ) -> str:
        filename = f"providers_report_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        report_data = {
            "generado_en": datetime.now().isoformat(),
            "resumen": summary.to_dict(),
            "resultados": [r.to_dict() for r in results]
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Providers JSON report generated: {filepath}")
        return filepath

    def _generate_csv_report(
        self,
        results: List[ProviderProcessingResult],
        timestamp: str
    ) -> str:
        filename = f"providers_report_{timestamp}.csv"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Fila Excel",
                "RFC",
                "Nombre",
                "Correo",
                "Direccion",
                "Estado",
                "Accion",
                "ID Contacto Alegra",
                "Mensaje de error",
                "Marca de tiempo"
            ])
            for r in results:
                writer.writerow([
                    r.excel_row,
                    r.rfc,
                    r.name,
                    r.email,
                    r.address,
                    self.STATUS_LABELS_ES.get(r.status, r.status.value),
                    r.action,
                    r.alegra_contact_id or "",
                    r.error_message or "",
                    r.timestamp
                ])
        logger.info(f"Providers CSV report generated: {filepath}")
        return filepath

    def _generate_html_report(
        self,
        results: List[ProviderProcessingResult],
        summary: ProviderReportSummary,
        timestamp: str
    ) -> str:
        filename = f"providers_report_{timestamp}.html"
        filepath = os.path.join(self.output_dir, filename)

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de Proveedores - {timestamp}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-radius: 8px; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #2ecc71; padding-bottom: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-card {{ padding: 15px; border-radius: 5px; text-align: center; }}
        .stat-card.info {{ background-color: #d1ecf1; border-left: 4px solid #17a2b8; }}
        .stat-card.success {{ background-color: #d4edda; border-left: 4px solid #28a745; }}
        .stat-card.warning {{ background-color: #fff3cd; border-left: 4px solid #ffc107; }}
        .stat-card.failed {{ background-color: #f8d7da; border-left: 4px solid #dc3545; }}
        .stat-label {{ font-size: 0.9em; color: #666; margin-bottom: 5px; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #333; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background-color: #2ecc71; color: white; padding: 12px; text-align: left; position: sticky; top: 0; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .status-badge {{ padding: 5px 10px; border-radius: 3px; font-size: 0.85em; font-weight: bold; display: inline-block; }}
        .status-SUCCESS {{ background-color: #28a745; color: white; }}
        .status-INVALID_DATA {{ background-color: #ffc107; color: black; }}
        .status-ERROR {{ background-color: #dc3545; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>👥 Reporte de Proveedores</h1>
        <p><strong>Generado:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <div class="summary">
            <div class="stat-card info"><div class="stat-label">Total filas</div><div class="stat-value">{summary.total_rows}</div></div>
            <div class="stat-card success"><div class="stat-label">Procesadas OK</div><div class="stat-value">{summary.processed_ok}</div></div>
            <div class="stat-card success"><div class="stat-label">Creadas</div><div class="stat-value">{summary.created}</div></div>
            <div class="stat-card success"><div class="stat-label">Actualizadas</div><div class="stat-value">{summary.updated}</div></div>
            <div class="stat-card info"><div class="stat-label">Sin cambios</div><div class="stat-value">{summary.unchanged}</div></div>
            <div class="stat-card warning"><div class="stat-label">Datos invalidos</div><div class="stat-value">{summary.invalid_data}</div></div>
            <div class="stat-card failed"><div class="stat-label">Errores</div><div class="stat-value">{summary.errors}</div></div>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Fila</th>
                    <th>RFC</th>
                    <th>Nombre</th>
                    <th>Correo</th>
                    <th>Direccion</th>
                    <th>Estado</th>
                    <th>Accion</th>
                    <th>ID Alegra</th>
                    <th>Detalles</th>
                </tr>
            </thead>
            <tbody>
"""
        for r in results:
            html += f"""
                <tr>
                    <td>{r.excel_row}</td>
                    <td>{r.rfc}</td>
                    <td>{r.name}</td>
                    <td>{r.email}</td>
                    <td>{r.address}</td>
                    <td><span class="status-badge status-{r.status.value}">{self.STATUS_LABELS_ES.get(r.status, r.status.value)}</span></td>
                    <td>{r.action}</td>
                    <td>{r.alegra_contact_id or '-'}</td>
                    <td>{r.error_message or '-'}</td>
                </tr>
"""
        html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"Providers HTML report generated: {filepath}")
        return filepath

    def _print_console_summary(
        self,
        summary: ProviderReportSummary,
        results: List[ProviderProcessingResult]
    ):
        print("\n" + "="*70)
        print("📊 RESUMEN DE PROVEEDORES".center(70))
        print("="*70)
        print(f"\n{'Total filas:':<30} {summary.total_rows:>10}")
        print(f"{'✅ Procesadas OK:':<30} {summary.processed_ok:>10}")
        print(f"{'🆕 Creadas:':<30} {summary.created:>10}")
        print(f"{'✏️ Actualizadas:':<30} {summary.updated:>10}")
        print(f"{'➖ Sin cambios:':<30} {summary.unchanged:>10}")
        print(f"{'⚠️ Datos invalidos:':<30} {summary.invalid_data:>10}")
        print(f"{'❌ Errores:':<30} {summary.errors:>10}")
        print("\n" + "="*70 + "\n")

        if summary.errors > 0 or summary.invalid_data > 0:
            print("⚠️ Muestra de filas con problema (primeras 5):")
            count = 0
            for r in results:
                if r.status != ProviderProcessingStatus.SUCCESS and count < 5:
                    label = self.STATUS_LABELS_ES.get(r.status, r.status.value)
                    print(f"  - Fila {r.excel_row}: {label} ({r.action})")
                    if r.error_message:
                        print(f"    → {r.error_message}")
                    count += 1
            print()
