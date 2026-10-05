from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from .models import CampusAnnouncement, AnnouncementCategory, AnnouncementAttachment, AnnouncementRead
from .forms import CampusAnnouncementForm, AnnouncementCategoryForm
from .permissions import staff_required, admin_required, is_announcement_admin
from audit.models import SystemAuditLog
from django.core.exceptions import PermissionDenied

# =========================================================================
# โซน 1: PUBLIC VIEWS (หน้าเว็บสำหรับคนทั่วไป นักศึกษา หรือผู้ใช้งานทั่วไป)
# =========================================================================

# ฟังก์ชันแสดงรายการประกาศทั้งหมด (หน้าแรกของระบบประกาศ)
def announcement_list(request):
    # 1. ดึงคำค้นหา (q) และ หมวดหมู่ (category) จาก URL (เช่น ?q=สอบ&category=2)
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')

    # 2. ค้นหาประกาศจากฐานข้อมูล โดยมีเงื่อนไขพื้นฐานคือ:
    # - ต้องถูกเผยแพร่แล้ว (PUBLISHED)
    # - ต้องยังไม่ถูกลบทิ้ง (is_deleted=False)
    # - ต้องยังไม่หมดอายุ (exclude expire_at ที่น้อยกว่าเวลาปัจจุบัน)
    announcements = CampusAnnouncement.objects.filter(
        status=CampusAnnouncement.Status.PUBLISHED,
        is_deleted=False
    ).exclude(
        expire_at__lt=timezone.now()
    )

    # 3. คัดกรองการมองเห็นตามสิทธิ์ (Role) ของผู้ใช้งาน
    if request.user.is_authenticated:
        # ดึงสิทธิ์ของผู้ใช้ ถ้าไม่มีให้ถือว่าเป็น BASIC
        role = getattr(request.user, 'role', 'BASIC')
        if role == 'ADMIN':
            # แอดมินเห็นประกาศได้ทุกประเภท
            target_audience = ['ALL', 'ADMIN', 'STAFF', 'STUDENT']
        elif role == 'MANAGER':
            # เจ้าหน้าที่เห็นประกาศของเจ้าหน้าที่และประกาศทั่วไปได้
            target_audience = ['ALL', 'STAFF']
        else:
            # ผู้ใช้ทั่วไป/นักศึกษา เห็นได้เฉพาะของนักศึกษาและทั่วไป
            target_audience = ['ALL', 'STUDENT']
            
        # กรองประกาศเฉพาะที่กลุ่มเป้าหมาย (Target Audience) ตรงกับรายการด้านบน
        announcements = announcements.filter(target_audience__in=target_audience)
    else:
        # ถ้ายังไม่ได้ล็อกอิน ให้เห็นเฉพาะประกาศที่เป็นสาธารณะ (ALL) เท่านั้น
        announcements = announcements.filter(target_audience='ALL')

    # 4. การค้นหาเพิ่มเติม (ถ้ายูสเซอร์พิมพ์คำค้นหา หรือกดเลือกหมวดหมู่)
    if query:
        # ค้นหาคำที่พิมพ์ว่าตรงกับ "หัวข้อ" หรือ "เนื้อหา" ไหม (Q object ช่วยให้ค้นหาแบบ OR ได้)
        announcements = announcements.filter(Q(title__icontains=query) | Q(content__icontains=query))
    if category_id:
        # กรองเฉพาะหมวดหมู่ที่เลือก
        announcements = announcements.filter(category_id=category_id)

    # 5. การแบ่งหน้า (Pagination)
    # นำประกาศทั้งหมดมาแบ่งหน้า หน้าละ 10 โพสต์
    paginator = Paginator(announcements, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 6. ดึงหมวดหมู่ทั้งหมดที่ยังเปิดใช้งานอยู่ เพื่อเอาไปทำปุ่ม Filter ด้านข้าง
    categories = AnnouncementCategory.objects.filter(is_active=True)

    # 7. ส่งข้อมูลทั้งหมดกลับไปวาดเป็นหน้าเว็บ (HTML)
    return render(request, 'announcements/list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'selected_category': category_id
    })

