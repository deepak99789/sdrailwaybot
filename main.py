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

# ══════════════════════════════════
# SYMBOL LISTS
# ══════════════════════════════════
NIFTY100_SYMBOLS = [
    "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS",
    "HINDUNILVR.NS","SBIN.NS","BHARTIARTL.NS","ITC.NS","KOTAKBANK.NS",
    "LT.NS","AXISBANK.NS","ASIANPAINT.NS","MARUTI.NS","SUNPHARMA.NS",
    "TITAN.NS","ULTRACEMCO.NS","WIPRO.NS","NESTLEIND.NS","BAJFINANCE.NS",
    "HCLTECH.NS","POWERGRID.NS","NTPC.NS","TECHM.NS","ONGC.NS",
    "TATAMOTORS.NS","ADANIENT.NS","ADANIPORTS.NS","BAJAJFINSV.NS","COALINDIA.NS",
    "JSWSTEEL.NS","GRASIM.NS","DIVISLAB.NS","DRREDDY.NS","EICHERMOT.NS",
    "CIPLA.NS","BPCL.NS","TATACONSUM.NS","BRITANNIA.NS","APOLLOHOSP.NS",
    "HEROMOTOCO.NS","HINDALCO.NS","INDUSINDBK.NS","SBILIFE.NS","HDFCLIFE.NS",
    "BAJAJ-AUTO.NS","TATASTEEL.NS","UPL.NS","SHREECEM.NS","PIDILITIND.NS",
    "DMART.NS","HAVELLS.NS","BERGEPAINT.NS","DABUR.NS","MARICO.NS",
    "MCDOWELL-N.NS","COLPAL.NS","SIEMENS.NS","ADANIGREEN.NS","ADANITRANS.NS",
    "BOSCHLTD.NS","ICICIGI.NS","ICICIPRULI.NS","GODREJCP.NS","PAGEIND.NS",
    "TORNTPHARM.NS","LUPIN.NS","BIOCON.NS","AUROPHARMA.NS","CONCOR.NS",
    "NMDC.NS","VEDL.NS","SAIL.NS","INDUSTOWER.NS","DLF.NS",
    "AMBUJACEM.NS","ACC.NS","BANKBARODA.NS","PNB.NS","CANBK.NS",
    "FEDERALBNK.NS","IDFCFIRSTB.NS","PERSISTENT.NS","MPHASIS.NS","COFORGE.NS",
    "LTIM.NS","OFSS.NS","ZOMATO.NS","NYKAA.NS","POLICYBZR.NS",
    "IRCTC.NS","CHOLAFIN.NS","MUTHOOTFIN.NS","BAJAJHLDNG.NS","MOTHERSON.NS",
    "ASHOKLEY.NS","TVSMOTOR.NS","BALKRISIND.NS","JUBLFOOD.NS",
    "^NSEI","^BSESN"
]

US100_SYMBOLS = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","TSLA","AVGO","COST",
    "NFLX","ASML","AMD","PEP","ADBE","QCOM","CSCO","TMUS","TXN","AMAT",
    "INTU","ISRG","AMGN","MU","LRCX","KLAC","REGN","PANW","ADI","SNPS",
    "CDNS","MRVL","CRWD","FTNT","NXPI","ORLY","ADP","MNST","CTAS","PAYX",
    "MELI","WDAY","DXCM","ODFL","FAST","ROST","BIIB","IDXX","VRSK","TEAM",
    "CPRT","FANG","EA","ZS","ANSS","ILMN","ALGN","DLTR","WBA","SGEN",
    "ZM","DOCU","OKTA","DDOG","NET","SNOW","PLTR","COIN","RBLX","ABNB",
    "DASH","UBER","PINS","SNAP","SPOT","SHOP","SQ","PYPL","INTC","IBM",
    "ORCL","CRM","NOW","VEEV","HUBS","BILL","MDB","ESTC","CFLT","GTLB",
    "SPY","QQQ","DIA","IWM"
]

