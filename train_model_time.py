import os
import pandas as pd
import numpy as np
import warnings
import pmdarima as pm
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score # 지표 추가
from sklearn.linear_model import LinearRegression 
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.exponential_smoothing.ets import ETSModel

### 모델 비교: ARIMA vs ETS vs 회귀분석
# ARIMA: 과거의 오차와 흐름(자기 상관성)에 집중합니다.
# ETS: 최근 데이터에 더 높은 가중치를 두어 추세를 반영합니다.
# Regression: 가격 외의 '외부 변수(날씨)'가 가격에 미치는 영향을 계산합니다.

# 불필요한 경고 메시지 무시
warnings.filterwarnings('ignore')

def load_and_prepare_data():
    """데이터 로드 및 경로 설정 함수"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    file_path = os.path.join(project_root, 'data', 'tomato_5years_data.csv')
    
    if not os.path.exists(file_path):
        print(f"❌ 데이터를 찾을 수 없습니다: {file_path}")
        return None

    print("📊 1. 빅데이터를 불러옵니다...")
    df = pd.read_csv(file_path)
    df['날짜'] = pd.to_datetime(df['날짜'])
    df = df.sort_values('날짜').reset_index(drop=True)

    print("🪄 2. 파생 변수(Feature)를 생성합니다...")
    # 가격 추세 변수
    df['1일전_가격'] = df['당일가격(원)'].shift(1)
    df['3일_평균가격'] = df['당일가격(원)'].rolling(window=3).mean()
    df['7일_평균가격'] = df['당일가격(원)'].rolling(window=7).mean()
    
    # 기상 변수
    df['3일_누적강수량'] = df['일강수량'].rolling(window=3).sum()
    df['3일_평균기온'] = df['평균기온'].rolling(window=3).mean()
    df['일교차'] = df['최고기온'] - df['최저기온']

    return df.dropna().reset_index(drop=True)

def split_train_test(df, test_days=30):
    """훈련용과 평가용 데이터 분리 함수"""
    train_data = df.iloc[:-test_days].copy()
    test_data = df.iloc[-test_days:].copy()
    print(f"✂️ 3. 데이터 분할 완료 (Train: {len(train_data)}일, Test: {len(test_data)}일)")
    return train_data, test_data

def calculate_mape(y_true, y_pred):
    """MAPE 계산 함수"""
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

def evaluate_baseline_models(train_df, test_df):
    """최적화된 ARIMA vs ETS vs 회귀분석 성능 비교 (다양한 지표 추가)"""
    print("\n🎯 [Phase 1] 전통적 통계 모델 3종 비교 시작!")
    
    y_train = train_df['당일가격(원)'].values
    y_test = test_df['당일가격(원)'].values
    
    # 각 모델의 지표를 저장할 딕셔너리
    metrics_report = {}

    # ----------------------------------------
    # 1. 최적화된 ARIMA (Auto-ARIMA)
    # ----------------------------------------
    print("📈 1. 최적의 ARIMA 파라미터를 찾는 중...")
    auto_arima_model = pm.auto_arima(y_train, start_p=0, start_q=0, max_p=3, max_q=3,
                                     seasonal=False, stepwise=True, 
                                     suppress_warnings=True, error_action='ignore')
    arima_pred = auto_arima_model.predict(n_periods=len(y_test))
    
    metrics_report['ARIMA'] = {
        'RMSE': np.sqrt(mean_squared_error(y_test, arima_pred)),
        'MAE': mean_absolute_error(y_test, arima_pred),
        'MAPE(%)': calculate_mape(y_test, arima_pred),
        'R2': r2_score(y_test, arima_pred)
    }

    # ----------------------------------------
    # 2. ETS (지수평활법)
    # ----------------------------------------
    print("📉 2. 최적의 ETS 파라미터를 찾는 중...")

    # error, trend, seasonal 설정을 'add'로 두되, 
    # damped_trend=True를 주어 추세가 무한히 발산하는 것을 방지(자동 조절 효과)합니다.
    ets_model = ETSModel(y_train, error='add', trend='add', seasonal=None, damped_trend=True)
    ets_fit = ets_model.fit(disp=False)
    
    ets_pred = ets_fit.forecast(steps=len(y_test))
    
    metrics_report['ETS'] = {
        'RMSE': np.sqrt(mean_squared_error(y_test, ets_pred)),
        'MAE': mean_absolute_error(y_test, ets_pred),
        'MAPE(%)': calculate_mape(y_test, ets_pred),
        'R2': r2_score(y_test, ets_pred)
    }

    # ----------------------------------------
    # 3. 선형 회귀분석 (Linear Regression)
    # ----------------------------------------
    print("📋 3. 선형 회귀분석 훈련 중... (날씨 변수 반영)")
    features = ['1일전_가격', '3일_평균기온', '3일_누적강수량', '일교차']
    X_train, X_test = train_df[features], test_df[features]
    
    lr_model = LinearRegression().fit(X_train, y_train)
    lr_pred = lr_model.predict(X_test)
    
    metrics_report['Regression'] = {
        'RMSE': np.sqrt(mean_squared_error(y_test, lr_pred)),
        'MAE': mean_absolute_error(y_test, lr_pred),
        'MAPE(%)': calculate_mape(y_test, lr_pred),
        'R2': r2_score(y_test, lr_pred)
    }

    # ----------------------------------------
    # 결과 비교 출력 테이블
    # ----------------------------------------
    print("\n" + "="*70)
    print(f"{'Model':<15} | {'RMSE':<10} | {'MAE':<10} | {'MAPE(%)':<10} | {'R2':<8}")
    print("-" * 70)
    for model, m in metrics_report.items():
        print(f"{model:<15} | {m['RMSE']:<10.2f} | {m['MAE']:<10.2f} | {m['MAPE(%)']:<10.2f} | {m['R2']:<8.4f}")
    print("="*70)
    
    winner = min(metrics_report, key=lambda x: metrics_report[x]['RMSE'])
    print(f"🏆 [Phase 1 결과] RMSE 기준 승자: {winner}\n")
    
    return metrics_report[winner]['RMSE']

if __name__ == "__main__":
    model_df = load_and_prepare_data()
    
    if model_df is not None:
        train_df, test_df = split_train_test(model_df, test_days=30)
        best_baseline_rmse = evaluate_baseline_models(train_df, test_df)
        
        print(f"💡 목표 설정: 오차 {best_baseline_rmse:.2f}원")