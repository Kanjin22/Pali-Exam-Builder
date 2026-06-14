from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(r"d:\Pali-Exam-Builder")
RAW_ROOT = PROJECT_ROOT / "data" / "วิสุทธิมรรค" / "บาลี"
OUTPUT_DIR = PROJECT_ROOT / "data" / "วิสุทธิมรรค" / "segments"

BOOK = "วิสุทธิมรรค"
SOURCE = "วิสุทฺธิมคฺค"

VOLUME_CONFIGS = {
    1: {
        "raw_dir_name": "(ไฟล์ดิบ) วิสุทฺธิมคฺคสฺส นาม ปกรณวิเสสสฺส (๑) ปฐโม ภาโค (สมบูรณ์)",
        "max_page": 291,
    },
    2: {
        "raw_dir_name": "(ไฟล์ดิบ) วิสุทฺธิมคฺคสฺส นาม ปกรณวิเสสสฺส (๒) ทุติโย ภาโค (สมบูรณ์)",
        "max_page": 288,
    },
}

THAI_DIGITS = str.maketrans({"๐": "0", "๑": "1", "๒": "2", "๓": "3", "๔": "4", "๕": "5", "๖": "6", "๗": "7", "๘": "8", "๙": "9"})


def parse_page_number(s: str) -> int:
    raw = str(s or "").strip().translate(THAI_DIGITS)
    m = re.search(r"\d+", raw)
    return int(m.group(0)) if m else 0


def pad_chunk_page_number(n: int) -> str:
    return str(int(n)).rjust(3, "0")


