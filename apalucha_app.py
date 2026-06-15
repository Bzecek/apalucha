[connections.gsheets]
spreadsheet = "https://docs.google.com/spreadsheets/d/19bLijNdL-_jF9gy3aTdc4oYRqMSnyrpfWF0G048zcIE/edit?gid=0#gid=0"
type = "service_account"
project_id = "apalucha-499518"
private_key_id = "f0b8c01039fdeda5b2d0e73d03f78a5cc6d9043f"
private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDCJzCSUlfCHQUN\ngTzw45mA3TSnR/cHYSw91YBYA/xRo5GyVqXyy7jROFIu2kCE8AG8QMwWJGpXhUvB\nI4mdtAA1b4+Dzho6ut3pi/zQyt9WpGCdNSW/QlaUIt+uwcU9eCY0OfCBcVKXknOe\nb90X1HBKZARw5ZO5WmqcMAqpQilNCBq+hGaCNWBppzZm8/DZ3W1jVT7NsfPSXmZe\n9lELFyfwKccojaPNFkBCb6lt2rGaG6NgHPuGnCJ+W52CUHlqLnZivSSkBUNoxd++\n0SKwS0n57iTJUw8ReVecxkjM8clFejZq68iMfYXJfWYx1MRdWu7mcrqhwA9HTGmz\nyrYC0aoRAgMBAAECggEALyLimPOi2L7A5kl1KSqoru+FhANlxwXhftWhxjyZepyS\nl9CPk4XARhM9aKCWP3Ahi7nTkqCerMbw4GAnXgFAd7ixCBf2qEGL9NKGu441cMyR\npDkuA+QwLuDUm5Hxt/2+kLlsWZDQs3nb1iBkdg+ef4EOzvX9ymdYMLk9LWChtFCS\nDNrbVlaNoceevdRzp2qbksmLlKiRdiSfMoCaIOzPqJ/0jX5VyP0Jy1EF9uDIfJdJ\nqjO8Cf9xgersYrWzYggjK6vIVrHwtUaEpLS0F5PjnZ0cglu+Z60VpPtdprjF0rkn\nxWD8vIzC/xPCa1mixjtrRE0o2w4b9zKTptzvRS4C7QKBgQDobGdLcwVV01jOXH0W\nomLhllPGFP0Xn8t8x6vvpOlkT8mgeTu1v8u9igncGqtkDGLMJ/D9nOHJ77KPXZkX\naFXVLOcBYV49SpO3NWx9GqDRZkDsj5tdOxeOCe5W3rz6oFoNUzmSvBAkvTqCdKhn\n3orzmpCgZz7SK21GF0vjUPHEKwKBgQDV2Po0WVBRPzGU7F+xHDPp0kwa1gTnSbFx\n4hPoSPYRq2tQemdK0ZoTofjKiwT3Mfu8mXmF9DoCCclPT9GXVQVCPLD8p2qeEE6b\nGz0mfTnr/q0a4wHWwY3mTvIYrC8qyBakx6/b+lUXXE96zS5zcOyQjA6vFcoG+pb/\nCGXyTxCAswKBgGRyLPYDgIPF8fRFLl4w0bESiaPqgDLMgWGs3VaVG7SZctbibfav\nK/r/BCHWeMmlPLFkdZb1TPM7nxysY7QlCCs326HSFatBZrNf6EHs1yGIInjZ21gg\naJ6fFhz+6Accc66ckB4lHojyKq4kgn9ZQw3id6yK0jB8Sh5nhQl5evK/AoGBAIQb\nJIZOXoWyiki7tWnOSGu8FHPHnwPazJnT1gR7fjfwM71lwIXB8nMKbo2BUDH9WMxr\n61zLQUKdFRW/83SPe04t/BA4xG6dGFJNg3tRhQS7MekYL7yhma2bO4fuZr0BGqv1\nCDjW7tYdmqP8OSPrsNijDTcwOLwS9lDauU/1c/ZtAoGBAM9Au1bSalYB9ZgOpDV4\nkltm4BADY0EcoRI366oZZaXCNarjM5KZR6zyhtCh9mW1HVm9ctHbUxY17KeD/eIs\n2p19L6fixI+pHAW08SGb8DOVIp3B6hfsZ9CeD/3oMq4hzSwjfebnIC39BPGVbtlg\njMfnmI5IJQdEHXg42Dnxx2W5\n-----END PRIVATE KEY-----\n"
client_email = "streamlit-apalucha@apalucha-499518.iam.gserviceaccount.com"
client_id = "104157882347641330047"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/streamlit-apalucha%40apalucha-499518.iam.gserviceaccount.com"
import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# ─────────────────────────────────────────────
# KONFIGURACE
# ─────────────────────────────────────────────
BARVA = "#2e7d32"  # lesní zelená

st.set_page_config(page_title="Apalucha – účtování", page_icon="🏕️", layout="centered")

