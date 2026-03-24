import pandas as pd
import joblib
import os

def predict_tomorrow():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. 저장된 모델 불러오기
    model_path = os.path.join(current_dir, 'models', 'tomato_best_model.pkl')
    if not os.path.exists(model_path):
        print("❌ 저장된 모델 파일이 없습니다. train_model_ml.py를 먼저 실행하세요.")
        return
    
    model = joblib.load(model_path)
    print("🤖 모델 로드 완료!")

    # 2. 기상청 예보 데이터 불러오기 (시험지)
    forecast_path = os.path.join(current_dir, 'data', 'tomato_weather_forecast.csv')
    forecast_df = pd.read_csv(forecast_path)
    
    # 3. 모델이 학습했던 데이터와 '똑같은 모양'으로 만들기 (전처리)
    # 학습 때 썼던 컬럼들: ['year', 'month', 'day', 'weekday', '평균기온', '최고기온', '최저기온', '일강수량']
    # 예보 데이터에는 '일강수량'이 PCP로 되어있을 수 있으니 0으로 임시 처리하거나 맞춰줘야 함
    
    forecast_df['날짜'] = pd.to_datetime(forecast_df['날짜'])
    forecast_df['year'] = forecast_df['날짜'].dt.year
    forecast_df['month'] = forecast_df['날짜'].dt.month
    forecast_df['day'] = forecast_df['날짜'].dt.day
    forecast_df['weekday'] = forecast_df['날짜'].dt.weekday
    
    # 예보 데이터에 '일강수량' 컬럼이 없다면 0으로 생성 (학습 모델 규격 맞춤)
    if '일강수량' not in forecast_df.columns:
        forecast_df['일강수량'] = 0 

    # 모델에 넣을 입력 데이터 선택 (학습 때와 순서/이름이 같아야 함)
    features = ['year', 'month', 'day', 'weekday', '평균기온', '최고기온', '최저기온', '일강수량']
    X_new = forecast_df[features]

    # 4. 예측 실행!
    predictions = model.predict(X_new)

    # 5. 결과 출력
    print("\n🔮 [토마토 가격 예측 결과]")
    print("-" * 40)
    for i in range(len(forecast_df)):
        target_date = forecast_df['날짜'].iloc[i].strftime('%Y-%m-%d')
        pred_price = round(predictions[i], -1) # 10원 단위 반올림
        print(f"📅 {target_date} 예상 가격: {int(pred_price):,}원")
    print("-" * 40)

if __name__ == "__main__":
    predict_tomorrow()