#!/usr/bin/env python3
"""
Reset Neo4j and load only baseline data (CSV + PDF)
샘플 기업 및 리스크 요소를 제거하고 baseline 데이터만 로드
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add parent directory's src to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(parent_dir, 'src'))

from db.neo4j_db import Neo4jDatabase
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

def main():
    print("=" * 70)
    print("Database Reset and Baseline Load")
    print("=" * 70)
    
    # Step 1: Reset Neo4j
    print("\n[1/2] Resetting Neo4j database...")
    try:
        db = Neo4jDatabase(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
        db.execute_query('MATCH (n) DETACH DELETE n')
        db.close()
        print("  ✓ Database reset complete")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        sys.exit(1)
    
    # Step 2: Load baseline data using batch_upload
    print("\n[2/2] Loading baseline data (CSV + PDF)...")
    baseline_path = Path(__file__).parent.parent / 'data' / 'baseline'
    
    if not baseline_path.exists():
        print(f"  ✗ Error: {baseline_path} not found")
        sys.exit(1)
    
    # Count files
    csv_files = list(baseline_path.glob('*.csv'))
    pdf_files = list(baseline_path.glob('*.pdf'))
    
    print(f"  Found: {len(csv_files)} CSV files, {len(pdf_files)} PDF files")
    
    # Use batch uploader
    try:
        from batch_upload import BatchUploader
        
        uploader = BatchUploader(
            folder_path=str(baseline_path),
            api_url='http://localhost:8000',
            recursive=False,
            permanentPdf=True
        )
        
        results = uploader.processFolder()
        uploader.saveReport(output_file=str(baseline_path / "upload_report.json"))
        
        # Summary
        csv_success = sum(1 for r in results["csv"] if r["status"] == "success")
        pdf_success = sum(1 for r in results["pdf"] if r["status"] == "success")
        
        print(f"\n✓ Upload complete:")
        print(f"  CSV: {csv_success}/{len(csv_files)} succeeded")
        print(f"  PDF: {pdf_success}/{len(pdf_files)} succeeded")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("✓ Baseline data loaded successfully")
    print("=" * 70)

if __name__ == "__main__":
    main()