# ฟังก์ชันสำหรับอ่านรายละเอียดประกาศ (เมื่อผู้ใช้คลิกเข้าไปดูข้างในโพสต์)
def announcement_detail(request, pk):
    # 1. ค้นหาประกาศจาก Primary Key (pk) ถ้าระบุเลขผิด หรือประกาศถูกลบไปแล้ว ให้เด้งไปหน้า 404
    announcement = get_object_or_404(CampusAnnouncement, pk=pk, is_deleted=False)
    
    # 2. ตรวจสอบสิทธิ์การเข้าถึง (กรณีประกาศยังไม่เผยแพร่ เช่น เป็นฉบับร่าง หรือตั้งเวลาไว้)
    # ถ้าไม่ใช่แอดมินระบบประกาศ และประกาศยังไม่ Published
    if not is_announcement_admin(request.user) and announcement.status != CampusAnnouncement.Status.PUBLISHED:
        # คนที่เข้ามาดูต้องเป็น "คนเขียนประกาศนี้เอง" เท่านั้น ถึงจะดูฉบับร่างของตัวเองได้
        if request.user != announcement.created_by:
            raise PermissionDenied # ถ้าไม่ใช่คนเขียน เด้งหน้า Error ไม่มีสิทธิ์ทันที

    # 3. ระบบบันทึกยอดคนอ่าน (Tracking)
    # ถ้าล็อกอินอยู่ ให้บันทึกว่าคนๆ นี้อ่านประกาศนี้แล้ว (ถ้าเคยอ่านแล้ว get_or_create จะไม่สร้างข้อมูลซ้ำ)
    if request.user.is_authenticated:
        AnnouncementRead.objects.get_or_create(announcement=announcement, user=request.user)

    # 4. ส่งข้อมูลประกาศไปวาดหน้าเว็บ
    return render(request, 'announcements/detail.html', {'announcement': announcement})

# =========================================================================
# โซน 2: MANAGEMENT VIEWS (ระบบหลังบ้าน สำหรับเจ้าหน้าที่และแอดมินเท่านั้น)
# =========================================================================

# ฟังก์ชันแสดงรายการประกาศทั้งหมด (มุมมองของคนจัดการระบบ)
@staff_required # ต้องมีสิทธิ์ STAFF ขึ้นไปถึงเข้าหน้านี้ได้
def manage_list(request):
    # ดึงประกาศทั้งหมดที่ยังไม่ถูกลบ (ไม่สนว่าร่าง หรือเผยแพร่แล้ว)
    announcements = CampusAnnouncement.objects.filter(is_deleted=False)
    
    # ถ้าไม่ใช่ระดับแอดมินสูงสุด (เป็นแค่เจ้าหน้าที่ทั่วไป)
    if not is_announcement_admin(request.user):
        # บังคับให้เห็นเฉพาะประกาศ "ที่ตัวเองเป็นคนเขียนเท่านั้น"
        announcements = announcements.filter(created_by=request.user)

    # แบ่งหน้าแสดงผล หน้าละ 20 รายการ
    paginator = Paginator(announcements, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'announcements/manage_list.html', {'page_obj': page_obj})

