import requests
import pandas as pd
import json
import os
from datetime import datetime, timedelta

def get_3day_forecast(api_key):
    # 1. EndPoint 설정
    base_url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst'
    
    # [참고] 새벽에 실행할 경우 0500 예보가 아직 안 올라왔을 수 있으므로 안전하게 처리
    now = datetime.now()
    if now.hour < 6: # 오전 6시 이전이라면 어제 날짜의 23시 예보를 사용하거나 하는 로직이 필요할 수 있음
        base_date = (now - timedelta(days=1)).strftime('%Y%m%d')
        base_time = '2300'
    else:
        base_date = now.strftime('%Y%m%d')
        base_time = '0500'

    # 2. 파라미터 설정 (serviceKey 제외)
    params = {
        'pageNo': '1',
        'numOfRows': '1000',
        'dataType': 'JSON',
        'base_date': base_date,
        'base_time': base_time, 
        'nx': '60', 
        'ny': '127'
    }

    # 3. 인증키 직접 결합 (Forbidden 방지 필살기)
    request_url = f"{base_url}?serviceKey={api_key}"

    try:
        response = requests.get(request_url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # API 응답 결과 코드 확인
            if data['response']['header']['resultCode'] == '00':
                items = data['response']['body']['items']['item']
                df = pd.DataFrame(items)
                
                # 데이터 가공: TMP(기온) 항목만 필터링
                df_tmp = df[df['category'] == 'TMP'].copy()
                df_tmp['fcstValue'] = df_tmp['fcstValue'].astype(float)
                
                # 날짜별 요약 (평균, 최고, 최저)
                result_list = []
                for date, group in df_tmp.groupby('fcstDate'):
                    avg_temp = group['fcstValue'].mean()
                    max_temp = group['fcstValue'].max()
                    min_temp = group['fcstValue'].min()
                    
                    result_list.append({
                        '날짜': pd.to_datetime(date).strftime('%Y-%m-%d'),
                        '평균기온': round(avg_temp, 2),
                        '최고기온': max_temp,
                        '최저기온': min_temp,
                        '일교차': round(max_temp - min_temp, 2)
                    })
                
                return pd.DataFrame(result_list).head(3) # 오늘 포함 3일치 반환
            else:
                print(f"❌ 기상청 메시지: {data['response']['header']['resultMsg']}")
                return None
        else:
            print(f"❌ 접속 실패 (Status: {response.status_code})")
            return None

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None

if __name__ == "__main__":
    # 경로 설정
    secret_path = r"c:\Users\leeyh\Desktop\agri_python\secret.json"
    save_dir = r"c:\Users\leeyh\Desktop\agri_python\data"
    
    # 폴더가 없으면 생성
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # API 키 로드
    with open(secret_path, 'r', encoding='utf-8') as file:
        secrets = json.load(file)
    
    # 실행
    print("🌤️ 기상청 단기 예보 수집 중...")
    forecast_df = get_3day_forecast(secrets["WEATHER_API_KEY"])
    
    if forecast_df is not None:
        save_path = os.path.join(save_dir, "tomato_weather_forecast.csv")
        forecast_df.to_csv(save_path, index=False, encoding='utf-8-sig')
        print(f"✅ 예보 데이터 저장 완료: {save_path}")
        print(forecast_df)