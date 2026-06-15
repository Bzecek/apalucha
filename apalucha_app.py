import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# ─────────────────────────────────────────────
# KONFIGURACE — les + oheň (zelená základ, jantar jako akcent)
# ─────────────────────────────────────────────
ZELENA_HL   = "#6aa84f"   # hlavní lesní zelená (tlačítka, jméno)
ZELENA_SVE  = "#8cc56a"   # světlejší zeleň pro text na tmavém
OHEN        = "#c1843c"   # jantarový akcent (banner proužek, čísla)
OHEN_SVE    = "#c1843c"
ZELENA      = "#7bbf5a"   # kladné saldo
CERVENA     = "#d9603f"   # záporné saldo
ZELENA_KARTA = "rgba(106,168,79,0.12)"   # podklad avataru/karet

OTCOVE_SEZNAM = ["Bzek", "Pošták", "Boss", "Tonda", "Jirka", "Kolouch"]

st.set_page_config(page_title="Apalucha", page_icon="🏕️", layout="centered")

st.markdown(f"""
    <style>
    div.stButton > button {{
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.15s ease;
    }}
    div.stButton > button:hover {{
        border-color: {ZELENA_HL};
        color: {ZELENA_SVE};
    }}
    div.stButton > button[kind="primary"] {{
        background-color: {ZELENA_HL};
        border-color: {ZELENA_HL};
        color: #0c1a06;
    }}
    div.stButton > button[kind="primary"]:hover {{
        background-color: #5a9442;
        border-color: #5a9442;
        color: #fff;
    }}
    [data-testid="stMetricValue"] {{ color: {ZELENA_SVE}; }}
    .karta {{
        background: {ZELENA_KARTA};
        border: 1px solid rgba(106,168,79,0.22);
        border-radius: 14px;
        padding: 10px 14px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
    }}
    .avatar {{
        width: 38px; height: 38px; border-radius: 50%;
        background: {ZELENA_KARTA}; color: {ZELENA_SVE};
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 14px; margin-right: 12px;
        flex-shrink: 0;
        border: 1px solid rgba(106,168,79,0.4);
    }}
    /* tábornický banner — zelené jméno, ohnivý boční proužek */
    .banner {{
        background: linear-gradient(180deg, rgba(106,168,79,0.10), rgba(106,168,79,0.02));
        border-left: 5px solid {OHEN};
        border-radius: 14px;
        padding: 20px 22px;
        margin-bottom: 6px;
    }}
    .banner-nazev {{
        font-size: 34px; font-weight: 700; color: {ZELENA_SVE};
        margin: 0; line-height: 1.1;
    }}
    .banner-podtitul {{
        font-size: 13px; color: var(--text-color, #888);
        margin-top: 6px; opacity: 0.85;
    }}
    /* účtenka — ohnivý okraj jako uhlíky */
    .uctenka {{
        border: 1px dashed rgba(193,132,60,0.55);
        border-radius: 12px;
        padding: 16px 18px;
        margin-top: 14px;
        font-family: monospace;
    }}
    .uctenka-hlava {{
        text-align: center; font-size: 12px; letter-spacing: 1px;
        color: {OHEN}; border-bottom: 1px dashed rgba(193,132,60,0.4);
        padding-bottom: 8px; margin-bottom: 10px;
    }}
    .uctenka-radek {{
        display: flex; justify-content: space-between;
        font-size: 14px; padding: 3px 0;
    }}
    </style>
""", unsafe_allow_html=True)

# zpětná kompatibilita názvů barev používaných dál v kódu
BARVA = ZELENA_HL
BARVA_SVE = ZELENA_SVE

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


