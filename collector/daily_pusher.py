import requests
import pandas as pd
from datetime import datetime, timedelta
from weather_api import get_weather_data, get_weather_forecast, MY_WEATHER_KEY
from kamis_api import get_kamis_data, MY_KAMIS_KEY, MY_KAMIS_ID

# [수정] 조회용과 전송용 URL 구분
BASE_URL = "http://127.0.0.1:8000/api/v1"
INGEST_URL = f"{BASE_URL}/ingest"

def get_last_date():
    """DB에서 가장 최근 저장된 가격 데이터의 날짜를 가져옵니다."""
    try:
        res = requests.get(f"{BASE_URL}/price") # 전체 가격 조회 API
        if res.status_code == 200 and res.json():
            df = pd.DataFrame(res.json())
            return pd.to_datetime(df['date']).max().date()
    except:
        pass
    return (datetime.now() - timedelta(days=30)).date() # 데이터 없으면 30일 전부터

def push_to_fastapi(endpoint, df):
    if df is None or df.empty:
        return
    payload = df.to_dict(orient='records')
    res = requests.post(f"{INGEST_URL}/{endpoint}", json=payload)
    if res.status_code == 200:
        print(f"✅ {endpoint} 전송 성공! ({len(df)}행)")
    else:
        print(f"❌ {endpoint} 전송 실패: {res.text}")

def run_daily_update():
    # 1. 동기화 시작 날짜 결정 (마지막 날짜 + 1일)
    last_date = get_last_date()
    start_date = last_date + timedelta(days=1)
    today = datetime.now().date()
    
    print(f"🚀 {start_date}부터 {today}까지 동기화 시작...")

    # 2. 누락된 날짜만큼 반복 실행 (과거 데이터 채우기)
    current_date = start_date
    while current_date <= today:
        d_str = current_date.strftime('%Y%m%d')        # API용 (YYYYMMDD)
        d_hyphen = current_date.strftime('%Y-%m-%d')  # KAMIS/DB용 (YYYY-MM-DD)

        # 어제/과거 확정 날씨 및 가격 수집
        df_weather = get_weather_data(MY_WEATHER_KEY, d_str, d_str)
        push_to_fastapi("weather-history", df_weather)

        df_price = get_kamis_data(MY_KAMIS_KEY, MY_KAMIS_ID, d_hyphen)
        push_to_fastapi("price", df_price)
        
        current_date += timedelta(days=1)

    # 3. 예보 수집 (예보는 항상 현재 시점 기준 최신본 하나만 유지)
    df_forecast = get_weather_forecast(MY_WEATHER_KEY)
    push_to_fastapi("weather-forecast", df_forecast)

if __name__ == "__main__":
    run_daily_update()