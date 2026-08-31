#!/usr/bin/env python3
"""
process_data.py - 원본 데이터를 Jekyll 페이지 생성용 JSON으로 가공

입력: _rawdata/senior_raw.json
출력: _rawdata/senior.json (센터 목록), search_index.json (검색용, 루트)

사용법:
  python scripts/process_data.py [--limit N]
"""
import json, re, hashlib, sys, argparse
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
RAW = ROOT / "_rawdata" / "senior_raw.json"
OUT = ROOT / "_rawdata" / "senior.json"
SEARCH_INDEX_OUT = ROOT / "search_index.json"

DO_MAP = {
    "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구",
    "인천광역시": "인천", "광주광역시": "광주", "대전광역시": "대전",
    "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기",
    "강원특별자치도": "강원", "강원도": "강원",
    "충청북도": "충북", "충청남도": "충남",
    "전북특별자치도": "전북", "전라북도": "전북", "전라남도": "전남",
    "경상북도": "경북", "경상남도": "경남", "제주특별자치도": "제주",
    "전남광주통합특별시": "광주",
}


def make_slug(name: str, addr: str) -> str:
    slug = re.sub(r"[^\w가-힣\s-]", "", name).strip()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    h = hashlib.md5(f"{name}|{addr}".encode("utf-8")).hexdigest()[:6]
    return f"{slug}-{h}" if slug else h


def extract_sigungu(addr: str) -> str:
    if not addr:
        return ""
    for p in addr.split()[1:3]:
        if p.endswith(("시", "군", "구")):
            return p
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="로컬 미리보기용: 앞에서 N개만 처리")
    args = ap.parse_args()

    raw = json.loads(RAW.read_text(encoding="utf-8"))
    items = []
    seen_slugs = Counter()
    skipped = 0
    for d in raw:
        # 필드명 주의: Jekyll 내장 Page.name과 충돌하므로 "centerName" 사용
        center_name = (d.get("FLCT_NM") or "").strip()
        addr = (d.get("LCTN_ROAD_NM_ADDR") or "").strip() or (d.get("LCTN_LOTNO_ADDR") or "").strip()
        if not center_name or not addr:
            skipped += 1
            continue

        do_full = addr.split()[0]
        do_short = DO_MAP.get(do_full)
        if do_short is None:
            skipped += 1
            continue
        sigungu = extract_sigungu(addr)

        slug = make_slug(center_name, addr)
        seen_slugs[slug] += 1
        if seen_slugs[slug] > 1:
            slug = f"{slug}-{seen_slugs[slug]}"

        items.append({
            "centerName": center_name,
            "type": (d.get("FLCT_TYP") or "").strip(),
            "doShort": do_short,
            "doFull": do_full,
            "sigungu": sigungu,
            "addr": addr,
            "lat": (d.get("LAT") or "").strip(),
            "lng": (d.get("LOT") or "").strip(),
            "tel": (d.get("TELNO") or "").strip(),
            "buildDate": (d.get("BUIL_YMD") or "").strip(),
            "buildArea": (d.get("BUIL_AREA") or "").strip(),
            "institution": (d.get("MNG_INST_NM") or "").strip(),
            "refDate": (d.get("CRTR_YMD") or "").strip(),
            "slug": slug,
        })

    if args.limit:
        items = items[:args.limit]
        print(f"[--limit] 상위 {len(items)}개만 처리 (로컬 미리보기 모드)")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"경로당/마을회관 {len(items)}개 저장 → {OUT}  (제외: {skipped}건)")

    do_counts = Counter(i["doShort"] for i in items)
    print("\n지역별 수:")
    for do, cnt in sorted(do_counts.items(), key=lambda x: -x[1]):
        print(f"  {do}: {cnt}개")

    type_counts = Counter(i["type"] for i in items)
    print("\n유형별 수:")
    for t, cnt in type_counts.most_common():
        print(f"  {t}: {cnt}개")

    index = [
        {
            "n": i["centerName"], "slug": i["slug"], "doShort": i["doShort"],
            "sigungu": i["sigungu"], "addr": i["addr"], "type": i["type"],
        }
        for i in items
    ]
    SEARCH_INDEX_OUT.write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    size_mb = SEARCH_INDEX_OUT.stat().st_size / 1024 / 1024
    print(f"\n검색 인덱스 {len(index)}건 저장 → {SEARCH_INDEX_OUT} ({size_mb:.1f}MB)")


if __name__ == "__main__":
    main()
