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
    
    col_udzial = next((c for c in df_filtrowane.columns if 'AKTUALNY UDZIAŁ' in c.upper() or 'UDZIAŁ PROCENTOWY' in c.upper()), None)
    col_cel = next((c for c in df_filtrowane.columns if 'CEL' in c.upper()), None)
    
    if col_konto and col_instrument and col_udzial and col_cel:
        df_alokacja = df_filtrowane[[col_konto, col_instrument, col_udzial, col_cel]].copy()
        
        df_alokacja.rename(columns={
            col_konto: 'Konto',
            col_instrument: 'Nazwa',
            col_udzial: 'Udział procentowy',
            col_cel: 'Udział cel'
        }, inplace=True)
        
        st.dataframe(df_alokacja, use_container_width=True, hide_index=True)
    else:
        st.info("Nie odnaleziono wszystkich potrzebnych kolumn do wyświetlenia tabeli udziałów (Konto, Instrument, Udział w portfelu, Cel).")
        
    # --- WYKRES POD TABELĄ ---
    col_wartosc = next((c for c in df_filtrowane.columns if 'WARTOŚĆ RYNKOWA' in c.upper()), None)
    
    if col_wartosc and col_instrument:
        st.markdown("<br>**Wykres podziału portfela**", unsafe_allow_html=True)
        
        df_wykres = df_filtrowane.copy()
        df_wykres['Wartość PLN'] = df_wykres[col_wartosc].apply(czysc_liczbe)
        
        df_wykres = df_wykres[df_wykres['Wartość PLN'] > 0]
        
        wykres = alt.Chart(df_wykres).mark_arc(innerRadius=60).encode(
            theta=alt.Theta(field="Wartość PLN", type="quantitative"),
            color=alt.Color(field=col_instrument, type="nominal", legend=alt.Legend(title="Instrumenty")),
            tooltip=[col_konto, col_instrument, 'Wartość PLN'] if col_konto else [col_instrument, 'Wartość PLN']
        ).properties(height=450)
        
        st.altair_chart(wykres, use_container_width=True)

else:
    st.warning("Oczekiwanie na dane lub problem z połączeniem z arkuszem.")
