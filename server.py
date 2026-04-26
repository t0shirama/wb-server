"""
WB Dashboard Server
- Отдаёт wb-dashboard.html по адресу /
- Проксирует запросы к WB API по адресу /wb/...
Деплой: Railway, Render, или любой VPS
"""

import os
import json
import urllib.request
import urllib.error
from flask import Flask, request, Response, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

WB_APIS = {
    "statistics": "https://statistics-api.wildberries.ru",
    "analytics":  "https://seller-analytics-api.wildberries.ru",
    "content":    "https://suppliers-api.wildberries.ru",
    "common":     "https://common-api.wildberries.ru",
}


@app.route("/")
def index():
    return send_file("wb-dashboard.html")


@app.route("/wb/<api_key>/<path:wb_path>", methods=["GET", "POST", "OPTIONS"])
def proxy(api_key, wb_path):
    if request.method == "OPTIONS":
        return Response(status=200, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
        })

    base = WB_APIS.get(api_key)
    if not base:
        return Response(
            json.dumps({"error": f"Unknown api: {api_key}"}),
            status=400, mimetype="application/json"
        )

    query = request.query_string.decode()
    url = f"{base}/{wb_path}" + (f"?{query}" if query else "")
    token = request.headers.get("Authorization", "")
    body = request.get_data() or None

    req = urllib.request.Request(url, data=body, method=request.method)
    req.add_header("Authorization", token)
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            return Response(data, status=resp.status, mimetype="application/json",
                            headers={"Access-Control-Allow-Origin": "*"})
    except urllib.error.HTTPError as e:
        data = e.read()
        return Response(data, status=e.code, mimetype="application/json",
                        headers={"Access-Control-Allow-Origin": "*"})
    except Exception as e:
        return Response(json.dumps({"error": str(e)}), status=502,
                        mimetype="application/json",
                        headers={"Access-Control-Allow-Origin": "*"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8765))
    print(f"Server running on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port)
