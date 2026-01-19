#!/usr/bin/env python3
"""
작은 PDF들만 빠르게 Neo4j에 업로드
"""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

load_dotenv()

API_URL = "http://localhost:8000"


def upload_pdf_via_api(pdf_path: Path):
    """API 엔드포인트를 사용하여 PDF 업로드"""
    print(f"\n{'='*70}")
    print(f"📄 {pdf_path.name}")
    print(f"{'='*70}")
    
    size_kb = pdf_path.stat().st_size / 1024
    print(f"   📊 크기: {size_kb:.1f} KB")
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path.name, f, 'application/pdf')}
            
            print(f"   ⏳ 업로드 중...")
            response = requests.post(
                f"{API_URL}/ingest_pdf_db",
                files=files,
                timeout=600  # 10분
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 성공!")
                print(f"      - 엔티티: {result.get('entities_extracted', 0)}")
                print(f"      - 관계: {result.get('relationships_extracted', 0)}")
                print(f"      - 텍스트 길이: {result.get('text_length', 0)}")
                return True
            else:
                print(f"   ❌ 실패: HTTP {response.status_code}")
                print(f"      {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"   ❌ 에러: {str(e)[:200]}")
        return False


def main():
    """메인 함수"""
    print("=" * 70)
    print("🚀 작은 PDF들을 Neo4j에 빠르게 업로드")
    print("=" * 70)
    
    # 서버 상태 확인
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ API 서버가 실행 중이지 않습니다.")
            print("   ./restart.sh 를 실행하세요.")
            sys.exit(1)
        print("✅ API 서버 연결 성공")
    except Exception as e:
        print(f"❌ API 서버에 연결할 수 없습니다: {e}")
        print("   ./restart.sh 를 실행하세요.")
        sys.exit(1)
    
    # PDF 파일 목록 (작은 것만)
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / 'data' / 'baseline'
    all_pdfs = list(data_dir.glob('*.pdf'))
    
    # 크기로 정렬하고 작은 것 4개만
    small_pdfs = sorted(all_pdfs, key=lambda p: p.stat().st_size)[:4]
    
    print(f"\n📚 선택된 PDF: {len(small_pdfs)}개 (작은 파일들)")
    for pdf in small_pdfs:
        size_kb = pdf.stat().st_size / 1024
        print(f"   - {pdf.name} ({size_kb:.1f} KB)")
    
    # 업로드
    success_count = 0
    
    for i, pdf in enumerate(small_pdfs, 1):
        print(f"\n진행: {i}/{len(small_pdfs)}")
        
        if upload_pdf_via_api(pdf):
            success_count += 1
    
    # 결과
    print(f"\n{'='*70}")
    print(f"✅ 완료: {success_count}/{len(small_pdfs)} 파일 업로드 성공")
    print(f"{'='*70}")
    
    # Neo4j 확인
    print("\n💡 Neo4j 데이터베이스에 저장되었습니다.")
    print("💡 Streamlit UI (http://localhost:8501)에서 확인하세요:")
    print("   - Visualization 탭에서 그래프 보기")
    print("   - Query 탭에서 질문하기")


if __name__ == "__main__":
    main()
