from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    Text,
    Numeric,
    Boolean,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from database import Base
import datetime

class NhanVienYTe(Base):
    __tablename__ = "nhan_vien_y_te"

    id = Column(Integer, primary_key=True, index=True)
    ma_bac_si = Column(String(20), unique=True, nullable=False, index=True)
    ho_ten = Column(String(100), nullable=False)
    chuyen_khoa = Column(String(100))
    so_dien_thoai = Column(String(20))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    dot_dieu_tri_list = relationship("DotDieuTri", back_populates="nhan_vien_y_te")

class BenhNhan(Base):
    __tablename__ = "benh_nhan"

    id = Column(Integer, primary_key=True, index=True)
    ma_bn = Column(String(50), unique=True, nullable=False, index=True)
    ho_ten = Column(String(100), nullable=False)
    ngay_sinh = Column(Date, nullable=False)
    gioi_tinh = Column(Integer, CheckConstraint('gioi_tinh IN (1, 2, 3)'))
    dia_chi = Column(Text)
    cccd = Column(String(12), unique=True)
    can_nang = Column(Numeric)
    ten_nguoi_dua_tre_den = Column(String(100))
    chu_ky_so = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    dot_dieu_tri_list = relationship("DotDieuTri", back_populates="benh_nhan")

class DotDieuTri(Base):
    __tablename__ = "dot_dieu_tri"

    ma_lk = Column(String(50), primary_key=True, index=True)
    benh_nhan_id = Column(Integer, ForeignKey("benh_nhan.id"))
    ma_bac_si = Column(String(20), ForeignKey("nhan_vien_y_te.ma_bac_si"))
    ma_the = Column(String(50))
    ma_dkbd = Column(String(20))
    gt_the_tu = Column(Date)
    gt_the_den = Column(Date)
    mien_cung_ct = Column(Date)
    ngay_vao = Column(DateTime)
    ngay_ra = Column(DateTime)
    ma_benh = Column(String(20))
    ma_benh_khac = Column(String(200))
    ten_benh = Column(Text)
    ket_qua_dtri = Column(Integer)
    tinh_trang_rv = Column(Integer)
    t_tongchi = Column(Numeric)
    t_bhtt = Column(Numeric)
    t_bntt = Column(Numeric)
    t_bncct = Column(Numeric)
    chu_ky_so = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    benh_nhan = relationship("BenhNhan", back_populates="dot_dieu_tri_list")
    nhan_vien_y_te = relationship("NhanVienYTe", back_populates="dot_dieu_tri_list")
    chi_tiet_thuoc_list = relationship("ChiTietThuoc", back_populates="dot_dieu_tri")
    dich_vu_ky_thuat_list = relationship("DichVuKyThuat", back_populates="dot_dieu_tri")
    can_lam_sang_list = relationship("CanLamSang", back_populates="dot_dieu_tri")
    dien_bien_lam_sang_list = relationship("DienBienLamSang", back_populates="dot_dieu_tri")

class ChiTietThuoc(Base):
    __tablename__ = "chi_tiet_thuoc"

    id = Column(Integer, primary_key=True, index=True)
    dot_dieu_tri_id = Column(String(50), ForeignKey("dot_dieu_tri.ma_lk"))
    ma_don_thuoc = Column(String(20))
    stt = Column(Integer)
    ma_thuoc = Column(String(50))
    ten_thuoc = Column(String(200))
    don_vi_tinh = Column(String(20))
    ham_luong = Column(String(50))
    duong_dung = Column(String(50))
    lieu_dung = Column(String(100))
    so_luong = Column(Numeric)
    don_gia = Column(Numeric)
    thanh_tien = Column(Numeric)
    ma_bac_si = Column(String(20))
    ngay_yl = Column(DateTime)
    chu_ky_so = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    dot_dieu_tri = relationship("DotDieuTri", back_populates="chi_tiet_thuoc_list")

class DichVuKyThuat(Base):
    __tablename__ = "dich_vu_ky_thuat"

    id = Column(Integer, primary_key=True, index=True)
    dot_dieu_tri_id = Column(String(50), ForeignKey("dot_dieu_tri.ma_lk"))
    stt = Column(Integer)
    ma_dich_vu = Column(String(50))
    ten_dich_vu = Column(String(200))
    ma_vat_tu = Column(String(50))
    ten_vat_tu = Column(String(200))
    so_luong = Column(Numeric)
    don_gia = Column(Numeric)
    thanh_tien = Column(Numeric)
    ma_khoa = Column(String(50))
    ma_giuong = Column(String(50))
    ma_bac_si = Column(String(20))
    ngay_yl = Column(DateTime)
    ngay_kq = Column(DateTime)
    chu_ky_so = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    dot_dieu_tri = relationship("DotDieuTri", back_populates="dich_vu_ky_thuat_list")

class CanLamSang(Base):
    __tablename__ = "can_lam_sang"

    id = Column(Integer, primary_key=True, index=True)
    dot_dieu_tri_id = Column(String(50), ForeignKey("dot_dieu_tri.ma_lk"))
    stt = Column(Integer)
    ma_dich_vu = Column(String(50))
    ma_chi_so = Column(String(50))
    ten_chi_so = Column(String(200))
    gia_tri = Column(String(100))
    ma_may = Column(String(50))
    mo_ta = Column(Text)
    ket_luan = Column(Text)
    ngay_kq = Column(DateTime)
    chu_ky_so = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    dot_dieu_tri = relationship("DotDieuTri", back_populates="can_lam_sang_list")

class DienBienLamSang(Base):
    __tablename__ = "dien_bien_lam_sang"

    id = Column(Integer, primary_key=True, index=True)
    dot_dieu_tri_id = Column(String(50), ForeignKey("dot_dieu_tri.ma_lk"))
    stt = Column(Integer)
    dien_bien = Column(Text)
    hoi_chan = Column(Text)
    phau_thuat = Column(Text)
    ngay_yl = Column(DateTime)
    chu_ky_so = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    dot_dieu_tri = relationship("DotDieuTri", back_populates="dien_bien_lam_sang_list")

