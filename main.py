import yfinance as yf
import requests
import pandas as pd
import time
import os
from datetime import datetime

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
LEGIN_BODY_PCT   = float(os.environ.get("LEGIN_PCT", "70"))
SCAN_INTERVAL    = int(os.environ.get("SCAN_INTERVAL", "60"))

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
    "ASHOKLEY.NS","TVSMOTOR.NS","BALKRISIND.NS","JUBLFOOD.NS","^NSEI","^BSESN"
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
COMMODITY_SYMBOLS = ["GC=F","SI=F","CL=F","BZ=F","NG=F","HG=F","BTC-USD"]

NAME_MAP = {
    "GC=F":"XAUUSD","SI=F":"XAGUSD","CL=F":"WTI_OIL","BZ=F":"BRENT",
    "NG=F":"NAT_GAS","HG=F":"COPPER","BTC-USD":"BTCUSD",
    "^NSEI":"NIFTY50","^BSESN":"SENSEX",
    "SPY":"SP500","QQQ":"NASDAQ","DIA":"DOW","IWM":"RUSSELL"
}
def dn(sym): return NAME_MAP.get(sym, sym.replace(".NS","").replace("=X","").replace("-USD","USD").replace("=F",""))

CUSTOM_TIMEFRAMES = {
    "5m"  : {"fetch":"5m",  "resample":None,  "period":"1d"},
    "15m" : {"fetch":"15m", "resample":None,  "period":"2d"},
    "30m" : {"fetch":"30m", "resample":None,  "period":"5d"},
    "75m" : {"fetch":"15m", "resample":"75T", "period":"5d"},
    "125m": {"fetch":"5m",  "resample":"125T","period":"5d"},
    "1h"  : {"fetch":"1h",  "resample":None,  "period":"7d"},
    "2h"  : {"fetch":"1h",  "resample":"2h",  "period":"10d"},
    "4h"  : {"fetch":"1h",  "resample":"4h",  "period":"15d"},
    "5h"  : {"fetch":"1h",  "resample":"5h",  "period":"20d"},
    "6h"  : {"fetch":"1h",  "resample":"6h",  "period":"20d"},
    "8h"  : {"fetch":"1h",  "resample":"8h",  "period":"30d"},
    "10h" : {"fetch":"1h",  "resample":"10h", "period":"30d"},
    "16h" : {"fetch":"1h",  "resample":"16h", "period":"40d"},
    "1d"  : {"fetch":"1d",  "resample":None,  "period":"60d"},
    "1wk" : {"fetch":"1wk", "resample":None,  "period":"1y"},
}
INDIAN_TF     = ["5m","15m","75m","125m","2h","4h","1d","1wk"]
NON_INDIAN_TF = ["15m","30m","75m","125m","1h","2h","4h","5h","6h","8h","10h","16h","1d","1wk"]

alerted      = set()
active_zones = {}

# ══════════════════════════════════
# CANDLE HELPERS
# ══════════════════════════════════
def body(r):      return abs(r["Close"] - r["Open"])
def rng(r):       return r["High"] - r["Low"]
def body_pct(r):  return body(r) / rng(r) * 100 if rng(r) != 0 else 0
def is_bull(r):   return r["Close"] >= r["Open"]
def is_bear(r):   return r["Close"] <  r["Open"]
def bbhigh(r):    return max(r["Open"], r["Close"])
def bblow(r):     return min(r["Open"], r["Close"])

def resample_df(df, rule):
    return df.resample(rule).agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna()

def fetch(symbol, tf_key):
    cfg = CUSTOM_TIMEFRAMES.get(tf_key)
    if not cfg: return None
    try:
        df = yf.Ticker(symbol).history(period=cfg["period"], interval=cfg["fetch"])
        if df.empty: return None
        df = df[["Open","High","Low","Close","Volume"]].dropna()
        if cfg["resample"]: df = resample_df(df, cfg["resample"])
        return df if len(df) >= 5 else None
    except: return None

