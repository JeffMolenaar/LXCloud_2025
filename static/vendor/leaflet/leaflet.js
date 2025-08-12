/* Interactive Map Implementation for LXCloud */
(function() {
  'use strict';

  // Enhanced map implementation with full interactivity
  window.L = {
    map: function(id, options) {
      return new InteractiveMap(id, options);
    },
    
    tileLayer: function(url, options) {
      return new TileLayer(url, options);
    },
    
    marker: function(latlng, options) {
      return new Marker(latlng, options);
    },
    
    divIcon: function(options) {
      return new DivIcon(options);
    },
    
    featureGroup: function() {
      return new FeatureGroup();
    }
  };

  // Interactive Map class with full zoom, pan, and click functionality
  function InteractiveMap(id, options) {
    this.container = document.getElementById(id);
    this.options = options || {};
    this.center = this.options.center || [52.3676, 4.9041];
    this.zoom = this.options.zoom || 8;
    this.minZoom = 1;
    this.maxZoom = 18;
    this.markers = [];
    this.layers = [];
    this.isDragging = false;
    this.dragStart = { x: 0, y: 0 };
    this.mapOffset = { x: 0, y: 0 };
    this.tileLayer = null;
    
    this._initMap();
    this._bindEvents();
  }

  InteractiveMap.prototype._initMap = function() {
    this.container.innerHTML = `
      <div class="map-viewport" style="position: relative; width: 100%; height: 100%; overflow: hidden; border-radius: 8px; background: #a0cce8; cursor: grab;">
        <div class="map-tiles" style="position: absolute; width: 100%; height: 100%; background: linear-gradient(180deg, #87CEEB 0%, #98FB98 100%); transition: transform 0.1s ease-out;">
          <div class="tile-grid" style="position: absolute; top: 0; left: 0; width: 200%; height: 200%; opacity: 0.3; background-image: repeating-linear-gradient(0deg, rgba(255,255,255,0.1), rgba(255,255,255,0.1) 1px, transparent 1px, transparent 50px), repeating-linear-gradient(90deg, rgba(255,255,255,0.1), rgba(255,255,255,0.1) 1px, transparent 1px, transparent 50px);"></div>
        </div>
        <div class="map-markers" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;"></div>
        <div class="leaflet-control leaflet-control-zoom" style="position: absolute; top: 10px; left: 10px; z-index: 1000; background: white; border-radius: 4px; box-shadow: 0 1px 5px rgba(0,0,0,0.4);">
          <a class="leaflet-control-zoom-in" href="#" style="display: block; width: 30px; height: 30px; line-height: 28px; text-align: center; text-decoration: none; color: #333; background: white; border: none; border-bottom: 1px solid #ccc; font-weight: bold; font-size: 18px; border-top-left-radius: 4px; border-top-right-radius: 4px;">+</a>
          <a class="leaflet-control-zoom-out" href="#" style="display: block; width: 30px; height: 30px; line-height: 30px; text-align: center; text-decoration: none; color: #333; background: white; border: none; font-weight: bold; font-size: 18px; border-bottom-left-radius: 4px; border-bottom-right-radius: 4px;">−</a>
        </div>
        <div class="leaflet-control-attribution" style="position: absolute; bottom: 2px; right: 2px; background: rgba(255,255,255,0.8); padding: 2px 6px; font-size: 11px; border-radius: 3px; color: #333;">
          © OpenStreetMap contributors
        </div>
        <div class="map-info" style="position: absolute; top: 10px; right: 10px; background: rgba(255,255,255,0.9); padding: 5px 8px; border-radius: 4px; font-size: 12px; color: #333; pointer-events: none;">
          Zoom: <span class="zoom-level">${this.zoom}</span>
        </div>
      </div>
    `;
    
    this.viewport = this.container.querySelector('.map-viewport');
    this.tilesContainer = this.container.querySelector('.map-tiles');
    this.markersContainer = this.container.querySelector('.map-markers');
    this.zoomInBtn = this.container.querySelector('.leaflet-control-zoom-in');
    this.zoomOutBtn = this.container.querySelector('.leaflet-control-zoom-out');
    this.zoomLevelDisplay = this.container.querySelector('.zoom-level');
    
    this._updateMapView();
  };

  InteractiveMap.prototype._bindEvents = function() {
    var self = this;
    
    // Zoom controls
    this.zoomInBtn.addEventListener('click', function(e) {
      e.preventDefault();
      self.zoomIn();
    });
    
    this.zoomOutBtn.addEventListener('click', function(e) {
      e.preventDefault();
      self.zoomOut();
    });
    
    // Mouse wheel zoom
    this.viewport.addEventListener('wheel', function(e) {
      e.preventDefault();
      var delta = e.deltaY > 0 ? -1 : 1;
      if (delta > 0) {
        self.zoomIn();
      } else {
        self.zoomOut();
      }
    });
    
    // Pan functionality
    this.viewport.addEventListener('mousedown', function(e) {
      if (e.button === 0) { // Left mouse button
        self.isDragging = true;
        self.dragStart.x = e.clientX - self.mapOffset.x;
        self.dragStart.y = e.clientY - self.mapOffset.y;
        self.viewport.style.cursor = 'grabbing';
        e.preventDefault();
      }
    });
    
    document.addEventListener('mousemove', function(e) {
      if (self.isDragging) {
        self.mapOffset.x = e.clientX - self.dragStart.x;
        self.mapOffset.y = e.clientY - self.dragStart.y;
        
        // Limit panning to reasonable bounds
        var maxOffset = 200;
        self.mapOffset.x = Math.max(-maxOffset, Math.min(maxOffset, self.mapOffset.x));
        self.mapOffset.y = Math.max(-maxOffset, Math.min(maxOffset, self.mapOffset.y));
        
        self._updateMapView();
      }
    });
    
    document.addEventListener('mouseup', function(e) {
      if (self.isDragging) {
        self.isDragging = false;
        self.viewport.style.cursor = 'grab';
      }
    });
    
    // Touch events for mobile
    this.viewport.addEventListener('touchstart', function(e) {
      if (e.touches.length === 1) {
        var touch = e.touches[0];
        self.isDragging = true;
        self.dragStart.x = touch.clientX - self.mapOffset.x;
        self.dragStart.y = touch.clientY - self.mapOffset.y;
        e.preventDefault();
      }
    });
    
    this.viewport.addEventListener('touchmove', function(e) {
      if (self.isDragging && e.touches.length === 1) {
        var touch = e.touches[0];
        self.mapOffset.x = touch.clientX - self.dragStart.x;
        self.mapOffset.y = touch.clientY - self.dragStart.y;
        
        var maxOffset = 200;
        self.mapOffset.x = Math.max(-maxOffset, Math.min(maxOffset, self.mapOffset.x));
        self.mapOffset.y = Math.max(-maxOffset, Math.min(maxOffset, self.mapOffset.y));
        
        self._updateMapView();
        e.preventDefault();
      }
    });
    
    this.viewport.addEventListener('touchend', function(e) {
      self.isDragging = false;
    });
    
    // Double-click to zoom in
    this.viewport.addEventListener('dblclick', function(e) {
      e.preventDefault();
      self.zoomIn();
    });
  };

  InteractiveMap.prototype._updateMapView = function() {
    var scale = Math.pow(2, this.zoom - 8); // Base scale at zoom 8
    var transform = `translate(${this.mapOffset.x}px, ${this.mapOffset.y}px) scale(${scale})`;
    
    this.tilesContainer.style.transform = transform;
    this.markersContainer.style.transform = transform;
    
    if (this.zoomLevelDisplay) {
      this.zoomLevelDisplay.textContent = this.zoom;
    }
    
    // Update zoom control states
    this.zoomInBtn.style.opacity = this.zoom >= this.maxZoom ? '0.5' : '1';
    this.zoomOutBtn.style.opacity = this.zoom <= this.minZoom ? '0.5' : '1';
  };

  InteractiveMap.prototype.setView = function(center, zoom) {
    this.center = center;
    this.zoom = Math.max(this.minZoom, Math.min(this.maxZoom, zoom));
    this._updateMapView();
    return this;
  };

  InteractiveMap.prototype.zoomIn = function() {
    if (this.zoom < this.maxZoom) {
      this.zoom++;
      this._updateMapView();
    }
  };

  InteractiveMap.prototype.zoomOut = function() {
    if (this.zoom > this.minZoom) {
      this.zoom--;
      this._updateMapView();
    }
  };

  InteractiveMap.prototype.fitBounds = function(bounds, options) {
    // Simple implementation - just ensure we're at a reasonable zoom
    this.zoom = Math.max(6, Math.min(12, this.zoom));
    this._updateMapView();
    return this;
  };

  InteractiveMap.prototype.invalidateSize = function() {
    // Re-render the map after container size changes
    setTimeout(() => {
      this._updateMapView();
    }, 10);
    return this;
  };

  // Tile Layer class
  function TileLayer(url, options) {
    this.url = url;
    this.options = options || {};
  }

  TileLayer.prototype.addTo = function(map) {
    map.tileLayer = this;
    return this;
  };

  // Enhanced Marker class
  function Marker(latlng, options) {
    this.latlng = latlng;
    this.options = options || {};
    this._popup = null;
    this._element = null;
    this.map = null;
  }

  Marker.prototype.addTo = function(map) {
    this.map = map;
    map.markers.push(this);
    this._createElement();
    return this;
  };

  Marker.prototype._createElement = function() {
    var markerEl = document.createElement('div');
    markerEl.style.position = 'absolute';
    markerEl.style.zIndex = '1000';
    markerEl.style.pointerEvents = 'auto';
    markerEl.style.transform = 'translate(-50%, -50%)';
    
    // Convert lat/lng to pixel position (simplified projection)
    var pos = this._latLngToPixel(this.latlng);
    markerEl.style.left = pos.x + 'px';
    markerEl.style.top = pos.y + 'px';
    
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
      markerEl.style.fontSize = '24px';
      markerEl.style.filter = 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))';
    }
    
    markerEl.style.cursor = 'pointer';
    markerEl.style.transition = 'transform 0.2s ease';
    
    // Hover effects
    markerEl.addEventListener('mouseenter', function() {
      markerEl.style.transform = 'translate(-50%, -50%) scale(1.1)';
    });
    
    markerEl.addEventListener('mouseleave', function() {
      markerEl.style.transform = 'translate(-50%, -50%) scale(1)';
    });
    
    var self = this;
    markerEl.addEventListener('click', function(e) {
      e.stopPropagation();
      if (self._popup) {
        self._showPopup();
      }
    });
    
    this._element = markerEl;
    this.map.markersContainer.appendChild(markerEl);
  };

  Marker.prototype._latLngToPixel = function(latlng) {
    // Simplified projection - distribute markers in the container area
    var containerRect = this.map.markersContainer.getBoundingClientRect();
    var lat = latlng[0];
    var lng = latlng[1];
    
    // Use a simple linear projection for demo purposes
    // In a real implementation, this would use proper map projection math
    var x = ((lng + 180) / 360) * containerRect.width;
    var y = ((90 - lat) / 180) * containerRect.height;
    
    return { x: x, y: y };
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
    popup.style.position = 'absolute';
    popup.style.zIndex = '1001';
    popup.style.pointerEvents = 'auto';
    popup.innerHTML = `
      <div class="leaflet-popup-content-wrapper" style="background: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); padding: 1px; margin-bottom: 12px;">
        <div class="leaflet-popup-content" style="margin: 15px 20px; line-height: 1.4; color: #333;">${this._popup}</div>
        <a class="leaflet-popup-close-button" href="#" style="position: absolute; top: 8px; right: 8px; width: 20px; height: 20px; text-align: center; line-height: 18px; text-decoration: none; color: #999; font-size: 16px; font-weight: bold; background: none; border: none; cursor: pointer;">&times;</a>
      </div>
      <div class="leaflet-popup-tip" style="background: white; width: 12px; height: 12px; transform: rotate(45deg); margin: -6px auto 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"></div>
    `;
    
    // Position popup above the marker
    var markerRect = this._element.getBoundingClientRect();
    var containerRect = this.map.container.getBoundingClientRect();
    
    var popupX = markerRect.left - containerRect.left;
    var popupY = markerRect.top - containerRect.top - 20;
    
    popup.style.left = popupX + 'px';
    popup.style.top = popupY + 'px';
    popup.style.transform = 'translate(-50%, -100%)';
    
    // Close button functionality
    var closeBtn = popup.querySelector('.leaflet-popup-close-button');
    closeBtn.addEventListener('click', function(e) {
      e.preventDefault();
      popup.remove();
    });
    
    // Close on map click
    var self = this;
    var closeOnMapClick = function(e) {
      if (!popup.contains(e.target)) {
        popup.remove();
        self.map.viewport.removeEventListener('click', closeOnMapClick);
      }
    };
    
    setTimeout(() => {
      this.map.viewport.addEventListener('click', closeOnMapClick);
    }, 10);
    
    this.map.container.appendChild(popup);
  };

  // DivIcon class
  function DivIcon(options) {
    this.options = options || {};
  }

  // FeatureGroup class
  function FeatureGroup() {
    this.layers = [];
  }

  FeatureGroup.prototype.addLayer = function(layer) {
    this.layers.push(layer);
    return this;
  };

  FeatureGroup.prototype.getBounds = function() {
    // Return a simple bounds object
    return {
      pad: function(amount) {
        return this;
      }
    };
  };

  FeatureGroup.prototype.getLayers = function() {
    return this.layers;
  };

})();