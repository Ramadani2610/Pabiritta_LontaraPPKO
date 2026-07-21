/**
 * Pa'Biritta — Peta interaktif Leaflet.
 * Dipakai di Beranda, Dashboard Admin & Super Admin.
 *
 * NOTE: Layer "kemiringan", "posko", "evakuasi", "titik kumpul"
 * masih placeholder (polygon contoh) — bisa diganti GeoJSON resmi nanti.
 */

function initPeta(elementId, opts = {}) {
  // Bounding box sekitar Desa Lonjoboko + Parangloe (padding kecil dari data PWK)
  const LONJOBOKO_BOUNDS = L.latLngBounds(
    [-5.300, 119.680],  // sudut barat daya
    [-5.220, 119.790],  // sudut timur laut
  );

  const map = L.map(elementId, {
    minZoom: 13,
    maxZoom: 18,
    maxBounds: LONJOBOKO_BOUNDS,
    maxBoundsViscosity: 1.0,  // 1.0 = tidak bisa digeser keluar sama sekali
  }).setView(opts.center || [-5.263, 119.735], opts.zoom || 14);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap',
    minZoom: 13,
    maxZoom: 19,
    bounds: LONJOBOKO_BOUNDS,  // tile hanya di-load di dalam area
  }).addTo(map);

  return map;
}

/** Layer-layer map yang bisa di-toggle */
const LAYERS = {};

/**
 * Helper: bikin blok foto untuk popup.
 * Kalau foto belum ada, tag <img> otomatis disembunyikan (onerror).
 * Taruh foto asli di: app/static/img/lokasi/<nama-file>.jpg
 */
function popupFoto(filename) {
  const src = `/static/img/lokasi/${filename}`;
  return `<img src="${src}" alt=""
            onerror="this.style.display='none'"
            style="width:100%;height:120px;object-fit:cover;border-radius:6px;margin-bottom:8px;display:block;">`;
}

