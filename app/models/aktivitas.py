"""Model Aktivitas — log aksi admin untuk feed 'Aktivitas Sistem Terbaru'."""
from datetime import datetime
from app import db


class Aktivitas(db.Model):
    __tablename__ = "aktivitas"

    id = db.Column(db.Integer, primary_key=True)
    aktor = db.Column(db.String(120), nullable=False)  # nama admin / "Sistem"
    aksi = db.Column(db.String(255), nullable=False)
    keterangan = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    @classmethod
    def log(cls, aktor: str, aksi: str, keterangan: str = None) -> "Aktivitas":
        entry = cls(aktor=aktor, aksi=aksi, keterangan=keterangan)
        db.session.add(entry)
        return entry

    def __repr__(self) -> str:
        return f"<Aktivitas {self.aktor} {self.aksi}>"
