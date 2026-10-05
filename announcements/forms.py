from django import forms
from .models import CampusAnnouncement, AnnouncementCategory

# =========================================================================
# คลาสพิเศษเพื่อรองรับการอัปโหลดหลายไฟล์พร้อมกัน
# =========================================================================

# แปลงช่องเลือกไฟล์ธรรมดา ให้สามารถลากคลุมเลือกหลายๆ ไฟล์ได้ (Multiple)
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

# จัดการข้อมูลที่รับมา หากอัปโหลดมาหลายไฟล์ ให้แกะออกมาเป็นลีสต์ (List) 
class MultipleFileField(forms.FileField):
    widget = MultipleFileInput
    
    def clean(self, data, initial=None):
        if not data:
            return []
        if not isinstance(data, (list, tuple)):
            data = [data]
        cleaned_data = []
        for d in data:
            cleaned = super().clean(d, initial)
            if cleaned:
                cleaned_data.append(cleaned)
        return cleaned_data

# =========================================================================
# การปรับแต่งหน้าตาแบบฟอร์มของระบบประกาศข่าวสาร (Announcements Forms)
# =========================================================================

# -------------------------------------------------------------------------
# 1. ฟอร์มรับข้อมูลสำหรับหน้า "สร้าง/แก้ไขประกาศ"
# -------------------------------------------------------------------------
class CampusAnnouncementForm(forms.ModelForm):
    
    # ดึงคลาสที่เราทำไว้ข้างบน มาใช้เป็นช่องอัปโหลด "ไฟล์แนบ"
    attachments = MultipleFileField(
        widget=MultipleFileInput(attrs={'multiple': True, 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring focus:border-blue-300'}),
        required=False, # ไม่บังคับแนบไฟล์
        label="ไฟล์แนบ (สามารถเลือกได้หลายไฟล์)"
    )

    class Meta:
        model = CampusAnnouncement
        
        # ระบุว่าแอดมินจะต้องกรอกข้อมูลฟิลด์อะไรบ้างเวลาสร้างประกาศ
        fields = [
            'title', 'content', 'category', 'priority', 'target_audience',
            'cover_image', 'publish_at', 'expire_at', 'is_pinned'
        ]
        
        # ตกแต่งหน้าตาฟอร์มแต่ละช่อง ด้วย Tailwind CSS (สังเกตพวก w-full, px-3, border, rounded-lg)
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring focus:border-blue-300'}),
            'content': forms.Textarea(attrs={'rows': 5, 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring focus:border-blue-300'}),
            'category': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring focus:border-blue-300'}),
            'priority': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring focus:border-blue-300'}),
            'target_audience': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring focus:border-blue-300'}),
            
            # ช่องเลือกรูปหน้าปก
            'cover_image': forms.ClearableFileInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring focus:border-blue-300'}),
            
            # ช่องเลือกเวลา (เปลี่ยนชนิด input เป็น datetime-local เพื่อให้มีปฏิทินและนาฬิกาเด้งขึ้นมาให้เลือก)
            'publish_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring focus:border-blue-300'}),
            'expire_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring focus:border-blue-300'}),
            
            # ช่องติ๊กถูก ปักหมุด
            'is_pinned': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'}),
        }
        
        # เปลี่ยนป้ายกำกับให้เป็นภาษาไทยเพื่อความเข้าใจง่าย
        labels = {
            'title': 'หัวข้อประกาศ',
            'content': 'เนื้อหา',
            'category': 'หมวดหมู่',
            'priority': 'ระดับความสำคัญ',
            'target_audience': 'กลุ่มเป้าหมาย',
            'cover_image': 'รูปภาพหน้าปก',
            'publish_at': 'เวลาที่ต้องการเผยแพร่ (เว้นว่างไว้เพื่อเผยแพร่ทันที)',
            'expire_at': 'เวลาสิ้นสุดประกาศ (ไม่บังคับ)',
            'is_pinned': 'ปักหมุดประกาศนี้'
        }

    # ---------------------------------------------------------------------
    # ฟังก์ชันตรวจสอบความถูกต้องของเวลา (Validation)
    # ---------------------------------------------------------------------
    # จะถูกเรียกอัตโนมัติเมื่อกด Submit เพื่อเช็คความสมเหตุสมผลของข้อมูล
    def clean(self):
        # ดึงข้อมูลทั้งหมดที่ผู้ใช้กรอกมา
        cleaned_data = super().clean()
        publish_at = cleaned_data.get('publish_at')
        expire_at = cleaned_data.get('expire_at')

        # เช็คว่า "ถ้ากรอกเวลาสิ้นสุดมา เวลาสิ้นสุดห้ามมาก่อนเวลาเผยแพร่" ไม่งั้นเดี๋ยวประกาศจะหมดอายุก่อนได้ลงเว็บ!
        if expire_at and publish_at:
            if expire_at <= publish_at:
                # สั่งโยนข้อความแจ้งเตือน Error สีแดงไปติดไว้ใต้ช่อง 'expire_at'
                self.add_error('expire_at', 'เวลาสิ้นสุดประกาศต้องอยู่หลังเวลาเริ่มเผยแพร่')
                
        return cleaned_data

# -------------------------------------------------------------------------
# 2. ฟอร์มสำหรับ "สร้างหมวดหมู่ประกาศใหม่" (เฉพาะแอดมิน)
# -------------------------------------------------------------------------
class AnnouncementCategoryForm(forms.ModelForm):
    class Meta:
        model = AnnouncementCategory
        fields = ['name', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring focus:border-blue-300'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'}),
        }
        labels = {
            'name': 'ชื่อหมวดหมู่',
            'is_active': 'เปิดใช้งานหมวดหมู่นี้'
        }
