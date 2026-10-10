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
        # header=1 ponieważ właściwe nazwy kolumn są w drugim wierszu
        df = pd.read_csv(url_google_sheets, header=1)
        
        # PANCERNY KROK: Usuwamy ukryte spacje z nazw kolumn!
        df.columns = df.columns.str.strip()
        df = df.dropna(how='all')
        
        # Filtrowanie pustych miesięcy po kolumnie Ticker (dynamicznie szuka kolumny)
        col_ticker = next((c for c in df.columns if 'TICKER' in c.upper()), None)
        if col_ticker:
            df = df.dropna(subset=[col_ticker])
            
        return df
    except Exception as e:
        st.error(f"Błąd podczas wczytywania danych: {e}")
        return None

df_surowe = wczytaj_dane()

if df_surowe is not None:
    
    # Dynamicznie odnajdujemy kolumnę z kontem
    col_konto = next((c for c in df_surowe.columns if 'KONTO' in c.upper()), None)
    
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
    st.dataframe(df_filtrowane, use_container_width=True, hide_index=True)
    
    # --- TABELA UDZIAŁÓW I WYKRES ---
    st.divider()
    st.subheader("Struktura portfela (Alokacja)")
    
    # Dynamicznie szukamy kolumn dla wykresu (odporne na literówki i spacje w arkuszu)
    col_wartosc = next((c for c in df_filtrowane.columns if 'WARTOŚĆ RYNKOWA' in c.upper()), None)
    col_instrument = next((c for c in df_filtrowane.columns if 'INSTRUMENT' in c.upper()), None)
    
    if col_wartosc and col_instrument:
        # Czyścimy dane do postaci liczbowej
        df_filtrowane['Wartość PLN'] = df_filtrowane[col_wartosc].apply(czysc_liczbe)
        
        # Grupowanie
        grupowanie = [col_instrument]
        if col_konto:
            grupowanie = [col_konto, col_instrument]
            
        df_udzialy = df_filtrowane.groupby(grupowanie)['Wartość PLN'].sum().reset_index()
        df_udzialy = df_udzialy[df_udzialy['Wartość PLN'] > 0]
        df_udzialy = df_udzialy.sort_values(by='Wartość PLN', ascending=False)
        
        kolumna_tabela, kolumna_wykres = st.columns([1, 1])
        
        with kolumna_tabela:
            st.markdown("**Podsumowanie udziałów**")
            st.dataframe(df_udzialy, use_container_width=True, hide_index=True)
            
        with kolumna_wykres:
            st.markdown("**Wykres wartości portfela**")
            
            wykres = alt.Chart(df_udzialy).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field="Wartość PLN", type="quantitative"),
                color=alt.Color(field=col_instrument, type="nominal", legend=alt.Legend(title="Instrumenty")),
                tooltip=grupowanie + ['Wartość PLN']
            ).properties(height=350)
            
            st.altair_chart(wykres, use_container_width=True)
    else:
        st.warning(f"Brak możliwości wygenerowania wykresu. Nie znaleziono odpowiednich kolumn. Dostępne kolumny to: {', '.join(df_filtrowane.columns)}")

else:
    st.warning("Oczekiwanie na dane lub problem z połączeniem z arkuszem.")
