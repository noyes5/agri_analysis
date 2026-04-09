import pandas as pd
import numpy as np
import joblib
import os

# 모델 라이브러리
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

# 평가 지표
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def train_model(target_item="토마토"):
    file_path = f'analytics/data/{target_item}_features.csv'
    if not os.path.exists(file_path):
        print(f"❌ 학습용 데이터 파일을 찾을 수 없습니다: {file_path}")
        return

    # 1. 데이터 로드 및 학습 변수 설정
    df = pd.read_csv(file_path)
    
    # AI 학습에 사용할 특성들
    features = [
        'avg_ta', 'max_ta', 'min_ta', 'sum_rn', 
        'month', 'day_of_week', 'is_weekend', 
        'price_lag_1', 'price_lag_7', 'price_rolling_7', 
        'temp_rolling_7', 'rain_sum_3d'
    ]
    
    X = df[features]
    y = df['price']

    # 시계열 데이터이므로 shuffle=False로 설정하여 과거로 학습하고 미래를 테스트
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    # 2. 비교할 모델 정의
    models = {
        "RandomForest": RandomForestRegressor(n_estimators=300, random_state=42),
        "XGBoost": XGBRegressor(n_estimators=1000, learning_rate=0.05, max_depth=5, random_state=42),
        "LightGBM": LGBMRegressor(n_estimators=1000, learning_rate=0.05, verbose=-1, random_state=42)
    }

    results = []
    best_model = None
    best_r2 = -float('inf')
    best_name = ""

    print(f"🚀 [{target_item}] 모델 성능 비교 및 학습 시작...\n")

    # 3. 루프를 돌며 모델별 학습 및 평가
    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)

        # 지표 계산
        mae = mean_absolute_error(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        r2 = r2_score(y_test, preds)

        results.append({
            "Model": name,
            "MAE": round(mae, 2),
            "RMSE": round(rmse, 2),
            "R2_Score": round(r2, 4)
        })

        # 가장 성능이 좋은(R2가 높은) 모델 저장용
        if r2 > best_r2:
            best_r2 = r2
            best_model = model
            best_name = name

    # 4. 결과 출력
    report_df = pd.DataFrame(results)
    print("📊 --- 최종 모델 성적표 ---")
    print(report_df.to_string(index=False))
    print(f"\n🥇 최우수 모델: {best_name} (R2: {best_r2:.4f})")

    # 5. 최우수 모델 저장
    os.makedirs('analytics/models', exist_ok=True)
    save_path = f'analytics/models/{target_item}_best_model.pkl'
    joblib.dump(best_model, save_path)
    
    print(f"✅ 모델 저장 완료: {save_path}")

if __name__ == "__main__":
    train_model(target_item="토마토")