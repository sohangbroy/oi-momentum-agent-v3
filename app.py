"""
╔══════════════════════════════════════════════════════════════════════╗
║   OI MOMENTUM AGENT v3 — COMPLETE UPGRADE                           ║
╠══════════════════════════════════════════════════════════════════════╣
║   1. Pre-market: Gift Nifty + FII + DII 9:00–9:15                  ║
║   2. Rolling 3-MIN OI snapshot — always vs 3 mins ago              ║
║   3. 8 ITM option buy setups — strict ITM buyer only               ║
║   4. Delta filter: CE ≥ +0.62 (bull) | PE ≤ -0.62 (bear)          ║
║   5. 3 sounds: hand-bell (aggression) > chime (planned) > soft     ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta, date
import time as time_module
import math

# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="OI Agent v3", page_icon="🎯",
                   layout="wide", initial_sidebar_state="expanded")

# ─────────────────────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Orbitron:wght@700;900&display=swap');

[data-testid="stAppViewContainer"]{background:#030508;font-family:'JetBrains Mono',monospace;}
[data-testid="stSidebar"]{background:#080d14;border-right:1px solid #131f2e;}
[data-testid="stHeader"]{background:#030508;}
h1,h2,h3{font-family:'JetBrains Mono',monospace !important;}

.phase-premarket {background:rgba(0,170,255,0.12);border:1px solid rgba(0,170,255,0.4);color:#00aaff;padding:5px 14px;border-radius:3px;font-size:0.65rem;letter-spacing:2px;}
.phase-opening   {background:rgba(255,170,0,0.15);border:1px solid rgba(255,170,0,0.5);color:#ffaa00;padding:5px 14px;border-radius:3px;font-size:0.65rem;letter-spacing:2px;animation:blink 1s infinite;}
.phase-aggression{background:rgba(255,45,85,0.15);border:1px solid rgba(255,45,85,0.5);color:#ff2d55;padding:5px 14px;border-radius:3px;font-size:0.65rem;letter-spacing:2px;animation:blink 0.6s infinite;}
.phase-afternoon {background:rgba(0,229,160,0.12);border:1px solid rgba(0,229,160,0.4);color:#00e5a0;padding:5px 14px;border-radius:3px;font-size:0.65rem;letter-spacing:2px;}
.phase-monitor   {background:rgba(255,255,255,0.03);border:1px solid #131f2e;color:#445566;padding:5px 14px;border-radius:3px;font-size:0.65rem;letter-spacing:2px;}
.phase-closed    {background:rgba(255,255,255,0.02);border:1px solid #0a1020;color:#2a3a4a;padding:5px 14px;border-radius:3px;font-size:0.65rem;letter-spacing:2px;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.35}}

/* SETUP CARDS */
.setup-card{background:#0c1420;border:1px solid #131f2e;border-radius:8px;padding:16px 20px;margin-bottom:10px;position:relative;overflow:hidden;}
.setup-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;}
.setup-bull::before{background:linear-gradient(90deg,#00e5a0,#00aaff);}
.setup-bear::before{background:linear-gradient(90deg,#ff2d55,#ff8800);}
.setup-number{font-family:'Orbitron',sans-serif;font-size:0.6rem;color:#445566;letter-spacing:3px;margin-bottom:6px;}
.setup-name{font-size:1rem;font-weight:700;margin-bottom:4px;}
.setup-strike{font-family:'Orbitron',sans-serif;font-size:1.4rem;font-weight:900;letter-spacing:3px;margin:8px 0;}
.setup-delta{font-size:0.75rem;font-weight:600;padding:3px 10px;border-radius:3px;display:inline-block;margin-bottom:6px;}
.delta-ok-bull{background:rgba(0,229,160,0.15);color:#00e5a0;border:1px solid rgba(0,229,160,0.35);}
.delta-ok-bear{background:rgba(255,45,85,0.15);color:#ff2d55;border:1px solid rgba(255,45,85,0.35);}
.delta-fail{background:rgba(255,170,0,0.1);color:#ffaa00;border:1px solid rgba(255,170,0,0.3);}
.setup-trigger{font-size:0.65rem;color:#445566;line-height:1.7;margin-top:6px;}
.setup-badge{font-size:0.58rem;letter-spacing:2px;text-transform:uppercase;padding:2px 8px;border-radius:2px;display:inline-block;margin-bottom:4px;}
.badge-fire{background:rgba(255,45,85,0.15);color:#ff2d55;}
.badge-ready{background:rgba(255,170,0,0.1);color:#ffaa00;}
.badge-wait{background:rgba(255,255,255,0.05);color:#445566;}

/* SETUP GRID */
.setup-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;}

/* 3-min snapshot panel */
.snap-panel{background:#0c1420;border:1px solid #131f2e;border-radius:6px;padding:14px 18px;margin-bottom:12px;}
.snap-title{font-size:0.6rem;color:#445566;letter-spacing:2px;text-transform:uppercase;margin-bottom:10px;display:flex;justify-content:space-between;}
.snap-row{display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.03);font-size:0.72rem;}
.snap-row:last-child{border:none;}

/* Delta gauge */
.delta-gauge{display:flex;align-items:center;gap:8px;margin:4px 0;}
.delta-track{flex:1;height:6px;background:#131f2e;border-radius:3px;overflow:hidden;}
.delta-fill{height:100%;border-radius:3px;}

/* OI table */
.oi-wrap{background:#0c1420;border:1px solid #131f2e;border-radius:6px;overflow:hidden;margin-top:10px;}
.oi-hdr{padding:10px 16px;font-size:0.6rem;color:#445566;letter-spacing:2px;border-bottom:1px solid #131f2e;}
table{width:100%;border-collapse:collapse;font-size:0.72rem;}
th{background:#080d14;color:#445566;font-size:0.58rem;letter-spacing:1.5px;text-transform:uppercase;padding:8px 10px;border-bottom:1px solid #131f2e;text-align:center;}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,0.025);text-align:center;color:#ccdcf0;}
tr.atm-r td{background:rgba(255,170,0,0.07);color:#ffaa00;font-weight:600;}
tr:hover td{background:rgba(255,255,255,0.02);}
.ce-sp{color:#ff2d55 !important;font-weight:700;background:rgba(255,45,85,0.1);}
.pe-sp{color:#00e5a0 !important;font-weight:700;background:rgba(0,229,160,0.08);}
.unw{color:#ffaa00 !important;}
.itm-c{color:#00e5a0;}

/* PM cards */
.pm3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:12px;}
.pm-card{background:#0c1420;border:1px solid #131f2e;border-radius:6px;padding:12px 14px;}
.pm-lbl{font-size:0.56rem;color:#445566;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;}
.pm-val{font-size:1.1rem;font-family:'Orbitron',sans-serif;font-weight:700;}
.pm-sub{font-size:0.58rem;color:#445566;margin-top:3px;}

/* intent */
.intent-box{background:#0c1420;border:1px solid #131f2e;border-radius:8px;padding:16px 20px;margin-top:10px;position:relative;overflow:hidden;}
.intent-box::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;}
.ib-bull::before{background:#00e5a0;} .ib-bear::before{background:#ff2d55;} .ib-neut::before{background:#ffaa00;}

/* legend */
.leg-bar{display:flex;gap:12px;flex-wrap:wrap;padding:8px 16px;font-size:0.58rem;color:#445566;border-top:1px solid #131f2e;}
.leg{display:flex;align-items:center;gap:5px;}
.ld{width:8px;height:8px;border-radius:2px;}

.green{color:#00e5a0;} .red{color:#ff2d55;} .amber{color:#ffaa00;} .blue{color:#00aaff;}
.sec-hdr{font-size:0.6rem;color:#445566;letter-spacing:3px;text-transform:uppercase;margin:12px 0 8px;padding-bottom:5px;border-bottom:1px solid #131f2e;}

.mom-track{height:8px;background:#131f2e;border-radius:4px;overflow:hidden;margin:5px 0;}
.mom-fill{height:100%;border-radius:4px;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  3 SOUNDS
#  AGGRESSION = LOUD HAND BELL (repeated rapid high tone)
#  PLANNED    = TEMPLE CHIME (3 melodic tones)
#  NORMAL     = SOFT PING (single soft tone)
# ─────────────────────────────────────────────────────────────
st.markdown("""
<script>
function playSound(type) {
    var ctx = new (window.AudioContext || window.webkitAudioContext)();

    if (type === 'aggression') {
        // LOUD HAND BELL — 5 rapid sharp high tones, high volume
        for (var i = 0; i < 5; i++) {
            var osc = ctx.createOscillator();
            var gain = ctx.createGain();
            var dist = ctx.createWaveShaper();
            osc.connect(gain); gain.connect(ctx.destination);
            osc.type = 'triangle';
            osc.frequency.value = 1480 - (i * 40);  // descending bell
            gain.gain.setValueAtTime(0.9, ctx.currentTime + i * 0.18);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.18 + 0.35);
            osc.start(ctx.currentTime + i * 0.18);
            osc.stop(ctx.currentTime + i * 0.18 + 0.35);
        }
        // Add a deeper bell undertone
        var bass = ctx.createOscillator();
        var bGain = ctx.createGain();
        bass.connect(bGain); bGain.connect(ctx.destination);
        bass.type = 'sine'; bass.frequency.value = 440;
        bGain.gain.setValueAtTime(0.4, ctx.currentTime);
        bGain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.8);
        bass.start(ctx.currentTime); bass.stop(ctx.currentTime + 0.8);

    } else if (type === 'planned') {
        // TEMPLE CHIME — 3 clean melodic descending tones
        var notes = [987, 784, 659];
        for (var j = 0; j < 3; j++) {
            var o2 = ctx.createOscillator();
            var g2 = ctx.createGain();
            o2.connect(g2); g2.connect(ctx.destination);
            o2.type = 'sine'; o2.frequency.value = notes[j];
            g2.gain.setValueAtTime(0.5, ctx.currentTime + j * 0.35);
            g2.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + j * 0.35 + 0.55);
            o2.start(ctx.currentTime + j * 0.35);
            o2.stop(ctx.currentTime + j * 0.35 + 0.55);
        }

    } else {
        // SOFT PING — single gentle tone
        var o3 = ctx.createOscillator();
        var g3 = ctx.createGain();
        o3.connect(g3); g3.connect(ctx.destination);
        o3.type = 'sine'; o3.frequency.value = 660;
        g3.gain.setValueAtTime(0.2, ctx.currentTime);
        g3.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
        o3.start(ctx.currentTime); o3.stop(ctx.currentTime + 0.4);
    }
}
</script>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  MARKET PHASE
# ─────────────────────────────────────────────────────────────
def get_phase():
    n = datetime.now().time()
    if   time(9,  0) <= n < time(9, 15): return "PRE_MARKET"
    elif time(9, 15) <= n < time(9, 20): return "OPENING_BURST"
    elif time(9, 20) <= n < time(9, 35): return "AGGRESSION"
    elif time(9, 35) <= n < time(13, 0): return "MONITORING"
    elif time(13, 0) <= n < time(14,30): return "AFTERNOON"
    elif time(14,30) <= n < time(15, 0): return "MONITORING"
    elif time(15, 0) <= n < time(15,30): return "EXPIRY_CLOSE"
    elif time(15,30) <= n < time(16, 0): return "POST_MARKET"
    else:                                 return "CLOSED"

