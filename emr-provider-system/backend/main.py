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

@app.post("/test/seed-practitioner/{count}", tags=["Testing"])
def seed_practitioners(count: int, db: Session = Depends(database.get_db)):
    """
    Tự động tạo ra 'count' nhân viên y tế ngẫu nhiên
    """
    created_names = []
    created_count = 0
    attempts = 0

    while created_count < count and attempts < count * 3:
        attempts += 1
        ts = str(int(time.time() * 1000))[-6:]
        suffix = uuid.uuid4().hex[:4].upper()
        prac_code = f"BS-2026-{ts}-{suffix}"
        
        exists = db.query(models.Practitioner).filter(models.Practitioner.practitioner_code == prac_code).first()
        if exists: continue

        try:
            new_prac = models.Practitioner(
                practitioner_code=prac_code,
                full_name=fake.name(),
                specialty=random.choice(["Nội khoa", "Ngoại khoa", "Nhi khoa", "Sản phụ khoa", "Mắt", "Tai Mũi Họng", "Răng Hàm Mặt"]),
                phone=fake.unique.numerify(text='09########')
            )
            db.add(new_prac)
            db.commit()
            db.refresh(new_prac)
            created_names.append(new_prac.full_name)
            created_count += 1
        except IntegrityError:
            db.rollback()
            continue
        except Exception as e:
            db.rollback()
            print(f" [❌] Lỗi: {e}")
            continue

    return {
        "status": "success",
        "requested": count,
        "created": created_count,
        "names": created_names
    }

@app.post("/test/seed-encounter/{count}", tags=["Testing"])
def seed_encounters(count: int, db: Session = Depends(database.get_db)):
    """
    Tự động tạo ra 'count' lượt khám (Encounter) ngẫu nhiên map giữa Patient và Practitioner có sẵn trong DB
    """
    patient_ids = [p.id for p in db.query(models.Patient.id).all()]
    practitioner_ids = [p.id for p in db.query(models.Practitioner.id).all()]
    
    if not patient_ids or not practitioner_ids:
        raise HTTPException(status_code=400, detail="Không có đủ dữ liệu Patient và Practitioner để tạo Encounter")

    created_ids = []
    created_count = 0

    for _ in range(count):
        try:
            new_enc = models.Encounter(
                patient_id=random.choice(patient_ids),
                practitioner_id=random.choice(practitioner_ids),
                status=random.choice(["COMPLETED", "IN_PROGRESS", "PLANNED", "ARRIVED", "CANCELLED"]),
                reason_code=random.choice(["J00", "I10", "E11", "K21"]),
                location=random.choice(["Phòng khám nội 1", "Phòng khám ngoại 2", "Khoa cấp cứu", "Phòng tiểu phẫu"])
            )
            db.add(new_enc)
            db.commit()
            db.refresh(new_enc)
            created_ids.append(new_enc.id)
            created_count += 1
        except Exception as e:
            db.rollback()
            print(f" [❌] Lỗi Encounter: {e}")
            continue

    return {
        "status": "success",
        "requested": count,
        "created": created_count,
        "encounter_ids": created_ids
    }
from typing import List

# --- PATIENT CRUD ---
@app.get("/patients/{patient_id}", response_model=schemas.PatientResponse)
def get_patient(patient_id: int, db: Session = Depends(database.get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id, models.Patient.is_deleted == False).first()
    if not patient: raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@app.get("/patients/", response_model=List[schemas.PatientResponse])
def list_patients(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return db.query(models.Patient).filter(models.Patient.is_deleted == False).offset(skip).limit(limit).all()

@app.put("/patients/{patient_id}", response_model=schemas.PatientResponse)
def update_patient(patient_id: int, patient_update: schemas.PatientUpdate, db: Session = Depends(database.get_db)):
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id, models.Patient.is_deleted == False).first()
    if not db_patient: raise HTTPException(status_code=404, detail="Patient not found")
    
    for key, value in patient_update.dict(exclude_unset=True).items():
        setattr(db_patient, key, value)
    db.commit()
    db.refresh(db_patient)
    return db_patient

@app.delete("/patients/{patient_id}", response_model=schemas.PatientResponse)
def delete_patient(patient_id: int, db: Session = Depends(database.get_db)):
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id, models.Patient.is_deleted == False).first()
    if not db_patient: raise HTTPException(status_code=404, detail="Patient not found")
    db_patient.is_deleted = True
    db.commit()
    db.refresh(db_patient)
    return db_patient

