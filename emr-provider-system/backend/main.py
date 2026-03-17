from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models
import schemas
import database
import publisher
from faker import Faker
import random
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
    publisher.publish_event(
        operation='c', 
        table_name='patients', 
        data_snapshot=snapshot
    )

    return db_patient

@app.post("/test/seed-patient/{count}", tags=["Testing"])
def seed_patients(count: int, db: Session = Depends(database.get_db)):
    """
    Tự động tạo ra 'count' bệnh nhân ngẫu nhiên và bắn qua RabbitMQ.
    Một cú click, cả hệ thống (Adapter, Mongo) đều chạy!
    """
    created_patients = []
    for _ in range(count):
        # 1. Tạo dữ liệu giả cực thực tế
        gender_vn = random.choice(["Nam", "Nữ", "Khác"])
        fake_patient = {
            "patient_external_id": f"AUTO-{fake.random_int(1000, 9999)}",
            "national_id": fake.ssn(),
            "full_name": fake.name(),
            "gender": gender_vn,
            "birth_date": fake.date_of_birth(minimum_age=0, maximum_age=90).isoformat(),
            "address": fake.address(),
            "phone": fake.phone_number(),
            "insurance_card_no": f"DN{fake.random_int(100, 999)}{fake.random_int(10000, 99999)}"
        }

        # 2. Lưu SQL
        db_patient = models.Patient(**fake_patient)
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient)

        # 3. Bắn sang RabbitMQ (dùng code snapshot của em)
        snapshot = {c.name: getattr(db_patient, c.name) for c in db_patient.__table__.columns}
        if snapshot.get('birth_date'): snapshot['birth_date'] = snapshot['birth_date'].isoformat()
        
        publisher.publish_event(operation='c', table_name='patients', data_snapshot=snapshot)
        created_patients.append(db_patient.full_name)

    return {"status": f"Đã 'gieo mầm' xong {count} bệnh nhân", "names": created_patients}