PHASE_LABELS = {
    "PRE_MARKET":    ("🌅 PRE-MARKET 9:00–9:15 — Reading Gift Nifty + FII + DII", "phase-premarket"),
    "OPENING_BURST": ("🔥 9:15–9:20 — TAKING OI SNAPSHOT + WATCHING FIRST 5 MIN", "phase-opening"),
    "AGGRESSION":    ("⚡ 9:20–9:35 — 3-MIN AGGRESSION DETECTION ACTIVE",          "phase-aggression"),
    "MONITORING":    ("👁 MONITORING — 3-min OI rolling",                           "phase-monitor"),
    "AFTERNOON":     ("⚡ 1:00–2:30 AFTERNOON WINDOW ACTIVE",                       "phase-afternoon"),
    "EXPIRY_CLOSE":  ("🎯 3:00–3:30 EXPIRY CLOSE",                                 "phase-opening"),
    "POST_MARKET":   ("🌆 POST MARKET",                                             "phase-monitor"),
    "CLOSED":        ("💤 MARKET CLOSED",                                           "phase-closed"),
}
def is_alert(p): return p in ["OPENING_BURST","AGGRESSION","AFTERNOON","EXPIRY_CLOSE"]


# ─────────────────────────────────────────────────────────────
#  DHAN API
# ─────────────────────────────────────────────────────────────
class DhanAPI:
    BASE = "https://api.dhan.co"
    INDICES = {
        "NIFTY 50":   {"scrip":13,  "lot":75,  "step":50,
                       "levels":[22000,22100,22200,22300,22400,22500,22600,22700,22800,22900,23000]},
        "BANK NIFTY": {"scrip":25,  "lot":30,  "step":100,
                       "levels":[51000,51500,52000,52500,53000,53500,54000,54500,55000]},
    }
    def __init__(self, cid, tok):
        self.h = {"access-token":tok,"client-id":cid,
                  "Content-Type":"application/json","Accept":"application/json"}

    def option_chain(self, scrip, expiry):
        try:
            r = requests.post(f"{self.BASE}/v2/optionchain", headers=self.h,
                json={"UnderlyingScripCode":scrip,"UnderlyingSecId":"0","ExpiryDate":expiry},
                timeout=15)
            if r.status_code == 200: return r.json()
            st.error(f"API {r.status_code}: {r.text[:120]}")
        except requests.Timeout: st.warning("Timeout — retry next cycle")
        except Exception as e:   st.error(f"Error: {e}")
        return {}

    def ltp(self, scrip):
        try:
            r = requests.post(f"{self.BASE}/v2/marketfeed/ltp", headers=self.h,
                json={"NSE":[str(scrip)]}, timeout=8)
            if r.status_code==200:
                return float(r.json().get("data",{}).get("NSE",{}).get(str(scrip),{}).get("last_price",0))
        except: pass
        return 0.0

    def prev_close(self, scrip):
        try:
            t = date.today(); p = t - timedelta(days=1)
            r = requests.post(f"{self.BASE}/v2/charts/historical", headers=self.h,
                json={"securityId":str(scrip),"exchangeSegment":"NSE_EQ","instrument":"INDEX",
                      "expiryCode":0,"fromDate":p.strftime("%Y-%m-%d"),
                      "toDate":t.strftime("%Y-%m-%d"),"oi":False}, timeout=10)
            if r.status_code==200:
                c = r.json().get("close",[])
                return float(c[-1]) if c else 0.0
        except: pass
        return 0.0


