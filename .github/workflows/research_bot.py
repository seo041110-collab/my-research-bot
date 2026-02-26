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
    # 깃허브 Secrets에서 가져온 API 키 사용
    api_key = os.environ.get('GEMINI_API_KEY')
    client = genai.Client(api_key=api_key)
    
    model = "gemini-2.5-flash"
    user_query = "SK하이닉스와 TSMC의 반도체 업황 최신 뉴스, 그리고 비트코인 및 이더리움의 거시 경제적 시황을 분석해서 보고서를 써줘."

    generate_content_config = types.GenerateContentConfig(
        tools=[types.Tool(googleSearch=types.GoogleSearch())],
        system_instruction=[
            types.Part.from_text(text="너는 전문 금융 리서치 에이전트야. 실시간 검색 후 전문적인 보고서를 작성해서 텔레그램으로 보내줘.")
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
