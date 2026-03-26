import os
from dotenv import load_dotenv
from google import genai


load_dotenv("api.env")

MY_API_KEY = os.getenv("GEMINI_API_KEY")

if not MY_API_KEY:
    print("오류: .env 파일에서 GEMINI_API_KEY를 찾을 수 없습니다.")
    exit()


client = genai.Client(api_key=MY_API_KEY.strip())
chat = client.chats.create(model="gemini-2.5-flash")

print("노래방 AI 도우미와 대화를 시작합니다. (종료하려면 '종료' 입력)")

while True:
    user_input = input("🐣나: ")
    
    if user_input == '종료':
        print("대화를 종료합니다.")
        break
        
    try:
        response = chat.send_message(user_input)
        print(f"AI 도우미: {response.text}")
    except Exception as e:
        print(f"에러가 발생했습니다: {e}")