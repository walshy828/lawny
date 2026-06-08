/** Lawn Map Page — Leaflet with satellite view and zone drawing */
const LawnMapPage = {
  map: null,
  drawnItems: null,
  zones: [],

  async render(container) {
    container.innerHTML = `
      <div class="section-header anim-fade-in">
        <h1 class="section-title">🗺️ Lawn Map</h1>
        <button class="btn btn-ghost btn-sm" id="calcBtn">📐 Calculator</button>
      </div>

      <div class="map-search anim-fade-in-up anim-delay-1">
        <span class="map-search-icon">🔍</span>
        <input type="text" class="map-search-input" id="mapSearch" placeholder="Search address to center map...">
      </div>

      <div id="mapNotice" class="anim-fade-in-up anim-delay-1" style="display:none"></div>

      <div class="map-container anim-fade-in-up anim-delay-2" id="mapContainer"></div>

      <div class="section-header"><span class="section-title">Zones</span></div>
      <div class="zone-list" id="zoneList">
        <div class="text-muted text-center" style="padding:var(--space-lg)">Loading zones...</div>
      </div>
    `;

    await this._initMap();
    await this._loadZones();
    this._bindEvents();
  },

  async _initMap() {
    // Default center (US)
    let center = [39.8283, -98.5795];
    let zoom = 4;
    const noticeEl = document.getElementById('mapNotice');

    try {
      const lawn = await API.getLawn();
      if (lawn && lawn.latitude && lawn.longitude) {
        center = [lawn.latitude, lawn.longitude];
        zoom = 19;
        // Pre-fill search bar with configured address
        if (lawn.address) {
          document.getElementById('mapSearch').value = lawn.address;
        }
      } else {
        // Show setup notice
        if (noticeEl) {
          noticeEl.style.display = 'block';
          noticeEl.innerHTML = `
            <div class="card" style="text-align:center;padding:var(--space-lg);border-color:var(--color-warning);border-style:dashed">
              <div style="font-size:1.5rem;margin-bottom:var(--space-sm)">📍</div>
              <div style="font-weight:var(--fw-semibold);margin-bottom:var(--space-xs)">No lawn location set</div>
              <div class="text-muted" style="font-size:var(--fs-sm);margin-bottom:var(--space-md)">Set your address in Settings to center the map, or search an address above.</div>
              <button class="btn btn-secondary btn-sm" onclick="App.navigate('settings')">Go to Settings</button>
            </div>`;
        }
      }
    } catch (e) {}

    this.map = L.map('mapContainer', { zoomControl: true }).setView(center, zoom);

    // Satellite tiles (Esri — free, no API key)
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: '&copy; Esri',
      maxZoom: 22,
    }).addTo(this.map);

    // Drawing layer
    this.drawnItems = new L.FeatureGroup();
    this.map.addLayer(this.drawnItems);

    // Drawing controls
    const drawControl = new L.Control.Draw({
      edit: { featureGroup: this.drawnItems },
      draw: {
        polygon: { allowIntersection: false, shapeOptions: { color: '#52B788', weight: 2, fillOpacity: 0.25 } },
        polyline: false, rectangle: false, circle: false, circlemarker: false, marker: false,
      },
    });
    this.map.addControl(drawControl);

    // Handle new polygon drawn
    this.map.on(L.Draw.Event.CREATED, async (e) => {
      const layer = e.layer;
      const coords = layer.getLatLngs()[0].map(ll => ({ lat: ll.lat, lng: ll.lng }));

      const name = await Modal.prompt({ title: 'Name This Zone', placeholder: 'e.g., Front Yard, Side Strip', confirmText: 'Create Zone' });
      if (!name) return;

      try {
        const zone = await API.createZone({ name, polygon_coords: coords, color: this._randomColor() });
        Toast.success(`${name} created — ${Fmt.sqft(zone.area_sqft)}`);
        await this._loadZones();
      } catch (err) { Toast.error(err.message); }
    });

    // Handle polygon edit
    this.map.on(L.Draw.Event.EDITED, async (e) => {
      const layers = e.layers;
      layers.eachLayer(async (layer) => {
        const zoneId = layer.options.zoneId;
        if (!zoneId) return;
        const coords = layer.getLatLngs()[0].map(ll => ({ lat: ll.lat, lng: ll.lng }));
        try {
          await API.updateZone(zoneId, { polygon_coords: coords });
          Toast.success('Zone updated');
          await this._loadZones();
        } catch (err) { Toast.error(err.message); }
      });
    });

    // Handle polygon delete
    this.map.on(L.Draw.Event.DELETED, async (e) => {
      const layers = e.layers;
      layers.eachLayer(async (layer) => {
        const zoneId = layer.options.zoneId;
        if (!zoneId) return;
        try {
          await API.deleteZone(zoneId);
          Toast.success('Zone deleted');
          await this._loadZones();
        } catch (err) { Toast.error(err.message); }
      });
    });

    // Fix Leaflet rendering in SPA
    setTimeout(() => this.map.invalidateSize(), 100);
  },

  async _loadZones() {
    try {
      this.zones = await API.getZones();

      // Clear existing polygons
      this.drawnItems.clearLayers();

      // Add zones to map
      this.zones.forEach(z => {
        if (!z.polygon_coords || z.polygon_coords.length < 3) return;
        const latlngs = z.polygon_coords.map(p => [p.lat, p.lng]);
        const polygon = L.polygon(latlngs, {
          color: z.color || '#52B788',
          weight: 2,
          fillOpacity: 0.25,
          zoneId: z.id,
        });
        polygon.bindPopup(`
          <div class="zone-popup">
            <h3>${z.name}</h3>
            <div class="zone-area">${Fmt.sqft(z.area_sqft)}</div>
            <div class="zone-meta">${z.notes || ''}</div>
          </div>
        `);
        this.drawnItems.addLayer(polygon);
      });

      // Render zone list
      const listEl = document.getElementById('zoneList');
      if (!this.zones.length) {
        listEl.innerHTML = `<div class="text-muted text-center" style="padding:var(--space-lg)">Draw polygons on the map to create lawn zones.</div>`;
        return;
      }

      const totalSqft = this.zones.reduce((sum, z) => sum + (z.area_sqft || 0), 0);
      listEl.innerHTML = this.zones.map(z => `
        <div class="zone-item" onclick="LawnMapPage._focusZone(${z.id})">
          <div class="zone-color-dot" style="background:${z.color || '#52B788'}"></div>
          <div class="zone-item-info">
            <div class="zone-item-name">${z.name}</div>
            <div class="zone-item-area">${Fmt.sqft(z.area_sqft)}</div>
          </div>
          <div class="zone-item-actions">
            <button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();LawnMapPage._deleteZone(${z.id},'${z.name}')">🗑️</button>
          </div>
        </div>
      `).join('') + `
        <div style="text-align:center;padding:var(--space-md);color:var(--text-accent);font-weight:var(--fw-semibold)">
          Total: ${Fmt.sqft(totalSqft)}
        </div>`;

    } catch (e) { console.error('Load zones:', e); }
  },

  _focusZone(id) {
    this.drawnItems.eachLayer(layer => {
      if (layer.options.zoneId === id) {
        this.map.fitBounds(layer.getBounds(), { padding: [50, 50] });
        layer.openPopup();
      }
    });
  },

  async _deleteZone(id, name) {
    if (!await Modal.confirm({ title: `Delete "${name}"?`, message: 'This zone and its area data will be permanently removed.', confirmText: 'Delete Zone', variant: 'danger' })) return;
    try {
      await API.deleteZone(id);
      Toast.success('Zone deleted');
      await this._loadZones();
    } catch (e) { Toast.error(e.message); }
  },

  _bindEvents() {
    const searchInput = document.getElementById('mapSearch');

    // Address search with visual feedback
    searchInput.addEventListener('keyup', async (e) => {
      if (e.key !== 'Enter') return;
      const query = searchInput.value.trim();
      if (!query) return;

      searchInput.disabled = true;
      searchInput.style.borderColor = 'var(--color-accent)';

      try {
        const result = await API.geocode(query);
        if (result) {
          this.map.setView([result.latitude, result.longitude], 19);
          // Also update lawn location
          await API.updateLawn({ latitude: result.latitude, longitude: result.longitude, address: query });

          // Add a temporary marker
          const marker = L.marker([result.latitude, result.longitude]).addTo(this.map);
          marker.bindPopup(`<div style="text-align:center;font-size:12px;color:#333"><strong>📍 ${result.display_name || query}</strong></div>`).openPopup();
          setTimeout(() => this.map.removeLayer(marker), 10000);

          // Hide the setup notice if visible
          const noticeEl = document.getElementById('mapNotice');
          if (noticeEl) noticeEl.style.display = 'none';

          Toast.success(`Map centered on: ${result.display_name || query}`);
        } else {
          Toast.error('Address not found. Try a more specific address.');
        }
      } catch (err) {
        Toast.error('Address lookup failed');
      }

      searchInput.disabled = false;
      searchInput.style.borderColor = '';
    });

    // Calculator button
    document.getElementById('calcBtn').addEventListener('click', () => this._showCalculator());
  },

  _showCalculator() {
    const zoneOptions = this.zones.map(z =>
      `<option value="${z.area_sqft}">${z.name} (${Fmt.sqft(z.area_sqft)})</option>`
    ).join('');

    Modal.show('📐 Product Calculator', `
      <div class="calc-section">
        <div class="form-group">
          <label class="form-label">Select Zone</label>
          <select class="form-select" id="calcZone">
            <option value="">Choose a zone...</option>
            ${zoneOptions}
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Product Rate (lbs per 1,000 sqft)</label>
          <input type="number" class="form-input" id="calcRate" step="0.1" placeholder="e.g., 4.0">
        </div>
        <button class="btn btn-primary btn-block" onclick="LawnMapPage._calculate()">Calculate</button>
        <div class="calc-result" id="calcResult"></div>
      </div>
    `);
  },

  _calculate() {
    const area = parseFloat(document.getElementById('calcZone').value);
    const rate = parseFloat(document.getElementById('calcRate').value);
    if (!area || !rate) { Toast.warning('Select a zone and enter a rate'); return; }
    const total = (area / 1000) * rate;
    document.getElementById('calcResult').textContent = `You need ${total.toFixed(1)} lbs`;
  },

  _randomColor() {
    const colors = ['#52B788', '#74C69D', '#40C057', '#339AF0', '#CC5DE8', '#FAB005', '#FF6B6B', '#20C997', '#845EF7'];
    return colors[Math.floor(Math.random() * colors.length)];
  },
};
