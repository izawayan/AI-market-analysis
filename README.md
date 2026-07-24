# 📊 Market Insights & AI Tracker

Dashboard interativo que correlaciona a evolução dos principais índices de mercado americanos com marcos de lançamento de modelos de Inteligência Artificial.

## 🚀 Funcionalidades

- **Índice Buffett dinâmico** por mercado (Market Cap / PIB dos EUA)
- **Gráfico interativo** com Plotly mostrando evolução dos índices nos últimos 12 meses
- **Marcadores de eventos de IA** plotados diretamente no gráfico (GPT, Gemini, Claude)
- **PIB atualizado** via API do Banco Mundial (com fallback de segurança)

## 🛠️ Instalação

```bash
git clone https://github.com/seu-usuario/market-ai-tracker.git
cd market-ai-tracker
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run main.py
```

## 📁 Estrutura

```
market-ai-tracker/
├── .streamlit/       # Configurações de tema
├── dados/            # CSV com eventos de IA
├── src/              # Módulos de dados e UI
├── main.py           # Orquestrador principal
└── requirements.txt
```

## 📌 Índices Monitorados

| Índice | Ticker |
|---|---|
| Wilshire 5000 | ^W5000 |
| NASDAQ Composite | ^IXIC |

## ⚙️ Configuração dos Eventos de IA

Edite o arquivo `dados/ai_features.csv` para adicionar novos lançamentos:

```csv
Date,Feature,AI_Type
2025-10-15,GPT-5,GPT
2026-02-10,Gemini 3.1,Gemini
2026-05-20,Claude Opus 4,Claude
```

---
> Dados de mercado via [Yahoo Finance](https://finance.yahoo.com/) · PIB via [World Bank API](https://data.worldbank.org/)