# --- PRACTITIONER CRUD ---
@app.post("/practitioners/", response_model=schemas.PractitionerResponse)
def create_practitioner(practitioner: schemas.PractitionerCreate, db: Session = Depends(database.get_db)):
    db_prac = models.Practitioner(**practitioner.dict())
    db.add(db_prac)
    db.commit()
    db.refresh(db_prac)
    return db_prac

@app.get("/practitioners/{prac_id}", response_model=schemas.PractitionerResponse)
def get_practitioner(prac_id: int, db: Session = Depends(database.get_db)):
    prac = db.query(models.Practitioner).filter(models.Practitioner.id == prac_id, models.Practitioner.is_deleted == False).first()
    if not prac: raise HTTPException(status_code=404, detail="Practitioner not found")
    return prac

@app.get("/practitioners/", response_model=List[schemas.PractitionerResponse])
def list_practitioners(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return db.query(models.Practitioner).filter(models.Practitioner.is_deleted == False).offset(skip).limit(limit).all()

@app.put("/practitioners/{prac_id}", response_model=schemas.PractitionerResponse)
def update_practitioner(prac_id: int, prac_update: schemas.PractitionerUpdate, db: Session = Depends(database.get_db)):
    db_prac = db.query(models.Practitioner).filter(models.Practitioner.id == prac_id, models.Practitioner.is_deleted == False).first()
    if not db_prac: raise HTTPException(status_code=404, detail="Practitioner not found")
    
    for key, value in prac_update.dict(exclude_unset=True).items():
        setattr(db_prac, key, value)
    db.commit()
    db.refresh(db_prac)
    return db_prac

@app.delete("/practitioners/{prac_id}", response_model=schemas.PractitionerResponse)
def delete_practitioner(prac_id: int, db: Session = Depends(database.get_db)):
    db_prac = db.query(models.Practitioner).filter(models.Practitioner.id == prac_id, models.Practitioner.is_deleted == False).first()
    if not db_prac: raise HTTPException(status_code=404, detail="Practitioner not found")
    db_prac.is_deleted = True
    db.commit()
    db.refresh(db_prac)
    return db_prac

# --- ENCOUNTER CRUD ---
@app.post("/encounters/", response_model=schemas.EncounterResponse)
def create_encounter(encounter: schemas.EncounterCreate, db: Session = Depends(database.get_db)):
    db_enc = models.Encounter(**encounter.dict())
    db.add(db_enc)
    db.commit()
    db.refresh(db_enc)
    return db_enc

@app.get("/encounters/{enc_id}", response_model=schemas.EncounterResponse)
def get_encounter(enc_id: int, db: Session = Depends(database.get_db)):
    enc = db.query(models.Encounter).filter(models.Encounter.id == enc_id, models.Encounter.is_deleted == False).first()
    if not enc: raise HTTPException(status_code=404, detail="Encounter not found")
    return enc

@app.get("/encounters/", response_model=List[schemas.EncounterResponse])
def list_encounters(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return db.query(models.Encounter).filter(models.Encounter.is_deleted == False).offset(skip).limit(limit).all()

@app.put("/encounters/{enc_id}", response_model=schemas.EncounterResponse)
def update_encounter(enc_id: int, enc_update: schemas.EncounterUpdate, db: Session = Depends(database.get_db)):
    db_enc = db.query(models.Encounter).filter(models.Encounter.id == enc_id, models.Encounter.is_deleted == False).first()
    if not db_enc: raise HTTPException(status_code=404, detail="Encounter not found")
    
    for key, value in enc_update.dict(exclude_unset=True).items():
        setattr(db_enc, key, value)
    db.commit()
    db.refresh(db_enc)
    return db_enc

@app.delete("/encounters/{enc_id}", response_model=schemas.EncounterResponse)
def delete_encounter(enc_id: int, db: Session = Depends(database.get_db)):
    db_enc = db.query(models.Encounter).filter(models.Encounter.id == enc_id, models.Encounter.is_deleted == False).first()
    if not db_enc: raise HTTPException(status_code=404, detail="Encounter not found")
    db_enc.is_deleted = True
    db.commit()
    db.refresh(db_enc)
    return db_enc