# ─────────────────────────────────────────────────────────────
#  FREE DATA — Gift Nifty + FII + DII
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_gift():
    try:
        r = requests.get(
            "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?interval=1m&range=1d",
            headers={"User-Agent":"Mozilla/5.0"}, timeout=8)
        if r.status_code==200:
            meta = r.json()["chart"]["result"][0]["meta"]
            p = meta.get("regularMarketPrice",0)
            pc= meta.get("previousClose",p)
            chg = p-pc; pct=(chg/pc*100) if pc else 0
            return {"price":p,"change":chg,"pct":pct,
                    "dir":"BULLISH" if chg>0 else "BEARISH","src":"NSE Spot (pre-open proxy)"}
    except: pass
    return {"price":0,"change":0,"pct":0,"dir":"UNKNOWN","src":"Unavailable"}

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fii_dii():
    """Returns FII + DII provisional data from NSE."""
    try:
        r = requests.get("https://www.nseindia.com/api/fiidiiTradeReact",
            headers={"User-Agent":"Mozilla/5.0","Accept":"application/json",
                     "Referer":"https://www.nseindia.com"}, timeout=10)
        if r.status_code==200:
            d = r.json()
            if isinstance(d,list) and d:
                l = d[0]
                fn = float(l.get("fiiNetSell",0) or 0)
                dn = float(l.get("diiNetBuy",0) or 0)
                # FII cash
                fii_buy  = float(l.get("fiiBuySell","0").split("|")[0] if "|" in str(l.get("fiiBuySell","")) else l.get("fiiBuy",0) or 0)
                fii_sell = float(l.get("fiiBuySell","0").split("|")[1] if "|" in str(l.get("fiiBuySell","")) else l.get("fiiSale",0) or 0)
                dii_buy  = float(l.get("diiBuySell","0").split("|")[0] if "|" in str(l.get("diiBuySell","")) else l.get("diiBuy",0) or 0)
                dii_sell = float(l.get("diiBuySell","0").split("|")[1] if "|" in str(l.get("diiBuySell","")) else l.get("diiSale",0) or 0)
                return {
                    "fii_net":fn,"dii_net":dn,
                    "fii_buy":fii_buy,"fii_sell":fii_sell,
                    "dii_buy":dii_buy,"dii_sell":dii_sell,
                    "fii_dir":"BUYING" if fn>0 else "SELLING",
                    "dii_dir":"BUYING" if dn>0 else "SELLING",
                    "intent": "BULLISH" if fn>500 else "BEARISH" if fn<-500 else "NEUTRAL",
                    "src":"NSE Provisional"
                }
    except: pass
    return {"fii_net":0,"dii_net":0,"fii_buy":0,"fii_sell":0,"dii_buy":0,"dii_sell":0,
            "fii_dir":"UNKNOWN","dii_dir":"UNKNOWN","intent":"UNKNOWN","src":"Unavailable"}

def score_intent(gift, fd, prev_c, spot):
    s = 50
    gp = gift.get("pct",0)
    if gp > 0.5:  s += min(25, gp*8)
    elif gp < -0.5: s -= min(25, abs(gp)*8)
    fn = fd.get("fii_net",0)
    dn = fd.get("dii_net",0)
    if fn > 1000: s += 22
    elif fn > 500: s += 12
    elif fn > 0:   s += 5
    elif fn < -1000: s -= 22
    elif fn < -500:  s -= 12
    elif fn < 0:     s -= 5
    # DII direction
    if dn > 500: s += 8
    elif dn < -500: s -= 8
    if prev_c>0 and spot>0:
        gp2 = (spot-prev_c)/prev_c*100
        if gp2 > 0.3: s += 8
        elif gp2 < -0.3: s -= 8
    s = max(0, min(100, s))
    if s >= 65:   return {"score":s,"dir":"PLANNED BULLISH","mtype":"PLANNED","reason":f"Gift {gp:+.2f}% + FII ₹{fn:+,.0f}Cr + DII ₹{dn:+,.0f}Cr → PLANNED BUY","bull":s,"bear":100-s}
    elif s <= 35: return {"score":s,"dir":"PLANNED BEARISH","mtype":"PLANNED","reason":f"Gift {gp:+.2f}% + FII ₹{fn:+,.0f}Cr + DII ₹{dn:+,.0f}Cr → PLANNED SELL","bull":s,"bear":100-s}
    else:         return {"score":s,"dir":"REACTIVE — WAIT","mtype":"REACTIVE","reason":"Mixed signals — confirm at 9:20 via OI aggression","bull":s,"bear":100-s}


# ─────────────────────────────────────────────────────────────
#  DELTA CALCULATOR
#  Uses Black-Scholes approximation from IV + moneyness
#  If IV unavailable → estimate from moneyness depth
# ─────────────────────────────────────────────────────────────
def calc_delta_ce(spot, strike, iv_pct, days_to_expiry=7, r=0.065):
    """Black-Scholes delta for CE."""
    try:
        if iv_pct <= 0 or days_to_expiry <= 0: raise ValueError
        T  = days_to_expiry / 365.0
        iv = iv_pct / 100.0
        d1 = (math.log(spot/strike) + (r + 0.5*iv**2)*T) / (iv * math.sqrt(T))
        # Cumulative normal distribution approximation
        return _norm_cdf(d1)
    except:
        # Fallback: moneyness-based estimate
        if spot <= 0 or strike <= 0: return 0.5
        m = (spot - strike) / spot  # positive = ITM CE
        return min(0.99, max(0.01, 0.5 + m * 5))

def calc_delta_pe(spot, strike, iv_pct, days_to_expiry=7, r=0.065):
    """Black-Scholes delta for PE (negative)."""
    try:
        if iv_pct <= 0 or days_to_expiry <= 0: raise ValueError
        T  = days_to_expiry / 365.0
        iv = iv_pct / 100.0
        d1 = (math.log(spot/strike) + (r + 0.5*iv**2)*T) / (iv * math.sqrt(T))
        return _norm_cdf(d1) - 1  # PE delta is negative
    except:
        if spot <= 0 or strike <= 0: return -0.5
        m = (strike - spot) / spot  # positive = ITM PE
        return max(-0.99, min(-0.01, -0.5 - m * 5))

def _norm_cdf(x):
    """Abramowitz & Stegun approximation of N(x)."""
    a = [0,0.319381530,-0.356563782,1.781477937,-1.821255978,1.330274429]
    t = 1.0 / (1.0 + 0.2316419 * abs(x))
    p = 1.0 - (1.0/math.sqrt(2*math.pi)) * math.exp(-0.5*x*x) * (
        a[1]*t + a[2]*t**2 + a[3]*t**3 + a[4]*t**4 + a[5]*t**5)
    return p if x >= 0 else 1.0 - p

def days_to_expiry(expiry_str):
    try:
        exp = datetime.strptime(expiry_str, "%Y-%m-%d").date()
        d = (exp - date.today()).days
        return max(1, d)
    except: return 7


# ─────────────────────────────────────────────────────────────
#  CHAIN PARSER
# ─────────────────────────────────────────────────────────────
def parse_chain(raw, spot, step, expiry_str):
    if not raw or "data" not in raw: return pd.DataFrame()
    rows = []
    dte = days_to_expiry(expiry_str)
    try:
        data = raw["data"]
        items = data if isinstance(data,list) else [
            {"strikePrice":k,"callOption":v.get("CE",{}),"putOption":v.get("PE",{})}
            for k,v in data.items()]
        for item in items:
            ce=item.get("callOption",{}); pe=item.get("putOption",{})
            strike = int(item.get("strikePrice",0))
            ce_iv = ce.get("impliedVolatility",0) or 0
            pe_iv = pe.get("impliedVolatility",0) or 0
            ce_delta = calc_delta_ce(spot, strike, ce_iv, dte)
            pe_delta = calc_delta_pe(spot, strike, pe_iv, dte)
            rows.append({
                "Strike":    strike,
                "CE_OI":     ce.get("openInterest",0),
                "CE_OI_Chg": ce.get("changeinOpenInterest",0),
                "CE_LTP":    ce.get("lastPrice",0),
                "CE_Vol":    ce.get("totalTradedVolume",0),
                "CE_IV":     ce_iv,
                "CE_Delta":  round(ce_delta,3),
                "PE_OI":     pe.get("openInterest",0),
                "PE_OI_Chg": pe.get("changeinOpenInterest",0),
                "PE_LTP":    pe.get("lastPrice",0),
                "PE_Vol":    pe.get("totalTradedVolume",0),
                "PE_IV":     pe_iv,
                "PE_Delta":  round(pe_delta,3),
            })
    except Exception as e:
        st.error(f"Parse: {e}"); return pd.DataFrame()

    df = pd.DataFrame(rows).sort_values("Strike").reset_index(drop=True)
    if df.empty: return df
    df["CE_Chg_Pct"] = df.apply(lambda r: r["CE_OI_Chg"]/r["CE_OI"]*100 if r["CE_OI"]>0 else 0, axis=1)
    df["PE_Chg_Pct"] = df.apply(lambda r: r["PE_OI_Chg"]/r["PE_OI"]*100 if r["PE_OI"]>0 else 0, axis=1)
    df["ATM"]  = df["Strike"].apply(lambda s: abs(s-spot)<step*1.5)
    df["Dist"] = (df["Strike"] - spot).abs()
    return df


