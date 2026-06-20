from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(r"d:\Pali-Exam-Builder")
PALI_SEGMENTS_DIR = PROJECT_ROOT / "data" / "ธรรมบท" / "segments"
THAI_ROOT = PROJECT_ROOT / "data" / "ธรรมบท" / "ไทย"
OUTPUT_DIR = PROJECT_ROOT / "data" / "ธรรมบท" / "topics"


@dataclass(frozen=True)
class Topic:
    vagga: str
    story: str
    start_page: int
    end_page: int


THAI_DIGITS = str.maketrans({"๐": "0", "๑": "1", "๒": "2", "๓": "3", "๔": "4", "๕": "5", "๖": "6", "๗": "7", "๘": "8", "๙": "9"})


def thai_to_arabic(s: str) -> str:
    return str(s or "").translate(THAI_DIGITS)


def parse_page_number(s: str) -> int:
    raw = thai_to_arabic(str(s or "").strip())
    m = re.search(r"\d+", raw)
    return int(m.group(0)) if m else 0


def decode_thai_bytes(b: bytes) -> str:
    for enc in ("utf-8", "cp874", "tis-620", "iso8859_11"):
        try:
            t = b.decode(enc, errors="replace")
        except Exception:
            continue
        if "�" not in t:
            return t
    return b.decode("cp874", errors="replace")


def strip_html(s: str) -> str:
    t = str(s or "")
    t = re.sub(r"<\s*br\s*/?\s*>", "\n", t, flags=re.IGNORECASE)
    t = re.sub(r"<\s*/?\s*sup\b[^>]*>", "", t, flags=re.IGNORECASE)
    t = re.sub(r"<\s*/?\s*b\b[^>]*>", "", t, flags=re.IGNORECASE)
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("\u00a0", " ")
    return t


def clean_title_text(s: str) -> str:
    t = str(s or "")
    t = strip_html(t)
    t = re.sub(r"^\s*\d{1,4}\s+(?=[๐-๙0-9]+\.)", "", t)
    t = re.sub(r"\[\s*[๐-๙0-9]+\s*\]\s*$", "", t).strip()
    t = re.sub(r"\s+", " ", t).strip()
    t = t.replace("*", "").strip()
    return t


def extract_story_base_name(title: str) -> str:
    t = re.sub(r"^[๐-๙0-9]+\.\s*", "", title)
    t = re.sub(r"\s*\([๐-๙0-9]+\)\s*$", "", t)
    return t.strip()


HEADING_THAI_RE = re.compile(r"^\s*[๐-๙0-9]+\.\s*.+วรรค\s*วรรณนา\s*$")
STORY_THAI_RE = re.compile(r"^\s*[๐-๙0-9]+\.\s*เรื่อง.+$")


