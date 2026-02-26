# Binance Futures Testnet Trading Bot

A small Python CLI bot for placing **Binance USDT-M Futures Testnet** orders (MARKET, LIMIT, STOP_LIMIT) with strong validation and logging.

---

## 1. Installation

From the project root (`C:\Users\ADMIN\Desktop\TradingBot`):

1. Clone the repo
   ```bash
   git clone https://github.com/AnishSonar1234/TradingBot.git
   cd TradingBot
   ```

2. (Optional but recommended) Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create .env File:

Create a file named `.env` in the project root (same folder as `cli.py`) with your **Binance Futures Testnet** API credentials:

```env
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
```

- **Use Testnet keys only** – this project is wired to Binance **futures testnet**, not mainnet.
- Keep this file **out of version control** – `.env` is already ignored by `.gitignore`.

5. Make sure your system clock is reasonably in sync (the client also syncs timestamp with Binance, but a very wrong local clock can still cause issues).

---

## 2. Running the Bot – Example Commands

The main entry point is `cli.py`. All commands follow this shape:

```bash
python cli.py --symbol SYMBOL --side BUY|SELL --type MARKET|LIMIT|STOP_LIMIT --quantity QTY [--price PRICE] [--stop-price STOP]
```

### 2.1 MARKET order example

Buy 0.003 BTC at market:

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.003
```

### 2.2 LIMIT order example

Place a limit buy for 0.002 BTC at 70,000 USDT:

```bash
python cli.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.002 --price 70000
```

### 2.3 STOP_LIMIT order example

Place a stop‑limit buy: trigger at 68,500, limit price 68,000:

```bash
python cli.py --symbol BTCUSDT --side BUY --type STOP_LIMIT --quantity 0.003 --price 68000 --stop-price 68500
```

- `--price`  → the **limit** price.
- `--stop-price` → the **trigger** price.

---

## 3. Min Notional Rule (Why small orders fail)

Binance Futures enforces a **minimum notional** per order (in USDT).

The bot:

- Fetches the current **mark price** for the symbol.
- Computes:

  \[
  \text{notional} = \text{mark\_price} \times \text{quantity}
  \]

- Fetches the `MIN_NOTIONAL` filter from the exchange.
- If `notional < min_notional`, it **raises a clear error** before sending the order:

> `Order notional too small: X.XX USDT. Minimum required: Y.YY USDT`

This prevents confusing Binance errors like `APIError(code=-4164): Order's notional must be no smaller than 100`.

---

## 4. Log File Location

Logging is configured in `bot/logging_config.py`.

- Logs are written to:

  ```text
  logs/trading.log
  ```

- Each entry includes:
  - Timestamp
  - Log level
  - Logger name
  - Message

You will see:

- Validated order parameters (after all checks).
- Raw responses from Binance.
- Stack traces when something goes wrong.

---

## 5. Assumptions

This project makes several assumptions:

- **Environment**
  - You are using **Python 3.10+** on Windows.
  - You have network access to `https://testnet.binancefuture.com`.

- **Exchange / product**
  - Trading **USDT‑margined futures** (e.g. `BTCUSDT`).
  - The symbol exists on Binance Futures Testnet and has filter data (`PRICE_FILTER`, `PERCENT_PRICE`, `MIN_NOTIONAL`).

- **Usage**
  - All orders are **single‑leg** (no multi‑symbol strategies).
  - You accept that this is only for **testnet / educational** purposes, not production trading.

---

## 6. Example Sample Output

### 6.1 MARKET order (success)

```text
==============================
ORDER REQUEST
==============================
Symbol   : BTCUSDT
Side     : BUY
Type     : MARKET
Quantity : 0.003

==============================
ORDER RESPONSE
==============================
Order ID     : 12548834819
Status       : NEW
ExecutedQty  : 0.000
Avg Price    : 0.00
Mark Price   : 68416.40
Notional     : 205.25 USDT

Order placed successfully
```

