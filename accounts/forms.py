from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import UnifiedUser

# =========================================================================
# การปรับแต่งหน้าตาแบบฟอร์มของระบบบัญชี (Accounts Forms)
# =========================================================================

# -------------------------------------------------------------------------
# 1. ฟอร์มเข้าสู่ระบบ (LoginForm)
# -------------------------------------------------------------------------
# เราเลือกที่จะสืบทอดมาจาก AuthenticationForm (ฟอร์มมาตรฐานที่ Django ทำไว้ให้)
# เพื่อให้เรายังคงได้ความปลอดภัย (เช่น ตรวจสอบรหัสผ่าน, กันบอทเดารหัส) 
# แต่สิ่งที่เราจะมาแก้ไขคือ "ความสวยงาม (UI)" ในการแสดงผลบนหน้า HTML
class LoginForm(AuthenticationForm):
    # ปรับแต่งช่องกรอก 'username' (ชื่อผู้ใช้)
    username = forms.CharField(
        # widget คือคำสั่งแปลง Python ให้กลายเป็นแท็ก HTML (เช่น <input type="text">)
        # attrs คือการใส่ Attribute เพิ่มเข้าไปในแท็กนั้น (ในที่นี้เราใส่คลาส CSS ของ Tailwind เพื่อให้สวยงาม)
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )
    
    # ปรับแต่งช่องกรอก 'password' (รหัสผ่าน)
    password = forms.CharField(
        # สังเกตว่าเราใช้ PasswordInput เพื่อให้ตอนพิมพ์รหัสผ่าน มันขึ้นเป็นจุดดำๆ (***) ป้องกันคนแอบมอง
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )

# -------------------------------------------------------------------------
# 2. ฟอร์มลงทะเบียนสมาชิกใหม่ (RegisterForm)
# -------------------------------------------------------------------------
# เราสืบทอดมาจาก UserCreationForm (ซึ่งจะจัดการเรื่องการเข้ารหัสผ่านให้เราอัตโนมัติ)
class RegisterForm(UserCreationForm):
    # คลาส Meta เอาไว้บอก Django ว่าฟอร์มนี้อ้างอิงจากโมเดลไหน และอยากให้มีช่องกรอกอะไรบ้าง
    class Meta:
        model = UnifiedUser # อ้างอิงตารางผู้ใช้หลักของเรา
        fields = ('username', 'first_name', 'last_name', 'email') # ข้อมูล 4 อย่างที่ผู้ใช้ต้องกรอก (รหัสผ่านมันจะงอกมาให้เอง 2 ช่อง)
        
    # ฟังก์ชัน __init__ จะทำงานทันทีที่มีการสร้างฟอร์มนี้ขึ้นมา
    def __init__(self, *args, **kwargs):
        # เรียกการตั้งค่าดั้งเดิมของ Django ขึ้นมาก่อน
        super().__init__(*args, **kwargs)
        
        # ปัญหาของ Django คือช่อง username ชอบมีข้อความอธิบายยาวเหยียดติดมาด้วย (help_text) ทำให้หน้าเว็บดูรก
        # เราจึงสั่งให้ล้างข้อความอธิบายทิ้งไป (ทำให้เป็นค่าว่าง)
        self.fields['username'].help_text = '' 
        
        # แทนที่จะเขียน widget ทีละอันแบบ LoginForm 
        # เราใช้ "การวนลูป (for)" เพื่อไล่ใส่คลาส CSS ของ Tailwind ลงไปในช่องกรอกทุกๆ ช่องให้เหมือนกันหมด (ประหยัดเวลาพิมพ์)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 mb-2'
            })