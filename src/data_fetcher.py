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
        try:
            url = "https://api.worldbank.org/v2/country/US/indicator/NY.GDP.MKTP.CD?format=json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list) and len(data) > 1:
                for entry in data[1]:
                    if entry.get("value") is not None:
                        return float(entry["value"]) / 1e12

        except Exception as e:
            logging.error(f"Erro ao buscar PIB: {e}")

        logging.warning(f"Usando fallback de PIB: US$ {GDP_FALLBACK_TRILLIONS} T")
        return GDP_FALLBACK_TRILLIONS

    @staticmethod
    def fetch_nasdaq_pe_5y() -> pd.Series:
        """
        Calcula o P/L agregado (Market Cap Total / Lucro Líquido Total) 
        das 100 empresas do NASDAQ para os últimos 5 anos.
        """
        csv_path = "dados/nasdaq_pe_5y.csv"
        
        # 1. Regra de Cache: O usuário não precisa atualizar se o CSV for mais novo que 4 semanas (28 dias)
        if os.path.exists(csv_path):
            try:
                df_pe = pd.read_csv(csv_path, index_col=0, parse_dates=True)
                if not df_pe.empty:
                    last_date = df_pe.index[-1]
                    if (datetime.today() - last_date).days <= 28:
                        return df_pe["PE_Ratio"]
            except Exception as e:
                logging.error(f"Erro ao ler CSV do PE: {e}")

        # Se não existe ou passou de 4 semanas, avisa na tela e começa a varredura
        st.toast("Calculando lucros reais de todas as empresas do NASDAQ-100 (5 anos). Isso levará alguns minutos...", icon="🔄")
        
        try:
            # Captura a lista de tickers atualizados do NDX-100 via Wikipedia
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
            # Fallback seguro com as Big Techs caso o scraping da wiki falhe
            tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "AVGO", "PEP", "COST", "CSCO", "ADBE"]

        end_date = datetime.today()
        start_date = end_date - timedelta(days=5*365)
        
        # Baixa os preços de todas as empresas de uma vez (Otimização de rede)
        df_prices = yf.download(tickers, start=start_date, end=end_date, progress=False)["Close"]
        
        total_mcap = pd.Series(0.0, index=df_prices.index)
        total_earnings = pd.Series(0.0, index=df_prices.index)
        
        # Itera sobre cada empresa para calcular o lucro
        for t in tickers:
            try:
                stock = yf.Ticker(t)
                info = stock.info
                shares = info.get("sharesOutstanding")
                
                if not shares or t not in df_prices.columns:
                    continue
                    
                # Capitalização da empresa (Preço * Ações em Circulação)
                mcap = df_prices[t] * shares
                total_mcap = total_mcap.add(mcap, fill_value=0)
                
                financials = stock.financials
                if not financials.empty and 'Net Income' in financials.index:
                    net_income = financials.loc['Net Income'].dropna()
                    if not net_income.empty:
                        df_ni = net_income.to_frame(name='NI')
                        df_ni.index = pd.to_datetime(df_ni.index)
                        df_ni = df_ni.sort_index()
                        
                        # Forward fill: o lucro do ano fiscal passado é usado todos os dias até sair o novo
                        daily_ni = df_ni.reindex(df_prices.index, method='ffill').bfill()
                        total_earnings = total_earnings.add(daily_ni['NI'], fill_value=0)
            except Exception:
                continue
                
        # Calcula o Price-to-Earnings agregado do Índice
        pe_ratio = total_mcap / total_earnings
        pe_ratio.name = "PE_Ratio"
        pe_ratio = pe_ratio.replace([float('inf'), float('-inf')], pd.NA).dropna()
        
        # Filtro de sanidade para excluir distorções gigantes em anos de prejuízo generalizado
        pe_ratio = pe_ratio[(pe_ratio > 0) & (pe_ratio < 200)]
        
        # Salva o arquivo CSV atualizado
        os.makedirs("dados", exist_ok=True)
        pe_ratio.to_csv(csv_path)
        
        return pe_ratio

    @st.cache_data(ttl=3600, persist="disk")
    def fetch_tech_stocks_data() -> pd.DataFrame:
        try:
            data = yf.download(TECH_TICKERS, period="3y", progress=False)
            if not data.empty:
                if isinstance(data.columns, pd.MultiIndex):
                    df_close = data["Close"]
                else:
                    df_close = data
                return df_close.ffill().dropna()
        except Exception as e:
            logging.error(f"Erro ao buscar ações tech: {e}")
            
        return pd.DataFrame()