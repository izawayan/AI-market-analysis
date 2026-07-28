import logging
import streamlit as st
from src.data_fetcher import DataFetcher
from src.ui_builder import UIBuilder

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def main():
    st.set_page_config(
        page_title="Market Insights & AI Tracker",
        page_icon="📈",
        layout="wide"
    )

    UIBuilder.injetar_css_customizado()

    with st.spinner("Buscando dados de mercado e indicadores macroeconômicos..."):
        df_indices = DataFetcher.fetch_indices_last_12m()
        gdp_trillions = DataFetcher.fetch_latest_us_gdp()
        # Nova busca: P/L Real de 5 anos do NASDAQ-100
        df_pe = DataFetcher.fetch_nasdaq_pe_5y()
        df_tech = DataFetcher.fetch_tech_stocks_data()

    st.markdown("### 📊 Market Insights & AI Tracker")
    st.divider()

    UIBuilder.build_kpi_cards(df_indices, gdp_trillions)
    
    # Nova Seção do P/L (Price/Earnings)
    UIBuilder.render_pe_section(df_pe)

    st.divider()

    UIBuilder.render_main_chart(df_indices, gdp_trillions)
    
    st.divider()
    
    UIBuilder.render_llm_impact_section(df_tech)


if __name__ == "__main__":
    main()