from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import models
import schemas
import database
# import publisher
from faker import Faker
import random
import time
import uuid
from constants import API_TITLE

app = FastAPI(title=API_TITLE)

fake = Faker(["vi_VN"])


@app.post("/patients/", response_model=schemas.PatientResponse)
def create_patient(
    patient: schemas.PatientCreate, db: Session = Depends(database.get_db)
):
    # Lưu vào SQL
    db_patient = models.Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)

    # Chụp ảnh dữ liệu (Snapshot) cho Fat Message
    # Lấy tự động tất cả các cột trong bảng patients
    snapshot = {c.name: getattr(db_patient, c.name) for c in db_patient.__table__.columns}
    
    # Ép kiểu datetime sang chuỗi ISO 8601 để thư viện JSON có thể đọc được
    if snapshot.get('birth_date'):
        snapshot['birth_date'] = snapshot['birth_date'].isoformat()
    if snapshot.get('created_at'):
        snapshot['created_at'] = snapshot['created_at'].isoformat()
    if snapshot.get('updated_at'):
        snapshot['updated_at'] = snapshot['updated_at'].isoformat()

    # Bắn sự kiện sang RabbitMQ theo chuẩn Debezium
    # op='c' nghĩa là Create, table_name='patients' để báo cho Adapter biết dùng Rule nào
    # publisher.publish_event(
    #     operation='c', 
    #     table_name='patients', 
    #     data_snapshot=snapshot
    # )

    return db_patient

@app.post("/test/seed-patient/{count}", tags=["Testing"])
def seed_patients(count: int, db: Session = Depends(database.get_db)):
    """
    Tự động tạo ra 'count' bệnh nhân ngẫu nhiên, không trùng lặp và bắn qua RabbitMQ.
    """
    created_names = []
    created_count = 0
    attempts = 0
    max_attempts = count * 3 # Tăng lên một chút để thoải mái thử lại nếu trùng

    while created_count < count and attempts < max_attempts:
        attempts += 1
        
        # 1. Tạo ID kết hợp Timestamp + UUID để đảm bảo không trùng với quá khứ
        # Lấy 6 số cuối của timestamp (miliseconds)
        ts = str(int(time.time() * 1000))[-6:] 
        suffix = uuid.uuid4().hex[:4].upper()
        ext_id = f"BN-2026-{ts}-{suffix}"

        # 2. Tạo CCCD ngẫu nhiên 12 số
        nat_id = fake.numerify(text='0###########')
        
        # Kiểm tra nhanh trong DB để tránh query lỗi Integrity sau này
        exists = db.query(models.Patient).filter(
            (models.Patient.patient_external_id == ext_id) | 
            (models.Patient.national_id == nat_id)
        ).first()

        if exists:
            continue # Trùng thì bỏ qua vòng này, tìm bộ mới

        try:
            # Lưu vào Postgres
            new_patient = models.Patient(
                patient_external_id=ext_id,
                national_id=nat_id,
                full_name=fake.name(),
                gender=random.choice(["Nam", "Nữ", "Khác"]),
                birth_date=fake.date_of_birth(minimum_age=1, maximum_age=90),
                address=fake.address().replace('\n', ', '),
                phone=fake.unique.numerify(text='09########'), # Dùng .unique của faker cho phone
                insurance_card_no=f"GD{fake.numerify(text='#############')}"
            )
            
            db.add(new_patient)
            db.commit()
            db.refresh(new_patient) # Để lấy lại ID tự tăng nếu có

            # 3. Bắn sang RabbitMQ
            # Lấy data_snapshot từ đối tượng vừa lưu (new_patient)
            snapshot = {c.name: getattr(new_patient, c.name) for c in new_patient.__table__.columns}
            
            # Convert date sang string cho JSON chuẩn
            if snapshot.get('birth_date'):
                snapshot['birth_date'] = snapshot['birth_date'].isoformat()
            
            # # Sử dụng publisher để bắn event
            # publisher.publish_event(
            #     operation='c', 
            #     table_name='patients', 
            #     data_snapshot=snapshot
            # )
            
            # 4. Ghi nhận thành công
            created_names.append(new_patient.full_name)
            created_count += 1

        except IntegrityError:
            db.rollback() # Trả lại transaction nếu trùng ở mức DB
            continue
        except Exception as e:
            db.rollback()
            print(f" [❌] Lỗi không xác định: {e}")
            continue

    return {
        "status": "success",
        "requested": count,
        "created": created_count,
        "total_attempts": attempts,
        "names": created_names
    }
