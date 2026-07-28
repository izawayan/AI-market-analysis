# scripts/update_data.py
import pandas as pd
import yfinance as yf  # exemplo: baixar ações
import os
from datetime import datetime

def main():
    print("🔄 Iniciando atualização dos dados...")
    
    # Exemplo: baixar dados de um ativo (ex: PETR4.SA)
    ticker = "PETR4.SA"
    df = yf.download(ticker, period="1y", interval="1d")
    df.to_csv("dados/petr4_daily.csv")
    
    # Exemplo: Atualizar indicadores macro (IPCA, SELIC, etc.)
    # Aqui você colocaria sua lógica de scraping ou API
    dados_macro = {
        "data": [datetime.now().strftime("%Y-%m-%d")],
        "selic": 0.1075,  # mock
        "ipca": 0.0423
    }
    pd.DataFrame(dados_macro).to_csv("dados/macro.csv", index=False)
    
    print("✅ Dados atualizados com sucesso!")

if __name__ == "__main__":
    main()