from django.db import models
from django.conf import settings
from django.utils import timezone
import os
from django.db.models.signals import post_delete
from django.dispatch import receiver

# -------------------------------------------------------------------------
# โมเดล 1: AnnouncementCategory (หมวดหมู่ของประกาศ)
# -------------------------------------------------------------------------
# ใช้สำหรับจัดกลุ่มประกาศ เช่น "ข่าวทุนการศึกษา", "กิจกรรมนักศึกษา", "ประกาศรับสมัครงาน"
class AnnouncementCategory(models.Model):
    # ชื่อหมวดหมู่จำกัดความยาว 100 ตัวอักษร
    name = models.CharField(max_length=100)
    
    # สถานะเปิด/ปิดการใช้งานหมวดหมู่นี้ (ถ้าเป็น False หมวดหมู่นี้อาจจะไม่แสดงให้คนทั่วไปเห็น)
    is_active = models.BooleanField(default=True)
    
    # บันทึกเวลาที่สร้างหมวดหมู่นี้แบบอัตโนมัติ (auto_now_add=True แปลว่าสร้างครั้งแรกจะใส่วันที่ปัจจุบันให้เลย)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # ฟังก์ชันนี้ใช้เวลาเอาออบเจกต์ไปปรินต์ หรือแสดงผลในหน้า Admin มันจะแสดงเป็น "ชื่อหมวดหมู่" แทนที่จะเป็นคำว่า "Object(1)"
    def __str__(self):
        return self.name

