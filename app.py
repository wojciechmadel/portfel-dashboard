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
    col_zysk = next((c for c in df_surowe.columns if 'ZYSK NETTO' in c.upper() or 'ZYSK / STRATA' in c.upper()), None)
    
    # --- PASEK BOCZNY (TYLKO JEDNOKROTNY WYBÓR - BEZ IKSÓW I TAGÓW) ---
    st.sidebar.header("📊 Filtrowanie")
    if col_konto:
        unikalne_konta = sorted(list(set(df_surowe[col_konto].dropna().astype(str).str.strip().tolist())))
        opcje_filtru = ["Wszystkie"] + unikalne_konta
        
        wybrane_konto = st.sidebar.selectbox(
            "Wybierz konto:", 
            options=opcje_filtru, 
            index=0,
            key="filtr_konta_czysta_lista"
        )
        
        if wybrane_konto == "Wszystkie":
            df_filtrowane = df_surowe.copy()
        else:
            df_filtrowane = df_surowe[df_surowe[col_konto].astype(str).str.strip() == wybrane_konto].copy()
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
        
        # WAŻONA STOPA ZWROTU
        if col_zysk and col_wartosc:
            suma_zysku = df_filtrowane[col_zysk].apply(czysc_liczbe).sum()
            suma_wartosci = df_filtrowane[col_wartosc].apply(czysc_liczbe).sum()
            suma_kosztu = suma_wartosci - suma_zysku
            
            if suma_kosztu > 0:
                srednia_wazona_stopa = (suma_zysku / suma_kosztu) * 100
            else:
                srednia_wazona_stopa = stopy_liczby.mean()
        else:
            srednia_wazona_stopa = stopy_liczby.mean()
            
        col_m2.metric("Średnia ważona stopa zwrotu", f"{srednia_wazona_stopa:+.2f}%".replace('.', ','))
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
        st.dataframe(df_filtrowane, use_container_width=True, hide_index=True)
        
    # --- REKOMENDACJE (OKAZJE DO DOKUPIENIA) ---
    col_rek = next((c for c in df_filtrowane.columns if 'REKOMENDACJA' in c.upper()), None)
    
    if col_rek and col_instrument:
        okazje = df_filtrowane[df_filtrowane[col_rek].astype(str).str.contains('OKAZJA|DOKUP', case=False, na=False)]
        
        if not okazje.empty:
            st.success("🎯 **Sygnały inwestycyjne - rozważ dokupienie tych pozycji:**")
            
            kolumny_okazje = [col_instrument]
            
            col_cena = next((c for c in df_filtrowane.columns if 'AKTUALNA CENA' in c.upper()), None)
            if col_cena and col_cena not in kolumny_okazje: kolumny_okazje.append(col_cena)
            
            col_roznica_proc = next((c for c in df_filtrowane.columns if 'RÓŻNICA [%]' in c.upper()), None)
            if col_roznica_proc and col_roznica_proc not in kolumny_okazje: kolumny_okazje.append(col_roznica_proc)
            
            if col_rek not in kolumny_okazje: kolumny_okazje.append(col_rek)
            
            st.dataframe(okazje[kolumny_okazje], use_container_width=True, hide_index=True)

    # --- TABELA UDZIAŁÓW ---
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
        st.info("Nie odnaleziono wszystkich potrzebnych kolumn do wyświetlenia tabeli udziałów.")
        
    # --- WYKRES ---
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
