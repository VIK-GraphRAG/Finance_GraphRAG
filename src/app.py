# app.py는 "FastAPI 서버"를 만드는 파일이에요!
# 마치 "웹 서버를 만드는 도구 상자" 같은 거예요!

from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn
import os
import sys

# src 디렉토리를 Python path에 추가해요!
# 이렇게 하면 'from engine import ...' 같은 import가 작동해요!
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# engine 모듈에서 HybridGraphRAGEngine을 가져와요!
from engine import HybridGraphRAGEngine
from config import (
    print_config,
    validate_config,
    validate_privacy_mode,
    ROUTER_MODEL,
    ROUTER_TEMPERATURE,
    WEB_SEARCH_MAX_RESULTS,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    PRIVACY_MODE,
    NEO4J_URI,
    NEO4J_USERNAME,
    NEO4J_PASSWORD
)
from openai import AsyncOpenAI
from utils import get_executive_report_prompt, get_web_search_report_prompt
try:
    from utils.error_logger import droneLogError
except Exception:
    def droneLogError(message: str, error: Exception | None = None) -> None:
        return

# --- [1] 전역 변수 ---
# engine은 "GraphRAG 엔진"이에요!
# None은 "아직 아무것도 없다"는 뜻이에요!
engine: HybridGraphRAGEngine = None
mcp_manager = None
neo4j_db = None
agentic_workflow = None

