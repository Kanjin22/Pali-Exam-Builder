from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(r"d:\Pali-Exam-Builder")
RAW_DIR = PROJECT_ROOT / "data" / "ธรรมบท" / "บาลี" / "(ไฟล์ดิบ) ธมฺมปทฏฺฐกถา (๗) สตฺตโม ภาโค (สมบูรณ์)"
OUTPUT_DIR = PROJECT_ROOT / "data" / "ธรรมบท" / "segments"
OUTPUT_PATH = OUTPUT_DIR / "ธมฺมปทฏฺฐกถา_๗.segments.jsonl"

VOLUME_NO = 7
MAX_PAGE = 162


THAI_DIGITS = str.maketrans({"๐": "0", "๑": "1", "๒": "2", "๓": "3", "๔": "4", "๕": "5", "๖": "6", "๗": "7", "๘": "8", "๙": "9"})


def to_thai_digits(n: int) -> str:
    s = str(int(n))
    return s.translate(str.maketrans("0123456789", "๐๑๒๓๔๕๖๗๘๙"))


def parse_page_number(s: str) -> int:
    raw = str(s or "").strip().translate(THAI_DIGITS)
    m = re.search(r"\d+", raw)
    return int(m.group(0)) if m else 0


def pad_chunk_page_number(n: int) -> str:
    return str(int(n)).rjust(3, "0")