# ══════════════════════════════════
# PATTERN DETECTION
# Legin(1) + Base(1-3) + Legout(1-3)
# Max window = 7 candles
# ══════════════════════════════════
def detect_pattern(df):
    """
    Scan last 7 candles for best pattern.
    Returns pattern with most legouts (strength).
    """
    n = len(df)
    if n < 3: return None

    best = None

    # Try all combinations: legin at pos i, base 1-3, legout 1-3
    for legin_idx in range(min(7, n-2), 1, -1):
        lg = df.iloc[-legin_idx]

        # Legin condition: body >= 70% of range
        if body_pct(lg) < LEGIN_BODY_PCT: continue

        legin_body = body(lg)
        legin_bull = is_bull(lg)

        # Try base count 1, 2, 3
        for base_cnt in [1, 2, 3]:
            # Need at least 1 legout after base
            if legin_idx - base_cnt < 1: break

            # Check all base candles
            bases = [df.iloc[-(legin_idx - b)] for b in range(base_cnt)]
            base_ok = all(body(b) <= legin_body * 0.5 for b in bases)
            if not base_ok: continue

            # First legout position
            lo1_idx = legin_idx - base_cnt
            if lo1_idx < 1: break
            lo1 = df.iloc[-lo1_idx]

            # Legout1: body >= legin body, same direction as legin
            if body(lo1) < legin_body: continue
            if legin_bull and not is_bull(lo1): continue
            if not legin_bull and not is_bear(lo1): continue

            legout_cnt = 1

            # Check Legout2
            if lo1_idx > 1:
                lo2 = df.iloc[-(lo1_idx - 1)]
                lo2_ok = (legin_bull and is_bull(lo2)) or (not legin_bull and is_bear(lo2))
                if lo2_ok:
                    legout_cnt = 2
                    # Check Legout3
                    if lo1_idx > 2:
                        lo3 = df.iloc[-(lo1_idx - 2)]
                        lo3_ok = (legin_bull and is_bull(lo3)) or (not legin_bull and is_bear(lo3))
                        if lo3_ok:
                            legout_cnt = 3

            # Determine zone type
            if legin_bull:
                zt  = "DEMAND" if is_bull(lo1) else "SUPPLY"
            else:
                zt  = "SUPPLY" if is_bear(lo1) else "DEMAND"

            # Pattern name
            if legin_bull and is_bull(lo1):   pat = "RBR"
            elif legin_bull and is_bear(lo1): pat = "RBD"
            elif is_bear(lg) and is_bear(lo1):pat = "DBD"
            else:                              pat = "DBR"

            # Base zone = all base candles range
            base_high = max(b["High"] for b in bases)
            base_low  = min(b["Low"]  for b in bases)
            base_open = bases[0]["Open"]
            base_close= bases[-1]["Close"]
            base_bull = base_close >= base_open
            bbh = max(base_open, base_close)
            bbl = min(base_open, base_close)

            # Proximal / Distal
            if zt == "DEMAND":
                proximal = bbh if base_bull else base_open
                distal   = base_low
            else:
                proximal = bbl if not base_bull else base_open
                distal   = base_high

            # Legout time = last legout candle time
            last_lo_idx = lo1_idx - (legout_cnt - 1)
            last_lo = df.iloc[-last_lo_idx] if last_lo_idx >= 1 else lo1

            strength_map = {1: "🟡 Good", 2: "🟠 Very Good", 3: "🌟 The Best"}

            result = {
                "pattern"     : pat,
                "zone_type"   : zt,
                "proximal"    : round(proximal, 6),
                "distal"      : round(distal,   6),
                "zone_high"   : round(base_high, 6),
                "zone_low"    : round(base_low,  6),
                "base_count"  : base_cnt,
                "legout_count": legout_cnt,
                "strength"    : strength_map[legout_cnt],
                "fresh"       : True,
                "base_color"  : "🟢 Green" if base_bull else "🔴 Red",
                "legout_time" : str(last_lo.name),
            }

            # Keep best (most legouts)
            if best is None or legout_cnt > best["legout_count"]:
                best = result

    return best

def calc_entry_sl(p):
    return p["proximal"], p["distal"]

def send(text):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                    json={"chat_id":TELEGRAM_CHAT_ID,"text":text,"parse_mode":"HTML"}, timeout=10)
    except Exception as e: print(f"[SEND ERROR] {e}")

def pat_msg(sym, tf, p):
    e    = "🟢" if p["zone_type"]=="DEMAND" else "🔴"
    dir_ = "📈 BUY Zone" if p["zone_type"]=="DEMAND" else "📉 SELL Zone"
    fresh= "✅ FRESH" if p["fresh"] else "🔁 TESTED"
    return (
        f"{e} <b>{p['pattern']} Pattern Formed!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📊 Asset       : <b>{dn(sym)}</b>\n"
        f"⏱ Timeframe   : <b>{tf}</b>\n"
        f"🔷 Pattern     : <b>{p['pattern']}</b>\n"
        f"🎯 Type        : <b>{dir_}</b>\n"
        f"💪 Strength    : <b>{p['strength']}</b>\n"
        f"📦 Base Count  : <b>{p['base_count']}</b>\n"
        f"🚀 Legout Count: <b>{p['legout_count']}</b>\n"
        f"🕯 Base Color  : <b>{p['base_color']}</b>\n"
        f"🆕 Status      : <b>{fresh}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📍 Proximal    : <b>{p['proximal']}</b>  ← Entry\n"
        f"📏 Distal      : <b>{p['distal']}</b>    ← SL"
    )

