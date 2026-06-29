"""GET /api/stats — returns the live RAG hyperparameters, straight from config."""
import os, sys, json
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import config


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        data = json.dumps(config.as_stats()).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
