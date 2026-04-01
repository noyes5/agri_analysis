import requests
import pandas as pd
import json
import os

def get_kamis_data(api_key, user_id, target_date):
    """
    KAMIS 원본 데이터를 가져와서 서버 규격(영문 컬럼명)으로 이름표만 바꿔줍니다.
    """
    url = "http://www.kamis.or.kr/service/price/xml.do"
    
    params = { 
        'action': 'dailyPriceByCategoryList',
        'p_cert_key': api_key,
        'p_cert_id': user_id,
        'p_returntype': 'json',
        'p_product_cls_code': '02',          # 02: 도매
        'p_item_category_code': '200',       # 200: 채소/과일류
        'p_regday': target_date              # 조회 일자 (YYYY-MM-DD)
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        # 데이터 존재 여부 확인
        if isinstance(data, dict) and data.get('data') and 'item' in data['data']:
            items = data['data']['item']
            df = pd.DataFrame(items)
            
            # [수정 포인트] 원본 컬럼명 -> FastAPI 서버 규격명 (schemas.py 기준)
            rename_map = {
                'item_name': 'item_name',   # 품목명 (배추, 토마토 등)
                'kind_name': 'kind_name',   # 품종명
                'rank': 'location',         # [참고] KAMIS는 rank(등급)나 countyname(지역)을 주는데, 
                                            # 우리 서버 location 컬럼에 맞춰줍니다.
                'unit': 'unit',             # 단위 (20kg 등)
                'dpr1': 'price'             # 당일 가격 (핵심 데이터)
            }
            
            # 1. 필요한 컬럼만 추출 및 이름 변경
            available_cols = [col for col in rename_map.keys() if col in df.columns]
            df = df[available_cols].copy()
            df.rename(columns=rename_map, inplace=True)
            
            # 2. 추가 정보: 이 데이터가 '어느 날짜'의 데이터인지 기록
            df['date'] = target_date
            
            # 3. 추가 정보: 품목 코드 (필요시)
            df['item_code'] = "" # 원본에 코드가 없으면 빈값으로 유지
            
            # 4. 가격 데이터 정제 (',' 제거 및 숫자 변환)
            # 원본 가격이 "25,000" 형태이므로 숫자 25000으로 바꿔줘야 DB에 들어갑니다.
            df['price'] = df['price'].astype(str).str.replace(',', '')
            df['price'] = df['price'].replace('-', '0').replace('', '0')
            df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0.0)
            
            # kamis_api.py의 return df 직전에 이 코드를 확실히 넣어주세요.
            # 서버 스키마에 정의된 모든 컬럼이 들어있어야 합니다.
            required_cols = ['date', 'item_code', 'item_name', 'kind_name', 'location', 'unit', 'price']
            for col in required_cols:
                if col not in df.columns:
                    df[col] = "" # 없는 컬럼은 빈 값으로 생성

            df = df[required_cols] # 순서와 구성을 강제함

            return df
            
        else:
            # 주말/공휴일 등 데이터 없음
            return None
            
    except Exception as e:
        print(f"[{target_date}] KAMIS 수집 중 오류: {e}")
        return None

# API 키 및 아이디 로드 부분
current_dir = os.path.dirname(os.path.abspath(__file__))
secret_path = os.path.join(current_dir, '..', 'secret.json')
with open(secret_path, 'r', encoding='utf-8') as file:
    secrets = json.load(file)
    MY_KAMIS_KEY = secrets["KAMIS_API_KEY"]
    MY_KAMIS_ID = secrets["KAMIS_USER_ID"]