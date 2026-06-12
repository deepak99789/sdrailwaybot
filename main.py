import yfinance as yf
import requests
import pandas as pd
import time
import os
from datetime import datetime

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
LEGIN_PCT        = float(os.environ.get("LEGIN_PCT", "70"))
BASE_PCT         = float(os.environ.get("BASE_PCT", "50"))
LEGOUT_MUL       = float(os.environ.get("LEGOUT_MUL", "1.0"))
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

def body(r):     return abs(r["Close"] - r["Open"])
def rng(r):      return r["High"] - r["Low"]
def body_pct(r): return body(r) / rng(r) * 100 if rng(r) != 0 else 0
def is_bull(r):  return r["Close"] >= r["Open"]
def is_bear(r):  return r["Close"] <  r["Open"]
def bbhigh(r):   return max(r["Open"], r["Close"])
def bblow(r):    return min(r["Open"], r["Close"])

def calc_entry_sl(bs, zone_type):
    """
    DEMAND:
      Base Green → Proximal(Entry) = base body HIGH | Distal(SL) = base candle LOW
      Base Red   → Proximal(Entry) = base OPEN      | Distal(SL) = base candle LOW
    SUPPLY:
      Base Red   → Proximal(Entry) = base body LOW  | Distal(SL) = base candle HIGH
      Base Green → Proximal(Entry) = base OPEN      | Distal(SL) = base candle HIGH
    """
    bbh = bbhigh(bs)
    bbl = bblow(bs)
    base_bull = is_bull(bs)

    if zone_type == "DEMAND":
        proximal = bbh if base_bull else bs["Open"]
        distal   = bs["Low"]
    else:  # SUPPLY
        proximal = bbl if not base_bull else bs["Open"]
        distal   = bs["High"]

    return round(proximal, 6), round(distal, 6)

def calc_strength(lg, bs, lo):
    ls = body_pct(lg) / 100
    os_ = min(body(lo) / body(lg), 3.0) / 3.0
    bs_ = 1 - (body_pct(bs) / 100)
    return round(min(max((ls + os_ + bs_) / 3 * 5, 1), 5), 1)

def strength_stars(s):
    f = int(round(s))
    return "⭐" * f + "☆" * (5 - f)

def resample_df(df, rule):
    return df.resample(rule).agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna()

def fetch(symbol, tf_key):
    cfg = CUSTOM_TIMEFRAMES.get(tf_key)
    if not cfg: return None
    try:
        df = yf.Ticker(symbol).history(period=cfg["period"], interval=cfg["fetch"])
        if df.empty: return None
        df = df[["Open","High","Low","Close","Volume"]].dropna()
        if cfg["resample"]:
            df = resample_df(df, cfg["resample"])
        return df if len(df) >= 3 else None
    except: return None

def detect_latest(df):
    if len(df) < 3: return None
    lg = df.iloc[-3]
    bs = df.iloc[-2]
    lo = df.iloc[-1]
    if not (body_pct(lg) >= LEGIN_PCT and body_pct(bs) < BASE_PCT and body(lo) >= body(lg) * LEGOUT_MUL):
        return None
    if   is_bull(lg) and is_bull(lo): pat, zt = "RBR", "DEMAND"
    elif is_bull(lg) and is_bear(lo): pat, zt = "RBD", "SUPPLY"
    elif is_bear(lg) and is_bear(lo): pat, zt = "DBD", "SUPPLY"
    elif is_bear(lg) and is_bull(lo): pat, zt = "DBR", "DEMAND"
    else: return None

    proximal, distal = calc_entry_sl(bs, zt)
    strength = calc_strength(lg, bs, lo)
    base_color = "🟢 Green" if is_bull(bs) else "🔴 Red"

    return {
        "pattern"     : pat,
        "zone_type"   : zt,
        "proximal"    : proximal,
        "distal"      : distal,
        "zone_high"   : round(bs["High"], 6),
        "zone_low"    : round(bs["Low"],  6),
        "strength"    : strength,
        "base_count"  : 1,
        "legout_count": 1,
        "fresh"       : True,
        "base_color"  : base_color,
        "legout_time" : str(lo.name),
    }

def send(text):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                    json={"chat_id":TELEGRAM_CHAT_ID,"text":text,"parse_mode":"HTML"}, timeout=10)
    except Exception as e:
        print(f"[SEND ERROR] {e}")

def pat_msg(sym, tf, p):
    e     = "🟢" if p["zone_type"]=="DEMAND" else "🔴"
    dir_  = "📈 BUY Zone"  if p["zone_type"]=="DEMAND" else "📉 SELL Zone"
    fresh = "✅ FRESH"     if p["fresh"]      else "🔁 TESTED"
    stars = strength_stars(p["strength"])
    return (
        f"{e} <b>{p['pattern']} Pattern Formed!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📊 Asset       : <b>{dn(sym)}</b>\n"
        f"⏱ Timeframe   : <b>{tf}</b>\n"
        f"🔷 Pattern     : <b>{p['pattern']}</b>\n"
        f"🎯 Type        : <b>{dir_}</b>\n"
        f"💪 Strength    : <b>{stars} ({p['strength']}/5)</b>\n"
        f"📦 Base Count  : <b>{p['base_count']}</b>\n"
        f"🚀 Legout Count: <b>{p['legout_count']}</b>\n"
        f"🕯 Base Color  : <b>{p['base_color']}</b>\n"
        f"🆕 Status      : <b>{fresh}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📍 Proximal    : <b>{p['proximal']}</b>  ← Entry\n"
        f"📏 Distal      : <b>{p['distal']}</b>    ← SL"
    )

def retest_msg(sym, tf, p, price):
    e     = "🟢" if p["zone_type"]=="DEMAND" else "🔴"
    stars = strength_stars(p["strength"])
    return (
        f"⚡ <b>{p['pattern']} RETEST!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📊 Asset     : <b>{dn(sym)}</b>\n"
        f"⏱ Timeframe : <b>{tf}</b>\n"
        f"🔷 Pattern   : <b>{p['pattern']}</b>\n"
        f"💪 Strength  : <b>{stars} ({p['strength']}/5)</b>\n"
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
            print(f"[NEW] {dn(sym)} {tf} {p['pattern']} Prox:{p['proximal']} Dist:{p['distal']}")
    for zk, z in list(active_zones.items()):
        if not zk.startswith(f"{sym}_{tf}_"): continue
        bull = z["zone_type"] == "DEMAND"
        slk, rtk = zk+"_sl", zk+"_retest"
        # SL = price closes beyond Distal
        if (bull and close <= z["distal"]) or (not bull and close >= z["distal"]):
            if slk not in alerted:
                alerted.add(slk)
                send(sl_msg(sym, tf, z, price))
                active_zones.pop(zk, None)
        # Retest = price reaches Proximal
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
    print("🚀 SD Alert Bot v6 Started!")
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID!"); return
    send("🤖 <b>SD Alert Bot v6 Started!</b>\n"
         "✅ Fixed Entry/SL Logic:\n"
         "📍 Proximal = Entry Level\n"
         "📏 Distal = SL Level\n"
         "Based on Base candle color!")
    while True:
        try: scan_all()
        except Exception as e: print(f"[MAIN ERR] {e}")
        print(f"[WAIT] {SCAN_INTERVAL}s...")
        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
