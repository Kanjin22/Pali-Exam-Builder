# Pali Exam Builder (ระบบออกข้อสอบบาลี)

โปรเจกต์นี้เป็นเว็บแบบ Static (เปิดใช้งานผ่าน GitHub Pages ได้) สำหรับ “ช่วยออกข้อสอบ” จากเนื้อหาบาลี/ไทย โดยเน้นการเตรียมข้อความให้เลือกเป็นช่วงหน้า แล้วนำไปจัดรูปแบบเป็นกระดาษข้อสอบที่พิมพ์ได้

## ลิงก์ใช้งาน
- หน้าออกข้อสอบ: https://kanjin22.github.io/Pali-Exam-Builder/pages/exam_builder.html

## แนวคิดหลัก
- เว็บอ่านข้อมูลจากไฟล์ใน repo โดยตรง (ไม่มี backend)
- เนื้อหาบาลีเป็นแกนหลักของการอ้างอิง (เช่น หน้า/เล่ม)
- รองรับการเพิ่ม “ฐานข้อมูลสำหรับเฉลย” แบบค่อย ๆ เติมทีหลัง โดยยึด `segment` เป็นหน่วยข้อมูล

## โครงสร้างโฟลเดอร์สำคัญ
- [pages/exam_builder.html](file:///d:/Pali-Exam-Builder/pages/exam_builder.html) หน้าเว็บหลักของระบบออกข้อสอบ
- `data/` รวมข้อมูลหนังสือทั้งหมด (บาลี/ไทย/segments)
  - `data/<ชื่อหนังสือ>/บาลี/` ข้อมูลบาลี (บางชุดเป็นไฟล์ `.dat`, บางชุดเป็นไฟล์ดิบ `.txt`)
  - `data/<ชื่อหนังสือ>/ไทย/` ข้อมูลไทย (รูปแบบไฟล์ตามชุดหนังสือ)
  - `data/<ชื่อหนังสือ>/segments/` ไฟล์ `segments` สำหรับเตรียมฐานข้อมูลคู่บาลี–ไทย (ใช้ทำเฉลย/ทำ indexing เพิ่มเติม)
- `tools/` สคริปต์ช่วยสร้างข้อมูล เช่น สร้าง `segments` จากไฟล์ดิบ

## การรันแบบ Local (แนะนำ)
การเปิดไฟล์ `pages/exam_builder.html` แบบ `file://` อาจถูกบล็อกการโหลดไฟล์ (`fetch`) โดย browser บางตัว แนะนำให้รันเป็น local web server จากโฟลเดอร์โปรเจกต์

ตัวอย่างด้วย Python:

```bash
python -m http.server 8000
```

แล้วเปิด:
- http://localhost:8000/pages/exam_builder.html

## รูปแบบข้อมูล “segments” (สำหรับทำเฉลย)
แนวทางนี้ตั้งใจให้ “เก็บไว้ก่อน แล้วค่อยเติมข้อมูลหลังสอบ” ได้ โดยใช้ JSONL (1 บรรทัด = 1 segment)

ตัวอย่างไฟล์:
- [ธมฺมปทฏฺฐกถา_๕.segments.jsonl](file:///d:/Pali-Exam-Builder/data/ธรรมบท/segments/ธมฺมปทฏฺฐกถา_๕.segments.jsonl)
- [ธมฺมปทฏฺฐกถา_๗.segments.jsonl](file:///d:/Pali-Exam-Builder/data/ธรรมบท/segments/ธมฺมปทฏฺฐกถา_๗.segments.jsonl)

ฟิลด์ที่ใช้ (สรุป):
- `id` รหัส segment
- `book`, `source`, `volume`
- `pageStart`, `pageEnd` รองรับประโยคค่อมหน้า
- `type` เช่น `heading`, `story_title`, `content`, `separator`
- `useInExamSelection` ใช้ตอน “สุ่ม/เลือก” ออกข้อสอบหรือไม่ (เช่น `separator` จะเป็น `false`)
- `pali` เนื้อหาบาลี
- `senseThai` แปลโดยอรรถ
- `literalThai` แปลโดยพยัญชนะ (เฉพาะชุดที่ต้องใช้)
- `thaiRelation` สัมพันธ์ไทย (เฉพาะชุดที่ต้องใช้)
- `thai` สำเนาของ `senseThai` เพื่อความเข้ากันได้กับข้อมูล/โค้ดเดิม

ไฟล์ตุ๊กตาสำหรับเริ่มทำข้อมูลจริง (JSONC มีคอมเมนต์):
- ดูรวมได้ที่ [data/README_โครงสร้างไฟล์เฉลย.md](file:///d:/Pali-Exam-Builder/data/README_โครงสร้างไฟล์เฉลย.md)

## สคริปต์ที่ใช้บ่อย
- สร้างไฟล์ตุ๊กตาเฉลย (JSONC): [create_answer_templates.py](file:///d:/Pali-Exam-Builder/tools/create_answer_templates.py)
- สร้าง segments ธรรมบท (ตัวอย่าง): [build_dhammapada_v5_segments.py](file:///d:/Pali-Exam-Builder/tools/build_dhammapada_v5_segments.py), [build_dhammapada_v7_segments.py](file:///d:/Pali-Exam-Builder/tools/build_dhammapada_v7_segments.py)

## หมายเหตุ
- โปรเจกต์นี้ตั้งใจให้เป็น “พื้นที่ทดลองและต่อยอด” จึงมีทั้งข้อมูลที่ใช้งานจริง และโครงสำหรับงานในอนาคต
- ข้อมูลหนังสือใน `data/` คัดลอกมาจากโปรแกรม BUDSIR 7 และโปรแกรมพระไตรปิฎก (TPD) แล้วมีการแก้ไข/ปรับปรุงเพิ่มเติมในส่วนของคำแปลเพื่อใช้ในการศึกษาเท่านั้น ไม่ได้นำไปใช้ในเชิงพาณิชย์
- ข้อมูลตัวบท/คำแปลใน `data/` อาจมีเงื่อนไขด้านลิขสิทธิ์ตามแหล่งที่มา ผู้ใช้งานควรตรวจสอบก่อนนำไปเผยแพร่หรือใช้งานเชิงพาณิชย์
