"""Minimal, safe debug reporter for LXCloud.

This module intentionally keeps imports and behavior lightweight so that
Flask app import will not fail even if parts of the environment are
missing. It writes sanitized JSON summaries to a queue directory.
"""

import json
import logging
import os
import traceback
from datetime import datetime
from typing import Any, Dict

try:
    from flask import request
except Exception:  # pragma: no cover - safe fallback when Flask not available
    request = None

LOG = logging.getLogger("lxcloud.debug_reporter")


class DebugReporter:
    """Simple debug reporter that saves JSON files to a queue dir."""

    def __init__(self, app=None,
                 debug_queue_dir: str = "/home/lxcloud/debug_queue"):
        self.app = app
        self.debug_queue_dir = debug_queue_dir
        try:
            os.makedirs(self.debug_queue_dir, exist_ok=True)
        except Exception:
            LOG.exception("Could not create debug queue dir")

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Register minimal error handlers on the Flask app."""
        self.app = app

        @app.errorhandler(500)
        def _handle_500(err):
            try:
                self.capture_500_error(err)
            except Exception:
                LOG.exception("Error while capturing 500 error")
            return app.handle_http_exception(err)

        @app.errorhandler(Exception)
        def _handle_exception(err):
            try:
                self.capture_exception(err)
            except Exception:
                LOG.exception("Error while capturing exception")
            raise err

    def _safe_dump(self, data: Dict[str, Any]) -> str:
        timestamp = datetime.utcnow().isoformat().replace(":", "-")
        fname = f"{timestamp}_{data.get('error_type','unknown')}.json"
        path = os.path.join(self.debug_queue_dir, fname)
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
            return fname
        except Exception:
            LOG.exception("Failed writing debug report")
            return ""

    def _get_request_info(self) -> Dict[str, Any]:
        if request is None:
            return {}
        try:
            return {
                "method": getattr(request, "method", None),
                "path": getattr(request, "path", None),
                "args": list(getattr(request, "args", {}).keys()),
            }
        except Exception:
            return {}

    def capture_500_error(self, error: Exception) -> None:
        info = {
            "error_type": "500_error",
            "error_message": str(error),
            "stack_trace": traceback.format_exc(),
            "request_info": self._get_request_info(),
        }
        fname = self._safe_dump(info)
        if fname:
            LOG.info("Saved 500 debug report: %s", fname)

    def capture_exception(self, error: Exception) -> None:
        info = {
            "error_type": "exception",
            "error_message": str(error),
            "stack_trace": traceback.format_exc(),
            "request_info": self._get_request_info(),
        }
        fname = self._safe_dump(info)
        if fname:
            LOG.info("Saved exception debug report: %s", fname)

    def capture_template_error(self, template_name: str, error: str) -> None:
        info = {
            "error_type": "template_error",
            "template": template_name,
            "error_message": error,
            "request_info": self._get_request_info(),
        }
        fname = self._safe_dump(info)
        if fname:
            LOG.info("Saved template error debug report: %s", fname)


# Module-level instance for convenience
debug_reporter = DebugReporter()
