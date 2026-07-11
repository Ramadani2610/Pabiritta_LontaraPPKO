/**
 * Pa'Biritta — Peta interaktif Leaflet.
 * Dipakai di Beranda, Dashboard Admin & Super Admin.
 *
 * NOTE: Layer "zona rawan", "kemiringan", "posko", "evakuasi", "titik kumpul"
 * masih placeholder (polygon contoh) — bisa diganti GeoJSON resmi nanti.
 */

const LONJOBOKO_BOUNDS = L.latLngBounds([-5.34, 119.44], [-5.21, 119.54]);

function initPeta(elementId, opts = {}) {
  const map = L.map(elementId, {
    maxBounds: LONJOBOKO_BOUNDS,
    maxBoundsViscosity: 0.9,
    minZoom: 12,
  }).setView(opts.center || [-5.275, 119.488], opts.zoom || 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap',
    maxZoom: 19,
  }).addTo(map);
  return map;
}

/** Layer-layer map yang bisa di-toggle */
const LAYERS = {};

async function fetchAndRenderLayers(map) {
  // ZONA RAWAN LONGSOR (placeholder polygon)
  LAYERS.zona = L.layerGroup([
    L.polygon([
      [-5.262, 119.475],
      [-5.258, 119.483],
      [-5.268, 119.487],
      [-5.270, 119.478],
    ], { color: '#DC2626', weight: 2, fillOpacity: 0.25 })
      .bindPopup('<strong>Zona Rawan Longsor</strong><br>Dusun Galesong'),
  ]);

  LAYERS.kemiringan = L.layerGroup([
    L.polygon([
      [-5.286, 119.487],
      [-5.282, 119.499],
      [-5.293, 119.503],
      [-5.297, 119.491],
    ], { color: '#F97316', weight: 2, fillOpacity: 0.2 })
      .bindPopup('<strong>Zona Kemiringan Lereng</strong>'),
  ]);

  LAYERS.posko = L.layerGroup([
    L.circleMarker([-5.278, 119.495], { color: '#16A34A', fillColor: '#16A34A', fillOpacity: 0.9, radius: 8 })
      .bindPopup('<strong>Posko Siaga</strong><br>Balai Desa'),
  ]);

  LAYERS.evakuasi = L.layerGroup([
    L.polyline([[-5.265, 119.482], [-5.270, 119.488], [-5.278, 119.495]],
      { color: '#374151', weight: 4, dashArray: '6, 8' })
      .bindPopup('<strong>Jalur Evakuasi</strong>'),
  ]);

  LAYERS.kumpul = L.layerGroup([
    L.circleMarker([-5.279, 119.497], { color: '#10B981', fillColor: '#10B981', fillOpacity: 0.9, radius: 8 })
      .bindPopup('<strong>Titik Kumpul</strong><br>Lapangan Desa'),
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

  // PERSEBARAN TITIK LONGSOR (laporan)
  try {
    const res = await fetch('/api/sensor/laporan-titik');
    const data = await res.json();
    LAYERS.laporan = L.layerGroup(
      data.map(l => L.circleMarker([l.latitude, l.longitude], {
        radius: 7, color: '#2563EB', fillColor: '#2563EB', fillOpacity: 0.8, weight: 2,
      }).bindPopup(`<strong>${l.lokasi_label}</strong><br>${l.kategori}<br>Status: ${l.status}`))
    );
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