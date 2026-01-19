"""
Connection Check - Verify Local Security Model is Running
로컬 보안 모델 연결 확인 모듈
"""

import requests
import sys
from typing import Tuple, Dict, List


class ConnectionChecker:
    """
    로컬 보안 모델 연결 체크
    
    Security Policy:
    - Ollama 로컬 모델이 실행 중이지 않으면 시스템 종료
    - 민감 데이터 처리 전 반드시 로컬 모델 확인
    - 클라우드 API로 폴백 절대 불가
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.required_model = "qwen2.5-coder"
    
    def check_ollama_connection(self) -> Tuple[bool, str, List[str]]:
        """
        Ollama 서버 연결 및 모델 확인
        
        Returns:
            (연결 성공 여부, 메시지, 사용 가능한 모델 목록)
        """
        try:
            response = requests.get(
                f"{self.ollama_url}/api/tags",
                timeout=3
            )
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                model_names = [m.get("name", "") for m in models]
                
                return True, "Ollama is running", model_names
            else:
                return False, f"Ollama returned status {response.status_code}", []
                
        except requests.exceptions.ConnectionError:
            return False, f"Cannot connect to Ollama at {self.ollama_url}", []
        except requests.exceptions.Timeout:
            return False, "Ollama connection timeout", []
        except Exception as e:
            return False, f"Ollama check failed: {str(e)}", []
    
    def verify_required_model(self) -> Tuple[bool, str]:
        """
        필수 모델(qwen2.5-coder) 존재 확인
        
        Returns:
            (모델 존재 여부, 메시지)
        """
        is_connected, message, models = self.check_ollama_connection()
        
        if not is_connected:
            return False, message
        
        # Check if required model exists
        model_found = any(self.required_model in model for model in models)
        
        if model_found:
            return True, f"Required model '{self.required_model}' is available"
        else:
            return False, f"Required model '{self.required_model}' not found. Available models: {', '.join(models)}"
    
    def enforce_local_model_or_exit(self):
        """
        로컬 모델 강제 확인 - 없으면 시스템 종료
        
        Security Critical:
        - 이 함수는 민감 데이터 처리 전에 반드시 호출되어야 함
        - 로컬 모델이 없으면 프로세스 종료
        """
        print("\n" + "=" * 70)
        print("🔒 SECURITY CHECK: Verifying Local Security Model")
        print("=" * 70)
        
        is_available, message = self.verify_required_model()
        
        if is_available:
            print(f"✅ {message}")
            print("✅ Local security model is ready for sensitive data processing")
            print("=" * 70 + "\n")
            return True
        else:
            print(f"❌ {message}")
            print("\n" + "!" * 70)
            print("🚨 SECURITY VIOLATION DETECTED")
            print("!" * 70)
            print("\n로컬 보안 모델이 구동되지 않았습니다.")
            print("보안을 위해 작업을 중단합니다.")
            print("\n필수 조치:")
            print("1. Ollama 서버를 시작하세요: ollama serve")
            print(f"2. 필수 모델을 다운로드하세요: ollama pull {self.required_model}")
            print("3. 모델이 정상 작동하는지 확인하세요: ollama list")
            print("\n" + "!" * 70)
            print("SYSTEM SHUTDOWN FOR SECURITY")
            print("!" * 70 + "\n")
            
            # Force exit
            sys.exit(1)


def check_local_model_before_processing():
    """
    민감 데이터 처리 전 로컬 모델 확인
    
    Usage:
        from engine.connection_check import check_local_model_before_processing
        check_local_model_before_processing()  # Will exit if local model not available
    """
    checker = ConnectionChecker()
    checker.enforce_local_model_or_exit()


def get_local_model_status() -> Dict[str, any]:
    """
    로컬 모델 상태 조회 (정보 확인용)
    
    Returns:
        상태 정보 딕셔너리
    """
    checker = ConnectionChecker()
    is_connected, message, models = checker.check_ollama_connection()
    is_model_ready, model_message = checker.verify_required_model()
    
    return {
        "ollama_running": is_connected,
        "connection_message": message,
        "available_models": models,
        "required_model_ready": is_model_ready,
        "model_message": model_message
    }


if __name__ == "__main__":
    """Test connection checker"""
    print("Testing Local Security Model Connection...")
    
    checker = ConnectionChecker()
    
    # Test 1: Check connection
    print("\n1. Checking Ollama connection...")
    is_connected, message, models = checker.check_ollama_connection()
    print(f"   Connected: {is_connected}")
    print(f"   Message: {message}")
    print(f"   Models: {models}")
    
    # Test 2: Verify required model
    print("\n2. Verifying required model...")
    is_ready, model_msg = checker.verify_required_model()
    print(f"   Ready: {is_ready}")
    print(f"   Message: {model_msg}")
    
    # Test 3: Enforce (will exit if not available)
    print("\n3. Enforcing local model requirement...")
    checker.enforce_local_model_or_exit()
    
    print("\n✅ All checks passed!")
