import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(
    page_title="Portfel",
    page_icon="📈",
    layout="wide"
)

def czysc_liczbe(wartosc):
    if pd.isna(wartosc) or wartosc == "#DIV/0!" or str(wartosc).strip() == "Brak danych":
        return 0.0
    if isinstance(wartosc, str):
        wartosc = (wartosc.replace('zł', '')
                          .replace('PLN', '')
                          .replace('%', '')
                          .replace(' ', '')
                          .replace('\u00a0', '')
                          .replace(',', '.'))
    try:
        return float(wartosc)
    except:
        return 0.0

url_google_sheets = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQbbEQJDM7jtXbscroBG3cOG53wP1gbkccHHJNQsvNC0cpPl7fl30bTj6hwwp9eiG4FIdou6S7MjvE6/pub?gid=1930372896&single=true&output=csv"

@st.cache_data(ttl=60)
def wczytaj_dane():
    try:
        df = pd.read_csv(url_google_sheets, header=1)
        df.columns = df.columns.str.strip()
        df = df.loc[:, ~df.columns.duplicated()]
        df = df.dropna(how='all')
        
        col_ticker = next((c for c in df.columns if 'TICKER' in c.upper()), None)
        if col_ticker:
            df = df.dropna(subset=[col_ticker])
            
        return df
    except Exception as e:
        st.error(f"Błąd podczas wczytywania danych: {e}")
        return None

df_surowe = wczytaj_dane()

if df_surowe is not None:
    
    dluga_nazwa = next((c for c in df_surowe.columns if 'AKTUALNA CENA RYNKOWA' in c.upper()), None)
    if dluga_nazwa:
        df_surowe = df_surowe.rename(columns={dluga_nazwa: 'Aktualna cena'})
        df_surowe = df_surowe.loc[:, ~df_surowe.columns.duplicated()]
    
    col_konto = next((c for c in df_surowe.columns if 'KONTO' in c.upper()), None)
    col_instrument = next((c for c in df_surowe.columns if 'INSTRUMENT' in c.upper()), None)
    col_wartosc = next((c for c in df_surowe.columns if 'WARTOŚĆ RYNKOWA' in c.upper()), None)
    
    # --- PASEK BOCZNY (CZYSTA LISTA ROZWIJANA BEZ TAGÓW/KWADRATÓW) ---
    st.sidebar.header("📊 Filtrowanie")
    if col_konto:
        unikalne_konta = sorted(list(set(df_surowe[col_konto].dropna().astype(str).tolist())))
        opcje_filtru = ["Wszystkie"] + unikalne_konta
        
        # Klucz key wymusza odświeżenie widgetu na urządzeniach mobilnych
        wybrane_konto = st.sidebar.selectbox(
            "Wybierz konto:", 
            options=opcje_filtru, 
            index=0,
            key="filtr_konta_select"
        )
        
        if wybrane_konto == "Wszystkie":
            df_filtrowane = df_surowe.copy()
        else:
            df_filtrowane = df_surowe[df_surowe[col_konto].astype(str) == wybrane_konto].copy()
    else:
        df_filtrowane = df_surowe.copy()
        
    # --- TYTUŁ APLIKACJI ---
    st.title("📈 Dashboard Portfela")
        
    # --- PODSUMOWANIE NA GÓRZE ---
    st.subheader("Podsumowanie")
    col_m1, col_m2 = st.columns(2)
    
    col_stopa = next((c for c in df_filtrowane.columns if 'RÓŻNICA [%]' in c.upper() or 'STOPA ZWROTU' in c.upper()), None)
    
    if col_stopa:
        stopy_liczby = df_filtrowane[col_stopa].apply(czysc_liczbe)
        
        ile_plus = (stopy_liczby > 0).sum()
        ile_minus = (stopy_liczby < 0).sum()
        ile_zero = (stopy_liczby == 0).sum()
        
        col_m1.metric("Pozycje (Zielone / Czerwone)", f"🟢 {ile_plus}  |  🔴 {ile_minus}" + (f"  |  ⚪ {ile_zero}" if ile_zero > 0 else ""))
        
        srednia_stopa = stopy_liczby.mean()
        col_m2.metric("Średnia stopa zwrotu", f"{srednia_stopa:+.2f}%".replace('.', ','))
    else:
        col_m1.metric("Pozycje", "Brak danych")
        col_m2.metric("Średnia stopa zwrotu", "Brak kolumny")
        
    st.divider()
        
    # --- GŁÓWNA TABELA ---
    st.subheader("Szczegóły portfela")
    
    wybrane_kolumny = []
    for c in df_filtrowane.columns:
        c_up = c.upper()
        if c_up == 'LP' or 'INSTRUMENT' in c_up or 'ŚREDNIA CENA ZAKUPU' in c_up or 'AKTUALNA CENA' in c_up or 'RÓŻNICA [%]' in c_up:
            if c not in wybrane_kolumny:
                wybrane_kolumny.append(c)
            
    if wybrane_kolumny:
        st.dataframe(df_filtrowane[wybrane_kolumny], use_container_width=True, hide_index=True)
    else:
        st.dataframe(df
