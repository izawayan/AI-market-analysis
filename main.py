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

    st.markdown("### 📊 Market Insights & AI Tracker")
    st.divider()

    UIBuilder.build_kpi_cards(df_indices, gdp_trillions)
    st.divider()

    UIBuilder.render_main_chart(df_indices, gdp_trillions)


if __name__ == "__main__":
    main()
