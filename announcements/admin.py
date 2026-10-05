from django.contrib import admin
from .models import AnnouncementCategory, CampusAnnouncement, AnnouncementAttachment, AnnouncementRead

# =========================================================================
# ระบบหลังบ้านสำหรับประกาศข่าวสาร (Announcements Admin)
# =========================================================================

# 1. การจัดการหมวดหมู่ของประกาศ (AnnouncementCategory)
@admin.register(AnnouncementCategory)
class AnnouncementCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at') # คอลัมน์ที่โชว์หน้ารวม
    list_filter = ('is_active',) # กรองดูเฉพาะหมวดหมู่ที่ยังเปิดใช้งานอยู่ได้
    search_fields = ('name',)    # ช่องค้นหาชื่อหมวดหมู่

# 2. คลาสพิเศษ (Inline) สำหรับ "ไฟล์แนบ"
# TabularInline คือการทำให้เราสามารถ "เพิ่มไฟล์แนบ" ได้พร้อมๆ กับตอนสร้าง/แก้ไขประกาศในหน้าจอเดียวกัน
class AnnouncementAttachmentInline(admin.TabularInline):
    model = AnnouncementAttachment
    extra = 1 # มีบรรทัดว่างสำหรับให้เพิ่มไฟล์ใหม่เผื่อไว้ 1 บรรทัดเสมอ
    # ฟิลด์พวกนี้ห้ามแก้ เพราะเป็นระบบดึงมาอัตโนมัติ (เช่น วันเวลาที่อัปโหลด)
    readonly_fields = ('uploaded_at', 'uploaded_by', 'file_size', 'file_type', 'file_name')

# 3. การจัดการตัวประกาศ (CampusAnnouncement)
@admin.register(CampusAnnouncement)
class CampusAnnouncementAdmin(admin.ModelAdmin):
    # คอลัมน์ที่โชว์เยอะหน่อย เพื่อให้แอดมินดูกวาดสายตาทีเดียวรู้เรื่อง
    list_display = ('title', 'category', 'status', 'priority', 'target_audience', 'publish_at', 'is_pinned', 'is_deleted')
    
    # ตัวกรองข้อมูลเพียบ! แยกตามสถานะ ระดับความสำคัญ ใครเห็นได้บ้าง ปักหมุดอยู่ไหม
    list_filter = ('status', 'priority', 'target_audience', 'is_pinned', 'is_deleted', 'category')
    
    # ค้นหาข้อความได้ทั้งจากชื่อหัวข้อและเนื้อหาข้างใน
    search_fields = ('title', 'content')
    
    # ดึงคลาส Inline ไฟล์แนบที่เราสร้างไว้ข้างบน มายัดรวมไว้ในหน้านี้ด้วย
    inlines = [AnnouncementAttachmentInline]
    
    # สร้างเมนูลัดสำหรับกรองตาม "วันที่" ด้านบนสุดของจอ
    date_hierarchy = 'publish_at'
    
    # ฟิลด์ที่ห้ามแก้ไข ป้องกันแอดมินมือบอนไปแก้เวลาหรือชื่อคนสร้าง
    readonly_fields = ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by', 'deleted_by')

# 4. การจัดการประวัติคนอ่านประกาศ (AnnouncementRead)
@admin.register(AnnouncementRead)
class AnnouncementReadAdmin(admin.ModelAdmin):
    list_display = ('announcement', 'user', 'read_at')
    list_filter = ('read_at',)
    # ค้นหาข้ามตารางได้! เช่น หาชื่อหัวข้อที่อยู่ในตาราง announcement (ใช้เครื่องหมาย __ สองตัว)
    search_fields = ('announcement__title', 'user__username', 'user__email')
