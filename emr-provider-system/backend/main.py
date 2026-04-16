from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
import random
from datetime import timedelta
import string

from database import Base, engine, get_db
import models
import schemas
from constants import *

# Initialize database
Base.metadata.create_all(bind=engine)

app = FastAPI(title=API_TITLE)

# Benh Nhan Endpoints
@app.get(ENDPOINT_BENH_NHAN, response_model=List[schemas.BenhNhanSchema])
def read_benh_nhans(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    benh_nhans = db.query(models.BenhNhan).filter(models.BenhNhan.is_deleted == False).offset(skip).limit(limit).all()
    return benh_nhans

@app.post(ENDPOINT_BENH_NHAN, response_model=schemas.BenhNhanSchema)
def create_benh_nhan(benh_nhan: schemas.BenhNhanCreate, db: Session = Depends(get_db)):
    db_benh_nhan = models.BenhNhan(**benh_nhan.dict())
    db.add(db_benh_nhan)
    db.commit()
    db.refresh(db_benh_nhan)
    return db_benh_nhan

# Nhan Vien Y Te Endpoints
@app.get(ENDPOINT_NHAN_VIEN_Y_TE, response_model=List[schemas.NhanVienYTeSchema])
def read_nhan_vien_y_tes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    nhan_viens = db.query(models.NhanVienYTe).filter(models.NhanVienYTe.is_deleted == False).offset(skip).limit(limit).all()
    return nhan_viens

@app.post(ENDPOINT_NHAN_VIEN_Y_TE, response_model=schemas.NhanVienYTeSchema)
def create_nhan_vien_y_te(nhan_vien: schemas.NhanVienYTeCreate, db: Session = Depends(get_db)):
    db_nhan_vien = models.NhanVienYTe(**nhan_vien.dict())
    db.add(db_nhan_vien)
    db.commit()
    db.refresh(db_nhan_vien)
    return db_nhan_vien

# Dot Dieu Tri Endpoints
@app.get(ENDPOINT_DOT_DIEU_TRI, response_model=List[schemas.DotDieuTriSchema])
def read_dot_dieu_tris(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    dot_dieu_tris = db.query(models.DotDieuTri).filter(models.DotDieuTri.is_deleted == False).offset(skip).limit(limit).all()
    return dot_dieu_tris

@app.post(ENDPOINT_DOT_DIEU_TRI, response_model=schemas.DotDieuTriSchema)
def create_dot_dieu_tri(dot_dieu_tri: schemas.DotDieuTriCreate, db: Session = Depends(get_db)):
    db_dot_dieu_tri = models.DotDieuTri(**dot_dieu_tri.dict())
    db.add(db_dot_dieu_tri)
    db.commit()
    db.refresh(db_dot_dieu_tri)
    return db_dot_dieu_tri

# Chi Tiet Thuoc Endpoints
@app.get(ENDPOINT_CHI_TIET_THUOC, response_model=List[schemas.ChiTietThuocSchema])
def read_chi_tiet_thuocs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    chi_tiet_thuocs = db.query(models.ChiTietThuoc).filter(models.ChiTietThuoc.is_deleted == False).offset(skip).limit(limit).all()
    return chi_tiet_thuocs

@app.post(ENDPOINT_CHI_TIET_THUOC, response_model=schemas.ChiTietThuocSchema)
def create_chi_tiet_thuoc(chi_tiet_thuoc: schemas.ChiTietThuocCreate, db: Session = Depends(get_db)):
    db_chi_tiet_thuoc = models.ChiTietThuoc(**chi_tiet_thuoc.dict())
    if db_chi_tiet_thuoc.don_gia and db_chi_tiet_thuoc.so_luong:
        db_chi_tiet_thuoc.thanh_tien = float(db_chi_tiet_thuoc.don_gia) * float(db_chi_tiet_thuoc.so_luong)
    db.add(db_chi_tiet_thuoc)
    db.commit()
    db.refresh(db_chi_tiet_thuoc)
    return db_chi_tiet_thuoc

# Dich Vu Ky Thuat Endpoints
@app.get(ENDPOINT_DICH_VU_KY_THUAT, response_model=List[schemas.DichVuKyThuatSchema])
def read_dich_vu_ky_thuats(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    dich_vu_ky_thuats = db.query(models.DichVuKyThuat).filter(models.DichVuKyThuat.is_deleted == False).offset(skip).limit(limit).all()
    return dich_vu_ky_thuats

@app.post(ENDPOINT_DICH_VU_KY_THUAT, response_model=schemas.DichVuKyThuatSchema)
def create_dich_vu_ky_thuat(dich_vu_ky_thuat: schemas.DichVuKyThuatCreate, db: Session = Depends(get_db)):
    db_dich_vu = models.DichVuKyThuat(**dich_vu_ky_thuat.dict())
    if db_dich_vu.don_gia and db_dich_vu.so_luong:
        db_dich_vu.thanh_tien = float(db_dich_vu.don_gia) * float(db_dich_vu.so_luong)
    db.add(db_dich_vu)
    db.commit()
    db.refresh(db_dich_vu)
    return db_dich_vu

# Can Lam Sang Endpoints
@app.get(ENDPOINT_CAN_LAM_SANG, response_model=List[schemas.CanLamSangSchema])
def read_can_lam_sangs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    can_lam_sangs = db.query(models.CanLamSang).filter(models.CanLamSang.is_deleted == False).offset(skip).limit(limit).all()
    return can_lam_sangs

@app.post(ENDPOINT_CAN_LAM_SANG, response_model=schemas.CanLamSangSchema)
def create_can_lam_sang(can_lam_sang: schemas.CanLamSangCreate, db: Session = Depends(get_db)):
    db_can_lam_sang = models.CanLamSang(**can_lam_sang.dict())
    db.add(db_can_lam_sang)
    db.commit()
    db.refresh(db_can_lam_sang)
    return db_can_lam_sang

# Dien Bien Lam Sang Endpoints
@app.get(ENDPOINT_DIEN_BIEN_LAM_SANG, response_model=List[schemas.DienBienLamSangSchema])
def read_dien_bien_lam_sangs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    dien_biens = db.query(models.DienBienLamSang).filter(models.DienBienLamSang.is_deleted == False).offset(skip).limit(limit).all()
    return dien_biens

@app.post(ENDPOINT_DIEN_BIEN_LAM_SANG, response_model=schemas.DienBienLamSangSchema)
def create_dien_bien_lam_sang(dien_bien: schemas.DienBienLamSangCreate, db: Session = Depends(get_db)):
    db_dien_bien = models.DienBienLamSang(**dien_bien.dict())
    db.add(db_dien_bien)
    db.commit()
    db.refresh(db_dien_bien)
    return db_dien_bien

# Seed Fake Database logic
@app.post("/test/seed-complex-workflow/{count}")
def seed_complex_workflow(count: int, db: Session = Depends(get_db)):
    from faker import Faker
    fake = Faker('vi_VN')
    num_practitioners = max(count // 10, 1)

    # 1. Nhan_Vien_Y_Te
    doctors = []
    for i in range(num_practitioners):
        doc = models.NhanVienYTe(
            ma_bac_si=f"BS{str(i).zfill(4)}{random.randint(100,999)}",
            ho_ten=fake.name(),
            chuyen_khoa=random.choice(["Nội khoa", "Ngoại khoa", "Nhi khoa", "Sản khoa", "Mắt", "Tai mũi họng"]),
            so_dien_thoai=fake.phone_number()[:10]
        )
        db.add(doc)
        doctors.append(doc)
    db.commit()

    created_patients = 0
    # Helper: chuyển datetime sang yyyymmddHHMM
    def to_qd130(dt):
        return dt.strftime("%Y%m%d%H%M")

    # Bệnh nhân
    for i in range(count):
        dob = fake.date_of_birth(minimum_age=1, maximum_age=90)
        patient = models.BenhNhan(
            ma_bn=f"BN{str(uuid.uuid4())[:8].upper()}",
            ho_ten=fake.name(),
            ngay_sinh=dob.strftime("%Y%m%d") + "0000",
            gioi_tinh=random.choice([1, 2, 3]),
            dia_chi=fake.address(),
            cccd=f"0{random.randint(10000000000, 99999999999)}",
            can_nang=round(random.uniform(3.0, 90.0), 1),
            ten_nguoi_dua_tre_den=fake.name() if random.random() < 0.2 else None
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
        created_patients += 1

        # Đợt điều trị cho mỗi BN
        num_encounters = random.randint(1, 3)
        for _ in range(num_encounters):
            dr = random.choice(doctors)
            ngay_vao = fake.date_time_between(start_date='-1y', end_date='now')
            ngay_ra = ngay_vao + timedelta(days=random.randint(1, 30))
            diagnosis_choices = [
                ("J00", "Viêm mũi họng cấp tính"),
                ("J06.9", "Nhiễm khuẩn hô hấp trên cấp"),
                ("J18.9", "Viêm phổi"),
                ("E11.9", "Đái tháo đường type 2"),
                ("I10", "Tăng huyết áp"),
                ("I50.9", "Suy tim"),
                ("K21.0", "Trào ngược dạ dày thực quản"),
                ("K29.7", "Viêm dạ dày"),
                ("K35.80", "Viêm ruột thừa cấp"),
                ("N39.0", "Nhiễm khuẩn đường tiết niệu"),
                ("M54.5", "Đau thắt lưng"),
                ("A09", "Tiêu chảy nhiễm khuẩn"),
                ("D50.9", "Thiếu máu thiếu sắt"),
            ]
            ma_benh, ten_benh = random.choice(diagnosis_choices)
            encounter = models.DotDieuTri(
                ma_lk=f"LK{str(uuid.uuid4()).replace('-', '').upper()[:20]}",
                benh_nhan_id=patient.id,
                ma_bac_si=dr.ma_bac_si,
                ngay_vao=to_qd130(ngay_vao),
                ngay_ra=to_qd130(ngay_ra),
                ma_the=f"GD479{random.randint(1000000000, 9999999999)}",
                ma_dkbd="01001",
                ma_benh=ma_benh,
                ten_benh=ten_benh,
                tinh_trang_rv=random.choice([1, 2, 3, 4])
            )
            db.add(encounter)
            db.commit()
            db.refresh(encounter)

            # Thuoc
            medication_choices = [
                ("PARA500", "Paracetamol 500mg", "Viên", "500mg", "Uống"),
                ("AMOX500", "Amoxicillin 500mg", "Viên", "500mg", "Uống"),
                ("METF500", "Metformin 500mg", "Viên", "500mg", "Uống"),
                ("AMLO5", "Amlodipine 5mg", "Viên", "5mg", "Uống"),
                ("OMEP20", "Omeprazole 20mg", "Viên", "20mg", "Uống"),
                ("ATOR20", "Atorvastatin 20mg", "Viên", "20mg", "Uống"),
                ("LOSA50", "Losartan 50mg", "Viên", "50mg", "Uống"),
                ("CEFO1G", "Cefotaxime 1g", "Lọ", "1g", "Tiêm tĩnh mạch"),
                ("CIPR500", "Ciprofloxacin 500mg", "Viên", "500mg", "Uống"),
                ("IBUP400", "Ibuprofen 400mg", "Viên", "400mg", "Uống"),
                ("FURO40", "Furosemide 40mg", "Viên", "40mg", "Uống"),
                ("SALB2", "Salbutamol 2mg", "Viên", "2mg", "Hít"),
            ]
            selected_meds = random.sample(medication_choices, k=random.randint(2, 5))
            for t_stt, (ma_thuoc, ten_thuoc, dvt, ham_luong, duong_dung) in enumerate(selected_meds, 1):
                ma_don_thuoc = f"{''.join(random.choices(string.ascii_uppercase, k=5))}{''.join(random.choices(string.digits, k=7))}-{random.choice(string.digits)}"
                sl = float(random.randint(1, 20))
                gia = float(random.randint(10, 500) * 1000)
                thuoc = models.ChiTietThuoc(
                    dot_dieu_tri_id=encounter.ma_lk,
                    ma_don_thuoc=ma_don_thuoc,
                    stt=t_stt,
                    ma_thuoc=ma_thuoc,
                    ten_thuoc=ten_thuoc,
                    ham_luong=ham_luong,
                    don_vi_tinh=dvt,
                    duong_dung=duong_dung,
                    lieu_dung=f"{random.randint(1,3)} lần/ngày",
                    so_luong=sl,
                    don_gia=gia,
                    thanh_tien=sl * gia,
                    ma_bac_si=dr.ma_bac_si,
                    ngay_yl=to_qd130(ngay_vao)
                )
                db.add(thuoc)
        
            # DichVuKyThuat
            procedure_choices = [
                ("PT004", "Nội soi dạ dày"),
                ("PT006", "Chụp X-quang ngực"),
                ("PT007", "Chụp CT Scanner"),
                ("PT009", "Siêu âm ổ bụng"),
                ("PT010", "Siêu âm tim"),
                ("PT011", "Điện tâm đồ (ECG)"),
                ("PT013", "Thở oxy"),
                ("PT014", "Truyền dịch"),
                ("PT016", "Khâu vết thương"),
                ("PT018", "Vật lý trị liệu"),
            ]
            selected_procs = random.sample(procedure_choices, k=random.randint(1, 4))
            for d_stt, (ma_dv, ten_dv) in enumerate(selected_procs, 1):
                sl = float(random.randint(1, 5))
                gia = float(random.randint(50, 2000) * 1000)
                dv = models.DichVuKyThuat(
                    dot_dieu_tri_id=encounter.ma_lk,
                    stt=d_stt,
                    ma_dich_vu=ma_dv,
                    ten_dich_vu=ten_dv,
                    so_luong=sl,
                    don_gia=gia,
                    thanh_tien=sl * gia,
                    ma_bac_si=dr.ma_bac_si,
                    ngay_yl=to_qd130(ngay_vao),
                    ngay_kq=to_qd130(ngay_ra)
                )
                db.add(dv)

            # CanLamSang (Xét nghiệm / Cận lâm sàng)
            lab_tests = [
                ("2339-0", "Glucose máu", "mmol/L", 3.9, 11.1),
                ("6690-2", "Bạch cầu", "G/L", 4.0, 15.0),
                ("718-7", "Hemoglobin", "g/dL", 10.0, 18.0),
                ("2160-0", "Creatinine", "µmol/L", 44.0, 133.0),
                ("1742-6", "ALT (SGPT)", "U/L", 5.0, 80.0),
            ]
            for c_stt, (ma_chi_so, ten_chi_so, unit, lo, hi) in enumerate(random.sample(lab_tests, k=random.randint(1, 4)), 1):
                cls = models.CanLamSang(
                    dot_dieu_tri_id=encounter.ma_lk,
                    stt=c_stt,
                    ma_dich_vu=f"XN{random.randint(100,999)}",
                    ma_chi_so=ma_chi_so,
                    ten_chi_so=ten_chi_so,
                    gia_tri=f"{round(random.uniform(lo, hi), 2)} {unit}",
                    ket_luan=random.choice(["Bình thường", "Cao", "Thấp", "Bất thường"]),
                    ngay_kq=to_qd130(ngay_ra)
                )
                db.add(cls)

            # DienBienLamSang
            for db_stt in range(1, random.randint(1, 3) + 1):
                dbls = models.DienBienLamSang(
                    dot_dieu_tri_id=encounter.ma_lk,
                    stt=db_stt,
                    dien_bien=random.choice([
                        "Bệnh nhân sốt cao 39 độ, ho có đờm",
                        "Huyết áp ổn định, không sốt",
                        "Đau bụng vùng hạ sườn phải, buồn nôn",
                        "Tình trạng cải thiện, ăn uống được"
                    ]),
                    hoi_chan=random.choice([None, "Hội chẩn khoa Nội: Tiếp tục điều trị nội khoa"]),
                    phau_thuat=random.choice([None, None, "Cắt ruột thừa nội soi"]),
                    ngay_yl=to_qd130(ngay_vao + timedelta(days=db_stt - 1))
                )
                db.add(dbls)

            db.commit()

    return {"message": f"Successfully seeded {created_patients} patients and related workflows"}
