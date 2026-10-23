"""카카오 로컬 '키워드로 장소 검색'으로 장소 찾기.

다른 파일에서:  from place import search_place
"""
import os

import requests
from dotenv import load_dotenv

# 🔌 API 주소는 여기 한 곳에만
API = {
    "keyword": "https://dapi.kakao.com/v2/local/search/keyword.json",
}


def search_place(query, size=5):
    """검색어로 장소를 찾아 [{"이름", "주소", "위도", "경도"}, ...] 를 돌려준다.

    못 찾으면 빈 목록. 키·설정·연결 문제면 '⛔'로 시작하는 RuntimeError.
    """
    load_dotenv(override=True)
    rest_key = os.getenv("KAKAO_REST_API_KEY")
    if not rest_key:
        raise RuntimeError("⛔ .env 에 KAKAO_REST_API_KEY 가 없어요")

    try:
        res = requests.get(  # 🔌 API 호출
            API["keyword"],
            headers={"Authorization": f"KakaoAK {rest_key}"},
            params={"query": query, "size": size},
            timeout=10,
        )
    except requests.RequestException:
        raise RuntimeError("⛔ 카카오 서버에 연결하지 못했어요 (인터넷 확인)") from None

    if res.status_code == 401:
        raise RuntimeError("⛔ 카카오 REST API 키가 틀렸어요")
    if res.status_code == 403:
        raise RuntimeError("⛔ 카카오맵 사용 설정을 켜 주세요")
    if res.status_code != 200:
        raise RuntimeError(f"⛔ 카카오 검색 실패 (상태 코드 {res.status_code})")

    places = []
    for doc in res.json().get("documents", []):
        # 카카오의 x = 경도, y = 위도 (글자라서 float 로)
        위도 = float(doc["y"])
        경도 = float(doc["x"])
        if not (33 <= 위도 <= 39 and 124 <= 경도 <= 132):
            continue  # 한국 밖 좌표는 잘못된 값
        places.append({
            "이름": doc["place_name"],
            "주소": doc.get("road_address_name") or doc.get("address_name", ""),
            "위도": 위도,
            "경도": 경도,
        })
    return places


if __name__ == "__main__":
    query = input("검색어를 입력하세요 (예: 성수동 카페): ").strip()
    if not query:
        print("검색어가 비어 있어요")
    else:
        try:
            places = search_place(query)
        except RuntimeError as e:
            print(e)
        else:
            if not places:
                print(f"'{query}'을(를) 찾지 못했어요")
            for i, p in enumerate(places, 1):
                print(f"{i}. {p['이름']}, {p['주소']}, ({p['위도']}, {p['경도']})")
    print("\n출처: 카카오 로컬 API (키워드로 장소 검색)")
