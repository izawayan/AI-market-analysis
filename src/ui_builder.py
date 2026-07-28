import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go


class UIBuilder:

    @staticmethod
    def injetar_css_customizado() -> None:
        st.markdown(
            """
            <style>
                #MainMenu {visibility: hidden;}
                header {visibility: hidden;}
                footer {visibility: hidden;}
                .block-container {
                    padding-top: 2rem !important;
                    padding-bottom: 2rem !important;
                    max-width: 1200px;
                }
                div[data-testid="metric-container"] {
                    background-color: #1E1E1E;
                    border-radius: 8px;
                    padding: 15px 20px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                    border-left: 4px solid #FF4B4B;
                }
                div[data-testid="metric-container"] label {
                    color: #A0A0A0 !important;
                    font-weight: 600;
                    font-size: 0.9rem;
                }
                div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
                    color: #FAFAFA !important;
                    font-size: 1.8rem;
                    font-weight: bold;
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
                    border-radius: 6px !important;
                    padding: 6px 16px;
                    margin: 0;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }
                div[role="radiogroup"] label[data-baseweb="radio"] p {
                    color: #7B828A;
                    font-weight: 600;
                    font-size: 0.90rem;
                    margin: 0;
                }
                div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) {
                    background-color: #212E48 !important;
                    border: 1px solid #3361A6 !important;
                }
                div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) p {
                    color: #AECBFA !important;
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

            pp_color = "#FF4B4B" if deviation_pp > 0 else "#A0A0A0"
            pp_arrow = "▲" if deviation_pp > 0 else "▼"

            with cols[i]:
                st.metric(
                    label=column,
                    value=f"{buffett_indicator:.1f}%",
                    delta=f"{deviation_pp:+.1f}pp vs {FAIR_VALUE_LIMIT:.0f}%",
                    delta_color="inverse"
                )
                st.markdown(
                    f'<div style="font-size:0.78rem;color:#A0A0A0;margin-top:-10px;padding-bottom:6px">'
                    f'<span style="font-family:monospace">'
                    f'${latest_mcap:.2f}T ÷ ${gdp_trillions:.2f}T = {buffett_indicator:.1f}%'
                    f'</span>'
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
                    font-size: 0.85rem;
                    background-color: #1E1E1E;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.2);
                }
                .buffett-table th, .buffett-table td {
                    border: 1px solid #333;
                    padding: 10px;
                }
                .buffett-table th {
                    background-color: #2B2B2B;
                    color: #A0A0A0;
                    font-weight: 600;
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
        """Renderiza o gráfico e as métricas do P/L (Price/Earnings) Agregado Real."""
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
            line=dict(width=2, color="#00BFFF"),
            fill="tozeroy",
            fillcolor="rgba(0, 191, 255, 0.1)"
        ))

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="",
            yaxis_title="Índice P/L",
            hovermode="x unified",
            margin=dict(l=20, r=20, t=40, b=20),
            height=350
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

        index_colors = ["#FF4B4B", "#00BFFF", "#A0A0A0"]
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
            color_map = {"Claude": "#FFA500", "Gemini": "#0088FF", "GPT": "#E0E0E0"}

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
                    font=dict(color=marker_color, size=11), bgcolor="rgba(14,17,23,0.6)", borderpad=3
                ))

        fig.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            title="Evolução de Mercado (Trilhões USD) vs Eventos de Inteligência Artificial",
            xaxis_title="", yaxis_title="Trilhões de Dólares (US$)", hovermode="x unified",
            annotations=annotations,
            legend=dict(orientation="v", xanchor="right", x=-0.02, yanchor="middle", y=0.5, bgcolor="rgba(30,30,30,0.85)", bordercolor="rgba(255,255,255,0.1)", borderwidth=1, font=dict(size=11)),
            margin=dict(l=20, r=20, t=60, b=0)
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
        color_map_stocks = {"NVDA": "#76B900", "MSFT": "#00A4EF", "GOOGL": "#F4B400"}
        dias_map = {"1W": 7, "3W": 21, "6W": 42}

        for _, row in eventos_recentes.iterrows():
            col1, col2 = st.columns([0.6, 11.4])
            
            with col1:
                st.markdown(
                    f"""
                    <div style="width:40px; height:40px; background-color:#1E1E1E; border-radius:8px; display:flex; align-items:center; justify-content:center; color:#A0A0A0; font-size:10px; font-weight:bold; border: 1px solid #444; margin-top:20px;">
                        IMG<br>{row['AI_Type'][:3].upper()}
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
            with col2:
                head_col_left, head_col_right = st.columns([0.7, 0.3])
                
                with head_col_left:
                    st.markdown(f"**{row['Feature']}** <span style='color:#888; font-size: 0.9em'>· {row['Date'].strftime('%d/%m/%Y')}</span>", unsafe_allow_html=True)
                
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
                    st.markdown("<hr style='margin: 10px 0; border-color: #333;'>", unsafe_allow_html=True)
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
                        x=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("<hr style='margin: 5px 0 15px 0; border-color: #333;'>", unsafe_allow_html=True)