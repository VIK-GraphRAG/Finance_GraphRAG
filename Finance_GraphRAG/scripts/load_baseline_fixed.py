#!/usr/bin/env python3
"""
Baseline Data Loader - 올바른 엔티티 타입으로 로드
"""

import os
import sys
from pathlib import Path
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir / 'src'))

from db.neo4j_db import Neo4jDatabase

API_URL = "http://localhost:8000"
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def load_time_series_data():
    """시계열 데이터를 TimeSeries 노드로 로드"""
    baseline_path = parent_dir / 'data' / 'baseline'
    
    # Time series CSV files
    time_series_files = {
        'VIX_Index': '1990~2026 vix_index.csv',
        'CPI': 'CPIAUCS미국 월별 소비자물가지수.csv',
        'DXY': 'DXY 06~26년.csv',
        'FedFundsRate': 'FedFundsRate 연준금리 54~26년.csv',
        'CentralBankBalance': 'Fred WALCL 중앙은행 현긍보유량.csv',
        'FearGreedIndex': 'fear-greed-2011-2023.csv',
        'SOX_Index': 'sox_index.csv',
        'SemiconductorTariff': 'semiconductor tariff.csv',
        'BigTechCapex': 'bigtech capex.csv'
    }
    
    db = Neo4jDatabase(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    
    total_records = 0
    
    for indicator_name, filename in time_series_files.items():
        file_path = baseline_path / filename
        
        if not file_path.exists():
            print(f"  ⚠ File not found: {filename}")
            continue
        
        try:
            print(f"\nProcessing: {filename}")
            df = pd.read_csv(file_path)
            df_clean = df.fillna('')
            
            print(f"  Columns: {list(df.columns)}")
            print(f"  Rows: {len(df)}")
            
            # Indicator 노드 생성
            query = """
            MERGE (i:Indicator {name: $name})
            SET i.type = 'TimeSeries',
                i.source = $source
            RETURN i
            """
            
            db.execute_query(query, {
                'name': indicator_name,
                'source': filename
            })
            
            # 각 행을 DataPoint로 저장
            for idx, row in df_clean.iterrows():
                date_val = row.get('Date') or row.get('date') or row.get('DATE')
                
                if not date_val or date_val == '':
                    continue
                
                # 수치 컬럼 찾기
                value_columns = [col for col in df.columns if col not in ['Date', 'date', 'DATE']]
                
                for col in value_columns:
                    val = row.get(col)
                    if val and val != '' and str(val).lower() != 'nan':
                        # DataPoint 생성 및 관계 연결
                        point_query = """
                        MATCH (i:Indicator {name: $indicator_name})
                        MERGE (d:DataPoint {date: $date, indicator: $indicator_name, field: $field})
                        SET d.value = $value
                        MERGE (i)-[:HAS_DATA_POINT]->(d)
                        """
                        
                        db.execute_query(point_query, {
                            'indicator_name': indicator_name,
                            'date': str(date_val),
                            'field': col,
                            'value': float(val) if isinstance(val, (int, float)) else str(val)
                        })
                        total_records += 1
                
                if (idx + 1) % 1000 == 0:
                    print(f"    Progress: {idx + 1}/{len(df)} rows")
            
            print(f"  ✓ Completed: {len(df)} rows")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    db.close()
    print(f"\n✓ Total data points created: {total_records}")

def load_pdf_files():
    """PDF 파일들을 영구 그래프로 로드"""
    baseline_path = parent_dir / 'data' / 'baseline'
    pdf_files = list(baseline_path.glob('*.pdf'))
    
    print(f"\nFound {len(pdf_files)} PDF files")
    
    total_entities = 0
    
    for pdf_file in pdf_files:
        try:
            print(f"\nProcessing: {pdf_file.name}")
            
            with open(pdf_file, 'rb') as f:
                files = {'file': (pdf_file.name, f, 'application/pdf')}
                data = {'permanent': 'true'}
                
                response = requests.post(
                    f"{API_URL}/ingest_pdf",
                    files=files,
                    data=data,
                    timeout=600
                )
            
            if response.status_code == 200:
                result = response.json()
                entities = result.get('entities_extracted', 0)
                total_entities += entities
                print(f"  ✓ {entities} entities extracted")
            else:
                print(f"  ✗ Failed: {response.status_code}")
                try:
                    error = response.json().get('detail', '')
                    print(f"     {error[:200]}")
                except:
                    pass
                    
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"\n✓ Total entities from PDFs: {total_entities}")

def main():
    print("="*70)
    print("Baseline Data Loader (Fixed)")
    print("="*70)
    
    # Step 1: Load time series data
    print("\n[1/2] Loading CSV time series data...")
    load_time_series_data()
    
    # Step 2: Load PDF documents
    print("\n[2/2] Loading PDF documents...")
    load_pdf_files()
    
    print("\n" + "="*70)
    print("✓ Baseline data loaded")
    print("="*70)

if __name__ == "__main__":
    main()
