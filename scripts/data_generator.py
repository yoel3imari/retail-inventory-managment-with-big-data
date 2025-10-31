# Creating a self-contained Python script that streams fake Point-of-Sale (PoS) transactions.
# The demo below will generate a few sample transactions and print them to the notebook output.
# Save this as `pos_streamer.py` for later use. The script supports console, file, and HTTP modes
# (HTTP requires the `requests` package; if missing it falls back to console printing).
#
# Usage examples (after saving as pos_streamer.py):
#  - Console streaming: python pos_streamer.py --mode console --count 100 --mean-interval 0.5
#  - HTTP streaming: python pos_streamer.py --mode http --url http://localhost:8000/ingest --count 500
#  - File output: python pos_streamer.py --mode file --out /tmp/transactions.ndjson --count 1000
#
# The demo run below prints 5 generated transactions (fast, without long sleeps).
import json
import random
import uuid
import time
import argparse
from datetime import datetime, timezone, timedelta

# --- Transaction generator ---
PRODUCT_CATALOG = [
    {"product_id": "sku-1001", "name": "Espresso", "price": 2.5, "tax_rate": 0.07},
    {"product_id": "sku-1002", "name": "Latte", "price": 3.5, "tax_rate": 0.07},
    {"product_id": "sku-1003", "name": "Bagel", "price": 1.8, "tax_rate": 0.00},
    {"product_id": "sku-1004", "name": "Sandwich", "price": 5.0, "tax_rate": 0.07},
    {"product_id": "sku-1005", "name": "Soda", "price": 1.2, "tax_rate": 0.07},
    {"product_id": "sku-1006", "name": "Water Bottle", "price": 1.0, "tax_rate": 0.00},
    {"product_id": "sku-1007", "name": "Croissant", "price": 2.0, "tax_rate": 0.07},
    {"product_id": "sku-1008", "name": "Sandwich Deluxe", "price": 7.5, "tax_rate": 0.07},
]

PAYMENT_METHODS = ["cash", "card", "mobile", "gift_card"]
CURRENCIES = ["USD", "EUR", "GBP"]

def iso_now():
    return datetime.now(timezone.utc).astimezone().isoformat()

def pick_items():
    # choose 1-5 distinct items, with random quantities
    count = random.choices([1,2,3,4,5], weights=[40,30,15,10,5])[0]
    items = []
    catalog = PRODUCT_CATALOG
    chosen = random.sample(catalog, k=min(count, len(catalog)))
    for p in chosen:
        qty = random.choices([1,1,1,2,3], weights=[50,20,10,15,5])[0]
        price = round(p["price"] * (1 + random.uniform(-0.03, 0.05)), 2)  # slight price noise
        tax_rate = p.get("tax_rate", 0.0)
        items.append({
            "product_id": p["product_id"],
            "name": p["name"],
            "qty": qty,
            "unit_price": price,
            "tax_rate": tax_rate
        })
    return items

def compute_totals(items):
    subtotal = sum(i["unit_price"] * i["qty"] for i in items)
    tax = sum(i["unit_price"] * i["qty"] * i.get("tax_rate", 0.0) for i in items)
    # small chance of discount
    discount = 0.0
    if random.random() < 0.08:
        # percent discount 5%-20%
        discount = round(subtotal * random.uniform(0.05, 0.2), 2)
    total = round(subtotal + tax - discount, 2)
    return {"subtotal": round(subtotal,2), "tax": round(tax,2), "discount": discount, "total": total}

