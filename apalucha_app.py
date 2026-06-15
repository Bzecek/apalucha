import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# ─────────────────────────────────────────────
# KONFIGURACE
# ─────────────────────────────────────────────
BARVA       = "#2e7d32"
BARVA_SVE   = "#3B6D11"
BARVA_KARTA = "#EAF3DE"

OTCOVE_SEZNAM = ["Bzek", "Pošták", "Boss", "Tonda", "Jirka", "Kolouch"]

st.set_page_config(page_title="Apalucha – účtování", page_icon="🏕️", layout="centered")

st.markdown(f"""
    <style>
    div.stButton > button {{
        border-radius: 12px;
        font-weight: 500;
        transition: all 0.15s ease;
    }}
    div.stButton > button:hover {{
        border-color: {BARVA};
        color: {BARVA};
    }}
    div.stButton > button[kind="primary"] {{
        background-color: {BARVA};
        border-color: {BARVA};
    }}
    [data-testid="stMetricValue"] {{ color: {BARVA}; }}
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
# Sloupce: Typ, Kdo, Co, Castka, KrkDeti, ZaKoho, Datum
#   Typ:    "ucastnik" | "bank" | "vydaj"
#   ZaKoho u výdaje:
#       "BANK"              → hradí se ze společného banku
#       "VSICHNI"           → na všechny otce + jejich děti (jídla)
#       "Pošták:3;Tonda:1"  → jen vybraní; číslo = počet jídel
# ─────────────────────────────────────────────
conn = st.connection("gsheets", type=GSheetsConnection)
SLOUPCE = ["Typ", "Kdo", "Co", "Castka", "KrkDeti", "ZaKoho", "Datum"]


def zajisti_list(rocnik):
    try:
        spreadsheet = conn._instance.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
        existujici = [w.title for w in spreadsheet.worksheets()]
        if rocnik not in existujici:
            ws = spreadsheet.add_worksheet(title=rocnik, rows=200, cols=len(SLOUPCE))
            ws.update([SLOUPCE])
            return True
    except Exception:
        pass
    return False


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
    try:
        conn.update(worksheet=rocnik, data=df[SLOUPCE])
    except Exception:
        zajisti_list(rocnik)
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


def deti_text(deti):
    if deti == 0:
        return "bez dětí"
    if deti == 1:
        return "1 dítě"
    if deti < 5:
        return f"{deti} děti"
    return f"{deti} dětí"


if "maze" not in st.session_state:
    st.session_state.maze = None


def tlacitko_smazat(rocnik, idx, klic):
    """Mazací tlačítko s potvrzením (dvojí klik). Vrací nic, sám řeší rerun."""
    if st.session_state.maze == klic:
        st.caption("Opravdu smazat?")
        ca, cn = st.columns(2)
        if ca.button("✅ Ano", key=f"ano_{klic}", use_container_width=True):
            smaz_radek(rocnik, idx)
            st.session_state.maze = None
            st.rerun()
        if cn.button("❌ Ne", key=f"ne_{klic}", use_container_width=True):
            st.session_state.maze = None
            st.rerun()
    else:
        if st.button("🗑️", key=f"del_{klic}", use_container_width=True):
            st.session_state.maze = klic
            st.rerun()


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

zajisti_list(rocnik)

df = nacti(rocnik)
df_uc   = df[df["Typ"] == "ucastnik"].reset_index()
df_bank = df[df["Typ"] == "bank"].reset_index()
df_vyd  = df[df["Typ"] == "vydaj"].reset_index()

otcove = list(df_uc["Kdo"].dropna().astype(str))


def jidla_otce(jmeno):
    radek = df_uc[df_uc["Kdo"] == jmeno]
    if radek.empty:
        return 1
    try:
        return 1 + int(float(radek.iloc[0]["KrkDeti"] or 0))
    except Exception:
        return 1


def deti_otce(jmeno):
    radek = df_uc[df_uc["Kdo"] == jmeno]
    if radek.empty:
        return 0
    try:
        return int(float(radek.iloc[0]["KrkDeti"] or 0))
    except Exception:
        return 0


celkem_jidel = sum(jidla_otce(o) for o in otcove)

if "ceka_na_deti" not in st.session_state:
    st.session_state.ceka_na_deti = None

# ─────────────────────────────────────────────
# 1) OTCOVÉ A DĚTI  (sbalitelná sekce)
# ─────────────────────────────────────────────
with st.expander(f"⚙️ 1. Otcové a děti ({len(otcove)})", expanded=(len(otcove) == 0)):
    st.caption("Klikni na jméno a vyber, kolik má s sebou dětí.")

    nepridani = [o for o in OTCOVE_SEZNAM if o not in otcove]
    if nepridani:
        cols = st.columns(2)
        for i, jm in enumerate(nepridani):
            if cols[i % 2].button(f"➕ {jm}", key=f"add_{jm}", use_container_width=True):
                st.session_state.ceka_na_deti = jm
                st.rerun()
    else:
        st.success("Všichni z party jsou přidaní 🎉")

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

    if otcove:
        st.write("")
        for _, r in df_uc.iterrows():
            deti = deti_otce(r["Kdo"])
            c1, c2 = st.columns([5, 1])
            c1.markdown(
                f'<div class="karta">'
                f'<div class="avatar">{iniciala(r["Kdo"])}</div>'
                f'<div><div style="font-weight:600;font-size:15px;">{r["Kdo"]}</div>'
                f'<div style="font-size:12px;color:#888;">{deti_text(deti)} · {1 + deti} jídel</div></div>'
                f'</div>',
                unsafe_allow_html=True
            )
            with c2:
                tlacitko_smazat(rocnik, r["index"], f"uc_{r['index']}")
    else:
        st.info("Zatím nikdo. Přidej prvního otce.")

# ─────────────────────────────────────────────
# 2) SPOLEČNÝ BANK  (sbalitelná sekce)
# ─────────────────────────────────────────────
bank_vlozeno  = sum(int(float(c or 0)) for c in df_bank["Castka"]) if not df_bank.empty else 0
bank_utraceno = sum(int(float(r["Castka"] or 0)) for _, r in df_vyd.iterrows() if str(r["ZaKoho"]) == "BANK")
bank_zustatek = bank_vlozeno - bank_utraceno

with st.expander(f"🏦 2. Společný bank (zůstatek {bank_zustatek} Kč)", expanded=False):
    if otcove:
        with st.form("f_bank", clear_on_submit=False):
            st.caption("Kolik každý otec vložil na začátku do společného banku (např. 3 000 Kč).")
            vlozky = {}
            for o in otcove:
                existuje = df_bank[df_bank["Kdo"] == o]
                vychozi = int(float(existuje.iloc[0]["Castka"] or 0)) if not existuje.empty else None
                vlozky[o] = st.number_input(
                    f"{o} vložil (Kč)", min_value=0, value=vychozi, step=100,
                    placeholder="0", key=f"bank_{o}"
                )
            if st.form_submit_button("💾 Uložit vklady", type="primary", use_container_width=True):
                df_now = nacti(rocnik)
                df_now = df_now[df_now["Typ"] != "bank"]
                nove = [{
                    "Typ": "bank", "Kdo": o, "Co": "", "Castka": int(vlozky[o] or 0),
                    "KrkDeti": 0, "ZaKoho": "", "Datum": datetime.now().strftime("%d.%m.%Y %H:%M"),
                } for o in otcove]
                uloz(rocnik, pd.concat([df_now, pd.DataFrame(nove)], ignore_index=True))
                st.rerun()

        m1, m2, m3 = st.columns(3)
        m1.metric("Vloženo", f"{bank_vlozeno} Kč")
        m2.metric("Utraceno z banku", f"{bank_utraceno} Kč")
        m3.metric("Zůstatek", f"{bank_zustatek} Kč")
        if bank_zustatek < 0:
            st.warning("Bank je v mínusu — utratilo se víc, než kolik je v něm vloženo.")
        st.caption("Zůstatek zůstává v banku na příště, nerozpočítává se mezi otce.")
    else:
        st.info("Nejdřív přidej účastníky.")

# ─────────────────────────────────────────────
# 3) VÝDAJE
# ─────────────────────────────────────────────
st.header("3. Výdaje – kdo platil za koho")

if otcove:
    st.caption("Zadej, kdo platil, kolik, a koho se výdaj týká. Dělí se na jídla (otec + jeho děti).")

    co = st.text_input("Co to bylo", placeholder="společný oběd, půjčovné, pivo…", key="vyd_co")
    c1, c2 = st.columns(2)
    kdo = c1.selectbox("Kdo platil", otcove, key="vyd_kdo")
    castka = c2.number_input("Kolik zaplatil (Kč)", min_value=0, value=None, step=50,
                             placeholder="Zadej částku", key="vyd_castka")

    typ_del = st.radio(
        "Jak se výdaj hradí / dělí?",
        ["Ze společného banku", "Všichni (otcové + děti)", "Jen vybraní"],
        index=0, key="vyd_typ"
    )

    vybrani = []
    rucni_jidla = {}
    if typ_del == "Jen vybraní":
        vybrani = st.multiselect("Koho se výdaj týká", otcove, key="vyd_vyb")
        if vybrani:
            uprav = st.checkbox("Ručně upravit počet jídel u vybraných", key="vyd_uprav")
            if uprav:
                st.caption("Kolik jídel (otec + děti) připadá na každého u tohoto výdaje:")
                for o in vybrani:
                    rucni_jidla[o] = st.number_input(
                        f"{o} — počet jídel",
                        min_value=1, max_value=20, value=jidla_otce(o), step=1, key=f"vyd_j_{o}"
                    )

    if st.button("➕ Přidat výdaj", type="primary", use_container_width=True, key="vyd_pridat"):
        if not castka or castka <= 0:
            st.warning("Zadej částku.")
        elif typ_del == "Jen vybraní" and not vybrani:
            st.warning("Vyber aspoň jednoho člověka.")
        else:
            if typ_del == "Ze společného banku":
                zk = "BANK"
            elif typ_del == "Všichni (otcové + děti)":
                zk = "VSICHNI"
            else:
                casti = []
                for o in vybrani:
                    j = rucni_jidla.get(o, jidla_otce(o))
                    casti.append(f"{o}:{int(j)}")
                zk = ";".join(casti)
            pridej_radek(rocnik, {
                "Typ": "vydaj", "Kdo": kdo, "Co": co.strip() or "—", "Castka": int(castka),
                "KrkDeti": 0, "ZaKoho": zk, "Datum": datetime.now().strftime("%d.%m.%Y %H:%M"),
            })
            st.rerun()

    st.write("")
    if not df_vyd.empty:
        for _, r in df_vyd.iterrows():
            zk = str(r["ZaKoho"])
            if zk == "BANK":
                popis = "ze společného banku"
            elif zk == "VSICHNI":
                popis = "všichni (otcové + děti)"
            else:
                kusy = []
                for cast in zk.split(";"):
                    if ":" in cast:
                        jm_o, j = cast.split(":")
                        kusy.append(f"{jm_o} ({j} j.)")
                    else:
                        kusy.append(cast)
                popis = ", ".join(kusy)
            castka_v = int(float(r["Castka"] or 0))
            c1, c2 = st.columns([5, 1])
            c1.markdown(
                f'<div class="karta">'
                f'<div class="avatar">{iniciala(r["Kdo"])}</div>'
                f'<div style="flex:1;"><div style="font-weight:600;font-size:15px;">{r["Co"]} · {castka_v} Kč</div>'
                f'<div style="font-size:12px;color:#888;">platil {r["Kdo"]} · {popis}</div></div>'
                f'</div>',
                unsafe_allow_html=True
            )
            with c2:
                tlacitko_smazat(rocnik, r["index"], f"vyd_{r['index']}")
    else:
        st.info("Zatím žádné výdaje.")
else:
    st.info("Nejdřív přidej účastníky (sekce 1 nahoře).")

# ─────────────────────────────────────────────
# 4) VYROVNÁNÍ
# ─────────────────────────────────────────────
st.header("4. Vyrovnání")

if otcove:
    saldo = {o: 0.0 for o in otcove}

    for _, r in df_vyd.iterrows():
        zk = str(r["ZaKoho"])
        if zk == "BANK":
            continue
        c = float(r["Castka"] or 0)
        if r["Kdo"] in saldo:
            saldo[r["Kdo"]] += c

        if zk == "VSICHNI":
            if celkem_jidel > 0:
                na_jidlo_v = c / celkem_jidel
                for o in otcove:
                    saldo[o] -= na_jidlo_v * jidla_otce(o)
        else:
            podily = {}
            for cast in zk.split(";"):
                if ":" in cast:
                    jm_o, j = cast.split(":")
                    if jm_o in saldo:
                        podily[jm_o] = int(float(j))
            soucet_j = sum(podily.values())
            if soucet_j > 0:
                na_jidlo_v = c / soucet_j
                for jm_o, j in podily.items():
                    saldo[jm_o] -= na_jidlo_v * j

    tbl = pd.DataFrame([{"Otec": o, "Saldo (Kč)": round(saldo[o])} for o in otcove])
    st.dataframe(tbl, use_container_width=True, hide_index=True)
    st.caption("Saldo: kladné = má dostat zpět, záporné = má doplatit. (Výdaje z banku se sem nepočítají.)")

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
    st.info("Přidej účastníky, bank a výdaje.")

st.divider()
st.caption(f"Data ročníku „{rocnik}\" se ukládají do Google Sheets a jsou sdílená pro všechny s odkazem.")
