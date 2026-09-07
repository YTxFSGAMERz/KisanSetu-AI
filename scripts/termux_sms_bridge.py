#!/usr/bin/env python3
"""
KisanSetu SMS Bridge Server — runs inside Termux on Android.
Receives SMS requests from KisanSetu backend on PC over USB (adb forward tcp:8080 tcp:8080).
Fires real SMS via Termux:API (termux-sms-send).
"""
import http.server
import json
import logging
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

PORT = 8080


class SMSRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "healthy",
                "service": "KisanSetu Termux SMS Bridge",
            }).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path in ("/sms", "/api/v1/message"):
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                data = json.loads(body)

                phone = data.get("phone", "") or data.get("phoneNumbers", [""])[0]
                message = data.get("message", "")

                if not phone or not message:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Missing phone or message"}).encode("utf-8"))
                    return

                logging.info("Sending SMS to %s: %s", phone, message[:60])
                res = subprocess.run(
                    ["termux-sms-send", "-n", str(phone), str(message)],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )

                if res.returncode == 0:
                    logging.info("✅ SMS dispatched to %s", phone)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "status": "success",
                        "phone": phone,
                    }).encode("utf-8"))
                else:
                    err = res.stderr.strip() or "Unknown error"
                    logging.error("❌ termux-sms-send error: %s", err)
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "status": "error",
                        "detail": err,
                    }).encode("utf-8"))

            except Exception as e:
                logging.exception("Exception handling SMS request")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def run():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), SMSRequestHandler)
    logging.info("🌾 KisanSetu SMS Bridge running on http://127.0.0.1:%d", PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
