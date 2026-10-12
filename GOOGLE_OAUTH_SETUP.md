# วิธีตั้งค่าล็อกอินผ่าน Google (Google OAuth 2.0)

ระบบรองรับการล็อกอินด้วย **อีเมล/รหัสผ่าน** และ **บัญชี Google** อยู่แล้ว
ส่วนของ Google จะแสดงปุ่มก็ต่อเมื่อคุณตั้งค่าคีย์ไว้ในไฟล์ `.env` เท่านั้น

---

## 1) สร้างโปรเจกต์ + คีย์ใน Google Cloud Console

1. เข้า https://console.cloud.google.com/
2. สร้างโปรเจกต์ใหม่ (หรือเลือกโปรเจกต์เดิม)
3. ไปเมนู **APIs & Services → OAuth consent screen**
   - เลือก User Type = **External**
   - กรอก App name / email แล้วเซฟ
   - ที่หน้า **Test users** ให้เพิ่มอีเมล Google ที่ต้องการทดสอบ (ในช่วงที่แอดมินยังไม่ Approve app)
4. ไปเมนู **APIs & Services → Credentials → Create Credentials → OAuth client ID**
   - Application type = **Web application**
   - เพิ่ม **Authorized redirect URIs** ดังนี้
     ```
     http://127.0.0.1:8000/social-auth/complete/google-oauth2/
     http://localhost:8000/social-auth/complete/google-oauth2/
     ```
   - กด Create แล้วคัดลอก **Client ID** และ **Client Secret**

## 2) ใส่คีย์ในโปรเจกต์

1. ที่โฟลเดอร์รากของโปรเจกต์ ให้ **copy** ไฟล์ `.env.example` เป็นชื่อ `.env`
   ```powershell
   Copy-Item .env.example .env
   ```
2. เปิด `.env` แล้วแปะค่าจริงแทนค่า placeholder
   ```
   GOOGLE_OAUTH2_KEY=1234567890-xxxx.apps.googleusercontent.com
   GOOGLE_OAUTH2_SECRET=GOCSPX-xxxxxxxxxxxx
   ```
   > หมายเหตุ: บันทึก `.env` ด้วย encoding **UTF-8 โดยไม่มี BOM** (ถ้าเปิดด้วย VS Code เลือก UTF-8 ได้เลย)

## 3) รันและทดสอบ

```powershell
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py runserver
```

- เปิด http://127.0.0.1:8000/accounts/login/
- จะเห็นปุ่ม **"เข้าสู่ระบบด้วย Google"** ปรากฏขึ้นเมื่อตั้งค่าครบ
- กดปุ่มเพื่อล็อกอินด้วยบัญชี Google ได้เลย

> ถ้าไม่กดปุ่ม โปรดตรวจว่าค่าใน `.env` ถูกต้อง และไม่มี BOM นำหน้าบรรทัดแรก

---

## พฤติกรรมหลังล็อกอินด้วย Google

- ถ้าอีเมลนั้น **มีบัญชีอยู่แล้ว** ระบบจะผูกกับบัญชีเดิม (ใช้ข้อมูลเดิม)
- ถ้ายังไม่มี ระบบจะ **สร้างบัญชีใหม่อัตโนมัติ** โดย:
  - สร้าง `username` จากส่วนหน้าอีเมล เช่น `somchai@gmail.com` → `somchai` (กันซ้ำด้วยตัวเลข)
  - ไม่ตั้งรหัสผ่าน (ล็อกอินผ่าน Google ล้วน ๆ)
  - ให้สิทธิ์เริ่มต้น = ผู้ใช้ทั่วไป (BASIC) → ไปหน้าแรกที่อ่านประกาศได้เลย

## ความปลอดภัย

- ไฟล์ `.env` ถูกลงรายการใน `.gitignore` อยู่แล้ว **ห้าม commit คีย์จริงขึ้น Git**
- `SOCIAL_AUTH_REDIRECT_IS_HTTPS` ตอนนี้เป็น `False` เพื่อ dev; เมื่อ deploy จริงให้เปลี่ยนเป็น `True`
