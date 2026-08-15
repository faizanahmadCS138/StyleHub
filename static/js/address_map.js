let map, marker;
const defaultCenter = [31.5204, 74.3587]; // Lahore

function initMap() {
  map = L.map('map').setView(defaultCenter, 15);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(map);

  marker = L.marker(defaultCenter, { draggable: true }).addTo(map);

  marker.on('dragend', () => {
    const pos = marker.getLatLng();
    reverseGeocode(pos.lat, pos.lng);
  });

  map.on('click', (e) => {
    marker.setLatLng(e.latlng);
    reverseGeocode(e.latlng.lat, e.latlng.lng);
  });

  reverseGeocode(defaultCenter[0], defaultCenter[1]);
}

async function reverseGeocode(lat, lng) {
  const roundedLat = Number(lat).toFixed(6);
  const roundedLng = Number(lng).toFixed(6);
  document.getElementById('latitude').value = roundedLat;
  document.getElementById('longitude').value = roundedLng;

  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${roundedLat}&lon=${roundedLng}`,
      { headers: { 'Accept-Language': 'en' } }
    );
    const data = await res.json();
    if (data && data.display_name) {
      document.getElementById('streetAddress').value = data.display_name;
      document.getElementById('city').value =
        data.address.city || data.address.town || data.address.suburb || data.address.county || '';
    }
  } catch (err) {
    console.error('Reverse geocode failed:', err);
  }
}

let searchTimeout;
function setupSearch() {
  const input = document.getElementById('addressSearchInput');
  const resultsBox = document.getElementById('searchResults');

  input.addEventListener('input', () => {
    clearTimeout(searchTimeout);
    const query = input.value.trim();
    if (query.length < 3) {
      resultsBox.innerHTML = '';
      return;
    }
    searchTimeout = setTimeout(async () => {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&countrycodes=pk&limit=5`,
        { headers: { 'Accept-Language': 'en' } }
      );
      const results = await res.json();
      resultsBox.innerHTML = results.map(r =>
        `<div class="search-result-item" data-lat="${r.lat}" data-lon="${r.lon}">${r.display_name}</div>`
      ).join('');
    }, 400);
  });

  resultsBox.addEventListener('click', (e) => {
    const item = e.target.closest('.search-result-item');
    if (!item) return;
    const lat = parseFloat(item.dataset.lat);
    const lon = parseFloat(item.dataset.lon);
    map.setView([lat, lon], 17);
    marker.setLatLng([lat, lon]);
    reverseGeocode(lat, lon);
    resultsBox.innerHTML = '';
    input.value = item.textContent;
  });
}

function getCookie(name) {
  const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return match ? match.pop() : '';
}
document.getElementById('locateBtn')?.addEventListener('click', function (e) {
  e.preventDefault();
  e.stopPropagation();

  if (!navigator.geolocation) {
    alert('Geolocation is not supported by your browser.');
    return;
  }

  const btn = this;
  btn.disabled = true;
  btn.innerHTML = '<span>⏳</span> Locating...';

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const { latitude, longitude } = pos.coords;
      map.setView([latitude, longitude], 17);
      marker.setLatLng([latitude, longitude]);
      reverseGeocode(latitude, longitude);
      btn.disabled = false;
      btn.innerHTML = '<span>📍</span> Locate';
    },
    (err) => {
      console.error('Geolocation error:', err);
      let msg = 'Could not get your location.';
      if (err.code === err.PERMISSION_DENIED) {
        msg = 'Location access was denied. Enable it in your browser settings.';
      } else if (err.code === err.POSITION_UNAVAILABLE) {
        msg = 'Location is currently unavailable.';
      } else if (err.code === err.TIMEOUT) {
        msg = 'Location request timed out. Try again.';
      }
      alert(msg);
      btn.disabled = false;
      btn.innerHTML = '<span>📍</span> Locate';
    },
    { enableHighAccuracy: true, timeout: 10000 }
  );
});
document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('addAddressModal');

  document.getElementById('openAddAddressBtn')?.addEventListener('click', () => {
    modal.style.display = 'flex';
    if (!map) {
      initMap();
      setupSearch();
      setTimeout(() => map.invalidateSize(), 100);
    }
  });

  document.getElementById('closeAddressModal').addEventListener('click', () => modal.style.display = 'none');
  document.getElementById('cancelAddressBtn').addEventListener('click', () => modal.style.display = 'none');

  document.getElementById('addressForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      full_name: document.getElementById('fullName').value,
      phone_number: document.getElementById('phoneNumber').value,
      street_address: document.getElementById('streetAddress').value,
      apartment: document.getElementById('apartment').value,
      city: document.getElementById('city').value,
      latitude: document.getElementById('latitude').value,
      longitude: document.getElementById('longitude').value,
    };

    const res = await fetch('/accounts/addresses/add/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.success) {
      location.reload();
    } else {
      alert(data.error);
    }
  });

  document.querySelectorAll('.delete-address-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const res = await fetch(`/accounts/addresses/${btn.dataset.id}/delete/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
      });
      const data = await res.json();
      if (data.success) location.reload();
    });
  });

  document.querySelectorAll('.set-primary-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const res = await fetch(`/accounts/addresses/${btn.dataset.id}/set-primary/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
      });
      const data = await res.json();
      if (data.success) location.reload();
    });
  });
});