FOREX_SYMBOLS = [
    "EURUSD=X","GBPUSD=X","USDJPY=X","USDCHF=X","AUDUSD=X","USDCAD=X","NZDUSD=X",
    "EURGBP=X","EURJPY=X","EURCHF=X","EURAUD=X","EURCAD=X","EURNZD=X",
    "GBPJPY=X","GBPCHF=X","GBPAUD=X","GBPCAD=X","GBPNZD=X",
    "AUDJPY=X","AUDCHF=X","AUDCAD=X","AUDNZD=X",
    "CADJPY=X","CADCHF=X","NZDJPY=X","NZDCHF=X","NZDCAD=X","CHFJPY=X",
    "USDINR=X","USDSGD=X","USDMXN=X","USDZAR=X","USDTRY=X"
]

COMMODITY_SYMBOLS = [
    "GC=F","SI=F","CL=F","BZ=F","NG=F","HG=F","BTC-USD"
]

NAME_MAP = {
    "GC=F":"XAUUSD","SI=F":"XAGUSD","CL=F":"WTI_OIL",
    "BZ=F":"BRENT","NG=F":"NAT_GAS","HG=F":"COPPER",
    "BTC-USD":"BTCUSD","^NSEI":"NIFTY50","^BSESN":"SENSEX",
    "SPY":"SP500","QQQ":"NASDAQ","DIA":"DOW","IWM":"RUSSELL"
}

def display_name(sym):
    return NAME_MAP.get(sym, sym.replace(".NS","").replace("=X","").replace("-USD","USD").replace("=F",""))

# ══════════════════════════════════
# CUSTOM TIMEFRAME RESAMPLING
# ══════════════════════════════════
# base_tf -> fetch this from yfinance
# then resample to custom minutes
CUSTOM_TIMEFRAMES = {
    "15m" : {"fetch":"15m",  "resample":None,  "period":"2d"},
    "30m" : {"fetch":"30m",  "resample":None,  "period":"5d"},
    "75m" : {"fetch":"15m",  "resample":"75T", "period":"5d"},
    "125m": {"fetch":"5m",   "resample":"125T","period":"5d"},
    "1h"  : {"fetch":"1h",   "resample":None,  "period":"7d"},
    "2h"  : {"fetch":"1h",   "resample":"2h",  "period":"10d"},
    "4h"  : {"fetch":"1h",   "resample":"4h",  "period":"15d"},
    "5h"  : {"fetch":"1h",   "resample":"5h",  "period":"20d"},
    "6h"  : {"fetch":"1h",   "resample":"6h",  "period":"20d"},
    "8h"  : {"fetch":"1h",   "resample":"8h",  "period":"30d"},
    "10h" : {"fetch":"1h",   "resample":"10h", "period":"30d"},
    "16h" : {"fetch":"1h",   "resample":"16h", "period":"40d"},
    "1d"  : {"fetch":"1d",   "resample":None,  "period":"60d"},
    "1wk" : {"fetch":"1wk",  "resample":None,  "period":"1y"},
}

ALL_TIMEFRAMES = list(CUSTOM_TIMEFRAMES.keys())

def resample_df(df, rule):
    """Resample OHLCV dataframe to custom timeframe"""
    df_resampled = df.resample(rule).agg({
        "Open" : "first",
        "High" : "max",
        "Low"  : "min",
        "Close": "last",
        "Volume":"sum"
    }).dropna()
    return df_resampled

def fetch(symbol, tf_key):
    cfg = CUSTOM_TIMEFRAMES[tf_key]
    try:
        df = yf.Ticker(symbol).history(period=cfg["period"], interval=cfg["fetch"])
        if df.empty: return None
        df = df[["Open","High","Low","Close","Volume"]].dropna()
        if cfg["resample"]:
            df = resample_df(df, cfg["resample"])
        return df if len(df) >= 3 else None
    except:
        return None

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
    if len(df) < 3: return None
    lg = df.iloc[-3]
    bs = df.iloc[-2]
    lo = df.iloc[-1]
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

def send(text):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                    json={"chat_id":TELEGRAM_CHAT_ID,"text":text,"parse_mode":"HTML"}, timeout=10)
    except Exception as e:
        print(f"[SEND ERROR] {e}")

