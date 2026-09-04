# Database Schema — ระบบจองยืมจักรยานออนไลน์ (Online Bicycle Rental Reservation System)

## 🗄️ ER Diagram

```mermaid
erDiagram
    UNIFIED_USER {
        int id PK
        string username
        string password_hash
        string email
        string first_name
        string last_name
        string student_id
        string faculty
        string department
        string phone
        string role
        string status
        datetime created_at
        datetime updated_at
    }

    BICYCLE {
        int id PK
        string bike_code
        string brand
        string model
        string color
        string frame_number
        string status
        string current_location
        string qr_code
        date purchase_date
        decimal purchase_price
        int total_rides
        datetime created_at
        datetime updated_at
    }

    MAINTENANCE {
        int id PK
        int bicycle_id FK
        int reported_by FK
        int assigned_to FK
        string type
        string description
        string status
        string parts_replaced
        decimal cost
        date start_date
        date end_date
        datetime created_at
        datetime updated_at
    }

    STAFF_OFFICER {
        int id PK
        int user_id FK
        string employee_id
        string position
        string access_level
        string department
        date hire_date
        string status
        datetime created_at
        datetime updated_at
    }

    CAMPUS_ANNOUNCEMENT {
        int id PK
        int created_by FK
        string title
        string content
        string priority
        string status
        datetime publish_date
        datetime expire_date
        int view_count
        datetime created_at
        datetime updated_at
    }

    SYSTEM_AUDIT_LOG {
        int id PK
        int user_id FK
        string action_type
        string entity_type
        int entity_id
        string old_values
        string new_values
        string ip_address
        string user_agent
        datetime created_at
    }

    BICYCLE_COMPARISON {
        int id PK
        int user_id FK
        int bicycle_id FK
        int comparison_session_id
        datetime added_at
        datetime removed_at
    }

    NOTIFICATION {
        int id PK
        int user_id FK
        string title
        string message
        string type
        string channel
        string status
        int reference_id
        string reference_type
        datetime sent_at
        datetime read_at
        datetime created_at
    }

    FEEDBACK_RATING {
        int id PK
        int user_id FK
        int bicycle_id FK
        int booking_id FK
        int rating
        string comment
        string status
        datetime created_at
        datetime updated_at
    }

    RETURN_RECORD {
        int id PK
        int booking_id FK
        int bicycle_id FK
        int user_id FK
        int return_station_id
        datetime borrowed_at
        datetime returned_at
        int odometer_reading
        string status
        string notes
        datetime created_at
    }

    DAMAGE_EVIDENCE {
        int id PK
        int return_record_id FK
        int bicycle_id FK
        string image_url
        string image_caption
        string damage_type
        string severity
        decimal estimated_cost
        datetime reported_at
        datetime created_at
    }

    PENALTY_STRIKE {
        int id PK
        int user_id FK
        int return_record_id FK
        int given_by FK
        int strike_points
        string reason
        string status
        date appeal_deadline
        string appeal_reason
        datetime created_at
        datetime updated_at
    }

    RESERVATION_BOOKING {
        int id PK
        int user_id FK
        int bicycle_id FK
        string booking_type
        datetime start_time
        datetime end_time
        string status
        string pickup_location
        string return_location
        datetime checked_out_at
        datetime checked_in_at
        datetime created_at
        datetime updated_at
    }

    USAGE_HISTORY_LOG {
        int id PK
        int user_id FK
        int bicycle_id FK
        int booking_id FK
        datetime start_time
        datetime end_time
        int duration_minutes
        decimal distance_km
        string starting_station
        string ending_station
        string status
        datetime created_at
    }

    SUPPORT_TICKET {
        int id PK
        int user_id FK
        int assigned_to FK
        string subject
        string description
        string category
        string priority
        string status
        string resolution_notes
        datetime resolved_at
        datetime created_at
        datetime updated_at
    }

    %% ==================== RELATIONSHIPS ====================

    UNIFIED_USER ||--o| STAFF_OFFICER : "is"
    UNIFIED_USER ||--o{ BICYCLE_COMPARISON : "compares"
    UNIFIED_USER ||--o{ NOTIFICATION : "receives"
    UNIFIED_USER ||--o{ FEEDBACK_RATING : "writes"
    UNIFIED_USER ||--o{ RETURN_RECORD : "returns bike"
    UNIFIED_USER ||--o{ PENALTY_STRIKE : "receives"
    UNIFIED_USER ||--o{ RESERVATION_BOOKING : "makes"
    UNIFIED_USER ||--o{ USAGE_HISTORY_LOG : "has"
    UNIFIED_USER ||--o{ SUPPORT_TICKET : "creates"
    UNIFIED_USER ||--o{ CAMPUS_ANNOUNCEMENT : "creates"
    UNIFIED_USER ||--o{ SYSTEM_AUDIT_LOG : "triggers"
    UNIFIED_USER ||--o{ MAINTENANCE : "reports"

    BICYCLE ||--o{ MAINTENANCE : "undergoes"
    BICYCLE ||--o{ BICYCLE_COMPARISON : "compared in"
    BICYCLE ||--o{ FEEDBACK_RATING : "rated in"
    BICYCLE ||--o{ RETURN_RECORD : "returned as"
    BICYCLE ||--o{ DAMAGE_EVIDENCE : "has damage"
    BICYCLE ||--o{ RESERVATION_BOOKING : "reserved for"
    BICYCLE ||--o{ USAGE_HISTORY_LOG : "tracked in"

    STAFF_OFFICER ||--o{ MAINTENANCE : "assigned to fix"
    STAFF_OFFICER ||--o{ PENALTY_STRIKE : "issues"
    STAFF_OFFICER ||--o{ SUPPORT_TICKET : "handles"

    RESERVATION_BOOKING ||--o| RETURN_RECORD : "results in"
    RETURN_RECORD ||--o{ DAMAGE_EVIDENCE : "may have"
    RETURN_RECORD ||--o{ PENALTY_STRIKE : "may incur"
    RESERVATION_BOOKING ||--o{ FEEDBACK_RATING : "reviewed in"
    RESERVATION_BOOKING ||--o| USAGE_HISTORY_LOG : "logged as"
```

