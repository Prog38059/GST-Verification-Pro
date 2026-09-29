import os
import time
import uuid
import base64
import requests
from flask import Flask, jsonify, render_template, request
from asgiref.wsgi import WsgiToAsgi

app = Flask(__name__)
asgi_app = WsgiToAsgi(app)

# Store sessions with creation timestamp: {id: {"session": session, "created_at": timestamp}}
gstSessions = {}
SESSION_TTL_SECONDS = 900  # 15 minutes


def cleanup_stale_sessions():
    """Remove sessions that have expired past SESSION_TTL_SECONDS to avoid memory leaks."""
    now = time.time()
    expired_ids = [
        sid
        for sid, sdata in gstSessions.items()
        if now - sdata.get("created_at", now) > SESSION_TTL_SECONDS
    ]
    for sid in expired_ids:
        gstSessions.pop(sid, None)


@app.route("/", methods=["GET"])
def index():
    """Serve the modern GST verification dashboard."""
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for cloud hosting providers like Render."""
    return jsonify({"status": "healthy", "service": "GST-Verification-API"}), 200


@app.route("/api/v1/getCaptcha", methods=["GET"])
def getCaptcha():
    try:
        cleanup_stale_sessions()
        captcha_url = "https://services.gst.gov.in/services/captcha"
        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
        })

        session_id = str(uuid.uuid4())

        # Visit the landing page to initialize cookies/session
        session.get("https://services.gst.gov.in/services/searchtp", timeout=10)

        captcha_response = session.get(captcha_url, timeout=10)
        if captcha_response.status_code != 200:
            return jsonify({"error": "Failed to retrieve captcha from GST portal"}), 502

        captcha_base64 = base64.b64encode(captcha_response.content).decode("utf-8")

        gstSessions[session_id] = {
            "session": session,
            "created_at": time.time(),
        }

        return jsonify({
            "success": True,
            "sessionId": session_id,
            "image": "data:image/png;base64," + captcha_base64,
        })

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Network error connecting to GST portal: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Internal error fetching captcha: {str(e)}"}), 500


@app.route("/api/v1/getGSTDetails", methods=["POST"])
def getGSTDetails():
    try:
        cleanup_stale_sessions()
        data = request.get_json(silent=True) or {}
        session_id = data.get("sessionId")
        gstin = (data.get("GSTIN") or "").strip().upper()
        captcha = (data.get("captcha") or "").strip()

        if not session_id or not gstin or not captcha:
            return jsonify({"error": "sessionId, GSTIN, and captcha are all required"}), 400

        user = gstSessions.get(session_id)
        if not user or "session" not in user:
            return jsonify({"error": "Session expired or invalid. Please refresh the captcha."}), 400

        session = user["session"]

        gst_payload = {
            "gstin": gstin,
            "captcha": captcha,
        }

        headers = {
            "Referer": "https://services.gst.gov.in/services/searchtp",
            "Origin": "https://services.gst.gov.in",
            "Content-Type": "application/json;charset=UTF-8",
        }

        response = session.post(
            "https://services.gst.gov.in/services/api/search/taxpayerDetails",
            json=gst_payload,
            headers=headers,
            timeout=15,
        )

        try:
            res_data = response.json()
        except Exception:
            return jsonify({
                "error": "Non-JSON response from GST portal",
                "raw": response.text[:300]
            }), 502

        # Check if portal returned an error code or message
        if isinstance(res_data, dict) and res_data.get("errorCode"):
            error_code = res_data.get("errorCode")
            error_msg = res_data.get("message") or res_data.get("desc") or f"GST Portal Error: {error_code}"
            return jsonify({"error": error_msg, "errorCode": error_code}), 400

        return jsonify(res_data)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Network error contacting GST portal: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 5000))
    # Bind to 0.0.0.0 if running in cloud (PORT env var present) or 127.0.0.1 locally
    host = "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"

    print("\n" + "=" * 60)
    print(f" GST Verification App is running!")
    print(f" Dashboard: http://{host}:{port}")
    print(f" API:       http://{host}:{port}/api/v1/getCaptcha")
    print("=" * 60 + "\n")
    uvicorn.run(asgi_app, host=host, port=port)


