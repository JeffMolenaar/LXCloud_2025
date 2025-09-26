// OpenLayers JS Stub - Basic implementation for fallback functionality
window.ol = {
    Map: function(options) {
        this.target = options.target;
        this.layers = options.layers || [];
        this.view = options.view;
        this.overlays = [];
        
        // Create a fallback map display
        const container = document.getElementById(this.target);
        if (container) {
            container.innerHTML = `
                <div style="
                    height: 100%; 
                    background: linear-gradient(45deg, #f0f8ff, #e6f3ff);
                    display: flex; 
                    align-items: center; 
                    justify-content: center;
                    flex-direction: column;
                    text-align: center;
                    border-radius: 8px;
                    border: 2px dashed #007bff;
                    color: #666;
                    padding: 20px;
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🗺️</div>
                    <h4 style="color: #007bff; margin-bottom: 0.5rem;">Controller Map</h4>
                    <p style="margin: 0; font-size: 0.9rem;">Map functionality temporarily unavailable</p>
                    <p style="margin: 0.5rem 0 0 0; font-size: 0.8rem; opacity: 0.7;">
                        Controllers: <strong id="map-controller-count">0</strong> | 
                        Online: <strong id="map-online-count">0</strong>
                    </p>
                </div>
            `;
        }
        
        return {
            addOverlay: function(overlay) {
                this.overlays.push(overlay);
            }.bind(this),
            on: function(event, handler) {
                // Stub event handler
            },
            getView: function() {
                return {
                    on: function(event, handler) {
                        // Stub view event handler
                    },
                    getZoom: function() { return 8; }
                };
            },
            forEachFeatureAtPixel: function(pixel, callback) {
                return null; // No features in fallback mode
            },
            updateSize: function() {
                // Stub method
            }
        };
    },
    
    View: function(options) {
        this.center = options.center;
        this.zoom = options.zoom;
        return this;
    },
    
    layer: {
        Tile: function(options) {
            this.source = options.source;
            return this;
        },
        Vector: function(options) {
            this.source = options.source;
            this.style = options.style;
            return this;
        }
    },
    
    source: {
        OSM: function() {
            return this;
        },
        Vector: function(options) {
            this.features = (options && options.features) ? options.features : [];
            return {
                getFeatures: function() {
                    return this.features || [];
                }.bind(this),
                addFeatures: function(features) {
                    this.features = this.features.concat(features);
                }.bind(this),
                clear: function() {
                    this.features = [];
                }.bind(this)
            };
        },
        Cluster: function(options) {
            this.source = (options && options.source) ? options.source : null;
            this.distance = (options && options.distance) ? options.distance : 20;
            return {
                setDistance: function(distance) {
                    this.distance = distance;
                }.bind(this),
                getSource: function() {
                    return this.source;
                }.bind(this)
            };
        }
    },
    
    Feature: function(options) {
        this.geometry = options.geometry;
        this.properties = {};
        return {
            setGeometry: function(geometry) {
                this.geometry = geometry;
            }.bind(this),
            getGeometry: function() {
                return this.geometry;
            }.bind(this),
            set: function(key, value) {
                this.properties[key] = value;
            }.bind(this),
            get: function(key) {
                return this.properties[key];
            }.bind(this)
        };
    },
    
    geom: {
        Point: function(coordinates) {
            this.coordinates = coordinates;
            return this;
        }
    },
    
    proj: {
        fromLonLat: function(coordinates) {
            return coordinates; // Simple pass-through for fallback
        }
    },
    
    style: {
        Style: function(options) {
            return this;
        },
        Circle: function(options) {
            return this;
        },
        Fill: function(options) {
            return this;
        },
        Stroke: function(options) {
            return this;
        },
        Text: function(options) {
            return this;
        }
    },
    
    Overlay: function(options) {
        this.element = options.element;
        this.positioning = options.positioning;
        this.offset = options.offset;
        return {
            setPosition: function(position) {
                // Stub method for overlay positioning
            }
        };
    }
};

console.log('OpenLayers stub loaded - using fallback map functionality');