# ─────────────────────────────────────────────────────────────
#  3-MINUTE ROLLING SNAPSHOT
# ─────────────────────────────────────────────────────────────
def update_3min_snapshot(key, df_now):
    """
    Saves OI snapshot every 3 minutes.
    Returns (df_3min_ago, minutes_ago) for comparison.
    """
    snaps = st.session_state.snaps.get(key, [])  # list of (datetime, df)
    now   = datetime.now()

    # Save new snapshot if 3+ minutes since last
    if not snaps or (now - snaps[-1][0]).total_seconds() >= 180:
        snaps.append((now, df_now[["Strike","CE_OI","PE_OI"]].copy()))
        # Keep last 10 snapshots (30 mins of history)
        if len(snaps) > 10: snaps = snaps[-10:]
        st.session_state.snaps[key] = snaps

    # Return snapshot from ~3 mins ago
    if len(snaps) >= 2:
        snap_time, snap_df = snaps[-2]
        mins_ago = round((now - snap_time).total_seconds() / 60, 1)
        return snap_df, mins_ago
    return pd.DataFrame(), 0


def compare_3min(df_now, df_3min, thr):
    """Compare current OI vs 3-min-ago OI. Returns per-strike delta %."""
    if df_3min.empty or df_now.empty: return pd.DataFrame()
    merged = pd.merge(
        df_now[["Strike","CE_OI","PE_OI","CE_LTP","PE_LTP","CE_Delta","PE_Delta","CE_IV","PE_IV","CE_Vol","PE_Vol","ATM","Dist"]],
        df_3min[["Strike","CE_OI","PE_OI"]].rename(columns={"CE_OI":"CE3","PE_OI":"PE3"}),
        on="Strike", how="inner")
    merged["CE_3min_Pct"] = merged.apply(lambda r: (r["CE_OI"]-r["CE3"])/r["CE3"]*100 if r["CE3"]>0 else 0, axis=1)
    merged["PE_3min_Pct"] = merged.apply(lambda r: (r["PE_OI"]-r["PE3"])/r["PE3"]*100 if r["PE3"]>0 else 0, axis=1)
    return merged


# ─────────────────────────────────────────────────────────────
#  8 ITM BUY SETUPS
#  All are strictly for OPTION BUYERS (not writers)
#  Delta filter: CE ≥ +0.62, PE ≤ -0.62
# ─────────────────────────────────────────────────────────────

DELTA_MIN_CE =  0.62  # minimum CE delta for ITM CE buy
DELTA_MAX_PE = -0.62  # maximum PE delta for ITM PE buy (more negative = deeper ITM)

SETUPS = {
    1: {"name":"PE WALL BUILD",       "dir":"BULL","desc":"PE OI +% in 3 min near ATM → support forming → Buy ITM CE"},
    2: {"name":"CE WALL BUILD",       "dir":"BEAR","desc":"CE OI +% in 3 min near ATM → resistance forming → Buy ITM PE"},
    3: {"name":"CE SHORT COVER",      "dir":"BULL","desc":"CE OI falling fast → call writers covering → Buy ITM CE"},
    4: {"name":"PE SHORT COVER",      "dir":"BEAR","desc":"PE OI falling fast → put longs exiting → Buy ITM PE"},
    5: {"name":"BULL IGNITION",       "dir":"BULL","desc":"PE writing + CE unwinding simultaneously → Buy ITM CE"},
    6: {"name":"BEAR IGNITION",       "dir":"BEAR","desc":"CE writing + PE unwinding simultaneously → Buy ITM PE"},
    7: {"name":"OPENING BURST",       "dir":"BOTH","desc":"Strongest 3-min OI direction in 9:15–9:35 → Buy ITM CE or PE"},
    8: {"name":"AFTERNOON OI FLIP",   "dir":"BOTH","desc":"OI direction flips after 1 PM dead zone → Buy ITM CE or PE"},
}

