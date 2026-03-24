import os
import json
import time
import pandas as pd
from datetime import datetime

# 파일이 상위로 이동했으므로 collector 폴더에서 import 하도록 수정
from collector.weather_api import get_weather_data
from collector.kamis_api import get_kamis_data
from collector.weather_forecast_api import get_3day_forecast

def main_collect():
    print("🚀 [빅데이터 구축] 5년 치 기상 및 가격 데이터 통합 파이프라인 시작...\n")

    # A. 경로 설정: 현재 파일(루트) 기준으로 secret.json 및 data 폴더 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    secret_path = os.path.join(current_dir, 'secret.json')
    data_dir = os.path.join(current_dir, 'data')

    # data 폴더가 없으면 생성
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # B. API 키 로드
    with open(secret_path, 'r', encoding='utf-8') as f:
        secrets = json.load(f)
        
    w_key = secrets["WEATHER_API_KEY"]
    k_key = secrets["KAMIS_API_KEY"]
    k_id = secrets["KAMIS_USER_ID"]

    # ==========================================
    # 🎯 기간 설정: 과거 5년 데이터 기준
    # ==========================================
    start_date = '2021-03-01'
    end_date = '2026-02-28'
    print(f"📅 훈련용 데이터 수집 기간: {start_date} ~ {end_date} (5년)\n")

    # ==========================================
    # 1. 과거 기상청 데이터 수집 (ASOS)
    # ==========================================
    print("⛅ [1/4] 과거 기상 데이터를 분할 수집합니다...")
    weather_chunks = [
        ('20210301', '20211231'), ('20220101', '20221231'),
        ('20230101', '20231231'), ('20240101', '20241231'),
        ('20250101', '20251231'), ('20260101', '20260228')
    ]
    
    weather_df_list = []
    for w_start, w_end in weather_chunks:
        print(f"   -> 수집 중: {w_start[:4]}년도 ({w_start} ~ {w_end})")
        chunk_df = get_weather_data(w_key, w_start, w_end, '108') # 108: 서울
        if chunk_df is not None:
            weather_df_list.append(chunk_df)
        time.sleep(0.5)
        
    if not weather_df_list:
        print("❌ 과거 기상 데이터 수집 실패.")
        return
        
    weather_df = pd.concat(weather_df_list, ignore_index=True)
    # 날짜 중복 제거 (혹시 모를 겹침 방지)
    weather_df = weather_df.drop_duplicates(subset=['날짜'])
    print(f"   ✅ 과거 기상 데이터 병합 완료!\n")

    # ==========================================
    # 2. KAMIS 과거 가격 데이터 수집
    # ==========================================
    print("🛒 [2/4] KAMIS 가격 데이터를 수집합니다. (상당 시간 소요...)")
    date_list = pd.date_range(start=start_date, end=end_date).strftime('%Y-%m-%d').tolist()
    kamis_df_list = []
    total_days = len(date_list)
    
    for i, dt in enumerate(date_list):
        time.sleep(0.05)
        daily_df = get_kamis_data(k_key, k_id, dt)
        if daily_df is not None:
            daily_df['날짜'] = dt 
            kamis_df_list.append(daily_df)
            
        if (i + 1) % 200 == 0 or (i + 1) == total_days:
            print(f"   ⏳ 진행률: {i + 1} / {total_days}일 ({(i+1)/total_days*100:.1f}%)")
            
    if not kamis_df_list:
        print("❌ 가격 데이터 수집 실패.")
        return
        
    price_df = pd.concat(kamis_df_list, ignore_index=True)
    # 토마토/상품 등급 필터링
    tomato_df = price_df[(price_df['품목'] == '토마토') & (price_df['등급'] == '상품')].copy()

    # ==========================================
    # 3. 데이터 병합 및 전처리
    # ==========================================
    print("\n🔗 [3/4] 날씨와 가격 데이터 병합 및 전처리 중...")
    
    # 날짜 포맷 통일
    weather_df['날짜'] = pd.to_datetime(weather_df['날짜']).dt.strftime('%Y-%m-%d')
    final_df = pd.merge(weather_df, tomato_df, on='날짜', how='left')

    # 숫자 데이터 전처리 (콤마 제거 및 수치형 변환)
    for col in ['당일가격(원)', '1년전가격(원)']:
        if col in final_df.columns:
            final_df[col] = final_df[col].astype(str).str.replace(',', '')
            final_df[col] = pd.to_numeric(final_df[col], errors='coerce')

    # 결측치 처리 (주말/휴일 가격 등)
    final_df = final_df.ffill().bfill()

    # 훈련용 데이터 저장
    hist_save_path = os.path.join(data_dir, 'tomato_5years_data.csv')
    final_df.to_csv(hist_save_path, index=False, encoding='utf-8-sig')
    print(f"✅ [훈련 데이터 저장] {hist_save_path}")

    # ==========================================
    # 4. 실시간 예보 수집 (예측용 Test Data)
    # ==========================================
    print("\n📡 [4/4] 실시간 3일 예보 수집 중...")
    # 🌟 기존 코드의 'my_key'를 'w_key'로 수정함
    df_forecast = get_3day_forecast(w_key) 
    
    if df_forecast is not None:
        forecast_save_path = os.path.join(data_dir, 'tomato_weather_forecast.csv')
        df_forecast.to_csv(forecast_save_path, index=False, encoding='utf-8-sig')
        print(f"✅ [예측 데이터 저장] {forecast_save_path}")
        print("-" * 30)
        print(df_forecast.head())
        print("-" * 30)
    else:
        print("⚠️ 실시간 예보 수집에 실패했습니다. (키 승인 여부 확인 요망)")

    print(f"\n✨ 모든 파이프라인이 정상적으로 종료되었습니다.")

if __name__ == "__main__":
    main_collect()