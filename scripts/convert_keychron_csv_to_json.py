"""
Keychron CSV 데이터를 MongoDB JSON 형식으로 변환하는 스크립트

2025-10-01 09:00, Claude 작성

이 스크립트는 products_keychron.csv 파일을 읽어서
MongoDB에 저장할 수 있는 JSON 형식으로 변환합니다.

주요 기능:
1. CSV 파일 읽기 및 파싱
2. 모든 제품 포함 (판매중 + 단종)
3. MongoDB 스키마에 맞춰 구조화
4. 제품 상태를 명확히 구분 (active/discontinued)
5. JSON 파일로 출력

변경 이력:
2025-10-01 09:30, Claude 수정 - 단종 제품도 포함하도록 변경
"""

import pandas as pd
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional


def clean_json_string(value: str) -> Any:
    """
    CSV에서 JSON 문자열 형식으로 저장된 값을 파싱
    
    Args:
        value: JSON 문자열 (예: '["적축", "청축"]')
        
    Returns:
        파싱된 Python 객체 (리스트, 딕셔너리 등)
    """
    if pd.isna(value) or value == '':
        return None
    
    if not isinstance(value, str):
        return value
    
    # "정보 없음", "미지원" 같은 값 처리
    if value in ['정보 없음', '미지원']:
        return None
    
    # JSON 문자열이면 파싱 시도
    if value.startswith('[') or value.startswith('{'):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    
    return value


def parse_price(price_str: str) -> Optional[int]:
    """
    가격 문자열을 정수로 변환
    
    Args:
        price_str: 가격 문자열 (예: "84,000")
        
    Returns:
        정수 가격 또는 None
    """
    if pd.isna(price_str):
        return None
    
    # 쉼표 제거하고 정수로 변환
    clean_price = str(price_str).replace(',', '').strip()
    try:
        return int(clean_price)
    except ValueError:
        return None


def extract_connectivity_info(row: pd.Series) -> Dict[str, Any]:
    """
    연결 방식 관련 정보 추출
    
    Args:
        row: 제품 데이터 행
        
    Returns:
        연결 방식 정보 딕셔너리
    """
    connectivity = {}
    
    # 연결 방식 파싱
    connection_method = row.get('connection_method', '')
    if pd.notna(connection_method):
        conn_lower = str(connection_method).lower()
        
        # 블루투스 정보
        if 'bluetooth' in conn_lower or '블루투스' in conn_lower:
            bt_version = None
            if '5.1' in conn_lower:
                bt_version = '5.1'
            elif '5.0' in conn_lower:
                bt_version = '5.0'
            
            connectivity['bluetooth'] = {
                'version': bt_version,
                'multi_device': 3  # Keychron 기본값
            }
        
        # USB 정보
        if 'usb' in conn_lower or 'type-c' in conn_lower or 'type c' in conn_lower:
            usb_type = 'USB-C' if 'type-c' in conn_lower or 'type c' in conn_lower else 'USB'
            connectivity['usb'] = {
                'type': usb_type,
                'cable_included': True
            }
        
        # 2.4GHz 정보
        supports_2_4ghz = row.get('supports_2_4ghz', '')
        if supports_2_4ghz and '지원' in str(supports_2_4ghz):
            connectivity['wireless_2_4ghz'] = True
    
    return connectivity if connectivity else None


def extract_battery_info(row: pd.Series) -> Optional[Dict[str, str]]:
    """
    배터리 정보 추출
    
    Args:
        row: 제품 데이터 행
        
    Returns:
        배터리 정보 딕셔너리 또는 None
    """
    battery_capacity = row.get('battery_capacity', '')
    bluetooth_runtime = row.get('bluetooth_runtime', '')
    
    if pd.isna(battery_capacity) or battery_capacity == '미지원':
        return None
    
    battery = {}
    
    if battery_capacity:
        battery['capacity'] = str(battery_capacity)
    
    if pd.notna(bluetooth_runtime) and bluetooth_runtime != '블루투스 미지원':
        battery['runtime'] = str(bluetooth_runtime)
    
    return battery if battery else None