def run_8_setups(df_now, df_3min, spot, step, thr, phase):
    """
    Runs all 8 setups against current + 3-min data.
    Returns list of fired setups with strike suggestion.
    """
    if df_now.empty: return []

    cmp = compare_3min(df_now, df_3min, thr) if not df_3min.empty else pd.DataFrame()
    near_atm = df_now[df_now["Dist"] <= step * 5].copy()
    fired = []

    # ── Helper: find best ITM CE strike with delta ≥ 0.62 ──
    def best_itm_ce():
        itm = df_now[df_now["Strike"] < spot].copy()
        itm = itm[itm["CE_Delta"] >= DELTA_MIN_CE]
        if itm.empty: return None
        # Closest ITM CE with delta ≥ 0.62
        row = itm.iloc[(itm["Strike"] - (spot-step)).abs().argsort()[:1]].iloc[0]
        return {"strike":int(row["Strike"]),"ltp":float(row["CE_LTP"]),
                "delta":float(row["CE_Delta"]),"type":"CE",
                "label":f"BUY {int(row['Strike'])} CE",
                "entry":f"₹{row['CE_LTP']*0.98:.1f}–₹{row['CE_LTP']*1.02:.1f}",
                "note":f"ITM CE δ={row['CE_Delta']:.2f} ≥ +0.62 ✓"}

    # ── Helper: find best ITM PE strike with delta ≤ -0.62 ──
    def best_itm_pe():
        itm = df_now[df_now["Strike"] > spot].copy()
        itm = itm[itm["PE_Delta"] <= DELTA_MAX_PE]
        if itm.empty: return None
        row = itm.iloc[(itm["Strike"] - (spot+step)).abs().argsort()[:1]].iloc[0]
        return {"strike":int(row["Strike"]),"ltp":float(row["PE_LTP"]),
                "delta":float(row["PE_Delta"]),"type":"PE",
                "label":f"BUY {int(row['Strike'])} PE",
                "entry":f"₹{row['PE_LTP']*0.98:.1f}–₹{row['PE_LTP']*1.02:.1f}",
                "note":f"ITM PE δ={row['PE_Delta']:.2f} ≤ -0.62 ✓"}

    # ── Helper: check cmp for near-ATM signal ──
    def near_atm_cmp():
        if cmp.empty: return pd.DataFrame()
        return cmp[cmp["Dist"] <= step * 5]

    nat = near_atm_cmp()

    # ════════════════════════════════════════════════
    # SETUP 1 — PE WALL BUILD → BULL → ITM CE
    # Condition: PE OI rising +thr% in 3 min at near-ATM strikes
    # ════════════════════════════════════════════════
    if not nat.empty:
        pe_build = nat[nat["PE_3min_Pct"] >= thr]
        if not pe_build.empty:
            sug = best_itm_ce()
            top = pe_build.nlargest(1,"PE_3min_Pct").iloc[0]
            fired.append({
                "setup":1, "name":"PE WALL BUILD","dir":"BULL",
                "trigger":f"PE OI +{top['PE_3min_Pct']:.1f}% in 3min @ strike {int(top['Strike'])} (near ATM)",
                "suggestion":sug,
                "sound":"planned" if sug else "soft",
            })

    # ════════════════════════════════════════════════
    # SETUP 2 — CE WALL BUILD → BEAR → ITM PE
    # Condition: CE OI rising +thr% in 3 min at near-ATM strikes
    # ════════════════════════════════════════════════
    if not nat.empty:
        ce_build = nat[nat["CE_3min_Pct"] >= thr]
        if not ce_build.empty:
            sug = best_itm_pe()
            top = ce_build.nlargest(1,"CE_3min_Pct").iloc[0]
            fired.append({
                "setup":2,"name":"CE WALL BUILD","dir":"BEAR",
                "trigger":f"CE OI +{top['CE_3min_Pct']:.1f}% in 3min @ strike {int(top['Strike'])} (near ATM)",
                "suggestion":sug,
                "sound":"planned" if sug else "soft",
            })

    # ════════════════════════════════════════════════
    # SETUP 3 — CE SHORT COVER → BULL → ITM CE
    # Condition: CE OI falling -thr% in 3 min (call writers running)
    # ════════════════════════════════════════════════
    if not cmp.empty:
        ce_cover = cmp[cmp["CE_3min_Pct"] <= -thr]
        if not ce_cover.empty:
            sug = best_itm_ce()
            top = ce_cover.nsmallest(1,"CE_3min_Pct").iloc[0]
            fired.append({
                "setup":3,"name":"CE SHORT COVER","dir":"BULL",
                "trigger":f"CE OI {top['CE_3min_Pct']:.1f}% in 3min @ {int(top['Strike'])} — call writers covering",
                "suggestion":sug,
                "sound":"aggression" if phase in ["OPENING_BURST","AGGRESSION"] else "planned",
            })

    # ════════════════════════════════════════════════
    # SETUP 4 — PE SHORT COVER → BEAR → ITM PE
    # Condition: PE OI falling -thr% in 3 min (put longs exiting)
    # ════════════════════════════════════════════════
    if not cmp.empty:
        pe_cover = cmp[cmp["PE_3min_Pct"] <= -thr]
        if not pe_cover.empty:
            sug = best_itm_pe()
            top = pe_cover.nsmallest(1,"PE_3min_Pct").iloc[0]
            fired.append({
                "setup":4,"name":"PE SHORT COVER","dir":"BEAR",
                "trigger":f"PE OI {top['PE_3min_Pct']:.1f}% in 3min @ {int(top['Strike'])} — put longs exiting",
                "suggestion":sug,
                "sound":"aggression" if phase in ["OPENING_BURST","AGGRESSION"] else "planned",
            })

    # ════════════════════════════════════════════════
    # SETUP 5 — BULL IGNITION → PE writing + CE unwinding simultaneously → ITM CE
    # Strongest setup: both confirming bullish at same time
    # ════════════════════════════════════════════════
    if not cmp.empty:
        pe_wr  = cmp[cmp["PE_3min_Pct"] >= thr]
        ce_unw = cmp[cmp["CE_3min_Pct"] <= -thr]
        if not pe_wr.empty and not ce_unw.empty:
            sug = best_itm_ce()
            fired.append({
                "setup":5,"name":"BULL IGNITION 🚀","dir":"BULL",
                "trigger":f"DUAL CONFIRM: PE writing +{pe_wr['PE_3min_Pct'].max():.1f}% AND CE unwinding {ce_unw['CE_3min_Pct'].min():.1f}% simultaneously",
                "suggestion":sug,
                "sound":"aggression",  # always loud for ignition
            })

    # ════════════════════════════════════════════════
    # SETUP 6 — BEAR IGNITION → CE writing + PE unwinding simultaneously → ITM PE
    # ════════════════════════════════════════════════
    if not cmp.empty:
        ce_wr  = cmp[cmp["CE_3min_Pct"] >= thr]
        pe_unw = cmp[cmp["PE_3min_Pct"] <= -thr]
        if not ce_wr.empty and not pe_unw.empty:
            sug = best_itm_pe()
            fired.append({
                "setup":6,"name":"BEAR IGNITION 🔻","dir":"BEAR",
                "trigger":f"DUAL CONFIRM: CE writing +{ce_wr['CE_3min_Pct'].max():.1f}% AND PE unwinding {pe_unw['PE_3min_Pct'].min():.1f}% simultaneously",
                "suggestion":sug,
                "sound":"aggression",
            })

    # ════════════════════════════════════════════════
    # SETUP 7 — OPENING BURST (9:15–9:35 only)
    # Strongest single-direction OI move in first 5-20 min
    # ════════════════════════════════════════════════
    if phase in ["OPENING_BURST","AGGRESSION"] and not cmp.empty:
        max_pe = cmp["PE_3min_Pct"].max()
        max_ce = cmp["CE_3min_Pct"].max()
        min_ce = cmp["CE_3min_Pct"].min()
        min_pe = cmp["PE_3min_Pct"].min()

        if max_pe >= thr * 1.5 and max_pe > max_ce:
            sug = best_itm_ce()
            fired.append({
                "setup":7,"name":"OPENING BURST — BULL","dir":"BULL",
                "trigger":f"Opening 3-min PE surge +{max_pe:.1f}% dominates — BULL bias confirmed",
                "suggestion":sug,
                "sound":"aggression",
            })
        elif max_ce >= thr * 1.5 and max_ce > max_pe:
            sug = best_itm_pe()
            fired.append({
                "setup":7,"name":"OPENING BURST — BEAR","dir":"BEAR",
                "trigger":f"Opening 3-min CE surge +{max_ce:.1f}% dominates — BEAR bias confirmed",
                "suggestion":sug,
                "sound":"aggression",
            })

    # ════════════════════════════════════════════════
    # SETUP 8 — AFTERNOON OI FLIP (1:00–2:30 only)
    # OI changes direction vs morning pattern
    # ════════════════════════════════════════════════
    if phase == "AFTERNOON" and not cmp.empty:
        morning_bull = st.session_state.get("morning_bias",{}).get("bull",0)
        morning_bear = st.session_state.get("morning_bias",{}).get("bear",0)
        cur_pe = cmp["PE_3min_Pct"].max()
        cur_ce = cmp["CE_3min_Pct"].max()

        if morning_bear > morning_bull and cur_pe >= thr:
            # Morning was bearish, afternoon PE writing = reversal BULL
            sug = best_itm_ce()
            fired.append({
                "setup":8,"name":"AFTERNOON REVERSAL — BULL","dir":"BULL",
                "trigger":f"Morning bias was BEARISH but afternoon PE building +{cur_pe:.1f}% → REVERSAL",
                "suggestion":sug,
                "sound":"planned",
            })
        elif morning_bull > morning_bear and cur_ce >= thr:
            # Morning was bullish, afternoon CE writing = reversal BEAR
            sug = best_itm_pe()
            fired.append({
                "setup":8,"name":"AFTERNOON REVERSAL — BEAR","dir":"BEAR",
                "trigger":f"Morning bias was BULLISH but afternoon CE building +{cur_ce:.1f}% → REVERSAL",
                "suggestion":sug,
                "sound":"planned",
            })

    return fired


def overall_direction(df, spot, step, thr):
    """Quick overall direction from current OI for morning bias tracking."""
    if df.empty: return "NEUTRAL", 0, 0
    near = df[df["Dist"] <= step * 8]
    bull = near[near["PE_Chg_Pct"] >= thr]["PE_Chg_Pct"].sum() + \
           abs(near[near["CE_Chg_Pct"] <= -thr]["CE_Chg_Pct"].sum())
    bear = near[near["CE_Chg_Pct"] >= thr]["CE_Chg_Pct"].sum() + \
           abs(near[near["PE_Chg_Pct"] <= -thr]["PE_Chg_Pct"].sum())
    d = "BULLISH" if bull > bear else "BEARISH" if bear > bull else "NEUTRAL"
    return d, bull, bear


def get_expiry(mode):
    t = datetime.now() + timedelta(days={"Current Week":0,"Next Week":7,"Monthly":28}[mode])
    thu = (3-t.weekday())%7
    return (t+timedelta(days=thu)).strftime("%Y-%m-%d")


# ─────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────
for k,v in [
    ("alert_log",[]),
    ("snaps",{}),          # {idx_name: [(datetime, df), ...]}
    ("morning_bias",{"bull":0,"bear":0}),
    ("prev_dir",{}),
    ("refresh_count",0),
    ("overnight",{}),
    ("last_setup_alert",{}),  # debounce: {setup_key: datetime}
]:
    if k not in st.session_state: st.session_state[k]=v


