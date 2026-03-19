import requests
import pandas as pd
import json
import os

def get_weather_data(api_key, start_date, end_date, station_id="108"):
    """
    기상청 ASOS(종관기상관측) 일자별 데이터를 수집하고 전처리하는 함수입니다.
    
    Args:
        api_key (str): 공공데이터포털 API 인증키
        start_date (str): 조회 시작일 (YYYYMMDD)
        end_date (str): 조회 종료일 (YYYYMMDD)
        station_id (str): 관측 지점 번호 (108: 서울, 기본값)
        
    Returns:
        pd.DataFrame: 전처리가 완료된 날씨 데이터프레임 (실패 시 None)
    """
    
    # 1. API 엔드포인트 및 파라미터 설정
    url = 'http://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList'
    
    params = {
        'serviceKey': api_key,
        'pageNo': '1',
        'numOfRows': '100',
        'dataType': 'JSON',
        'dataCd': 'ASOS',    # 종관기상관측
        'dateCd': 'DAY',     # 일자별 데이터
        'startDt': start_date,
        'endDt': end_date,
        'stnIds': station_id
    }
    
    try:
        # 2. 데이터 요청 및 JSON 파싱
        response = requests.get(url, params=params)
        data = response.json()
        
        # 3. API 응답 코드가 정상('00')인지 확인
        if data['response']['header']['resultCode'] == '00':
            
            # 4. 실제 데이터 알맹이(리스트 형태) 추출
            items = data['response']['body']['items']['item']
            
            # 5. 판다스 데이터프레임으로 변환
            df = pd.DataFrame(items)
            
            # 6. 분석에 필요한 핵심 컬럼만 명시적으로 선택
            target_columns = ['tm', 'stnNm', 'avgTa', 'maxTa', 'minTa', 'sumRn', 'avgRhm']
            df = df[target_columns].copy()
            
            # 7. 누구나 알아보기 쉽게 한글 컬럼명으로 변경
            df.columns = ['날짜', '지점명', '평균기온', '최고기온', '최저기온', '일강수량', '평균습도']
            
            # 8. 전처리: 비가 오지 않은 날의 강수량 결측치('')를 '0'으로 변경
            df['일강수량'] = df['일강수량'].replace('', '0')
            
            return df
            
        else:
            # API에서 자체적으로 에러를 반환한 경우 (예: 키 오류, 트래픽 초과)
            error_msg = data['response']['header']['resultMsg']
            print(f"API 응답 에러: {error_msg}")
            return None
            
    except Exception as e:
        # 통신 오류 등 파이썬 실행 중 예외가 발생한 경우
        print(f"데이터 수집 중 오류가 발생했습니다: {e}")
        return None


# ==========================================
# 실행 부분 (보안 키 로드 및 테스트)
# ==========================================
if __name__ == "__main__":
    
    # A. 현재 파일의 절대 경로를 기준으로 secret.json 파일 찾기
    current_dir = os.path.dirname(os.path.abspath(__file__))
    secret_path = os.path.join(current_dir, 'secret.json')
    
    # B. 안전하게 파일 열고 API 키 가져오기
    with open(secret_path, 'r', encoding='utf-8') as file:
        secrets = json.load(file)
        
    my_weather_key = secrets["WEATHER_API_KEY"]
    
    # C. 데이터 수집 테스트 (2023년 7월 1일 ~ 10일, 서울)
    print("기상청 데이터를 수집하는 중입니다...\n")
    weather_df = get_weather_data(my_weather_key, '20230701', '20230710', '108')
    
    if weather_df is not None:
        print("✅ 기상 데이터 수집 및 전처리 완료!\n")
        print(weather_df)