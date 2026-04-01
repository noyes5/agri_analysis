import requests
import pandas as pd
from datetime import datetime, timedelta
from weather_api import get_weather_data, get_weather_forecast, MY_WEATHER_KEY
from kamis_api import get_kamis_data, MY_KAMIS_KEY, MY_KAMIS_ID

BASE_URL = "http://127.0.0.1:8000/api/v1/ingest"

def push_to_fastapi(endpoint, df):
    if df is None or df.empty:
        return
    payload = df.to_dict(orient='records')
    res = requests.post(f"{BASE_URL}/{endpoint}", json=payload)
    if res.status_code == 200:
        print(f"✅ {endpoint} 전송 성공! ({len(df)}행)")
    else:
        print(f"❌ {endpoint} 전송 실패: {res.text}")

def run_daily_update():
    # 1. 날짜 설정 (어제 데이터 수집)
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    yesterday_hyphen = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"🚀 {yesterday_hyphen} 데일리 업데이트 시작...")

    # 2. 어제 확정 날씨 수집 (AsosDaly)
    df_weather = get_weather_data(MY_WEATHER_KEY, yesterday, yesterday)
    push_to_fastapi("weather-history", df_weather)

    # 3. 어제 확정 가격 수집 (KAMIS)
    df_price = get_kamis_data(MY_KAMIS_KEY, MY_KAMIS_ID, yesterday_hyphen)
    push_to_fastapi("price", df_price)

    # 4. 향후 3일 날씨 예보 수집 (기상청 단기예보 - 별도 함수 필요)
    df_forecast = get_weather_forecast(MY_WEATHER_KEY)
    push_to_fastapi("weather-forecast", df_forecast)

if __name__ == "__main__":
    run_daily_update()