def iter_thai_page_lines(folder: Path, page: int) -> list[str]:
    candidates = [
        folder / f"{str(page).rjust(6, '0')}.txt",
        folder / f"{str(page).rjust(6, '0')}.TXT",
        folder / f"{str(page).rjust(3, '0')}.txt",
        folder / f"{str(page).rjust(3, '0')}.TXT",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        matches = sorted(folder.glob(f"*{str(page).rjust(3, '0')}.txt"))
        if matches:
            path = matches[0]
    if path is None:
        return []
    t = decode_thai_bytes(path.read_bytes())
    lines = []
    for raw in t.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if "class='footnote'" in raw or 'class="footnote"' in raw:
            continue
        cleaned = clean_title_text(raw)
        if cleaned:
            lines.append(cleaned)
    return lines


def build_thai_topics_for_folder(folder_name: str, max_page: int) -> list[Topic]:
    folder = THAI_ROOT / folder_name
    current_vagga = ""
    stories: list[dict] = []
    for page in range(1, max_page + 1):
        lines = iter_thai_page_lines(folder, page)
        for line in lines[:40]:
            if HEADING_THAI_RE.match(line):
                current_vagga = line
                break
        for line in lines:
            if STORY_THAI_RE.match(line):
                stories.append({
                    "vagga": current_vagga,
                    "story": line,
                    "start": page,
                    "end": -1
                })
            elif "จบ." in line and stories:
                current_story = stories[-1]
                if current_story["end"] == -1:
                    current_story["end"] = page
    topics: list[Topic] = []
    for i, s in enumerate(stories):
        start = s["start"]
        end = s["end"]
        next_start = stories[i + 1]["start"] if i + 1 < len(stories) else max_page
        if end == -1:
            end = max(start, min(max_page, next_start))
        end = max(start, min(max_page, end))
        topics.append(Topic(vagga=s["vagga"], story=s["story"], start_page=start, end_page=end))
    return topics


def build_pali_topics_from_segments(volume_no: int, max_page: int) -> list[Topic]:
    vol_thai = str(volume_no).translate(str.maketrans("0123456789", "๐๑๒๓๔๕๖๗๘๙"))
    path = PALI_SEGMENTS_DIR / f"ธมฺมปทฏฺฐกถา_{vol_thai}.segments.jsonl"
    if not path.exists():
        return []
    current_vagga = ""
    stories: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = str(raw or "").strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            typ = str(obj.get("type") or "").strip()
            pali = str(obj.get("pali") or "").strip()
            page = int(obj.get("pageStart") or 0) or 0
            if typ == "heading" and pali and page:
                current_vagga = pali
            if typ == "story_title" and pali and page:
                stories.append({
                    "vagga": current_vagga,
                    "story": pali,
                    "start": page,
                    "end": -1,
                    "base_name": extract_story_base_name(pali)
                })
            elif pali and stories:
                current_story = stories[-1]
                if current_story["end"] == -1 and pali == current_story["base_name"]:
                    current_story["end"] = page
    topics: list[Topic] = []
    for i, s in enumerate(stories):
        start = s["start"]
        end = s["end"]
        next_start = stories[i + 1]["start"] if i + 1 < len(stories) else max_page
        if end == -1:
            end = max(start, min(max_page, next_start))
        end = max(start, min(max_page, end))
        topics.append(Topic(vagga=s["vagga"], story=s["story"], start_page=start, end_page=end))
    return topics


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()

    pali_volume_cfg = {
        1: {"max_page": 148, "part_id": "dhamma-1"},
        2: {"max_page": 158, "part_id": "dhamma-2"},
        3: {"max_page": 190, "part_id": "dhamma-3"},
        4: {"max_page": 149, "part_id": "dhamma-4"},
        5: {"max_page": 120, "part_id": "dhamma-5"},
        6: {"max_page": 189, "part_id": "dhamma-6"},
        7: {"max_page": 162, "part_id": "dhamma-7"},
        8: {"max_page": 194, "part_id": "dhamma-8"},
    }

    thai_volume_cfg = {
        1: {"max_page": 215, "part_id": "p4-thai-raw", "folder_name": "ธรรมปทัฏฐกถา (๑)"},
        2: {"max_page": 241, "part_id": "p5-thai-2", "folder_name": "ธรรมปทัฏฐกถา (๒)"},
        3: {"max_page": 286, "part_id": "p5-thai-3", "folder_name": "ธรรมปทัฏฐกถา (๓)"},
        4: {"max_page": 225, "part_id": "p5-thai-4", "folder_name": "ธรรมปทัฏฐกถา (๔)"},
        5: {"max_page": 187, "part_id": "p6-thai-5", "folder_name": "ธรรมปทัฏฐกถา (๕)"},
        6: {"max_page": 295, "part_id": "p6-thai-6", "folder_name": "ธรรมปทัฏฐกถา (๖)"},
        7: {"max_page": 252, "part_id": "p6-thai-7", "folder_name": "ธรรมปทัฏฐกถา (๗)"},
        8: {"max_page": 302, "part_id": "p6-thai-8", "folder_name": "ธรรมปทัฏฐกถา (๘)"},
    }

    pali_parts: dict[str, list[dict]] = {}
    for vol, cfg in pali_volume_cfg.items():
        max_page = int(cfg["max_page"])
        part_id = str(cfg["part_id"])
        topics = build_pali_topics_from_segments(vol, max_page)
        pali_parts[part_id] = [
            {"vagga": t.vagga, "story": t.story, "pageStart": t.start_page, "pageEnd": t.end_page}
            for t in topics
        ]

    thai_parts: dict[str, list[dict]] = {}
    for vol, cfg in thai_volume_cfg.items():
        max_page = int(cfg["max_page"])
        part_id = str(cfg["part_id"])
        folder_name = str(cfg["folder_name"])
        topics = build_thai_topics_for_folder(folder_name, max_page)
        thai_parts[part_id] = [
            {"vagga": t.vagga, "story": t.story, "pageStart": t.start_page, "pageEnd": t.end_page}
            for t in topics
        ]

    write_json(
        OUTPUT_DIR / "dhammapada_topics_pali.json",
        {"generatedAt": generated_at, "source": "segments", "parts": pali_parts},
    )
    write_json(
        OUTPUT_DIR / "dhammapada_topics_thai.json",
        {"generatedAt": generated_at, "source": "tpd_thai_pages", "parts": thai_parts},
    )

    pali_count = sum(len(v) for v in pali_parts.values())
    thai_count = sum(len(v) for v in thai_parts.values())
    print(f"Wrote topics: pali={pali_count} stories, thai={thai_count} stories -> {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
