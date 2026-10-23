"""장소를 검색해 카카오 지도 위에 마커로 찍은 map.html 만들기.

다른 파일에서:  from make_map import kakao_map
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from place import search_place

MAX_MARKERS = 200  # 너무 많으면 지도가 느려짐
MAP_FILE = Path(__file__).parent / "map.html"  # 어느 폴더에서 실행해도 D08-map 안에 만들기

HTML_TEMPLATE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>카카오 지도</title>
<style>
  body { margin: 0; font-family: sans-serif; }
  #map { width: 100%; height: 600px; }
  #help { padding: 8px 12px; font-size: 14px; color: #555; }
  .info { padding: 6px 10px; font-size: 13px; line-height: 1.5; min-width: 180px; }
  .info b { display: block; }
</style>
</head>
<body>
<div id="map"></div>
<p id="help">지도가 회색이면: ① 카카오맵 사용 설정 ② 지금 주소(포트까지) 등록 ③ 서버 주소로 열기</p>
<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=__JS_KEY__&autoload=false"></script>
<script>
const MARKERS = __MARKERS__;
kakao.maps.load(function () {
  const map = new kakao.maps.Map(document.getElementById("map"), {
    center: new kakao.maps.LatLng(37.5665, 126.9780),  // 장소가 없을 때: 서울시청
    level: 5,
  });
  const bounds = new kakao.maps.LatLngBounds();
  const info = new kakao.maps.InfoWindow({ removable: true });

  MARKERS.forEach(function (p) {
    const pos = new kakao.maps.LatLng(p["위도"], p["경도"]);
    const marker = new kakao.maps.Marker({ map: map, position: pos });
    bounds.extend(pos);

    // 이름·주소는 textContent 로 (따옴표·태그가 있어도 안 깨지게)
    const box = document.createElement("div");
    box.className = "info";
    const name = document.createElement("b");
    name.textContent = p["이름"];
    const addr = document.createElement("span");
    addr.textContent = p["주소"];
    box.append(name, addr);

    kakao.maps.event.addListener(marker, "click", function () {
      info.setContent(box);
      info.open(map, marker);
    });
  });

  // 마커가 다 화면에 들어오게 (1개면 setBounds 가 너무 확대해서 가운데로만)
  if (MARKERS.length === 1) {
    map.setCenter(new kakao.maps.LatLng(MARKERS[0]["위도"], MARKERS[0]["경도"]));
    map.setLevel(3);
  } else if (MARKERS.length > 1) {
    map.setBounds(bounds);
  }
});
</script>
</body>
</html>
"""


def kakao_map(js_key, markers):
    """[{"이름", "주소", "위도", "경도"}, ...] 를 마커로 찍은 지도 HTML 글자를 돌려준다.

    js_key 는 JavaScript 키만. REST 키는 절대 넣지 않는다.
    """
    data = [
        {"이름": m["이름"], "주소": m["주소"], "위도": m["위도"], "경도": m["경도"]}
        for m in markers[:MAX_MARKERS]
    ]
    # </script>, <!-- 같은 글자가 이름에 있어도 스크립트가 끊기지 않게
    data_js = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    return HTML_TEMPLATE.replace("__JS_KEY__", js_key).replace("__MARKERS__", data_js)


if __name__ == "__main__":
    load_dotenv(override=True)
    js_key = os.getenv("KAKAO_JS_KEY")
    query = input("검색어를 입력하세요 (예: 성수동 카페): ").strip()
    if not js_key:
        print("⛔ .env 에 KAKAO_JS_KEY 가 없어요")
    elif not query:
        print("검색어가 비어 있어요")
    else:
        try:
            places = search_place(query, size=10)
        except RuntimeError as e:
            print(e)
        else:
            if not places:
                print(f"'{query}'을(를) 찾지 못했어요")
            else:
                with open(MAP_FILE, "w", encoding="utf-8") as f:
                    f.write(kakao_map(js_key, places))
                for i, p in enumerate(places, 1):
                    print(f"{i}. {p['이름']}, {p['주소']}, ({p['위도']}, {p['경도']})")
                print(f"\nmap.html 을 만들었어요 (마커 {len(places)}개)")
                print("여는 법: 이 폴더에서  python -m http.server 8000 --bind 127.0.0.1")
                print("        → 브라우저에서 http://localhost:8000/map.html")
    print("\n출처: 카카오 로컬 API (키워드로 장소 검색), 카카오 지도 JavaScript SDK")
