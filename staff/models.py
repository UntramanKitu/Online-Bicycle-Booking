from django.db import models
from django.conf import settings

# =========================================================================
# โมเดลประวัติส่วนตัวพนักงาน/เจ้าหน้าที่ (StaffProfile)
# =========================================================================
# คลาสนี้สร้างขึ้นมาเพื่อเก็บข้อมูลที่ "ลึกกว่า" บัญชีผู้ใช้งานปกติ 
# เช่น รหัสพนักงาน แผนก ตำแหน่ง และวันเริ่มงาน (คนที่เป็นแค่นักศึกษาจะไม่มีโปรไฟล์นี้)

class StaffProfile(models.Model):
    # ---------------------------------------------------------------------
    # 1. ตัวเลือกระดับสิทธิ์ของเจ้าหน้าที่ (Access Level)
    # ---------------------------------------------------------------------
    class AccessLevel(models.TextChoices):
        # BASIC = มีประวัติเฉยๆ แต่สิทธิ์ยังเท่ากับผู้ใช้ทั่วไป (อาจจะเป็นภารโรง หรือยาม)
        BASIC = 'BASIC', 'Basic'         
        # MANAGER = เจ้าหน้าที่ทั่วไปที่มีสิทธิ์เขียนข่าว หรือดูแลระบบบางส่วนได้
        MANAGER = 'MANAGER', 'Manager'   
        # ADMIN = ผู้ดูแลระบบสูงสุด สามารถลบข่าวคนอื่น หรือเพิ่ม/ลดสิทธิ์พนักงานได้
        ADMIN = 'ADMIN', 'Admin'         
        
    # ---------------------------------------------------------------------
    # 2. ตัวเลือกสถานะของประวัติ (Status)
    # ---------------------------------------------------------------------
    class Status(models.TextChoices):
        # ACTIVE = เป็นพนักงานที่ทำงานอยู่ปกติ
        ACTIVE = 'ACTIVE', 'Active'             
        # INACTIVE = ลาออก หรือไม่ได้ใช้งานแล้ว
        INACTIVE = 'INACTIVE', 'Inactive'       
        # SUSPENDED = ถูกแบน หรือพักงาน (เข้าระบบไม่ได้ชั่วคราว)
        SUSPENDED = 'SUSPENDED', 'Suspended'    
        # PENDING = เพิ่งกรอกฟอร์มขอสิทธิ์มา รอให้แอดมินกด "อนุมัติ" ก่อน
        PENDING = 'PENDING', 'Pending Approval' 
        
    # ---------------------------------------------------------------------
    # 3. ฟิลด์เก็บข้อมูลลงฐานข้อมูล
    # ---------------------------------------------------------------------
    # เชื่อมกับบัญชีผู้ใช้ (UnifiedUser) แบบ 1 ต่อ 1 
    # หมายความว่ายูสเซอร์ 1 บัญชี จะมีประวัติพนักงานได้แค่ 1 ประวัติเท่านั้น
    # on_delete=models.CASCADE แปลว่าถ้าบัญชีผู้ใช้โดนลบ ประวัตินี้ก็จะปลิวตามไปด้วย
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='staff_profile') 
    
    # รหัสพนักงาน (unique=True คือห้ามซ้ำกัน)
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True) 
    
    # ตำแหน่ง (เช่น "หัวหน้าฝ่ายทะเบียน", "นักวิชาการคอมพิวเตอร์")
    position = models.CharField(max_length=100) 
    
    # แผนก (เช่น "กองกิจการนักศึกษา", "ฝ่ายบุคคล")
    department = models.CharField(max_length=100, null=True, blank=True) 
    
    # เลือกระดับสิทธิ์และสถานะ โดยอิงจาก Choice ด้านบน
    access_level = models.CharField(max_length=20, choices=AccessLevel.choices, default=AccessLevel.BASIC) 
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE) 
    
    hire_date = models.DateField(null=True, blank=True) # วันที่เริ่มเข้าทำงาน
    
    created_at = models.DateTimeField(auto_now_add=True) # บันทึกเวลาตอนสร้างให้อัตโนมัติ
    updated_at = models.DateTimeField(auto_now=True)     # บันทึกเวลาตอนแก้ให้อัตโนมัติ

    # ---------------------------------------------------------------------
    # 4. ฟังก์ชันช่วยตรวจสอบสิทธิ์ (has_permission)
    # ---------------------------------------------------------------------
    # ฟังก์ชันนี้ฉลาดมาก! มันช่วยเช็คว่าคนๆ นี้มีสิทธิ์ "ถึงเกณฑ์" ที่ต้องการไหม
    # เช่น ถ้าเป้าหมายคือต้องการสิทธิ์ MANAGER แต่เราเป็น ADMIN ก็จะคืนค่าเป็น True ทันที เพราะ ADMIN ใหญ่กว่า MANAGER
    def has_permission(self, access_level: str) -> bool:
        # ดึงรายชื่อลำดับสิทธิ์มาเป็น Array: ['BASIC', 'MANAGER', 'ADMIN']
        levels = [choice[0] for choice in self.AccessLevel.choices]
        try:
            # ใช้ฟังก์ชัน .index() เพื่อหาเลขลำดับ แล้วเช็คว่าลำดับที่เรามี มันมากกว่าหรือเท่ากับลำดับที่ต้องการไหม?
            return levels.index(self.access_level) >= levels.index(access_level)
        except ValueError:
            # ป้องกันระบบพังถ้าเผลอส่งชื่อสิทธิ์แปลกๆ มา
            return False

    # กำหนดวิธีแสดงผลให้หน้าแอดมินหรือตอน Print ว่าให้ขึ้นเป็น "ชื่อยูสเซอร์ - ตำแหน่ง"
    def __str__(self):
        return f"{self.user.username} - {self.position}"