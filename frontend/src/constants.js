export const BOOKING_TYPES = {
  advance_reservation: { label: 'จองล่วงหน้า', cls: 'badge-violet' },
  walk_in: { label: 'Walk-in', cls: 'badge-sage' },
}

export const BOOKING_STATUSES = {
  pending: { label: 'รออนุมัติ', cls: 'badge-warn' },
  confirmed: { label: 'ยืนยันแล้ว', cls: 'badge-info' },
  in_progress: { label: 'กำลังยืม', cls: 'badge-active' },
  completed: { label: 'เสร็จสิ้น', cls: 'badge-success' },
  cancelled: { label: 'ยกเลิก', cls: 'badge-danger' },
  no_show: { label: 'ไม่มาใช้บริการ', cls: 'badge-muted' },
}

export const GROUP_STATUSES = {
  open: { label: 'เปิดรับสมาชิก', cls: 'badge-success' },
  full: { label: 'สมาชิกเต็ม', cls: 'badge-warn' },
  cancelled: { label: 'ยกเลิก', cls: 'badge-danger' },
  completed: { label: 'เสร็จสิ้น', cls: 'badge-muted' },
}

export const TICKET_CATEGORIES = {
  bicycle_issue: { label: 'ปัญหาจักรยาน', cls: 'badge-danger' },
  account_issue: { label: 'ปัญหาบัญชี', cls: 'badge-info' },
  booking_issue: { label: 'ปัญหาการจอง', cls: 'badge-warn' },
  other: { label: 'อื่น ๆ', cls: 'badge-muted' },
}

export const TICKET_PRIORITIES = {
  low: { label: 'ต่ำ', cls: 'badge-muted' },
  normal: { label: 'ปกติ', cls: 'badge-info' },
  high: { label: 'สูง', cls: 'badge-warn' },
  urgent: { label: 'เร่งด่วน', cls: 'badge-danger' },
}

export const TICKET_STATUSES = {
  open: { label: 'เปิด', cls: 'badge-danger' },
  in_progress: { label: 'กำลังดำเนินการ', cls: 'badge-active' },
  resolved: { label: 'แก้ไขแล้ว', cls: 'badge-success' },
  closed: { label: 'ปิดเคส', cls: 'badge-muted' },
  reopened: { label: 'เปิดใหม่', cls: 'badge-warn' },
}