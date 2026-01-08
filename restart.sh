   # 변경 사항이 코드에 바로 반영되도록 reload 옵션을 사용하여 서버 실행

   # 기존 프로세스 종료
   lsof -ti:8000 | xargs kill -9
   lsof -ti:8501 | xargs kill -9

   # FastAPI 서버 (Auto-reload)
   cd /Users/gyuteoi/Desktop/graphrag/Finance_GraphRAG
   source .venv/bin/activate
   # --reload 옵션 사용 시 코드 변경 즉시 반영됨
   uvicorn src.app:app --reload &

   # Streamlit도 변경 자동반영: 기본적으로 코드 변경 자동감지(따로 옵션 불필요)
   streamlit run src/streamlit_app.py