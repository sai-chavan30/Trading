import json
import os
from time import strftime

TRADE_LOG_FILE = "trades.json"
_trades_log = []


def _load_trades():
    global _trades_log
    if os.path.exists(TRADE_LOG_FILE):
        try:
            with open(TRADE_LOG_FILE, "r") as f:
                _trades_log = json.load(f)
        except:
            _trades_log = []
    else:
        _trades_log = []


def _save_trades():
    with open(TRADE_LOG_FILE, "w") as f:
        json.dump(_trades_log, f, indent=2)


def record_trade(symbol, name, trade_type, qty, price):
    """Record a trade and save to JSON."""
    global _trades_log
    _load_trades()
    trade = {
        "time": strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": symbol,
        "name": name,
        "type": trade_type,
        "qty": int(qty),
        "price": float(price),
    }
    _trades_log.append(trade)
    _save_trades()
    print(f"🧾 Recorded trade: {trade}")


def calculate_profit_loss():
    """Compute total profit/loss and open positions."""
    _load_trades()
    total_profit = 0.0
    positions = {}

    for t in _trades_log:
        sym = t["symbol"]
        if sym not in positions:
            positions[sym] = {"qty": 0, "avg_price": 0.0}
        pos = positions[sym]

        if t["type"] == "buy":
            old_qty = pos["qty"]
            old_avg = pos["avg_price"]
            new_avg = (old_avg * old_qty + t["price"] * t["qty"]) / (old_qty + t["qty"]) if old_qty + t["qty"] > 0 else t["price"]
            pos["qty"] += t["qty"]
            pos["avg_price"] = new_avg
        elif t["type"] == "sell":
            if pos["qty"] > 0:
                profit = (t["price"] - pos["avg_price"]) * t["qty"]
                total_profit += profit
                pos["qty"] -= t["qty"]

    return {
        "total_profit": round(total_profit, 2),
        "open_positions": positions,
        "trades": _trades_log,
    }