async function fetchAndRenderLayers(map) {
  // ZONA RAWAN LONGSOR — dari data PWK (GeoJSON, WGS84)
  try {
    const res = await fetch('/static/data/kelas_rawan_longsor.geojson');
    const gj = await res.json();

const styleKelas = (kelas) => {
  // Palet: Tinggi = merah, Sedang = oranye, Rendah = kuning
  if (kelas === 'Tinggi') return { fillColor: '#DC2626', weight: 0, stroke: false, fillOpacity: 0.55 };
  if (kelas === 'Sedang') return { fillColor: '#F97316', weight: 0, stroke: false, fillOpacity: 0.45 };
  return                       { fillColor: '#EAB308', weight: 0, stroke: false, fillOpacity: 0.35 };
};

    LAYERS.zona = L.geoJSON(gj, {
      style: (feature) => styleKelas(feature.properties.Kelas),
      onEachFeature: (feature, layer) => {
        const p = feature.properties || {};
        layer.bindPopup(`
          <div style="min-width:160px;">
            <strong>Zona Rawan Longsor</strong><br>
            Kelas kerawanan: <b>${p.Kelas || '-'}</b><br>
            <span style="font-size:11px;color:#6b7280;">Sumber: Data PWK</span>
          </div>
        `);
      },
    });
  } catch (e) {
    console.warn('Gagal load zona rawan longsor:', e);
    LAYERS.zona = L.layerGroup();
  }

  LAYERS.kemiringan = L.layerGroup([
    L.polygon([
      [-5.258, 119.715],
      [-5.258, 119.728],
      [-5.268, 119.730],
      [-5.270, 119.717],
    ], { color: '#F97316', weight: 2, fillOpacity: 0.2 })
      .bindPopup('<strong>Zona Kemiringan Lereng</strong><br>Lereng curam sekitar Desa Lonjoboko'),
  ]);

  LAYERS.posko = L.layerGroup([
    L.circleMarker([-5.260, 119.722], { color: '#16A34A', fillColor: '#16A34A', fillOpacity: 0.9, radius: 8 })
      .bindPopup(`
        <div style="min-width:200px;">
          ${popupFoto('posko-balai-desa.jpg')}
          <strong>Posko Siaga Desa</strong><br>
          Balai Desa Lonjoboko<br>
          <a href="tel:08112233445" style="color:#DC2626;font-weight:600;">0811-2233-4455</a>
        </div>`),
    L.circleMarker([-5.253, 119.748], { color: '#16A34A', fillColor: '#16A34A', fillOpacity: 0.9, radius: 8 })
      .bindPopup(`
        <div style="min-width:200px;">
          ${popupFoto('puskesmas-parangloe.jpg')}
          <strong>Puskesmas Parangloe</strong><br>
          <a href="tel:08223344556" style="color:#DC2626;font-weight:600;">0822-3344-5566</a>
        </div>`),
    L.circleMarker([-5.275, 119.760], { color: '#16A34A', fillColor: '#16A34A', fillOpacity: 0.9, radius: 8 })
      .bindPopup(`
        <div style="min-width:200px;">
          ${popupFoto('bpbd-gowa.jpg')}
          <strong>Pos BPBD Kab. Gowa</strong><br>
          Hotline: <a href="tel:112" style="color:#DC2626;font-weight:600;">112</a>
        </div>`),
  ]);

  LAYERS.evakuasi = L.layerGroup([
    L.polyline(
      [[-5.268, 119.720], [-5.263, 119.728], [-5.258, 119.738], [-5.255, 119.748]],
      { color: '#374151', weight: 4, dashArray: '6, 8' })
      .bindPopup('<strong>Jalur Evakuasi</strong><br>Menuju titik kumpul dan puskesmas'),
    L.polyline(
      [[-5.272, 119.750], [-5.268, 119.755], [-5.263, 119.755]],
      { color: '#374151', weight: 4, dashArray: '6, 8' })
      .bindPopup('<strong>Jalur Evakuasi</strong><br>Menuju pos BPBD'),
  ]);

  LAYERS.kumpul = L.layerGroup([
    L.circleMarker([-5.255, 119.746], { color: '#10B981', fillColor: '#10B981', fillOpacity: 0.9, radius: 8 })
      .bindPopup(`
        <div style="min-width:200px;">
          ${popupFoto('titik-kumpul-lapangan.jpg')}
          <strong>Titik Kumpul Utama</strong><br>
          Lapangan Desa Parangloe
        </div>`),
    L.circleMarker([-5.263, 119.720], { color: '#10B981', fillColor: '#10B981', fillOpacity: 0.9, radius: 8 })
      .bindPopup(`
        <div style="min-width:200px;">
          ${popupFoto('titik-kumpul-balai.jpg')}
          <strong>Titik Kumpul Cadangan</strong><br>
          Halaman Balai Desa Lonjoboko
        </div>`),
  ]);

  // SENSOR IoT (live)
  try {
    const res = await fetch('/api/sensor/list');
    const data = await res.json();
    LAYERS.sensor = L.layerGroup(
      data.map(s => {
        const color = s.status === 'Bahaya' ? '#B91C1C'
                    : s.status === 'Waspada' ? '#EAB308'
                    : '#DC2626';
        return L.circleMarker([s.latitude, s.longitude], {
          radius: 9, color, fillColor: color, fillOpacity: 0.85, weight: 2,
        }).bindPopup(`
          <strong>${s.kode} — ${s.nama_lokasi}</strong><br>
          Status: <b>${s.status}</b><br>
          Kelembapan: ${s.kelembapan ?? '-'}%<br>
          Getaran: ${s.getaran ?? '-'}
        `);
      })
    );
  } catch (e) {
    LAYERS.sensor = L.layerGroup();
  }

  // PERSEBARAN TITIK LONGSOR (laporan warga)
  try {
    const res = await fetch('/api/sensor/laporan-titik');
    const data = await res.json();
    const valid = data.filter(l => l.latitude != null && l.longitude != null);
    const markers = valid.map(l => {
      const foto = l.foto_url
        ? `<img src="${l.foto_url}" alt=""
             style="width:100%;height:120px;object-fit:cover;border-radius:6px;margin-bottom:8px;display:block;">`
        : '';
      return L.circleMarker([l.latitude, l.longitude], {
        radius: 7, color: '#2563EB', fillColor: '#2563EB', fillOpacity: 0.8, weight: 2,
      }).bindPopup(`
        <div style="min-width:200px;">
          ${foto}
          <strong>${l.lokasi_label}</strong><br>
          ${l.kategori}<br>
          Status: <b>${l.status}</b><br>
          <a href="/laporan/${l.id}" style="color:#DC2626;font-weight:600;">Lihat Detail →</a>
        </div>
      `);
    });
    LAYERS.laporan = L.layerGroup(markers);
  } catch (e) {
    LAYERS.laporan = L.layerGroup();
  }

  // Hubungkan checkbox ke layer
  document.querySelectorAll('[data-layer]').forEach(cb => {
    const key = cb.dataset.layer;
    if (!LAYERS[key]) return;
    if (cb.checked) LAYERS[key].addTo(map);
    cb.addEventListener('change', () => {
      if (cb.checked) LAYERS[key].addTo(map);
      else map.removeLayer(LAYERS[key]);
    });
  });

  // Popup sambutan
  setTimeout(() => map.invalidateSize(), 200);
}