def generate_transaction(store_ids=(1,2,3,4), currency="USD"):
    tx_id = str(uuid.uuid4())
    ts = iso_now()
    store_id = f"store-{random.choice(store_ids)}"
    terminal_id = f"term-{random.randint(1,8)}"
    cashier_id = f"cashier-{random.randint(100,199)}"
    items = pick_items()
    totals = compute_totals(items)
    payment_method = random.choices(PAYMENT_METHODS, weights=[20,60,15,5])[0]
    approval_code = None
    if payment_method in ("card", "mobile", "gift_card"):
        approval_code = f"APP-{random.randint(100000,999999)}"
    # customer sometimes present
    customer_id = None
    if random.random() < 0.15:
        customer_id = f"cust-{random.randint(10000,99999)}"
    status = random.choices(["completed", "voided", "pending"], weights=[93,4,3])[0]
    transaction = {
        "transaction_id": tx_id,
        "timestamp": ts,
        "store_id": store_id,
        "terminal_id": terminal_id,
        "cashier_id": cashier_id,
        "items": items,
        "totals": totals,
        "payment_method": payment_method,
        "approval_code": approval_code,
        "customer_id": customer_id,
        "currency": currency,
        "status": status,
    }
    return transaction

# --- Inter-request timing model ---
def next_delay(mean_interval=1.0, burstiness=1.0):
    """
    Return next delay in seconds.
    Uses exponential distribution (Poisson process) scaled by burstiness.
    burstiness>1 increases variance, <1 decreases.
    """
    if mean_interval <= 0:
        return 0.0
    # exponential with rate = 1/mean
    base = random.expovariate(1.0 / mean_interval)
    # add small jitter
    jitter = random.uniform(-0.1 * mean_interval, 0.1 * mean_interval)
    delay = max(0.0, base * burstiness + jitter)
    return delay

# --- Streaming runner ---
def stream_transactions(mode="console", count=None, mean_interval=1.0, burstiness=1.0,
                        out_file=None, url=None, batch_size=1, store_ids=(1,2,3), currency="USD",
                        seed=None):
    if seed is not None:
        random.seed(seed)
    sent = 0
    # try to import requests if HTTP mode
    requests = None
    if mode == "http":
        try:
            import requests as _r
            requests = _r
        except Exception as e:
            print("requests not available; falling back to console mode. Install `requests` for HTTP POST support.")
            mode = "console"

    outfile = None
    if mode == "file":
        outfile = open(out_file or "transactions.ndjson", "a", encoding="utf-8")
    try:
        while True:
            batch = []
            for _ in range(batch_size):
                tx = generate_transaction(store_ids=store_ids, currency=currency)
                batch.append(tx)
                sent += 1
                # if count provided and reached, stop building more
                if count and sent >= count:
                    break
            # dispatch batch
            if mode == "console":
                for tx in batch:
                    print(json.dumps(tx, ensure_ascii=False))
            elif mode == "file":
                for tx in batch:
                    outfile.write(json.dumps(tx, ensure_ascii=False) + "\n")
                outfile.flush()
            elif mode == "http" and requests:
                # send each tx or the whole batch as chosen; here we send individual requests to mimic PoS
                for tx in batch:
                    try:
                        r = requests.post(url, json=tx, timeout=5)
                        print(f"POST {url} -> {r.status_code} ({r.reason})")
                    except Exception as e:
                        print("HTTP send failed:", e)
            # exit if reached count
            if count and sent >= count:
                break
            # compute next delay, but modulate by local time (simulate busier hours)
            # local hour (0-23)
            local_hour = datetime.now().hour
            # multiplier: busier between 7-10 and 11-14 and 17-20 (coffee & lunch & dinner)
            if 7 <= local_hour <= 10 or 11 <= local_hour <= 14 or 17 <= local_hour <= 20:
                hour_multiplier = 0.5  # more frequent
            else:
                hour_multiplier = 1.5  # slower
            delay = next_delay(mean_interval=mean_interval * hour_multiplier, burstiness=burstiness)
            time.sleep(delay)
    finally:
        if outfile:
            outfile.close()

# --- If executed as script, provide CLI ---
SCRIPT = """
Save this block as pos_streamer.py and run with arguments, or use the function directly from Python.
"""

# For demonstration: generate 5 quick transactions printed to console.
if __name__ == "__main__":
    print("Demo: generating 5 sample transactions (fast)")
    for i in range(5):
        tx = generate_transaction(store_ids=(1,2,3), currency="USD")
        print(json.dumps(tx, ensure_ascii=False))
        time.sleep(0.05)