# -------------------------------------------------------------------------
# โมเดล 2: CampusAnnouncement (ตัวประกาศข่าวสารหลัก)
# -------------------------------------------------------------------------
# โมเดลนี้เปรียบเสมือนโพสต์ 1 โพสต์ที่เอาไว้แสดงข้อมูลประกาศ
class CampusAnnouncement(models.Model):
    
    # ระดับความสำคัญของประกาศ เพื่อให้ระบบรู้ว่าควรเอาขึ้นแนะนำ หรือไฮไลท์สีแดงไหม
    class Priority(models.TextChoices):
        LOW = "LOW", "Low"          # ต่ำ
        NORMAL = "NORMAL", "Normal" # ปกติ
        HIGH = "HIGH", "High"       # สูง
        URGENT = "URGENT", "Urgent" # ด่วนมาก!
        
    # สถานะของตัวประกาศ ว่าจะให้ใครเห็นบ้าง หรือตั้งเวลาไว้
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"             # ฉบับร่าง (กำลังพิมพ์ ยังไม่เสร็จ)
        SCHEDULED = "SCHEDULED", "Scheduled" # ตั้งเวลาไว้ (ถึงเวลาค่อยเผยแพร่)
        PUBLISHED = "PUBLISHED", "Published" # เผยแพร่แล้ว (ทุกคนเห็นได้)
        EXPIRED = "EXPIRED", "Expired"       # หมดอายุแล้ว (อาจจะซ่อนหรือขึ้นป้ายหมดอายุ)
        ARCHIVED = "ARCHIVED", "Archived"    # จัดเก็บแล้ว (เก็บเข้ากรุ ไม่แสดงหน้าแรก)
        CANCELLED = "CANCELLED", "Cancelled" # ยกเลิกประกาศ

    # กลุ่มเป้าหมายที่ต้องการให้เห็นประกาศนี้
    class TargetAudience(models.TextChoices):
        ALL = "ALL", "All"           # เห็นทุกคน
        STUDENT = "STUDENT", "Student" # เห็นเฉพาะนักศึกษา
        STAFF = "STAFF", "Staff"       # เห็นเฉพาะเจ้าหน้าที่
        ADMIN = "ADMIN", "Admin"       # เห็นเฉพาะแอดมิน

    # ฟิลด์ข้อมูลหลัก
    title = models.CharField(max_length=255) # หัวข้อประกาศ
    content = models.TextField()             # เนื้อหาประกาศแบบยาว
    
    # หมวดหมู่ของประกาศ โยงไปหาโมเดล AnnouncementCategory (ถ้าลบหมวดหมู่ ให้ระงับไว้ห้ามลบ (PROTECT) จนกว่าจะย้ายประกาศออกไป)
    category = models.ForeignKey(AnnouncementCategory, on_delete=models.PROTECT, related_name="announcements")
    
    # การตั้งค่าตัวเลือกต่างๆ (ใช้ Choices ที่เราสร้างไว้ด้านบน)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.NORMAL)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DRAFT)
    target_audience = models.CharField(max_length=15, choices=TargetAudience.choices, default=TargetAudience.ALL)
    
    # รูปภาพหน้าปกของประกาศ (null=True คืออนุญาตให้ไม่มีรูปได้)
    cover_image = models.ImageField(upload_to="announcements/covers/", null=True, blank=True)
    
    # การตั้งเวลา
    publish_at = models.DateTimeField(null=True, blank=True) # เวลาที่เริ่มเผยแพร่
    expire_at = models.DateTimeField(null=True, blank=True)  # เวลาที่ประกาศจะหมดอายุ
    
    # หมุด (ปักหมุดประกาศนี้ให้อยู่บนสุดตลอดไหม)
    is_pinned = models.BooleanField(default=False)
    
    # ระบบลบแบบซ่อน (Soft Delete) - ใช้ตั้งค่าว่าถูกลบแล้วนะ แต่ยังไม่ลบออกจากฐานข้อมูลจริงๆ เพื่อกันพลาด
    is_deleted = models.BooleanField(default=False)
    
    # ข้อมูลการติดตาม (ใครเป็นคนสร้าง, แก้ไข, หรือลบ) โยงไปหาโมเดลผู้ใช้ (AUTH_USER_MODEL)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_announcements")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="updated_announcements")
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="deleted_announcements")
    
    # วันที่เวลาบันทึก
    created_at = models.DateTimeField(auto_now_add=True) # เวลาสร้าง (ลงเวลาอัตโนมัติ)
    updated_at = models.DateTimeField(auto_now=True)     # เวลาแก้ไขล่าสุด (อัปเดตอัตโนมัติทุกครั้งที่กดเซฟ)
    deleted_at = models.DateTimeField(null=True, blank=True) # เวลาที่ถูกกดลบแบบซ่อน

    # Meta เป็นคลาสพิเศษที่ใช้ตั้งค่าฐานข้อมูลระดับลึก
    class Meta:
        # สร้าง Index (สารบัญฐานข้อมูล) ช่วยให้ดึงข้อมูลค้นหาได้ไวขึ้นมาก
        indexes = [
            models.Index(fields=['status', 'is_deleted']),
            models.Index(fields=['publish_at']),
            models.Index(fields=['expire_at']),
            models.Index(fields=['category']),
            models.Index(fields=['is_pinned']),
        ]
        # สั่งเรียงลำดับเวลาดึงข้อมูล: เอาโพสต์ปักหมุดขึ้นก่อน (-is_pinned) ตามด้วยวันที่เผยแพร่ล่าสุด (-publish_at)
        ordering = ['-is_pinned', '-publish_at', '-created_at']

    def __str__(self):
        return self.title

    # ฟังก์ชันช่วยสำหรับ "ลบแบบซ่อน" แทนที่จะลบทิ้งไปเลย
    def soft_delete(self, user):
        self.is_deleted = True # เปลี่ยนสถานะเป็นลบแล้ว
        self.deleted_by = user # คนที่กดลบคือใคร
        self.deleted_at = timezone.now() # ลบตอนไหน
        self.save(update_fields=["is_deleted", "deleted_by", "deleted_at"]) # เซฟเฉพาะฟิลด์ที่เปลี่ยน (ประหยัดทรัพยากร)

    # ฟังก์ชันสำหรับกู้คืนประกาศที่โดนลบแบบซ่อนกลับมา
    def restore(self, user):
        self.is_deleted = False
        self.deleted_by = None
        self.deleted_at = None
        self.updated_by = user
        self.save(update_fields=["is_deleted", "deleted_by", "deleted_at", "updated_by", "updated_at"])

