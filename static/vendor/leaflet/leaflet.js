/* Leaflet JS - Minimal implementation for LXCloud */
(function() {
  'use strict';

  // Minimal Leaflet implementation
  window.L = {
    map: function(id, options) {
      return new LeafletMap(id, options);
    },
    
    tileLayer: function(url, options) {
      return new TileLayer(url, options);
    },
    
    marker: function(latlng, options) {
      return new Marker(latlng, options);
    },
    
    divIcon: function(options) {
      return new DivIcon(options);
    }
  };

  // Map class
  function LeafletMap(id, options) {
    this.container = document.getElementById(id);
    this.options = options || {};
    this.center = this.options.center || [52.3676, 4.9041];
    this.zoom = this.options.zoom || 8;
    this.markers = [];
    this.layers = [];
    
    this._initMap();
  }

  LeafletMap.prototype._initMap = function() {
    this.container.innerHTML = `
      <div style="position: relative; width: 100%; height: 100%; background: #a8d8f0; overflow: hidden;">
        <div style="position: absolute; top: 10px; left: 50%; transform: translateX(-50%); background: rgba(255,255,255,0.9); padding: 8px 12px; border-radius: 4px; font-size: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
          Map View (Lat: ${this.center[0].toFixed(4)}, Lng: ${this.center[1].toFixed(4)})
        </div>
        <div class="map-markers" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></div>
        <div class="leaflet-control leaflet-control-zoom" style="position: absolute; top: 10px; left: 10px;">
          <a class="leaflet-control-zoom-in" href="#" onclick="return false;">+</a>
          <a class="leaflet-control-zoom-out" href="#" onclick="return false;">−</a>
        </div>
        <div class="leaflet-control-attribution" style="position: absolute; bottom: 0; right: 0;">
          © OpenStreetMap contributors
        </div>
      </div>
    `;
    
    this.markersContainer = this.container.querySelector('.map-markers');
  };

  LeafletMap.prototype.addTo = function(layer) {
    // For tile layers, we just note that they're added
    return this;
  };

  LeafletMap.prototype.setView = function(center, zoom) {
    this.center = center;
    this.zoom = zoom;
    return this;
  };

  // Tile Layer class
  function TileLayer(url, options) {
    this.url = url;
    this.options = options || {};
  }

  TileLayer.prototype.addTo = function(map) {
    return this;
  };

  // Marker class
  function Marker(latlng, options) {
    this.latlng = latlng;
    this.options = options || {};
    this._popup = null;
  }

  Marker.prototype.addTo = function(map) {
    this.map = map;
    this._createElement();
    return this;
  };

  Marker.prototype._createElement = function() {
    var markerEl = document.createElement('div');
    markerEl.style.position = 'absolute';
    markerEl.style.zIndex = '1000';
    
    // Calculate position (simplified - center of map area)
    var containerRect = this.map.markersContainer.getBoundingClientRect();
    var x = containerRect.width / 2 + (Math.random() - 0.5) * 200; // Spread markers around
    var y = containerRect.height / 2 + (Math.random() - 0.5) * 200;
    
    markerEl.style.left = Math.max(0, Math.min(containerRect.width - 30, x)) + 'px';
    markerEl.style.top = Math.max(0, Math.min(containerRect.height - 30, y)) + 'px';
    
    if (this.options.icon && this.options.icon.options) {
      var iconOpts = this.options.icon.options;
      markerEl.innerHTML = iconOpts.html || '';
      markerEl.className = iconOpts.className || 'custom-div-icon';
      if (iconOpts.iconSize) {
        markerEl.style.width = iconOpts.iconSize[0] + 'px';
        markerEl.style.height = iconOpts.iconSize[1] + 'px';
      }
    } else {
      markerEl.innerHTML = '📍';
      markerEl.style.fontSize = '20px';
    }
    
    markerEl.style.cursor = 'pointer';
    
    var self = this;
    markerEl.addEventListener('click', function() {
      if (self._popup) {
        self._showPopup();
      }
    });
    
    this._element = markerEl;
    this.map.markersContainer.appendChild(markerEl);
  };

  Marker.prototype.bindPopup = function(content) {
    this._popup = content;
    return this;
  };

  Marker.prototype._showPopup = function() {
    // Remove existing popups
    var existingPopups = this.map.container.querySelectorAll('.leaflet-popup');
    existingPopups.forEach(function(popup) {
      popup.remove();
    });
    
    var popup = document.createElement('div');
    popup.className = 'leaflet-popup';
    popup.innerHTML = `
      <div class="leaflet-popup-content-wrapper">
        <div class="leaflet-popup-content">${this._popup}</div>
      </div>
      <div class="leaflet-popup-tip"></div>
      <a class="leaflet-popup-close-button" href="#" onclick="this.parentElement.remove(); return false;">×</a>
    `;
    
    var rect = this._element.getBoundingClientRect();
    var containerRect = this.map.container.getBoundingClientRect();
    
    popup.style.left = (rect.left - containerRect.left) + 'px';
    popup.style.top = (rect.top - containerRect.top - 100) + 'px';
    
    this.map.container.appendChild(popup);
  };

  // DivIcon class
  function DivIcon(options) {
    this.options = options || {};
  }

})();