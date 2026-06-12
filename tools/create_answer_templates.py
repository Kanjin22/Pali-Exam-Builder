from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(r"d:\Pali-Exam-Builder")
DATA_ROOT = PROJECT_ROOT / "data"


README_TEXT = """# โครงสร้างไฟล์เฉลยแบบตุ๊กตา

ไฟล์ในโฟลเดอร์ย่อย `segments` เป็นไฟล์ตัวอย่างแบบ `JSONC` สำหรับใช้เป็นแม่แบบตอนเริ่มทำข้อมูลจริง

## หลักการใช้
- ไฟล์จริงที่จะใช้ภายหลังควรเป็น `JSONL` คือ 1 บรรทัดต่อ 1 segment
- ไฟล์ `.template.jsonc` ชุดนี้มีคอมเมนต์ภาษาไทยเพื่ออธิบายฟิลด์ จึงเหมาะกับการดูโครงสร้าง ไม่ใช่ไฟล์สำหรับโหลดเข้าระบบโดยตรง
- เมื่อเริ่มทำจริง ให้คัดลอกไฟล์ตุ๊กตาไปเป็นชื่อจริง แล้วลบคอมเมนต์ออกหรือแปลงเป็น `JSONL`
- `pali` เป็นแกนหลักของทุกชุดหนังสือ
- `thai` เก็บไว้เป็นสำเนาของ `senseThai` เพื่อให้เข้ากับงานเดิมที่ยังอ้างฟิลด์นี้อยู่

## กติกาตามชุดหนังสือ
- ธรรมบท ภาค ๑-๔: ใช้ `literalThai`, `senseThai`
- ธรรมบท ภาค ๕-๘: ใช้ `literalThai`, `senseThai`, `thaiRelation`
- มังคลัตถทีปนี ถึง อภิธรรมฯ: ใช้ `senseThai` อย่างเดียว และคง `thai` ไว้เป็นสำเนา

## รายชื่อไฟล์ตุ๊กตาที่เตรียมไว้
- `data/ธรรมบท/segments/ธมฺมปทฏฺฐกถา_๑.template.jsonc` ถึง `ธมฺมปทฏฺฐกถา_๘.template.jsonc`
- `data/มังคลัตถทีปนี/segments/มงฺคลตฺถทีปนี_01.template.jsonc` และ `_02.template.jsonc`
- `data/สมันตปาสาทิกา/segments/สมนฺตปาสาทิกา_01.template.jsonc` ถึง `_03.template.jsonc`
- `data/วิสุทธิมรรค/segments/วิสุทฺธิมคฺค_01.template.jsonc` และ `_02.template.jsonc`
- `data/อภิธรรมฯ/segments/อภิธมฺมตฺถสงฺคหปาลิ.template.jsonc`
"""


TEMPLATE_DHAMMA_1_4 = """{
  // ใช้เป็นแม่แบบสำหรับ ธรรมบท ภาค ๑-๔
  // ไฟล์จริงภายหลังควรเป็น JSONL: 1 บรรทัด = 1 segment
  // thai เป็นสำเนาของ senseThai เพื่อให้เข้ากับงานเดิม
  "id": "dhammapada-v1-s000001",
  "book": "ธรรมบท",
  "source": "ธมฺมปทฏฺฐกถา",
  "volume": 1,
  "pageStart": 1,
  "pageEnd": 1,
  "type": "content",
  "useInExamSelection": true,
  "pali": "",
  "literalThai": "",
  "senseThai": "",
  "thai": ""
}
"""


TEMPLATE_DHAMMA_5_8 = """{
  // ใช้เป็นแม่แบบสำหรับ ธรรมบท ภาค ๕-๘
  // ชุดนี้มีสัมพันธ์ไทยเพิ่มจากภาค ๑-๔
  // thai เป็นสำเนาของ senseThai เพื่อให้เข้ากับงานเดิม
  "id": "dhammapada-v5-s000001",
  "book": "ธรรมบท",
  "source": "ธมฺมปทฏฺฐกถา",
  "volume": 5,
  "pageStart": 1,
  "pageEnd": 1,
  "type": "content",
  "useInExamSelection": true,
  "pali": "",
  "literalThai": "",
  "senseThai": "",
  "thaiRelation": "",
  "thai": ""
}
"""


