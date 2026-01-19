from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import requests
import time
import strategy
import utils

# ----------------------------
# CONFIG
# ----------------------------
USERNAME = "FBL_50_ZZ60"
PASSWORD = "RHW1PLQ2"
LOGIN_URL = "https://www.stockmarketgame.org/login.html"

# Flask app endpoint (make sure app.py is running)
GAINERS_URL = "http://127.0.0.1:5000/api/gainers"

# ----------------------------
# SELENIUM FUNCTIONS
# ----------------------------

def login(driver):
    """Logs into the stock trading website."""
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, 10)

    username = wait.until(EC.presence_of_element_located((By.NAME, "ACCOUNTNO")))
    username.send_keys(USERNAME)

    password = driver.find_element(By.NAME, "USER_PIN")
    password.send_keys(PASSWORD)

    login_btn = driver.find_element(By.XPATH, "//input[@value='Log In']")
    login_btn.click()
    print("✅ Logged in successfully.")
    time.sleep(3)


def enter_trade(driver, stock_name, stock_symbol, order_type='buy', qty=1):
    """Places a buy/sell trade via Selenium and confirms if required."""
    wait = WebDriverWait(driver, 10)

    # Navigate to TRADE → Enter a Trade
    trade_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@class='parent' and text()='TRADE']")))
    trade_btn.click()

    enter_trade_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='eat.html' and text()='Enter a Trade']")))
    enter_trade_link.click()

    wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@id='aStockTrade']"))).click()

    # Search for stock
    search_box = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@id='SymbolName']")))
    search_box.send_keys(stock_name)
    time.sleep(2)

    # Select matching symbol
    results = driver.find_elements(By.CSS_SELECTOR, "div.search-result")
    for r in results:
        try:
            ticker = r.find_element(By.XPATH, ".//div/p").text.strip()
            if ticker.upper() == stock_symbol.upper():
                r.click()
                break
        except:
            continue

    # Select order type
    order_map = {
        'buy': 'rbBuy',
        'sell': 'rbSell',
        'short_sell': 'rbShortSell',
        'short_cover': 'rbShortCover'
    }
    driver.find_element(By.ID, order_map[order_type]).click()

    # Quantity
    qty_field = driver.find_element(By.ID, "BuySellAmt")
    qty_field.clear()
    qty_field.send_keys(str(qty))

    # Market order
    market_select = Select(driver.find_element(By.ID, "OrderType"))
    market_select.select_by_visible_text("Market")

    # Preview trade
    preview_btn = driver.find_element(By.XPATH, "//button[@class='btnTradeBlue' and text()='Preview Trade']")
    preview_btn.click()
    print(f"✅ Placed {order_type.upper()} order for {qty} {stock_symbol}")

    # Confirm trade page (only appears after Preview)
    try:
        trade_pass_field = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='TradePassword']")))
        trade_pass_field.send_keys("yashraj")

        confirm_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='divTradeOrderPreview']/div/div[14]/div[2]/div[1]")))
        confirm_btn.click()
        print("✅ Trade confirmed successfully.")
        time.sleep(2)
    except Exception as e:
        print("⚠️ Could not confirm trade automatically:", e)


# ----------------------------
# STOCK MOMENTUM SELECTION
# ----------------------------

def get_top_momentum_stock(prev_data=None):
    """Fetch top movers and find the one increasing the fastest."""
    try:
        response = requests.get(GAINERS_URL, timeout=5)
        data = response.json()
        if not data:
            print("⚠️ No gainers fetched.")
            return None, prev_data

        # Compute momentum by comparing with previous snapshot
        if prev_data:
            momentum = []
            prev_map = {s["symbol"]: s["changePercent"] for s in prev_data}
            for s in data:
                prev_change = prev_map.get(s["symbol"], 0)
                delta = s["changePercent"] - prev_change
                momentum.append((delta, s))
            momentum.sort(key=lambda x: -x[0])  # descending by delta
            fastest = momentum[0][1] if momentum else data[0]
            print(f"🚀 Fastest mover: {fastest['symbol']} ({fastest['changePercent']:.2f}%)")
            return fastest, data
        else:
            return data[0], data

    except Exception as e:
        print("❌ Error fetching gainers:", e)
        return None, prev_data


# ----------------------------
# TRADING LOOP
# ----------------------------

def trading_loop(driver):
    """Main trading loop based on top momentum stock."""
    print("🚀 Starting trading loop using live gainers feed...\n")
    prev_data = None

    while True:
        stock, prev_data = get_top_momentum_stock(prev_data)
        if not stock:
            time.sleep(3)
            continue

        sym = stock["symbol"]
        name = stock["name"]
        price = stock["price"]
        change = stock["changePercent"]

        # Make buy/sell decisions
        if strategy.should_buy(stock):
            enter_trade(driver, name, sym, "buy", qty=1)
            strategy.note_buy(sym, price)
            utils.record_trade(sym, name, "buy", 1, price)

        elif strategy.should_sell(stock):
            enter_trade(driver, name, sym, "sell", qty=1)
            strategy.note_sell(sym)
            utils.record_trade(sym, name, "sell", 1, price)

        if strategy.done_trading(stock):
            print(f"✅ Done trading {sym}")

        time.sleep(5)  # adjust frequency


# ----------------------------
# MAIN
# ----------------------------
def main():
    driver = webdriver.Chrome()
    driver.maximize_window()

    try:
        login(driver)
        trading_loop(driver)
    except Exception as e:
        print("❌ Trading error:", e)
    finally:
        print("📊 Final portfolio:", utils.calculate_profit_loss())
        driver.quit()


if __name__ == "__main__":
    main()
