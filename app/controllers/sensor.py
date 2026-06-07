"""Endpoint API untuk ESP32 mengirim data sensor + endpoint internal untuk peta."""
from flask import Blueprint, request, jsonify, current_app

from app import db
from app.models.sensor import Sensor, DataSensor

sensor_bp = Blueprint("sensor", __name__)


def _validate_api_key() -> bool:
    key = request.headers.get("X-API-Key") or request.headers.get("X-Api-Key")
    return key and key == current_app.config["SENSOR_API_KEY"]


@sensor_bp.route("/data", methods=["POST"])
def terima_data():
    """Terima pembacaan dari ESP32.

    Header: X-API-Key: <rahasia>
    Body JSON: { "sensor_id": "S1", "kelembapan": 45, "getaran": "Rendah" }
    """
    if not _validate_api_key():
        return jsonify({"error": "API Key tidak valid"}), 401

    payload = request.get_json(silent=True) or {}
    kode = (payload.get("sensor_id") or "").strip()
    kelembapan = payload.get("kelembapan")
    getaran = (payload.get("getaran") or "").strip()

    if not kode or kelembapan is None or not getaran:
        return jsonify({"error": "Field wajib: sensor_id, kelembapan, getaran"}), 400

    try:
        kelembapan = float(kelembapan)
    except (TypeError, ValueError):
        return jsonify({"error": "Kelembapan harus angka"}), 400

    sensor = Sensor.query.filter_by(kode_sensor=kode).first()
    if not sensor:
        return jsonify({"error": f"Sensor {kode} tidak terdaftar"}), 404

    status = DataSensor.hitung_status(kelembapan, getaran)
    data = DataSensor(
        sensor_id=sensor.id,
        kelembapan=kelembapan,
        getaran=getaran,
        status=status,
    )
    db.session.add(data)
    db.session.commit()

    return jsonify({
        "ok": True,
        "data": data.to_dict(),
        "sensor": {"id": sensor.id, "kode": sensor.kode_sensor},
    }), 201


@sensor_bp.route("/list", methods=["GET"])
def list_sensors():
    """Untuk peta — daftar sensor + status terkini (publik)."""
    items = []
    for s in Sensor.query.filter_by(is_active=True).all():
        latest = s.latest
        items.append({
            "id": s.id,
            "kode": s.kode_sensor,
            "nama_lokasi": s.nama_lokasi,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "status": latest.status if latest else "Normal",
            "kelembapan": latest.kelembapan if latest else None,
            "getaran": latest.getaran if latest else None,
        })
    return jsonify(items)


@sensor_bp.route("/laporan-titik", methods=["GET"])
def titik_laporan():
    """Untuk peta — titik laporan yang sudah diverifikasi."""
    from app.models.laporan import Laporan
    items = []
    laporans = Laporan.query.filter(
        Laporan.status != Laporan.STATUS_MENUNGGU,
        Laporan.status != Laporan.STATUS_DITOLAK,
    ).all()
    for l in laporans:
        items.append({
            "id": l.id,
            "latitude": l.latitude,
            "longitude": l.longitude,
            "kategori": l.kategori,
            "lokasi_label": l.lokasi_label or l.dusun,
            "status": l.status,
        })
    return jsonify(items)
