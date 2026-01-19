_state = {
    "active_symbol": None,
    "buys": {},
    "sells": {},
    "avg_buy_price": {},
}

def reset_symbol(symbol):
    _state["buys"][symbol] = 0
    _state["sells"][symbol] = 0
    _state["avg_buy_price"][symbol] = 0.0
    if _state["active_symbol"] == symbol:
        _state["active_symbol"] = None

def should_buy(stock):
    sym = stock["symbol"]
    price = stock.get("price", 0)
    change = stock.get("changePercent", 0)

    if _state["active_symbol"] is not None and _state["active_symbol"] != sym:
        return False
    if sym not in _state["buys"]:
        reset_symbol(sym)
    if _state["buys"][sym] == 0 and change > 0:
        return True
    if price > _state["avg_buy_price"][sym]:
        return True
    return False

def should_sell(stock):
    sym = stock["symbol"]
    price = stock.get("price", 0)
    if sym != _state["active_symbol"]:
        return False
    avg_price = _state["avg_buy_price"].get(sym, 0)
    if avg_price == 0: return False
    if price <= avg_price * 0.97 or price >= avg_price * 1.10:
        return True
    return False

def done_trading(stock):
    sym = stock["symbol"]
    if sym != _state["active_symbol"]:
        return True
    return _state["buys"].get(sym, 0) <= _state["sells"].get(sym, 0)

def note_buy(symbol, price):
    if symbol not in _state["buys"]:
        reset_symbol(symbol)
    _state["active_symbol"] = symbol
    curr_buys = _state["buys"][symbol]
    curr_avg = _state["avg_buy_price"][symbol]
    new_avg = (curr_avg * curr_buys + price) / (curr_buys + 1)
    _state["avg_buy_price"][symbol] = new_avg
    _state["buys"][symbol] += 1

def note_sell(symbol):
    if symbol not in _state["sells"]:
        reset_symbol(symbol)
    _state["sells"][symbol] += 1
    if _state["sells"][symbol] >= _state["buys"][symbol]:
        _state["active_symbol"] = None