def extract_switch_info(switch_str: str) -> Optional[List[str]]:
    """
    스위치 옵션 정보 추출 및 정리
    
    Args:
        switch_str: 스위치 정보 문자열 또는 JSON
        
    Returns:
        스위치 옵션 리스트
    """
    switches = clean_json_string(switch_str)
    
    if not switches:
        return None
    
    if isinstance(switches, list):
        # 리스트를 평탄화하고 중복 제거
        all_switches = []
        for item in switches:
            if isinstance(item, str):
                # "적축, 청축, 갈축" 같은 문자열 분리
                sub_switches = [s.strip() for s in item.replace('/', ',').split(',')]
                all_switches.extend(sub_switches)
        
        # 중복 제거하고 정렬
        return sorted(list(set(all_switches)))
    
    return [str(switches)]


def parse_dimensions(size_str: str) -> Optional[Dict[str, str]]:
    """
    크기 정보 파싱
    
    Args:
        size_str: 크기 문자열 (예: "357 x 130mm")
        
    Returns:
        크기 정보 딕셔너리
    """
    if pd.isna(size_str) or size_str == '정보 없음':
        return None
    
    return {
        'dimensions': str(size_str).strip()
    }


def convert_row_to_product(row: pd.Series, index: int) -> Dict[str, Any]:
    """
    CSV 행을 MongoDB 제품 문서로 변환
    
    Args:
        row: Pandas Series (CSV의 한 행)
        index: 제품 인덱스
        
    Returns:
        MongoDB 문서 형식의 딕셔너리
    """
    # 기본 제품 ID 생성 (KB-숫자4자리)
    product_id = f"KB-{str(row.get('id', index)).zfill(4)}"
    
    # 제품명
    product_name = row.get('product_name', '').strip()
    
    # 가격
    price = parse_price(row.get('price'))
    
    # 제품 상태 결정 (2025-10-01 09:30, Claude 수정)
    is_discontinued = row.get('discontinued', False)
    status = 'discontinued' if is_discontinued else 'active'
    
    # 기본 정보
    basic_info = {
        'name_kr': product_name,
        'name_en': product_name,  # 영문명은 별도 데이터가 없으므로 동일하게
        'status': status,
        'discontinued': is_discontinued,  # 명시적으로 표시
        'price': price,
        'currency': 'KRW'
    }
    
    # 스펙 정보
    specs = {
        'layout': row.get('keyboard_layout'),
        'keyboard_type': row.get('keyboard_type'),
        'switch_options': extract_switch_info(row.get('switch_options')),
        'connectivity': extract_connectivity_info(row),
        'battery': extract_battery_info(row),
        'hot_swappable': True if '핫스왑' in str(row.get('hot_swap_socket', '')) else False,
        'rgb': True if 'RGB' in str(row.get('backlight_pattern', '')) else False,
        'multimedia_keys': row.get('multi_media_key_count'),
        'frame_material': row.get('main_frame_material'),
        'keycap_profile': row.get('key_cap_profile'),
        'n_key_rollover': row.get('n_key_rollover'),
        'polling_rate': row.get('polling_rate')
    }
    
    # None 값 제거
    specs = {k: v for k, v in specs.items() if v is not None}
    
    # 호환성 정보
    platforms = row.get('support_platforms', '')
    if pd.notna(platforms):
        os_list = [p.strip() for p in str(platforms).replace('/', ',').split(',') if p.strip()]
        compatibility = {
            'os': os_list,
            'plug_and_play': 'Plug & Play' in str(row.get('plug_and_play', ''))
        }
    else:
        compatibility = None
    
    # 물리적 정보
    physical = {
        'size': parse_dimensions(row.get('size')),
        'weight': f"{row.get('weight')}g" if pd.notna(row.get('weight')) else None,
        'height': {
            'with_keycap': row.get('height_including_key_cap'),
            'without_keycap': row.get('height_not_including_key_cap')
        }
    }
    physical = {k: v for k, v in physical.items() if v is not None}
    
    # 색상 정보
    colors = clean_json_string(row.get('color'))
    
    # 패키지 내용물
    package_contents = clean_json_string(row.get('package_contents'))
    
    # 메타데이터
    metadata = {
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'data_source': 'products_keychron.csv',
        'tags': []
    }
    
    # 태그 생성 (검색 최적화용)
    tags = []
    if specs.get('layout'):
        tags.append(specs['layout'])
    if specs.get('hot_swappable'):
        tags.append('핫스왑')
    if specs.get('rgb'):
        tags.append('RGB')
    if specs.get('connectivity', {}).get('bluetooth'):
        tags.append('블루투스')
    if specs.get('connectivity', {}).get('wireless_2_4ghz'):
        tags.append('2.4GHz')
    
    # 단종 제품 태그 추가 (2025-10-01 09:30, Claude 추가)
    if is_discontinued:
        tags.append('단종')
    
    metadata['tags'] = tags
    
    # 최종 문서 구성
    product_doc = {
        'product_id': product_id,
        'brand': 'keychron',
        'category': 'keyboard',
        'model_name': product_name,
        'basic_info': basic_info,
        'specs': specs,
        'compatibility': compatibility,
        'physical': physical,
        'colors': colors,
        'package_contents': package_contents,
        'warranty_period': row.get('warranty_period'),
        'metadata': metadata
    }
    
    # None 값인 최상위 키 제거
    product_doc = {k: v for k, v in product_doc.items() if v is not None}
    
    return product_doc


