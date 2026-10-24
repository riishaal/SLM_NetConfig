"""
SLM-Based Intelligent Network Configuration - Web Server
Lightweight, zero-dependency HTTP server providing the REST API and
serving the professional web dashboard interface.
Connects directly to the existing NetworkConfigAgent backend.
"""

import argparse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import json
import mimetypes
import os
import sys
import time

# Ensure project root is in path
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from controller.agent import NetworkConfigAgent

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Global agent singleton for instant response latencies
_agent_instance = None


def get_agent() -> NetworkConfigAgent:
    global _agent_instance
    if _agent_instance is None:
        print("[SLM Web Server] Initializing NetworkConfigAgent...")
        _agent_instance = NetworkConfigAgent(load_model_weights=False)
        print("[SLM Web Server] NetworkConfigAgent ready.")
    return _agent_instance


class SLMWebRequestHandler(SimpleHTTPRequestHandler):
    """Handles static assets and API requests for the web interface."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def end_headers(self):
        # Enable CORS and disable aggressive caching for local development
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            index_path = os.path.join(STATIC_DIR, "index.html")
            with open(index_path, "rb") as f:
                self.wfile.write(f.read())
            return

        if self.path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "SLM-NetConfig"}).encode("utf-8"))
            return

        # Serve other static files
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/generate":
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length).decode("utf-8")
            
            try:
                payload = json.loads(raw_body) if raw_body else {}
            except Exception as e:
                self._send_json_error(400, f"Invalid JSON payload: {str(e)}")
                return

            requirement = payload.get("requirement", "").strip()
            device_name = payload.get("device", "Switch1").strip() or "Switch1"

            if not requirement:
                self._send_json_error(400, "Requirement text cannot be empty.")
                return

            try:
                agent = get_agent()
                t0 = time.time()
                res = agent.process_request(requirement, device_name=device_name)
                duration = round(time.time() - t0, 4)

                # Determine verification status
                if not res.get("success", True):
                    v_status = "ERROR"
                elif res.get("verified", False):
                    v_status = "APPROVED (PASSED)"
                else:
                    v_status = "REFINEMENT NEEDED"

                pt_path = None
                if res.get("packet_tracer_export") and isinstance(res["packet_tracer_export"], dict):
                    pt_path = res["packet_tracer_export"].get("txt_path")

                response_payload = {
                    "success": res.get("success", True),
                    "user_requirement": requirement,
                    "device_name": device_name,
                    "detected_category": res.get("detected_category", "UNKNOWN"),
                    "verification_status": v_status,
                    "verified": res.get("verified", False),
                    "final_config": res.get("final_config", ""),
                    "processing_time_sec": res.get("total_duration_sec", duration),
                    "config_output_location": res.get("saved_in_repo"),
                    "packet_tracer_export_location": pt_path,
                    "iterations_count": res.get("iterations_count", 1),
                    "error": res.get("error")
                }

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response_payload).encode("utf-8"))

            except Exception as ex:
                self._send_json_error(500, f"Backend processing error: {str(ex)}")
            return

        self._send_json_error(404, "Endpoint not found")

    def _send_json_error(self, code: int, message: str):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"success": False, "error": message}).encode("utf-8"))

    def log_message(self, format, *args):
        # Clean logging format
        sys.stderr.write(f"[SLM-Web] {self.address_string()} - {format % args}\n")


def run_server(port: int = 5000, host: str = "127.0.0.1"):
    # Ensure agent is loaded
    get_agent()

    server_address = (host, port)
    try:
        httpd = ThreadingHTTPServer(server_address, SLMWebRequestHandler)
    except OSError:
        # If port 5000 is occupied, try 5001
        port = port + 1
        server_address = (host, port)
        httpd = ThreadingHTTPServer(server_address, SLMWebRequestHandler)

    url = f"http://{host}:{port}"
    print("\n" + "=" * 60)
    print("SLM-Based Intelligent Network Configuration")
    print(f"Web Dashboard running at: {url}")
    print(f"Serving static files from: {STATIC_DIR}")
    print("Press Ctrl+C to stop.")
    print("=" * 60 + "\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down SLM Web Dashboard...")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SLM Network Configuration Web Server")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind (default: 5000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    args = parser.parse_args()

    run_server(port=args.port, host=args.host)
