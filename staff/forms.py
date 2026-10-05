from django import forms
from django.contrib.auth import get_user_model
from .models import StaffProfile

# ดึงโมเดล User ปัจจุบันที่ใช้อยู่ (UnifiedUser) มาเก็บไว้ในตัวแปร User
User = get_user_model() 

# =========================================================================
# การปรับแต่งหน้าตาแบบฟอร์มของระบบเจ้าหน้าที่ (Staff Forms)
# =========================================================================

# -------------------------------------------------------------------------
# 1. ฟอร์มสำหรับ "ยื่นคำขอ" สิทธิ์เจ้าหน้าที่ (StaffAccessRequestForm)
# -------------------------------------------------------------------------
# ใช้สำหรับให้ผู้ใช้งานที่ยังเป็นแค่นักศึกษา/คนทั่วไป กรอกข้อมูลเพื่อขออัปเกรดเป็นพนักงาน
class StaffAccessRequestForm(forms.ModelForm):
    class Meta:
        model = StaffProfile # บันทึกลงตาราง StaffProfile
        # ข้อมูล 4 อย่างที่ให้คนขอสิทธิ์เป็นคนกรอก
        fields = ['employee_id', 'department', 'position', 'access_level']
        
        # เปลี่ยนชื่อป้ายกำกับ (Label) จากภาษาอังกฤษให้เป็นภาษาไทย เพื่อความสวยงามตอนแสดงบนเว็บ
        labels = {
            'employee_id': 'รหัสพนักงาน (ถ้ามี)',
            'department': 'แผนก/หน่วยงาน',
            'position': 'ตำแหน่ง',
            'access_level': 'ระดับสิทธิ์ที่ต้องการ',
        }

    # ฟังก์ชันที่ทำงานอัตโนมัติตอนสร้างฟอร์ม เพื่อตกแต่งหน้าตาด้วย CSS (Tailwind)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # วนลูปตกแต่งทุกกล่องข้อความให้สวยงาม
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 mb-4'
            })
            
        # บังคับให้ช่อง "ระดับสิทธิ์ที่ต้องการ" เลือกได้แค่ 2 แบบนี้เท่านั้น (กันคนแอบส่งค่าแปลกๆ มา)
        self.fields['access_level'].choices = [
            ('MANAGER', 'เจ้าหน้าที่ / ผู้จัดการ (MANAGER)'),
            ('ADMIN', 'ผู้ดูแลระบบ (ADMIN)'),
        ]

# -------------------------------------------------------------------------
# 2. ฟอร์มสำหรับ "แอดมิน" ใช้ตอนกด "อนุมัติ" (StaffApproveForm)
# -------------------------------------------------------------------------
# แอดมินสามารถแก้ไข/ตรวจสอบ รหัสพนักงาน ตำแหน่ง และสิทธิ์อีกรอบได้ ก่อนจะกดยืนยันการอนุมัติ
class StaffApproveForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        fields = ['employee_id', 'department', 'position', 'access_level']
        labels = {
            'employee_id': 'รหัสพนักงาน',
            'department': 'แผนก/หน่วยงาน',
            'position': 'ตำแหน่ง',
            'access_level': 'ระดับสิทธิ์',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 mb-2'
            })

# -------------------------------------------------------------------------
# 3. ฟอร์มสำหรับแก้ไขข้อมูลพนักงานที่มีอยู่แล้ว (StaffUpdateForm)
# -------------------------------------------------------------------------
# ฟอร์มนี้พิเศษตรงที่ มันแก้ไขข้อมูล "ข้าม 2 ตารางพร้อมกัน" ได้ (StaffProfile + UnifiedUser)
class StaffUpdateForm(forms.ModelForm):
    # เพิ่มช่องกรอก 3 ช่องนี้เข้ามาเอง (เพราะชื่อ นามสกุล และอีเมล จริงๆ มันอยู่ในตาราง UnifiedUser ไม่ใช่ StaffProfile)
    first_name = forms.CharField(max_length=30, label='ชื่อจริง')
    last_name = forms.CharField(max_length=30, label='นามสกุล')
    email = forms.EmailField(label='อีเมล')

    class Meta:
        model = StaffProfile
        fields = ['employee_id', 'department', 'position', 'access_level', 'status', 'hire_date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # ถ้าเป็นการแก้ไข (มีข้อมูลเดิมส่งมาใน self.instance)
        if self.instance and self.instance.user:
            # ดึงชื่อ นามสกุล อีเมลจากตาราง User มายัดใส่ 3 ช่องที่เราสร้างใหม่ ให้มีค่าเริ่มต้นกรอกรอไว้เลย
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

        # เปลี่ยนช่อง "วันที่เริ่มงาน" ให้เป็นปฏิทิน (DateInput) เพื่อให้คลิกเลือกวันได้ง่ายๆ
        self.fields['hire_date'].widget = forms.DateInput(attrs={'type': 'date'})
        
        # ตกแต่งทุกช่องด้วย Tailwind CSS
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 mb-2'
            })

    # เขียนฟังก์ชันเซฟ (save) ทับของเดิม เพื่อให้มันเซฟข้อมูลลงทั้ง 2 ตาราง!
    def save(self, commit=True):
        # 1. เซฟตาราง StaffProfile ก่อน (แต่ยังไม่บันทึกจริง commit=False)
        staff_profile = super().save(commit=False)
        user = staff_profile.user
        
        # 2. เอาข้อมูลจาก 3 ช่องที่เราสร้างไว้ ไปอัปเดตใส่ตาราง UnifiedUser
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        # 3. ถ้าสั่งเซฟจริง ก็บันทึกทั้ง 2 ตารางพร้อมกันเลย!
        if commit:
            user.save() 
            staff_profile.save() 
            
        return staff_profile
