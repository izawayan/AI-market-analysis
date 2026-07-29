import os
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

TECH_TICKERS = ["NVDA", "MSFT", "GOOGL"]

MARKET_CAP_MULTIPLIERS = {
    "Wilshire 5000": 1.15 / 1000,
    "NASDAQ Composite": 1.55 / 1000
}

GDP_FALLBACK_TRILLIONS = 27.36


class DataFetcher:

    # --------------------------------------------------------------
    # 1. ÍNDICES (Wilshire 5000 e NASDAQ) - Últimos 5 anos
    # --------------------------------------------------------------
    @staticmethod
    def fetch_indices_data() -> pd.DataFrame:
        """
        Baixa os dados de Wilshire 5000 e NASDAQ Composite dos últimos 5 anos.
        Salva em 'dados/indices.csv'.
        """
        end_date = datetime.today()
        start_date = end_date - timedelta(days=5*365)

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
            df = df.ffill().dropna()
            os.makedirs("dados", exist_ok=True)
            df.to_csv("dados/indices.csv")
            logging.info("indices.csv atualizado com sucesso!")
            return df

        logging.warning("Falha ao atualizar índices. Retornando DataFrame vazio.")
        return pd.DataFrame()

    # --------------------------------------------------------------
    # 2. PIB dos EUA (último valor disponível)
    # --------------------------------------------------------------
    @staticmethod
    def fetch_macro_data() -> pd.DataFrame:
        """
        Busca o PIB dos EUA mais recente (World Bank API) e salva em 'dados/macro.csv'.
        Retorna um DataFrame com data e valor (em trilhões).
        """
        try:
            url = "https://api.worldbank.org/v2/country/US/indicator/NY.GDP.MKTP.CD?format=json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            gdp_trillions = None
            if isinstance(data, list) and len(data) > 1:
                for entry in data[1]:
                    if entry.get("value") is not None:
                        gdp_trillions = float(entry["value"]) / 1e12
                        break

            if gdp_trillions is None:
                logging.warning("Nenhum valor de PIB encontrado. Usando fallback.")
                gdp_trillions = GDP_FALLBACK_TRILLIONS

        except Exception as e:
            logging.error(f"Erro ao buscar PIB: {e}")
            gdp_trillions = GDP_FALLBACK_TRILLIONS
            logging.warning(f"Usando fallback: US$ {gdp_trillions} T")

        df = pd.DataFrame({
            "data": [datetime.today().strftime("%Y-%m-%d")],
            "us_gdp_trillions": [gdp_trillions]
        })
        os.makedirs("dados", exist_ok=True)
        df.to_csv("dados/macro.csv", index=False)
        logging.info("macro.csv atualizado com sucesso!")
        return df

    # --------------------------------------------------------------
    # 3. NASDAQ P/E (últimos 5 anos)
    # --------------------------------------------------------------
    @staticmethod
    def fetch_nasdaq_pe_5y() -> pd.Series:
        """
        Calcula o P/L agregado do NASDAQ-100 para os últimos 5 anos.
        Salva em 'dados/nasdaq_pe.csv'.
        """
        csv_path = "dados/nasdaq_pe.csv"

        if os.path.exists(csv_path):
            try:
                df_pe = pd.read_csv(csv_path, index_col=0, parse_dates=True)
                if not df_pe.empty:
                    last_date = df_pe.index[-1]
                    if (datetime.today() - last_date).days <= 1:
                        return df_pe["PE_Ratio"]
            except Exception as e:
                logging.error(f"Erro ao ler CSV do PE: {e}")

        st.toast("Calculando P/L do NASDAQ-100 (5 anos). Isso pode levar alguns minutos...", icon="🔄")
        
        try:
            tables = pd.read_html('https://en.wikipedia.org/wiki/Nasdaq-100')
            tickers = []
            for df in tables:
                if 'Ticker' in df.columns:
                    tickers = df['Ticker'].tolist()
                    break
            if not tickers:
                raise ValueError("Tabela não encontrada.")
            tickers = [str(t).replace('.', '-') for t in tickers]
        except Exception:
            tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "AVGO", "PEP", "COST", "CSCO", "ADBE"]

        end_date = datetime.today()
        start_date = end_date - timedelta(days=5*365)
        
        df_prices = yf.download(tickers, start=start_date, end=end_date, progress=False)["Close"]
        
        total_mcap = pd.Series(0.0, index=df_prices.index)
        total_earnings = pd.Series(0.0, index=df_prices.index)
        
        for t in tickers:
            try:
                stock = yf.Ticker(t)
                info = stock.info
                shares = info.get("sharesOutstanding")
                if not shares or t not in df_prices.columns:
                    continue
                mcap = df_prices[t] * shares
                total_mcap = total_mcap.add(mcap, fill_value=0)
                
                financials = stock.financials
                if not financials.empty and 'Net Income' in financials.index:
                    net_income = financials.loc['Net Income'].dropna()
                    if not net_income.empty:
                        df_ni = net_income.to_frame(name='NI')
                        df_ni.index = pd.to_datetime(df_ni.index)
                        df_ni = df_ni.sort_index()
                        daily_ni = df_ni.reindex(df_prices.index, method='ffill').bfill()
                        total_earnings = total_earnings.add(daily_ni['NI'], fill_value=0)
            except Exception:
                continue
                
        pe_ratio = total_mcap / total_earnings
        pe_ratio.name = "PE_Ratio"
        pe_ratio = pe_ratio.replace([float('inf'), float('-inf')], pd.NA).dropna()
        pe_ratio = pe_ratio[(pe_ratio > 0) & (pe_ratio < 200)]
        
        os.makedirs("dados", exist_ok=True)
        pe_ratio.to_csv(csv_path)
        logging.info("nasdaq_pe.csv atualizado com sucesso!")
        return pe_ratio

    # --------------------------------------------------------------
    # 4. AI Events - Agrupamento hierárquico
    # --------------------------------------------------------------
    @staticmethod
    def get_grouped_ai_events() -> dict:
        """
        Lê o arquivo dados/ai_features.csv e retorna um dicionário agrupado por AI_Type.
        Cada chave contém uma lista de eventos com 'feature' e 'date'.
        Se o arquivo não existir ou estiver vazio, retorna dicionário vazio.
        """
        csv_path = "dados/ai_features.csv"
        if not os.path.exists(csv_path):
            logging.warning("ai_features.csv não encontrado. Nenhum evento de IA carregado.")
            return {}

        try:
            df = pd.read_csv(csv_path, parse_dates=["Date"])
        except Exception as e:
            logging.error(f"Erro ao ler ai_features.csv: {e}")
            return {}

        if df.empty:
            return {}

        grouped = {}
        for _, row in df.iterrows():
            ai_type = row["AI_Type"]
            if ai_type not in grouped:
                grouped[ai_type] = []
            grouped[ai_type].append({
                "feature": row["Feature"],
                "date": row["Date"]
            })
        return grouped

    # --------------------------------------------------------------
    # 5. Método auxiliar para Tech Stocks (privado)
    # --------------------------------------------------------------
    @staticmethod
    def _fetch_tech_stocks_data() -> pd.DataFrame:
        try:
            data = yf.download(TECH_TICKERS, period="3y", progress=False)
            if not data.empty:
                if isinstance(data.columns, pd.MultiIndex):
                    return data["Close"].ffill().dropna()
                else:
                    return data.ffill().dropna()
        except Exception as e:
            logging.error(f"Erro ao buscar ações tech: {e}")
        return pd.DataFrame()

    # --------------------------------------------------------------
    # 6. AI Features (opcional, mantido para compatibilidade)
    # --------------------------------------------------------------
    @staticmethod
    def fetch_ai_features():
        """
        Gera um CSV com features técnicas das principais tech stocks.
        (Este método é mantido, mas não é chamado pela rotina diária).
        """
        df = DataFetcher._fetch_tech_stocks_data()
        if df.empty:
            logging.warning("Sem dados para gerar ai_features.csv")
            return pd.DataFrame()

        features = pd.DataFrame(index=df.index)
        for ticker in df.columns:
            features[f"{ticker}_Close"] = df[ticker]
        returns = df.pct_change()
        for ticker in df.columns:
            features[f"{ticker}_Return"] = returns[ticker]
            features[f"{ticker}_SMA_5"] = df[ticker].rolling(5).mean()
            features[f"{ticker}_SMA_20"] = df[ticker].rolling(20).mean()
            features[f"{ticker}_Vol_5"] = returns[ticker].rolling(5).std()
        features["Tech_Avg"] = df.mean(axis=1)
        features = features.dropna()
        
        os.makedirs("dados", exist_ok=True)
        features.to_csv("dados/ai_features.csv")
        logging.info("ai_features.csv atualizado (manual).")
        return features

    # ==============================================================
    # ALIASES PARA COMPATIBILIDADE COM O main.py
    # ==============================================================
    fetch_tech_stocks_data = _fetch_tech_stocks_data

    @staticmethod
    def fetch_latest_us_gdp() -> float:
        """
        Retorna o PIB dos EUA mais recente (em trilhões). Alias para compatibilidade.
        """
        df = DataFetcher.fetch_macro_data()
        if not df.empty:
            return df["us_gdp_trillions"].iloc[0]
        return GDP_FALLBACK_TRILLIONS