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
    # ปรับแต่งช่องกรอก 'username' (ชื่อผู้ใช้ที่ใช้เข้าสู่ระบบ)
    username = forms.CharField(
        # widget คือคำสั่งแปลง Python ให้กลายเป็นแท็ก HTML (เช่น <input type="text">)
        # attrs คือการใส่ Attribute เพิ่มเข้าไปในแท็กนั้น (ในที่นี้เราใส่คลาส CSS ของ Tailwind เพื่อให้สวยงาม)
        widget=forms.TextInput(attrs={
            'class': 'bs-input',
            'placeholder': 'ชื่อผู้ใช้',
            'autofocus': True,
        })
    )

    # ปรับแต่งช่องกรอก 'password' (รหัสผ่าน)
    password = forms.CharField(
        # สังเกตว่าเราใช้ PasswordInput เพื่อให้ตอนพิมพ์รหัสผ่าน มันขึ้นเป็นจุดดำๆ (***) ป้องกันคนแอบมอง
        widget=forms.PasswordInput(attrs={
            'class': 'bs-input'
        })
    )

    def confirm_login_allowed(self, user):
        # อนุญาตให้ล็อกอินตามปกติ (เรียกของเดิมก่อน)
        super().confirm_login_allowed(user)

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
        
        # เนื่องจากเราล็อกอินด้วย "อีเมล" จึงบังคับให้กรอกอีเมล (ห้ามว่าง) และต้องไม่ซ้ำกับผู้อื่น
        self.fields['email'].required = True
        
        # แทนที่จะเขียน widget ทีละอันแบบ LoginForm 
        # เราใช้ "การวนลูป (for)" เพื่อไล่ใส่คลาส CSS ของ Tailwind ลงไปในช่องกรอกทุกๆ ช่องให้เหมือนกันหมด (ประหยัดเวลาพิมพ์)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'bs-input mb-2'
            })
    
    # ตรวจสอบอีเมลซ้ำ (เพราะใช้เป็นตัวล็อกอิน ห้ามให้สองบัญชีใช้อีเมลเดียวกัน)
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if UnifiedUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('อีเมลนี้ถูกใช้งานแล้ว กรุณาใช้อีเมลอื่น')
        return email
