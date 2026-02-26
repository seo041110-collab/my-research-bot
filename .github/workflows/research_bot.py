import os
import requests
import sys
import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from google import genai
from google.genai import types

# 1. 텔레그램 전송 함수
def send_telegram(text):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text[:4000], "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# 2. 구글 시트 기록 함수
def update_google_sheet(mode, content):
    try:
        # Secrets에서 JSON 키 불러오기
        service_account_info = json.loads(os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON'))
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
        client = gspread.authorize(creds)

        # 시트 열기
        sheet_id = os.environ.get('SPREADSHEET_ID')
        sheet = client.open_by_key(sheet_id).sheet1

        # 기록할 데이터 구성 (날짜, 구분, 내용 요약)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary = content[:200] + "..." # 너무 길면 시트가 복잡하니 요약본만 저장
        
        sheet.append_row([now, mode, summary])
        print("✅ 구글 시트 기록 성공!")
    except Exception as e:
        print(f"❌ 구글 시트 기록 실패: {e}")

# 3. 메인 리서치 실행 함수
def run():
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    api_key = os.environ.get('GEMINI_API_KEY')
    client = genai.Client(api_key=api_key)
    
    if mode == "daily":
        user_query = "비트코인, 이더리움, SK하이닉스, TSMC 심층 투자 보고서를 써줘. 뉴스 분석과 향후 전망을 포함해."
        sys_instr = "너는 수석 금융 분석가야. 상세한 마크다운 보고서를 작성해."
    else:
        user_query = "최근 1시간 동안의 핵심 뉴스와 실시간 시세를 짧게 브리핑해줘. 없으면 시세라도 알려줘."
        sys_instr = "너는 속보 전문 비서야. 핵심만 전달해."

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=user_query,
        config=types.GenerateContentConfig(
            tools=[types.Tool(googleSearch=types.GoogleSearch())],
            system_instruction=sys_instr
        )
    )
    
    report = response.text
    
    # 텔레그램 발송
    send_telegram(report)
    
    # 구글 시트 기록
    update_google_sheet(mode, report)

if __name__ == "__main__":
    run()
