import os
import requests
from google import genai
from google.genai import types

def send_telegram_message(text):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def generate_research():
    # 깃허브 Secrets에 저장한 API 키를 가져옵니다
    api_key = os.environ.get('GEMINI_API_KEY')
    client = genai.Client(api_key=api_key)
    
    model = "gemini-2.5-flash"
    user_query = "SK하이닉스와 TSMC의 최신 반도체 뉴스, 그리고 이더리움 시황을 분석해서 보고서를 써줘."

    generate_content_config = types.GenerateContentConfig(
        tools=[types.Tool(googleSearch=types.GoogleSearch())],
        system_instruction=[
            types.Part.from_text(text="너는 전문 금융 리서치 에이전트야. 실시간 검색 후 전문적인 보고서를 작성해줘.")
        ],
    )

    response = client.models.generate_content(
        model=model,
        contents=user_query,
        config=generate_content_config,
    )
    
    send_telegram_message(response.text)

if __name__ == "__main__":
    generate_research()