def uprav_radek(rocnik, idx, radek):
    """Přepíše existující řádek (podle indexu) novými hodnotami."""
    df = nacti(rocnik).reset_index(drop=True)
    if idx in df.index:
        for klic, hodnota in radek.items():
            df.at[idx, klic] = hodnota
        uloz(rocnik, df)
    else:
        pridej_radek(rocnik, radek)


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
rok_ted = datetime.now().year
roky = [str(r) for r in range(rok_ted + 1, 2019, -1)]
c_rok, c_novy = st.columns([2, 1])
rocnik = c_rok.selectbox("Ročník Apaluchy", roky, index=roky.index(str(rok_ted)) if str(rok_ted) in roky else 0)
vlastni = c_novy.text_input("…nebo vlastní list", placeholder="2026_jaro")
if vlastni.strip():
    rocnik = vlastni.strip()

# tábornický banner (varianta B) — zobrazí i vybraný ročník
st.markdown(
    f'<div class="banner">'
    f'<div class="banner-nazev">🏕️ Apalucha</div>'
    f'<div class="banner-podtitul">Pánská jízda s dětmi · ročník {rocnik}</div>'
    f'</div>',
    unsafe_allow_html=True
)
st.caption("Appka pohlídá, kdo komu kolik dluží.")

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
if "edit_vyd_idx" not in st.session_state:
    st.session_state.edit_vyd_idx = None

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
                f'<div style="font-size:12px;color:#888;">{deti_text(deti)} · {1 + deti} osob</div></div>'
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

st.header("2. Společný bank")

# Přehled banku — VŽDY viditelný (mimo sbalený panel)
m1, m2, m3 = st.columns(3)
m1.metric("Vloženo", f"{bank_vlozeno} Kč")
m2.metric("Utraceno z banku", f"{bank_utraceno} Kč")
m3.metric("Zůstatek", f"{bank_zustatek} Kč")

