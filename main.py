import yfinance as yf
import requests
import pandas as pd
import time
import os
from datetime import datetime

# ── Config ──
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
LEGIN_PCT        = float(os.environ.get("LEGIN_PCT", "70"))
BASE_PCT         = float(os.environ.get("BASE_PCT", "50"))
LEGOUT_MUL       = float(os.environ.get("LEGOUT_MUL", "1.0"))
SCAN_INTERVAL    = int(os.environ.get("SCAN_INTERVAL", "60"))

CRYPTO_SYMBOLS = ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD"]
INDIAN_SYMBOLS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "^NSEI", "^BSESN"]
FOREX_SYMBOLS  = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "USDINR=X"]
TIMEFRAMES     = ["15m", "30m", "1h", "4h", "1d", "1wk"]

PERIOD_MAP = {"15m":"2d","30m":"5d","1h":"7d","4h":"15d","1d":"60d","1wk":"1y"}

# ── State ──
alerted      = set()
active_zones = {}

# ══════════════════════════════════
# HELPERS
# ══════════════════════════════════
def body(r):     return abs(r["Close"] - r["Open"])
def rng(r):      return r["High"] - r["Low"]
def body_pct(r): return body(r) / rng(r) * 100 if rng(r) != 0 else 0
def is_bull(r):  return r["Close"] >= r["Open"]
def is_bear(r):  return r["Close"] <  r["Open"]
def bbhigh(r):   return max(r["Open"], r["Close"])
def bblow(r):    return min(r["Open"], r["Close"])

def detect_latest(df):
    """Sirf last 3 candles check karo — [2]=Legin [1]=Base [0]=Legout"""
    if len(df) < 3:
        return None
    lg = df.iloc[-3]   # Legin
    bs = df.iloc[-2]   # Base
    lo = df.iloc[-1]   # Legout (latest closed candle)

    if not (body_pct(lg) >= LEGIN_PCT and body_pct(bs) < BASE_PCT and body(lo) >= body(lg) * LEGOUT_MUL):
        return None

    if   is_bull(lg) and is_bull(lo): pat,zt,ep,sl = "RBR","DEMAND",bblow(bs), bbhigh(bs)
    elif is_bull(lg) and is_bear(lo): pat,zt,ep,sl = "RBD","SUPPLY",bbhigh(bs),bblow(bs)
    elif is_bear(lg) and is_bear(lo): pat,zt,ep,sl = "DBD","SUPPLY",bbhigh(bs),bblow(bs)
    elif is_bear(lg) and is_bull(lo): pat,zt,ep,sl = "DBR","DEMAND",bblow(bs), bbhigh(bs)
    else: return None

    return {"pattern":pat,"zone_type":zt,"entry":round(ep,6),"sl":round(sl,6),
            "zone_high":round(bs["High"],6),"zone_low":round(bs["Low"],6),
            "legout_time":str(lo.name)}

def fetch(symbol, tf):
    try:
        df = yf.Ticker(symbol).history(period=PERIOD_MAP.get(tf,"7d"), interval=tf)
        if df.empty: return None
        return df[["Open","High","Low","Close","Volume"]].dropna()
    except: return None

def send(text):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                    json={"chat_id":TELEGRAM_CHAT_ID,"text":text,"parse_mode":"HTML"}, timeout=10)
    except Exception as e:
        print(f"[SEND ERROR] {e}")

def pat_msg(sym, tf, p):
    e = "🟢" if p["zone_type"]=="DEMAND" else "🔴"
    return (f"{e} <b>{p['pattern']} Pattern Formed!</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📊 Symbol    : <b>{sym}</b>\n"
            f"⏱ Timeframe : <b>{tf}</b>\n"
            f"🎯 Zone      : <b>{p['zone_type']}</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📍 Entry     : <b>{p['entry']}</b>\n"
            f"🛑 SL        : <b>{p['sl']}</b>\n"
            f"📦 Zone      : {p['zone_low']} — {p['zone_high']}")

def retest_msg(sym, tf, p, price):
    e = "🟢" if p["zone_type"]=="DEMAND" else "🔴"
    return (f"⚡ <b>{p['pattern']} RETEST!</b>\n"
            f"📊 {sym} | {tf}\n"
            f"💰 Price : <b>{price}</b>\n"
            f"📍 Entry : <b>{p['entry']}</b>\n"
            f"🛑 SL    : <b>{p['sl']}</b>\n"
            f"{e} Price entered <b>{p['zone_type']}</b> zone!")

def sl_msg(sym, tf, p, price):
    return (f"❌ <b>{p['pattern']} Zone INVALIDATED</b>\n"
            f"📊 {sym} | {tf}\n"
            f"💰 Price : <b>{price}</b>\n"
            f"🛑 SL Hit: <b>{p['sl']}</b>")

def scan_symbol(sym, tf):
    df = fetch(sym, tf)
    if df is None or len(df) < 3: return
    price = round(df["Close"].iloc[-1], 6)

    # ── Check latest pattern (only last 3 candles) ──
    p = detect_latest(df)
    if p:
        pk = f"{sym}_{tf}_{p['legout_time']}_{p['pattern']}"
        zk = f"{sym}_{tf}_{p['legout_time']}"
        if pk not in alerted:
            alerted.add(pk)
            active_zones[zk] = {**p}
            send(pat_msg(sym, tf, p))
            print(f"[NEW] {sym} {tf} {p['pattern']} @ {datetime.now()}")

    # ── Check active zones for retest/SL ──
    to_delete = []
    for zk, z in active_zones.items():
        if not zk.startswith(f"{sym}_{tf}_"): continue
        bull = z["zone_type"] == "DEMAND"
        slk  = zk + "_sl"
        rtk  = zk + "_retest"

        if (bull and price < z["sl"]) or (not bull and price > z["sl"]):
            if slk not in alerted:
                alerted.add(slk)
                send(sl_msg(sym, tf, z, price))
                to_delete.append(zk)
                print(f"[SL] {sym} {tf}")
        elif rtk not in alerted:
            if (bull and price <= z["entry"]) or (not bull and price >= z["entry"]):
                alerted.add(rtk)
                send(retest_msg(sym, tf, z, price))
                print(f"[RETEST] {sym} {tf}")

    for zk in to_delete:
        if zk in active_zones:
            del active_zones[zk]

def scan_all():
    print(f"\n[SCAN] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    for syms in [CRYPTO_SYMBOLS, INDIAN_SYMBOLS, FOREX_SYMBOLS]:
        for sym in syms:
            for tf in TIMEFRAMES:
                try:
                    scan_symbol(sym, tf)
                    time.sleep(0.5)
                except Exception as e:
                    print(f"[ERROR] {sym} {tf}: {e}")

def main():
    print("🚀 SD Alert Bot Started!")
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ ERROR: TELEGRAM_TOKEN aur TELEGRAM_CHAT_ID set karo!")
        return
    send("🤖 <b>SD Alert Bot Started!</b>\n📊 Sirf FRESH patterns alert honge!")
    while True:
        try:
            scan_all()
        except Exception as e:
            print(f"[MAIN ERROR] {e}")
        print(f"[WAIT] {SCAN_INTERVAL}s...")
        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