# -------------------------------------------------------------------------
# โมเดล 3: AnnouncementAttachment (ไฟล์แนบของประกาศ)
# -------------------------------------------------------------------------
class AnnouncementAttachment(models.Model):
    # เชื่อมกับโมเดล CampusAnnouncement หลัก (1 ประกาศ มีไฟล์แนบได้หลายไฟล์)
    # on_delete=models.CASCADE แปลว่าถ้าลบประกาศทิ้ง ไฟล์แนบทั้งหมดของประกาศนั้นจะโดนลบตามทันที
    announcement = models.ForeignKey(CampusAnnouncement, on_delete=models.CASCADE, related_name="attachments")
    
    # ตัวไฟล์จริงๆ ที่ถูกอัปโหลด (เก็บไว้ที่โฟลเดอร์ media/announcements/attachments/)
    file = models.FileField(upload_to="announcements/attachments/")
    file_name = models.CharField(max_length=255)  # ชื่อไฟล์เดิมตอนอัปโหลดมา
    file_type = models.CharField(max_length=100)  # ชนิดไฟล์ (เช่น pdf, jpeg, png)
    file_size = models.PositiveIntegerField()     # ขนาดไฟล์ (เป็น Bytes) เพื่อเอาไปเช็คว่าไฟล์ใหญ่เกินไหม
    
    uploaded_at = models.DateTimeField(auto_now_add=True) # อัปโหลดเมื่อไหร่
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True) # ใครอัปโหลด

    def __str__(self):
        return self.file_name

# -------------------------------------------------------------------------
# โมเดล 4: AnnouncementRead (บันทึกว่าใครอ่านประกาศไหนไปแล้วบ้าง)
# -------------------------------------------------------------------------
# มีประโยชน์เอาไว้ทำระบบ "อ่านแล้ว" หรือสรุปสถิติว่านักศึกษาอ่านประกาศเยอะไหม
class AnnouncementRead(models.Model):
    # โยงไปหาประกาศ
    announcement = models.ForeignKey(CampusAnnouncement, on_delete=models.CASCADE, related_name="reads")
    # โยงไปหาผู้ใช้งาน
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="announcement_reads")
    # อ่านตอนไหน
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # บังคับกฎของฐานข้อมูล (UniqueConstraint) คือ: ผู้ใช้ 1 คน (user) ห้ามถูกบันทึกว่าอ่านประกาศเดิม (announcement) ซ้ำสองครั้ง
        # ช่วยป้องกันข้อมูลขยะเต็มฐานข้อมูลถ้าผู้ใช้กด F5 รัวๆ
        constraints = [
            models.UniqueConstraint(fields=["announcement", "user"], name="unique_announcement_read")
        ]

    def __str__(self):
        return f"{self.user.username} read {self.announcement.title}"

# =========================================================================
# โซนพิเศษ: คำสั่งลบไฟล์ออกจากโฟลเดอร์อัตโนมัติ (Auto Delete Files)
# =========================================================================

# ดักจับเมื่อมีการลบ "ประกาศ" (CampusAnnouncement) ออกจากฐานข้อมูลถาวร
@receiver(post_delete, sender=CampusAnnouncement)
def auto_delete_cover_image_on_delete(sender, instance, **kwargs):
    # ตรวจสอบว่าประกาศนั้นมีรูปหน้าปกไหม
    if instance.cover_image:
        # เช็คว่าไฟล์นี้มีอยู่จริงในโฟลเดอร์หรือเปล่า
        if os.path.isfile(instance.cover_image.path):
            os.remove(instance.cover_image.path) # สั่งลบไฟล์ทิ้งจริงๆ

# ดักจับเมื่อมีการลบ "ไฟล์แนบ" (AnnouncementAttachment)
# ซึ่งคำสั่งนี้จะทำงานอัตโนมัติเมื่อประกาศหลักถูกลบด้วย (เพราะเราใช้ on_delete=CASCADE ไว้)
@receiver(post_delete, sender=AnnouncementAttachment)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    # ตรวจสอบว่ามีไฟล์อยู่จริง
    if instance.file:
        # เช็คในโฟลเดอร์ว่ามีไฟล์นี้ไหม
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path) # สั่งลบไฟล์ทิ้งจริงๆ

