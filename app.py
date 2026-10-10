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
        wartosc = (wartosc.replace('€', '')
                          .replace('zł', '')
                          .replace(' ', '')
                          .replace('\u00a0', '')
                          .replace(',', '.'))
        if '%' in wartosc:
            wartosc = wartosc.replace('%', '')
            try:
                return float(wartosc) / 100.0
            except ValueError:
                return 0.0
    try:
        return float(wartosc)
    except (ValueError, TypeError):
        return 0.0

@st.cache_data(ttl=300)
def pobierz_dane():
      url_google_sheets = https://docs.google.com/spreadsheets/d/e/2PACX-1vQbbEQJDM7jtXbscroBG3cOG53wP1gbkccHHJNQsvNC0cpPl7fl30bTj6hwwp9eiG4FIdou6S7MjvE6/pubhtml
    
    df = pd.read_csv(url_google_sheets)
    df.columns = df.columns.astype(str).str.strip()
    return df

try:
    # --- PANEL BOCZNY (FILTRY I STATUS ZMIAN) ---
    st.sidebar.header("🔍 Filtry i Status")
    
    df_aktualne = pobierz_dane()

    if "poprzedni_df" in st.session_state:
        czy_sie_zmienily = not st.session_state["poprzedni_df"].equals(df_aktualne)
    else:
        czy_sie_zmienily = False

    if st.sidebar.button("🔄 Odśwież dane z arkusza"):
        st.cache_data.clear()
        st.session_state["poprzedni_df"] = df_aktualne.copy()
        st.rerun()

    if "poprzedni_df" in st.session_state and not czy_sie_zmienily:
        st.sidebar.markdown("🔴 **Status:** Dane stoją w miejscu (brak zmian)")
    else:
        st.sidebar.markdown("🟢 **Status:** Dane aktywne / zaktualizowane")

    # Filtrujemy wiersze, które mają numer LP lub Instrument
    df = df_aktualne.dropna(subset=["INSTRUMENT"]).copy()
    if "LP" in df.columns:
        df = df[df["LP"].notna() & (df["LP"] != "")]

    # Czyszczenie kolumn liczbowych
    kol_srednia = "Średnia cena zakupu"
    kol_aktualna = "Aktualna cena rynkowa (pobierana automatycznie)"
    kol_roznica_proc = "Różnica [%]"
    kol_zwrotu = "Średnia stopa zwrotu [%]"
    kol_udzialu = "Aktualny udział w portfelu"

    if kol_srednia in df.columns:
        df[kol_srednia] = df[kol_srednia].apply(czysc_liczbe)
    if kol_aktualna in df.columns:
        df[kol_aktualna] = df[kol_aktualna].apply(czysc_liczbe)
    if kol_roznica_proc in df.columns:
        df[kol_roznica_proc] = df[kol_roznica_proc].apply(czysc_liczbe)
    if kol_zwrotu in df.columns:
        df[kol_zwrotu] = df[kol_zwrotu].apply(czysc_liczbe)
    if kol_udzialu in df.columns:
        df[kol_udzialu] = df[kol_udzialu].apply(czysc_liczbe)

    df_posiadane = df[df[kol_srednia] > 0].copy()

    if "Konto" in df_posiadane.columns:
        dostepne_konta = ["Wszystkie"] + list(df_posiadane["Konto"].dropna().unique())
        wybrane_konto = st.sidebar.selectbox("Wybierz konto", dostepne_konta)
        
        if wybrane_konto != "Wszystkie":
            df_posiadane = df_posiadane[df_posiadane["Konto"] == wybrane_konto]
    else:
        st.sidebar.info("Brak kolumny 'Konto' w arkuszu.")

    # --- KAFELKI KPI (PODSUMOWANIE) ---
    st.subheader("📊 Podsumowanie")
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    
    with col_kpi1:
        st.metric("Liczba aktywnych pozycji", len(df_posiadane))
        
    with col_kpi2:
        if not df_posiadane.empty and kol_zwrotu in df_posiadane.columns:
            sredni_wynik = df_posiadane[kol_zwrotu].mean()
        else:
            sredni_wynik = 0.0
        st.metric("Średnia stopa zwrotu", f"{sredni_wynik:.2f}%")
        
    with col_kpi3:
        if not df_posiadane.empty and kol_zwrotu in df_posiadane.columns:
            zyskownych = len(df_posiadane[df_posiadane[kol_zwrotu] > 0])
        else:
            zyskownych = 0
        st.metric("Pozycje na plusie", f"{zyskownych} / {len(df_posiadane)}")

    st.markdown("---")

    # --- SEKCJA 1: RANKING ZAKUPÓW I REKOMENDACJE ---
    st.subheader("🏆 Ranking zakupów i Rekomendacje")
    
    if kol_roznica_proc in df_posiadane.columns:
        df_rank = df_posiadane.sort_values(kol_roznica_proc, ascending=True)
    else:
        df_rank = df_posiadane

    kolumny_gorne = ["Konto", "INSTRUMENT", "Ticker", kol_srednia, kol_aktualna, kol_roznica_proc, "Aktualna rekomendacja"]
    istniejace_kolumny_gorne = [c for c in kolumny_gorne if c in df_rank.columns]

    st.dataframe(
        df_rank[istniejace_kolumny_gorne],
        use_container_width=True,
        hide_index=True
    )

    # --- SEKCJA 2: POZYCJE DOKUP ---
    st.markdown("---")
    st.subheader("✅ Pozycje DOKUP")
    
    if "Aktualna rekomendacja" in df_posiadane.columns:
        df_posiadane["Aktualna rekomendacja"] = df_posiadane["Aktualna rekomendacja"].astype(str)
        dokup = df_posiadane[
            df_posiadane["Aktualna rekomendacja"].str.contains("DOKUP", case=False, na=False)
        ]
        if kol_roznica_proc in dokup.columns:
            dokup = dokup.sort_values(by=kol_roznica_proc, ascending=True)

        if len(dokup) > 0:
            for _, row in dokup.iterrows():
                roznica_val = row.get(kol_roznica_proc, 0)
                st.info(f"**{row['INSTRUMENT']}** ({row['Ticker']}) | Różnica: {roznica_val:.2f}%")
        else:
            st.write("Brak pozycji do dokupienia")
    else:
        st.write("Brak kolumny z rekomendacjami")

    # --- SEKCJA 3: STRUKTURA PORTFELA I UDZIAŁY ---
    st.markdown("---")
    st.subheader("📊 Struktura i Udział w Portfelu")

    if kol_udzialu in df_posiadane.columns:
        kolumny_dolne = ["Konto", "INSTRUMENT", "Ticker", kol_udzialu, kol_zwrotu]
        istniejace_kolumny_dolne = [c for c in kolumny_dolne if c in df_posiadane.columns]

        st.markdown("##### Tabela udziałów i stóp zwrotu")
        st.dataframe(
            df_posiadane[istniejace_kolumny_dolne],
            use_container_width=True,
            hide_index=True
        )

        st.markdown("##### Wykres struktury")
        df_chart = df_posiadane.copy()
        
        chart = alt.Chart(df_chart).mark_arc(innerRadius=80).encode(
            theta=alt.Theta(field=kol_udzialu, type="quantitative"),
            color=alt.Color(field="INSTRUMENT", type="nominal", legend=alt.Legend(title="Instrumenty")),
            tooltip=[
                alt.Tooltip("INSTRUMENT", title="Instrument"),
                alt.Tooltip("Ticker", title="Ticker"),
                alt.Tooltip(kol_udzialu, title="Aktualny udział"),
                alt.Tooltip(kol_zwrotu, title="Stopa zwrotu")
            ]
        ).properties(height=350)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.warning(f"Oczekiwano kolumny '{kol_udzialu}' w arkuszu.")

except Exception as e:
    st.error(f"Wystąpił błąd podczas ładowania danych: {e}")