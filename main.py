import logging
import streamlit as st
from src.data_fetcher import DataFetcher
from src.ui_builder import UIBuilder

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def main():
    st.set_page_config(
        page_title="AI Analysis",
        page_icon="📈",
        layout="wide"
    )

    UIBuilder.injetar_css_customizado()

    with st.spinner("Buscando dados de mercado e indicadores macroeconômicos..."):
        df_indices = DataFetcher.fetch_indices_data()
        gdp_trillions = DataFetcher.fetch_macro_data()["us_gdp_trillions"].iloc[0]
        df_pe = DataFetcher.fetch_nasdaq_pe_5y()
        df_tech = DataFetcher.fetch_tech_stocks_data()

    # Carrega eventos de IA agrupados (já estruturados)
    ai_events = DataFetcher.get_grouped_ai_events()

    st.markdown("### 📊 Market Insights & AI Tracker")
    st.divider()

    UIBuilder.build_kpi_cards(df_indices, gdp_trillions)
    UIBuilder.render_pe_section(df_pe)

    st.divider()

    UIBuilder.render_main_chart(df_indices, gdp_trillions)
    
    st.divider()
    
    # Passa os eventos agrupados para a UI
    UIBuilder.render_llm_impact_section(df_tech, ai_events)

    # NOVA SEÇÃO DE MONTE CARLO
    st.divider()
    UIBuilder.render_monte_carlo_section()

if __name__ == "__main__":
    main()