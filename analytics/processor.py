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

def process_and_save_data(target_item="토마토"):
    print(f"🔄 [{target_item}] 데이터 통합 및 정제 시작...")

    # 1. 데이터 가져오기
    weather_df = fetch_data("weather-history")
    price_df = fetch_data("price")

    if weather_df.empty or price_df.empty:
        print("⚠️ 통합할 데이터가 부족합니다. DB를 확인해주세요.")
        return

    # 2. 날짜 형식 통일
    weather_df['date'] = pd.to_datetime(weather_df['date']).dt.strftime('%Y-%m-%d')
    price_df['date'] = pd.to_datetime(price_df['date']).dt.strftime('%Y-%m-%d')

    # 3. 가격 데이터 필터링 (품목만 체크)
    filtered_price = price_df[price_df['item_name'] == target_item].copy()

    if filtered_price.empty:
        available = price_df['item_name'].unique()
        print(f"⚠️ DB에 '{target_item}' 품목이 없습니다. (현재 품목: {available})")
        return

    # 4. 데이터 병합 (kind_name 대신 item_name 사용)
    # 규격(kind_name)이 섞이면 학습에 방해될 수 있으므로 대표 명칭인 item_name만 유지합니다.
    cols = ['date', 'price', 'item_name']
    if 'unit' in filtered_price.columns:
        cols.append('unit')

    final_df = pd.merge(
        weather_df[['date', 'avg_ta', 'max_ta', 'min_ta', 'sum_rn']], 
        filtered_price[cols], 
        on='date', 
        how='left'
    )

    # 5. 정제 및 결측치 처리
    final_df = final_df.sort_values('date')
    
    # 비 안온 날 0처리
    final_df['sum_rn'] = final_df['sum_rn'].fillna(0.0)
    
    # [핵심] 품목명 채우기 및 가격 결측치(주말 등) 처리
    final_df['item_name'] = final_df['item_name'].ffill().bfill()
    final_df['price'] = final_df['price'].ffill().bfill()
    
    if 'unit' in final_df.columns:
        final_df['unit'] = final_df['unit'].ffill().bfill()

    # 6. 결과 저장
    os.makedirs('analytics/data', exist_ok=True)
    save_path = f'analytics/data/{target_item}_integrated_data.csv'
    final_df.to_csv(save_path, index=False, encoding='utf-8-sig')

    print(f"✅ {target_item} 통합 완료! (총 {len(final_df)}행)")
    print(f"📂 저장 경로: {save_path}")
    
    return final_df

if __name__ == "__main__":
    process_and_save_data(target_item="토마토")