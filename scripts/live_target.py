"""
Minimal HTTP target for live pipeline verification.
Exposes several discoverable endpoints with intentional patterns
that the pipeline stages can detect.
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sys
import threading

RESPONSES = {
    "/": {
        "status": 200,
        "body": "<html><body><h1>Test Target</h1><p>Welcome</p></body></html>",
        "content_type": "text/html",
    },
    "/api/v1/users": {
        "status": 200,
        "body": json.dumps({"users": [{"id": 1, "name": "admin"}]}),
        "content_type": "application/json",
    },
    "/api/v1/config": {
        "status": 200,
        "body": json.dumps({"debug": True, "api_key": "AKIAIOSFODNN7EXAMPLE"}),
        "content_type": "application/json",
    },
    "/login": {
        "status": 200,
        "body": '<html><body><form action="/auth" method="post"><input name="user"><input name="pass" type="password"><button>Login</button></form></body></html>',
        "content_type": "text/html",
    },
    "/auth": {
        "status": 302,
        "body": "",
        "content_type": "text/html",
        "headers": {"Location": "/dashboard"},
    },
    "/dashboard": {
        "status": 200,
        "body": "<html><body><h1>Dashboard</h1><script>var api_key='sk-proj-abc123def456ghi789';</script></body></html>",
        "content_type": "text/html",
    },
    "/search": {
        "status": 200,
        "body": "<html><body>Search results for: <span class='query'></span></body></html>",
        "content_type": "text/html",
    },
    "/.env": {
        "status": 200,
        "body": "DB_PASSWORD=supersecret\nAPI_KEY=AKIAIOSFODNN7EXAMPLE",
        "content_type": "text/plain",
    },
    "/.git/HEAD": {
        "status": 200,
        "body": "ref: refs/heads/main",
        "content_type": "text/plain",
    },
    "/robots.txt": {
        "status": 200,
        "body": "User-agent: *\nDisallow: /admin\nDisallow: /api/internal",
        "content_type": "text/plain",
    },
    "/health": {
        "status": 200,
        "body": json.dumps({"status": "ok"}),
        "content_type": "application/json",
    },
    "/static/app.js": {
        "status": 200,
        "body": 'const CONFIG = { apiKey: "AIzaSyB-xxxxxxxxxxxxxxxxxxxx", endpoint: "/api" }; document.getElementById("content").innerHTML = userInput;',
        "content_type": "application/javascript",
    },
}


class TargetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path in RESPONSES:
            resp = RESPONSES[path]
            self.send_response(resp["status"])
            self.send_header("Content-Type", resp["content_type"])
            # Add CORS header for CORS scanner testing
            origin = self.headers.get("Origin", "")
            if origin:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Access-Control-Allow-Credentials", "true")
            for k, v in resp.get("headers", {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(resp["body"].encode())
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Not Found")

    def do_POST(self):
        self.do_GET()

    def log_message(self, format, *args):
        pass  # Suppress logs


def start_server(port=8888):
    server = HTTPServer(("0.0.0.0", port), TargetHandler)
    print(f"Live target running on http://0.0.0.0:{port}")
    sys.stdout.flush()
    server.serve_forever()


if __name__ == "__main__":
    start_server()
