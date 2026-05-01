import os
from pathlib import Path
#from google import genai
from dotenv import load_dotenv

# 1. 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"

# 2. 환경 변수 로드
load_dotenv(env_path)
api_key = os.getenv("GEMINI_API_KEY")

# 키가 로드되지 않았을 경우 AI_API 폴더 내부도 확인 (예비 경로)
if not api_key:
    alt_path = BASE_DIR / "AI_API" / "api.env"
    load_dotenv(alt_path)
    api_key = os.getenv("GEMINI_API_KEY")

# 3. AI 클라이언트 생성 (test1.py에서 검증된 방식 사용)
client = None
    
MODEL_ID = "gemini-2.5-flash"

# --- [기능 1] 노래 및 가수 추천 함수 ---
def recommend_songs(artist_or_song):
    """사용자가 입력한 가수/곡과 유사한 노래 추천"""
    if not client: return "API 키가 설정되지 않았습니다."
    
    prompt = f"""
    당신은 냉철한 음악 데이터 분석가이자 보컬 큐레이터입니다. 
    사용자가 입력한 '{artist_or_song}'의 음악적 특징(장르, BPM, 보컬 음색, 곡의 구성)을 객관적으로 분석하여 유사한 곡 3곡을 추천하십시오.

    피드백 구조:
    1. 추천 요약 (한 줄: 추천의 핵심 근거)
    2. 곡별 상세 분석 (곡명 - 아티스트)
    - 유사성 근거: '{artist_or_song}'과 비교했을 때 어떤 기술적/음악적 요소가 일치하는지 설명
    - 가창 포인트: 해당 곡에서 주의 깊게 들어야 하거나 따라 불러야 할 핵심 구간
    3. 가창 난이도 평가 (음역대 및 호흡 난이도 포함)
    4. 연습 가이드 (해당 곡들을 부를 때 필요한 발성적 팁)
    추상적인 표현은 금지하며, 음악적 용어를 사용하여 명확하게 기술하십시오.
    만약 입력된 가수명이 '자동 분석'이라면:
    1. 위 점수와 가장 음악적으로 잘 어울리는 한국 가수 3명을 당신이 직접 선정하십시오.
    2. 선정한 이유를 발성적 특징과 연결하여 설명하십시오.
    만약 특정 가수가 입력되었다면:
    1. 그 가수와 유사한 스타일의 곡을 추천하십시오.
    구조는 이전과 동일하게 유지하되, 반드시 한국 가요를 중심으로 추천하십시오.
    """
    try:
        response = client.models.generate_content(model=MODEL_ID, contents=prompt)
        return response.text
    except Exception as e:
        return f"추천 중 오류 발생: {e}"

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

# --- [기능 3] 가창 실시간 피드백 함수 ---
def get_vocal_feedback(pitch_score, tempo_score, avg_volume):
    """음정, 박자, 성량 데이터를 바탕으로 보컬 피드백 생성"""
    if not client: return "AI 클라이언트가 설정되지 않았습니다."
    
    prompt = f"""
    너는 냉정하고 정확한 보컬 트레이너다. 감정에 치우치지 말고, 발성·호흡·음정·리듬·발음·표현력 등을 객관적으로 분석해라. 문제점은 구체적으로 짚고, 어떻게 개선해야 하는지 실전적인 방법을 제시해라.
    다만, 잘한 부분에 대해서는 반드시 이유를 포함해 칭찬하라. “좋다”가 아니라 왜 좋은지 설명해야 한다.
    피드백은 다음 구조를 따라라:
    1. 전체 평가 (한 줄 요약)
    2. 잘한 점 (구체적 근거 포함)
    3. 개선할 점 (가장 중요한 것부터 우선순위)
    4. 연습 방법 (바로 실행 가능한 형태)
    애매한 표현, 추상적인 조언은 금지한다. 항상 명확하고 실행 가능하게 말해라.
    다음 가창 데이터를 분석해 주세요:
    - 음정 정확도: {pitch_score}점
    - 박자 정확도: {tempo_score}점
    - 평균 성량(Volume): {avg_volume}/100
    이 데이터를 피드백을 보컬 선생님처럼 말해줘.
    """
    try:
        response = client.models.generate_content(model=MODEL_ID, contents=prompt)
        return response.text
    except Exception as e:
        return f"피드백 생성 중 오류 발생: {e}"

# --- [기능 4] 벡터 유사도 기반 맞춤 가수 추천 함수 ---
def get_similarity_based_feedback(singer_name, similarity_score):
    """ChromaDB/유사도 엔진에서 뽑은 1등 가수와 유사도(%)를 바탕으로 맞춤 피드백 생성"""
    if not client: return "AI 클라이언트가 설정되지 않았습니다."
    
    prompt = f"""
    당신은 'SING-PICK' 시스템의 수석 보컬 트레이너이자 음색 분석가입니다.
    자체 AI 벡터 유사도 분석 결과, 사용자의 목소리는 한국 가수 '{singer_name}'와(과) {similarity_score}% 일치한다는 객관적인 데이터가 나왔습니다.

    이 데이터를 바탕으로 아래 3가지 항목을 포함하여 사용자에게 전문적이고 구체적인 피드백을 작성해 주세요.

    1. **음색 매칭 결과**: 사용자의 음색이 '{singer_name}'와(과) {similarity_score}% 유사하다는 사실을 안내하고, '{singer_name}'의 보컬적 특징(음색, 발성, 주특기)을 바탕으로 사용자의 목소리가 가진 매력과 잠재력을 설명해 주세요.
    2. **맞춤 곡 추천**: '{singer_name}'의 노래 중 발성 연습이나 음색을 살리기 가장 좋은 딱 1곡만 추천해 주세요.
    3. **가창 포인트**: 추천한 곡을 부를 때 주의해야 할 기술적 포인트(호흡, 성구 전환, 감정선 등)를 알려주세요.

    [주의사항]
    - 절대 '{singer_name}' 외의 다른 가수는 언급하거나 추천하지 마세요.
    - 감정적인 칭찬보다는 음악적이고 객관적인 용어(성구 전환, 다이내믹스, 믹스 보이스 등)를 사용하여 전문가처럼 작성하세요.
    - 마크다운 형식(글머리 기호, 굵은 글씨 등)을 사용하여 가독성 좋게 작성하세요.
    """
    try:
        response = client.models.generate_content(model=MODEL_ID, contents=prompt)
        return response.text
    except Exception as e:
        return f"유사도 기반 추천 중 오류 발생: {e}"


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
        print(get_vocal_feedback(88, 92, 40))
    
    print("\n" + "="*50)