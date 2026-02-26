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
    user_query = """
1. 비트코인(BTC): 현재 온체인 지표, 미국 ETF 유입량 현황, 그리고 주요 지지선/저항선을 분석해줘.
2. 이더리움(ETH): 비트코인과의 상관관계(ETH/BTC 차트)를 분석하고, 스테이킹 유입량 변화를 체크해줘.
3. 반도체(SK하이닉스, TSMC): 엔비디아와 관련된 최신 공급망 이슈를 분석해줘.
위 내용을 종합해서 '긴급성' 위주로 보고서를 작성해줘.
"""

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