def pat_msg(sym, tf, p):
    e   = "🟢" if p["zone_type"]=="DEMAND" else "🔴"
    dn  = display_name(sym)
    dir = "📈 BUY Zone" if p["zone_type"]=="DEMAND" else "📉 SELL Zone"
    return (f"{e} <b>{p['pattern']} Pattern Formed!</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📊 Symbol    : <b>{dn}</b>\n"
            f"⏱ Timeframe : <b>{tf}</b>\n"
            f"🎯 Type      : <b>{dir}</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📍 Entry     : <b>{p['entry']}</b>\n"
            f"🛑 SL        : <b>{p['sl']}</b>\n"
            f"📦 Zone      : {p['zone_low']} — {p['zone_high']}")

def retest_msg(sym, tf, p, price):
    e  = "🟢" if p["zone_type"]=="DEMAND" else "🔴"
    dn = display_name(sym)
    return (f"⚡ <b>{p['pattern']} RETEST!</b>\n"
            f"📊 {dn} | {tf}\n"
            f"💰 Price : <b>{price}</b>\n"
            f"📍 Entry : <b>{p['entry']}</b>\n"
            f"🛑 SL    : <b>{p['sl']}</b>\n"
            f"{e} Price entered <b>{p['zone_type']}</b> zone!")

def sl_msg(sym, tf, p, price):
    dn = display_name(sym)
    return (f"❌ <b>{p['pattern']} Zone INVALIDATED</b>\n"
            f"📊 {dn} | {tf}\n"
            f"💰 Price : <b>{price}</b>\n"
            f"🛑 SL Hit: <b>{p['sl']}</b>")

def scan_symbol(sym, tf):
    df = fetch(sym, tf)
    if df is None or len(df) < 3: return
    price = round(df["Close"].iloc[-1], 6)
    p = detect_latest(df)
    if p:
        pk = f"{sym}_{tf}_{p['legout_time']}_{p['pattern']}"
        zk = f"{sym}_{tf}_{p['legout_time']}"
        if pk not in alerted:
            alerted.add(pk)
            active_zones[zk] = {**p}
            send(pat_msg(sym, tf, p))
            print(f"[NEW] {display_name(sym)} {tf} {p['pattern']}")
    for zk, z in list(active_zones.items()):
        if not zk.startswith(f"{sym}_{tf}_"): continue
        bull = z["zone_type"] == "DEMAND"
        slk, rtk = zk+"_sl", zk+"_retest"
        if (bull and price < z["sl"]) or (not bull and price > z["sl"]):
            if slk not in alerted:
                alerted.add(slk)
                send(sl_msg(sym, tf, z, price))
                active_zones.pop(zk, None)
        elif rtk not in alerted:
            if (bull and price <= z["entry"]) or (not bull and price >= z["entry"]):
                alerted.add(rtk)
                send(retest_msg(sym, tf, z, price))

def scan_all():
    print(f"\n[SCAN] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    all_lists = [NIFTY100_SYMBOLS, US100_SYMBOLS, FOREX_SYMBOLS, COMMODITY_SYMBOLS]
    for syms in all_lists:
        for sym in syms:
            for tf in ALL_TIMEFRAMES:
                try:
                    scan_symbol(sym, tf)
                    time.sleep(0.2)
                except Exception as e:
                    print(f"[ERR] {sym} {tf}: {e}")

def main():
    print("🚀 SD Alert Bot v4 Started!")
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID!")
        return
    send("🤖 <b>SD Alert Bot v4 Started!</b>\n"
         "⏱ Timeframes: 15m 30m 75m 125m 1h 2h 4h 5h 6h 8h 10h 16h 1d 1wk\n"
         "🇮🇳 Nifty100 | 🇺🇸 US100 | 💱 Forex | 🏅 Commodities | ₿ BTC")
    while True:
        try:
            scan_all()
        except Exception as e:
            print(f"[MAIN ERR] {e}")
        print(f"[WAIT] {SCAN_INTERVAL}s...")
        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
