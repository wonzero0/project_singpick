import os
from pathlib import Path
from google import genai
from dotenv import load_dotenv

# 1. 경로 설정 및 환경 변수 로드
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(env_path)
api_key = os.getenv("GEMINI_API_KEY")

# 키가 로드되지 않았을 경우 예비 경로 확인
if not api_key:
    alt_path = BASE_DIR / "AI_API" / "api.env"
    load_dotenv(alt_path)
    api_key = os.getenv("GEMINI_API_KEY")

# 2. AI 클라이언트 초기화 로직
client = None
if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None

MODEL_ID = "gemini-2.5-flash"

def get_vocal_feedback(pitch_score, tempo_score, avg_volume, pitch_hz_avg, tempo_bpm, volume_rms_avg):
    """분석된 데이터 점수들을 바탕으로 보컬 실력 향상을 위한 피드백만 제공"""
    if not client: return "AI 클라이언트가 설정되지 않았습니다."
    
    prompt = f"""
    당신은 엄격하고 전문적인 보컬 트레이너입니다. 감정적인 격려보다는 데이터에 기반한 객관적인 분석을 통해 10문장 이내의 실질적인 조언을 주세요.
    
    [분석 데이터]
    - 음정 정확도: {pitch_score}점 (평균 주파수: {pitch_hz_avg}Hz)
    - 박자 정확도: {tempo_score}점 (평균 템포: {tempo_bpm}BPM)
    - 성량(Volume): {avg_volume}/100 (RMS 평균: {volume_rms_avg})
    
    [요청 사항]
    위 데이터를 분석하여, 사용자가 어떻게 가창력을 향상시킬 수 있을지 '훈련 방법' 위주로 서술하세요. 추천곡이나 다른 가수에 대한 언급은 절대 금지합니다. 오직 사용자의 가창 데이터와 개선점에만 집중하세요.
    
    [피드백 구조]
    1. 전체 가창 평가 (한 줄 요약: 데이터 기반의 현재 가창 상태 진단)
    2. 데이터별 상세 분석 (각 수치가 무엇을 의미하는지 해석)
       - 음정, 박자, 성량 각각이 가진 문제점이나 강점을 데이터 기반으로 설명
    3. 단계별 훈련 로드맵
       - 성량 개선 훈련법 (호흡 지지 등 구체적 방법)
       - 음정 정확도 향상 훈련법 (튜너 활용 및 단음정 연습 등)
       - 박자 감각 고도화 훈련법 (메트로놈 활용 등)
    4. 다음 가창을 위한 핵심 과제 (가장 먼저 고쳐야 할 것 1가지)
    
    추상적인 표현은 배제하고, 음악적 용어(복식 호흡, 성대 접촉, 호흡 압력, 리듬 밀당 등)를 사용하여 전문가처럼 작성하세요.
    """
    try:
        response = client.models.generate_content(model=MODEL_ID, contents=prompt)
        return response.text
    except Exception as e:
        return f"피드백 생성 중 오류 발생: {e}"

# --- [기능 2] 시스템 에러 분석 함수 ---
def analyze_error(error_log):
    """에러 로그를 분석하여 개발자에게 해결책 제시"""
    if not client: return "AI 클라이언트가 설정되지 않았습니다."
    
    prompt = f"""
    당신은 10년 차 이상의 냉정한 시니어 백엔드 엔지니어입니다. 
    다음 에러 로그를 시스템 공학적으로 분석하여 보고하십시오:
    ---
    {error_log}
    ---

    피드백 구조:
    1. 에러 요약 (한 줄: 에러의 핵심 원인 코드)
    2. 근본 원인 분석 (Root Cause Analysis)
    - 왜 이 에러가 발생했는지 시스템 아키텍처 및 코드 레벨에서 구체적으로 설명
    3. 조치 사항 (Priority 기반)
    - [우선순위 1]:즉시 수정해야 할 코드나 DB 설정
    - [우선순위 2]: 재발 방지를 위한 로그 강화 또는 구조 변경
    4. 검증 방법 (해당 조치가 성공했는지 확인할 수 있는 테스트 쿼리 또는 명령어)

    애매한 "확인해 보세요" 식의 조언은 배제하고, 구체적인 명령어나 코드 수정 예시를 제시하십시오.
    """
    try:
        response = client.models.generate_content(model=MODEL_ID, contents=prompt)
        return response.text
    except Exception as e:
        return f"에러 분석 중 오류 발생: {e}"


# --- 🚀 터미널 테스트 실행부 ---
if __name__ == "__main__":
    print("\n" + "="*50)
    print("🤖 SING-PICK 노래방 AI 엔진 통합 테스트")
    print("="*50)

    if not api_key:
        print(f"❌ 키 로드 실패: {env_path} 위치에 파일이 있는지 확인하세요.")
    else:
        print(f"✅ 키 로드 성공 (앞자리: {api_key[:5]}...)")
        
        # 테스트 1: 노래 추천
        print("\n[TEST 1: 노래 추천 결과]")
        print(recommend_songs("아이유"))
        
        # 테스트 2: 에러 분석
        print("\n[TEST 2: 에러 분석 결과]")
        sample_log = "mysql.connector.errors.ProgrammingError: 1146 (42S02): Table 'singpick.scores' doesn't exist"
        print(analyze_error(sample_log))

        # 테스트 3: 실시간 가창 피드백 (Volume 기반)
        print("\n[TEST 3: 가창 피드백 결과]")
        # (음정 88, 박자 92, 성량 40점 가상 데이터)
        print(get_vocal_feedback(88, 92, 40, 261.68, 137.2, 0.0714))
    
    print("\n" + "="*50)