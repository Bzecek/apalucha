import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# ─────────────────────────────────────────────
# KONFIGURACE
# ─────────────────────────────────────────────
BARVA      = "#2e7d32"   # lesní zelená
BARVA_SVE  = "#3B6D11"   # tmavší zelená pro text
BARVA_KARTA = "#EAF3DE"  # světlá zelená pozadí avataru

# Předpřipravený seznam otců (rychlé přidání jedním klikem)
OTCOVE_SEZNAM = ["Bzek", "Pošták", "Boss", "Tonda", "Jirka"]

st.set_page_config(page_title="Apalucha – účtování", page_icon="🏕️", layout="centered")

st.markdown(f"""
    <style>
    /* hezčí tlačítka */
    div.stButton > button {{
        border-radius: 12px;
        font-weight: 500;
        transition: all 0.15s ease;
    }}
    div.stButton > button:hover {{
        border-color: {BARVA};
        color: {BARVA};
    }}
    /* primární tlačítka zelená */
    div.stButton > button[kind="primary"] {{
        background-color: {BARVA};
        border-color: {BARVA};
    }}
    [data-testid="stMetricValue"] {{ color: {BARVA}; }}
    /* karta účastníka / výdaje */
    .karta {{
        background: rgba(46,125,50,0.06);
        border: 1px solid rgba(46,125,50,0.15);
        border-radius: 14px;
        padding: 10px 14px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
    }}
    .avatar {{
        width: 38px; height: 38px; border-radius: 50%;
        background: {BARVA_KARTA}; color: {BARVA_SVE};
        display: flex; align-items: center; justify-content: center;
        font-weight: 600; font-size: 14px; margin-right: 12px;
        flex-shrink: 0;
    }}
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PŘIPOJENÍ NA GOOGLE SHEETS
# Každý ročník = vlastní list (worksheet).
# Sloupce: Typ, Kdo, Co, Castka, KrkDeti, ZaKoho, Datum
#   Typ:    "ucastnik" | "baget" | "vydaj"
#   ZaKoho: "BAGET" | "VSICHNI" | "Jméno1;Jméno2"
# ─────────────────────────────────────────────
conn = st.connection("gsheets", type=GSheetsConnection)
SLOUPCE = ["Typ", "Kdo", "Co", "Castka", "KrkDeti", "ZaKoho", "Datum"]


@st.cache_data(ttl=30)
def nacti(rocnik):
    try:
        df = conn.read(worksheet=rocnik, ttl=30)
        if df is None or df.empty:
            return pd.DataFrame(columns=SLOUPCE)
        df = df.dropna(how="all")
        for s in SLOUPCE:
            if s not in df.columns:
                df[s] = None
        return df[SLOUPCE]
    except Exception:
        return pd.DataFrame(columns=SLOUPCE)


def uloz(rocnik, df):
    conn.update(worksheet=rocnik, data=df[SLOUPCE])
    st.cache_data.clear()


def pridej_radek(rocnik, radek):
    df = nacti(rocnik)
    novy = pd.concat([df, pd.DataFrame([radek])], ignore_index=True)
    uloz(rocnik, novy)


def smaz_radek(rocnik, idx):
    df = nacti(rocnik).reset_index(drop=True)
    if idx in df.index:
        df = df.drop(index=idx).reset_index(drop=True)
        uloz(rocnik, df)


def iniciala(jmeno):
    return (jmeno[:2]).upper() if jmeno else "??"


# ─────────────────────────────────────────────
# HLAVIČKA + VÝBĚR ROČNÍKU
# ─────────────────────────────────────────────
st.markdown(
    f'<div style="display:flex;align-items:center;margin-bottom:6px;">'
    f'<span style="font-size:42px;margin-right:12px;">🏕️</span>'
    f'<h1 style="margin:0;color:{BARVA_SVE};">Apalucha</h1></div>',
    unsafe_allow_html=True
)
st.caption("Otcové a děti pod stanem. Kdo platil za koho — appka spočítá vyrovnání.")

rok_ted = datetime.now().year
roky = [str(r) for r in range(rok_ted + 1, 2019, -1)]
c_rok, c_novy = st.columns([2, 1])
rocnik = c_rok.selectbox("Ročník Apaluchy", roky, index=roky.index(str(rok_ted)) if str(rok_ted) in roky else 0)
vlastni = c_novy.text_input("…nebo vlastní list", placeholder="2026_jaro")
if vlastni.strip():
    rocnik = vlastni.strip()

st.divider()

df = nacti(rocnik)
df_uc    = df[df["Typ"] == "ucastnik"].reset_index()
df_baget = df[df["Typ"] == "baget"].reset_index()
df_vyd   = df[df["Typ"] == "vydaj"].reset_index()

otcove = list(df_uc["Kdo"].dropna().astype(str))


def krky(jmeno):
    radek = df_uc[df_uc["Kdo"] == jmeno]
    if radek.empty:
        return 1
    try:
        return 1 + int(float(radek.iloc[0]["KrkDeti"] or 0))
    except Exception:
        return 1


celkem_krku = sum(krky(o) for o in otcove)

# ─────────────────────────────────────────────
# 1) OTCOVÉ A DĚTI — rychlé přidání
# ─────────────────────────────────────────────
st.header("1. Otcové a děti")
st.caption("Klikni na jméno a vyber, kolik má s sebou dětí.")

# stav: na koho jsme klikli a čekáme na zadání počtu dětí
if "ceka_na_deti" not in st.session_state:
    st.session_state.ceka_na_deti = None

# tlačítka rychlého přidání — 2 ve sloupci
nepridani = [o for o in OTCOVE_SEZNAM if o not in otcove]
if nepridani:
    cols = st.columns(2)
    for i, jm in enumerate(nepridani):
        if cols[i % 2].button(f"➕ {jm}", key=f"add_{jm}", use_container_width=True):
            st.session_state.ceka_na_deti = jm
            st.rerun()
else:
    st.success("Všichni z party jsou přidaní 🎉")

# dialog pro zadání počtu dětí
if st.session_state.ceka_na_deti:
    jm = st.session_state.ceka_na_deti
    with st.container(border=True):
        st.write(f"**Kolik dětí přijede s {jm}?**")
        pocet = st.number_input("Počet dětí", min_value=0, max_value=10, value=0, step=1, key="vyber_deti")
        cok, czr = st.columns(2)
        if cok.button("✅ Přidat", type="primary", use_container_width=True):
            pridej_radek(rocnik, {
                "Typ": "ucastnik", "Kdo": jm, "Co": "", "Castka": 0,
                "KrkDeti": int(pocet), "ZaKoho": "",
                "Datum": datetime.now().strftime("%d.%m.%Y %H:%M"),
            })
            st.session_state.ceka_na_deti = None
            st.rerun()
        if czr.button("Zrušit", use_container_width=True):
            st.session_state.ceka_na_deti = None
            st.rerun()

# seznam přidaných jako karty
if otcove:
    st.write("")
    for _, r in df_uc.iterrows():
        deti = int(float(r["KrkDeti"] or 0))
        jidla = 1 + deti
        deti_txt = "bez dětí" if deti == 0 else (f"{deti} dítě" if deti == 1 else f"{deti} děti" if deti < 5 else f"{deti} dětí")
        c1, c2 = st.columns([5, 1])
        c1.markdown(
            f'<div class="karta">'
            f'<div class="avatar">{iniciala(r["Kdo"])}</div>'
            f'<div><div style="font-weight:600;font-size:15px;">{r["Kdo"]}</div>'
            f'<div style="font-size:12px;color:#888;">{deti_txt} · {jidla} jídel</div></div>'
            f'</div>',
            unsafe_allow_html=True
        )
        if c2.button("🗑️", key=f"del_uc_{r['index']}", use_container_width=True):
            smaz_radek(rocnik, r["index"])
            st.rerun()
else:
    st.info("Zatím nikdo. Přidej prvního otce.")

# ─────────────────────────────────────────────
# 2) SPOLEČNÝ BAGET
# ─────────────────────────────────────────────
st.header("2. Společný baget na suroviny")

if otcove:
    with st.form("f_baget", clear_on_submit=False):
        st.caption("Kolik kdo vložil do společného bagetu. Tip: nech vyplnit částkou na jedno jídlo.")
        na_krk = st.number_input("Rychlé vyplnění: částka na jedno jídlo (Kč)", min_value=0, value=0, step=50)
        vlozky = {}
        for o in otcove:
            existuje = df_baget[df_baget["Kdo"] == o]
            if not existuje.empty:
                vychozi = int(float(existuje.iloc[0]["Castka"] or 0))
            else:
                vychozi = na_krk * krky(o) if na_krk else 0
            vlozky[o] = st.number_input(f"{o} ({krky(o)} jídel)", min_value=0, value=int(vychozi), step=50, key=f"bg_{o}")
        if st.form_submit_button("💾 Uložit baget", type="primary", use_container_width=True):
            df_now = nacti(rocnik)
            df_now = df_now[df_now["Typ"] != "baget"]
            nove = [{
                "Typ": "baget", "Kdo": o, "Co": "", "Castka": int(vlozky[o]),
                "KrkDeti": 0, "ZaKoho": "", "Datum": datetime.now().strftime("%d.%m.%Y %H:%M"),
            } for o in otcove]
            uloz(rocnik, pd.concat([df_now, pd.DataFrame(nove)], ignore_index=True))
            st.rerun()

    baget_celkem = sum(int(float(c or 0)) for c in df_baget["Castka"]) if not df_baget.empty else 0
    st.metric("Baget celkem", f"{baget_celkem} Kč")
else:
    st.info("Nejdřív přidej účastníky.")

# ─────────────────────────────────────────────
# 3) VÝDAJE
# ─────────────────────────────────────────────
st.header("3. Výdaje – kdo platil za koho")

if otcove:
    with st.form("f_vyd", clear_on_submit=True):
        co = st.text_input("Co to bylo", placeholder="nákup masa, půjčovné, pivo…")
        c1, c2 = st.columns(2)
        kdo = c1.selectbox("Kdo platil", otcove)
        castka = c2.number_input("Částka (Kč)", min_value=0, value=0, step=50)
        typ_del = st.radio("Za koho se to dělí?",
                           ["Z bagetu (suroviny)", "Všichni rovným dílem", "Jen vybraní"], index=0)
        vybrani = st.multiselect("Jen vybraní – koho se týká", otcove)
        if st.form_submit_button("➕ Přidat výdaj", type="primary", use_container_width=True):
            if castka <= 0:
                st.warning("Zadej částku.")
            elif typ_del == "Jen vybraní" and not vybrani:
                st.warning("Vyber aspoň jednoho člověka.")
            else:
                if typ_del == "Z bagetu (suroviny)":
                    zk = "BAGET"
                elif typ_del == "Všichni rovným dílem":
                    zk = "VSICHNI"
                else:
                    zk = ";".join(vybrani)
                pridej_radek(rocnik, {
                    "Typ": "vydaj", "Kdo": kdo, "Co": co.strip() or "—", "Castka": int(castka),
                    "KrkDeti": 0, "ZaKoho": zk, "Datum": datetime.now().strftime("%d.%m.%Y %H:%M"),
                })
                st.rerun()

    if not df_vyd.empty:
        for _, r in df_vyd.iterrows():
            zk = str(r["ZaKoho"])
            popis = "z bagetu" if zk == "BAGET" else "všichni" if zk == "VSICHNI" else zk.replace(";", ", ")
            castka_v = int(float(r["Castka"] or 0))
            c1, c2 = st.columns([5, 1])
            c1.markdown(
                f'<div class="karta">'
                f'<div class="avatar">{iniciala(r["Kdo"])}</div>'
                f'<div style="flex:1;"><div style="font-weight:600;font-size:15px;">{r["Co"]} · {castka_v} Kč</div>'
                f'<div style="font-size:12px;color:#888;">platil {r["Kdo"]} · za: {popis}</div></div>'
                f'</div>',
                unsafe_allow_html=True
            )
            if c2.button("🗑️", key=f"del_vyd_{r['index']}", use_container_width=True):
                smaz_radek(rocnik, r["index"])
                st.rerun()
    else:
        st.info("Zatím žádné výdaje.")
else:
    st.info("Nejdřív přidej účastníky.")

# ─────────────────────────────────────────────
# 4) VYROVNÁNÍ
# ─────────────────────────────────────────────
st.header("4. Vyrovnání")

if otcove:
    saldo = {o: 0.0 for o in otcove}

    for _, b in df_baget.iterrows():
        if b["Kdo"] in saldo:
            saldo[b["Kdo"]] += float(b["Castka"] or 0)

    baget_vydaje = sum(float(r["Castka"] or 0) for _, r in df_vyd.iterrows() if str(r["ZaKoho"]) == "BAGET")
    for _, r in df_vyd.iterrows():
        if str(r["ZaKoho"]) == "BAGET" and r["Kdo"] in saldo:
            saldo[r["Kdo"]] += float(r["Castka"] or 0)

    if celkem_krku > 0:
        baget_celkem_val = sum(float(b["Castka"] or 0) for _, b in df_baget.iterrows())
        k_rozdeleni = baget_vydaje if baget_vydaje > 0 else baget_celkem_val
        na_krk = k_rozdeleni / celkem_krku
        for o in otcove:
            saldo[o] -= na_krk * krky(o)

    for _, r in df_vyd.iterrows():
        zk = str(r["ZaKoho"])
        if zk == "BAGET":
            continue
        c = float(r["Castka"] or 0)
        if r["Kdo"] in saldo:
            saldo[r["Kdo"]] += c
        if zk == "VSICHNI":
            podil = c / len(otcove)
            for o in otcove:
                saldo[o] -= podil
        else:
            lidi = [x for x in zk.split(";") if x in saldo]
            if lidi:
                podil = c / len(lidi)
                for o in lidi:
                    saldo[o] -= podil

    tbl = pd.DataFrame([{"Otec": o, "Saldo (Kč)": round(saldo[o])} for o in otcove])
    st.dataframe(tbl, use_container_width=True, hide_index=True)
    st.caption("Saldo: kladné = má dostat zpět, záporné = má doplatit.")

    d = [[o, -s] for o, s in saldo.items() if s < -0.5]
    v = [[o, s] for o, s in saldo.items() if s > 0.5]
    d.sort(key=lambda x: -x[1])
    v.sort(key=lambda x: -x[1])
    platby = []
    i = j = 0
    while i < len(d) and j < len(v):
        c = min(d[i][1], v[j][1])
        platby.append((d[i][0], v[j][0], round(c)))
        d[i][1] -= c
        v[j][1] -= c
        if d[i][1] < 0.5:
            i += 1
        if v[j][1] < 0.5:
            j += 1

    st.subheader("Kdo komu pošle")
    if platby:
        radky_txt = []
        for od, komu, c in platby:
            st.success(f"**{od}** → **{komu}**: {int(c)} Kč")
            radky_txt.append(f"{od} → {komu}: {int(c)} Kč")
        souhrn = f"🏕️ Apalucha {rocnik} – vyrovnání:\n" + "\n".join(radky_txt)
        st.text_area("Pro zkopírování do skupiny", souhrn, height=120)
    else:
        st.success("Všichni jsou vyrovnaní 🎉")
else:
    st.info("Přidej účastníky, baget a výdaje.")

st.divider()
st.caption(f"Data ročníku „{rocnik}\" se ukládají do Google Sheets a jsou sdílená pro všechny s odkazem.")
