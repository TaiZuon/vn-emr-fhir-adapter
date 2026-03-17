from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models
import schemas
import database
import publisher
from constants import API_TITLE

app = FastAPI(title=API_TITLE)


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
