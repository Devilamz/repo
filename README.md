# repo

## Inventory Manager (Streamlit)

เพิ่มฟีเจอร์และโครงสร้างเบื้องต้น:

- จัดโครงสร้างเป็น layers: `ui/`, `models/`, `services/`, `de/` (DB)
- เพิ่มฟิลด์ร้านค้า: `address`, `phone`
- เพิ่มฟิลด์สินค้า: `Image_Path`, `Notes` และรองรับการอัปโหลดรูป
- เพิ่มตารางสำหรับ `orders`, `order_items`, `receipts`, `receipt_items`
- หน้าใหม่ใน UI: `รับออเดอร์`, `รับของ`, `พิมพ์` (พรีวิว/ดาวน์โหลดใบสั่งและใบรับของ), `รายงาน` (สรุปต้นทุน/กำไรตามรอบ)

วิธีใช้สั้นๆ:

1. รัน `streamlit run streamlit_app.py`
2. ไปที่เมนู `สินค้า` เพื่อเพิ่มสินค้าและรูป
3. ไปที่เมนู `จัดการร้าน` เพื่อเพิ่มร้าน (ใส่ที่อยู่/เบอร์ด้วย)
4. สร้าง `รอบการรับ` แล้วไปที่ `รับออเดอร์` เพื่อบันทึกออเดอร์จากร้าน
5. ไปที่ `รับของ` เพื่อบันทึกการรับจริง (สร้างใบรับของ)
6. ไปที่ `ลูกค้า` เพื่อจัดการข้อมูลลูกค้า (รหัส, ชื่อ, ที่อยู่, เบอร์)
7. ไปที่ `การแจกจ่ายร้าน` เพื่อแจกสินค้า แต่ก่อนบันทึกให้กด `Validate Allocation` เพื่อตรวจสอบว่าแจกไม่เกินยอดรับ แล้วกด `บันทึกการแจกจ่าย`
8. ไปที่ `พิมพ์` เพื่อดูและดาวน์โหลดใบสั่ง, ใบรับของ และใบเสร็จของแต่ละร้าน

สรุปขั้นตอนที่ผมได้ทำไปแล้ว:

- ตรวจสอบ repository และวางแผนงาน
- ออกแบบและอัปเดต schema (migration สำหรับ DB ที่มีอยู่แล้ว)
- เพิ่มฟังก์ชันการจัดการคำสั่งซื้อและการรับของ
- เพิ่ม UI สำหรับรับออเดอร์, รับของ, การแจกจ่าย และการพิมพ์
- เพิ่มการคำนวณต้นทุน/รายรับ/กำไร และการพิมพ์เอกสาร

ถัดไปผมจะ: แยก UI เป็นคอมโพเนนต์ ปรับ UX/ดีไซน์ให้สวยงาม และเพิ่มการทดสอบอัตโนมัติ

## Optional: PDF export (WeasyPrint)

The app can export print pages as PDF if `weasyprint` is installed along with system dependencies.

On Debian/Ubuntu you may need to install:

```bash
sudo apt install -y libpango-1.0-0 libgdk-pixbuf2.0-0 libcairo2 libffi-dev
pip install weasyprint
```

If `weasyprint` is not available the app will still provide HTML/CSV downloads and show a short instruction to enable PDF export.
