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
        # Pobieramy dane z pominięciem pierwszego wiersza
        df = pd.read_csv(url_google_sheets, header=1)
        df = df.dropna(how='all')
        
        # Filtrujemy puste miesiące - zostawiamy tylko wiersze z wpisanym Tickerem
        if 'Ticker' in df.columns:
            df = df.dropna(subset=['Ticker'])
            
        return df
    except Exception as e:
        st.error(f"Błąd podczas wczytywania danych: {e}")
        return None

df_surowe = wczytaj_dane()

if df_surowe is not None:
    st.success("Dane z Google Sheets zostały pomyślnie załadowane i wyczyszczone!")
    
    # --- PASEK BOCZNY (FILTRY) ---
    st.sidebar.header("Opcje Filtrowania")
    if 'Konto' in df_surowe.columns:
        wszystkie_konta = df_surowe['Konto'].dropna().unique().tolist()
        wybrane_konta = st.sidebar.multiselect(
            "Wybierz konto (np. IKE, IKZE, XTB):", 
            options=wszystkie_konta, 
            default=wszystkie_konta
        )
        
        # Aplikujemy filtr
        if wybrane_konta:
            df_filtrowane = df_surowe[df_surowe['Konto'].isin(wybrane_konta)].copy()
        else:
            df_filtrowane = df_surowe.copy()
    else:
        df_filtrowane = df_surowe.copy()
        
    # --- GŁÓWNA TABELA ---
    st.subheader("Szczegóły portfela")
    # hide_index=True usunie tę brzydką pierwszą kolumnę z numerkami (2, 3, 4...)
    st.dataframe(df_filtrowane, use_container_width=True, hide_index=True)
    
    # --- TABELA UDZIAŁÓW I WYKRES ---
    st.divider()
    st.subheader("Struktura portfela (Alokacja)")
    
    # Sprawdzamy, czy w pliku jest kolumna z wartością do zrobienia wykresu
    if 'Wartość rynkowa [PLN]' in df_filtrowane.columns and 'INSTRUMENT' in df_filtrowane.columns:
        
        # Czyścimy wartości, by dało się je sumować matematycznie
        df_filtrowane['Wartość PLN (liczba)'] = df_filtrowane['Wartość rynkowa [PLN]'].apply(czysc_liczbe)
        
        # Grupowanie udziałów wg Instrumentu
        df_udzialy = df_filtrowane.groupby(['Konto', 'INSTRUMENT'])['Wartość PLN (liczba)'].sum().reset_index()
        # Pomijamy instrumenty z zerową wartością i sortujemy malejąco
        df_udzialy = df_udzialy[df_udzialy['Wartość PLN (liczba)'] > 0]
        df_udzialy = df_udzialy.sort_values(by='Wartość PLN (liczba)', ascending=False)
        
        kolumna_tabela, kolumna_wykres = st.columns([1, 1])