def chunk_filename_for_page(page: int) -> str:
    local_page = max(1, min(MAX_PAGE, int(page) if page else 1))
    chunk_start = ((local_page - 1) // 10) * 10 + 1
    chunk_end = min(MAX_PAGE, chunk_start + 9)
    suffix = " (จบ)" if chunk_end >= MAX_PAGE else ""
    range_part = f"{pad_chunk_page_number(chunk_start)}-{pad_chunk_page_number(chunk_end)}"
    vol_thai = to_thai_digits(VOLUME_NO)
    return f"ธมฺมปทฏฺฐกถา ({vol_thai}) - หน้า {range_part}{suffix}.txt"


def decode_thai_bytes(b: bytes) -> str:
    encodings = ["utf-8", "cp874", "tis-620", "iso8859_11"]
    for enc in encodings:
        try:
            t = b.decode(enc, errors="replace")
        except Exception:
            continue
        if "�" not in t:
            return t
    return b.decode("utf-8", errors="replace")


def extract_raw_chunk_page_text(text: str, target_page: int) -> str:
    lines = str(text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    markers: list[tuple[int, int]] = []
    for i, raw in enumerate(lines):
        line = str(raw or "").strip()
        m = re.search(r"หน้า\s*([๐-๙0-9]+)\s*$", line)
        if not m:
            continue
        markers.append((i, parse_page_number(m.group(1))))

    idx = next((j for j, (_, p) in enumerate(markers) if p == target_page), -1)
    if idx < 0:
        return str(text or "")

    start_line = min(len(lines), markers[idx][0] + 2)
    next_marker = markers[idx + 1] if idx + 1 < len(markers) else None
    end_line = (max(start_line, next_marker[0] - 2) if next_marker else len(lines))
    page_lines = lines[start_line:end_line]

    while page_lines and re.match(r"^\s*=+\s*$", str(page_lines[-1] or "")):
        page_lines.pop()
    while page_lines and not str(page_lines[0] or "").strip():
        page_lines.pop(0)
    while page_lines and not str(page_lines[-1] or "").strip():
        page_lines.pop()

    return "\n".join(page_lines)


def clean_page_lines_for_segments(page_text: str) -> list[str]:
    lines = str(page_text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: list[str] = []
    for raw in lines:
        line = str(raw or "").replace("\u00a0", " ").rstrip()
        trimmed = line.strip()
        if not trimmed:
            continue
        if trimmed.startswith("@"):
            continue
        if re.fullmatch(r"[=]{10,}", trimmed):
            continue
        cleaned = re.sub(r"\s+", " ", trimmed).strip()
        if cleaned:
            out.append(cleaned)
    return out


@dataclass
class Segment:
    id: str
    volume: int
    page_start: int
    page_end: int
    pali: str


@dataclass
class AnnotationFields:
    literal_thai: str = ""
    sense_thai: str = ""
    thai_relation: str = ""


def classify_segment_type(text: str) -> str:
    s = str(text or "").strip()
    if not s:
        return "content"
    if re.fullmatch(r"-{3,}", s):
        return "separator"
    if re.match(r"^[๐-๙0-9]+\.\s*.+วณฺณนา$", s):
        return "heading"
    if re.match(r"^[๐-๙0-9]+\.\s*.+วตฺถุ\.\s*(\([๐-๙0-9]+\))?$", s):
        return "story_title"
    return "content"


def should_use_in_exam_selection(segment_type: str) -> bool:
    return segment_type != "separator"


def read_annotation_fields(obj: dict) -> AnnotationFields:
    sense_thai = str(obj.get("senseThai") or obj.get("thai") or "")
    return AnnotationFields(
        literal_thai=str(obj.get("literalThai") or ""),
        sense_thai=sense_thai,
        thai_relation=str(obj.get("thaiRelation") or ""),
    )


def load_existing_records() -> tuple[dict[str, AnnotationFields], dict[str, AnnotationFields]]:
    if not OUTPUT_PATH.exists():
        return {}, {}
    annotations_by_id: dict[str, AnnotationFields] = {}
    annotations_by_pali: dict[str, AnnotationFields] = {}
    with OUTPUT_PATH.open("r", encoding="utf-8") as f:
        for raw in f:
            line = str(raw or "").strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            seg_id = str(obj.get("id") or "").strip()
            pali = str(obj.get("pali") or "").strip()
            if not seg_id:
                continue
            annotations = read_annotation_fields(obj)
            annotations_by_id[seg_id] = annotations
            if pali and pali not in annotations_by_pali:
                annotations_by_pali[pali] = annotations
    return annotations_by_id, annotations_by_pali


def iter_segments() -> list[Segment]:
    segments: list[Segment] = []
    buf: list[str] = []
    start_page = 1

    seg_index = 0

    def add_segment(text: str, page_start: int, page_end: int) -> None:
        nonlocal seg_index
        cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
        cleaned = re.sub(r"\s+([ฯ.])", r"\1", cleaned)
        if not cleaned:
            return
        seg_index += 1
        seg_id = f"dhammapada-v{VOLUME_NO}-s{seg_index:06d}"
        segments.append(Segment(id=seg_id, volume=VOLUME_NO, page_start=page_start, page_end=page_end, pali=cleaned))

    def flush(end_page: int) -> None:
        nonlocal buf, start_page
        text = re.sub(r"\s+", " ", " ".join(buf)).strip()
        text = re.sub(r"\s+([ฯ.])", r"\1", text)
        if not text:
            buf = []
            start_page = end_page
            return
        add_segment(text, start_page, end_page)
        buf = []
        start_page = end_page

    for page in range(1, MAX_PAGE + 1):
        chunk_path = RAW_DIR / chunk_filename_for_page(page)
        chunk_text = decode_thai_bytes(chunk_path.read_bytes())
        page_text = extract_raw_chunk_page_text(chunk_text, page)
        page_lines = clean_page_lines_for_segments(page_text)
        if not page_lines:
            continue

        for line in page_lines:
            line_type = classify_segment_type(line)
            if line_type in ("heading", "story_title", "separator"):
                flush(page)
                add_segment(line, page, page)
                continue

            if not buf:
                start_page = page

            parts = re.split(r"(ฯ|\.)", line)
            for part in parts:
                if part == "":
                    continue
                if part in ("ฯ", "."):
                    buf.append(part)
                    flush(page)
                    continue
                buf.append(part)

    if buf:
        flush(MAX_PAGE)

    return segments


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    segments = iter_segments()
    existing_annotations_by_id, existing_annotations_by_pali = load_existing_records()
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="\n") as f:
        for s in segments:
            segment_type = classify_segment_type(s.pali)
            annotations = existing_annotations_by_id.get(s.id, existing_annotations_by_pali.get(s.pali, AnnotationFields()))
            f.write(
                json.dumps(
                    {
                        "id": s.id,
                        "book": "ธรรมบท",
                        "source": "ธมฺมปทฏฺฐกถา",
                        "volume": s.volume,
                        "pageStart": s.page_start,
                        "pageEnd": s.page_end,
                        "type": segment_type,
                        "useInExamSelection": should_use_in_exam_selection(segment_type),
                        "pali": s.pali,
                        "literalThai": annotations.literal_thai,
                        "senseThai": annotations.sense_thai,
                        "thaiRelation": annotations.thai_relation,
                        "thai": annotations.sense_thai,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    print(f"Wrote {len(segments)} segments to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

