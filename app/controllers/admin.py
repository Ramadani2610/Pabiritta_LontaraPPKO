"""Blueprint area admin: dashboard, manajemen laporan, manajemen pengguna."""
from functools import wraps
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, abort
)
from flask_login import login_required, current_user
from sqlalchemy import desc, or_

from app import db
from app.models.user import User
from app.models.laporan import Laporan
from app.models.sensor import Sensor
from app.models.aktivitas import Aktivitas

admin_bp = Blueprint("admin", __name__)


def superadmin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not current_user.is_superadmin:
            abort(403)
        return f(*args, **kwargs)
    return wrapper


# -------------------- DASHBOARD --------------------
@admin_bp.route("/")
@admin_bp.route("/dashboard")
@login_required
def dashboard():
    stats = {
        "total": Laporan.query.count(),
        "menunggu": Laporan.query.filter_by(status=Laporan.STATUS_MENUNGGU).count(),
        "selesai": Laporan.query.filter_by(status=Laporan.STATUS_SELESAI).count(),
        "sensor_aktif": Sensor.query.filter_by(is_active=True).count(),
        "sensor_total": Sensor.query.count(),
    }
    sensors = Sensor.query.filter_by(is_active=True).all()
    aktivitas = Aktivitas.query.order_by(desc(Aktivitas.created_at)).limit(5).all()

    # Distribusi laporan per kategori
    total_kategori = Laporan.query.count() or 1
    distribusi = []
    for kat in Laporan.KATEGORI_CHOICES:
        c = Laporan.query.filter_by(kategori=kat).count()
        distribusi.append({
            "kategori": kat,
            "count": c,
            "percent": round(c / total_kategori * 100),
        })

    template = (
        "admin/dashboard_superadmin.html"
        if current_user.is_superadmin
        else "admin/dashboard_admin.html"
    )
    return render_template(
        template,
        stats=stats,
        sensors=sensors,
        aktivitas=aktivitas,
        distribusi=distribusi,
    )


# -------------------- MANAJEMEN LAPORAN --------------------
@admin_bp.route("/laporan")
@login_required
def manajemen_laporan():
    q = request.args.get("q", "").strip()
    kategori = request.args.get("kategori", "").strip()
    status = request.args.get("status", "").strip()

    query = Laporan.query
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
        "admin/manajemen_laporan.html",
        laporans=laporans,
        q=q,
        kategori=kategori,
        status=status,
        kategori_choices=Laporan.KATEGORI_CHOICES,
        status_choices=Laporan.STATUS_CHOICES,
    )


@admin_bp.route("/laporan/<int:laporan_id>")
@login_required
def detail_laporan(laporan_id):
    laporan = Laporan.query.get_or_404(laporan_id)
    return render_template(
        "admin/detail_laporan.html",
        laporan=laporan,
        status_choices=Laporan.STATUS_CHOICES,
    )


@admin_bp.route("/laporan/<int:laporan_id>/status", methods=["POST"])
@login_required
def ubah_status(laporan_id):
    laporan = Laporan.query.get_or_404(laporan_id)
    new_status = request.form.get("status", "").strip()
    catatan = request.form.get("catatan_admin", "").strip()

    if new_status not in Laporan.STATUS_CHOICES:
        flash("Status tidak valid.", "error")
        return redirect(url_for("admin.detail_laporan", laporan_id=laporan_id))

    old_status = laporan.status
    laporan.status = new_status
    if catatan:
        laporan.catatan_admin = catatan

    Aktivitas.log(
        current_user.nama,
        f"Mengubah Status Laporan ({new_status})",
        f"Laporan #{laporan.id}: {old_status} → {new_status}",
    )
    db.session.commit()
    flash(f"Status laporan berhasil diubah menjadi {new_status}.", "success")
    return redirect(url_for("admin.detail_laporan", laporan_id=laporan_id))


# -------------------- MANAJEMEN PENGGUNA (SUPERADMIN) --------------------
@admin_bp.route("/pengguna")
@superadmin_required
def manajemen_pengguna():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/manajemen_pengguna.html", users=users)


@admin_bp.route("/pengguna/tambah", methods=["POST"])
@superadmin_required
def tambah_pengguna():
    email = request.form.get("email", "").strip().lower()
    nama = request.form.get("nama", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", User.ROLE_ADMIN)

    if not email or not nama or not password:
        flash("Semua field wajib diisi.", "error")
        return redirect(url_for("admin.manajemen_pengguna"))
    if len(password) < 6:
        flash("Password minimal 6 karakter.", "error")
        return redirect(url_for("admin.manajemen_pengguna"))
    if User.query.filter_by(email=email).first():
        flash("Email sudah terdaftar.", "error")
        return redirect(url_for("admin.manajemen_pengguna"))
    if role not in (User.ROLE_ADMIN, User.ROLE_SUPERADMIN):
        role = User.ROLE_ADMIN

    user = User(email=email, nama=nama, role=role, is_active=True)
    user.set_password(password)
    db.session.add(user)
    Aktivitas.log(current_user.nama, "Menambah Pengguna", f"{nama} ({role})")
    db.session.commit()
    flash(f"Pengguna {nama} berhasil ditambahkan.", "success")
    return redirect(url_for("admin.manajemen_pengguna"))


@admin_bp.route("/pengguna/<int:user_id>/toggle", methods=["POST"])
@superadmin_required
def toggle_pengguna(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Anda tidak bisa menonaktifkan akun sendiri.", "error")
        return redirect(url_for("admin.manajemen_pengguna"))
    user.is_active = not user.is_active
    aksi = "Mengaktifkan Pengguna" if user.is_active else "Menonaktifkan Pengguna"
    Aktivitas.log(current_user.nama, aksi, user.nama)
    db.session.commit()
    flash(f"Status pengguna {user.nama} berhasil diubah.", "success")
    return redirect(url_for("admin.manajemen_pengguna"))