### 6.2 STOP_LIMIT order (success)

```text
==============================
ORDER REQUEST
==============================
Symbol   : BTCUSDT
Side     : BUY
Type     : STOP_LIMIT
Quantity : 0.003
Input Price     : 68000.0
Input Stop Price: 68500.0

==============================
ORDER RESPONSE
==============================
Order ID     : 1000000017210147
Status       : NEW
Mark Price   : 68326.12
Notional     : 204.98 USDT
Final Price  : 68000.0

Order placed successfully
```

---

## 7. Architecture Overview

High‑level data flow:

```mermaid
flowchart LR
    U[User (CLI)] --> C[cli.py]
    C --> O[OrderService (bot/orders.py)]
    O --> V[Validators (bot/validators.py)]
    O --> CL[BinanceFuturesClient (bot/client.py)]
    O --> L[Logging (bot/logging_config.py)]
    CL --> B[(Binance Futures Testnet API)]
    L --> F[logs/trading.log]
```

- `cli.py`
  - Parses command‑line args.
  - Prints the request summary and final response.
  - Calls into `OrderService`.

- `bot/orders.py` (`OrderService`)
  - Applies all trading-logic validations.
  - Builds the correct Binance request payload.
  - Calls the client and returns a structured result.

- `bot/validators.py`
  - Simple, focused functions that validate:
    - Side (`BUY` / `SELL`)
    - Order type (`MARKET`, `LIMIT`, `STOP_LIMIT`)
    - Quantity
    - Price and stop price requirements

- `bot/client.py` (`BinanceFuturesClient`)
  - Wraps `python-binance` `Client`.
  - Points it to **futures testnet**.
  - Syncs timestamp to avoid `-1021` recvWindow errors.
  - Exposes:
    - `create_order(...)`
    - `get_mark_price(symbol)`
    - `get_symbol_filters(symbol)`

- `bot/logging_config.py`
  - Central place to configure logging to `logs/trading.log`.

---

## 8. Validation Approach

The bot is deliberately strict to fail fast **before** sending bad orders to Binance.

- **Input normalization**
  - `side` and `type` are upper‑cased and validated against known sets.

- **Field‑level validation (`validators.py`)**
  - `validate_side` – only `BUY` or `SELL`.
  - `validate_order_type` – only `MARKET`, `LIMIT`, `STOP_LIMIT`.
  - `validate_quantity` – must be `> 0`.
  - `validate_price` – required for `LIMIT` and `STOP_LIMIT`.
  - `validate_stop_price` – required for `STOP_LIMIT`.

- **Exchange‑level validation (`OrderService.place_order`)**
  - Fetches `futures_exchange_info()` and extracts filters:
    - `PRICE_FILTER` – `minPrice`, `maxPrice`, `tickSize`.
    - `PERCENT_PRICE` – allowed price band around the current mark price.
    - `MIN_NOTIONAL` – minimum USDT value per order.
  - Rounds prices to the correct **tick size**.
  - Enforces:
    - Limit/stop prices within `[minPrice, maxPrice]`.
    - Limit/stop prices within the **percent price band** around mark price.
    - `notional >= min_notional`.

- **Type mapping to Binance**
  - Internal types:
    - `MARKET` → Binance `type="MARKET"`.
    - `LIMIT` → Binance `type="LIMIT"`, `timeInForce="GTC"`, `price` set.
    - `STOP_LIMIT` → Binance conditional stop:
      - `type="STOP"`
      - `price` = limit price
      - `stopPrice` = trigger price
      - `timeInForce="GTC"`

- **Response handling**
  - For regular futures orders, the bot reads `orderId`, `status`, `executedQty`, `avgPrice`.
  - For conditional STOP orders (which return `algoId` / `algoStatus`), the CLI falls back to those fields and skips execution fields that do not exist.

This layered validation makes behavior predictable and error messages much easier to understand than raw exchange errors.

