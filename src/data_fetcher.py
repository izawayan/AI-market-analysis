import logging
import requests
import pandas as pd
import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta

# ==========================================
# CONFIGURAÇÃO
# ==========================================
TICKERS = {
    "Wilshire 5000": "^W5000",
    "NASDAQ Composite": "^IXIC"
}

# Fatores multiplicadores ilustrativos para estimar Market Cap (em Trilhões de USD)
MARKET_CAP_MULTIPLIERS = {
    "Wilshire 5000": 1.15 / 1000,
    "NASDAQ Composite": 1.55 / 1000
}

GDP_FALLBACK_TRILLIONS = 27.36  # PIB aprox. EUA 2023 em trilhões


class DataFetcher:
    """Responsável por extrair dados de APIs externas."""

    @st.cache_data(ttl=3600, persist="disk")
    def fetch_indices_last_12m() -> pd.DataFrame:
        end_date = datetime.today()
        start_date = end_date - timedelta(days=365)

        df_list = []
        for name, ticker in TICKERS.items():
            try:
                data = yf.download(ticker, start=start_date, end=end_date, progress=False)
                if not data.empty:
                    if isinstance(data.columns, pd.MultiIndex):
                        close_series = data["Close"].iloc[:, 0]
                    else:
                        close_series = data["Close"]

                    mcap_series = close_series * MARKET_CAP_MULTIPLIERS[name]
                    df_list.append(pd.Series(mcap_series, name=name))
                else:
                    logging.warning(f"Sem dados para {ticker}")
            except Exception as e:
                logging.error(f"Erro ao buscar {ticker}: {e}")

        if df_list:
            df = pd.concat(df_list, axis=1)
            return df.ffill().dropna()

        return pd.DataFrame()

    @st.cache_data(ttl=86400, persist="disk")
    def fetch_latest_us_gdp() -> float:
        """Busca o PIB mais recente dos EUA via World Bank API. Retorna em Trilhões de USD."""
        try:
            url = "https://api.worldbank.org/v2/country/US/indicator/NY.GDP.MKTP.CD?format=json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            for entry in data[1]:
                if entry["value"] is not None:
                    return float(entry["value"]) / 1e12

        except Exception as e:
            logging.error(f"Erro ao buscar PIB: {e}")

        logging.warning(f"Usando fallback de PIB: US$ {GDP_FALLBACK_TRILLIONS} T")
        return GDP_FALLBACK_TRILLIONS
