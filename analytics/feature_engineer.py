import pandas as pd
import os

def create_features(target_item="토마토"):
    file_path = f'analytics/data/{target_item}_integrated_data.csv'
    
    if not os.path.exists(file_path):
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return

    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    print(f"🛠️ {target_item} 특성 공학(Feature Engineering) 시작...")

    # 1. 날짜 관련 변수 (계절성 및 요일 특성)
    df['month'] = df['date'].dt.month
    df['day_of_week'] = df['date'].dt.dayofweek  # 0:월, 6:일
    df['is_weekend'] = df['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)

    # 2. 가격 시계열 변수 (Lag Features)
    # AI에게 '어제 가격'과 '일주일 전 가격'을 힌트로 줍니다.
    df['price_lag_1'] = df['price'].shift(1)
    df['price_lag_7'] = df['price'].shift(7)
    
    # 가격 증감율 (어제 대비 얼마나 변했나?)
    df['price_diff'] = df['price'].shift(1).pct_change()

    # 3. 이동 평균 변수 (Rolling Windows)
    # 최근 7일간의 평균 기온과 가격 흐름
    df['price_rolling_7'] = df['price'].shift(1).rolling(window=7).mean()
    df['temp_rolling_7'] = df['avg_ta'].rolling(window=7).mean()

    # 4. 날씨 누적 변수
    # 최근 3일간 비가 얼마나 왔는가? (출하량에 영향을 줌)
    df['rain_sum_3d'] = df['sum_rn'].rolling(window=3).mean()

    # 결측치 제거 (Lag 변수 생성 시 발생하는 상단 NaN 제거)
    df = df.dropna().reset_index(drop=True)

    # 5. 결과 저장
    save_path = f'analytics/data/{target_item}_features.csv'
    df.to_csv(save_path, index=False, encoding='utf-8-sig')

    print(f"✅ 특성 생성 완료! (최종 컬럼 수: {len(df.columns)}개)")
    print(f"📂 저장 경로: {save_path}")
    
    return df

if __name__ == "__main__":
    create_features(target_item="토마토")