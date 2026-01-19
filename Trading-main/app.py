from flask import Flask, jsonify, render_template
from threading import Thread, Lock
from flask_socketio import SocketIO
import robin_stocks.robinhood as r
import time
import utils

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

lock = Lock()
_cached_gainers = []
_last_fetch = 0.0
FETCH_INTERVAL = 0.1  # ✅ Update every 0.1 seconds 


def fetch_loop():
    """Background thread to continuously fetch top movers and emit updates."""
    global _cached_gainers, _last_fetch

    print("[INFO] Fetch loop started (interval = 0.1s)")
    while True:
        try:
            # Fetch top movers (no market param)
            movers = r.markets.get_top_movers()
            if not movers:
                print("[WARN] No movers data returned from Robinhood.")
                time.sleep(2)
                continue

            results = []
            for m in movers[:20]:
                symbol = m.get("symbol", "")
                price = float(m.get("last_trade_price") or 0)
                prev = float(m.get("previous_close") or 0)
                change_pct = ((price - prev) / prev * 100) if prev else 0.0

                results.append({
                    "symbol": symbol,
                    "name": symbol,
                    "price": round(price, 2),
                    "changePercent": round(change_pct, 2)
                })

            results.sort(key=lambda x: -x["changePercent"])

            with lock:
                _cached_gainers = results
                _last_fetch = time.time()

            # Emit updates to connected clients
            socketio.emit('update_gainers', _cached_gainers)
            socketio.emit('update_trades', utils.calculate_profit_loss())

        except Exception as e:
            print("[ERROR] fetch_loop:", e)

        time.sleep(FETCH_INTERVAL)


@app.route("/")
def index():
    return render_template("index_dashboard.html")


@app.route("/api/gainers")
def api_gainers():
    with lock:
        return jsonify(_cached_gainers)


@app.route("/api/trades")
def api_trades():
    return jsonify(utils.calculate_profit_loss())


if __name__ == "__main__":
    print("[INFO] Starting background fetch thread...")
    t = Thread(target=fetch_loop, daemon=True)
    t.start()

    print("[INFO] Flask-SocketIO server running at http://127.0.0.1:5000")
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)