def retest_msg(sym, tf, p, price):
    e = "🟢" if p["zone_type"]=="DEMAND" else "🔴"
    return (
        f"⚡ <b>{p['pattern']} RETEST!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📊 Asset     : <b>{dn(sym)}</b>\n"
        f"⏱ Timeframe : <b>{tf}</b>\n"
        f"🔷 Pattern   : <b>{p['pattern']}</b>\n"
        f"💪 Strength  : <b>{p['strength']}</b>\n"
        f"🔁 Status    : <b>TESTED</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 Price     : <b>{price}</b>\n"
        f"📍 Proximal  : <b>{p['proximal']}</b>  ← Entry\n"
        f"📏 Distal    : <b>{p['distal']}</b>    ← SL\n"
        f"{e} Price entered <b>{p['zone_type']}</b> zone!"
    )

def sl_msg(sym, tf, p, price):
    return (
        f"❌ <b>{p['pattern']} Zone INVALIDATED</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📊 Asset     : <b>{dn(sym)}</b>\n"
        f"⏱ Timeframe : <b>{tf}</b>\n"
        f"🔷 Pattern   : <b>{p['pattern']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 Price     : <b>{price}</b>\n"
        f"📏 Distal Hit: <b>{p['distal']}</b>\n"
        f"Zone removed ✂️"
    )

def scan_symbol(sym, tf):
    df = fetch(sym, tf)
    if df is None or len(df) < 5: return
    price = round(df["Close"].iloc[-1], 6)
    p = detect_pattern(df)
    if p:
        pk = f"{sym}_{tf}_{p['legout_time']}_{p['pattern']}"
        zk = f"{sym}_{tf}_{p['legout_time']}"
        if pk not in alerted:
            alerted.add(pk)
            active_zones[zk] = {**p}
            send(pat_msg(sym, tf, p))
            print(f"[NEW] {dn(sym)} {tf} {p['pattern']} Base:{p['base_count']} Legout:{p['legout_count']} {p['strength']}")
    for zk, z in list(active_zones.items()):
        if not zk.startswith(f"{sym}_{tf}_"): continue
        bull = z["zone_type"] == "DEMAND"
        slk, rtk = zk+"_sl", zk+"_retest"
        if (bull and price < z["distal"]) or (not bull and price > z["distal"]):
            if slk not in alerted:
                alerted.add(slk)
                send(sl_msg(sym, tf, z, price))
                active_zones.pop(zk, None)
        elif rtk not in alerted:
            if (bull and price <= z["proximal"]) or (not bull and price >= z["proximal"]):
                alerted.add(rtk)
                z["fresh"] = False
                send(retest_msg(sym, tf, z, price))

def scan_all():
    print(f"\n[SCAN] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    for sym in NIFTY100_SYMBOLS:
        for tf in INDIAN_TF:
            try: scan_symbol(sym, tf); time.sleep(0.2)
            except Exception as e: print(f"[ERR] {sym} {tf}: {e}")
    for syms in [US100_SYMBOLS, FOREX_SYMBOLS, COMMODITY_SYMBOLS]:
        for sym in syms:
            for tf in NON_INDIAN_TF:
                try: scan_symbol(sym, tf); time.sleep(0.2)
                except Exception as e: print(f"[ERR] {sym} {tf}: {e}")

def main():
    print("🚀 SD Alert Bot v7 Started!")
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID!"); return
    send("🤖 <b>SD Alert Bot v7 Started!</b>\n"
         "✅ New Pattern Logic:\n"
         "📦 Base: 1-3 candles (body ≤ 50% of Legin)\n"
         "🚀 Legout: 1-3 candles\n"
         "💪 Strength: 1=🟡Good 2=🟠VeryGood 3=🌟TheBest")
    while True:
        try: scan_all()
        except Exception as e: print(f"[MAIN ERR] {e}")
        print(f"[WAIT] {SCAN_INTERVAL}s...")
        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
