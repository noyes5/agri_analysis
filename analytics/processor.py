import pandas as pd
import requests
import os

# 설정
BASE_URL = "http://127.0.0.1:8000/api/v1"

def fetch_data(endpoint):
    """FastAPI 서버에서 데이터를 가져와 DataFrame으로 변환"""
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}")
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except Exception as e:
        print(f"❌ {endpoint} 호출 중 오류 발생: {e}")
        return pd.DataFrame()

def process_and_save_data(target_item="토마토", target_location="서울"):
    print(f"🔄 [{target_item} / {target_location}] 데이터 통합 및 정제 시작...")

    # 1. 데이터 가져오기
    weather_df = fetch_data("weather-history")
    price_df = fetch_data("price")

    if weather_df.empty or price_df.empty:
        print("⚠️ 통합할 데이터가 부족합니다.")
        return

    # 2. 날짜 형식 통일 (tm -> date, p_date -> date)
    # 기상청 날짜(tm)와 가격 날짜(p_date)를 'date' 컬럼으로 통일합니다.
    weather_df['date'] = pd.to_datetime(weather_df['tm']).dt.strftime('%Y-%m-%d')
    price_df['date'] = pd.to_datetime(price_df['p_date']).dt.strftime('%Y-%m-%d')

    # 3. 가격 데이터 필터링 (원하는 작물과 지역만 추출)
    # 여러 작물이 섞여 있을 수 있으므로 필터링이 필요합니다.
    filtered_price = price_df[
        (price_df['item_name'] == target_item) & 
        (price_df['location'] == target_location)
    ].copy()

    if filtered_price.empty:
        print(f"⚠️ {target_item}({target_location})에 해당하는 가격 데이터가 없습니다.")
        return

    # 4. 데이터 병합 (Left Join)
    # 날씨는 매일 데이터가 있으므로 weather_df를 왼쪽에 둡니다.
    final_df = pd.merge(
        weather_df[['date', 'avg_ta', 'max_ta', 'min_ta', 'sum_rn']], 
        filtered_price[['date', 'price', 'kind_name', 'unit']], 
        on='date', 
        how='left'
    )

    # 5. 정제 및 결측치 처리
    final_df = final_df.sort_values('date') # 날짜순 정렬
    
    # 강수량(sum_rn) NaN은 비가 안 온 것이므로 0으로 채움
    final_df['sum_rn'] = final_df['sum_rn'].fillna(0.0)
    
    # 주말/휴일 가격(price) NaN은 이전 영업일 가격(ffill)으로 채우고, 
    # 데이터 시작점의 빈값은 다음날 가격(bfill)으로 채움
    final_df['price'] = final_df['price'].ffill().bfill()
    
    # 작물 정보도 빈칸 채우기
    final_df['kind_name'] = final_df['kind_name'].ffill().bfill()
    final_df['unit'] = final_df['unit'].ffill().bfill()

    # 6. 결과 저장
    os.makedirs('analytics/data', exist_ok=True)
    save_path = f'analytics/data/{target_item}_integrated_data.csv'
    final_df.to_csv(save_path, index=False, encoding='utf-8-sig')

    print(f"✅ 통합 완료! ({len(final_df)}행)")
    print(f"📂 저장 경로: {save_path}")
    
    return final_df

if __name__ == "__main__":
    # 실행 (원하는 작물과 지역을 넣으세요)
    process_and_save_data(target_item="토마토", target_location="서울")