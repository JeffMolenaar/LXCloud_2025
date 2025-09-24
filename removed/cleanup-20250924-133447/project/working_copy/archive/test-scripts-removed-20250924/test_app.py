#!/usr/bin/env python3
"""
Simple test to verify basic Flask app functionality
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template_string
from config.config import Config

app = Flask(__name__)
app.config.from_object(Config)


@app.route("/")
def test_index():
    return render_template_string(
        """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LXCloud Test</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="text-center">
                <h1 class="text-primary">🌩️ LXCloud Platform</h1>
                <p class="lead">Cloud Dashboard Platform Test</p>
                <div class="alert alert-success">
                    ✅ Flask application is working correctly!
                </div>
                <div class="card">
                    <div class="card-body">
                        <h5>Configuration Test</h5>
                        <p><strong>Version:</strong> {{ version }}</p>
                        <p><strong>Environment:</strong> Development</p>
                        <p><strong>Status:</strong> Ready for production deployment</p>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """,
        version=Config.get_version(),
    )


if __name__ == "__main__":
    print("Starting LXCloud Test Server...")
    print(f"Version: {Config.get_version()}")
    app.run(host="127.0.0.1", port=5000, debug=True)
#!/usr/bin/env python3
"""
Simple test to verify basic Flask app functionality
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template_string
from config.config import Config

app = Flask(__name__)
app.config.from_object(Config)


@app.route("/")
def test_index():
    return render_template_string(
        """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LXCloud Test</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="text-center">
                <h1 class="text-primary">🌩️ LXCloud Platform</h1>
                <p class="lead">Cloud Dashboard Platform Test</p>
                <div class="alert alert-success">
                    ✅ Flask application is working correctly!
                </div>
                <div class="card">
                    <div class="card-body">
                        <h5>Configuration Test</h5>
                        <p><strong>Version:</strong> {{ version }}</p>
                        <p><strong>Environment:</strong> Development</p>
                        <p><strong>Status:</strong> Ready for production deployment</p>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """,
        version=Config.get_version(),
    )


if __name__ == "__main__":
    print("Starting LXCloud Test Server...")
    print(f"Version: {Config.get_version()}")
    app.run(host="127.0.0.1", port=5000, debug=True)