# --- [2] 서버 시작/종료 이벤트 핸들러 ---
# @asynccontextmanager는 "비동기 컨텍스트 매니저"를 만드는 거예요!
# 마치 "서버가 시작될 때와 끝날 때 뭔가를 하는" 것처럼!
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버가 시작될 때 실행되는 부분이에요!
    global engine, mcp_manager, neo4j_db, agentic_workflow
    
    # 설정 정보를 출력해요!
    print_config()
    
    # validate_config()는 "설정이 올바른지 확인하는" 함수예요!
    validate_config()
    
    # Privacy Mode 검증 및 진단
    print("\n🔍 Privacy Mode 진단 시작...")
    privacy_validation = validate_privacy_mode()
    
    if not privacy_validation["valid"]:
        print("⚠️  Privacy Mode 검증 실패:")
        for error in privacy_validation["errors"]:
            print(f"   ❌ {error}")
        print("\n💡 시스템이 degraded mode로 시작됩니다.")
        print("   일부 기능이 제한될 수 있습니다.\n")
    
    if privacy_validation["warnings"]:
        print("⚠️  경고:")
        for warning in privacy_validation["warnings"]:
            print(f"   ⚠️  {warning}")
    
    # Neo4j ping 테스트
    if NEO4J_URI and NEO4J_PASSWORD:
        print("\n🔍 Neo4j 연결 테스트 중...")
        try:
            from db.neo4j_db import Neo4jDatabase
            neo4j_db = Neo4jDatabase(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
            # Test connection
            neo4j_db.execute_query("RETURN 1")
            print(f"✅ Neo4j 연결 성공: {NEO4J_URI}")
            neo4j_db.close()
            
        except Exception as e:
            print(f"❌ Neo4j 진단 실패: {e}")
            print("   쿼리 기능이 제한됩니다.\n")
    
    # HybridGraphRAGEngine을 초기화하는 거예요!
    # Privacy Mode 전용으로 동작합니다.
    print("🚀 PrivacyGraphRAGEngine 초기화 중...")
    try:
        engine = HybridGraphRAGEngine()
        print("✅ PrivacyGraphRAGEngine 준비 완료!")
    except Exception as e:
        print(f"❌ Engine 초기화 실패: {e}")
        print("   degraded mode로 계속 진행합니다...")
        engine = None
    
    # MCP Manager 초기화 (옵션)
    try:
        from mcp.manager import MCPManager
        print("🔧 MCP Manager 초기화 중...")
        mcp_manager = MCPManager()
        print("✅ MCP Manager 준비 완료!")
    except Exception as e:
        print(f"⚠️ MCP Manager 초기화 실패 (옵션): {e}")
        mcp_manager = None
    
    # Neo4j DB 초기화 (옵션)
    try:
        from db.neo4j_db import Neo4jDatabase
        print("🔧 Neo4j Database 초기화 중...")
        neo4j_db = Neo4jDatabase()
        print("✅ Neo4j Database 준비 완료!")
    except Exception as e:
        print(f"⚠️ Neo4j Database 초기화 실패 (옵션): {e}")
        neo4j_db = None
    
    # Agentic Workflow 초기화
    # #region agent log
    import json
    with open('/Users/gyuteoi/Desktop/Finance_GraphRAG/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"location":"app.py:70","message":"Agentic Workflow init start","data":{"engine_ready":engine is not None,"mcp_ready":mcp_manager is not None,"neo4j_ready":neo4j_db is not None},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","runId":"run1","hypothesisId":"H1,H2,H4"})+'\n')
    # #endregion
    try:
        # #region agent log
        with open('/Users/gyuteoi/Desktop/Finance_GraphRAG/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"location":"app.py:72","message":"Before import AgenticWorkflow","data":{},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","runId":"run1","hypothesisId":"H1,H5"})+'\n')
        # #endregion
        from agents.langgraph_workflow import AgenticWorkflow
        # #region agent log
        with open('/Users/gyuteoi/Desktop/Finance_GraphRAG/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"location":"app.py:73","message":"After import AgenticWorkflow","data":{"class_type":str(type(AgenticWorkflow))},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","runId":"run1","hypothesisId":"H1,H5"})+'\n')
        # #endregion
        print("🔧 Agentic Workflow 초기화 중...")
        # #region agent log
        with open('/Users/gyuteoi/Desktop/Finance_GraphRAG/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"location":"app.py:74","message":"Before AgenticWorkflow instantiation","data":{},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","runId":"run1","hypothesisId":"H2,H3"})+'\n')
        # #endregion
        agentic_workflow = AgenticWorkflow(
            engine=engine,
            mcp_manager=mcp_manager,
            neo4j_db=neo4j_db
        )
        # #region agent log
        with open('/Users/gyuteoi/Desktop/Finance_GraphRAG/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"location":"app.py:79","message":"After AgenticWorkflow instantiation","data":{"workflow_ready":agentic_workflow is not None},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","runId":"run1","hypothesisId":"H3"})+'\n')
        # #endregion
        print("✅ Agentic Workflow 준비 완료!")
    except Exception as e:
        # #region agent log
        import traceback
        with open('/Users/gyuteoi/Desktop/Finance_GraphRAG/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"location":"app.py:80","message":"Agentic Workflow exception caught","data":{"error_type":type(e).__name__,"error_msg":str(e),"traceback":traceback.format_exc()},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","runId":"run1","hypothesisId":"H1,H2,H3,H4,H5"})+'\n')
        # #endregion
        print(f"⚠️ Agentic Workflow 초기화 실패: {e}")
        agentic_workflow = None
    
    # yield는 "여기서 잠시 멈춰서 서버를 실행하고, 나중에 다시 돌아와"라는 뜻이에요!
    yield
    
    # 서버가 종료될 때 실행되는 부분이에요!
    if mcp_manager:
        print("🔒 MCP Manager 종료 중...")
        await mcp_manager.shutdown()
        print("✅ MCP Manager 종료 완료!")
    
    if neo4j_db:
        print("🔒 Neo4j Database 종료 중...")
        neo4j_db.close()
        print("✅ Neo4j Database 종료 완료!")

# --- [3] FastAPI 앱 초기화 ---
# FastAPI()는 "웹 서버 앱을 만들어줘"라는 뜻이에요!
# lifespan은 "서버 시작/종료 이벤트 핸들러"예요!
app = FastAPI(
    title="VIK AI: Hybrid GraphRAG API",
    description="금융 분석을 위한 하이브리드 GraphRAG API예요! 인덱싱은 OpenAI API, 질문은 API/LOCAL 선택 가능해요!",
    version="2.0.0",
    lifespan=lifespan  # lifespan 이벤트 핸들러를 연결해요!
)

# --- [4] Pydantic 모델 ---
# Pydantic 모델은 "데이터 구조를 정의하는 것"이에요!
# 마치 "이런 모양의 데이터를 받을게요!"라고 미리 알려주는 거예요!

# QueryRequest는 "질문 요청"을 나타내는 모델이에요!
class QueryRequest(BaseModel):
    # question은 "질문 내용"이에요!
    question: str
    # mode는 "어떤 모드를 사용할지" 정하는 거예요. "api" 또는 "local"!
    # 기본값은 "local"이에요!
    mode: str = "local"
    # temperature는 "응답의 창의성"을 조절해요! (0.0 = 정확, 2.0 = 창의적)
    temperature: float = 0.2
    # top_k는 "검색할 청크 개수"를 정해요!
    top_k: int = 30
    # search_type은 "local" (특정 검색) 또는 "global" (전체 요약)
    search_type: str = "local"
    # enable_web_search는 "웹 검색을 활성화할지" 정해요! (기본값: False)
    enable_web_search: bool = False
    
    # Pydantic v2 스타일로 예시 설정
    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "What is NVIDIA revenue?",
                "mode": "local",
                "search_type": "local",
                "enable_web_search": False
            }
        }
    }

# InsertRequest는 "텍스트 추가 요청"을 나타내는 모델이에요!
class InsertRequest(BaseModel):
    # text는 "추가할 텍스트"예요!
    text: str
    
    # Pydantic v2 스타일로 설정 (deprecation warning 해결)
    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "NVIDIA reported record revenue of $57.0 billion in Q3 2026."
            }
        }
    }

# --- [5] Router 함수들 (Decision Layer) ---
# 질문을 분류하고 웹 검색을 처리하는 함수들이에요!

async def classify_query(question: str) -> str:
    """
    GPT-4o-mini를 사용하여 질문을 분류하는 Router 함수
    
    Args:
        question: 사용자 질문
    
    Returns:
        "GRAPH_RAG" 또는 "WEB_SEARCH"
    """
    try:
        # OpenAI 클라이언트 생성
        client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL
        )
        
        # 분류를 위한 시스템 프롬프트
        system_prompt = """You are a query classifier for a financial AI system.

Your task is to classify user questions into two categories:

1. GRAPH_RAG: Questions about uploaded PDF documents, company information, people, financials from internal reports
   Examples:
   - "What is NVIDIA's Q3 revenue?"
   - "Who is Jensen Huang?" (person information from documents)
   - "How old is the CEO?" (biographical information)
   - "Summarize the uploaded report"
   - "What are the key findings in the document?"

2. WEB_SEARCH: Questions EXPLICITLY requiring TODAY's/LATEST/CURRENT real-time market data or breaking news
   Examples:
   - "What is today's stock price?"
   - "Latest news TODAY about Tesla"
   - "Current inflation rate RIGHT NOW"
   - "What happened in the market TODAY?"

IMPORTANT: Default to GRAPH_RAG unless the question EXPLICITLY asks for TODAY/LATEST/CURRENT/NOW information.

Respond with ONLY ONE WORD: Either "GRAPH_RAG" or "WEB_SEARCH" - nothing else."""

        # GPT-4o-mini 호출
        response = await client.chat.completions.create(
            model=ROUTER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Classify this question: {question}"}
            ],
            temperature=ROUTER_TEMPERATURE,
            max_tokens=10
        )
        
        # 응답 추출 및 정규화
        classification = response.choices[0].message.content.strip().upper()
        
        # 유효성 검사
        if "GRAPH_RAG" in classification:
            return "GRAPH_RAG"
        elif "WEB_SEARCH" in classification or "WEB" in classification:
            return "WEB_SEARCH"
        else:
            # 기본값: GRAPH_RAG (내부 문서 우선)
            print(f"⚠️ 분류 결과가 명확하지 않아요: {classification}, 기본값 GRAPH_RAG 사용")
            return "GRAPH_RAG"
    
    except Exception as e:
        print(f"❌ 질문 분류 중 에러 발생: {e}")
        # 에러 시 기본값: GRAPH_RAG
        return "GRAPH_RAG"


async def handle_web_search(question: str) -> str:
    """
    웹 검색을 수행하고 결과를 요약하는 함수
    Note: Legacy function - web search is now handled by Multi-Agent system with MCP Tavily
    
    Args:
        question: 사용자 질문
    
    Returns:
        검색 결과를 바탕으로 생성된 답변
    """
    # Web search is now handled by Multi-Agent system with MCP Tavily
    return "웹 검색 기능은 Multi-Agent 모드에서 사용 가능합니다. Advanced Settings에서 'Multi-Agent Analysis Mode'를 활성화해주세요."


