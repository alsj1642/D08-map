"""카카오 로컬 '주소 → 좌표', '좌표 → 주소' 변환.

다른 파일에서:  from geo import address_to_coord, coord_to_address
"""
import os

import requests
from dotenv import load_dotenv

# 🔌 API 주소는 여기 한 곳에만
API = {
    "address": "https://dapi.kakao.com/v2/local/search/address.json",
    "coord2address": "https://dapi.kakao.com/v2/local/geo/coord2address.json",
}


def _kakao_get(url, params):
    """카카오 로컬 API를 불러 JSON을 돌려준다. 문제가 있으면 '⛔' RuntimeError."""
    load_dotenv(override=True)
    rest_key = os.getenv("KAKAO_REST_API_KEY")
    if not rest_key:
        raise RuntimeError("⛔ .env 에 KAKAO_REST_API_KEY 가 없어요")

    try:
        res = requests.get(  # 🔌 API 호출
            url,
            headers={"Authorization": f"KakaoAK {rest_key}"},
            params=params,
            timeout=10,
        )
    except requests.RequestException:
        raise RuntimeError("⛔ 카카오 서버에 연결하지 못했어요 (인터넷 확인)") from None

    if res.status_code == 401:
        raise RuntimeError("⛔ 카카오 REST API 키가 틀렸어요")
    if res.status_code == 403:
        raise RuntimeError("⛔ 카카오맵 사용 설정을 켜 주세요")
    if res.status_code != 200:
        raise RuntimeError(f"⛔ 카카오 요청 실패 (상태 코드 {res.status_code})")
    return res.json()


def address_to_coord(address):
    """주소 → (위도, 경도). 못 찾거나 한국 밖 좌표면 None."""
    docs = _kakao_get(API["address"], {"query": address}).get("documents", [])
    if not docs:
        return None
    # 카카오의 x = 경도, y = 위도 (글자라서 float 로)
    위도 = float(docs[0]["y"])
    경도 = float(docs[0]["x"])
    if not (33 <= 위도 <= 39 and 124 <= 경도 <= 132):
        return None  # 한국 밖 좌표는 잘못된 값
    return 위도, 경도


def coord_to_address(위도, 경도):
    """(위도, 경도) → 도로명 주소. 도로명이 없으면 지번 주소. 못 찾으면 None."""
    # 보낼 때는 x = 경도, y = 위도
    docs = _kakao_get(API["coord2address"], {"x": 경도, "y": 위도}).get("documents", [])
    if not docs:
        return None
    road = docs[0].get("road_address")  # 비어 있을 수 있음(null)
    if road:
        return road["address_name"]
    return docs[0]["address"]["address_name"]


if __name__ == "__main__":
    address = input("주소를 입력하세요 (예: 서울 성동구 왕십리로 83-21): ").strip()
    if not address:
        print("주소가 비어 있어요")
    else:
        try:
            coord = address_to_coord(address)
            if coord is None:
                print(f"'{address}'을(를) 찾지 못했어요")
            else:
                위도, 경도 = coord
                print(f"1) 주소 → 좌표: ({위도}, {경도})")
                back = coord_to_address(위도, 경도)
                if back is None:
                    print("2) 좌표 → 주소: 이 좌표의 주소를 찾지 못했어요")
                else:
                    print(f"2) 좌표 → 주소: {back}")
        except RuntimeError as e:
            print(e)
    print("\n출처: 카카오 로컬 API (주소로 좌표 변환, 좌표로 주소 변환)")
