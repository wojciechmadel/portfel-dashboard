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
    if pd.isna(wartosc) or wartosc == "#DIV/0!" or wartosc == "Brak danych":
        return 0.0
    if isinstance(wartosc, str):
        wartosc = (wartosc.replace('zł', '')
                          .replace('zł', '')
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
        tabele = pd.read_html(url_google_sheets)
        if tabele:
            df = tabele[0]
            return df
    except Exception as e:
        st.error(f"Błąd podczas wczytywania danych: {e}")
    return None

df_surowe = wczytaj_dane()

if df_surowe is not None:
    st.success("Dane z Google Sheets zostały pomyślnie załadowane!")
    st.subheader("Podgląd tabeli z arkusza")
    st.dataframe(df_surowe)
else:
    st.warning("Oczekiwanie na dane lub problem z połączeniem z arkuszem.")