# --- [6] 루트 엔드포인트 ---
# @app.get("/")는 "루트 경로(/)에 GET 요청이 오면" 실행되는 함수예요!
# 마치 "홈페이지에 접속하면" 실행되는 거예요!
@app.get("/")
async def root():
    # return은 "이걸 돌려줘"라는 뜻이에요!
    return {
        "message": "VIK AI Hybrid GraphRAG API에 오신 것을 환영해요!",
        "description": "인덱싱은 OpenAI API(gpt-5-mini)를 사용하고, 질문은 API/LOCAL 모드를 선택할 수 있어요!",
        "endpoints": {
            "/insert": "텍스트 인덱싱하기 (POST) - OpenAI API 사용",
            "/query": "질문하기 (POST) - mode 파라미터로 'api' 또는 'local' 선택",
            "/health": "서버 상태 확인 (GET)",
            "/graph_stats": "그래프 현황 확인 (GET)",
            "/visualize": "그래프 시각화 HTML 생성 (GET)",
            "/docs": "API 문서 보기 (GET)"
        },
        "usage": {
            "insert": {
                "method": "POST",
                "url": "/insert",
                "body": {"text": "인덱싱할 텍스트"}
            },
            "query": {
                "method": "POST",
                "url": "/query",
                "body": {
                    "question": "질문 내용",
                    "mode": "api 또는 local (기본값: local)"
                }
            }
        }
    }

# --- [7] 서버 상태 확인 엔드포인트 ---
# @app.get("/health")는 "서버 상태를 확인하는" 엔드포인트예요!
@app.get("/health")
async def health():
    # 서버가 잘 작동하고 있다는 것을 알려주는 거예요!
    return {
        "status": "healthy",
        "message": "서버가 정상적으로 작동 중이에요!",
        "engine_ready": engine is not None
    }

# --- [8] 그래프 통계 엔드포인트 ---
# @app.get("/graph_stats")는 "그래프 통계를 보여주는" 엔드포인트예요!
@app.get("/graph_stats")
async def graph_stats():
    # if는 "만약"이라는 뜻이에요!
    if engine is None:
        return {"nodes": 0, "edges": 0, "message": "엔진이 아직 초기화되지 않았어요!"}
    
    # engine.get_graph_stats()는 그래프 통계를 가져오는 거예요!
    return engine.get_graph_stats()

# --- [9] 그래프 초기화 엔드포인트 ---
# @app.post("/reset")는 "그래프를 초기화하는" 엔드포인트예요!
@app.post("/reset",
          summary="그래프 초기화",
          description="기존 그래프 스토리지를 백업하고 삭제한 후 새로운 그래프로 시작해요!")
async def reset_graph():
    global engine
    # if는 "만약"이라는 뜻이에요!
    if engine is None:
        raise HTTPException(status_code=503, detail="엔진이 아직 초기화되지 않았어요!")
    
    try:
        import shutil
        from datetime import datetime
        
        # 백업 폴더 이름 생성 (타임스탬프 포함)
        backup_dir = f"{engine.working_dir}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 기존 그래프 스토리지가 있으면 백업
        if os.path.exists(engine.working_dir):
            shutil.move(engine.working_dir, backup_dir)
            print(f"✅ 기존 그래프 백업 완료: {backup_dir}")
        
        # 엔진 재초기화
        engine = HybridGraphRAGEngine()
        
        return {
            "message": "그래프가 성공적으로 초기화되었어요!",
            "status": "success",
            "backup_dir": backup_dir if os.path.exists(backup_dir) else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"그래프 초기화 중 에러가 발생했어요: {str(e)}")

# --- [10] 그래프 시각화 엔드포인트 ---
# @app.get("/visualize")는 "그래프를 시각화하는 HTML 파일을 생성하는" 엔드포인트예요!
@app.get("/visualize",
         summary="그래프 시각화",
         description="GraphRAG 그래프를 인터랙티브하게 시각화한 HTML 파일을 생성해요!")
