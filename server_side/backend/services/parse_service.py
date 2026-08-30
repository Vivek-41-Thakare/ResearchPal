import os
import zipfile
import tempfile
import pymupdf
import shutil
from typing import List, Dict, Any, Tuple
from fastapi.concurrency import run_in_threadpool

from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
from adobe.pdfservices.operation.pdf_services import PDFServices
from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_pdf_params import ExtractPDFParams
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_element_type import ExtractElementType
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_renditions_element_type import ExtractRenditionsElementType
from adobe.pdfservices.operation.pdfjobs.jobs.extract_pdf_job import ExtractPDFJob
from adobe.pdfservices.operation.pdfjobs.result.extract_pdf_result import ExtractPDFResult
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.table_structure_type import TableStructureType

class ParseService:
    def __init__(self):
        # Read and automatically strip any surrounding quotes from credentials
        raw_id = os.getenv("PDF_SERVICES_CLIENT_ID", "")
        raw_secret = os.getenv("PDF_SERVICES_CLIENT_SECRET", "")
        
        self.client_id = raw_id.strip('"').strip("'") if raw_id else ""
        self.client_secret = raw_secret.strip('"').strip("'") if raw_secret else ""

    async def parse_pdf(
        self, 
        pdf_bytes: bytes, 
        filename: str,
        parser_mode: str = "basic"
    ) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Parses PDF:
        1. Uses PyMuPDF to extract full plain text (extremely fast).
        2. Tries to use Adobe PDF Extract API to get visual figures (.png) and tables (.csv).
           If Adobe fails or is unconfigured, falls back to text-only mode gracefully.
        """
        # Save uploaded bytes to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(pdf_bytes)
            temp_pdf_path = temp_pdf.name

        try:
            # 1. PyMuPDF Text Extraction
            def extract_text():
                with pymupdf.open(temp_pdf_path) as doc:
                    marked_pages = []
                    for idx, page in enumerate(doc):
                        page_num = idx + 1
                        marked_pages.append(f"\n[PAGE_MARKER_{page_num}]\n{page.get_text()}")
                    return "".join(marked_pages)
            
            plain_text = await run_in_threadpool(extract_text)

            extracted_figures = []
            extracted_tables = []
            
            # Check if Adobe credentials look valid and user requested advanced parsing
            has_adobe = (
                self.client_id and 
                self.client_secret and 
                "your-adobe" not in self.client_id and
                parser_mode == "advanced"
            )

            if has_adobe:
                print("ℹ️ Initiating Adobe PDF Extract API call...")
                try:
                    def run_adobe_extract():
                        credentials = ServicePrincipalCredentials(
                            client_id=self.client_id,
                            client_secret=self.client_secret
                        )
                        pdf_services = PDFServices(credentials)
                        
                        # Upload local temp file safely
                        with open(temp_pdf_path, "rb") as file_stream:
                            input_asset = pdf_services.upload(
                                input_stream=file_stream, 
                                mime_type=PDFServicesMediaType.PDF
                            )
                        
                        # Select tables and figures extract
                        extract_pdf_params = ExtractPDFParams(
                            elements_to_extract=[ExtractElementType.TEXT, ExtractElementType.TABLES],
                            elements_to_extract_renditions=[ExtractRenditionsElementType.TABLES, ExtractRenditionsElementType.FIGURES],
                            table_structure_type=TableStructureType.CSV
                        )
                        
                        job = ExtractPDFJob(input_asset=input_asset, extract_pdf_params=extract_pdf_params)
                        location = pdf_services.submit(job)
                        result = pdf_services.get_job_result(location, ExtractPDFResult)
                        
                        result_asset = result.get_result().get_resource()
                        stream_asset = pdf_services.get_content(result_asset)
                        
                        return stream_asset.get_input_stream()

                    zip_content = await run_in_threadpool(run_adobe_extract)

                    # 3. Unpack zip content to retrieve figures and tables
                    temp_extracted_dir = tempfile.mkdtemp()
                    temp_zip_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
                    
                    try:
                        with open(temp_zip_file.name, "wb") as f:
                            f.write(zip_content)
                        
                        with zipfile.ZipFile(temp_zip_file.name, 'r') as zip_ref:
                            zip_ref.extractall(temp_extracted_dir)

                        # Find extracted CSVs and PNGs
                        for root, dirs, files in os.walk(temp_extracted_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                if file.lower().endswith('.png'):
                                    with open(file_path, 'rb') as f:
                                        extracted_figures.append({
                                            "filename": file,
                                            "content": f.read()
                                        })
                                elif file.lower().endswith('.csv'):
                                    with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                                        extracted_tables.append({
                                            "filename": file,
                                            "content": f.read()
                                        })
                    finally:
                        shutil.rmtree(temp_extracted_dir, ignore_errors=True)
                        if os.path.exists(temp_zip_file.name):
                            os.remove(temp_zip_file.name)
                            
                except Exception as e:
                    print(f"⚠️ Warning: Adobe PDF Extract API call failed: {e}")
                    print("🔄 Falling back gracefully to plain text extraction.")
            else:
                print("ℹ️ Adobe Extract credentials not set. Falling back to plain text extraction.")

            return plain_text, extracted_figures, extracted_tables

        finally:
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
