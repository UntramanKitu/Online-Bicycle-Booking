from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .models import StaffProfile
from .forms import StaffUpdateForm, StaffAccessRequestForm, StaffApproveForm

# =========================================================================
# ส่วนจัดการข้อมูลเจ้าหน้าที่ (Staff Views)
# =========================================================================

# ฟังก์ชันด่านตรวจ: เช็คว่าคนที่ล็อกอินอยู่เป็นแอดมิน (ADMIN) หรือไม่
def is_admin(user):
    return user.is_authenticated and getattr(user, 'role', '') == 'ADMIN'

# -------------------------------------------------------------------------
# 1. หน้าแสดงรายชื่อเจ้าหน้าที่ทั้งหมด (staff_list)
# -------------------------------------------------------------------------
# ต้องล็อกอินก่อน (@login_required) และต้องเป็นแอดมินเท่านั้น (@user_passes_test) ถึงจะเห็นหน้านี้ได้
@login_required
@user_passes_test(is_admin)
def staff_list(request):
    # ดึงรายชื่อพนักงานที่มีสิทธิ์อยู่แล้ว (ไม่ใช่ PENDING) เรียงจากใหม่ไปเก่า
    active_staff = StaffProfile.objects.exclude(status='PENDING').order_by('-created_at')
    # ดึงรายชื่อพนักงานที่ "กำลังรอคอยการอนุมัติ" (เพื่อเอามาโชว์ที่ตารางด้านบนให้แอดมินกดอนุมัติ)
    pending_staff = StaffProfile.objects.filter(status='PENDING').order_by('-created_at')
    
    return render(request, 'staff/staff_list.html', {
        'active_staff': active_staff,
        'pending_staff': pending_staff
    })

# -------------------------------------------------------------------------
# 2. หน้าให้คนทั่วไปกรอกฟอร์มขอสิทธิ์เจ้าหน้าที่ (request_access)
# -------------------------------------------------------------------------
@login_required
def request_access(request):
    # เช็คก่อนว่า "เคยขอไปแล้วหรือเปล่า?" ถ้าเคยขอไปแล้ว หรือเป็นเจ้าหน้าที่อยู่แล้ว จะส่งกลับหน้าแรกพร้อมคำเตือน
    if hasattr(request.user, 'staff_profile'):
        messages.info(request, 'คุณได้ส่งคำขอหรือเป็นเจ้าหน้าที่อยู่แล้ว')
        return redirect('core:home')

    if request.method == 'POST':
        # ถ้ายื่นฟอร์มมา
        form = StaffAccessRequestForm(request.POST)
        if form.is_valid():
            # เซฟฟอร์มไว้ก่อน แต่อย่าเพิ่งบันทึกลงฐานข้อมูล (commit=False) เพราะต้องยัดไส้ข้อมูลเพิ่ม
            profile = form.save(commit=False)
            
            # โยงโปรไฟล์นี้ให้เข้ากับ User ปัจจุบันที่กำลังล็อกอินอยู่
            profile.user = request.user
            # บังคับให้สถานะเป็น PENDING (รอการอนุมัติ) เท่านั้น ห้ามเนียนแก้มาเป็น ACTIVE เด็ดขาด
            profile.status = StaffProfile.Status.PENDING 
            profile.save() # บันทึกลงฐานข้อมูลจริงๆ
            
            messages.success(request, 'ส่งคำขอสิทธิ์เจ้าหน้าที่สำเร็จแล้ว กรุณารอการอนุมัติจากผู้ดูแลระบบ')
            return redirect('core:home')
    else:
        # หน้าฟอร์มเปล่าๆ สำหรับเข้ามาครั้งแรก
        form = StaffAccessRequestForm()
        
    return render(request, 'staff/request_access.html', {'form': form, 'title': 'ลงทะเบียนเป็นเจ้าหน้าที่'})

