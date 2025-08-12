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
      <div style="position: relative; width: 100%; height: 100%; background: linear-gradient(180deg, #87CEEB 0%, #98FB98 100%); overflow: hidden; border-radius: 8px;">
        <div style="position: absolute; inset: 0; background-image: 
          radial-gradient(2px 2px at 20px 30px, #87CEEB, transparent),
          radial-gradient(2px 2px at 40px 70px, rgba(255,255,255,0.1), transparent),
          radial-gradient(1px 1px at 90px 40px, rgba(255,255,255,0.1), transparent),
          radial-gradient(1px 1px at 130px 80px, rgba(255,255,255,0.1), transparent),
          radial-gradient(2px 2px at 160px 30px, rgba(255,255,255,0.1), transparent);
          background-repeat: repeat;
          background-size: 200px 100px;">
        </div>
        <div class="map-markers" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></div>
        <div class="leaflet-control leaflet-control-zoom" style="position: absolute; top: 10px; left: 10px; z-index: 1000;">
          <a class="leaflet-control-zoom-in" href="#" onclick="return false;" style="display: block; width: 30px; height: 30px; line-height: 30px; text-align: center; text-decoration: none; color: #333; background: white; border: 1px solid #ccc; border-bottom: none; font-weight: bold; font-size: 18px;">+</a>
          <a class="leaflet-control-zoom-out" href="#" onclick="return false;" style="display: block; width: 30px; height: 30px; line-height: 30px; text-align: center; text-decoration: none; color: #333; background: white; border: 1px solid #ccc; font-weight: bold; font-size: 18px;">−</a>
        </div>
        <div class="leaflet-control-attribution" style="position: absolute; bottom: 0; right: 0; background: rgba(255,255,255,0.7); padding: 2px 4px; font-size: 11px; border-radius: 2px;">
          © OpenStreetMap contributors
        </div>
        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(59, 130, 246, 0.1); border: 2px solid #3b82f6; border-radius: 50%; width: 20px; height: 20px; animation: pulse 2s infinite;"></div>
      </div>
      <style>
        @keyframes pulse {
          0% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
          70% { transform: translate(-50%, -50%) scale(1.5); opacity: 0.5; }
          100% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
        }
      </style>
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