import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(
    page_title="Portfel",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Dashboard Portfela")

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
    
    # Skracamy nazwę długiej kolumny z ceną rynkową od razu po załadowaniu
    dluga_nazwa = next((c for c in df_surowe.columns if 'AKTUALNA CENA RYNKOWA' in c.upper()), None)
    if dluga_nazwa:
        df_surowe = df_surowe.rename(columns={dluga_nazwa: 'Aktualna cena'})
    
    col_konto = next((c for c in df_surowe.columns if 'KONTO' in c.upper()), None)
    col_instrument = next((c for c in df_surowe.columns if 'INSTRUMENT' in c.upper()), None)
    
    # --- PASEK BOCZNY (FILTRY) ---
    st.sidebar.header("Opcje Filtrowania")
    if col_konto:
        wszystkie_konta = df_surowe[col_konto].dropna().unique().tolist()
        wybrane_konta = st.sidebar.multiselect(
            "Wybierz konto (np. IKE, IKZE, XTB):", 
            options=wszystkie_konta, 
            default=wszystkie_konta
        )
        if wybrane_konta:
            df_filtrowane = df_surowe[df_surowe[col_konto].isin(wybrane_konta)].copy()
        else:
            df_filtrowane = df_surowe.copy()
    else:
        df_filtrowane = df_surowe.copy()
        
    # --- GŁÓWNA TABELA ---
    st.subheader("Szczegóły portfela")
    
    szukane_kolumny = ['LP', 'INSTRUMENT', 'ŚREDNIA CENA ZAKUPU', 'AKTUALNA CENA', 'RÓŻNICA']
    wybrane_kolumny = []
    
    for c in df_filtrowane.columns:
        if any(szukana in c.upper() for szukana in szukane_kolumny):
            wybrane_kolumny.append(c)
            
    if wybrane_kolumny:
        st.dataframe(df_filtrowane[wybrane_kolumny], use_container_width=True, hide_index=True)
    else:
        st.dataframe(df_filtrowane, use_container_width=True, hide_index=True)
        
    # --- REKOMENDACJE (OKAZJE DO DOKUPIENIA) ---
    col_rek = next((c for c in df_filtrowane.columns if 'REKOMENDACJA' in c.upper()), None)
    
    if col_rek and col_instrument:
        okazje = df_filtrowane[df_filtrowane[col_rek].astype(str).str.contains('OKAZJA|DOKUP', case=False, na=False)]
        
        if not okazje.empty:
            st.success("🎯 **Sygnały inwestycyjne - rozważ dokupienie tych pozycji:**")
            
            kolumny_okazje = [col_instrument]
            
            # Cena
            col_cena = next((c for c in df_filtrowane.columns if 'AKTUALNA CENA' in c.upper()), None)
            if col_cena: kolumny_okazje.append(col_cena)
            
            # Różnica procentowa przed sygnałem
            col_roznica_proc = next((c for c in df_filtrowane.columns if 'RÓŻNICA [%]' in c.upper()), None)
            if col_roznica_proc: kolumny_okazje.append(col_roznica_proc)
            
            # Rekomendacja (Sygnał)
            kolumny_okazje.append(col_rek)
            
            st.dataframe(okazje[kolumny_okazje], use_container_width=True, hide_index=True)

    # --- NOWA TABELA UDZIAŁÓW ---
    st.divider()
    st.subheader("Struktura portfela (Alokacja)")
    
    col_udzial = next((c for c in df_filtrowane.columns if 'AKTUALNY UDZIAŁ' in c.upper() or 'UDZIAŁ PROCENTOWY'