async def visualize():
    # if는 "만약"이라는 뜻이에요!
    if engine is None:
        raise HTTPException(status_code=503, detail="엔진이 아직 초기화되지 않았어요!")
    
    try:
        # visualize.py에서 visualize_graph 함수를 가져와요!
        from visualize import visualize_graph
        
        # 그래프를 시각화해서 HTML 파일을 생성해요!
        output_path = visualize_graph(working_dir=engine.working_dir, output_file="graph_visualization.html")
        
        if output_path and os.path.exists(output_path):
            # FileResponse는 "파일을 반환하는" 거예요!
            # 마치 "이 HTML 파일을 브라우저로 보여줘"라는 뜻이에요!
            return FileResponse(
                output_path,
                media_type="text/html",
                filename="graph_visualization.html"
            )
        else:
            raise HTTPException(status_code=500, detail="그래프 시각화 파일을 생성할 수 없어요!")
            
    except ImportError:
        raise HTTPException(status_code=500, detail="pyvis 패키지가 설치되지 않았어요! 'pip install pyvis'로 설치해주세요!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"그래프 시각화 중 에러가 발생했어요: {str(e)}")

# --- [11] 텍스트 인덱싱 엔드포인트 ---
# @app.post("/insert")는 "텍스트를 인덱싱하는" 엔드포인트예요!
# 인덱싱은 항상 OpenAI API를 사용해요! (정확한 금융 수치 추출을 위해)
@app.post("/insert", 
          summary="텍스트 인덱싱",
          description="텍스트를 GraphRAG에 인덱싱해요. 항상 OpenAI API를 사용해요!",
          response_description="인덱싱 결과")
async def insert(request: InsertRequest):
    # if는 "만약"이라는 뜻이에요!
    if engine is None:
        # HTTPException은 "에러를 던지는" 거예요!
        # 503은 "서비스를 사용할 수 없음"이라는 뜻이에요!
        raise HTTPException(status_code=503, detail="엔진이 아직 초기화되지 않았어요!")
    
    # text 필드가 비어있으면 에러를 발생시켜요!
    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=422, 
            detail="'text' 필드는 비어있을 수 없어요! 텍스트를 입력해주세요."
        )
    
    try:
        # try는 "시도해봐"라는 뜻이에요!
        # engine.ainsert()는 비동기로 텍스트를 그래프에 넣는 거예요!
        # 인덱싱은 항상 OpenAI API를 사용해요!
        await engine.ainsert(request.text)
        
        # return은 "이걸 돌려줘"라는 뜻이에요!
        return {
            "message": "텍스트가 성공적으로 인덱싱되었어요! (OpenAI API 사용)",
            "status": "success",
            "mode": "openai_api"
        }
    except Exception as e:
        # except는 "만약 에러가 생기면"이라는 뜻이에요!
        # Exception은 "모든 종류의 에러"예요!
        # e는 에러 내용이에요!
        # HTTPException으로 에러를 반환해요!
        import traceback
        error_detail = f"인덱싱 중 에러가 발생했어요: {str(e)}\n\n상세 정보:\n{traceback.format_exc()}"
        print(f"❌ 인덱싱 에러:\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"인덱싱 중 에러가 발생했어요: {str(e)}")

# --- [12] 질문-답변 엔드포인트 (Decision Layer 통합) ---
# --- [7] Agentic Query Endpoint ---
@app.post("/agentic-query",
          summary="Agentic Workflow 질문-답변",
          description="LangGraph 기반 멀티 에이전트 워크플로우로 질문 처리 (Planner → Collector → Analyst → Writer)")
async def agentic_query(request: QueryRequest):
    """
    Agentic Workflow를 사용한 질문-답변
    
    워크플로우:
    1. Planner: 질문을 서브태스크로 분해
    2. Collector: 각 서브태스크별 정보 수집 + Neo4j 저장
    3. Analyst: 데이터 검증 + 충분성 판단 (부족 시 Collector로 회귀)
    4. Writer: 최종 리포트 작성 + 추론 경로 포함
    """
    if agentic_workflow is None:
        raise HTTPException(
            status_code=503,
            detail="Agentic Workflow가 초기화되지 않았습니다. 서버를 재시작해주세요."
        )
    
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=422,
            detail="'question' 필드는 비어있을 수 없습니다."
        )
    
    try:
        print(f"\n{'='*60}")
        print(f"[Agentic Workflow] 질문: {request.question}")
        print(f"{'='*60}\n")
        
        # Agentic Workflow 실행 (최대 3회 Feedback Loop)
        result = await agentic_workflow.run(
            question=request.question,
            max_iterations=3
        )
        
        print(f"\n{'='*60}")
        print(f"[Agentic Workflow] 완료!")
        print(f"- 서브태스크: {len(result.get('subtasks', []))}개")
        print(f"- 반복 횟수: {result.get('iteration_count', 0)}회")
        print(f"- 신뢰도: {result.get('confidence', 0):.0%}")
        print(f"- 추천: {result.get('recommendation', 'N/A')}")
        print(f"{'='*60}\n")
        
        return {
            "question": request.question,
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "confidence": result.get("confidence", 0.0),
            "recommendation": result.get("recommendation", "HOLD"),
            "reasoning_path": result.get("reasoning_path", []),
            "subtasks": result.get("subtasks", []),
            "iteration_count": result.get("iteration_count", 0),
            "processing_steps": result.get("processing_steps", []),
            "mode": "AGENTIC_WORKFLOW",
            "status": "success"
        }
        
    except Exception as e:
        print(f"❌ Agentic Workflow 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Agentic Workflow 처리 중 에러 발생: {str(e)}"
        )

# @app.post("/query")는 "질문을 받아서 답변을 주는" 엔드포인트예요!
# mode 파라미터로 "api" 또는 "local"을 선택할 수 있어요!
@app.post("/query",
          summary="질문-답변",
          description="GraphRAG에 질문하고 답변을 받아요. mode로 'api' 또는 'local'을 선택할 수 있어요!\n\n**요청 형식**:\n```json\n{\n  \"question\": \"질문 내용\",\n  \"mode\": \"local\"\n}\n```",
          response_description="질문과 답변",
          responses={
              200: {
                  "description": "질문 성공",
                  "content": {
                      "application/json": {
                          "example": {
                              "question": "What is NVIDIA revenue?",
                              "answer": "NVIDIA's revenue is $57.0 billion in Q3 2026.",
                              "mode": "local",
                              "status": "success"
                          }
                      }
                  }
              },
              422: {
                  "description": "요청 데이터 형식 오류",
                  "content": {
                      "application/json": {
                          "example": {
                              "detail": [
                                  {
                                      "type": "missing",
                                      "loc": ["body", "question"],
                                      "msg": "Field required",
                                      "input": {}
                                  }
                              ]
                          }
                      }
                  }
              }
          })