# proužek vyčerpání banku (zelená → oranžová → červená)
if bank_vlozeno > 0:
    procento = bank_utraceno / bank_vlozeno
    if procento < 0.7:
        barva_bar = "#2e7d32"   # zelená
    elif procento <= 1.0:
        barva_bar = "#e67e22"   # oranžová
    else:
        barva_bar = "#c0392b"   # červená
    sirka = min(procento * 100, 100)
    st.markdown(
        f"""
        <div style="margin:4px 0 8px 0;">
            <div style="background:rgba(127,127,127,0.15);border-radius:8px;height:12px;overflow:hidden;">
                <div style="width:{sirka:.0f}%;height:100%;background:{barva_bar};
                            border-radius:8px;transition:width 0.4s ease;"></div>
            </div>
            <div style="font-size:11px;color:#888;margin-top:3px;text-align:right;">
                vyčerpáno {procento*100:.0f} %
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

if bank_zustatek < 0:
    st.warning("Bank je v mínusu — utratilo se víc, než kolik je v něm vloženo. 😬")
st.caption("Zůstatek zůstává v banku na příště, nerozpočítává se mezi otce.")

with st.expander("✏️ Upravit vklady do banku", expanded=False):
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
    else:
        st.info("Nejdřív přidej účastníky.")

# ─────────────────────────────────────────────
# 3) VÝDAJE
# ─────────────────────────────────────────────
st.header("3. Výdaje – kdo platil za koho")

if otcove:
    # zjistíme, jestli editujeme — pokud ano, předvyplníme hodnoty
    edit_idx = st.session_state.edit_vyd_idx
    edit_radek = None
    if edit_idx is not None:
        _shoda = df_vyd[df_vyd["index"] == edit_idx]
        if not _shoda.empty:
            edit_radek = _shoda.iloc[0]
        else:
            st.session_state.edit_vyd_idx = None
            edit_idx = None

    if edit_radek is not None:
        st.info(f"📝 Upravuješ výdaj: **{edit_radek['Co']}**")
    else:
        st.caption("Zadej, kdo platil, kolik, a koho se výdaj týká. Dělí se na osoby (otec + jeho děti).")

    # předvyplnění hodnot při editaci (jen když ještě nejsou v session_state)
    if edit_radek is not None and "vyd_nacteno" not in st.session_state:
        st.session_state["vyd_co"] = str(edit_radek["Co"]) if edit_radek["Co"] else ""
        st.session_state["vyd_kdo"] = str(edit_radek["Kdo"])
        st.session_state["vyd_castka"] = int(float(edit_radek["Castka"] or 0))
        zk_e = str(edit_radek["ZaKoho"])
        if zk_e == "BANK":
            st.session_state["vyd_typ"] = "Ze společného banku"
        elif zk_e == "VSICHNI":
            st.session_state["vyd_typ"] = "Všichni (otcové + děti)"
        else:
            st.session_state["vyd_typ"] = "Jen vybraní"
            vyb = []
            for cast in zk_e.split(";"):
                if ":" in cast:
                    jm_o, j = cast.split(":")
                    vyb.append(jm_o)
                    st.session_state[f"vyd_j_{jm_o}"] = int(float(j))
            st.session_state["vyd_vyb"] = vyb
            st.session_state["vyd_uprav"] = True
        st.session_state["vyd_nacteno"] = True

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
            uprav = st.checkbox("Ručně upravit počet osob u vybraných", key="vyd_uprav")
            if uprav:
                st.caption("Kolik osob (otec + děti) připadá na každého u tohoto výdaje:")
                for o in vybrani:
                    rucni_jidla[o] = st.number_input(
                        f"{o} — počet osob",
                        min_value=1, max_value=20, value=jidla_otce(o), step=1, key=f"vyd_j_{o}"
                    )

    def _vycisti_formular():
        for k in ["vyd_co", "vyd_castka", "vyd_typ", "vyd_vyb", "vyd_uprav", "vyd_nacteno"]:
            st.session_state.pop(k, None)
        for o in OTCOVE_SEZNAM:
            st.session_state.pop(f"vyd_j_{o}", None)
        st.session_state.edit_vyd_idx = None

    popisek_tlacitka = "💾 Uložit změny" if edit_radek is not None else "➕ Přidat výdaj"
    cb1, cb2 = st.columns([3, 1]) if edit_radek is not None else (st.container(), None)

    klik_ulozit = cb1.button(popisek_tlacitka, type="primary", use_container_width=True, key="vyd_pridat")
    klik_zrusit = cb2.button("Zrušit", use_container_width=True, key="vyd_zrusit") if cb2 is not None else False

    if klik_zrusit:
        _vycisti_formular()
        st.rerun()

    if klik_ulozit:
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
            radek_data = {
                "Typ": "vydaj", "Kdo": kdo, "Co": co.strip() or "—", "Castka": int(castka),
                "KrkDeti": 0, "ZaKoho": zk, "Datum": datetime.now().strftime("%d.%m.%Y %H:%M"),
            }
            if edit_radek is not None:
                uprav_radek(rocnik, edit_idx, radek_data)
            else:
                pridej_radek(rocnik, radek_data)
            _vycisti_formular()
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
                        kusy.append(f"{jm_o} ({j} os.)")
                    else:
                        kusy.append(cast)
                popis = ", ".join(kusy)
            castka_v = int(float(r["Castka"] or 0))
            c1, c2, c3 = st.columns([5, 1, 1])
            c1.markdown(
                f'<div class="karta">'
                f'<div class="avatar">{iniciala(r["Kdo"])}</div>'
                f'<div style="flex:1;"><div style="font-weight:600;font-size:15px;">{r["Co"]} · {castka_v} Kč</div>'
                f'<div style="font-size:12px;color:#888;">platil {r["Kdo"]} · {popis}</div></div>'
                f'</div>',
                unsafe_allow_html=True
            )
            with c2:
                if st.button("✏️", key=f"edit_vyd_{r['index']}", use_container_width=True):
                    # vyčistíme případný předchozí stav a nastavíme nový k editaci
                    for k in ["vyd_co", "vyd_castka", "vyd_typ", "vyd_vyb", "vyd_uprav", "vyd_nacteno"]:
                        st.session_state.pop(k, None)
                    for o in OTCOVE_SEZNAM:
                        st.session_state.pop(f"vyd_j_{o}", None)
                    st.session_state.edit_vyd_idx = r["index"]
                    st.rerun()
            with c3:
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

    st.caption("Saldo: zelené = má dostat zpět, červené = má doplatit. (Výdaje z banku se sem nepočítají.)")
    for o in otcove:
        s = round(saldo[o])
        if s > 0:
            barva_s = ZELENA; znak = "+"; popis_s = "dostane zpět"
        elif s < 0:
            barva_s = CERVENA; znak = ""; popis_s = "doplatí"
        else:
            barva_s = "#888"; znak = ""; popis_s = "vyrovnán"
        st.markdown(
            f'<div class="karta" style="justify-content:space-between;">'
            f'<div style="display:flex;align-items:center;">'
            f'<div class="avatar">{iniciala(o)}</div>'
            f'<div style="font-weight:600;font-size:15px;">{o}</div></div>'
            f'<div style="text-align:right;">'
            f'<div style="font-weight:700;font-size:16px;color:{barva_s};">{znak}{s} Kč</div>'
            f'<div style="font-size:11px;color:#888;">{popis_s}</div></div>'
            f'</div>',
            unsafe_allow_html=True
        )

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
        # tábornická účtenka
        radky_html = "".join(
            f'<div class="uctenka-radek"><span>{od} → {komu}</span><span>{int(c)} Kč</span></div>'
            for od, komu, c in platby
        )
        st.markdown(
            f'<div class="uctenka">'
            f'<div class="uctenka-hlava">— ÚČTENKA APALUCHA {rocnik} —</div>'
            f'{radky_html}'
            f'</div>',
            unsafe_allow_html=True
        )
        radky_txt = [f"{od} → {komu}: {int(c)} Kč" for od, komu, c in platby]
        souhrn = f"🏕️ Apalucha {rocnik} – vyrovnání:\n" + "\n".join(radky_txt)
        st.text_area("Pro zkopírování do skupiny", souhrn, height=120)
    else:
        st.success("Všichni vyrovnaní, můžeme na pivo 🍺")

    # Celková útrata za celou partu — pro představu, kolik nás to stálo
    utrata_celkem = sum(int(float(r["Castka"] or 0)) for _, r in df_vyd.iterrows())
    st.divider()
    st.subheader("💸 Celková útrata")
    cu1, cu2 = st.columns(2)
    cu1.metric("Všechny výdaje dohromady", f"{utrata_celkem} Kč")
    if celkem_jidel > 0:
        cu2.metric("Na jednu osobu (orientačně)", f"{round(utrata_celkem / celkem_jidel)} Kč")
    st.caption("Součet všech výdajů (z banku i mezi otci) — kolik nás celá Apalucha stála.")
else:
    st.info("Přidej účastníky, bank a výdaje.")

st.divider()
st.caption(f"Data ročníku „{rocnik}\" se ukládají do Google Sheets a jsou sdílená pro všechny s odkazem.")

st.markdown(f"""
    <div style="background-color:rgba(106,168,79,0.08);border:1px solid rgba(106,168,79,0.22);
                padding:16px;border-radius:14px;margin-top:18px;text-align:center;">
        <span style="font-weight:700;font-size:0.95rem;color:{ZELENA_SVE};">🏕️ Apalucha</span><br>
        <span style="color:#888;font-size:0.78rem;">Pánská jízda s dětmi pod stanem</span>
        <div style="margin:10px auto;border-top:1px dashed rgba(193,132,60,0.5);width:60%;"></div>
        <span style="font-size:0.82rem;">Autor: <b>Pavel Dvořáček</b></span><br>
        <a href="mailto:pavel.dvoracek@obchod.t-mobile.cz?subject=Apalucha%20-%20zpetna%20vazba"
           style="display:inline-block;margin-top:8px;color:#0c1a06!important;background-color:{ZELENA_HL};
                  padding:6px 16px;border-radius:18px;text-decoration:none;font-size:0.78rem;font-weight:700;">
           📩 Napsat autorovi
        </a>
    </div>
""", unsafe_allow_html=True)