# ─────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='font-family:Orbitron,sans-serif;font-size:0.9rem;color:#00e5a0;letter-spacing:2px;'>OI AGENT v3</div>",unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.55rem;color:#445566;margin-bottom:12px;'>8 SETUPS · 3-MIN SNAP · DELTA FILTER</div>",unsafe_allow_html=True)
    cid   = st.text_input("API Client ID",   placeholder="Your client ID")
    token = st.text_input("Access Token",      type="password", placeholder="Access token")
    st.markdown("---")
    refresh_secs  = st.slider("Refresh (sec)", 30, 300, 60, 10)
    spike_thr     = st.slider("OI Spike %",    5,  30,  15, 5)
    strikes_shown = st.slider("Strikes ±ATM",  5,  15,  8,  1)
    sound_on      = st.toggle("Sound alerts", True)
    auto_refresh  = st.toggle("Auto-refresh",  True)
    st.markdown("---")
    expiry_mode = st.radio("Expiry",["Current Week","Next Week","Monthly"],index=0)
    st.markdown("---")
    st.markdown("""<div style='font-size:0.6rem;color:#445566;line-height:2;'>
    <b style='color:#ff2d55;'>🔔 AGGRESSION</b> = LOUD HAND BELL<br>
    <b style='color:#00aaff;'>🔔 PLANNED</b> = TEMPLE CHIME<br>
    <b style='color:#00e5a0;'>🔔 NORMAL</b> = SOFT PING<br><br>
    <b style='color:#00e5a0;'>CE Delta ≥ +0.62</b> → ITM CE only<br>
    <b style='color:#ff2d55;'>PE Delta ≤ -0.62</b> → ITM PE only<br><br>
    3-min rolling snapshot — always compares vs 3 mins ago
    </div>""",unsafe_allow_html=True)
    if st.button("🔄 Force Refresh",use_container_width=True): st.cache_data.clear(); st.rerun()
    if st.button("🗑 Clear Snapshots",use_container_width=True):
        st.session_state.snaps={}; st.success("Snapshots cleared")


# ─────────────────────────────────────────────────────────────
#  CREDENTIAL CHECK
# ─────────────────────────────────────────────────────────────
if not cid or not token:
    st.markdown("""<div style='text-align:center;padding:60px 20px;'>
    <div style='font-family:Orbitron,sans-serif;font-size:1.5rem;color:#00e5a0;letter-spacing:4px;'>OI MOMENTUM AGENT v3</div>
    <div style='color:#445566;font-size:0.75rem;margin-top:8px;letter-spacing:2px;'>8 SETUPS · DELTA FILTER · 3-MIN ROLLING SNAP</div>
    <br><br>
    <div style='color:#ccdcf0;font-size:0.85rem;'>👈 👈 Enter API credentials in sidebar</div>
    <br><div style='color:#445566;font-size:0.7rem;line-height:2;'>
    Activate API access from your broker portal<br>
    Copy Client ID + Access Token → paste here
    </div></div>""",unsafe_allow_html=True)
    st.stop()


# ─────────────────────────────────────────────────────────────
#  INIT
# ─────────────────────────────────────────────────────────────
api     = DhanAPI(cid, token)
phase   = get_phase()
p_lbl, p_cls = PHASE_LABELS[phase]
now_str = datetime.now().strftime("%d %b %Y  %H:%M:%S")

# ─────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────
st.markdown("""<div style='text-align:center;padding:8px 0 14px;'>
  <div style='font-family:Orbitron,sans-serif;font-size:1.5rem;font-weight:900;letter-spacing:5px;
              background:linear-gradient(90deg,#00e5a0,#00aaff,#ff2d55);
              -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>
    OI MOMENTUM AGENT v3
  </div>
  <div style='color:#445566;font-size:0.62rem;letter-spacing:3px;margin-top:3px;'>
    8 ITM BUY SETUPS · DELTA ≥0.62 FILTER · 3-MIN ROLLING OI · GIFT+FII+DII
  </div>
</div>""",unsafe_allow_html=True)

c1,c2,c3=st.columns([2,4,2])
c1.markdown(f"<div style='color:#445566;font-size:0.72rem;padding-top:6px;'>🕐 {now_str}</div>",unsafe_allow_html=True)
c2.markdown(f"<div class='{p_cls}'>{p_lbl}</div>",unsafe_allow_html=True)
c3.markdown(f"<div style='color:#445566;font-size:0.68rem;text-align:right;padding-top:6px;'>Refresh #{st.session_state.refresh_count}</div>",unsafe_allow_html=True)
st.markdown("---")


