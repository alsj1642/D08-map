"""AI가 알려 준 가게 목록(1.txt)을 카카오 장소 검색으로 사실 확인.

1.txt 한 줄 = "가게이름 | 주소" 또는 "가게이름 : 주소"
(앞 번호 1. 2) · 기호 - • · 표 기호 | --- | 는 떼고 읽음)
실행: python factcheck.py            (다른 파일: python factcheck.py 파일.txt)
"""
import re
import sys
import time
from pathlib import Path

from place import search_place

MAX_LINES = 30  # 한 번에 확인할 최대 줄 수 (쿼터·예절)
HEADER_NAMES = {"가게이름", "가게", "이름", "상호", "상호명", "장소"}


def read_text(path):
    """utf-8-sig → cp949 순서로 읽고, 어떤 인코딩으로 읽었는지 같이 돌려준다."""
    for enc in ("utf-8-sig", "cp949"):
        try:
            return Path(path).read_text(encoding=enc), enc
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"⛔ {path} 를 utf-8 / cp949 로 읽지 못했어요")


def parse_line(line):
    """한 줄 → (가게이름, 주소). 빈 줄·표 머리·구분선이면 None."""
    line = line.strip().replace("**", "")
    line = re.sub(r"^(\d+\s*[.)]|[-*•])\s*", "", line)  # 1.  2)  -  *  • 떼기
    if "|" in line:
        cells = [c.strip() for c in line.strip("|").split("|")]
    else:  # "가게이름 : 주소" — 주소 뒤 괄호에도 ':' 가 있을 수 있어 첫 ':' 에서만 자름
        cells = [c.strip() for c in line.split(":", 1)]
    cells = [c for c in cells if c]
    if cells and cells[0].isdigit():  # | 1 | 가게 | 주소 | 처럼 번호 칸이 있는 표
        cells = cells[1:]
    if len(cells) < 2 or all(set(c) <= set("-: ") for c in cells):
        return None  # 빈 줄, 구분선(| --- |)
    if cells[0].replace(" ", "") in HEADER_NAMES or cells[1] == "주소":
        return None  # 표 머리 줄
    return cells[0], cells[1]


def addr_key(address):
    """주소 → (구, 동·길). 첫 단어(서울특별시/서울) 표기 차이는 비교에서 뺀다."""
    words = address.split()
    for i, w in enumerate(words):
        if w.endswith(("구", "군")):  # 서울 성동구 성수동1가 / 서울특별시 성동구 왕십리로4길
            break
    else:
        i = 1  # 구·군이 없는 주소(세종 등): 첫 단어만 빼고
    gu = words[i] if i < len(words) else ""
    dong = words[i + 1] if i + 1 < len(words) else ""
    dong = re.sub(r"\d+가$", "", dong)  # 성수동1가 → 성수동
    return gu, dong


def same_name(kakao_name, name):
    """띄어쓰기 무시하고 같거나, 카카오 이름이 AI 이름 + 지점명(○○ 성수점)이면 같은 이름.
    반대(카카오 '오우' ↔ AI '오우도')는 다른 가게로 본다."""
    return kakao_name.replace(" ", "").startswith(name.replace(" ", ""))


def judge(name, address):
    """(판정 기호, 비교한 카카오 장소 또는 None)"""
    gu, dong = addr_key(address)
    name = re.sub(r"\s*\(.*?\)", "", name).strip()  # 매일로 커피(meilo coffee) → 매일로 커피
    results = search_place(f"{gu} {name}".strip(), size=15)
    same = [p for p in results if same_name(p["이름"], name)]
    if not same:
        # AI가 구를 틀렸으면 동네 검색에 안 잡힘 → 이름만으로 한 번 더 (🟡 찾기)
        time.sleep(0.1)
        same = [p for p in search_place(name, size=15) if same_name(p["이름"], name)]
    for p in same:
        # 카카오 쪽은 도로명·지번 둘 다 비교 (AI가 어느 쪽으로 썼을지 모름)
        if (gu, dong) in (addr_key(p["주소"]), addr_key(p["지번주소"])):
            return "✅", p
    if same:
        return "🟡", same[0]
    return "❌", None


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "1.txt"
    try:
        text, enc = read_text(path)
    except FileNotFoundError:
        print(f"⛔ {path} 파일이 없어요")
        sys.exit(1)
    except RuntimeError as e:
        print(e)
        sys.exit(1)
    print(f"{Path(path).name} 읽음 (인코딩: {enc})\n")

    rows = [r for r in map(parse_line, text.splitlines()) if r]
    if not rows:
        print("확인할 줄이 없어요. '가게이름 | 주소' 형식으로 적어 주세요")
    if len(rows) > MAX_LINES:
        print(f"줄이 {len(rows)}개라 앞 {MAX_LINES}개만 확인해요\n")
        rows = rows[:MAX_LINES]

    counts = {"✅": 0, "🟡": 0, "❌": 0}
    for i, (name, address) in enumerate(rows, 1):
        try:
            mark, p = judge(name, address)
        except RuntimeError as e:
            print(e)  # 키·설정·연결 문제면 바로 멈춤
            break
        counts[mark] += 1
        print(f"{i}. {mark} {name} | {address}")
        if p:
            print(f"      카카오: {p['이름']} | {p['주소']}")
        time.sleep(0.1)

    total = sum(counts.values())
    if total:
        wrong = counts["🟡"] + counts["❌"]
        print(f"\n✅ {counts['✅']}개 / 🟡 {counts['🟡']}개 / ❌ {counts['❌']}개 (총 {total}개)")
        print(f"AI 실수율: {wrong}/{total} = {wrong / total * 100:.1f}%")
        print("판정 기준: ✅ 이름이 같고 구·동(길)이 맞음 / 🟡 이름은 있지만 주소가 다름 / ❌ 못 찾음")
        print("          (주소 첫 단어 '서울특별시/서울'은 비교에서 뺌,")
        print("           검색어 = '구 + 가게이름', 없으면 '가게이름'만으로 한 번 더)")
    print("\n출처: 카카오 로컬 API (키워드로 장소 검색)")
