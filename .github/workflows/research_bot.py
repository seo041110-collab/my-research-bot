import os
import requests
import sys
from google import genai
from google.genai import types

def send_telegram(text):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # 텔레그램 글자수 제한(4096자)을 고려해 안전하게 자릅니다.
    payload = {"chat_id": chat_id, "text": text[:4000], "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def run():
    # 실행 시 인자값 확인 (daily 또는 hourly)
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    
    api_key = os.environ.get('GEMINI_API_KEY')
    client = genai.Client(api_key=api_key)
    
    if mode == "daily":
        # [아침 7시용 장문 보고서 프롬프트]
        user_query = "비트코인, 이더리움, SK하이닉스, TSMC에 대해 지난 24시간을 총망라하는 아주 상세한 심층 투자 보고서를 써줘. 뉴스 분석, 온체인 데이터, 향후 전망을 포함해서 길게 작성해."
        sys_instr = "너는 수석 금융 분석가야. 아주 전문적이고 상세한 마크다운 형식의 보고서를 작성해."
    else:
        # [매시간용 짧은 브리핑 프롬프트]
        user_query = "최근 1시간 동안의 BTC, ETH, 반도체 핵심 뉴스만 3줄 요약해서 짧게 브리핑해줘."
        sys_instr = "너는 속보 전문 비서야. 불필요한 말 빼고 핵심 뉴스만 짧게 전달해."

    response = client.models.generate_content(
        model="gemini-2.0-flash", # 가장 빠르고 안정적인 모델
        contents=user_query,
        config=types.GenerateContentConfig(
            tools=[types.Tool(googleSearch=types.GoogleSearch())],
            system_instruction=sys_instr
        )
    )
    
    send_telegram(response.text)

if __name__ == "__main__":
    run()
