# scripts/update_data.py
import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data_fetcher import DataFetcher

def main():
    print("🔄 Iniciando atualização diária dos dados dinâmicos...")
    
    # 1. Índices (Wilshire 5000 e NASDAQ) - 5 anos
    print("📊 Atualizando indices.csv...")
    DataFetcher.fetch_indices_data()
    
    # 2. PIB dos EUA (último valor)
    print("📊 Atualizando macro.csv...")
    DataFetcher.fetch_macro_data()
    
    # 3. NASDAQ P/E (5 anos)
    print("📊 Atualizando nasdaq_pe.csv...")
    DataFetcher.fetch_nasdaq_pe_5y()
    
    # Nota: ai_features.csv NÃO é atualizado automaticamente (dado estático)
    
    print("✅ Todos os dados dinâmicos atualizados com sucesso!")

if __name__ == "__main__":
    main()