# ─────────────────────────────────────────────────────────────
#  PRE-MARKET PANEL — Gift Nifty + FII + DII
# ─────────────────────────────────────────────────────────────
with st.expander("🌅 PRE-MARKET INTELLIGENCE — Gift Nifty + FII + DII",
                 expanded=(phase in ["PRE_MARKET","OPENING_BURST","CLOSED"])):

    gift = fetch_gift()
    fd   = fetch_fii_dii()
    pc   = api.prev_close(DhanAPI.INDICES["NIFTY 50"]["scrip"])
    spot0= api.ltp(DhanAPI.INDICES["NIFTY 50"]["scrip"])
    intent = score_intent(gift, fd, pc, spot0)
    st.session_state.overnight = {"gift":gift,"fd":fd,"intent":intent}

    gc = "#00e5a0" if gift["change"]>=0 else "#ff2d55"
    fc = "#00e5a0" if fd["fii_net"]>=0  else "#ff2d55"
    dc_ = "#00e5a0" if fd["dii_net"]>=0  else "#ff2d55"
    ic = "#00e5a0" if intent["score"]>=65 else "#ff2d55" if intent["score"]<=35 else "#ffaa00"

    cg,cf,cd,ci = st.columns(4)
    with cg:
        st.markdown(f"""<div class='pm-card' style='border-top:2px solid {gc};'>
          <div class='pm-lbl'>Gift Nifty / Spot</div>
          <div class='pm-val' style='color:{gc};'>₹{gift['price']:,.0f}</div>
          <div class='pm-sub'>{gift['change']:+.1f} pts ({gift['pct']:+.2f}%)</div>
          <div class='pm-sub'>{gift['dir']} · {gift['src']}</div>
        </div>""",unsafe_allow_html=True)
    with cf:
        st.markdown(f"""<div class='pm-card' style='border-top:2px solid {fc};'>
          <div class='pm-lbl'>FII (prev day)</div>
          <div class='pm-val' style='color:{fc};'>₹{fd['fii_net']:+,.0f} Cr</div>
          <div class='pm-sub'>Buy: ₹{fd['fii_buy']:,.0f} Cr</div>
          <div class='pm-sub'>Sell: ₹{fd['fii_sell']:,.0f} Cr</div>
        </div>""",unsafe_allow_html=True)
    with cd:
        st.markdown(f"""<div class='pm-card' style='border-top:2px solid {dc_};'>
          <div class='pm-lbl'>DII (prev day)</div>
          <div class='pm-val' style='color:{dc_};'>₹{fd['dii_net']:+,.0f} Cr</div>
          <div class='pm-sub'>Buy: ₹{fd['dii_buy']:,.0f} Cr</div>
          <div class='pm-sub'>Sell: ₹{fd['dii_sell']:,.0f} Cr</div>
        </div>""",unsafe_allow_html=True)
    with ci:
        st.markdown(f"""<div class='pm-card' style='border-top:2px solid {ic};'>
          <div class='pm-lbl'>Intent Score</div>
          <div class='pm-val' style='color:{ic};'>{intent['score']}/100</div>
          <div class='pm-sub'>{intent['dir']}</div>
          <div class='pm-sub'>{intent['mtype']} move</div>
        </div>""",unsafe_allow_html=True)

    icls = "ib-bull" if intent["score"]>=65 else "ib-bear" if intent["score"]<=35 else "ib-neut"
    st.markdown(f"""<div class='intent-box {icls}' style='margin-top:10px;'>
      <div style='font-size:0.72rem;font-weight:700;color:{ic};margin-bottom:6px;'>{intent['dir']} · {intent['mtype']} MOVE</div>
      <div style='font-size:0.65rem;color:#445566;line-height:1.7;'>{intent['reason']}</div>
      <div style='font-size:0.62rem;color:#445566;margin-top:6px;'>
        FII: <b style='color:{fc};'>{fd['fii_dir']}</b> &nbsp;|&nbsp;
        DII: <b style='color:{dc_};'>{fd['dii_dir']}</b> &nbsp;|&nbsp;
        Bull prob: <b style='color:#00e5a0;'>{intent['bull']}%</b> &nbsp;|&nbsp;
        Bear prob: <b style='color:#ff2d55;'>{intent['bear']}%</b>
      </div>
    </div>""",unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  INDEX TABS
# ─────────────────────────────────────────────────────────────
tab_n, tab_bn, tab_log = st.tabs(["📊 NIFTY 50","🏦 BANK NIFTY","🔔 ALERT LOG"])


def render_index(tab, idx_name, idx_info):
    with tab:
        scrip  = idx_info["scrip"]
        step   = idx_info["step"]
        expiry = get_expiry(expiry_mode)

        with st.spinner(f"Fetching {idx_name}..."):
            spot = api.ltp(scrip)
            raw  = api.option_chain(scrip, expiry)

        df = parse_chain(raw, spot, step, expiry)
        if df.empty:
            st.warning(f"No data for {idx_name}. Check credentials / expiry."); return

        # ── 3-MIN ROLLING SNAPSHOT ──
        df_3min, mins_ago = update_3min_snapshot(idx_name, df)

        # ── DIRECTION + MORNING BIAS ──
        direction, bull_raw, bear_raw = overall_direction(df, spot, step, spike_thr)
        total_raw = bull_raw + bear_raw
        bull_sc = round(bull_raw/total_raw*100) if total_raw>0 else 50
        bear_sc = 100-bull_sc

        # Track morning bias for Setup 8
        if phase in ["OPENING_BURST","AGGRESSION","MONITORING"] and \
           datetime.now().hour < 13:
            st.session_state.morning_bias = {"bull":bull_raw,"bear":bear_raw}

        dc = {"BULLISH":"#00e5a0","BEARISH":"#ff2d55","NEUTRAL":"#ffaa00"}.get(direction,"#ffaa00")
        de = {"BULLISH":"🚀","BEARISH":"🔻","NEUTRAL":"↔️"}.get(direction,"↔️")
        pcr= round(df["PE_OI"].sum()/df["CE_OI"].sum(),2) if df["CE_OI"].sum()>0 else 0

        # ── METRICS ──
        m1,m2,m3,m4,m5,m6 = st.columns(6)
        m1.metric("Spot",     f"₹{spot:,.0f}" if spot>0 else "—")
        m2.metric("Direction",f"{de} {direction}")
        m3.metric("Bull",     f"{bull_sc}%")
        m4.metric("Bear",     f"{bear_sc}%")
        m5.metric("PCR",      f"{pcr:.2f}")
        m6.metric("3-min snap",f"{mins_ago}m ago" if mins_ago>0 else "Pending")

        # ── MOMENTUM BAR ──
        bw = bull_sc if direction=="BULLISH" else bear_sc
        st.markdown(f"""<div style='margin:8px 0;'>
          <div style='font-size:0.58rem;color:#445566;letter-spacing:2px;margin-bottom:3px;display:flex;justify-content:space-between;'>
            <span>MOMENTUM DIRECTION — {direction}</span>
            <span style='color:{dc};'>{bw}/100</span>
          </div>
          <div class='mom-track'><div class='mom-fill' style='width:{bw}%;background:{dc};'></div></div>
        </div>""",unsafe_allow_html=True)

        # ── 8 SETUPS ──
        fired = run_8_setups(df, df_3min, spot, step, spike_thr, phase)

        st.markdown("<div class='sec-hdr'>🎯 8 ITM BUY SETUPS — LIVE STATUS</div>",unsafe_allow_html=True)

        if not fired:
            # Show all 8 as waiting
            st.markdown("<div class='setup-grid'>",unsafe_allow_html=True)
            for num, meta in SETUPS.items():
                bd = "setup-bull" if meta["dir"]=="BULL" else "setup-bear" if meta["dir"]=="BEAR" else "setup-bull"
                st.markdown(f"""<div class='setup-card {bd}'>
                  <div class='setup-number'>SETUP {num}</div>
                  <span class='setup-badge badge-wait'>WATCHING</span>
                  <div class='setup-name' style='color:#445566;'>{meta['name']}</div>
                  <div class='setup-trigger'>{meta['desc']}<br><br>
                  <span style='color:#2a3a4a;'>Waiting for OI ≥{spike_thr}% change in 3-min window</span></div>
                </div>""",unsafe_allow_html=True)
            st.markdown("</div>",unsafe_allow_html=True)
        else:
            # Show fired setups prominently
            for f in fired:
                sug    = f.get("suggestion") or {}
                has_sug= bool(sug)
                has_delta = has_sug  # delta already filtered inside best_itm_ce/pe
                d_val  = sug.get("delta",0) if has_sug else 0
                stype  = sug.get("type","")
                dcolor = "#00e5a0" if stype=="CE" else "#ff2d55" if stype=="PE" else "#ffaa00"
                box_cls= "setup-bull" if f["dir"]=="BULL" else "setup-bear"
                d_label= f"δ = {d_val:+.2f} {'≥ +0.62 ✓' if stype=='CE' else '≤ -0.62 ✓'}" if has_delta else "No ITM strike meets delta threshold"
                d_cls  = ("delta-ok-bull" if stype=="CE" else "delta-ok-bear") if has_delta else "delta-fail"

                st.markdown(f"""<div class='setup-card {box_cls}'>
                  <div class='setup-number'>SETUP {f['setup']} — {f['name']}</div>
                  <span class='setup-badge badge-fire'>🔥 FIRED</span>
                  <div style='font-size:0.68rem;color:#445566;margin:6px 0;'>{f['trigger']}</div>
                  {'<div class="setup-strike" style="color:'+dcolor+';">► '+sug.get('label','')+'&nbsp;|&nbsp; LTP ₹'+str(round(sug.get('ltp',0),1))+'</div>' if has_sug else '<div style="color:#445566;font-size:0.75rem;">⚠️ No qualifying ITM strike — delta threshold not met</div>'}
                  <span class='setup-delta {d_cls}'>{d_label}</span>
                  {'<div class="setup-trigger">Entry: '+sug.get("entry","")+'&nbsp;·&nbsp;'+sug.get("note","")+'</div>' if has_sug else ''}
                </div>""",unsafe_allow_html=True)

                # Play sound
                if is_alert(phase) and sound_on:
                    snd = f.get("sound","soft")
                    # Debounce: same setup fires max once per 5 min
                    sk = f"{idx_name}_setup{f['setup']}"
                    last = st.session_state.last_setup_alert.get(sk)
                    if not last or (datetime.now()-last).total_seconds()>300:
                        st.markdown(f"<script>playSound('{snd}');</script>",unsafe_allow_html=True)
                        st.session_state.last_setup_alert[sk] = datetime.now()

            # Also show remaining setups as watching
            fired_nums = {f["setup"] for f in fired}
            remaining  = {k:v for k,v in SETUPS.items() if k not in fired_nums}
            if remaining:
                with st.expander(f"👁 {len(remaining)} setups watching (not yet triggered)"):
                    for num,meta in remaining.items():
                        st.markdown(f"<div style='font-size:0.72rem;color:#445566;padding:4px 0;border-bottom:1px solid #131f2e;'><b>SETUP {num} — {meta['name']}</b> · {meta['desc']}</div>",unsafe_allow_html=True)

        # ── 3-MIN OI COMPARISON PANEL ──
        with st.expander(f"⏱ 3-MIN OI DELTA — vs {mins_ago}min ago ({idx_name})", expanded=False):
            if not df_3min.empty:
                cmp_df = compare_3min(df, df_3min, spike_thr)
                if not cmp_df.empty:
                    near = cmp_df[cmp_df["Dist"]<=step*8].sort_values("Dist")
                    st.markdown("""<div class='snap-panel'>
                    <div class='snap-title'>
                      <span>STRIKE</span><span>CE 3-min Δ%</span><span>PE 3-min Δ%</span><span>ATM?</span>
                    </div>""",unsafe_allow_html=True)
                    for _,row in near.iterrows():
                        cp = row["CE_3min_Pct"]; pp = row["PE_3min_Pct"]
                        cc = "#ff2d55" if cp>=spike_thr else "#00e5a0" if cp<=-spike_thr else "#445566"
                        pc = "#00e5a0" if pp>=spike_thr else "#ff2d55" if pp<=-spike_thr else "#445566"
                        am = "← ATM" if row["ATM"] else ""
                        st.markdown(f"""<div class='snap-row'>
                          <span style='color:{"#ffaa00" if row["ATM"] else "#ccdcf0"};'>₹{int(row["Strike"]):,} {am}</span>
                          <span style='color:{cc};font-weight:{"700" if abs(cp)>=spike_thr else "400"};'>{cp:+.1f}%</span>
                          <span style='color:{pc};font-weight:{"700" if abs(pp)>=spike_thr else "400"};'>{pp:+.1f}%</span>
                          <span style='color:#445566;font-size:0.65rem;'>CE δ={row["CE_Delta"]:.2f} | PE δ={row["PE_Delta"]:.2f}</span>
                        </div>""",unsafe_allow_html=True)
                    st.markdown("</div>",unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:#445566;font-size:0.72rem;'>3-min snapshot building — needs 2 cycles (6 min). Waiting...</div>",unsafe_allow_html=True)

        # ── OI TABLE WITH DELTA COLUMN ──
        st.markdown("<div class='sec-hdr'>OPTION CHAIN + DELTA</div>",unsafe_allow_html=True)
        atm_i=(df["Strike"]-spot).abs().idxmin()
        lo=max(0,atm_i-strikes_shown); hi=min(len(df)-1,atm_i+strikes_shown)
        df_v=df.iloc[lo:hi+1]

        html="""<div class='oi-wrap'><div class='oi-hdr'>CE LEFT · STRIKE CENTER · PE RIGHT · 🟢 δ≥+0.62 ITM CE | 🔴 δ≤-0.62 ITM PE</div>
        <table><thead><tr>
          <th>CE OI</th><th>CE Chg%</th><th>CE LTP</th><th>CE δ</th>
          <th style='background:#0c1420;color:#ffaa00;'>STRIKE</th>
          <th>PE δ</th><th>PE LTP</th><th>PE OI</th><th>PE Chg%</th>
        </tr></thead><tbody>"""

        for _,row in df_v.iterrows():
            atm = row["ATM"]; rc = "atm-r" if atm else ""
            am  = " ← ATM" if atm else ""
            cp  = row["CE_Chg_Pct"]; pp = row["PE_Chg_Pct"]
            ced = row["CE_Delta"];   ped = row["PE_Delta"]
            cc  = "ce-sp" if cp>=spike_thr else ("unw" if cp<=-spike_thr else "")
            pc_ = "pe-sp" if pp>=spike_thr else ("unw" if pp<=-spike_thr else "")
            sc  = "#00e5a0" if row["Strike"]<spot else ("#ccdcf0" if row["Strike"]>spot else "#ffaa00")
            # Delta highlight
            ced_col = "#00e5a0" if ced>=DELTA_MIN_CE else "#445566"
            ped_col = "#ff2d55" if ped<=DELTA_MAX_PE else "#445566"
            ced_bold = "font-weight:700;" if ced>=DELTA_MIN_CE else ""
            ped_bold = "font-weight:700;" if ped<=DELTA_MAX_PE else ""

            html+=f"""<tr class='{rc}'>
              <td class='{cc}'>{int(row['CE_OI']):,}</td>
              <td class='{cc}'>{cp:+.1f}%</td>
              <td>{row['CE_LTP']:.1f}</td>
              <td style='color:{ced_col};{ced_bold}'>{ced:+.2f}</td>
              <td style='color:{sc};font-weight:600;'>{int(row['Strike']):,}{am}</td>
              <td style='color:{ped_col};{ped_bold}'>{ped:.2f}</td>
              <td>{row['PE_LTP']:.1f}</td>
              <td class='{pc_}'>{int(row['PE_OI']):,}</td>
              <td class='{pc_}'>{pp:+.1f}%</td>
            </tr>"""

        html+="""</tbody></table>
        <div class='leg-bar'>
          <div class='leg'><div class='ld' style='background:#ff2d55;'></div>CE Writing</div>
          <div class='leg'><div class='ld' style='background:#00e5a0;'></div>PE Writing</div>
          <div class='leg'><div class='ld' style='background:#ffaa00;'></div>Unwinding/ATM</div>
          <div class='leg'><div class='ld' style='background:#00e5a0;opacity:0.6;'></div>CE δ≥+0.62 (ITM buy)</div>
          <div class='leg'><div class='ld' style='background:#ff2d55;opacity:0.6;'></div>PE δ≤-0.62 (ITM buy)</div>
        </div></div>"""
        st.markdown(html,unsafe_allow_html=True)

        # ── LOG ──
        for f in fired:
            if is_alert(phase) and f.get("suggestion"):
                sk = f"{idx_name}_s{f['setup']}_dir{f['dir']}"
                if st.session_state.prev_dir.get(sk) != direction:
                    sug=f["suggestion"]
                    st.session_state.alert_log.insert(0,{
                        "time":datetime.now().strftime("%H:%M:%S"),
                        "index":idx_name,"setup":f"Setup {f['setup']} — {f['name']}",
                        "dir":f["dir"],"delta":sug.get("delta",0),
                        "strike":sug.get("label",""),"ltp":sug.get("ltp",0),
                        "sound":f.get("sound","soft"),"phase":phase})
                    st.session_state.prev_dir[sk]=direction
                    st.session_state.alert_log=st.session_state.alert_log[:50]


render_index(tab_n,  "NIFTY 50",   DhanAPI.INDICES["NIFTY 50"])
render_index(tab_bn, "BANK NIFTY", DhanAPI.INDICES["BANK NIFTY"])


# ─────────────────────────────────────────────────────────────
#  ALERT LOG
# ─────────────────────────────────────────────────────────────
with tab_log:
    st.markdown("### 🔔 Alert Log — All fired setups")
    if not st.session_state.alert_log:
        st.info("No alerts yet. Setups fire during 9:15–9:35, 1:00–2:30, 3:00–3:30.")
    else:
        for e in st.session_state.alert_log:
            col="#00e5a0" if e["dir"]=="BULL" else "#ff2d55"
            snd_icon={"aggression":"🔔🔔🔔","planned":"🔔🔔","soft":"🔔"}.get(e.get("sound","soft"),"🔔")
            st.markdown(f"""<div style='background:#0c1420;border:1px solid #131f2e;border-left:3px solid {col};
              border-radius:4px;padding:10px 16px;margin:5px 0;font-size:0.72rem;'>
              {snd_icon} <span style='color:#445566;'>{e['time']}</span> &nbsp;
              <b style='color:{col};'>{e['dir']}</b> &nbsp;|&nbsp;
              <b style='color:#ffaa00;'>{e['setup']}</b> &nbsp;|&nbsp;
              <b>{e['index']}</b> &nbsp;|&nbsp;
              {e['strike']} @ ₹{e['ltp']:,.1f} &nbsp;|&nbsp;
              δ = <b style='color:{col};'>{e['delta']:+.2f}</b> &nbsp;|&nbsp;
              <span style='color:#445566;'>{e['phase']}</span>
            </div>""",unsafe_allow_html=True)
    if st.button("🗑 Clear Log"): st.session_state.alert_log=[]; st.rerun()


# ─────────────────────────────────────────────────────────────
#  AUTO REFRESH
# ─────────────────────────────────────────────────────────────
st.session_state.refresh_count+=1
msg = f"Next refresh in {refresh_secs}s · 3-min snapshots auto-save" if auto_refresh and phase!="CLOSED" else "💤 Market closed — resumes 9:00 AM"
st.markdown(f"<div style='text-align:center;color:#445566;font-size:0.62rem;margin-top:14px;padding-top:10px;border-top:1px solid #131f2e;'>{msg}</div>",unsafe_allow_html=True)

if auto_refresh and phase!="CLOSED":
    time_module.sleep(refresh_secs)
    st.rerun()
