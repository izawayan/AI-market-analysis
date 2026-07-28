import os
import numpy as np
import pandas as pd

def carregar_parametros(csv_path=None):
    """
    Lê o arquivo de configuração com distribuições triangulares.
    Se csv_path não for fornecido, procura em '../dados/constantes_gestor.csv'
    relativo à localização deste script.
    """
    if csv_path is None:
        # Obtém o diretório onde este arquivo (monte_carlo.py) está → src/
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Sobe um nível (raiz do projeto) e entra em dados/
        csv_path = os.path.join(base_dir, '..', 'dados', 'constantes_gestor.csv')
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"Arquivo '{csv_path}' não encontrado.\n"
            "Certifique-se de que o arquivo constantes_gestor.csv está na pasta 'dados'."
        )
    
    df = pd.read_csv(csv_path)
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

    # Parâmetros fixos do modelo
    receita_inicial = 1000.0          # milhões (ex.: $1bi)
    margem_fcl = 0.15                 # FCL como % da receita
    anos_projecao = 5

    # Geração dos parâmetros estocásticos
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