TEMPLATE_SENSE_ONLY = """{
  // ใช้เป็นแม่แบบสำหรับหนังสือที่เก็บเฉพาะแปลโดยอรรถ
  // thai เป็นสำเนาของ senseThai เพื่อให้เข้ากับงานเดิม
  "id": "sample-s000001",
  "book": "",
  "source": "",
  "volume": 1,
  "pageStart": 1,
  "pageEnd": 1,
  "type": "content",
  "useInExamSelection": true,
  "pali": "",
  "senseThai": "",
  "thai": ""
}
"""


THAI_DIGITS = "๐๑๒๓๔๕๖๗๘๙"


def to_thai_digits(n: int) -> str:
    return "".join(THAI_DIGITS[int(ch)] for ch in str(n))


def make_dhamma_template(volume: int) -> str:
    if 1 <= volume <= 4:
        return (
            TEMPLATE_DHAMMA_1_4.replace('"id": "dhammapada-v1-s000001"', f'"id": "dhammapada-v{volume}-s000001"')
            .replace('"volume": 1', f'"volume": {volume}')
        )
    return (
        TEMPLATE_DHAMMA_5_8.replace('"id": "dhammapada-v5-s000001"', f'"id": "dhammapada-v{volume}-s000001"')
        .replace('"volume": 5', f'"volume": {volume}')
    )


def make_sense_only_template(sample_id: str, book: str, source: str, volume: int) -> str:
    return (
        TEMPLATE_SENSE_ONLY.replace('"id": "sample-s000001"', f'"id": "{sample_id}"')
        .replace('"book": ""', f'"book": "{book}"')
        .replace('"source": ""', f'"source": "{source}"')
        .replace('"volume": 1', f'"volume": {volume}')
    )


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def main() -> None:
    files_written = 0

    write_text(DATA_ROOT / "README_โครงสร้างไฟล์เฉลย.md", README_TEXT)
    files_written += 1

    for volume in range(1, 9):
        write_text(
            DATA_ROOT / "ธรรมบท" / "segments" / f"ธมฺมปทฏฺฐกถา_{to_thai_digits(volume)}.template.jsonc",
            make_dhamma_template(volume),
        )
        files_written += 1

    for volume in (1, 2):
        write_text(
            DATA_ROOT / "มังคลัตถทีปนี" / "segments" / f"มงฺคลตฺถทีปนี_{volume:02d}.template.jsonc",
            make_sense_only_template(f"mangala-v{volume}-s000001", "มังคลัตถทีปนี", "มงฺคลตฺถทีปนี", volume),
        )
        files_written += 1

    for volume in (1, 2, 3):
        write_text(
            DATA_ROOT / "สมันตปาสาทิกา" / "segments" / f"สมนฺตปาสาทิกา_{volume:02d}.template.jsonc",
            make_sense_only_template(f"samanta-v{volume}-s000001", "สมันตปาสาทิกา", "สมนฺตปาสาทิกา", volume),
        )
        files_written += 1

    for volume in (1, 2):
        write_text(
            DATA_ROOT / "วิสุทธิมรรค" / "segments" / f"วิสุทฺธิมคฺค_{volume:02d}.template.jsonc",
            make_sense_only_template(f"visuddhi-v{volume}-s000001", "วิสุทธิมรรค", "วิสุทฺธิมคฺค", volume),
        )
        files_written += 1

    write_text(
        DATA_ROOT / "อภิธรรมฯ" / "segments" / "อภิธมฺมตฺถสงฺคหปาลิ.template.jsonc",
        make_sense_only_template("abhidhamma-v1-s000001", "อภิธรรมฯ", "อภิธมฺมตฺถสงฺคหปาลิ", 1),
    )
    files_written += 1

    print(f"Wrote {files_written} files")


if __name__ == "__main__":
    main()
