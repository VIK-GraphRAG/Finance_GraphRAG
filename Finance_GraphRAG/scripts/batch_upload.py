#!/usr/bin/env python3
"""
Batch Upload Script - 폴더의 모든 파일을 Neo4j에 일괄 업로드
CSV, JSON, PDF 파일을 자동으로 감지하고 업로드합니다.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any
import requests
import pandas as pd

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
UPLOAD_TIMEOUT = 600  # 10 minutes per file

class BatchUploader:
    """폴더의 모든 파일을 Neo4j에 일괄 업로드하는 클래스"""
    
    def __init__(
        self,
        folder_path: str,
        api_url: str = API_BASE_URL,
        recursive: bool = True,
        permanentPdf: bool = True,
        includeCsv: bool = True,
        includePdf: bool = True,
        includeJson: bool = True
    ):
        self.folder_path = Path(folder_path)
        self.api_url = api_url
        self.recursive = recursive
        self.permanentPdf = permanentPdf
        self.includeCsv = includeCsv
        self.includePdf = includePdf
        self.includeJson = includeJson
        self.results = {
            "csv": [],
            "json": [],
            "pdf": [],
            "errors": []
        }
        
    def uploadCsv(self, file_path: Path) -> Dict[str, Any]:
        """CSV 파일 업로드"""
        try:
            print(f"\n[CSV] Processing: {file_path.name}")
            
            # CSV 읽기
            df = pd.read_csv(file_path)
            df_clean = df.fillna('')  # NaN 처리
            
            # 첫 번째 컬럼을 엔티티로, 나머지를 속성으로 자동 설정
            entity_column = df.columns[0]
            property_columns = list(df.columns[1:])
            
            # 엔티티 타입 추론 (파일명 기반)
            entity_type = "Company"  # 기본값
            filename_lower = file_path.stem.lower()
            if "person" in filename_lower or "people" in filename_lower:
                entity_type = "Person"
            elif "tech" in filename_lower or "technology" in filename_lower:
                entity_type = "Technology"
            elif "country" in filename_lower or "region" in filename_lower:
                entity_type = "Country"
            
            print(f"  Entity Column: {entity_column}")
            print(f"  Entity Type: {entity_type}")
            print(f"  Property Columns: {property_columns}")
            print(f"  Rows: {len(df)}")
            
            # API 호출
            response = requests.post(
                f"{self.api_url}/upload_csv",
                json={
                    "data": df_clean.to_dict(orient='records'),
                    "entity_column": entity_column,
                    "entity_type": entity_type,
                    "property_columns": property_columns
                },
                timeout=UPLOAD_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✓ Success: {result.get('nodes_created', 0)} nodes created")
                return {
                    "file": file_path.name,
                    "status": "success",
                    "nodes": result.get('nodes_created', 0),
                    "type": entity_type
                }
            else:
                error_msg = f"HTTP {response.status_code}"
                print(f"  ✗ Failed: {error_msg}")
                return {
                    "file": file_path.name,
                    "status": "error",
                    "error": error_msg
                }
                
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            return {
                "file": file_path.name,
                "status": "error",
                "error": str(e)
            }
    
    def uploadJson(self, file_path: Path) -> Dict[str, Any]:
        """JSON 파일 업로드"""
        try:
            print(f"\n[JSON] Processing: {file_path.name}")
            
            # JSON 읽기
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 루트 키 자동 감지
            root_key = None
            if isinstance(data, dict) and len(data) == 1:
                root_key = list(data.keys())[0]
                print(f"  Root Key: {root_key}")
            
            # 엔티티 타입 추론
            entity_type = "Company"
            filename_lower = file_path.stem.lower()
            if "person" in filename_lower:
                entity_type = "Person"
            elif "tech" in filename_lower:
                entity_type = "Technology"
            elif "country" in filename_lower:
                entity_type = "Country"
            
            print(f"  Entity Type: {entity_type}")
            
            # API 호출
            response = requests.post(
                f"{self.api_url}/upload_json",
                json={
                    "data": data,
                    "root_key": root_key,
                    "entity_key": "name",
                    "entity_type": entity_type
                },
                timeout=UPLOAD_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✓ Success: {result.get('nodes_created', 0)} nodes created")
                return {
                    "file": file_path.name,
                    "status": "success",
                    "nodes": result.get('nodes_created', 0),
                    "type": entity_type
                }
            else:
                error_msg = f"HTTP {response.status_code}"
                print(f"  ✗ Failed: {error_msg}")
                return {
                    "file": file_path.name,
                    "status": "error",
                    "error": error_msg
                }
                
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            return {
                "file": file_path.name,
                "status": "error",
                "error": str(e)
            }
    
    def uploadPdf(self, file_path: Path) -> Dict[str, Any]:
        """PDF 파일 업로드"""
        try:
            print(f"\n[PDF] Processing: {file_path.name}")
            
            # API 호출
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'application/pdf')}
                data = {'permanent': 'true' if self.permanentPdf else 'false'}
                response = requests.post(
                    f"{self.api_url}/ingest_pdf",
                    files=files,
                    data=data,
                    timeout=UPLOAD_TIMEOUT
                )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✓ Success: {result.get('entities_extracted', 0)} entities extracted")
                return {
                    "file": file_path.name,
                    "status": "success",
                    "entities": result.get('entities_extracted', 0),
                    "sensitive": result.get('sensitive_count', 0)
                }
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json().get('detail', error_msg)
                    print(f"  ✗ Failed: {error_detail}")
                except:
                    print(f"  ✗ Failed: {error_msg}")
                return {
                    "file": file_path.name,
                    "status": "error",
                    "error": error_msg
                }
                
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            return {
                "file": file_path.name,
                "status": "error",
                "error": str(e)
            }
    
    def processFolder(self) -> Dict[str, Any]:
        """폴더의 모든 파일 처리"""
        if not self.folder_path.exists():
            print(f"Error: Folder not found: {self.folder_path}")
            return self.results
        
        print(f"\n{'='*70}")
        print(f"Batch Upload Started")
        print(f"Folder: {self.folder_path}")
        print(f"{'='*70}")
        
        # 파일 목록 수집
        if self.recursive:
            csv_files = list(self.folder_path.rglob("*.csv")) if self.includeCsv else []
            json_files = list(self.folder_path.rglob("*.json")) if self.includeJson else []
            pdf_files = list(self.folder_path.rglob("*.pdf")) if self.includePdf else []
        else:
            csv_files = list(self.folder_path.glob("*.csv")) if self.includeCsv else []
            json_files = list(self.folder_path.glob("*.json")) if self.includeJson else []
            pdf_files = list(self.folder_path.glob("*.pdf")) if self.includePdf else []
        
        total_files = len(csv_files) + len(json_files) + len(pdf_files)
        
        print(f"\nFiles found:")
        print(f"  CSV: {len(csv_files)}")
        print(f"  JSON: {len(json_files)}")
        print(f"  PDF: {len(pdf_files)}")
        print(f"  Total: {total_files}")
        
        if total_files == 0:
            print("\nNo files to process.")
            return self.results
        
        start_time = time.time()
        
        # CSV 파일 처리
        for csv_file in csv_files:
            result = self.uploadCsv(csv_file)
            self.results["csv"].append(result)
            time.sleep(0.5)  # Rate limiting
        
        # JSON 파일 처리
        for json_file in json_files:
            result = self.uploadJson(json_file)
            self.results["json"].append(result)
            time.sleep(0.5)
        
        # PDF 파일 처리
        for pdf_file in pdf_files:
            result = self.uploadPdf(pdf_file)
            self.results["pdf"].append(result)
            time.sleep(1)  # PDF는 더 긴 간격
        
        elapsed_time = time.time() - start_time
        
        # 결과 요약
        print(f"\n{'='*70}")
        print(f"Batch Upload Completed")
        print(f"{'='*70}")
        print(f"\nSummary:")
        
        csv_success = sum(1 for r in self.results["csv"] if r["status"] == "success")
        json_success = sum(1 for r in self.results["json"] if r["status"] == "success")
        pdf_success = sum(1 for r in self.results["pdf"] if r["status"] == "success")
        
        print(f"  CSV: {csv_success}/{len(csv_files)} succeeded")
        print(f"  JSON: {json_success}/{len(json_files)} succeeded")
        print(f"  PDF: {pdf_success}/{len(pdf_files)} succeeded")
        print(f"\nTotal Nodes Created:")
        
        total_nodes = sum(r.get("nodes", 0) for r in self.results["csv"] + self.results["json"])
        total_entities = sum(r.get("entities", 0) for r in self.results["pdf"])
        
        print(f"  From CSV/JSON: {total_nodes} nodes")
        print(f"  From PDF: {total_entities} entities")
        print(f"\nElapsed Time: {elapsed_time:.1f} seconds")
        
        # 실패한 파일 표시
        failed = [r for r in self.results["csv"] + self.results["json"] + self.results["pdf"] 
                  if r["status"] == "error"]
        
        if failed:
            print(f"\nFailed Files ({len(failed)}):")
            for f in failed:
                print(f"  - {f['file']}: {f.get('error', 'Unknown error')}")
        
        return self.results
    
    def saveReport(self, output_file: str = "upload_report.json"):
        """업로드 결과를 JSON 파일로 저장"""
        report_path = self.folder_path / output_file
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\nReport saved: {report_path}")

    # Backward compatibility
    def upload_csv(self, file_path: Path) -> Dict[str, Any]:
        return self.uploadCsv(file_path)

    def upload_json(self, file_path: Path) -> Dict[str, Any]:
        return self.uploadJson(file_path)

    def upload_pdf(self, file_path: Path) -> Dict[str, Any]:
        return self.uploadPdf(file_path)

    def process_folder(self) -> Dict[str, Any]:
        return self.processFolder()

    def save_report(self, output_file: str = "upload_report.json"):
        return self.saveReport(output_file=output_file)


def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("Usage: python batch_upload.py <folder_path>")
        print("\nExample:")
        print("  python batch_upload.py ./data/baseline")
        print("  python batch_upload.py /path/to/your/data")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    
    # 업로더 생성 및 실행
    uploader = BatchUploader(folder_path)
    results = uploader.process_folder()
    
    # 결과 저장
    uploader.save_report()
    
    # 종료 코드 반환 (실패가 있으면 1)
    failed_count = sum(
        1 for r in results["csv"] + results["json"] + results["pdf"]
        if r["status"] == "error"
    )
    
    sys.exit(1 if failed_count > 0 else 0)


if __name__ == "__main__":
    main()