# -------------------------------------------------------------------------
# 3. หน้าสำหรับแอดมินแก้ไขข้อมูลพนักงาน (staff_update)
# -------------------------------------------------------------------------
@login_required
@user_passes_test(is_admin)
def staff_update(request, pk):
    # ดึงข้อมูลพนักงานจากรหัส pk
    staff_profile = get_object_or_404(StaffProfile, pk=pk)
    if request.method == 'POST':
        form = StaffUpdateForm(request.POST, instance=staff_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'แก้ไขข้อมูลเจ้าหน้าที่สำเร็จแล้ว')
            return redirect('staff:staff_list')
    else:
        form = StaffUpdateForm(instance=staff_profile)
    return render(request, 'staff/staff_form.html', {'form': form, 'title': 'แก้ไขข้อมูลเจ้าหน้าที่'})

# -------------------------------------------------------------------------
# 4. หน้าสำหรับแอดมินลบพนักงาน (staff_delete)
# -------------------------------------------------------------------------
@login_required
@user_passes_test(is_admin)
def staff_delete(request, pk):
    staff_profile = get_object_or_404(StaffProfile, pk=pk)
    if request.method == 'POST':
        # เราไม่ลบแค่โปรไฟล์ แต่เราจะลบ "ยูสเซอร์" คนนั้นออกจากระบบไปเลย
        # (เพราะใน models เราตั้ง on_delete=CASCADE ไว้ การลบ User จะทำให้ StaffProfile หายตามไปด้วย)
        user = staff_profile.user
        username = user.username
        user.delete() 
        
        messages.success(request, f'ลบข้อมูลเจ้าหน้าที่ {username} ออกจากระบบสำเร็จแล้ว')
        return redirect('staff:staff_list')
        
    # ถ้ายังไม่กดยืนยัน (GET) ให้โชว์หน้าถามความแน่ใจก่อน
    return render(request, 'staff/staff_confirm_delete.html', {'staff_profile': staff_profile})

# -------------------------------------------------------------------------
# 5. หน้าสำหรับแอดมินกด "อนุมัติ" คำขอสิทธิ์ (staff_approve)
# -------------------------------------------------------------------------
@login_required
@user_passes_test(is_admin)
def staff_approve(request, pk):
    # หาคนที่รอการอนุมัติอยู่ (ต้องมี status='PENDING' เท่านั้น ถึงจะให้กดอนุมัติได้)
    staff_profile = get_object_or_404(StaffProfile, pk=pk, status='PENDING')
    if request.method == 'POST':
        form = StaffApproveForm(request.POST, instance=staff_profile)
        if form.is_valid():
            profile = form.save(commit=False)
            # เปลี่ยนสถานะจาก รออนุมัติ (PENDING) ให้กลายเป็น ใช้งานได้ (ACTIVE)
            profile.status = StaffProfile.Status.ACTIVE
            # ใส่วันที่เริ่มงานเป็น "วันนี้"
            profile.hire_date = timezone.now().date()
            profile.save()
            
            messages.success(request, 'อนุมัติสิทธิ์เจ้าหน้าที่สำเร็จแล้ว')
            return redirect('staff:staff_list')
    else:
        form = StaffApproveForm(instance=staff_profile)
        
    return render(request, 'staff/staff_form.html', {'form': form, 'title': 'อนุมัติสิทธิ์เจ้าหน้าที่'})

# -------------------------------------------------------------------------
# 6. หน้าสำหรับแอดมินกด "ปฏิเสธ" คำขอสิทธิ์ (staff_reject)
# -------------------------------------------------------------------------
@login_required
@user_passes_test(is_admin)
def staff_reject(request, pk):
    staff_profile = get_object_or_404(StaffProfile, pk=pk, status='PENDING')
    if request.method == 'POST':
        # ถ้ากดปฏิเสธ เราจะ "ลบโปรไฟล์" ที่เขาส่งคำขอมาทิ้งไปเลย (แต่บัญชีผู้ใช้เขายังอยู่นะ แค่สิทธิ์ไม่ผ่าน)
        staff_profile.delete()
        messages.success(request, 'ปฏิเสธคำขอสิทธิ์เจ้าหน้าที่เรียบร้อยแล้ว')
        return redirect('staff:staff_list')
        
    return render(request, 'staff/staff_confirm_reject.html', {'staff_profile': staff_profile})
