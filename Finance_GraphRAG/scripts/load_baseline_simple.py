#!/usr/bin/env python3
"""
Simple baseline loader - CSV만 먼저 로드
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

API_URL = "http://localhost:8000"

def load_csv_files():
    """CSV 파일들을 Neo4j에 로드"""
    baseline_path = parent_dir / 'data' / 'baseline'
    csv_files = list(baseline_path.glob('*.csv'))
    
    print(f"\nFound {len(csv_files)} CSV files")
    
    total_nodes = 0
    
    for csv_file in csv_files:
        try:
            print(f"\nProcessing: {csv_file.name}")
            
            df = pd.read_csv(csv_file)
            df_clean = df.fillna('')
            
            # 첫 컬럼을 엔티티로
            entity_column = df.columns[0]
            property_columns = list(df.columns[1:])
            
            # 타입 추론
            entity_type = "Indicator"  # 기본값 (경제 지표)
            filename = csv_file.stem.lower()
            
            if 'company' in filename or 'capex' in filename or 'tech' in filename:
                entity_type = "Company"
            elif 'country' in filename or 'region' in filename:
                entity_type = "Country"
            
            print(f"  Type: {entity_type}, Rows: {len(df)}")
            
            # API 호출
            response = requests.post(
                f"{API_URL}/upload_csv",
                json={
                    "data": df_clean.to_dict(orient='records'),
                    "entity_column": entity_column,
                    "entity_type": entity_type,
                    "property_columns": property_columns
                },
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                nodes = result.get('nodes_created', 0)
                total_nodes += nodes
                print(f"  ✓ {nodes} nodes created")
            else:
                print(f"  ✗ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"\n✓ Total nodes created: {total_nodes}")

if __name__ == "__main__":
    print("="*70)
    print("Loading Baseline CSV Data")
    print("="*70)
    load_csv_files()
    print("\n"+"="*70)
    print("✓ Complete")
    print("="*70)
