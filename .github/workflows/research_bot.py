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
    try:
        token = os.environ.get('TELEGRAM_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        # 텔레그램 마크다운 파싱 에러 방지를 위해 단순 텍스트로 보낼 수도 있으나, 
        # 일단 리치 텍스트를 위해 MarkdownV2 대신 기본 Markdown 유지
        payload = {"chat_id": chat_id, "text": text[:4000], "parse_mode": "Markdown"}
        res = requests.post(url, json=payload)
        print(f"📡 텔레그램 전송 상태: {res.status_code}")
    except Exception as e:
        print(f"❌ 텔레그램 전송 실패: {e}")

# 2. 구글 시트 기록 함수
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
        # 시트에는 너무 길지 않게 앞부분만 요약해서 저장
        summary = content[:300].replace('\n', ' ') if content else "내용 없음"
        
        sheet.append_row([now, mode, summary])
        print("✅ 구글 시트 기록 성공!")
    except Exception as e:
        print(f"❌ 구글 시트 기록 상세 에러: {e}")

# 3. 메인 리서치 실행 함수
def run():
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    api_key = os.environ.get('GEMINI_API_KEY')
    client = genai.Client(api_key=api_key)
    
    print(f"🚀 {mode} 모드로 전문 리서치 시작...")
    
    # --- 모드별 상세 프롬프트 설정 ---
    if mode == "daily":
        user_query = f"""
        다음 4가지 섹션을 포함하여 아주 상세한 '데일리 투자 전략 리포트'를 작성해줘:
        
        1. 시장 요약 (Market Overview): 
           - 비트코인(BTC)과 이더리움(ETH)의 지난 24시간 가격 변동 및 주요 뉴스.
           - 미 연준(Fed) 금리 전망이나 환율 등 거시 경제가 시장에 미친 영향.
        2. 반도체 섹터 심층 분석: 
           - SK하이닉스와 TSMC의 최신 뉴스 및 공급망 이슈.
           - HBM 관련 경쟁사 동향 분석.
        3. 온체인 및 기술적 지표: 
           - 주요 거래소 유입/유출량 및 기술적 지지선/저항선 분석.
        4. 투자자 행동 지침 (Action Plan): 
           - 현재 상황에서 '적립식 매수'가 유리한지 제언 및 리스크 요인 3가지.
        
        (현재 시간: {datetime.now()})
        """
        sys_instr = "너는 골드만삭스 출신의 시니어 애널리스트야. 전문적이고 가독성이 좋은 마크다운 형식으로 한국어로 작성해."
    else:
        user_query = f"""
        최근 1시간 내 발생한 핵심 사건을 '긴급성' 위주로 3줄 요약해줘:
        1. BTC/ETH: 급격한 시세 변동이나 대규모 이체 내역.
        2. 반도체: SK하이닉스, TSMC 관련 주요 뉴스.
        3. 실시간 지표: 현재가 및 시장 공포/탐욕 지수.
        뉴스 검색 결과가 없으면 현재 시세라도 알려줘야 해.
        
        (현재 시간: {datetime.now()})
        """
        sys_instr = "너는 실시간 금융 속보 기자야. 불필요한 서술은 빼고 팩트와 수치 위주로 짧게 보고해."

    # --- AI 리포트 생성 ---
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
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

    # --- 결과 출력 (텔레그램 & 시트) ---
    send_telegram(report)
    update_google_sheet(mode, report)

if __name__ == "__main__":
    run()
