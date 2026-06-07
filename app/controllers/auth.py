"""Autentikasi admin."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from app.models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Email atau password salah.", "error")
            return render_template("admin/login.html", email=email)
        if not user.is_active:
            flash("Akun Anda telah dinonaktifkan. Hubungi Super Admin.", "error")
            return render_template("admin/login.html", email=email)

        login_user(user, remember=remember)
        flash(f"Selamat datang, {user.nama}!", "success")
        next_url = request.args.get("next")
        return redirect(next_url or url_for("admin.dashboard"))

    return render_template("admin/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Anda telah logout.", "success")
    return redirect(url_for("auth.login"))
