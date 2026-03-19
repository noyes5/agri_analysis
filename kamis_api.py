import requests
import pandas as pd
import json
import os

def get_kamis_data(api_key, user_id, target_date):
    """
    KAMIS(한국농수산식품유통공사) 일별 품목별 도매가격 데이터를 수집하고 전처리하는 함수입니다.
    
    Args:
        api_key (str): KAMIS Open API 인증키
        user_id (str): KAMIS 가입 아이디(이메일)
        target_date (str): 조회할 날짜 (YYYY-MM-DD 형식, 반드시 평일이어야 함!)
        
    Returns:
        pd.DataFrame: 전처리가 완료된 가격 데이터프레임 (데이터가 없거나 실패 시 None)
    """
    
    # 1. API 엔드포인트 및 파라미터 설정
    url = "http://www.kamis.or.kr/service/price/xml.do"
    
    params = {
        'action': 'dailyPriceByCategoryList', # 일별 부류별 도소매가격정보 조회
        'p_cert_key': api_key,
        'p_cert_id': user_id,
        'p_returntype': 'json',               # JSON 포맷으로 응답 요청
        'p_product_cls_code': '02',           # 02: 도매, 01: 소매
        'p_item_category_code': '200',        # 200: 과일류 (필요시 214: 채소류 등으로 변경)
        'p_regday': target_date               # 조회 일자
    }
    
    try:
        # 2. 데이터 요청 및 JSON 파싱
        response = requests.get(url, params=params)
        data = response.json()
        
        # 3. 데이터 정상 응답 및 구조 확인 (방어 로직)
        # KAMIS는 주말/공휴일에 데이터가 없으면 딕셔너리 구조가 무너지거나 리스트를 반환함
        is_valid_data = (
            isinstance(data, dict) and 
            data.get('data') and 
            isinstance(data['data'], dict) and 
            'item' in data['data']
        )
        
        if is_valid_data:
            # 4. 실제 데이터 알맹이(리스트 형태) 추출
            items = data['data']['item']
            
            # 5. 판다스 데이터프레임으로 변환
            df = pd.DataFrame(items)
            
            # 6. 분석에 필요한 핵심 컬럼만 명시적으로 선택
            # dpr1: 당일가격, dpr2: 1일전가격, dpr3: 1개월전가격, dpr4: 1년전가격
            target_columns = ['item_name', 'kind_name', 'rank', 'unit', 'dpr1', 'dpr4']
            df = df[target_columns].copy()
            
            # 7. 누구나 알아보기 쉽게 한글 컬럼명으로 변경
            df.columns = ['품목', '품종', '등급', '단위', '당일가격(원)', '1년전가격(원)']
            
            # 8. 전처리: 가격 데이터 중 비어있는 값('-') 처리 로직을 여기에 추가할 수 있음
            
            return df
            
        else:
            # 주말이거나 API 승인이 아직 나지 않은 경우
            print(f"[{target_date}] 해당 날짜의 데이터가 없습니다. (주말/공휴일 휴장이거나 승인 대기 중일 수 있습니다.)")
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
    
    # B. 안전하게 파일 열고 API 키와 아이디 가져오기
    with open(secret_path, 'r', encoding='utf-8') as file:
        secrets = json.load(file)
        
    my_kamis_key = secrets["KAMIS_API_KEY"]
    my_kamis_id = secrets["KAMIS_USER_ID"]
    
    # C. 데이터 수집 테스트 (반드시 평일 날짜로 설정)
    test_date = '2023-07-05'
    print(f"KAMIS 가격 데이터를 수집하는 중입니다... (조회일: {test_date})\n")
    
    price_df = get_kamis_data(my_kamis_key, my_kamis_id, test_date)
    
    if price_df is not None:
        print("✅ 가격 데이터 수집 및 전처리 완료!\n")
        print(price_df.head())