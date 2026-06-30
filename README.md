# Pa'Biritta

**Sistem Pemantauan Bencana Longsor berbasis komunitas** untuk Desa Lonjoboko,
Kabupaten Gowa. Warga dapat melaporkan kejadian/potensi longsor, admin desa
memverifikasi & menindaklanjuti, dan sensor IoT (EWS / Early Warning System)
memantau kondisi tanah secara real-time.

> "Pa'Biritta" — kabar / berita (Bahasa Bugis-Makassar).

---

## Fitur

- **Publik (tanpa login)**
  - Beranda dengan peta interaktif (Leaflet + OSM)
  - Status kondisi desa otomatis (Aman / Waspada / Bahaya) dari data sensor
  - Form laporan multi-step (Foto → Lokasi → Detail → Pelapor → Review)
  - Daftar laporan warga dengan filter & pencarian
- **Admin (login)**
  - Dashboard statistik, peta, monitoring sensor, aktivitas sistem
  - Manajemen laporan: verifikasi, ubah status, catatan tindak lanjut
- **Super Admin (login, role lebih tinggi)**
  - Semua fitur admin
  - Manajemen pengguna: tambah/aktifkan/nonaktifkan akun admin
- **API endpoint khusus ESP32** untuk push data sensor (proteksi API Key)

---

## Tech Stack

| Layer        | Tools                                                            |
|--------------|------------------------------------------------------------------|
| Frontend     | HTML, JavaScript vanilla, Tailwind CSS (via CDN)                 |
| Peta         | Leaflet.js + OpenStreetMap                                       |
| Backend      | Python 3.11+, Flask, Flask-Login, Flask-WTF                      |
| Database     | PostgreSQL + SQLAlchemy ORM (lokal) / **Neon** (produksi)        |
| Gambar       | **Cloudinary** (CDN upload, menggantikan penyimpanan lokal)      |
| Auth         | Flask-Login + bcrypt                                             |
| Deploy       | **Vercel** (Python Serverless) + Neon + Cloudinary               |

---

## Cara Menjalankan (Local Development)

### 1. Prasyarat
- Python 3.11+
- PostgreSQL 13+
- (Opsional) virtualenv / venv

### 2. Setup database
```bash
createdb pabiritta
```

### 3. Setup proyek
```bash
# Clone & masuk ke folder
git clone <repo-url>
cd pabiritta

# Buat virtualenv
python -m venv venv
source venv/bin/activate          # Linux/macOS
# venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Konfigurasi env
cp .env.example .env
# Edit .env — sesuaikan DATABASE_URL (Neon), SECRET_KEY,
# CLOUDINARY_CLOUD_NAME/API_KEY/API_SECRET, dan SENSOR_API_KEY
```

### 4. Inisialisasi data
```bash
python seed.py
```
Akan terbuat:
- 2 akun admin (lihat output)
- 4 sensor + bacaan awal
- 5 contoh laporan
- Beberapa log aktivitas

### 5. Jalankan aplikasi
```bash
python run.py
```
Buka http://localhost:5000

**Login admin:**
- Super Admin: `superadmin@pabiritta.id` / `admin123`
- Admin:       `admin@pabiritta.id`      / `admin123`

> ⚠️ Ganti password default sebelum deploy ke produksi.

---

## API Endpoint Sensor (ESP32 / EWS)

Endpoint untuk ESP32 mengirim data sensor.

**POST** `/api/sensor/data`

**Header:**
```
Content-Type: application/json
X-API-Key: <SENSOR_API_KEY dari .env>
```

**Body:**
```json
{
  "sensor_id": "S1",
  "kelembapan": 45,
  "getaran": "Rendah"
}
```

**Response (201):**
```json
{
  "ok": true,
  "data": { "id": 12, "sensor_id": 1, "kelembapan": 45, "getaran": "Rendah", "status": "Normal", "timestamp": "2026-06-05T10:00:00" },
  "sensor": { "id": 1, "kode": "S1" }
}
```

**Threshold otomatis:**
| Kondisi                                            | Status   |
|----------------------------------------------------|----------|
| `kelembapan > 90` atau `getaran = "Sangat Tinggi"` | Bahaya   |
| `kelembapan > 80` atau `getaran = "Tinggi"`        | Waspada  |
| Lainnya                                            | Normal   |

**Errors:**
- `401` — API Key tidak valid
- `404` — `sensor_id` tidak terdaftar
- `400` — Field tidak lengkap / format salah

> ⚠️ **EWS belum tersedia.** Hardware ESP32 + sensor belum dipasang. Endpoint
> ini sudah lengkap & berfungsi — tinggal arahkan ESP32 ke URL ini saat sudah
> siap. Data dummy bisa di-seed via `seed.py`.

---

## Deployment (Vercel + Neon + Cloudinary)

Stack produksi gratis tanpa kartu kredit:

| Komponen | Layanan |
|----------|---------|
| App host | [Vercel](https://vercel.com) — Python Serverless via `vercel.json` |
| Database | [Neon](https://neon.tech) — Serverless PostgreSQL |
| Gambar   | [Cloudinary](https://cloudinary.com) — CDN upload foto laporan |

### Langkah deploy
1. Push repo ke GitHub
2. Buat project Neon → salin `DATABASE_URL` (format `postgresql://...?sslmode=require`)
3. Buat akun Cloudinary → salin `CLOUD_NAME`, `API_KEY`, `API_SECRET`
4. Import repo ke Vercel → tambahkan semua env vars dari `.env.example`
5. Vercel otomatis deploy via `vercel.json` yang sudah ada

> **Catatan:** Neon bisa idle setelah tidak aktif — `pool_pre_ping=True` di `config.py` menangani reconnect otomatis.

---

## Struktur Folder

```
pabiritta/
├── app/
│   ├── __init__.py            # App factory
│   ├── models/                # SQLAlchemy models
│   ├── controllers/           # Blueprints (public, admin, auth, dst.)
│   ├── services/              # Business logic (status desa)
│   ├── views/                 # Templates Jinja2
│   │   ├── public/
│   │   ├── admin/
│   │   └── errors/
│   └── static/                # css/, js/, img/, uploads/
├── config.py
├── run.py
├── seed.py
├── requirements.txt
└── .env.example
```

---

## Keamanan

- Password admin di-hash dengan **bcrypt**
- Session cookie HTTP-only + SameSite=Lax
- CSRF protection di semua form (Flask-WTF)
- Role-based access (`@superadmin_required`)
- Endpoint sensor diproteksi API Key (Header `X-API-Key`)
- File upload divalidasi ekstensi & ukuran (default maks 5MB)

---

## Lisensi

© 2026 PPK Ormawa SPACE FT-UH.