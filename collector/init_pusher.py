import time
import pandas as pd
import requests
from datetime import datetime, timedelta

# 1. 기존 모듈에서 함수와 키 가져오기
from weather_api import get_weather_data, MY_WEATHER_KEY
from kamis_api import get_kamis_data, MY_KAMIS_KEY, MY_KAMIS_ID

# FastAPI 서버 주소
BASE_URL = "http://127.0.0.1:8000/api/v1/ingest"

def push_to_fastapi(endpoint, data_df):
    """FastAPI 엔드포인트로 데이터를 전송하는 공통 함수"""
    if data_df is None or data_df.empty:
        return
    
    # 전송을 위해 JSON 리스트로 변환
    payload = data_df.to_dict(orient='records')
    
    try:
        response = requests.post(f"{BASE_URL}/{endpoint}", json=payload)
        if response.status_code == 200:
            print(f"    ✅ {endpoint} 전송 성공! ({len(data_df)}행)")
        else:
            print(f"    ❌ 전송 실패({response.status_code}): {response.text}")
    except Exception as e:
        print(f"    ⚠️ 연결 오류: {e}")

def run_init_collection():
    print("🚀 [초기 데이터 구축] 2021-03-01 ~ 2026-03-30 데이터 수집 시작...\n")

    # [A] 과거 기상 데이터 수집 (연 단위 루프)
    print("⛅ [1/2] 기상청 과거 데이터 수집 및 전송 중...")
    years = [2021, 2022, 2023, 2024, 2025, 2026]
    for year in years:
        start_dt = f"{year}0301" if year == 2021 else f"{year}0101"
        end_dt = "20260330" if year == 2026 else f"{year}1231"
        
        print(f"  -> {year}년 구간({start_dt}~{end_dt}) 처리 중...")
        df_w = get_weather_data(api_key=MY_WEATHER_KEY, start_date=start_dt, end_date=end_dt)
        push_to_fastapi("weather-history", df_w)
        time.sleep(1) # API 부하 방지

    # [B] 과거 가격 데이터 수집 (일 단위 루프)
    # KAMIS 카테고리 200(채소류) 내의 모든 품목을 가져옵니다.
    print("\n🛒 [2/2] KAMIS 과거 가격 데이터 수집 및 전송 중...")
    start_date = datetime.strptime("2021-03-01", "%Y-%m-%d")
    now_str = datetime.now().strftime("%Y-%m-%d")
    end_date = datetime.strptime(now_str, "%Y-%m-%d")
    
    current_date = start_date
    while current_date <= end_date:
        target_str = current_date.strftime("%Y-%m-%d")
        
        # KAMIS는 하루치씩 호출해야 함
        df_p = get_kamis_data(api_key=MY_KAMIS_KEY, user_id=MY_KAMIS_ID, target_date=target_str)
        
        if df_p is not None:
            print(f"  -> {target_str} 가격 데이터 수집 완료")
            push_to_fastapi("price", df_p)
        
        # 날짜 1일 증가
        current_date += timedelta(days=1)
        time.sleep(0.3) # KAMIS 서버 차단 방지 (매우 중요)

    print("\n✨ 모든 초기 데이터 구축이 완료되었습니다.")

if __name__ == "__main__":
    run_init_collection()