---

## 📋 คำอธิบาย Database Schema

### 🎯 ภาพรวม

Database Schema นี้แปลงมาจาก Class Diagram ของระบบจองยืมจักรยานออนไลน์ ประกอบด้วย **15 ตาราง** โดย methods ทั้งหมดในคลาสจะถูกนำไปทำเป็น business logic ในระดับ Application Layer (Django / FastAPI) ไม่ได้เก็บไว้ใน Database

### 🔑 หลักการแปลง Class → Table

| Class concept | Database concept |
|---|---|
| Attribute (field) | Column |
| `+int id` | `id` (Primary Key, auto-increment) |
| Foreign key แบบ `xxx_id` | Column ชนิด `int` พร้อม `FK` constraint |
| Method (`+method()`) | ไม่ถูกแปลงเป็น column — ใช้เป็น business logic ที่ layer แอปพลิเคชัน |
| `string` ที่เป็นชุดค่าคงที่ (เช่น `role`, `status`) | แนะนำให้ทำเป็น `ENUM` หรือ lookup table แทน `VARCHAR` เปิดกว้าง |

### 🗂️ ตารางและ Foreign Key หลัก

| ตาราง | Primary Key | Foreign Key ที่อ้างถึง |
|---|---|---|
| `unified_user` | id | – |
| `bicycle` | id | – |
| `maintenance` | id | bicycle_id → bicycle, reported_by/assigned_to → unified_user |
| `staff_officer` | id | user_id → unified_user |
| `campus_announcement` | id | created_by → unified_user |
| `system_audit_log` | id | user_id → unified_user |
| `bicycle_comparison` | id | user_id → unified_user, bicycle_id → bicycle |
| `notification` | id | user_id → unified_user |
| `feedback_rating` | id | user_id → unified_user, bicycle_id → bicycle, booking_id → reservation_booking |
| `return_record` | id | booking_id → reservation_booking, bicycle_id → bicycle, user_id → unified_user |
| `damage_evidence` | id | return_record_id → return_record, bicycle_id → bicycle |
| `penalty_strike` | id | user_id → unified_user, return_record_id → return_record, given_by → unified_user (staff) |
| `reservation_booking` | id | user_id → unified_user, bicycle_id → bicycle |
| `usage_history_log` | id | user_id → unified_user, bicycle_id → bicycle, booking_id → reservation_booking |
| `support_ticket` | id | user_id → unified_user, assigned_to → unified_user (staff) |

### ⚠️ ข้อควรพิจารณาเพิ่มเติม

1. **ENUM fields** — ควรกำหนดค่าที่แน่นอนตามที่ระบุใน Class Diagram เดิม เช่น:
   - `unified_user.role` → `student`, `staff`, `officer`
   - `bicycle.status` → `available`, `in_use`, `under_maintenance`, `retired`
   - `reservation_booking.status` → `pending`, `confirmed`, `in_progress`, `completed`, `cancelled`, `no_show`

2. **`staff_officer.user_id`** ควรมี `UNIQUE constraint` เพราะเป็นความสัมพันธ์ 1:0..1 กับ `unified_user`

3. **`return_record.return_station_id`** และ `usage_history_log.starting_station` / `ending_station` — ในไดอะแกรมเดิมยังเป็น string/int เปล่า ๆ ถ้ามีตาราง Station แยกในระบบจริง ควรทำเป็น FK ไปยังตาราง `station` แทน

4. **Cross-service tables (Monolith vs FastAPI)** — เนื่องจากระบบแบ่งเป็น Django Monolith และ FastAPI/React แยกกัน หากใช้ database คนละตัว ควรพิจารณาว่า field ที่อ้างข้ามฝั่ง (เช่น `user_id`, `bicycle_id` ที่ FastAPI service ต้องอ้างถึง) จะ sync กันอย่างไร (เช่น ผ่าน API แทน FK ตรง หรือใช้ shared DB)