def chunk_filename_for_page(volume_no: int, max_page: int, page: int) -> str:
    local_page = max(1, min(max_page, int(page) if page else 1))
    chunk_start = ((local_page - 1) // 10) * 10 + 1
    chunk_end = min(max_page, chunk_start + 9)
    suffix = " (จบ)" if chunk_end >= max_page else ""
    if chunk_start == chunk_end:
        page_part = pad_chunk_page_number(chunk_start)
    else:
        page_part = f"{pad_chunk_page_number(chunk_start)}-{pad_chunk_page_number(chunk_end)}"
    return f"{SOURCE} ({'๑' if volume_no == 1 else str(volume_no).translate(str.maketrans('0123456789', '๐๑๒๓๔๕๖๗๘๙'))}) - หน้า {page_part}{suffix}.txt"


def decode_thai_bytes(b: bytes) -> str:
    for enc in ("utf-8", "cp874", "tis-620", "iso8859_11"):
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
        if m:
            markers.append((i, parse_page_number(m.group(1))))

    idx = next((j for j, (_, p) in enumerate(markers) if p == target_page), -1)
    if idx < 0:
        return str(text or "")

    start_line = min(len(lines), markers[idx][0] + 2)
    next_marker = markers[idx + 1] if idx + 1 < len(markers) else None
    end_line = max(start_line, next_marker[0] - 2) if next_marker else len(lines)
    page_lines = lines[start_line:end_line]

    while page_lines and re.match(r"^\s*=+\s*$", str(page_lines[-1] or "")):
        page_lines.pop()
    while page_lines and not str(page_lines[0] or "").strip():
        page_lines.pop(0)
    while page_lines and not str(page_lines[-1] or "").strip():
        page_lines.pop()

    return "\n".join(page_lines)


def strip_raw_pali_footnote_markers(text: str) -> str:
    out = str(text or "")
    out = out.replace("\u00a0", " ")
    out = re.sub(r"(^|[ \t])(?:\[[๐-๙0-9]{1,3}\]|[๐-๙0-9]{1,3})\s*-\s*", r"\1", out)
    out = re.sub(r"\[\s*[^\]\r\n\s]{1,4}\s*\]\s*-\s*", "", out)
    out = re.sub(r"\[\s*[^\]\r\n\s]{1,4}\s*\]", "", out)
    out = re.sub(r"^\s*\*\s*", "", out)
    return out


def clean_page_lines_for_segments(page_text: str) -> list[str]:
    out: list[str] = []
    for raw in str(page_text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = str(raw or "").rstrip()
        trimmed = line.strip()
        if not trimmed:
            continue
        if trimmed.startswith("@"):
            continue
        if re.fullmatch(r"[=]{10,}", trimmed):
            continue
        cleaned = strip_raw_pali_footnote_markers(line)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
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
    sense_thai: str = ""


def classify_segment_type(text: str) -> str:
    s = str(text or "").strip()
    if not s:
        return "content"
    if re.fullmatch(r"-{3,}", s):
        return "separator"
    if re.search(r"(นิทฺเทโส|ปริจฺเฉโท|ภาโค)$", s):
        return "heading"
    return "content"


def should_use_in_exam_selection(segment_type: str) -> bool:
    return segment_type != "separator"


def output_path_for_volume(volume_no: int) -> Path:
    return OUTPUT_DIR / f"{SOURCE}_{volume_no:02d}.segments.jsonl"


def raw_dir_for_volume(volume_no: int) -> Path:
    return RAW_ROOT / str(VOLUME_CONFIGS[volume_no]["raw_dir_name"])


def read_annotation_fields(obj: dict) -> AnnotationFields:
    return AnnotationFields(sense_thai=str(obj.get("senseThai") or obj.get("thai") or ""))


def load_existing_records(volume_no: int) -> tuple[dict[str, AnnotationFields], dict[str, AnnotationFields]]:
    output_path = output_path_for_volume(volume_no)
    if not output_path.exists():
        return {}, {}

    annotations_by_id: dict[str, AnnotationFields] = {}
    annotations_by_pali: dict[str, AnnotationFields] = {}

    with output_path.open("r", encoding="utf-8") as f:
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


def iter_segments(volume_no: int, max_page: int) -> list[Segment]:
    raw_dir = raw_dir_for_volume(volume_no)
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
        segments.append(
            Segment(
                id=f"visuddhi-v{volume_no}-s{seg_index:06d}",
                volume=volume_no,
                page_start=page_start,
                page_end=page_end,
                pali=cleaned,
            )
        )

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

    for page in range(1, max_page + 1):
        chunk_path = raw_dir / chunk_filename_for_page(volume_no, max_page, page)
        chunk_text = decode_thai_bytes(chunk_path.read_bytes())
        page_text = extract_raw_chunk_page_text(chunk_text, page)
        page_lines = clean_page_lines_for_segments(page_text)
        if not page_lines:
            continue

        for line in page_lines:
            line_type = classify_segment_type(line)
            if line_type in ("heading", "separator"):
                flush(page)
                add_segment(line, page, page)
                continue

            if not buf:
                start_page = page

            for part in re.split(r"(ฯ|\.)", line):
                if not part:
                    continue
                if part in ("ฯ", "."):
                    buf.append(part)
                    flush(page)
                    continue
                buf.append(part)

    if buf:
        flush(max_page)

    return segments


def write_volume_segments(volume_no: int) -> int:
    max_page = int(VOLUME_CONFIGS[volume_no]["max_page"])
    output_path = output_path_for_volume(volume_no)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    segments = iter_segments(volume_no, max_page)
    annotations_by_id, annotations_by_pali = load_existing_records(volume_no)

    with output_path.open("w", encoding="utf-8", newline="\n") as f:
        for segment in segments:
            segment_type = classify_segment_type(segment.pali)
            annotations = annotations_by_id.get(segment.id, annotations_by_pali.get(segment.pali, AnnotationFields()))
            f.write(
                json.dumps(
                    {
                        "id": segment.id,
                        "book": BOOK,
                        "source": SOURCE,
                        "volume": segment.volume,
                        "pageStart": segment.page_start,
                        "pageEnd": segment.page_end,
                        "type": segment_type,
                        "useInExamSelection": should_use_in_exam_selection(segment_type),
                        "pali": segment.pali,
                        "senseThai": annotations.sense_thai,
                        "thai": annotations.sense_thai,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    return len(segments)


def main() -> None:
    counts = {}
    for volume_no in sorted(VOLUME_CONFIGS):
        counts[volume_no] = write_volume_segments(volume_no)
    for volume_no, count in counts.items():
        print(f"Volume {volume_no}: wrote {count} segments to {output_path_for_volume(volume_no)}")


if __name__ == "__main__":
    main()
