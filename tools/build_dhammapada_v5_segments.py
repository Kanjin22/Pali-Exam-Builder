from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(r"d:\Pali-Exam-Builder")
RAW_DIR = PROJECT_ROOT / "data" / "ธรรมบท" / "บาลี" / "(ไฟล์ดิบ) ธมฺมปทฏฺฐกถา (๕) ปญฺจโม ภาโค (สมบูรณ์)"
OUTPUT_DIR = PROJECT_ROOT / "data" / "ธรรมบท" / "segments"
OUTPUT_PATH = OUTPUT_DIR / "ธมฺมปทฏฺฐกถา_๕.segments.jsonl"

VOLUME_NO = 5
MAX_PAGE = 120


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


def clean_page_text_for_segments(page_text: str) -> str:
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
        out.append(line)
    joined = " ".join(out)
    joined = re.sub(r"\s+", " ", joined).strip()
    return joined


@dataclass
class Segment:
    id: str
    volume: int
    page_start: int
    page_end: int
    pali: str


def iter_segments() -> list[Segment]:
    segments: list[Segment] = []
    buf: list[str] = []
    start_page = 1

    seg_index = 0

    def flush(end_page: int) -> None:
        nonlocal seg_index, buf, start_page
        text = re.sub(r"\s+", " ", " ".join(buf)).strip()
        text = re.sub(r"\s+([ฯ.])", r"\1", text)
        if not text:
            buf = []
            start_page = end_page
            return
        seg_index += 1
        seg_id = f"dhammapada-v{VOLUME_NO}-s{seg_index:06d}"
        segments.append(Segment(id=seg_id, volume=VOLUME_NO, page_start=start_page, page_end=end_page, pali=text))
        buf = []
        start_page = end_page

    for page in range(1, MAX_PAGE + 1):
        chunk_path = RAW_DIR / chunk_filename_for_page(page)
        chunk_text = decode_thai_bytes(chunk_path.read_bytes())
        page_text = extract_raw_chunk_page_text(chunk_text, page)
        cleaned = clean_page_text_for_segments(page_text)
        if not cleaned:
            continue

        if not buf:
            start_page = page

        parts = re.split(r"(ฯ|\.)", cleaned)
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
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="\n") as f:
        for s in segments:
            f.write(
                json.dumps(
                    {
                        "id": s.id,
                        "book": "ธรรมบท",
                        "source": "ธมฺมปทฏฺฐกถา",
                        "volume": s.volume,
                        "pageStart": s.page_start,
                        "pageEnd": s.page_end,
                        "pali": s.pali,
                        "thai": "",
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    print(f"Wrote {len(segments)} segments to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