def main():
    """메인 변환 프로세스"""
    
    print("=" * 60)
    print("Keychron CSV → MongoDB JSON 변환 시작")
    print("=" * 60)
    print()
    
    # CSV 파일 읽기
    csv_path = 'C:\\workspace\\CSAI\\products_keychron.csv'
    print(f"CSV 파일 로딩: {csv_path}")
    
    df = pd.read_csv(csv_path)
    print(f"총 {len(df)}개 제품 로드됨")
    print()
    
    # 2025-10-01 09:30, Claude 수정: 모든 제품 포함 (필터링 제거)
    # 제품 통계 출력
    active_count = len(df[df['discontinued'] == False])
    discontinued_count = len(df[df['discontinued'] == True])
    print(f"판매중인 제품: {active_count}개")
    print(f"단종된 제품: {discontinued_count}개")
    print(f"→ 모든 제품을 변환에 포함합니다")
    print()
    
    # 각 행을 제품 문서로 변환
    print("제품 데이터 변환 중...")
    products = []
    
    for idx, row in df.iterrows():
        try:
            product_doc = convert_row_to_product(row, idx)
            products.append(product_doc)
            
            # 진행상황 표시 (10개마다)
            if (len(products)) % 10 == 0:
                print(f"  변환 완료: {len(products)}/{len(df)}")
        
        except Exception as e:
            print(f"  ⚠️ 경고: 제품 {row.get('product_name')} 변환 중 오류: {e}")
            continue
    
    print(f"✅ 변환 완료: 총 {len(products)}개 제품")
    print()
    
    # JSON 파일로 저장
    output_path = 'C:\\workspace\\CSAI\\data\\products_keychron.json'
    
    # data 폴더가 없으면 생성
    import os
    os.makedirs('C:\\workspace\\CSAI\\data', exist_ok=True)
    
    print(f"JSON 파일 저장: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 저장 완료!")
    print()
    
    # 샘플 출력
    print("=" * 60)
    print("샘플 제품 (첫 번째)")
    print("=" * 60)
    print(json.dumps(products[0], ensure_ascii=False, indent=2))
    print()
    
    print("=" * 60)
    print("변환 완료!")
    print(f"출력 파일: {output_path}")
    print(f"총 제품 수: {len(products)}개")
    print("=" * 60)


if __name__ == '__main__':
    main()
