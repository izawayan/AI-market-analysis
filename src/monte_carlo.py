import os
import io
import numpy as np
import pandas as pd
import streamlit as st

def carregar_parametros(csv_path=None):
    """
    Carrega as premissas do gestor para a simulação.
    Tenta primeiro o arquivo local (desenvolvimento); se não existir,
    recorre a st.secrets["constantes_gestor"] (produção).
    """
    if csv_path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(base_dir, '..', 'dados', 'constantes_gestor.csv')

    # Tenta arquivo local (existente apenas em desenvolvimento)
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        # Modo produção: lê dos segredos do Streamlit Cloud
        try:
            secret_content = st.secrets["constantes_gestor"]
            df = pd.read_csv(io.StringIO(secret_content))
        except KeyError:
            raise FileNotFoundError(
                f"Arquivo '{csv_path}' não encontrado e segredo 'constantes_gestor' não configurado."
            )

    params = {}
    for _, row in df.iterrows():
        var = row["Variavel"].strip()
        params[var] = {
            "min": float(row["Minimo"]),
            "moda": float(row["Mais_Provavel"]),
            "max": float(row["Maximo"]),
        }
    return params


def executar_monte_carlo(params, n_simulacoes=10000, seed=7, modo='base', wacc_fixo=None, g_fixo=None):
    """
    Executa simulação de Monte Carlo para valuation DCF.
    Retorna dict com 'dados' (array de valuations), 'mediana', 'p5', 'p95'.
    """
    if seed is not None:
        np.random.seed(seed)

    receita_inicial = 1000.0          # milhões (ex.: $1bi)
    margem_fcl = 0.15                 # FCL como % da receita
    anos_projecao = 5

    if modo == 'base':
        wacc = np.random.triangular(
            params["WACC"]["min"], params["WACC"]["moda"], params["WACC"]["max"], n_simulacoes
        )
        g = np.random.triangular(
            params["Crescimento_Perpetuo"]["min"],
            params["Crescimento_Perpetuo"]["moda"],
            params["Crescimento_Perpetuo"]["max"],
            n_simulacoes
        )
    else:
        wacc = np.full(n_simulacoes, wacc_fixo)
        g = np.full(n_simulacoes, g_fixo)

    cresc_receita = np.random.triangular(
        params["Crescimento_Receita"]["min"],
        params["Crescimento_Receita"]["moda"],
        params["Crescimento_Receita"]["max"],
        n_simulacoes
    )

    valuations = np.zeros(n_simulacoes)

    for i in range(n_simulacoes):
        receitas = [receita_inicial]
        for _ in range(1, anos_projecao + 1):
            receitas.append(receitas[-1] * (1 + cresc_receita[i]))
        fcls = [r * margem_fcl for r in receitas[1:]]

        vp_fcl = sum(fcl / (1 + wacc[i]) ** (t + 1) for t, fcl in enumerate(fcls))

        if wacc[i] > g[i]:
            fcl_ano5 = fcls[-1]
            perpetuidade = fcl_ano5 * (1 + g[i]) / (wacc[i] - g[i])
            vp_perpetuidade = perpetuidade / (1 + wacc[i]) ** anos_projecao
            valuation = vp_fcl + vp_perpetuidade
            valuations[i] = valuation if valuation > 0 else np.nan
        else:
            valuations[i] = np.nan

    valuations = valuations[~np.isnan(valuations)]

    p5 = np.percentile(valuations, 5)
    mediana = np.median(valuations)
    p95 = np.percentile(valuations, 95)

    return {
        "dados": valuations,
        "mediana": mediana,
        "p5": p5,
        "p95": p95
    }