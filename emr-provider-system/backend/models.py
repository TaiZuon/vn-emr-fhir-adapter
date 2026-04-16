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
    ma_bac_si = Column(String(255), unique=True, nullable=False, index=True)
    ho_ten = Column(String(255), nullable=False)
    chuyen_khoa = Column(String(255))
    so_dien_thoai = Column(String(20))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    dot_dieu_tri_list = relationship("DotDieuTri", back_populates="nhan_vien_y_te")

class BenhNhan(Base):
    __tablename__ = "benh_nhan"

    id = Column(Integer, primary_key=True, index=True)
    ma_bn = Column(String(100), unique=True, nullable=False, index=True)
    ho_ten = Column(String(255), nullable=False)
    ngay_sinh = Column(String(12), nullable=False)
    gioi_tinh = Column(Integer, CheckConstraint('gioi_tinh IN (1, 2, 3)'))
    dia_chi = Column(String(1024))
    cccd = Column(String(15), unique=True)
    can_nang = Column(Numeric(5, 2))
    ten_nguoi_dua_tre_den = Column(String(255))
    chu_ky_so = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    dot_dieu_tri_list = relationship("DotDieuTri", back_populates="benh_nhan")

class DotDieuTri(Base):
    __tablename__ = "dot_dieu_tri"

    ma_lk = Column(String(100), primary_key=True, index=True)
    benh_nhan_id = Column(Integer, ForeignKey("benh_nhan.id"))
    ma_bac_si = Column(String(255), ForeignKey("nhan_vien_y_te.ma_bac_si"))
    ma_the = Column(String(15))
    ma_dkbd = Column(String(5))
    gt_the_tu = Column(String(12))
    gt_the_den = Column(String(12))
    mien_cung_ct = Column(String(12))
    ngay_vao = Column(String(12))
    ngay_ra = Column(String(12))
    ma_benh = Column(String(20))
    ma_benh_khac = Column(Text)
    ten_benh = Column(Text)
    ket_qua_dtri = Column(Integer)
    tinh_trang_rv = Column(Integer)
    t_tongchi = Column(Numeric(15, 2))
    t_bhtt = Column(Numeric(15, 2))
    t_bntt = Column(Numeric(15, 2))
    t_bncct = Column(Numeric(15, 2))
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
    dot_dieu_tri_id = Column(String(100), ForeignKey("dot_dieu_tri.ma_lk"))
    ma_don_thuoc = Column(String(20))
    stt = Column(Integer)
    ma_thuoc = Column(String(255))
    ten_thuoc = Column(String(1024))
    don_vi_tinh = Column(String(50))
    ham_luong = Column(String(1024))
    duong_dung = Column(String(4))
    lieu_dung = Column(String(1024))
    so_luong = Column(Numeric(15, 3))
    don_gia = Column(Numeric(15, 3))
    thanh_tien = Column(Numeric(15, 2))
    ma_bac_si = Column(String(255))
    ngay_yl = Column(String(12))
    chu_ky_so = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    dot_dieu_tri = relationship("DotDieuTri", back_populates="chi_tiet_thuoc_list")

class DichVuKyThuat(Base):
    __tablename__ = "dich_vu_ky_thuat"

    id = Column(Integer, primary_key=True, index=True)
    dot_dieu_tri_id = Column(String(100), ForeignKey("dot_dieu_tri.ma_lk"))
    stt = Column(Integer)
    ma_dich_vu = Column(String(255))
    ten_dich_vu = Column(String(1024))
    ma_vat_tu = Column(String(255))
    ten_vat_tu = Column(String(1024))
    so_luong = Column(Numeric(15, 3))
    don_gia = Column(Numeric(15, 3))
    thanh_tien = Column(Numeric(15, 2))
    ma_khoa = Column(String(15))
    ma_giuong = Column(String(50))
    ma_bac_si = Column(String(255))
    ngay_yl = Column(String(12))
    ngay_kq = Column(String(12))
    ma_may = Column(String(1024))
    chu_ky_so = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    dot_dieu_tri = relationship("DotDieuTri", back_populates="dich_vu_ky_thuat_list")

class CanLamSang(Base):
    __tablename__ = "can_lam_sang"

    id = Column(Integer, primary_key=True, index=True)
    dot_dieu_tri_id = Column(String(100), ForeignKey("dot_dieu_tri.ma_lk"))
    stt = Column(Integer)
    ma_dich_vu = Column(String(255))
    ma_chi_so = Column(String(50))
    ten_chi_so = Column(String(255))
    gia_tri = Column(String(255))
    ma_may = Column(String(1024))
    mo_ta = Column(Text)
    ket_luan = Column(Text)
    ngay_kq = Column(String(12))
    chu_ky_so = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    dot_dieu_tri = relationship("DotDieuTri", back_populates="can_lam_sang_list")

class DienBienLamSang(Base):
    __tablename__ = "dien_bien_lam_sang"

    id = Column(Integer, primary_key=True, index=True)
    dot_dieu_tri_id = Column(String(100), ForeignKey("dot_dieu_tri.ma_lk"))
    stt = Column(Integer)
    dien_bien = Column(Text)
    hoi_chan = Column(Text)
    phau_thuat = Column(Text)
    ngay_yl = Column(String(12))
    chu_ky_so = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    dot_dieu_tri = relationship("DotDieuTri", back_populates="dien_bien_lam_sang_list")

