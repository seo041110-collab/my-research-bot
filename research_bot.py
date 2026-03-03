import os
import requests
import sys
import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from google import genai
from google.genai import types

def send_telegram(text):
    try:
        token = os.environ.get('TELEGRAM_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text[:4000], "parse_mode": "Markdown"}
        res = requests.post(url, json=payload)
        print(f"📡 텔레그램 전송 상태: {res.status_code}")
    except Exception as e:
        print(f"❌ 텔레그램 전송 실패: {e}")

def update_google_sheet(mode, content):
    try:
        json_key = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
        if not json_key:
            print("❌ 에러: GOOGLE_SERVICE_ACCOUNT_JSON 시크릿이 설정되지 않았습니다.")
            return

        service_account_info = json.loads(json_key)
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
        client = gspread.authorize(creds)

        sheet_id = os.environ.get('SPREADSHEET_ID')
        if not sheet_id:
            print("❌ 에러: SPREADSHEET_ID 시크릿이 설정되지 않았습니다.")
            return

        sheet = client.open_by_key(sheet_id).sheet1
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary = content[:300].replace('\n', ' ') if content else "내용 없음"
        
        sheet.append_row([now, mode, summary])
        print("✅ 구글 시트 기록 성공!")
    except Exception as e:
        print(f"❌ 구글 시트 기록 상세 에러: {e}")

def run():
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    api_key = os.environ.get('GEMINI_API_KEY')
    client = genai.Client(api_key=api_key)
    
    print(f"🚀 {mode} 모드로 전문 리서치 시작...")
    
    if mode == "daily":
        user_query = f"비트코인, 이더리움, SK하이닉스, TSMC 시황을 상세히 알려줘. (현재 시간: {datetime.now()})"
        sys_instr = "너는 투자 애널리스트야. 한국어로 전문적인 리포트를 마크다운으로 써줘."
    else:
        user_query = f"최근 1시간 핵심 사건 3줄 요약해줘. (현재 시간: {datetime.now()})"
        sys_instr = "너는 금융 속보 기자야. 팩트 위주로 짧게 보고해."

    # --- AI 리포트 생성 (여기가 들여쓰기 핵심!) ---
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash-002",
            contents=user_query,
            config=types.GenerateContentConfig(
                tools=[types.Tool(googleSearch=types.GoogleSearch())],
                system_instruction=sys_instr
            )
        )
        report = response.text if response.text else "AI 응답 내용이 비어있습니다."
    except Exception as e:
        report = f"AI 리서치 중 에러 발생: {e}"
        print(f"❌ AI 생성 실패: {e}")

    send_telegram(report)
    update_google_sheet(mode, report)

if __name__ == "__main__":
    run()
