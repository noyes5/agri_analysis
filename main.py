import os
import json
import pandas as pd
from datetime import datetime, timedelta

from weather_api import get_weather_data
from kamis_api import get_kamis_data

def main():
    print("🚀 기상 및 농산물 가격 데이터 통합 파이프라인 시작...\n")

    # 1. 보안 파일(secret.json)에서 API 키 불러오기
    current_dir = os.path.dirname(os.path.abspath(__file__))
    secret_path = os.path.join(current_dir, 'secret.json')
    
    with open(secret_path, 'r', encoding='utf-8') as f:
        secrets = json.load(f)
        
    w_key = secrets["WEATHER_API_KEY"]
    k_key = secrets["KAMIS_API_KEY"]
    k_id = secrets["KAMIS_USER_ID"]

    # ==========================================
    # 기상청 데이터 수집 (예: 2023년 7월 3일 ~ 7월 7일, 서울) --> 고정 데이터. 실제 분석할 땐 자동화로 매주/매월단위 가져와서 분석할 예정
    # ==========================================
    print("⛅ [1/3] 기상청 날씨 데이터를 수집합니다...")
    # 참고: API 요청용 날짜 포맷은 YYYYMMDD
    weather_df = get_weather_data(w_key, '20230703', '20230707', '108')
    
    if weather_df is None:
        print("❌ 기상 데이터 수집 실패로 프로세스를 종료합니다.")
        return

    # ==========================================
    # KAMIS 가격 데이터 수집
    # ==========================================
    print("🛒 [2/3] KAMIS 과일 가격 데이터를 수집합니다...")
    # KAMIS는 하루치씩만 조회되므로, 여러 날짜를 리스트로 만들어 반복 수집
    date_list = ['2023-07-03', '2023-07-04', '2023-07-05', '2023-07-06', '2023-07-07']
    kamis_df_list = []
    
    for dt in date_list:
        daily_df = get_kamis_data(k_key, k_id, dt)
        if daily_df is not None:
            # 병합(Merge)을 위해 가격 표에도 '날짜' 컬럼을 억지로 하나 추가해줌
            daily_df['날짜'] = dt 
            kamis_df_list.append(daily_df)
            
    if not kamis_df_list: # 승인이 안 났거나 데이터가 아예 없으면
        print("❌ 가격 데이터가 없어서 병합할 수 없습니다. (API 승인을 기다려주세요!)")
        return
        
    # 수집된 매일의 가격 표들을 위아래로 길게 하나로 합침
    price_df = pd.concat(kamis_df_list, ignore_index=True)
    
    # 너무 많으니까 '사과' 품목만 쏙 골라내기 (필터링)
    apple_df = price_df[price_df['품목'] == '사과'].copy()

    # ==========================================
    # 날씨 표와 가격 표 병합 (Merge)
    # ==========================================
    print("🔗 [3/3] 날씨 데이터와 사과 가격 데이터를 날짜 기준으로 병합합니다...")
    
    # how='left': 날씨 표(왼쪽)를 기준으로 합침. 
    # 즉, 날씨는 다 나오는데, 주말이라 가격이 없으면 빈칸(NaN)으로 둠
    final_df = pd.merge(weather_df, apple_df, on='날짜', how='left')

    print("\n✅ 통합 데이터 생성 완료! 최종 결과물:\n")
    print(final_df.to_string()) # 표가 안 잘리게 전체 출력
    
    # 나중에 분석하기 편하게 엑셀이나 CSV로 저장하는 코드 (옵션)
    # final_df.to_csv('merged_apple_data.csv', index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    main()