import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, RobustScaler
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# 1. 데이터 로드
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, 'data', 'tomato_5years_data.csv')
df = pd.read_csv(file_path)

# 2. 전처리
df['날짜'] = pd.to_datetime(df['날짜'])
df['year'] = df['날짜'].dt.year
df['month'] = df['날짜'].dt.month
df['day'] = df['날짜'].dt.day
df['weekday'] = df['날짜'].dt.weekday # 요일 정보 추가 (0:월 ~ 6:일)

# 타겟 설정
y = df.pop('당일가격(원)')

# 학습에 사용할 변수들만 선택 (텍스트 컬럼인 '품목', '단위', '등급' 등은 제외)
# 만약 '지역' 컬럼이 있다면 포함시킵니다.
cols_to_use = ['year', 'month', 'day', 'weekday', '평균기온', '최고기온', '최저기온', '일강수량']
if '지역' in df.columns:
    cols_to_use.append('지역')

X = df[cols_to_use].copy()

# 🌟 [핵심] 문자열 데이터를 숫자로 변환 (Label Encoding)
from sklearn.preprocessing import LabelEncoder

if '지역' in X.columns:
    le = LabelEncoder()
    # .astype(str)을 붙여 혹시 모를 결측치나 타입 오류를 방지합니다.
    X['지역'] = le.fit_transform(X['지역'].astype(str))
    print(f"✅ '지역' 컬럼 인코딩 완료: {list(le.classes_)} -> {le.transform(le.classes_)}")

# 3. Encoder (지역 등 텍스트 변수가 있다면 진행)
# 현재 데이터에 '지역' 컬럼이 있다면 아래 로직 사용
if '지역' in X.columns:
    encoder = LabelEncoder()
    X['지역'] = encoder.fit_transform(X['지역'])

# 4. Scaler (RobustScaler 적용)
num_cols = X.select_dtypes(exclude=['object']).columns
scaler = RobustScaler()
X[num_cols] = scaler.fit_transform(X[num_cols])

# 5. 데이터 분할 (시계열 특성을 고려하여 순서 유지)
x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# 6. 모델 정의 및 훈련
models = {
    "RF": RandomForestRegressor(n_estimators=100, random_state=42),
    "XGB": XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42),
    "LGBM": LGBMRegressor(n_estimators=100, random_state=42)
}

results = {}

print(f"{'Model':<10} | {'RMSE':<12} | {'MAE':<12} | {'R2':<10}")
print("-" * 50)

for name, model in models.items():
    model.fit(x_train, y_train)
    pred = model.predict(x_test)
    
    rmse = np.sqrt(mean_squared_error(y_test, pred))
    mae = mean_absolute_error(y_test, pred)
    r2 = r2_score(y_test, pred)
    
    results[name] = {'model': model, 'rmse': rmse}
    print(f"{name:<10} | {rmse:<12.2f} | {mae:<12.2f} | {r2:<10.4f}")

# 7. 최적의 모델 선정 및 최종 저장
best_model_name = min(results, key=lambda x: results[x]['rmse'])
best_model = results[best_model_name]['model']
print(f"\n🏆 최종 선정 모델: {best_model_name}")

# 8. 모델 저장 (나중에 predict_price.py에서 사용)
import joblib
model_save_path = os.path.join(current_dir, 'models', 'tomato_best_model.pkl')
if not os.path.exists(os.path.dirname(model_save_path)):
    os.makedirs(os.path.dirname(model_save_path))
joblib.dump(best_model, model_save_path)
print(f"✅ 모델 저장 완료: {model_save_path}")