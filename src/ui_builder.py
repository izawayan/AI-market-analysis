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
            </style>
            """,
            unsafe_allow_html=True
        )

    @staticmethod
    def build_kpi_cards(df_indices: pd.DataFrame, gdp_trillions: float) -> None:
        if df_indices.empty:
            st.warning("⚠️ Dados dos índices indisponíveis. Verifique sua conexão e tente novamente.")
            return

        FAIR_VALUE_LIMIT = 110.0  # Preço Justo + 1 Sigma

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
                    delta_color="inverse"  # positivo (acima de 110%) = vermelho
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

    @staticmethod
    def render_main_chart(df_indices: pd.DataFrame, gdp_trillions: float) -> None:
        if df_indices.empty:
            st.error(
                "❌ Não foi possível carregar os dados dos índices de mercado. "
                "Verifique sua conexão com a internet ou tente novamente mais tarde."
            )
            return

        fig = go.Figure()

        # 1. Linhas dos Índices
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

        # 2. Linha de Referência do PIB
        fig.add_trace(go.Scatter(
            x=[df_indices.index[0], df_indices.index[-1]],
            y=[gdp_trillions, gdp_trillions],
            mode="lines",
            name="PIB EUA (Referência)",
            line=dict(width=3, dash="dot", color="#A0A0A0"),
            legendgroup="indices",
            showlegend=True
        ))

        # 3. Marcadores de Eventos de IA
        csv_path = "dados/ai_features.csv"
        annotations = []
        if os.path.exists(csv_path):
            df_ai = pd.read_csv(csv_path, parse_dates=["Date"])

            color_map = {
                "Claude": "#FFA500",
                "Gemini": "#0088FF",
                "GPT":    "#E0E0E0"
            }

            for _, row in df_ai.iterrows():
                if row["Date"] < df_indices.index[0] or row["Date"] > df_indices.index[-1]:
                    continue

                anchor_y = gdp_trillions
                if "Wilshire 5000" in df_indices.columns:
                    closest_idx = df_indices.index.get_indexer([row["Date"]], method="nearest")[0]
                    anchor_y = df_indices["Wilshire 5000"].iloc[closest_idx]

                marker_color = color_map.get(row["AI_Type"], "#FFFFFF")

                fig.add_trace(go.Scatter(
                    x=[row["Date"]],
                    y=[anchor_y],
                    mode="markers",
                    name=f"{row['Feature']}",
                    showlegend=False,
                    marker=dict(
                        size=50,
                        symbol="circle",
                        color="rgba(0,0,0,0)",
                        line=dict(color=marker_color, width=2)
                    ),
                    hovertemplate=(
                        f"<b>{row['Feature']}</b><br>"
                        f"Tipo: {row['AI_Type']}<br>"
                        f"Data: {row['Date'].strftime('%d/%m/%Y')}<extra></extra>"
                    )
                ))

                annotations.append(dict(
                    x=row["Date"],
                    y=anchor_y,
                    text=f"  🚀 <b>{row['Feature']}</b>",
                    showarrow=False,
                    xanchor="left",
                    yanchor="middle",
                    font=dict(color=marker_color, size=11),
                    bgcolor="rgba(14,17,23,0.6)",
                    borderpad=3
                ))

        # 4. Layout — legenda encostada na borda esquerda do gráfico
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            title="Evolução de Mercado (Trilhões USD) vs Eventos de Inteligência Artificial",
            xaxis_title="",
            yaxis_title="Trilhões de Dólares (US$)",
            hovermode="x unified",
            annotations=annotations,
            legend=dict(
                orientation="v",
                xanchor="right",
                x=-0.02,
                yanchor="middle",
                y=0.5,
                bgcolor="rgba(30,30,30,0.85)",
                bordercolor="rgba(255,255,255,0.1)",
                borderwidth=1,
                font=dict(size=11)
            ),
            margin=dict(l=20, r=20, t=60, b=0)
        )

        st.plotly_chart(fig, width="stretch")