# ฟังก์ชันสำหรับ "สร้าง" ประกาศใหม่ (เฉพาะเจ้าหน้าที่)
@staff_required
def manage_create(request):
    # ถ้ายูสเซอร์กรอกข้อมูลเสร็จแล้วกด Submit (POST)
    if request.method == 'POST':
        # รับข้อมูลจากฟอร์ม ทั้งข้อความ (POST) และ ไฟล์แนบ (FILES)
        form = CampusAnnouncementForm(request.POST, request.FILES)
        if form.is_valid(): # ถ้าข้อมูลถูกต้องตามกฎ (เช่น กรอกครบทุกช่อง)
            
            # 1. สร้างประกาศ แต่ยังไม่เซฟลงฐานข้อมูล (commit=False) เพราะต้องเติมข้อมูลเพิ่ม
            announcement = form.save(commit=False)
            announcement.created_by = request.user # ระบุว่าใครเป็นคนสร้าง
            
            # 2. ตรวจสอบว่ายูสเซอร์กดปุ่มอะไรมา? (ปุ่ม Draft, Publish, หรือ Schedule)
            action = request.POST.get('action', 'DRAFT')
            if action == 'PUBLISH':
                announcement.status = CampusAnnouncement.Status.PUBLISHED
                # ถ้าลืมใส่วันที่เผยแพร่ ให้ใช้วันที่ปัจจุบันเลย
                if not announcement.publish_at:
                    announcement.publish_at = timezone.now()
            elif action == 'SCHEDULE':
                announcement.status = CampusAnnouncement.Status.SCHEDULED
            
            # 3. บันทึกประกาศลงฐานข้อมูลจริงๆ แล้ว
            announcement.save()
            
            # 4. วนลูปบันทึก "ไฟล์แนบ" ทั้งหมดที่ถูกอัปโหลดเข้ามา
            # (request.FILES.getlist จะดึงไฟล์ทั้งหมดออกมาเป็นลิสต์)
            for f in request.FILES.getlist('attachments'):
                AnnouncementAttachment.objects.create(
                    announcement=announcement, # ผูกกับประกาศที่เพิ่งสร้างเมื่อกี้
                    file=f,
                    file_name=f.name,
                    file_size=f.size,
                    file_type=f.content_type,
                    uploaded_by=request.user
                )

            # 5. บันทึกประวัติ (Audit Log) ว่ามีการสร้างประกาศใหม่ เพื่อความปลอดภัยของระบบ
            SystemAuditLog.log_action(
                user=request.user,
                action_type="CREATE_ANNOUNCEMENT",
                entity=announcement,
                request=request
            )

            # 6. แจ้งเตือนสีเขียวว่าสร้างสำเร็จ และเด้งกลับไปหน้าจัดการ
            messages.success(request, 'สร้างประกาศสำเร็จ')
            return redirect('announcements:manage_list')
    else:
        # ถ้าเพิ่งเปิดหน้านี้ครั้งแรก ให้แสดงฟอร์มเปล่าๆ
        form = CampusAnnouncementForm()

    return render(request, 'announcements/manage_form.html', {'form': form, 'title': 'สร้างประกาศใหม่'})

# ฟังก์ชันสำหรับ "แก้ไข" ประกาศเดิม (เฉพาะเจ้าหน้าที่)
@staff_required
def manage_update(request, pk):
    # 1. ค้นหาประกาศที่ต้องการแก้ไข
    announcement = get_object_or_404(CampusAnnouncement, pk=pk, is_deleted=False)
    
    # 2. เช็คสิทธิ์: ถ้าไม่ใช่แอดมิน และไม่ได้เป็นคนเขียนประกาศนี้ จะไม่อนุญาตให้แก้
    if not is_announcement_admin(request.user) and announcement.created_by != request.user:
        raise PermissionDenied

    # 3. เก็บข้อมูลเดิมไว้เปรียบเทียบตอนบันทึกประวัติ (Audit Log)
    old_values = {'title': announcement.title, 'status': announcement.status}

    # 4. ถ้ายูสเซอร์กด Submit 
    if request.method == 'POST':
        # ส่ง instance=announcement เพื่อบอกว่าเราจะ "แก้ไข" ตัวเดิมนะ ไม่ได้สร้างใหม่
        form = CampusAnnouncementForm(request.POST, request.FILES, instance=announcement)
        if form.is_valid():
            updated_announcement = form.save(commit=False)
            updated_announcement.updated_by = request.user # บันทึกว่าใครเป็นคนแก้อัปเดตล่าสุด
            
            # ตรวจสอบปุ่มที่กดมาเหมือนตอนสร้าง
            action = request.POST.get('action')
            if action == 'PUBLISH':
                updated_announcement.status = CampusAnnouncement.Status.PUBLISHED
                if not updated_announcement.publish_at:
                    updated_announcement.publish_at = timezone.now()
            elif action == 'SCHEDULE':
                updated_announcement.status = CampusAnnouncement.Status.SCHEDULED
            elif action == 'ARCHIVE':
                updated_announcement.status = CampusAnnouncement.Status.ARCHIVED # ปุ่มเก็บเข้ากรุ

            updated_announcement.save()

            # บันทึกไฟล์แนบอันใหม่ที่เพิ่งอัปโหลดเพิ่ม
            for f in request.FILES.getlist('attachments'):
                AnnouncementAttachment.objects.create(
                    announcement=updated_announcement,
                    file=f,
                    file_name=f.name,
                    file_size=f.size,
                    file_type=f.content_type,
                    uploaded_by=request.user
                )

            # บันทึกประวัติ (Audit Log) พร้อมแนบข้อมูลเก่าและใหม่ไปเปรียบเทียบ
            SystemAuditLog.log_action(
                user=request.user,
                action_type="UPDATE_ANNOUNCEMENT",
                entity=updated_announcement,
                old_values=old_values,
                new_values={'title': updated_announcement.title, 'status': updated_announcement.status},
                request=request
            )

            messages.success(request, 'อัปเดตประกาศสำเร็จ')
            return redirect('announcements:manage_list')
    else:
        # แสดงฟอร์มที่มีข้อมูลเก่ากรอกรอไว้อยู่แล้ว
        form = CampusAnnouncementForm(instance=announcement)

    return render(request, 'announcements/manage_form.html', {
        'form': form, 
        'title': 'แก้ไขประกาศ',
        'announcement': announcement
    })

