import os
import numpy as np
import streamlit as st
import pandas as pd
import plotly.graph_objects as go


class UIBuilder:

    @staticmethod
    def injetar_css_customizado() -> None:
        st.markdown(
            """
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

                html, body, [class*="css"] {
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }

                #MainMenu {visibility: hidden;}
                header {visibility: hidden;}
                footer {visibility: hidden;}

                .block-container {
                    padding-top: 2rem !important;
                    padding-bottom: 2rem !important;
                    max-width: 1200px;
                }

                .stApp {
                    background-color: #0a0a0a;
                }

                div[data-testid="metric-container"] {
                    background-color: #141414;
                    border-radius: 4px;
                    padding: 15px 20px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.4);
                    border-left: 4px solid #f97316;
                }
                div[data-testid="metric-container"] label {
                    color: #A0A0A0 !important;
                    font-weight: 600;
                    font-size: 0.8rem;
                    text-transform: uppercase;
                    letter-spacing: 0.08em;
                }
                div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
                    color: #FAFAFA !important;
                    font-size: 1.8rem;
                    font-weight: 700;
                }

                div[data-testid="stRadio"] > div {
                    display: flex;
                    flex-direction: row;
                    gap: 8px;
                    background-color: transparent;
                }
                div[role="radiogroup"] label[data-baseweb="radio"] div:first-child {
                    display: none !important;
                }
                div[role="radiogroup"] label[data-baseweb="radio"] {
                    background-color: #1A1C20;
                    border: 1px solid #2B2E33;
                    border-radius: 4px !important;
                    padding: 6px 16px;
                    margin: 0;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }
                div[role="radiogroup"] label[data-baseweb="radio"] p {
                    color: #7B828A;
                    font-weight: 600;
                    font-size: 0.8rem;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    margin: 0;
                }
                div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) {
                    background-color: rgba(249,115,22,0.15) !important;
                    border: 1px solid #f97316 !important;
                }
                div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) p {
                    color: #f97316 !important;
                }

                h1, h2, h3, h4, h5, h6 {
                    font-family: 'Inter', sans-serif;
                    font-weight: 600;
                    letter-spacing: -0.02em;
                }
                .stMarkdown p, .stMarkdown span, .stMarkdown div {
                    font-family: 'Inter', sans-serif;
                }
                .stCaption {
                    color: #A0A0A0 !important;
                    font-size: 0.8rem;
                }
            </style>
            """,
            unsafe_allow_html=True
        )

    @staticmethod
    def build_kpi_cards(df_indices: pd.DataFrame, gdp_trillions: float) -> None:
        if df_indices.empty:
            st.warning("⚠️ Dados dos índices indisponíveis. Verifique sua conexão e tente novamente.")
            return

        FAIR_VALUE_LIMIT = 110.0

        st.subheader("Índice Buffett por Mercado (Market Cap / PIB)")
        st.caption(
            f"PIB dos EUA estimado em **US$ {gdp_trillions:.2f} T** · "
            f"Referência de preço justo: **{FAIR_VALUE_LIMIT:.0f}%** (Preço Justo + 1σ)"
        )

        cols = st.columns(len(df_indices.columns))
        for i, column in enumerate(df_indices.columns):
            latest_mcap = df_indices[column].iloc[-1]
            buffett_indicator = (latest_mcap / gdp_trillions) * 100
            deviation_pp = buffett_indicator - FAIR_VALUE_LIMIT

            pp_color = "#f97316" if deviation_pp > 0 else "#A0A0A0"
            pp_arrow = "▲" if deviation_pp > 0 else "▼"

            with cols[i]:
                st.metric(
                    label=column,
                    value=f"{buffett_indicator:.1f}%",
                    delta=f"{deviation_pp:+.1f}pp vs {FAIR_VALUE_LIMIT:.0f}%",
                    delta_color="inverse"
                )
                st.markdown(
                    f'<div style="font-size:0.75rem;color:#A0A0A0;margin-top:-10px;padding-bottom:6px;font-family:monospace;">'
                    f'${latest_mcap:.2f}T ÷ ${gdp_trillions:.2f}T = {buffett_indicator:.1f}%'
                    f'&nbsp;&nbsp;'
                    f'<span style="color:{pp_color};font-weight:bold">'
                    f'{deviation_pp:+.1f}pp {pp_arrow}'
                    f'</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        st.markdown(
            """
            <style>
                .buffett-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 25px;
                    margin-bottom: 25px;
                    text-align: center;
                    font-size: 0.75rem;
                    background-color: #141414;
                    border-radius: 4px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                }
                .buffett-table th, .buffett-table td {
                    border: 1px solid #2B2E33;
                    padding: 10px;
                }
                .buffett-table th {
                    background-color: #1A1C20;
                    color: #A0A0A0;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }
                .buffett-table td {
                    color: #FAFAFA;
                }
            </style>
            <table class="buffett-table">
                <tr>
                    <th>Abaixo de 70%</th>
                    <th>De 75% a 90%</th>
                    <th>De 90% a 115%</th>
                    <th>De 115% a 150%</th>
                    <th>Acima de 150%</th>
                </tr>
                <tr>
                    <td>Mercado significativamente subavaliado (Barato)</td>
                    <td>Mercado levemente subavaliado</td>
                    <td>Preço justo</td>
                    <td>Mercado superavaliado (Caro)</td>
                    <td>Território de Bolha (Risco severo de correção)</td>
                </tr>
            </table>
            """,
            unsafe_allow_html=True
        )

    @staticmethod
    def render_pe_section(df_pe: pd.Series) -> None:
        if df_pe is None or df_pe.empty:
            st.warning("⚠️ Dados do P/L do NASDAQ-100 indisponíveis no momento.")
            return

        st.subheader("P/L Agregado Histórico (5 Anos) - NASDAQ-100")
        st.caption("Cálculo fundamentalista das empresas do índice, mapeando o lucro líquido real reportado vs. capitalização.")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_pe.index,
            y=df_pe.values,
            mode="lines",
            name="P/L Ratio",
            line=dict(width=2, color="#f97316"),
            fill="tozeroy",
            fillcolor="rgba(249, 115, 22, 0.1)"
        ))

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="",
            yaxis_title="Índice P/L",
            hovermode="x unified",
            margin=dict(l=20, r=20, t=40, b=20),
            height=350,
            font=dict(family="Inter, sans-serif")
        )

        st.plotly_chart(fig, use_container_width=True)

        mean_val = df_pe.mean()
        median_val = df_pe.median()
        min_val = df_pe.min()
        max_val = df_pe.max()

        cols = st.columns(4)
        cols[0].metric(label="Mean (Média)", value=f"{mean_val:.2f}")
        cols[1].metric(label="Median (Mediana)", value=f"{median_val:.2f}")
        cols[2].metric(label="Min (Mínimo)", value=f"{min_val:.2f}")
        cols[3].metric(label="Max (Máximo)", value=f"{max_val:.2f}")

    @staticmethod
    def render_main_chart(df_indices: pd.DataFrame, gdp_trillions: float) -> None:
        if df_indices.empty:
            st.error("❌ Não foi possível carregar os dados dos índices de mercado.")
            return

        fig = go.Figure()

        index_colors = ["#f97316", "#00BFFF", "#A0A0A0"]
        for i, column in enumerate(df_indices.columns):
            fig.add_trace(go.Scatter(
                x=df_indices.index,
                y=df_indices[column],
                mode="lines",
                name=f"{column} (M. Cap)",
                line=dict(width=2, color=index_colors[i % len(index_colors)]),
                legendgroup="indices",
                showlegend=True
            ))

        fig.add_trace(go.Scatter(
            x=[df_indices.index[0], df_indices.index[-1]],
            y=[gdp_trillions, gdp_trillions],
            mode="lines",
            name="PIB EUA (Referência)",
            line=dict(width=3, dash="dot", color="#A0A0A0"),
            legendgroup="indices",
            showlegend=True
        ))

        csv_path = "dados/ai_features.csv"
        annotations = []
        if os.path.exists(csv_path):
            df_ai = pd.read_csv(csv_path, parse_dates=["Date"])
            color_map = {"Claude": "#f97316", "Gemini": "#0088FF", "GPT": "#E0E0E0"}

            for _, row in df_ai.iterrows():
                if row["Date"] < df_indices.index[0] or row["Date"] > df_indices.index[-1]:
                    continue

                anchor_y = gdp_trillions
                if "Wilshire 5000" in df_indices.columns:
                    closest_idx = df_indices.index.get_indexer([row["Date"]], method="nearest")[0]
                    anchor_y = df_indices["Wilshire 5000"].iloc[closest_idx]

                marker_color = color_map.get(row["AI_Type"], "#FFFFFF")

                fig.add_trace(go.Scatter(
                    x=[row["Date"]], y=[anchor_y], mode="markers",
                    name=f"{row['Feature']}", showlegend=False,
                    marker=dict(size=50, symbol="circle", color="rgba(0,0,0,0)", line=dict(color=marker_color, width=2)),
                    hovertemplate=f"<b>{row['Feature']}</b><br>Tipo: {row['AI_Type']}<br>Data: {row['Date'].strftime('%d/%m/%Y')}<extra></extra>"
                ))

                annotations.append(dict(
                    x=row["Date"], y=anchor_y, text=f"  🚀 <b>{row['Feature']}</b>",
                    showarrow=False, xanchor="left", yanchor="middle",
                    font=dict(color=marker_color, size=11, family="Inter, sans-serif"),
                    bgcolor="rgba(14,17,23,0.6)", borderpad=3
                ))

        fig.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            title="Evolução de Mercado (Trilhões USD) vs Eventos de Inteligência Artificial",
            xaxis_title="", yaxis_title="Trilhões de Dólares (US$)", hovermode="x unified",
            annotations=annotations,
            legend=dict(orientation="v", xanchor="right", x=-0.02, yanchor="middle", y=0.5, bgcolor="rgba(20,20,20,0.9)", bordercolor="rgba(255,255,255,0.1)", borderwidth=1, font=dict(size=11, family="Inter, sans-serif")),
            margin=dict(l=20, r=20, t=60, b=0),
            font=dict(family="Inter, sans-serif")
        )

        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def render_llm_impact_section(df_tech: pd.DataFrame) -> None:
        if df_tech.empty:
            st.warning("⚠️ Dados das Big Techs indisponíveis para análise.")
            return

        st.subheader("Impacto Pós-Release nas Big Techs")
        st.caption("Análise de volatilidade e performance acumulada para NVDA, MSFT e GOOGL pós-lançamentos de LLMs.")

        csv_path = "dados/ai_features.csv"
        if not os.path.exists(csv_path):
            st.info("Arquivo de eventos (ai_features.csv) não encontrado.")
            return

        df_ai = pd.read_csv(csv_path, parse_dates=["Date"])

        df_ai_sorted = df_ai.sort_values("Date", ascending=False)
        eventos_recentes = df_ai_sorted.drop_duplicates(subset=["AI_Type"]).head(3)

        if eventos_recentes.empty:
            st.info("Nenhum evento de IA registrado no CSV para analisar.")
            return

        st.markdown("<br>", unsafe_allow_html=True)
        color_map_stocks = {"NVDA": "#76B900", "MSFT": "#00A4EF", "GOOGL": "#f97316"}
        dias_map = {"1W": 7, "3W": 21, "6W": 42}

        for _, row in eventos_recentes.iterrows():
            col1, col2 = st.columns([0.6, 11.4])

            with col1:
                st.markdown(
                    f"""
                    <div style="width:40px; height:40px; background-color:#141414; border-radius:4px; display:flex; align-items:center; justify-content:center; color:#A0A0A0; font-size:9px; font-weight:bold; border: 1px solid #2B2E33; margin-top:20px; font-family:monospace; text-transform:uppercase;">
                        {row['AI_Type'][:3]}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:
                head_col_left, head_col_right = st.columns([0.7, 0.3])

                with head_col_left:
                    st.markdown(f"**{row['Feature']}** <span style='color:#A0A0A0; font-size: 0.85em'>· {row['Date'].strftime('%d/%m/%Y')}</span>", unsafe_allow_html=True)

                with head_col_right:
                    tempo_selecionado = st.radio(
                        f"Janela_{row['Feature']}",
                        options=["1W", "3W", "6W"],
                        horizontal=True,
                        label_visibility="collapsed",
                        key=f"radio_{row['Feature']}"
                    )

                dias_janela = dias_map[tempo_selecionado]
                start_date = row['Date']
                end_date = start_date + pd.Timedelta(days=dias_janela)

                mask = (df_tech.index >= start_date) & (df_tech.index <= end_date)
                df_period = df_tech.loc[mask]

                if df_period.empty:
                    st.caption("Sem dados de mercado (futuro ou feriado) para este período.")
                    st.markdown("<hr style='margin: 10px 0; border-color: #2B2E33;'>", unsafe_allow_html=True)
                    continue

                df_normalized = (df_period / df_period.iloc[0] - 1) * 100

                fig = go.Figure()
                for ticker in df_normalized.columns:
                    if ticker in color_map_stocks:
                        fig.add_trace(go.Scatter(
                            x=df_normalized.index,
                            y=df_normalized[ticker],
                            mode="lines",
                            name=ticker,
                            line=dict(width=2, color=color_map_stocks[ticker])
                        ))

                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis_title="",
                    yaxis_title="Variação (%)",
                    hovermode="x unified",
                    margin=dict(l=10, r=20, t=10, b=10),
                    height=180,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1,
                        font=dict(family="Inter, sans-serif")
                    ),
                    font=dict(family="Inter, sans-serif")
                )

                st.plotly_chart(fig, use_container_width=True)
                st.markdown("<hr style='margin: 5px 0 15px 0; border-color: #2B2E33;'>", unsafe_allow_html=True)

    # ---------- SEÇÃO DE MONTE CARLO ----------
    @staticmethod
    def render_monte_carlo_section() -> None:
        from src.monte_carlo import carregar_parametros, executar_monte_carlo

        st.header("🎲 Simulação de Monte Carlo – Valuation DCF")
        st.caption("Análise de sensibilidade do valor intrínseco com base nas premissas do gestor.")

        # Carrega parâmetros (caminho absoluto automático)
        try:
            params = carregar_parametros()
        except FileNotFoundError as e:
            st.error(str(e))
            return

        # Barra lateral: controles
        st.sidebar.header("⚙️ Configurações da Simulação")

        st.sidebar.markdown(
            """
            **🔒 Congruência dos Resultados**  
            Para garantir a reprodutibilidade e congruência dos resultados, 
            foi definida uma **semente (seed) padrão = 7** para o gerador 
            de números aleatórios.
            """
        )

        excluir_seed = st.sidebar.checkbox(
            "❌ Excluir seed padrão (resultados aleatórios)",
            value=False,
            help="Marque esta opção para gerar números verdadeiramente aleatórios a cada execução. Útil para testes de sensibilidade, mas os resultados não serão reproduzíveis."
        )

        seed_atual = None if excluir_seed else 7

        if seed_atual is not None:
            st.sidebar.success(f"✅ Usando seed fixa: **{seed_atual}**")
        else:
            st.sidebar.warning("⚠️ Modo aleatório ativado. Os resultados variarão a cada execução.")

        st.sidebar.divider()

        n_base = st.sidebar.slider(
            "Nº de Simulações (Base - Gestor)",
            min_value=1000,
            max_value=100000,
            value=10000,
            step=1000,
            help="Número de iterações para a simulação base. Quanto maior, mais preciso, porém mais lento."
        )

        n_persp = st.sidebar.slider(
            "Nº de Simulações (Sua Perspectiva)",
            min_value=1000,
            max_value=100000,
            value=10000,
            step=1000,
            help="Número de iterações para a simulação personalizada. Pode ser diferente do slider da base."
        )

        st.sidebar.divider()

        st.sidebar.header("✏️ Crie sua Própria Perspectiva")
        wacc_user = st.sidebar.number_input("WACC (%)", min_value=0.0, max_value=0.5, value=0.16, step=0.01, format="%.2f")
        g_user = st.sidebar.number_input("Crescimento Perpétuo (g) (%)", min_value=0.0, max_value=0.1, value=0.04, step=0.005, format="%.3f")

        if st.sidebar.button("🚀 Aplicar Perspectiva", use_container_width=True):
            result_persp = executar_monte_carlo(
                params,
                n_simulacoes=n_persp,
                seed=seed_atual,
                modo='personalizado',
                wacc_fixo=wacc_user,
                g_fixo=g_user
            )
            st.session_state['result_persp'] = result_persp
            st.session_state['n_persp'] = n_persp

        @st.cache_data
        def simular_base(n_sim, seed):
            return executar_monte_carlo(params, n_simulacoes=n_sim, seed=seed, modo='base')

        result_base = simular_base(n_base, seed_atual)
        st.session_state['n_base'] = n_base
        st.session_state['result_base'] = result_base

        st.subheader("📊 Comparação de Cenários")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"#### Base (Gestor) – {n_base} simulações")
            if seed_atual is not None:
                st.caption(f"🔒 Seed fixa: {seed_atual}")
            else:
                st.caption("🎲 Resultados aleatórios")
            UIBuilder._plot_histograma(result_base['dados'], cor="#f97316")
            st.metric("Mediana", f"R$ {result_base['mediana']:.2f}M")
            st.caption(f"P5: R$ {result_base['p5']:.2f}M | P95: R$ {result_base['p95']:.2f}M")

        with col2:
            if 'result_persp' in st.session_state:
                st.markdown(f"#### Sua Perspectiva – {st.session_state['n_persp']} simulações")
                if seed_atual is not None:
                    st.caption(f"🔒 Seed fixa: {seed_atual}")
                else:
                    st.caption("🎲 Resultados aleatórios")
                UIBuilder._plot_histograma(st.session_state['result_persp']['dados'], cor="#00BFFF")
                st.metric("Mediana", f"R$ {st.session_state['result_persp']['mediana']:.2f}M")
                st.caption(f"P5: R$ {st.session_state['result_persp']['p5']:.2f}M | P95: R$ {st.session_state['result_persp']['p95']:.2f}M")
            else:
                st.info("Clique em 'Aplicar Perspectiva' para comparar.")

        st.divider()
        st.subheader("📋 Resumo Estatístico")
        if 'result_persp' in st.session_state:
            df_compare = pd.DataFrame({
                "Cenário": ["Base (Gestor)", "Sua Perspectiva"],
                "Nº Simulações": [n_base, st.session_state['n_persp']],
                "Seed": [
                    seed_atual if seed_atual is not None else "Aleatória",
                    seed_atual if seed_atual is not None else "Aleatória"
                ],
                "P5 (R$ M)": [f"{result_base['p5']:.2f}", f"{st.session_state['result_persp']['p5']:.2f}"],
                "Mediana (R$ M)": [f"{result_base['mediana']:.2f}", f"{st.session_state['result_persp']['mediana']:.2f}"],
                "P95 (R$ M)": [f"{result_base['p95']:.2f}", f"{st.session_state['result_persp']['p95']:.2f}"]
            })
            st.dataframe(df_compare, use_container_width=True)
        else:
            st.info("Aplique uma perspectiva para ver a comparação detalhada.")

    @staticmethod
    def _plot_histograma(dados, cor="#f97316"):
        p5 = np.percentile(dados, 5)
        p50 = np.median(dados)
        p95 = np.percentile(dados, 95)

        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=dados,
            nbinsx=50,
            marker_color=cor,
            opacity=0.7,
            name="Valuation"
        ))
        for p, nome in zip([p5, p50, p95], ["P5", "P50", "P95"]):
            fig.add_vline(x=p, line_dash="dash", line_color="white",
                          annotation_text=f"{nome}: {p:.1f}",
                          annotation_position="top")
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Valuation (R$ Milhões)",
            yaxis_title="Frequência",
            showlegend=False,
            margin=dict(l=10, r=20, t=20, b=10),
            height=300,
            font=dict(family="Inter, sans-serif")
        )
        st.plotly_chart(fig, use_container_width=True)