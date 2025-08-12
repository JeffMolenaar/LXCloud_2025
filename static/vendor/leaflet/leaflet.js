/*
 * Leaflet 1.9.4, a JS library for interactive maps. https://leafletjs.com
 * (c) 2010-2023 Vladimir Agafonkin, (c) 2010-2011 CloudMade
 */

(function (global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined' ? factory(exports) :
    typeof define === 'function' && define.amd ? define(['exports'], factory) :
    (global = global || self, factory(global.L = {}));
}(this, (function (exports) { 'use strict';

    var version = "1.9.4";

    // Utility functions
    function extend(dest) {
        var sources = Array.prototype.slice.call(arguments, 1);
        for (var i = 0; i < sources.length; i++) {
            var source = sources[i];
            for (var key in source) {
                dest[key] = source[key];
            }
        }
        return dest;
    }

    function bind(fn, obj) {
        var slice = Array.prototype.slice;
        if (fn.bind) {
            return fn.bind.apply(fn, slice.call(arguments, 1));
        }
        var args = slice.call(arguments, 2);
        return function () {
            return fn.apply(obj, args.length ? args.concat(slice.call(arguments)) : arguments);
        };
    }

    function stamp(obj) {
        obj._leaflet_id = obj._leaflet_id || ++lastId;
        return obj._leaflet_id;
    }

    var lastId = 0;

    // Basic Map class
    function Map(element, options) {
        options = options || {};
        this._container = typeof element === 'string' ? document.getElementById(element) : element;
        this._container.innerHTML = '';
        
        this._zoom = options.zoom || 10;
        this._center = options.center || [51.505, -0.09];
        this._layers = [];
        this._markers = [];
        this.options = options;
        
        this._initContainer();
        this._initEvents();
        
        if (options.center && options.zoom !== undefined) {
            this.setView(options.center, options.zoom);
        }
    }

    Map.prototype = {
        _initContainer: function() {
            var container = this._container;
            container.style.position = 'relative';
            container.style.overflow = 'hidden';
            container.style.width = '100%';
            container.style.height = '100%';
            
            this._mapPane = document.createElement('div');
            this._mapPane.className = 'leaflet-map-pane';
            this._mapPane.style.position = 'absolute';
            this._mapPane.style.left = '0';
            this._mapPane.style.top = '0';
            this._mapPane.style.width = '100%';
            this._mapPane.style.height = '100%';
            container.appendChild(this._mapPane);
            
            this._tilePane = document.createElement('div');
            this._tilePane.className = 'leaflet-tile-pane';
            this._tilePane.style.position = 'absolute';
            this._tilePane.style.left = '0';
            this._tilePane.style.top = '0';
            this._mapPane.appendChild(this._tilePane);
            
            this._markerPane = document.createElement('div');
            this._markerPane.className = 'leaflet-marker-pane';
            this._markerPane.style.position = 'absolute';
            this._markerPane.style.left = '0';
            this._markerPane.style.top = '0';
            this._markerPane.style.pointerEvents = 'none';
            this._mapPane.appendChild(this._markerPane);
            
            this._popupPane = document.createElement('div');
            this._popupPane.className = 'leaflet-popup-pane';
            this._popupPane.style.position = 'absolute';
            this._popupPane.style.left = '0';
            this._popupPane.style.top = '0';
            this._popupPane.style.pointerEvents = 'none';
            this._mapPane.appendChild(this._popupPane);
            
            this._controlContainer = document.createElement('div');
            this._controlContainer.className = 'leaflet-control-container';
            this._controlContainer.style.position = 'absolute';
            this._controlContainer.style.top = '0';
            this._controlContainer.style.left = '0';
            this._controlContainer.style.width = '100%';
            this._controlContainer.style.height = '100%';
            this._controlContainer.style.pointerEvents = 'none';
            container.appendChild(this._controlContainer);
        },

        _initEvents: function() {
            var self = this;
            
            // Check if dragging is enabled (default true)
            var isDraggingEnabled = this.options.dragging !== false;
            
            if (isDraggingEnabled) {
                // Mouse events for panning
                var dragging = false;
                var startX, startY, startCenterX, startCenterY;
                
                this._container.addEventListener('mousedown', function(e) {
                    dragging = true;
                    startX = e.clientX;
                    startY = e.clientY;
                    startCenterX = self._center[1];
                    startCenterY = self._center[0];
                    self._container.style.cursor = 'grabbing';
                    e.preventDefault();
                });
                
                document.addEventListener('mousemove', function(e) {
                    if (!dragging) return;
                    
                    var deltaX = e.clientX - startX;
                    var deltaY = e.clientY - startY;
                    
                    var scale = 256 * Math.pow(2, self._zoom);
                    var deltaLng = (deltaX / scale) * 360;
                    var deltaLat = (deltaY / scale) * 360;
                    
                    self._center = [startCenterY - deltaLat, startCenterX - deltaLng];
                    self._update();
                });
                
                document.addEventListener('mouseup', function(e) {
                    if (dragging) {
                        dragging = false;
                        self._container.style.cursor = 'grab';
                    }
                });
                
                this._container.style.cursor = 'grab';
            }
            
            // Wheel zoom (always enabled)
            this._container.addEventListener('wheel', function(e) {
                e.preventDefault();
                var delta = e.deltaY < 0 ? 1 : -1;
                self.setZoom(self._zoom + delta);
            });
        },

        setView: function(center, zoom, options) {
            this._center = center;
            this._zoom = Math.max(1, Math.min(18, zoom));
            this._update();
            return this;
        },

        setZoom: function(zoom) {
            this._zoom = Math.max(1, Math.min(18, zoom));
            this._update();
            return this;
        },

        zoomIn: function() {
            return this.setZoom(this._zoom + 1);
        },

        zoomOut: function() {
            return this.setZoom(this._zoom - 1);
        },

        addLayer: function(layer) {
            if (layer.addTo) {
                layer.addTo(this);
            } else {
                this._layers.push(layer);
                if (layer._initTiles) {
                    layer._initTiles(this);
                }
            }
            return this;
        },

        removeLayer: function(layer) {
            var index = this._layers.indexOf(layer);
            if (index !== -1) {
                this._layers.splice(index, 1);
                if (layer._removeTiles) {
                    layer._removeTiles();
                }
            }
            return this;
        },

        getContainer: function() {
            return this._container;
        },

        getCenter: function() {
            return { lat: this._center[0], lng: this._center[1] };
        },

        getZoom: function() {
            return this._zoom;
        },

        invalidateSize: function() {
            // Force recalculation of map size and tile positions
            for (var i = 0; i < this._layers.length; i++) {
                if (this._layers[i]._update) {
                    this._layers[i]._update();
                }
            }
            this._updateMarkers();
            return this;
        },

        fitBounds: function(bounds, options) {
            options = options || {};
            
            var sw = bounds.getSouthWest();
            var ne = bounds.getNorthEast();
            
            var centerLat = (sw.lat + ne.lat) / 2;
            var centerLng = (sw.lng + ne.lng) / 2;
            
            // Calculate zoom level based on bounds
            var latDiff = Math.abs(ne.lat - sw.lat);
            var lngDiff = Math.abs(ne.lng - sw.lng);
            
            // Simple zoom calculation (can be improved)
            var zoom = Math.floor(Math.log2(360 / Math.max(latDiff, lngDiff))) - 1;
            zoom = Math.max(1, Math.min(18, zoom));
            
            this.setView([centerLat, centerLng], zoom);
            return this;
        },

        _update: function() {
            // Update all layers
            for (var i = 0; i < this._layers.length; i++) {
                if (this._layers[i]._update) {
                    this._layers[i]._update();
                }
            }
            
            this._updateMarkers();
        },

        _updateMarkers: function() {
            // Update markers
            for (var j = 0; j < this._markers.length; j++) {
                if (this._markers[j]._update) {
                    this._markers[j]._update();
                }
            }
        },

        latLngToContainerPoint: function(latlng) {
            var lat = latlng[0] * Math.PI / 180;
            var lng = latlng[1] * Math.PI / 180;
            
            var scale = 256 * Math.pow(2, this._zoom);
            var centerLat = this._center[0] * Math.PI / 180;
            var centerLng = this._center[1] * Math.PI / 180;
            
            var x = (lng - centerLng) * scale / (2 * Math.PI) + this._container.offsetWidth / 2;
            var y = (centerLat - lat) * scale / (2 * Math.PI) + this._container.offsetHeight / 2;
            
            return {x: x, y: y};
        },

        fitBounds: function(bounds) {
            var sw = bounds.getSouthWest();
            var ne = bounds.getNorthEast();
            
            var centerLat = (sw.lat + ne.lat) / 2;
            var centerLng = (sw.lng + ne.lng) / 2;
            
            var latDiff = Math.abs(ne.lat - sw.lat);
            var lngDiff = Math.abs(ne.lng - sw.lng);
            
            var zoom = Math.min(
                Math.floor(Math.log2(360 / lngDiff)),
                Math.floor(Math.log2(180 / latDiff))
            );
            
            this.setView([centerLat, centerLng], Math.max(1, zoom - 1));
            return this;
        },

        invalidateSize: function() {
            this._update();
            return this;
        }
    };

    // TileLayer class
    function TileLayer(urlTemplate, options) {
        this._url = urlTemplate;
        this.options = extend({
            attribution: '',
            maxZoom: 18,
            tileSize: 256
        }, options);
        this._tiles = {};
        this._map = null;
    }

    TileLayer.prototype = {
        addTo: function(map) {
            this._map = map;
            map._layers.push(this);
            this._initTiles();
            return this;
        },

        _initTiles: function() {
            if (!this._map) return;
            this._update();
        },

        _update: function() {
            if (!this._map) return;
            
            this._clearTiles();
            
            var zoom = this._map._zoom;
            var center = this._map._center;
            var tileSize = this.options.tileSize;
            
            // Calculate tile coordinates
            var lat = center[0] * Math.PI / 180;
            var lng = center[1] * Math.PI / 180;
            
            var n = Math.pow(2, zoom);
            var tileX = Math.floor((lng + Math.PI) / (2 * Math.PI) * n);
            var tileY = Math.floor((1 - Math.asinh(Math.tan(lat)) / Math.PI) / 2 * n);
            
            var containerWidth = this._map._container.offsetWidth;
            var containerHeight = this._map._container.offsetHeight;
            
            var tilesX = Math.ceil(containerWidth / tileSize) + 2;
            var tilesY = Math.ceil(containerHeight / tileSize) + 2;
            
            var startX = tileX - Math.floor(tilesX / 2);
            var startY = tileY - Math.floor(tilesY / 2);
            
            for (var x = startX; x < startX + tilesX; x++) {
                for (var y = startY; y < startY + tilesY; y++) {
                    this._loadTile(x, y, zoom);
                }
            }
        },

        _loadTile: function(x, y, z) {
            var key = x + ':' + y + ':' + z;
            if (this._tiles[key]) return;
            
            var tile = document.createElement('img');
            tile.style.position = 'absolute';
            tile.style.width = this.options.tileSize + 'px';
            tile.style.height = this.options.tileSize + 'px';
            
            // Calculate tile position
            var n = Math.pow(2, z);
            var centerLat = this._map._center[0] * Math.PI / 180;
            var centerLng = this._map._center[1] * Math.PI / 180;
            
            var centerTileX = (centerLng + Math.PI) / (2 * Math.PI) * n;
            var centerTileY = (1 - Math.asinh(Math.tan(centerLat)) / Math.PI) / 2 * n;
            
            var offsetX = (x - centerTileX) * this.options.tileSize + this._map._container.offsetWidth / 2;
            var offsetY = (y - centerTileY) * this.options.tileSize + this._map._container.offsetHeight / 2;
            
            tile.style.left = offsetX + 'px';
            tile.style.top = offsetY + 'px';
            
            // Wrap tile coordinates
            var wrappedX = ((x % n) + n) % n;
            var wrappedY = Math.max(0, Math.min(n - 1, y));
            
            var url = this._url
                .replace('{s}', 'a') // Use 'a' subdomain
                .replace('{z}', z)
                .replace('{x}', wrappedX)
                .replace('{y}', wrappedY);
            
            tile.src = url;
            tile.style.zIndex = 1;
            
            this._map._tilePane.appendChild(tile);
            this._tiles[key] = tile;
        },

        _clearTiles: function() {
            for (var key in this._tiles) {
                var tile = this._tiles[key];
                if (tile.parentNode) {
                    tile.parentNode.removeChild(tile);
                }
            }
            this._tiles = {};
        }
    };

    // Marker class
    function Marker(latlng, options) {
        this._latlng = latlng;
        this.options = extend({
            icon: null
        }, options);
        this._element = null;
        this._popup = null;
        this._map = null;
    }

    Marker.prototype = {
        addTo: function(map) {
            this._map = map;
            map._markers.push(this);
            this._initMarker();
            return this;
        },

        _initMarker: function() {
            if (!this._map) return;
            
            this._element = document.createElement('div');
            this._element.className = 'leaflet-marker-icon';
            this._element.style.position = 'absolute';
            this._element.style.pointerEvents = 'auto';
            this._element.style.cursor = 'pointer';
            
            if (this.options.icon) {
                if (this.options.icon.createIcon) {
                    this._element = this.options.icon.createIcon();
                } else if (this.options.icon.html) {
                    this._element.innerHTML = this.options.icon.html;
                    this._element.style.width = this.options.icon.iconSize[0] + 'px';
                    this._element.style.height = this.options.icon.iconSize[1] + 'px';
                    this._element.className += ' ' + this.options.icon.className;
                }
            } else {
                this._element.innerHTML = '📍';
                this._element.style.fontSize = '20px';
            }
            
            var self = this;
            this._element.addEventListener('click', function(e) {
                e.stopPropagation();
                if (self._popup && self._popup._content) {
                    self.openPopup();
                }
            });
            
            this._map._markerPane.appendChild(this._element);
            this._update();
        },

        _update: function() {
            if (!this._map || !this._element) return;
            
            var point = this._map.latLngToContainerPoint(this._latlng);
            
            // Center the marker on the point
            var iconSize = this.options.icon && this.options.icon.iconSize ? this.options.icon.iconSize : [20, 20];
            this._element.style.left = (point.x - iconSize[0] / 2) + 'px';
            this._element.style.top = (point.y - iconSize[1]) + 'px';
        },

        bindPopup: function(content) {
            this._popup = {
                _content: content,
                _element: null
            };
            return this;
        },

        openPopup: function() {
            if (!this._popup || !this._map) return;
            
            this.closePopup();
            
            this._popup._element = document.createElement('div');
            this._popup._element.className = 'leaflet-popup';
            this._popup._element.innerHTML = '<div class="leaflet-popup-content-wrapper">' +
                '<div class="leaflet-popup-content">' + this._popup._content + '</div></div>' +
                '<div class="leaflet-popup-tip-container"><div class="leaflet-popup-tip"></div></div>';
            
            var point = this._map.latLngToContainerPoint(this._latlng);
            this._popup._element.style.left = point.x + 'px';
            this._popup._element.style.top = (point.y - 40) + 'px';
            this._popup._element.style.transform = 'translateX(-50%)';
            
            this._map._popupPane.appendChild(this._popup._element);
            this._map._popupPane.style.pointerEvents = 'auto';
            
            var self = this;
            setTimeout(function() {
                document.addEventListener('click', self._closePopupHandler = function(e) {
                    if (!self._popup._element.contains(e.target)) {
                        self.closePopup();
                    }
                });
            }, 10);
        },

        closePopup: function() {
            if (this._popup && this._popup._element) {
                this._popup._element.parentNode.removeChild(this._popup._element);
                this._popup._element = null;
                this._map._popupPane.style.pointerEvents = 'none';
                
                if (this._closePopupHandler) {
                    document.removeEventListener('click', this._closePopupHandler);
                    this._closePopupHandler = null;
                }
            }
        }
    };

    // DivIcon class
    function DivIcon(options) {
        this.options = extend({
            iconSize: [12, 12],
            className: '',
            html: ''
        }, options);
    }

    DivIcon.prototype = {
        createIcon: function() {
            var div = document.createElement('div');
            div.innerHTML = this.options.html;
            div.className = 'leaflet-div-icon ' + this.options.className;
            div.style.width = this.options.iconSize[0] + 'px';
            div.style.height = this.options.iconSize[1] + 'px';
            return div;
        }
    };

    // LatLngBounds class
    function LatLngBounds(southWest, northEast) {
        if (southWest && northEast) {
            this._southWest = southWest;
            this._northEast = northEast;
        }
    }

    LatLngBounds.prototype = {
        getSouthWest: function() {
            return { lat: this._southWest[0], lng: this._southWest[1] };
        },
        
        getNorthEast: function() {
            return { lat: this._northEast[0], lng: this._northEast[1] };
        },

        pad: function(bufferRatio) {
            var sw = this.getSouthWest();
            var ne = this.getNorthEast();
            
            var heightBuffer = Math.abs(ne.lat - sw.lat) * bufferRatio;
            var widthBuffer = Math.abs(ne.lng - sw.lng) * bufferRatio;
            
            return new LatLngBounds(
                [sw.lat - heightBuffer, sw.lng - widthBuffer],
                [ne.lat + heightBuffer, ne.lng + widthBuffer]
            );
        }
    };

    // FeatureGroup class
    function FeatureGroup() {
        this._layers = [];
    }

    FeatureGroup.prototype = {
        addLayer: function(layer) {
            this._layers.push(layer);
        },

        getLayers: function() {
            return this._layers;
        },

        getBounds: function() {
            if (this._layers.length === 0) {
                return new LatLngBounds([0, 0], [0, 0]);
            }

            var lats = [];
            var lngs = [];

            for (var i = 0; i < this._layers.length; i++) {
                var layer = this._layers[i];
                if (layer._latlng) {
                    lats.push(layer._latlng[0]);
                    lngs.push(layer._latlng[1]);
                }
            }

            var minLat = Math.min.apply(Math, lats);
            var maxLat = Math.max.apply(Math, lats);
            var minLng = Math.min.apply(Math, lngs);
            var maxLng = Math.max.apply(Math, lngs);

            return new LatLngBounds([minLat, minLng], [maxLat, maxLng]);
        }
    };

    // Control classes
    function Control() {}

    Control.Zoom = function(options) {
        this.options = extend({
            position: 'topleft'
        }, options);
    };

    Control.Zoom.prototype = {
        addTo: function(map) {
            var container = document.createElement('div');
            container.className = 'leaflet-control leaflet-control-zoom leaflet-bar';
            container.style.position = 'absolute';
            container.style.top = '10px';
            container.style.left = '10px';
            container.style.pointerEvents = 'auto';
            
            var zoomIn = document.createElement('a');
            zoomIn.href = '#';
            zoomIn.className = 'leaflet-control-zoom-in';
            zoomIn.innerHTML = '+';
            zoomIn.style.display = 'block';
            zoomIn.style.width = '30px';
            zoomIn.style.height = '30px';
            zoomIn.style.lineHeight = '30px';
            zoomIn.style.textAlign = 'center';
            zoomIn.style.textDecoration = 'none';
            zoomIn.style.color = '#333';
            zoomIn.style.backgroundColor = 'white';
            zoomIn.style.border = '2px solid rgba(0,0,0,0.2)';
            zoomIn.style.borderBottom = 'none';
            
            var zoomOut = document.createElement('a');
            zoomOut.href = '#';
            zoomOut.className = 'leaflet-control-zoom-out';
            zoomOut.innerHTML = '−';
            zoomOut.style.display = 'block';
            zoomOut.style.width = '30px';
            zoomOut.style.height = '30px';
            zoomOut.style.lineHeight = '30px';
            zoomOut.style.textAlign = 'center';
            zoomOut.style.textDecoration = 'none';
            zoomOut.style.color = '#333';
            zoomOut.style.backgroundColor = 'white';
            zoomOut.style.border = '2px solid rgba(0,0,0,0.2)';
            
            container.appendChild(zoomIn);
            container.appendChild(zoomOut);
            
            zoomIn.addEventListener('click', function(e) {
                e.preventDefault();
                map.zoomIn();
            });
            
            zoomOut.addEventListener('click', function(e) {
                e.preventDefault();
                map.zoomOut();
            });
            
            map._controlContainer.appendChild(container);
            return this;
        }
    };

    // Factory functions
    function map(id, options) {
        return new Map(id, options);
    }

    function tileLayer(url, options) {
        return new TileLayer(url, options);
    }

    function marker(latlng, options) {
        return new Marker(latlng, options);
    }

    function divIcon(options) {
        return new DivIcon(options);
    }

    function featureGroup() {
        return new FeatureGroup();
    }

    // Export
    var L = {
        version: version,
        map: map,
        tileLayer: tileLayer,
        marker: marker,
        divIcon: divIcon,
        featureGroup: featureGroup,
        Map: Map,
        TileLayer: TileLayer,
        Marker: Marker,
        DivIcon: DivIcon,
        FeatureGroup: FeatureGroup,
        LatLngBounds: LatLngBounds,
        Control: Control
    };

    // Set up default controls
    L.control = {
        zoom: function(options) {
            return new Control.Zoom(options);
        }
    };

    // Export for different module systems
    if (typeof exports !== 'undefined') {
        exports.L = L;
    } else {
        global.L = L;
    }

    // Auto-add zoom control
    if (typeof window !== 'undefined') {
        window.L = L;
    }

})));