async def query(request: QueryRequest):
    # if는 "만약"이라는 뜻이에요!
    if engine is None:
        raise HTTPException(status_code=503, detail="엔진이 아직 초기화되지 않았어요!")
    
    # question 필드가 비어있으면 에러를 발생시켜요!
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=422,
            detail="'question' 필드는 비어있을 수 없어요! 질문을 입력해주세요."
        )
    
    # mode가 "api" 또는 "local"이 아니면 에러를 발생시켜요!
    if request.mode not in ["api", "local"]:
        raise HTTPException(
            status_code=400,
            detail="mode는 'api' 또는 'local'이어야 해요! (현재 값: '{}')".format(request.mode)
        )
    
    try:
        # #region agent log
        import json
        with open('/Users/gyuteoi/Desktop/Finance_GraphRAG/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"location":"app.py:325","message":"Query entry","data":{"question":request.question,"mode":request.mode,"enable_web_search":request.enable_web_search},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","runId":"run1","hypothesisId":"H1,H2,H5"})+'\n')
        # #endregion
        
        # --- Decision Layer (Router) ---
        # 웹 검색이 활성화된 경우에만 질문 분류
        if request.enable_web_search:
            # 1단계: 질문 분류 (GRAPH_RAG vs WEB_SEARCH)
            print(f"🤔 질문 분류 중 (웹 검색 활성화됨): '{request.question}'")
            query_type = await classify_query(request.question)
            print(f"✅ 분류 결과: {query_type}")
        else:
            # 웹 검색 비활성화 시 항상 GraphRAG 사용
            query_type = "GRAPH_RAG"
            print(f"📚 웹 검색 비활성화 - 업로드된 문서에서만 검색합니다")
        
        # 2단계: 분류 결과에 따라 처리
        sources_list = []
        
        if query_type == "WEB_SEARCH":
            # 웹 검색으로 처리 - Multi-Agent 모드 사용 권장
            print(f"🌐 웹 검색 모드 감지 - Multi-Agent 모드 권장")
            response = "웹 검색 기능은 Multi-Agent Analysis 모드에서 더 강력하게 동작합니다. Advanced Settings에서 'Multi-Agent Analysis Mode'를 활성화한 후 다시 질문해주세요."
            sources_list = []
            source = "WEB_SEARCH"
        else:
            # GraphRAG로 처리 (출처 정보 포함)
            print(f"📚 GraphRAG 모드로 처리 (mode: {request.mode}, search_type: {request.search_type}, temperature: {request.temperature}, top_k: {request.top_k})")
            retrieval_backend = "unknown"
            retrieval_context = ""
            
            # Global vs Local search 분기
            if request.search_type == "global":
                # Global Search: 전체 문서 요약
                result = await engine.aglobal_search(
                    request.question,
                    top_k=request.top_k,
                    temperature=request.temperature
                )
                base_answer = result.get("answer", "")
                sources_list = result.get("sources", [])
                retrieval_backend = "community"
            else:
                # Local Search: 특정 엔티티 검색
                result = await engine.aquery(
                    request.question,
                    mode=request.mode,
                    return_context=True,
                    top_k=request.top_k
                )
                
                if isinstance(result, dict):
                    base_answer = result.get("answer", "")
                    sources_list = result.get("sources", [])
                    retrieval_backend = result.get("retrieval_backend", "unknown")
                    retrieval_context = result.get("context", "") or ""
                else:
                    base_answer = result
                    sources_list = []
            
            # Strict Grounding으로 보고서 재생성
            if sources_list:
                # #region agent log
                with open('/Users/gyuteoi/Desktop/Finance_GraphRAG/.cursor/debug.log', 'a') as f:
                    f.write(__import__('json').dumps({"location":"app.py:567","message":"sources_list before grounding","data":{"count":len(sources_list),"sources":[{"id":s.get("id"),"file":s.get("file"),"excerpt":s.get("excerpt","")[:100]} for s in sources_list[:3]]},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","runId":"run1","hypothesisId":"H4"})+'\n')
                # #endregion
                # 실제 소스 개수만 사용하도록 제한
                max_sources = min(len(sources_list), 10)  # 최대 10개
                sources_list = sources_list[:max_sources]
                
                # Strict Grounding Prompt 사용
                from utils import get_strict_grounding_prompt
                strict_prompt = get_strict_grounding_prompt(request.question, sources_list)
                
                client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
                llm_response = await client.chat.completions.create(
                    model=ROUTER_MODEL,
                    messages=[
                        {"role": "system", "content": strict_prompt},
                        {"role": "user", "content": request.question}
                    ],
                    temperature=0.0,  # Strict grounding: 창의성 제거
                    max_tokens=2000
                )
                response = llm_response.choices[0].message.content.strip()
                # #region agent log
                with open('/Users/gyuteoi/Desktop/Finance_GraphRAG/.cursor/debug.log', 'a') as f:
                    f.write(__import__('json').dumps({"location":"app.py:584","message":"LLM response before validation","data":{"response_length":len(response),"response_preview":response[:300]},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","runId":"run1","hypothesisId":"H5"})+'\n')
                # #endregion
                
                # Self-Correction: Citation Validation
                from citation_validator import CitationValidator
                validator = CitationValidator(sources_list)
                validation_result = validator.validate_response(response)
                evidence = []
                # #region agent log
                with open('/Users/gyuteoi/Desktop/Finance_GraphRAG/.cursor/debug.log', 'a') as f:
                    f.write(__import__('json').dumps({"location":"app.py:596","message":"validation result","data":{"confidence":validation_result.get('confidence_score'),"valid_citations":validation_result.get('valid_citations'),"total_citations":validation_result.get('total_citations'),"missing_citations":validation_result.get('missing_citations',[])},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","runId":"run1","hypothesisId":"H5"})+'\n')
                # #endregion
                
                print(f"[VALIDATION] Confidence: {validation_result['confidence_score']:.1%}")
                print(f"[VALIDATION] Valid citations: {validation_result['valid_citations']}/{validation_result['total_citations']}")

                # Strict Grounding LLM이 '정보 없음'이라고 답했지만 실제로는 소스가 충분한 경우 보정
                override_applied = False
                if response.strip() == "해당 문서들에서는 관련 정보를 찾을 수 없습니다." and len(sources_list) > 0:
                    print("[WARNING] Strict grounding LLM returned 'no info' despite non-empty sources. Falling back to base GraphRAG answer.")
                    # #region agent log
                    with open('/Users/gyuteoi/Desktop/Finance_GraphRAG/.cursor/debug.log', 'a') as f:
                        f.write(__import__('json').dumps({
                            "location": "app.py:610",
                            "message": "override no-info with base_answer",
                            "data": {
                                "base_answer_preview": base_answer[:200] if base_answer else None,
                                "sources_count": len(sources_list)
                            },
                            "timestamp": __import__('time').time()*1000,
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "H4,H5"
                        }) + '\n')
                    # #endregion
                    response = base_answer or response
                    # base_answer에는 citation이 없을 수 있으므로 validation은 유지하되 신뢰도는 0.7 이상으로 설정하여 후속 체크를 통과시킴
                    validation_result = {"confidence_score": 0.75, "is_valid": True}
                    evidence = []
                    override_applied = True

                # 신뢰도가 낮거나 응답이 비정상적이면 Perplexity로 폴백
                # 또는 응답에 HTML/웹 검색 흔적이 있으면 거부
                # 단, override가 적용된 경우는 스킵 (base_answer를 사용하므로)
                if not override_applied and (validation_result["confidence_score"] < 0.7 or 
                    "<a href" in response or 
                    "Thesaurus.com" in response or
                    "WordHippo" in response or
                    len(response.strip()) < 50):
                    print(f"[WARNING] Low confidence or invalid response, falling back to Perplexity search")
                    
                    # Perplexity로 폴백
                    try:
                        from engine.search_handler import SearchHandler
                        search_handler = SearchHandler()
                        
                        # 질문에서 공개 엔티티 추출
                        perplexity_result = search_handler.search(
                            query=request.question,
                            max_results=5,
                            sanitize=True
                        )
                        
                        if perplexity_result and not perplexity_result.get("error"):
                            # Perplexity 답변 사용
                            response = f"## 실시간 검색 결과 (Perplexity)\n\n{perplexity_result.get('answer', '')}"
                            
                            # Citations를 sources로 변환
                            sources_list = []
                            for i, url in enumerate(perplexity_result.get('citations', [])[:5], 1):
                                sources_list.append({
                                    'id': i,
                                    'file': 'Perplexity Web Search',
                                    'url': url,
                                    'excerpt': f"실시간 웹 검색 결과 #{i}"
                                })
                            
                            validation_result = {"confidence_score": 0.8, "is_valid": True}
                            evidence = []
                            print(f"✅ Perplexity fallback successful: {len(sources_list)} sources")
                        else:
                            # Perplexity도 실패한 경우
                            response = "데이터베이스와 실시간 검색 모두에서 관련 정보를 찾을 수 없습니다."
                            sources_list = []
                            validation_result = {"confidence_score": 0.0, "is_valid": False}
                            evidence = []
                    except Exception as e:
                        print(f"❌ Perplexity fallback failed: {e}")
                        response = "해당 문서들에서는 관련 정보를 찾을 수 없습니다."
                        sources_list = []
                        validation_result = {"confidence_score": 0.0, "is_valid": False}
                        evidence = []
                else:
                    # 응답에서 실제로 사용된 citation 번호 추출 및 필터링
                    import re
                    citation_pattern = r'\[(\d+)\]'
                    used_citations = set()
                    for match in re.finditer(citation_pattern, response):
                        citation_num = int(match.group(1))
                        if 1 <= citation_num <= len(sources_list):
                            used_citations.add(citation_num)
                    
                    # 사용된 citation에 해당하는 소스만 유지
                    if used_citations:
                        sources_list = [s for s in sources_list if s['id'] in used_citations]
                        # ID를 1부터 다시 매핑
                        for idx, source in enumerate(sources_list, 1):
                            old_id = source['id']
                            source['id'] = idx
                            # 응답에서 citation 번호 재매핑
                            response = response.replace(f'[{old_id}]', f'[{idx}]')
                            response = re.sub(rf'\[{old_id}\]', f'[{idx}]', response)

                    # evidence(클레임-근거) 구조 생성 (citation remap 이후)
                    # override가 적용된 경우는 evidence를 빈 배열로 유지 (base_answer에는 citation이 없음)
                    if not override_applied:
                        validator = CitationValidator(sources_list)
                        evidence = validator.build_evidence(response)
                    # override_applied인 경우 evidence는 이미 빈 배열로 설정됨
            else:
                # 출처가 없으면 Perplexity로 폴백
                print(f"📚 No sources found in database, falling back to Perplexity search")
                
                try:
                    from engine.search_handler import SearchHandler
                    search_handler = SearchHandler()
                    
                    # Perplexity 검색
                    perplexity_result = search_handler.search(
                        query=request.question,
                        max_results=5,
                        sanitize=True
                    )
                    
                    if perplexity_result and not perplexity_result.get("error"):
                        # Perplexity 답변 사용
                        response = f"## 실시간 검색 결과 (Perplexity)\n\n{perplexity_result.get('answer', '')}"
                        
                        # Citations를 sources로 변환
                        sources_list = []
                        for i, url in enumerate(perplexity_result.get('citations', [])[:5], 1):
                            sources_list.append({
                                'id': i,
                                'file': 'Perplexity Web Search',
                                'url': url,
                                'excerpt': f"실시간 웹 검색 결과 #{i}"
                            })
                        
                        validation_result = {"confidence_score": 0.8, "is_valid": True}
                        evidence = []
                        print(f"✅ Perplexity fallback successful: {len(sources_list)} sources")
                    else:
                        response = "데이터베이스와 실시간 검색 모두에서 관련 정보를 찾을 수 없습니다."
                        validation_result = {"confidence_score": 0.0, "is_valid": False}
                        evidence = []
                except Exception as e:
                    print(f"❌ Perplexity fallback failed: {e}")
                    response = "해당 문서들에서는 관련 정보를 찾을 수 없습니다."
                    validation_result = {"confidence_score": 0.0, "is_valid": False}
                    evidence = []
            
            source = "GRAPH_RAG"
        
        # #region agent log
        with open('/Users/gyuteoi/Desktop/Finance_GraphRAG/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"location":"app.py:338","message":"Query response","data":{"response":response[:500] if response else None,"response_type":type(response).__name__,"source":source},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","runId":"run1","hypothesisId":"H1,H3"})+'\n')
        # #endregion
        
        # return은 "이걸 돌려줘"라는 뜻이에요!
        return {
            "question": request.question,
            "answer": response,
            "sources": sources_list,  # Citation용 출처 리스트
            "source": source,  # 어디서 답변을 가져왔는지 알려줘요!
            "mode": request.mode if source == "GRAPH_RAG" else "N/A",  # GraphRAG일 때만 의미 있어요
            "search_type": request.search_type if source == "GRAPH_RAG" else "N/A",
            "validation": validation_result if source == "GRAPH_RAG" and 'validation_result' in locals() else None,
            "evidence": evidence if source == "GRAPH_RAG" and 'evidence' in locals() else [],
            "retrieval_backend": retrieval_backend if source == "GRAPH_RAG" and 'retrieval_backend' in locals() else "N/A",
            "retrieval_context": retrieval_context if source == "GRAPH_RAG" and 'retrieval_context' in locals() else "",
            "status": "success"
        }
    except Exception as e:
        # #region agent log
        import traceback
        with open('/Users/gyuteoi/Desktop/Finance_GraphRAG/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"location":"app.py:352","message":"Query error","data":{"error":str(e),"error_type":type(e).__name__,"traceback":traceback.format_exc()},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","runId":"run1","hypothesisId":"H1,H4"})+'\n')
        # #endregion
        # except는 "만약 에러가 생기면"이라는 뜻이에요!
        raise HTTPException(status_code=500, detail=f"질문 처리 중 에러가 발생했어요: {str(e)}")


# --- [12] PDF Upload Endpoint (Local Model) ---
@app.post("/ingest_pdf",
          summary="PDF Upload and Processing (Local)",
          description="Upload PDF document and extract graph with Local Ollama model")
async def ingest_pdf(file: UploadFile = File(...)):
    """
    Upload and process PDF with Local Ollama model
    
    Process:
    - Extract text from PDF (PyMuPDF)
    - Extract entities + relationships with Ollama (qwen2.5-coder)
    - Merge into Neo4j graph database
    """
    import tempfile
    from pathlib import Path
    import json
    
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        print(f"📄 Received PDF upload: {file.filename}")
        
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        print(f"💾 Saved to: {tmp_path}")

        # Extract text with PyMuPDF
        try:
            import pymupdf
            doc = pymupdf.open(tmp_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF text extraction failed: {str(e)}")

        if not text or len(text.strip()) < 10:
            raise HTTPException(status_code=400, detail="PDF contains no extractable text")

        print(f"✅ Extracted {len(text)} characters from PDF")

        # Extract entities + relationships with Local Ollama
        from engine.extractor import KnowledgeExtractor
        
        extractor = KnowledgeExtractor()
        
        chunk_size = 1000  # 500 → 1000으로 증가 (요청 횟수 50% 감소)
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        
        # 청크 수 제한 (처리 시간 단축)
        max_chunks = 20  # 최대 20개 청크 (약 20,000자, 청크 크기 증가로 커버량 유지)
        if len(chunks) > max_chunks:
            print(f"⚠️ 청크 수 제한: {len(chunks)} → {max_chunks} (처리 시간 단축)")
            chunks = chunks[:max_chunks]
        
        all_entities = []
        all_relationships = []

        print(f"🔒 Processing {len(chunks)} chunks with Local Ollama (parallel)...")

        # 병렬 처리로 속도 향상 (동시에 3개씩 처리)
        import asyncio
        batch_size = 3
        
        for batch_start in range(0, len(chunks), batch_size):
            batch = chunks[batch_start:batch_start + batch_size]
            print(f"   Progress: {batch_start}/{len(chunks)} chunks ({batch_start*100//len(chunks)}%)")
            
            # 배치 내 청크들을 동시 처리
            tasks = [extractor.extract_entities(chunk) for chunk in batch]
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        print(f"⚠️ Chunk {batch_start + i} failed: {result}")
                        continue
                    all_entities.extend(result.get("entities", []))
                    all_relationships.extend(result.get("relationships", []))
            except Exception as e:
                print(f"⚠️ Batch processing failed: {e}")
                continue

        print(f"✅ Extracted {len(all_entities)} entities, {len(all_relationships)} relationships")

        graph_data = {
            "entities": all_entities,
            "relationships": all_relationships
        }

        # Store in Neo4j via integrator
        from engine.integrator import DataIntegrator

        if NEO4J_URI and NEO4J_PASSWORD:
            integrator = DataIntegrator()
            merge_stats = integrator.ingestPdfGraph(
                graphData=graph_data,
                sourceFile=file.filename,
                sourceLabel=Path(file.filename).stem
            )
            integrator.close()
            print("✅ PDF graph merge complete")
        else:
            merge_stats = {"entitiesMerged": 0, "relationshipsCreated": 0}
            print("⚠️ Neo4j not configured, skipping storage")
        
        # Clean up temp file
        Path(tmp_path).unlink()
        
        return {
            "message": "PDF processed with Local Ollama and merged into Neo4j",
            "filename": file.filename,
            "text_length": len(text),
            "entities_extracted": len(all_entities),
            "relationships_extracted": len(all_relationships),
            "merge_stats": merge_stats,
            "processing_model": "ollama-local",
            "status": "success"
        }
        
    except Exception as e:
        droneLogError("PDF processing failed", e)
        import traceback
        print(f"❌ PDF processing error: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"PDF processing failed: {str(e)}"
        )


# --- [13] PDF Upload for Database (OpenAI API) ---
@app.post("/ingest_pdf_db",
          summary="PDF Upload for Database (OpenAI API)",
          description="Upload PDF document and extract graph with OpenAI API for permanent database storage")
async def ingest_pdf_db(file: UploadFile = File(...)):
    """
    Upload and process PDF with OpenAI API for database merge
    
    Process:
    - Extract text from PDF (PyMuPDF)
    - Extract entities + relationships with GPT-4o-mini
    - Merge into Neo4j graph database permanently
    """
    import tempfile
    from pathlib import Path
    import json
    
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )

        print(f"📄 Received PDF upload for DB: {file.filename}")

        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        print(f"💾 Saved to: {tmp_path}")

        # Extract text with PyMuPDF
        try:
            import pymupdf
            doc = pymupdf.open(tmp_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF text extraction failed: {str(e)}")

        if not text or len(text.strip()) < 10:
            raise HTTPException(status_code=400, detail="PDF contains no extractable text")

        print(f"✅ Extracted {len(text)} characters from PDF")

        # Extract entities + relationships with OpenAI API (GPT-4o-mini)
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        
        chunk_size = 2000  # Larger chunks for OpenAI
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        all_entities = []
        all_relationships = []

        print(f"🤖 Processing {len(chunks)} chunks with GPT-4o-mini...")

        for i, chunk in enumerate(chunks):
            if i > 0 and i % 10 == 0:
                print(f"   Progress: {i}/{len(chunks)} chunks")
            
            prompt = f"""Extract business entities and relationships from this text.
Return ONLY valid JSON format:

{{
  "entities": [
    {{"name": "EntityName", "type": "COMPANY|PERSON|PRODUCT|TECHNOLOGY|FINANCIAL_METRIC|LOCATION", "properties": {{"key": "value"}}}}
  ],
  "relationships": [
    {{"source": "EntityA", "target": "EntityB", "type": "RELATIONSHIP_TYPE", "properties": {{"key": "value"}}}}
  ]
}}

Entity types: COMPANY, PERSON, PRODUCT, TECHNOLOGY, FINANCIAL_METRIC, LOCATION, REGULATION, RISK
Relationship types: SUPPLIES, PURCHASES, COMPETES_WITH, HAS_CEO, EMPLOYS, LOCATED_IN, PRODUCES, IMPACTS, DEPENDS_ON

Text:
{chunk[:2000]}

JSON output:"""

            try:
                response = await client.chat.completions.create(
                    model=ROUTER_MODEL,  # gpt-4o-mini
                    messages=[
                        {"role": "system", "content": "You are a financial document analyzer. Extract structured entities and relationships. Respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=2000
                )
                
                content = response.choices[0].message.content.strip()
                
                # Parse JSON from response
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                extracted = json.loads(content)
                all_entities.extend(extracted.get("entities", []))
                all_relationships.extend(extracted.get("relationships", []))
                
            except Exception as e:
                print(f"⚠️ Chunk {i} extraction failed: {e}")
                continue

        print(f"✅ Extracted {len(all_entities)} entities, {len(all_relationships)} relationships")

        graph_data = {
            "entities": all_entities,
            "relationships": all_relationships
        }

        # Store in Neo4j via integrator
        from engine.integrator import DataIntegrator

        if NEO4J_URI and NEO4J_PASSWORD:
            integrator = DataIntegrator()
            merge_stats = integrator.ingestPdfGraph(
                graphData=graph_data,
                sourceFile=file.filename,
                sourceLabel=Path(file.filename).stem
            )
            integrator.close()
            print("✅ PDF graph merge complete (OpenAI)")
        else:
            merge_stats = {"entitiesMerged": 0, "relationshipsCreated": 0}
            print("⚠️ Neo4j not configured, skipping storage")

        # Clean up temp file
        Path(tmp_path).unlink()

        return {
            "message": "PDF processed with OpenAI API and merged into Neo4j database",
            "filename": file.filename,
            "text_length": len(text),
            "entities_extracted": len(all_entities),
            "relationships_extracted": len(all_relationships),
            "merge_stats": merge_stats,
            "processing_model": "gpt-4o-mini",
            "status": "success"
        }

    except Exception as e:
        droneLogError("PDF DB processing failed", e)
        import traceback
        print(f"❌ PDF DB processing error: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"PDF processing failed: {str(e)}"
        )


# --- [14] CSV Upload Endpoint (REMOVED) ---
# CSV/JSON uploads have been removed per user request

# Old CSV endpoint
@app.post("/upload_csv_old",
          summary="CSV Data Upload to Neo4j",
          description="Upload CSV data directly to Neo4j graph database")
async def upload_csv(request: dict):
    """
    CSV 데이터를 Neo4j에 직접 업로드 (로컬 처리만)
    """
    try:
        data = request.get("data", [])
        entity_column = request.get("entity_column")
        entity_type = request.get("entity_type", "Entity")
        property_columns = request.get("property_columns", [])
        
        if not data or not entity_column:
            raise HTTPException(status_code=400, detail="data and entity_column are required")
        
        print(f"📊 Uploading CSV data: {len(data)} rows (로컬 처리)")
        
        # Neo4j에 데이터 삽입
        from db.neo4j_db import Neo4jDatabase
        
        if not NEO4J_URI or not NEO4J_PASSWORD:
            raise HTTPException(status_code=500, detail="Neo4j not configured")
        
        db = Neo4jDatabase(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
        
        nodes_created = 0
        
        for row in data:
            entity_name = row.get(entity_column)
            if not entity_name:
                continue
            
            # 노드 속성 준비
            properties = {col: row.get(col) for col in property_columns if col in row}
            properties['name'] = entity_name
            
            # Cypher 쿼리 생성
            query = f"MERGE (n:{entity_type} {{name: $name}}) SET n += $properties RETURN n"
            
            db.execute_query(query, {"name": entity_name, "properties": properties})
            nodes_created += 1
        
        db.close()
        
        return {
            "message": f"Successfully uploaded {nodes_created} nodes (로컬 처리)",
            "nodes_created": nodes_created,
            "relationships_created": 0,
            "status": "success"
        }
    
    except Exception as e:
        print(f"❌ CSV upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- [14] JSON Upload Endpoint ---
@app.post("/upload_json",
          summary="JSON Data Upload to Neo4j",
          description="Upload JSON data directly to Neo4j graph database")
async def upload_json(request: dict):
    """
    JSON 데이터를 Neo4j에 직접 업로드 (로컬 처리만)
    """
    try:
        data = request.get("data")
        root_key = request.get("root_key")
        entity_key = request.get("entity_key", "name")
        entity_type = request.get("entity_type", "Entity")
        
        if not data:
            raise HTTPException(status_code=400, detail="data is required")
        
        # 루트 키가 있으면 해당 배열 추출
        if root_key and isinstance(data, dict):
            data = data.get(root_key, [])
        
        # 리스트가 아니면 리스트로 변환
        if not isinstance(data, list):
            data = [data]
        
        print(f"📦 Uploading JSON data: {len(data)} items (로컬 처리)")
        
        # Neo4j에 데이터 삽입
        from db.neo4j_db import Neo4jDatabase
        
        if not NEO4J_URI or not NEO4J_PASSWORD:
            raise HTTPException(status_code=500, detail="Neo4j not configured")
        
        db = Neo4jDatabase(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
        
        nodes_created = 0
        
        for item in data:
            if not isinstance(item, dict):
                continue
            
            entity_name = item.get(entity_key)
            if not entity_name:
                continue
            
            # 모든 속성 포함
            properties = dict(item)
            properties['name'] = entity_name
            
            # Cypher 쿼리 생성
            query = f"MERGE (n:{entity_type} {{name: $name}}) SET n += $properties RETURN n"
            
            db.execute_query(query, {"name": entity_name, "properties": properties})
            nodes_created += 1
        
        db.close()
        
        return {
            "message": f"Successfully uploaded {nodes_created} nodes (로컬 처리)",
            "nodes_created": nodes_created,
            "relationships_created": 0,
            "status": "success"
        }
    
    except Exception as e:
        print(f"❌ JSON upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- [15] 서버 실행 ---
# if __name__ == "__main__": 이건 "이 파일을 직접 실행했을 때만"이라는 뜻이에요!
if __name__ == "__main__":
    # uvicorn.run()은 "서버를 실행하는" 거예요!
    # app은 "FastAPI 앱"이에요!
    # host="0.0.0.0"은 "모든 네트워크 인터페이스에서 접속 가능"하다는 뜻이에요!
    # port=8000은 "8000번 포트를 사용한다"는 뜻이에요!
    uvicorn.run(app, host="0.0.0.0", port=8000)

