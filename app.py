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

# Funkcja do radzenia sobie z widełkami celów (np. "4-6%")
def parsuj_procent_cel(wartosc):
    if pd.isna(wartosc): return 0.0
    val = str(wartosc).replace('%', '').replace(' ', '')
    if '-' in val:
        parts = val.split('-')
        try:
            return (float(parts[0].replace(',', '.')) + float(parts[1].replace(',', '.'))) / 2.0
        except:
            return 0.0
    try:
        return float(val.replace(',', '.'))
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
    
    # --- PASEK BOCZNY ---
    st.sidebar.header("📊 Filtrowanie")
    if col_konto:
        unikalne_konta = sorted(list(set(df_surowe[col_konto].dropna().astype(str).str.strip().tolist())))
        opcje_filtru = ["Wszystkie"] + unikalne_konta
        
        wybrane_konto = st.sidebar.selectbox(
            "Wybierz konto:", 
            options=opcje_filtru, 
            index=0,
            key="filtr_konta_single"
        )
        
        if wybrane_konto == "Wszystkie":
            df_filtrowane = df_surowe.copy()
        else:
            df_filtrowane = df_surowe[df_surowe[col_konto].astype(str).str.strip() == wybrane_konto].copy()
    else:
        df_filtrowane = df_surowe.copy()
        
    st.sidebar.divider()
    st.sidebar.header("🧮 Kalkulator wpłat")
    kwota_wplaty = st.sidebar.number_input("Planowana wpłata (PLN):", min_value=0.0, step=100.0, value=0.0)
        
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
        
        if col_zysk and col_wartosc:
            suma_zysku = df_filtrowane[col_zysk].apply(czysc_liczbe).sum()
            suma_wartosci = df_filtrowane[col_wartosc].apply(czysc_liczbe).sum()
            suma_kosztu = suma_wartosci - suma_zysku
            srednia_wazona_stopa = (suma_zysku / suma_kosztu) * 100 if suma_kosztu > 0 else stopy_liczby.mean()
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

    # --- WIZUALIZACJA I KALKULATOR (NOWOŚĆ) ---
    col_udzial = next((c for c in df_filtrowane.columns if 'AKTUALNY UDZIAŁ' in c.upper() or 'UDZIAŁ PROCENTOWY' in c.upper()), None)
    col_cel = next((c for c in df_filtrowane.columns if 'CEL' in c.upper()), None)

    if col_udzial and col_cel and col_wartosc and col_instrument:
        st.divider()
        st.subheader("⚖️ Rebalancing i Kalkulator wpłat")
        
        # Przygotowanie danych do matematyki
        df_calc = df_filtrowane.copy()
        df_calc['Aktualny_proc'] = df_calc[col_udzial].apply(parsuj_procent_cel)
        df_calc['Cel_proc'] = df_calc[col_cel].apply(parsuj_procent_cel)
        df_calc['Wartość_PLN'] = df_calc[col_wartosc].apply(czysc_liczbe)
        
        # Obliczanie odchylenia: Cel - Aktualny. Wynik dodatni = brakuje nam tego w portfelu.
        df_calc['Odchylenie'] = df_calc['Cel_proc'] - df_calc['Aktualny_proc']
        
        # 1. WYKRES ODCHYLEŃ
        st.markdown("**Odchylenie od celu (w punktach procentowych)**")
        wykres_odchylen = alt.Chart(df_calc).mark_bar().encode(
            x=alt.X('Odchylenie:Q', title='Brakujący udział (%) ->', scale=alt.Scale(domainMid=0)),
            y=alt.Y(f'{col_instrument}:N', sort='-x', title=''),
            color=alt.condition(
                alt.datum.Odchylenie > 0,
                alt.value('#27ae60'),  # Zielony - trzeba dokupić
                alt.value('#e74c3c')   # Czerwony - jest tego za dużo
            ),
            tooltip=[col_instrument, 'Aktualny_proc', 'Cel_proc', 'Odchylenie']
        ).properties(height=350)
        st.altair_chart(wykres_odchylen, use_container_width=True)
        
        # 2. KALKULATOR ZAKUPÓW
        if kwota_wplaty > 0:
            st.markdown(f"**Jak optymalnie zainwestować {kwota_wplaty:,.2f} PLN, aby wyrównać portfel?**")
            
            # Normalizujemy cele (przydaje się, gdy filtrujemy np. tylko "IKE" i cele nie sumują się do 100%)
            suma_celow = df_calc['Cel_proc'].sum()
            if suma_celow > 0:
                obecna_wart = df_calc['Wartość_PLN'].sum()
                docelowa_wart = obecna_wart + kwota_wplaty
                
                # Obliczamy ile PLN POWINNO być w danym instrumencie po wpłacie
                df_calc['Docelowa_Kwota'] = docelowa_wart * (df_calc['Cel_proc'] / suma_celow)
                
                # Obliczamy braki kwotowe
                df_calc['Brakuje_PLN'] = df_calc['Docelowa_Kwota'] - df_calc['Wartość_PLN']
                
                # Filtrujemy tylko te,
