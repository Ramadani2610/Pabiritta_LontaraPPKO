"""Blueprint laporan warga (buat & lihat daftar)."""
import os
import uuid
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, current_app
)
from werkzeug.utils import secure_filename
from sqlalchemy import or_, desc

from app import db
from app.models.laporan import Laporan
from app.models.aktivitas import Aktivitas

laporan_bp = Blueprint("laporan", __name__)


def _allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


@laporan_bp.route("/buat", methods=["GET", "POST"])
def buat():
    if request.method == "POST":
        # Validasi field wajib
        kategori = request.form.get("kategori", "").strip()
        deskripsi = request.form.get("deskripsi", "").strip()
        lokasi_label = request.form.get("lokasi_label", "").strip() or None
        latitude = request.form.get("latitude", "").strip()
        longitude = request.form.get("longitude", "").strip()
        nama = request.form.get("nama_pelapor", "").strip()
        dusun = request.form.get("dusun", "").strip()
        no_hp = request.form.get("no_hp", "").strip() or None

        errors = []
        if kategori not in Laporan.KATEGORI_CHOICES:
            errors.append("Kategori tidak valid.")
        if not deskripsi:
            errors.append("Deskripsi wajib diisi.")
        try:
            lat_f = float(latitude)
            lng_f = float(longitude)
        except ValueError:
            errors.append("Koordinat lokasi tidak valid.")
            lat_f = lng_f = None
        if not nama:
            errors.append("Nama pelapor wajib diisi.")
        if not dusun:
            errors.append("Dusun wajib diisi.")

        # Upload foto
        foto_url = None
        file = request.files.get("foto")
        if file and file.filename:
            if not _allowed_file(file.filename):
                errors.append("Format foto harus JPG atau PNG.")
            else:
                ext = file.filename.rsplit(".", 1)[1].lower()
                fname = f"{uuid.uuid4().hex}.{ext}"
                fname = secure_filename(fname)
                fpath = os.path.join(current_app.config["UPLOAD_FOLDER"], fname)
                file.save(fpath)
                foto_url = f"uploads/{fname}"

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("public/buat_laporan.html", form=request.form)

        laporan = Laporan(
            foto_url=foto_url,
            latitude=lat_f,
            longitude=lng_f,
            kategori=kategori,
            deskripsi=deskripsi,
            lokasi_label=lokasi_label,
            nama_pelapor=nama,
            dusun=dusun,
            no_hp=no_hp,
            status=Laporan.STATUS_MENUNGGU,
        )
        db.session.add(laporan)
        Aktivitas.log("Sistem", "Menerima Laporan Baru", f"Laporan #{laporan.id} dari {nama}")
        db.session.commit()

        flash("Laporan berhasil dikirim. Terima kasih telah melapor!", "success")
        return redirect(url_for("laporan.daftar"))

    return render_template("public/buat_laporan.html", form={})


@laporan_bp.route("/")
def daftar():
    q = request.args.get("q", "").strip()
    kategori = request.args.get("kategori", "").strip()
    status = request.args.get("status", "").strip()

    # Publik hanya melihat laporan yang sudah diverifikasi (bukan Menunggu)
    query = Laporan.query.filter(Laporan.status != Laporan.STATUS_MENUNGGU)

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Laporan.deskripsi.ilike(like),
                Laporan.lokasi_label.ilike(like),
                Laporan.dusun.ilike(like),
                Laporan.nama_pelapor.ilike(like),
            )
        )
    if kategori and kategori in Laporan.KATEGORI_CHOICES:
        query = query.filter_by(kategori=kategori)
    if status and status in Laporan.STATUS_CHOICES:
        query = query.filter_by(status=status)

    laporans = query.order_by(desc(Laporan.created_at)).all()

    return render_template(
        "public/laporan_warga.html",
        laporans=laporans,
        q=q,
        kategori=kategori,
        status=status,
        kategori_choices=Laporan.KATEGORI_CHOICES,
        status_choices=[
            Laporan.STATUS_PROSES,
            Laporan.STATUS_TINDAK_LANJUT,
            Laporan.STATUS_SELESAI,
            Laporan.STATUS_DITOLAK,
        ],
    )