st.markdown(f"""
    <style>
    div.stButton > button:first-child {{ border-radius: 12px; }}
    [data-testid="stMetricValue"] {{ color: {BARVA}; }}
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PŘIPOJENÍ NA GOOGLE SHEETS
# Každý ročník = vlastní list (worksheet) v jednom dokumentu.
# Sloupce: Typ, Kdo, Co, Castka, KrkDeti, ZaKoho, Datum
#   Typ:    "ucastnik" | "baget" | "vydaj"
#   ZaKoho: "BAGET" | "VSICHNI" | "Jméno1;Jméno2" (u výdajů)
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
        # List ještě neexistuje nebo je prázdný
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


# ─────────────────────────────────────────────
# VÝBĚR ROČNÍKU
# ─────────────────────────────────────────────
st.markdown(
    f'<div style="display:flex;align-items:center;margin-bottom:10px;">'
    f'<span style="font-size:40px;margin-right:10px;">🏕️</span>'
    f'<h1 style="margin:0;color:{BARVA};">Apalucha</h1></div>',
    unsafe_allow_html=True
)
st.caption("Otcové a děti pod stanem. Kdo platil za koho — appka spočítá vyrovnání.")

rok_ted = datetime.now().year
roky = [str(r) for r in range(rok_ted + 1, 2019, -1)]
c_rok, c_novy = st.columns([2, 1])
rocnik = c_rok.selectbox("Ročník Apaluchy", roky, index=roky.index(str(rok_ted)) if str(rok_ted) in roky else 0)
vlastni = c_novy.text_input("…nebo vlastní název listu", placeholder="např. 2026_jaro")
if vlastni.strip():
    rocnik = vlastni.strip()

st.divider()

df = nacti(rocnik)

# rozpad dat dle typu (zachováváme původní index z Google Sheetu)
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
# 1) ÚČASTNÍCI
# ─────────────────────────────────────────────
st.header("1. Otcové a děti")

with st.form("f_uc", clear_on_submit=True):
    c1, c2 = st.columns([2, 1])
    jm = c1.text_input("Jméno otce")
    pd_ = c2.number_input("Počet dětí", min_value=0, max_value=10, value=0, step=1)
    if st.form_submit_button("➕ Přidat účastníka", use_container_width=True):
        if jm.strip() and jm.strip() not in otcove:
            pridej_radek(rocnik, {
                "Typ": "ucastnik", "Kdo": jm.strip(), "Co": "", "Castka": 0,
                "KrkDeti": int(pd_), "ZaKoho": "", "Datum": datetime.now().strftime("%d.%m.%Y %H:%M"),
            })
            st.rerun()

if otcove:
    for _, r in df_uc.iterrows():
        c1, c2 = st.columns([4, 1])
        deti = int(float(r["KrkDeti"] or 0))
        c1.write(f"**{r['Kdo']}** — {deti} dětí (= {1 + deti} jídel)")
        if c2.button("🗑️", key=f"del_uc_{r['index']}"):
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
        st.caption("Zadej, kolik kdo vložil do společného bagetu. Tip: nech vyplnit částkou na jedno jídlo.")
        na_krk = st.number_input("Rychlé vyplnění: částka na jedno jídlo (Kč)", min_value=0, value=0, step=50)
        vlozky = {}
        for o in otcove:
            existuje = df_baget[df_baget["Kdo"] == o]
            if not existuje.empty:
                vychozi = int(float(existuje.iloc[0]["Castka"] or 0))
            else:
                vychozi = na_krk * krky(o) if na_krk else 0
            vlozky[o] = st.number_input(f"{o} ({krky(o)} jídel)", min_value=0, value=int(vychozi), step=50, key=f"bg_{o}")
        if st.form_submit_button("💾 Uložit baget", use_container_width=True):
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
        if st.form_submit_button("➕ Přidat výdaj", use_container_width=True):
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
            c1, c2 = st.columns([5, 1])
            c1.write(f"**{r['Kdo']}** zaplatil **{int(float(r['Castka'] or 0))} Kč** za _{r['Co']}_ ({popis})")
            if c2.button("🗑️", key=f"del_vyd_{r['index']}"):
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

    # baget: vklad = plus
    for _, b in df_baget.iterrows():
        if b["Kdo"] in saldo:
            saldo[b["Kdo"]] += float(b["Castka"] or 0)

    # výdaje z bagetu: platič dostává zpět; spotřeba se dělí podle krků
    baget_vydaje = sum(float(r["Castka"] or 0) for _, r in df_vyd.iterrows() if str(r["ZaKoho"]) == "BAGET")
    for _, r in df_vyd.iterrows():
        if str(r["ZaKoho"]) == "BAGET" and r["Kdo"] in saldo:
            saldo[r["Kdo"]] += float(r["Castka"] or 0)

    if celkem_krku > 0:
        baget_celkem_val = sum(float(b["Castka"] or 0) for _, b in df_baget.iterrows())
        # rozpočítá se to, co se z bagetu reálně utratilo; když nic, rozpočítá se vložený baget
        k_rozdeleni = baget_vydaje if baget_vydaje > 0 else baget_celkem_val
        na_krk = k_rozdeleni / celkem_krku
        for o in otcove:
            saldo[o] -= na_krk * krky(o)

    # ostatní výdaje
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

    # minimalizace plateb
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
