import pandas as pd
import joblib
import os
from datetime import datetime, timedelta

def predict_3_days(target_item="토마토"):
    # 1. 모델과 최근 데이터 로드
    model_path = f'analytics/models/{target_item}_best_model.pkl'
    data_path = f'analytics/data/{target_item}_features.csv'
    
    if not os.path.exists(model_path):
        print("❌ 모델 파일이 없습니다.")
        return

    model = joblib.load(model_path)
    df = pd.read_csv(data_path)
    
    # 모델이 사용하는 특성 리스트
    features = [
        'avg_ta', 'max_ta', 'min_ta', 'sum_rn', 
        'month', 'day_of_week', 'is_weekend', 
        'price_lag_1', 'price_lag_7', 'price_rolling_7', 
        'temp_rolling_7', 'rain_sum_3d'
    ]

    # 가장 최근의 실제 데이터 한 줄 가져오기
    current_data = df.iloc[-1].copy()
    current_price = current_data['price']
    
    predictions = []
    base_date = datetime.now()

    print(f"🔮 [{target_item}] 향후 3일 가격 예측 보고서")
    print(f"📊 현재 가격: {int(current_price):,}원")
    print("-" * 40)

    # 2. 3일간 반복 예측 (재귀적 방식)
    for i in range(1, 4):
        # 예측용 데이터프레임 생성
        input_df = pd.DataFrame([current_data[features]])
        
        # 예측 실행
        pred_price = model.predict(input_df)[0]
        target_date = base_date + timedelta(days=i)
        
        predictions.append({
            "date": target_date.strftime('%Y-%m-%d'),
            "price": int(pred_price)
        })

        # --- 중요: 다음 날 예측을 위한 데이터 업데이트 ---
        # 실제 환경이라면 내일의 기상 예보를 넣어야 하지만, 
        # 여기서는 현재 기온이 유지된다고 가정하고 가격 정보만 업데이트합니다.
        
        current_data['price_lag_7'] = current_data['price_lag_1'] # 7일전 데이터를 한 칸 밀어냄 (간략화)
        current_data['price_lag_1'] = pred_price                 # 방금 예측한 가격이 내일의 '어제 가격'이 됨
        current_data['day_of_week'] = (current_data['day_of_week'] + 1) % 7
        current_data['is_weekend'] = 1 if current_data['day_of_week'] >= 5 else 0
        # --------------------------------------------

    # 3. 결과 출력
    for res in predictions:
        diff = res['price'] - current_price
        status = "▲ 상승" if diff > 0 else "▼ 하락"
        if diff == 0: status = "─ 보합"
        
        print(f"📅 {res['date']}: {res['price']:,}원 ({status} {abs(int(diff)):,}원)")
        # 다음 루프 비교를 위해 현재 가격 업데이트
        current_price = res['price']

    return predictions

if __name__ == "__main__":
    predict_3_days(target_item="토마토")