# ฟังก์ชันสำหรับ "ลบ" ประกาศ (การลบทิ้งถาวร - Hard Delete)
@staff_required
def manage_delete(request, pk):
    # ค้นหาประกาศที่ไม่ถูกลบแบบซ่อนอยู่ 
    announcement = get_object_or_404(CampusAnnouncement, pk=pk, is_deleted=False)
    
    # เช็คสิทธิ์ ลบได้เฉพาะประกาศของตัวเอง (ยกเว้นแอดมินลบของใครก็ได้)
    if not is_announcement_admin(request.user) and announcement.created_by != request.user:
        raise PermissionDenied

    if request.method == 'POST':
        # บันทึกประวัติก่อนลบ เพราะถ้าลบไปแล้วเดี๋ยวจะอ้างอิง entity ไม่ได้
        SystemAuditLog.log_action(
            user=request.user,
            action_type="DELETE_ANNOUNCEMENT",
            entity=announcement,
            request=request
        )
        
        # ลบทิ้งถาวรออกจากฐานข้อมูล ซึ่งจะไปกระตุ้น Signal ใน models ให้ตามลบไฟล์ทิ้งด้วย
        announcement.delete()
        
        messages.success(request, 'ลบประกาศและไฟล์แนบที่เกี่ยวข้องออกจากระบบถาวรสำเร็จแล้ว')
        return redirect('announcements:manage_list')

    # ถ้ายังไม่กดยืนยัน (GET) จะแสดงหน้าถามให้แน่ใจก่อนลบ
    return render(request, 'announcements/manage_confirm_delete.html', {'announcement': announcement})


# =========================================================================
# โซน 3: CATEGORY VIEWS (ระบบจัดการหมวดหมู่ เฉพาะ ADMIN เท่านั้น)
# =========================================================================

# ฟังก์ชันแสดงรายชื่อหมวดหมู่ทั้งหมด (เช่น ทุนการศึกษา, กิจกรรม)
@admin_required # ล็อกให้เฉพาะแอดมินเข้าได้
def category_list(request):
    categories = AnnouncementCategory.objects.all()
    return render(request, 'announcements/category_list.html', {'categories': categories})

# ฟังก์ชันสร้างหมวดหมู่ใหม่
@admin_required
def category_create(request):
    if request.method == 'POST':
        form = AnnouncementCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            SystemAuditLog.log_action(user=request.user, action_type="CREATE_CATEGORY", entity=category, request=request)
            messages.success(request, 'สร้างหมวดหมู่สำเร็จ')
            return redirect('announcements:category_list')
    else:
        form = AnnouncementCategoryForm()
    return render(request, 'announcements/category_form.html', {'form': form, 'title': 'สร้างหมวดหมู่ใหม่'})
