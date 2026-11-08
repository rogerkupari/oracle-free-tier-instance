
#!/usr/bin/env python3

import os
import json
import time
import hmac
import hashlib
import threading
import urllib.request
import urllib.error

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
API_KEY = os.environ["GATEWAY_API_KEY"]
LOG_FILE = os.environ["SOCI_LOG_FILE"]

HOST = "0.0.0.0"
PORT = 8787

CHECK_INTERVAL = 300  # 5 minutes

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


# --------------------------------------------------
# TELEGRAM API
# --------------------------------------------------

def telegram_api(method, payload=None, timeout=25):

    url = f"{TELEGRAM_API}/{method}"

    data = json.dumps(payload or {}).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        result = json.loads(response.read().decode("utf-8"))

    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error: {result}")

    return result


def send_telegram(message, chat_id=None):

    return telegram_api(
        "sendMessage",
        {
            "chat_id": chat_id or CHAT_ID,
            "text": message
        }
    )


# --------------------------------------------------
# LOG FILE
# --------------------------------------------------

def get_log_fingerprint():

    try:
        digest = hashlib.sha256()

        with open(LOG_FILE, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)

                if not chunk:
                    break

                digest.update(chunk)

        return digest.hexdigest()

    except FileNotFoundError:
        return "FILE_NOT_FOUND"


def get_last_log_line():

    try:
        with open(LOG_FILE, "rb") as f:

            f.seek(0, os.SEEK_END)
            position = f.tell()

            if position == 0:
                return "(Log is empty)"

            data = b""

            while position > 0:

                size = min(4096, position)
                position -= size

                f.seek(position)
                data = f.read(size) + data

                if b"\n" in data:
                    break

            lines = data.splitlines()

            if not lines:
                return "(Log is empty)"

            return lines[-1].decode("utf-8", errors="replace")

    except FileNotFoundError:
        return "Error: log file not found"


# --------------------------------------------------
# LOG MONITOR
# --------------------------------------------------

def monitor_log():

    print("Log monitor started.", flush=True)

    last_fingerprint = get_log_fingerprint()

    last_change_time = time.monotonic()

    alert_sent = False

    while True:

        time.sleep(CHECK_INTERVAL)

        try:

            current_fingerprint = get_log_fingerprint()

            # Log file has changed
            if current_fingerprint != last_fingerprint:

                print("Log file changed.", flush=True)

                last_fingerprint = current_fingerprint

                last_change_time = time.monotonic()

                # Allow a new alert after the next idle period
                alert_sent = False

                continue

            # Log has not changed for 5 minutes
            elapsed = time.monotonic() - last_change_time

            if elapsed >= CHECK_INTERVAL and not alert_sent:

                print(
                    "Log unchanged for 5 minutes. Sending alert.",
                    flush=True
                )

                try:

                    send_telegram("Service has stopped")

                    alert_sent = True

                    print("Alert sent successfully.", flush=True)

                except Exception as exc:

                    print(
                        f"Alert sending failed: {exc}",
                        flush=True
                    )

        except Exception as exc:

            print(
                f"Log monitor error: {exc}",
                flush=True
            )


# --------------------------------------------------
# TELEGRAM INCOMING MESSAGES
# --------------------------------------------------

def telegram_listener():

    print("Telegram listener started.", flush=True)

    offset = None

    while True:

        try:

            payload = {
                "timeout": 30,
                "allowed_updates": ["message"]
            }

            if offset is not None:
                payload["offset"] = offset

            result = telegram_api(
                "getUpdates",
                payload,
                timeout=40
            )

            for update in result.get("result", []):

                offset = update["update_id"] + 1

                message = update.get("message", {})

                chat = message.get("chat", {})

                incoming_chat_id = str(chat.get("id", ""))

                # Only accept commands from configured chat
                if incoming_chat_id != str(CHAT_ID):
                    continue

                text = message.get("text", "")

                if not isinstance(text, str):
                    continue

                command = text.strip().lower()

                # STATUS COMMAND
                if command in ("status", "/status"):

                    last_line = get_last_log_line()

                    try:

                        send_telegram(
                            last_line,
                            chat_id=incoming_chat_id
                        )

                    except Exception as exc:

                        print(
                            f"Status response failed: {exc}",
                            flush=True
                        )

        except Exception as exc:

            print(
                f"Telegram listener error: {exc}",
                flush=True
            )

            time.sleep(5)


# --------------------------------------------------
# HTTP GATEWAY
# --------------------------------------------------

class GatewayHandler(BaseHTTPRequestHandler):

    def respond(self, status, data):

        body = json.dumps(data).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.end_headers()

        self.wfile.write(body)

    def do_GET(self):

        if self.path == "/health":

            self.respond(
                200,
                {
                    "status": "ok",
                    "service": "telegram-gateway"
                }
            )

        else:

            self.respond(
                404,
                {"error": "not found"}
            )

    def do_POST(self):

        if self.path != "/send":

            self.respond(
                404,
                {"error": "not found"}
            )

            return

        authorization = self.headers.get(
            "Authorization",
            ""
        )

        expected = f"Bearer {API_KEY}"

        if not hmac.compare_digest(authorization, expected):

            self.respond(
                401,
                {"error": "unauthorized"}
            )

            return

        try:

            length = int(
                self.headers.get("Content-Length", "0")
            )

            if length < 1 or length > 16384:

                self.respond(
                    400,
                    {"error": "invalid request size"}
                )

                return

            data = json.loads(
                self.rfile.read(length)
            )

            message = data.get("message", "")

            if not isinstance(message, str):

                self.respond(
                    400,
                    {"error": "message must be a string"}
                )

                return

            message = message.strip()

            if not message:

                self.respond(
                    400,
                    {"error": "message is empty"}
                )

                return

            if len(message) > 4096:

                self.respond(
                    400,
                    {"error": "message too long"}
                )

                return

            result = send_telegram(message)

            self.respond(
                200,
                {
                    "status": "sent",
                    "message_id": result["result"]["message_id"]
                }
            )

        except (ValueError, UnicodeDecodeError):

            self.respond(
                400,
                {"error": "invalid JSON"}
            )

        except Exception as exc:

            print(
                f"Gateway error: {exc}",
                flush=True
            )

            self.respond(
                502,
                {"error": "message delivery failed"}
            )

    def log_message(self, fmt, *args):

        print(fmt % args, flush=True)


# --------------------------------------------------
# START SERVICES
# --------------------------------------------------

if __name__ == "__main__":

    threading.Thread(
        target=monitor_log,
        daemon=True
    ).start()

    threading.Thread(
        target=telegram_listener,
        daemon=True
    ).start()

    print(
        f"Telegram Gateway listening on {HOST}:{PORT}",
        flush=True
    )

    server = ThreadingHTTPServer(
        (HOST, PORT),
        GatewayHandler
    )

    server.serve_forever()
