import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# ⚙️ CONFIGURAÇÕES INICIAIS
# ==========================================
# PARTE 1 - CONFIGURAÇÕES DA PÁGINA
st.set_page_config(
    page_title="SF6 - Dados de jogadores",
    layout="wide",
    page_icon= "❄️"
)

st.title("📊 Análise de Desempenho")


# ==========================================
# ℹ️ AVISOS SOBRE A COLETA DE DADOS
# ==========================================
with st.expander("📌 Informações sobre a Base de Dados (Leia antes de analisar)", expanded=True):
    st.markdown("""
    * ⚠️ **Limite:** O sistema da Capcom disponibiliza apenas o histórico das últimas 100 partidas de cada jogador.
    * 🔄 **Coleta:** Para contornar essa limitação, os dados devem ser extraídos periodicamente através de um script de automação.
    * 📅 **Período Coberto:** Dados coletados a partir do dia **20/04/2026**.
    * 🔌 **Nota:** Partidas interrompidas por desconexão ("Rage Quit") geralmente não são registradas pelo sistema oficial.
    * ⚡ **Performance:** O Dashboard pode apresentar uma leve lentidão ou levar alguns segundos para carregar ao cruzar um grande volume de informações simultaneamente.
    """)

st.write("") # Dá um pequeno espaço antes de começar os filtros e gráficos

JOGADOR_ID = "4125616529"
# Atualizado para ler o novo arquivo limpo e otimizado!
ARQUIVO = f"SF6_historico_LIMPO_{JOGADOR_ID}.csv" 

# ==========================================
# 📥 CARREGAMENTO E PREPARAÇÃO DOS DADOS
# ==========================================
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv(ARQUIVO)
        # Cria a coluna de data pro filtro funcionar direitinho
        df['Data_Datetime'] = pd.to_datetime(df['Data'])

        # 🛡️ FIX RÁPIDO: Força a coluna a ser número (garante que não seja lida como texto)
        df['Oponente_MR'] = pd.to_numeric(df['Oponente_MR'], errors='coerce').fillna(0).astype(int)
        return df
    except FileNotFoundError:
        return None

df = carregar_dados()

if df is not None:
    # Pega o nome do jogador focado direto da primeira linha da tabela
    nome_jogador = df['Meu_Nome'].iloc[0]
    st.subheader(f"**{nome_jogador}** (ID: {JOGADOR_ID})")

    # ==========================================
    # 🎛️ BARRA LATERAL (FILTROS)
    # ==========================================
    st.sidebar.header("🎛️ Filtros")

    # Filtro 1: Personagem Utilizado 
    lista_meus_chars = df['Meu_Personagem'].unique().tolist()
    filtro_meu_char = st.sidebar.multiselect(
        "Personagens utilizados:", 
        options=lista_meus_chars, 
        default=[],
        placeholder="Selecione..."
    )

    # Filtro 2: Personagem do Oponente 
    lista_op_chars = df['Oponente_Personagem'].unique().tolist()
    filtro_op_char = st.sidebar.multiselect(
        "Personagens dos Oponentes:", 
        options=lista_op_chars, 
        default=[],
        placeholder="Selecione..."
    )

    # Filtro 3: Modo de Jogo 
    lista_modos = df['Tipo Partida (Jogo)'].unique().tolist()
    filtro_modo = st.sidebar.multiselect(
        "Modo de Jogo:", 
        options=lista_modos, 
        default=[],
        placeholder="Selecione..."
    )

    # Filtro 4: Pontos AM do Oponente (Maior ou Igual)
    filtro_mr = st.sidebar.number_input(
        "Pontos AM do Oponente (Mínimo):", 
        min_value=0, 
        max_value=5000, 
        value=0, 
        step=50, 
        help="Mostra apenas lutas contra oponentes com Pontos AM iguais ou superiores ao valor digitado."
    )

    # Filtro 5: Intervalo de Data
    min_date = df['Data_Datetime'].min().date()
    max_date = df['Data_Datetime'].max().date()
    
    filtro_data = st.sidebar.date_input(
        "Intervalo de Data:",
        value=[], 
        min_value=min_date,
        max_value=max_date
    )

    st.sidebar.info("📅 **Como usar a data:** O 1º clique define o início e o 2º clique define o fim do período.")

    # ==========================================
    # 🔄 APLICANDO OS FILTROS DE FORMA INTELIGENTE
    # ==========================================
    df_filtrado = df.copy()

    if filtro_meu_char:
        df_filtrado = df_filtrado[df_filtrado['Meu_Personagem'].isin(filtro_meu_char)]

    if filtro_op_char:
        df_filtrado = df_filtrado[df_filtrado['Oponente_Personagem'].isin(filtro_op_char)]

    if filtro_modo:
        df_filtrado = df_filtrado[df_filtrado['Tipo Partida (Jogo)'].isin(filtro_modo)]

    if filtro_mr > 0:
        df_filtrado = df_filtrado[df_filtrado['Oponente_MR'] >= filtro_mr]

    if len(filtro_data) == 2:
        data_inicio, data_fim = filtro_data
        df_filtrado = df_filtrado[
            (df_filtrado['Data_Datetime'].dt.date >= data_inicio) &
            (df_filtrado['Data_Datetime'].dt.date <= data_fim)
        ]
    elif len(filtro_data) == 1:
        df_filtrado = df_filtrado[df_filtrado['Data_Datetime'].dt.date == filtro_data[0]]

    # ==========================================
    # 🧮 CÁLCULOS DE BASE (NÃO APAGAR)
    # ==========================================
    total_partidas = len(df_filtrado)
    vitorias = len(df_filtrado[df_filtrado['Meu_Resultado'] == "Vitória 🏆"])
    derrotas = len(df_filtrado[df_filtrado['Meu_Resultado'] == "Derrota ❌"])
    
    win_rate = (vitorias / total_partidas) * 100 if total_partidas > 0 else 0

    # ==========================================
    # 🏆 SEÇÃO 1: RESUMO DE PERFORMANCE E MODOS
    # ==========================================
    st.markdown("---")
    st.markdown("### 🏆 Visão Geral de Resultados e Modos de Jogo")
    
    # Prepara os dados do resultado
    df_resultados = df_filtrado['Meu_Resultado'].value_counts().reset_index()
    df_resultados.columns = ['Resultado', 'Quantidade']
    cores_resultado = {"Vitória 🏆": "#119c0c", "Derrota ❌": "#b63a24", "Empate ➖": "#2f45c4"}

    # Prepara os dados dos Modos de Jogo
    df_modos = df_filtrado['Tipo Partida (Jogo)'].value_counts().reset_index()
    df_modos.columns = ['Modo', 'Quantidade']

    # Criamos duas colunas de tamanhos iguais para os gráficos
    col1, col2 = st.columns(2) 

    with col1:
        if total_partidas > 0:
            fig_pizza_res = px.pie(
                df_resultados, 
                values='Quantidade', 
                names='Resultado',
                color='Resultado',                
                color_discrete_map=cores_resultado,  
                hole=0, 
                title="Distribuição de Resultados",
                template="plotly_dark",
                height=350
            )

            fig_pizza_res.update_traces(
                textinfo='percent+value',
                textfont_color="white",      
                marker_line_color='white',   
                marker_line_width=0.5,
                hovertemplate="<b>%{label}</b><br>%{value:,.0f} partidas<extra></extra>"
            )
            
            fig_pizza_res.update_layout(
                margin=dict(l=10, r=10, t=50, b=10),
                legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5)
            )
            
            st.plotly_chart(fig_pizza_res, use_container_width=True)
        else:
            st.warning("Sem dados para exibir o gráfico de resultados.")

    with col2:
        if not df_modos.empty:
            fig_pizza_modos = px.pie(
                df_modos, 
                values='Quantidade', 
                names='Modo',
                hole=0, 
                title="Distribuição por Modo de Jogo",
                template="plotly_dark",
                height=350
            )

            fig_pizza_modos.update_traces(
                textinfo='percent+label', 
                textfont_color="white",      
                marker_line_color='white',   
                marker_line_width=0.5,
                hovertemplate="<b>%{label}</b><br>%{value:,.0f} partidas<extra></extra>"
            )
            
            fig_pizza_modos.update_layout(
                margin=dict(l=10, r=10, t=50, b=10),
                showlegend=False # Escondemos a legenda lateral porque os textos já estão dentro da pizza
            )
            
            st.plotly_chart(fig_pizza_modos, use_container_width=True)
            
    # Lógica inteligente para o aviso (st.info) dos Modos Casuais e Hub
    modos_jogados = df_filtrado['Tipo Partida (Jogo)'].unique()
    faltam = []
    if 'Casual' not in modos_jogados:
        faltam.append('Casual')
    if 'Battle Hub' not in modos_jogados:
        faltam.append('Battle Hub')
        
    if faltam:
        modos_str = " ou ".join(faltam)
        st.info(f"💡 **Nota:** Não constam partidas no modo **{modos_str}** no histórico atual.")

    st.write("") # Um pequeno respiro visual
    
    # Criamos 4 colunas para alinhar os números embaixo dos gráficos
    c_a, c_b, c_c, c_d = st.columns(4)
    c_a.metric("Total de Partidas", f"{total_partidas:,.0f}".replace(",", "."))
    c_b.metric("Vitórias", f"{vitorias:,.0f}".replace(",", "."))
    c_c.metric("Derrotas", f"{derrotas:,.0f}".replace(",", "."))
    c_d.metric("Win Rate Geral", f"{win_rate:.1f}%")


    # ==========================================
    # 🥋 SEÇÃO 2: PERSONAGENS UTILIZADOS (BARRAS + PIZZA)
    # ==========================================
    st.markdown("---")
    st.markdown("### 🥋 Personagens Mais Utilizados")
    
    if total_partidas > 0:
        # Agrupa os dados (Apenas o nome da coluna mudou para Meu_Personagem)
        df_meus_chars = df_filtrado['Meu_Personagem'].value_counts().reset_index()
        df_meus_chars.columns = ['Personagem', 'Quantidade']
        
        col3, col4 = st.columns(2)
        
        with col3:
            fig_barras_meus = px.bar(
                df_meus_chars,
                x='Personagem',
                y='Quantidade',
                color='Personagem',
                title="Quantidade de Partidas por Personagem",
                template="plotly_dark",
                height=400
            )
            
            fig_barras_meus.update_traces(
                texttemplate='%{y:,.0f}',    
                textfont_color="white",      
                textposition="outside",       
                marker_line_color='white',   
                marker_line_width=0.5,
                hovertemplate="<b>%{x}</b><br>%{y:,.0f} partidas<extra></extra>"
            )
            
            fig_barras_meus.update_layout(
                separators=",.",
                yaxis=dict(tickformat=","),
                showlegend=False,
                margin=dict(l=10, r=10, t=50, b=10)
            )
            st.plotly_chart(fig_barras_meus, use_container_width=True)
            
        with col4:
            fig_pizza_meus = px.pie(
                df_meus_chars, 
                values='Quantidade', 
                names='Personagem',
                color='Personagem',
                hole=0, 
                title="Proporção de Uso (%)",
                template="plotly_dark",
                height=400
            )

            fig_pizza_meus.update_traces(
                textinfo='percent', 
                textfont_color="white",      
                marker_line_color='white',   
                marker_line_width=0.5,
                hovertemplate="<b>%{label}</b><br>%{value:,.0f} partidas<extra></extra>"
            )
            
            fig_pizza_meus.update_layout(
                margin=dict(l=10, r=10, t=50, b=10),
                legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_pizza_meus, use_container_width=True)

    
    # ==========================================
    # 🥊 SEÇÃO 3: OPONENTES ENFRENTADOS E INSIGHTS
    # ==========================================
    st.markdown("---")
    st.markdown("### 🥊 Personagens dos Oponentes (Matchups)")
    
    if total_partidas > 0:
        df_oponentes = df_filtrado['Oponente_Personagem'].value_counts().reset_index()
        df_oponentes.columns = ['Personagem', 'Quantidade']
        
        fig_barras_op = px.bar(
            df_oponentes,
            x='Personagem',
            y='Quantidade',
            color='Personagem',
            title="Personagens mais enfrentados",
            template="plotly_dark",
            height=450
        )
        
        fig_barras_op.update_traces(
            texttemplate='%{y:,.0f}',    
            textfont_color="white",      
            textposition="outside",       
            marker_line_color='white',   
            marker_line_width=0.5,
            hovertemplate="<b>%{x}</b><br>%{y:,.0f} lutas<extra></extra>"
        )
        
        fig_barras_op.update_layout(
            separators=",.",
            yaxis=dict(tickformat=","),
            showlegend=False,
            margin=dict(l=10, r=10, t=50, b=10)
        )
        st.plotly_chart(fig_barras_op, use_container_width=True)

        # Lógica do st.info() posicionada logo abaixo do gráfico
        todos_oponentes = set(df['Oponente_Personagem'].dropna().unique())
        oponentes_enfrentados = set(df_filtrado['Oponente_Personagem'].dropna().unique())
        nao_enfrentados = sorted(list(todos_oponentes - oponentes_enfrentados))
        
        st.write("") # Dá um pequeno respiro visual
        if nao_enfrentados:
            qtd_nao = len(nao_enfrentados)
            nomes_str = ", ".join(nao_enfrentados)
            st.info(f"💡 **Curiosidade:** Com os filtros aplicados, existem **{qtd_nao} personagens** no histórico  não enfrentado(s): {nomes_str}.")
        else:
            st.info("💡 **Curiosidade:** Com os filtros aplicados, todos os personagens foram enfrentados!")

        st.write("")

        st.divider() # Linha divisória para separar visualmente as seções
        st.markdown("#### 📊 Taxa de Vitória contra os Personagens")
        
        # Cria a tabela agrupando por personagem
        df_matchup = df_filtrado.groupby('Oponente_Personagem').agg(
            Lutas=('Meu_Resultado', 'count'),
            Vitórias=('Meu_Resultado', lambda x: (x == "Vitória 🏆").sum()),
            Derrotas=('Meu_Resultado', lambda x: (x == "Derrota ❌").sum())
        ).reset_index()
        
        # Calcula o Win Rate
        df_matchup['Win Rate (%)'] = (df_matchup['Vitórias'] / df_matchup['Lutas']) * 100
        
        # Ordena (quem tem mais lutas aparece primeiro) e formata a % para ficar bonito
        df_matchup_view = df_matchup.sort_values(by=['Lutas', 'Win Rate (%)'], ascending=[False, False]).copy()
        df_matchup_view['Win Rate (%)'] = df_matchup_view['Win Rate (%)'].apply(lambda x: f"{x:.1f}%")
        
        # Exibe a tabela na tela
        st.dataframe(df_matchup_view, use_container_width=True, hide_index=True)

        st.info("💡 **É possível ordernar as tabelas clicando nos cabeçalhos das colunas**")

    # ==========================================
    # 📅 SEÇÃO 4: PERFORMANCE POR DIA DA SEMANA
    # ==========================================
    st.markdown("---")
    st.markdown("### 📅 Desempenho por Dia da Semana")

    if total_partidas > 0:
        col5, col6 = st.columns([1.5, 1])
        
        # Preparando os dados para os dias da semana na ordem correta
        ordem_dias = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
        
        # Conta as partidas e força a ordem cronológica da semana
        df_dias = df_filtrado['Dia da Semana'].value_counts().reindex(ordem_dias).fillna(0).reset_index()
        df_dias.columns = ['Dia da Semana', 'Quantidade']
        df_dias = df_dias[df_dias['Quantidade'] > 0] # Oculta os dias em que não houve partidas
        
        with col5:
            fig_barras_dias = px.bar(
                df_dias,
                x='Dia da Semana',
                y='Quantidade',
                title="Quantidade de Partidas",
                template="plotly_dark",
                height=350
            )
            
            fig_barras_dias.update_traces(
                texttemplate='%{y:,.0f}',    
                textfont_color="white",      
                textposition="outside",       
                marker_line_color='white',   
                marker_line_width=0.5,
                hovertemplate="<b>%{x}</b><br>%{y:,.0f} partidas<extra></extra>"
            )
            
            fig_barras_dias.update_layout(
                xaxis=dict(title=""),
                yaxis=dict(showticklabels=False, title=""), # Esconde os números do eixo Y para ficar mais limpo
                margin=dict(l=10, r=10, t=50, b=10)
            )
            st.plotly_chart(fig_barras_dias, use_container_width=True)

        with col6:
            # Dando um pequeno espaço para alinhar com o título do gráfico
            st.write("") 
            st.write("")
            st.markdown("#### Taxa de Vitória (Win Rate)")
            
            # Calcula e exibe a % de vitória linha por linha de forma elegante
            for dia in df_dias['Dia da Semana']:
                df_dia_especifico = df_filtrado[df_filtrado['Dia da Semana'] == dia]
                total_dia = len(df_dia_especifico)
                # Atualizado para Meu_Resultado
                vitorias_dia = len(df_dia_especifico[df_dia_especifico['Meu_Resultado'] == "Vitória 🏆"])
                
                tx_vitoria = (vitorias_dia / total_dia) * 100 if total_dia > 0 else 0
                
                # Usa st.markdown para deixar o dia em negrito e a taxa na frente
                st.markdown(f"- **{dia}:** {tx_vitoria:.1f}%")

    # ==========================================
    # 🕒 SEÇÃO 4.5: PERFORMANCE POR HORA DO DIA
    # ==========================================
    st.markdown("---")
    st.markdown("### 🕒 Performance por Faixa de Horário")

    if total_partidas > 0:
        # Extrai apenas os 2 primeiros caracteres da 'Hora Exata' (ex: "21:03" vira "21")
        df_filtrado['Hora_Fixa'] = df_filtrado['Hora Exata'].str[:2]
        
        # Agrupa os dados pela hora
        df_horas = df_filtrado.groupby('Hora_Fixa').agg(
            Lutas=('Meu_Resultado', 'count'), # Atualizado para Meu_Resultado
            Vitórias=('Meu_Resultado', lambda x: (x == "Vitória 🏆").sum()) # Atualizado para Meu_Resultado
        ).reset_index()
        
        # Calcula o Win Rate
        df_horas['Win Rate (%)'] = (df_horas['Vitórias'] / df_horas['Lutas']) * 100
        
        # Cria a coluna com o texto bonito da faixa de horário
        df_horas['Faixa de Horário'] = df_horas['Hora_Fixa'] + ":00 às " + df_horas['Hora_Fixa'] + ":59"
        
        # Formata o Win Rate para exibir o símbolo de porcentagem e 1 casa decimal
        df_horas['Win Rate (%)'] = df_horas['Win Rate (%)'].apply(lambda x: f"{x:.1f}%")
        
        # Prepara a tabela final apenas com as colunas que importam para visualização
        df_horas_view = df_horas[['Faixa de Horário', 'Lutas', 'Win Rate (%)']].sort_values(by='Faixa de Horário')
        
        if not df_horas_view.empty:
            st.info("💡 **Dica:** Você pode clicar no título das colunas abaixo para ordenar pelo horário com mais lutas ou maior Win Rate!")
            # Exibe a tabela interativa
            st.dataframe(df_horas_view, use_container_width=True, hide_index=True)
        else:
            st.write("Sem dados de horário para exibir.")



        # ==========================================
    # 📺 SEÇÃO 5.1: LADO DA TELA (P1 VS P2)
    # ==========================================
    st.markdown("---")
    st.markdown("### 📺 Análise das Partidas começando como Player 1 ou Player 2")
    
    if total_partidas > 0:
        col_lado1, col_lado2 = st.columns(2)
        
        with col_lado1:
            df_lados = df_filtrado['Meu_Lado'].value_counts().reset_index()
            df_lados.columns = ['Lado', 'Quantidade']
            
            # Criamos uma coluna invisível no gráfico só para traduzir o texto do Hover
            df_lados['Nome_Hover'] = df_lados['Lado'].map({"Player 1": "Lado Esquerdo", "Player 2": "Lado Direito"})
            
            cores_lados = {"Player 1": "#3498db", "Player 2": "#e74c3c"} 
            
            fig_pizza_lado = px.pie(
                df_lados,
                values='Quantidade',
                names='Lado',
                color='Lado',
                color_discrete_map=cores_lados,
                title="Distribuição como Player 1 ou Player 2",
                template="plotly_dark",
                height=350,
                custom_data=['Nome_Hover'] # Passa a tradução para o gráfico usar no hover
            )
            
            # Removido o 'hole=0.4' (volta a ser pizza cheia) e ajustado o texto do hover
            fig_pizza_lado.update_traces(
                textinfo='percent+label', 
                textfont_color="white", 
                marker_line_color='white', 
                marker_line_width=0.5,
                hovertemplate="<b>%{customdata[0]}</b><br>%{value:,.0f} Partidas<extra></extra>"
            )
            fig_pizza_lado.update_layout(showlegend=False, margin=dict(l=10, r=10, t=50, b=10))
            
            st.plotly_chart(fig_pizza_lado, use_container_width=True)

        with col_lado2:
            st.write("") 
            st.write("")
            
            # Cálculo P1
            df_p1 = df_filtrado[df_filtrado['Meu_Lado'] == 'Player 1']
            total_p1 = len(df_p1)
            vit_p1 = len(df_p1[df_p1['Meu_Resultado'] == "Vitória 🏆"]) # Atualizado para Meu_Resultado
            tx_p1 = (vit_p1 / total_p1) * 100 if total_p1 > 0 else 0
            
            # Cálculo P2
            df_p2 = df_filtrado[df_filtrado['Meu_Lado'] == 'Player 2']
            total_p2 = len(df_p2)
            vit_p2 = len(df_p2[df_p2['Meu_Resultado'] == "Vitória 🏆"]) # Atualizado para Meu_Resultado
            tx_p2 = (vit_p2 / total_p2) * 100 if total_p2 > 0 else 0
            
            # Agora usamos st.metric SEM o 3º parâmetro (some a setinha confusa)
            # E usamos st.caption para colocar o detalhe logo abaixo, pequeno e cinza
            st.metric("Taxa de Vitória como Player 1 (Esquerda)", f"{tx_p1:.1f}%")
            st.caption(f"🎯 **{vit_p1} vitórias** de {total_p1} partidas")
            
            st.write("") 
            
            st.metric("Taxa de Vitória como Player 2 (Direita)", f"{tx_p2:.1f}%")
            st.caption(f"🎯 **{vit_p2} vitórias** de {total_p2} partidas")


    # ==========================================
    # 🧠 SEÇÃO 5.2: FATOR PSICOLÓGICO (ROUNDS) E FINALIZAÇÕES
    # ==========================================
    st.markdown("---")
    st.markdown("### 🧠 Fator Psicológico e Finalização de Rounds")
    
    if total_partidas > 0:
        # 1. Cartões de Peso do 1º Round
        c_r1_v, c_r1_p = st.columns(2)
        
        df_venceu = df_filtrado[df_filtrado['Venceu_Primeiro_Round'] == 'Sim']
        total_venceu = len(df_venceu)
        vit_venceu = len(df_venceu[df_venceu['Meu_Resultado'] == "Vitória 🏆"]) # Atualizado
        tx_venceu = (vit_venceu / total_venceu) * 100 if total_venceu > 0 else 0
        
        df_perdeu = df_filtrado[df_filtrado['Venceu_Primeiro_Round'] == 'Não']
        total_perdeu = len(df_perdeu)
        vit_perdeu = len(df_perdeu[df_perdeu['Meu_Resultado'] == "Vitória 🏆"]) # Atualizado
        tx_perdeu = (vit_perdeu / total_perdeu) * 100 if total_perdeu > 0 else 0
        
        with c_r1_v:
            st.metric("Taxa de Vitória SE VENCER o 1º Round", f"{tx_venceu:.1f}%")
            st.caption(f"🎯 **{vit_venceu} vitórias** de {total_venceu} partidas onde venceu o 1º round")
            
        with c_r1_p:
            st.metric("Taxa de Vitória SE PERDER o 1º Round", f"{tx_perdeu:.1f}%")
            st.caption(f"🎯 **{vit_perdeu} vitórias** de {total_perdeu} partidas onde perdeu o 1º round")

        # 2. Gráfico Horizontal mostrando a Trajetória da Partida e Gráfico de Pizza
        st.markdown("#### 🔄 Trajetória da Partida (Sequência de Rounds)")
        
        contagem_seq = df_filtrado['Sequencia_Rounds'].value_counts().reset_index()
        contagem_seq.columns = ['Sequência', 'Quantidade']
        
        traducao_seq = {
            "V-V": "Vitória Limpa 2-0 (V-V)",
            "V-D-V": "Vitória Suada 2-1 (V-D-V)",
            "V-D-D": "Tomou Virada 1-2 (V-D-D)",
            "D-D": "Derrota Limpa 0-2 (D-D)",
            "D-V-D": "Reagiu mas Perdeu 1-2 (D-V-D)",
            "D-V-V": "Virada Épica 2-1 (D-V-V)"
        }
        
        contagem_seq['Descrição'] = contagem_seq['Sequência'].map(traducao_seq).fillna(contagem_seq['Sequência'])
        contagem_seq = contagem_seq[contagem_seq['Sequência'] != "Sem dados"]
        
        if not contagem_seq.empty:
            cores_seq = {
                "V-V": "#19a50d", "V-D-V": "#005fcc", "D-V-V": "#9c00cc",
                "D-D": "#ac1f06", "D-V-D": "#4d2d27", "V-D-D": "#efec3b"
            }
            
            c_seq1, c_seq2 = st.columns(2)
            
            with c_seq1:
                fig_seq_bar = px.bar(
                    contagem_seq, x='Quantidade', y='Descrição', color='Sequência',
                    color_discrete_map=cores_seq, orientation='h', template="plotly_dark",
                    height=350, custom_data=['Sequência'] 
                )
                fig_seq_bar.update_traces(
                    texttemplate='<b>%{x}</b>', textposition="outside", textfont_color="white",
                    hovertemplate="<b>Sequência: %{customdata[0]}</b><br>%{x} partidas<extra></extra>"
                )
                fig_seq_bar.update_layout(
                    showlegend=False, yaxis={'categoryorder': 'total ascending', 'title': ''},
                    xaxis={'title': 'Quantidade de Partidas', 'showticklabels': False}, margin=dict(l=10, r=10, t=10, b=10)
                )
                st.plotly_chart(fig_seq_bar, use_container_width=True)

            with c_seq2:
                fig_seq_pie = px.pie(
                    contagem_seq, values='Quantidade', names='Descrição', color='Sequência',
                    color_discrete_map=cores_seq, template="plotly_dark", height=350, custom_data=['Sequência']
                )
                fig_seq_pie.update_traces(
                    textinfo='percent', textfont_color="white", marker_line_color='white', marker_line_width=0.5,
                    hovertemplate="<b>Sequência: %{customdata[0]}</b><br>%{value} partidas<extra></extra>"
                )
                fig_seq_pie.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig_seq_pie, use_container_width=True)

        # ==========================================
        # 3. NOVOS GRÁFICOS: COMO OS ROUNDS FORAM DECIDIDOS
        # ==========================================
        st.markdown("#### 💥 Como os Rounds Foram Decididos")
        
        # Como o CSV já está limpo, extrair a lista ficou super simples e rápido!
        def extrair_golpes_limpos(texto):
            if pd.isna(texto) or texto == "Nenhum" or texto == "Sem dados":
                return []
            return [g.strip() for g in str(texto).split(',')]
        
        df_golpes = df_filtrado[['Meus_Golpes_Finais', 'Golpes_Oponente']].copy()
        df_golpes['Meus_Lista'] = df_golpes['Meus_Golpes_Finais'].apply(extrair_golpes_limpos)
        df_golpes['Op_Lista'] = df_golpes['Golpes_Oponente'].apply(extrair_golpes_limpos)
        
        # 'explode' separa cada item da lista em uma linha diferente
        df_meus_golpes = df_golpes.explode('Meus_Lista')['Meus_Lista'].value_counts().reset_index()
        df_meus_golpes.columns = ['Golpe Final', 'Quantidade']
        df_meus_golpes = df_meus_golpes.sort_values('Quantidade', ascending=True) 
        
        df_op_golpes = df_golpes.explode('Op_Lista')['Op_Lista'].value_counts().reset_index()
        df_op_golpes.columns = ['Golpe Final', 'Quantidade']
        df_op_golpes = df_op_golpes.sort_values('Quantidade', ascending=True)
        
        # 🔢 Calcula os totais de rounds somando as quantidades
        total_meus_rounds = df_meus_golpes['Quantidade'].sum() if not df_meus_golpes.empty else 0
        total_op_rounds = df_op_golpes['Quantidade'].sum() if not df_op_golpes.empty else 0
        
        c_g1, c_g2 = st.columns(2)
        
        with c_g1:
            if not df_meus_golpes.empty:
                fig_meus_g = px.bar(
                    df_meus_golpes, x='Quantidade', y='Golpe Final', orientation='h',
                    # Título atualizado com o total dinâmico
                    title=f"Como VOCÊ finalizou os rounds (Total: {total_meus_rounds})", template="plotly_dark",
                    color_discrete_sequence=["#00cc96"] # Verde para vitórias
                )
                fig_meus_g.update_traces(
                    texttemplate='<b>%{x}</b>', textposition="outside", textfont_color="white",
                    hovertemplate="<b>%{y}</b><br>%{x} rounds finalizados<extra></extra>"
                )
                fig_meus_g.update_layout(xaxis={'showticklabels': False, 'title': ''}, yaxis={'title': ''}, margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig_meus_g, use_container_width=True)
            else:
                st.info("Sem dados de seus golpes finais para exibir.")

        with c_g2:
            if not df_op_golpes.empty:
                fig_op_g = px.bar(
                    df_op_golpes, x='Quantidade', y='Golpe Final', orientation='h',
                    # Título atualizado com o total dinâmico
                    title=f"Como o OPONENTE finalizou os rounds (Total: {total_op_rounds})", template="plotly_dark",
                    color_discrete_sequence=["#ef553b"] # Vermelho para derrotas
                )
                fig_op_g.update_traces(
                    texttemplate='<b>%{x}</b>', textposition="outside", textfont_color="white",
                    hovertemplate="<b>%{y}</b><br>%{x} rounds finalizados<extra></extra>"
                )
                fig_op_g.update_layout(xaxis={'showticklabels': False, 'title': ''}, yaxis={'title': ''}, margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig_op_g, use_container_width=True)
            else:
                st.info("Sem dados de golpes do oponente para exibir.")


    # ==========================================
    # 🎯 SEÇÃO 5.5: OPONENTES (JOGADORES ENFRENTADOS)
    # ==========================================
    st.markdown("---")
    st.markdown("### 🎯 Oponentes (Jogadores Enfrentados)")
    
    if total_partidas > 0:
        # Agrupando pelo NOME DO JOGADOR adversário usando as novas colunas
        df_rivais = df_filtrado.groupby('Oponente_Nome').agg(
            Partidas=('Meu_Resultado', 'count'),
            Vitórias=('Meu_Resultado', lambda x: (x == "Vitória 🏆").sum()),
            Derrotas=('Meu_Resultado', lambda x: (x == "Derrota ❌").sum())
        ).reset_index()
        
        df_rivais['Win Rate'] = (df_rivais['Vitórias'] / df_rivais['Partidas']) * 100

        if not df_rivais.empty:
            c_d1, c_d2, c_d3, c_d4 = st.columns(4)
            
            # 1. Mais Enfrentado (Jogador)
            mais_enfrentado = df_rivais.loc[df_rivais['Partidas'].idxmax()]
            
            # 2. Mais Derrotou (Maior número absoluto de vitórias)
            mais_derrotou = df_rivais.loc[df_rivais['Vitórias'].idxmax()]
            
            # 3. Mais Perdeu (Maior número absoluto de derrotas)
            mais_perdeu = df_rivais.loc[df_rivais['Derrotas'].idxmax()]
            
            # 4. Confronto Equilibrado (Mais próximo de 50% de Win Rate, Mínimo 4 Partidas)
            df_eq = df_rivais[df_rivais['Partidas'] >= 4].copy()
            if not df_eq.empty:
                df_eq['Distancia_50'] = abs(df_eq['Win Rate'] - 50.0)
                df_eq = df_eq.sort_values(by=['Distancia_50', 'Partidas'], ascending=[True, False])
                
                mais_eq = df_eq.iloc[0]
                nome_eq = mais_eq['Oponente_Nome'] # Atualizado para Oponente_Nome
                detalhe_eq = f"⚖️ **{mais_eq['Win Rate']:.1f}%** de vitórias em {mais_eq['Partidas']} partidas"
            else:
                nome_eq = "Sem dados"
                detalhe_eq = "Requer mín. de 4 partidas"

            # Renderiza os cartões usando st.metric SEM a setinha e st.caption para os detalhes
            with c_d1:
                st.metric("Jogador Mais Enfrentado", f"{mais_enfrentado['Oponente_Nome']}")
                st.caption(f"⚔️ **{mais_enfrentado['Partidas']} partidas** disputadas")
            
            with c_d2:
                st.metric("'Freguês' (Vitórias totais)", f"{mais_derrotou['Oponente_Nome']}")
                st.caption(f"🎯 **{mais_derrotou['Vitórias']} vitórias** em {mais_derrotou['Partidas']} partidas")
            
            with c_d3:
                st.metric("Nêmesis (Derrotas totais)", f"{mais_perdeu['Oponente_Nome']}")
                st.caption(f"💀 **{mais_perdeu['Derrotas']} derrotas** em {mais_perdeu['Partidas']} partidas")
            
            with c_d4:
                st.metric(
                    "Rivalidade Equilibrada", 
                    f"{nome_eq}",
                    help="Mostra o oponente com quem sua taxa de vitória (Win Rate) está mais próxima de 50%. Exige um mínimo de 4 partidas disputadas para evitar falsos equilíbrios de 1x1."
                )
                st.caption(detalhe_eq)


    # ==========================================
    # 🔍 SEÇÃO 5.8: BUSCA DIRETA DE CONFRONTOS
    # ==========================================
    st.markdown("---")
    st.markdown("### 🔍 Busca de Histórico contra Oponente")
    
    # 1. Pega todos os nomes únicos de oponentes no seu histórico filtrado e coloca em ordem alfabética
    lista_oponentes = sorted(df_filtrado['Oponente_Nome'].dropna().unique().tolist())

    # 2. Cria a caixa de seleção inteligente e pesquisável
    busca_oponente = st.selectbox(
        "Selecione ou digite o nome do jogador adversário:", 
        options=lista_oponentes,
        index=None, # Isso faz a caixa começar vazia em vez de selecionar o 1º nome da lista
        placeholder="Clique aqui e comece a digitar para filtrar..."
    )

    if busca_oponente:
        # Como agora a pessoa clica no nome exato, a busca fica muito mais rápida
        df_busca = df_filtrado[df_filtrado['Oponente_Nome'] == busca_oponente]

        if not df_busca.empty:
            # Conta as vitórias e derrotas dentro dessa busca específica
            vitorias_busca = (df_busca['Meu_Resultado'] == "Vitória 🏆").sum()
            derrotas_busca = (df_busca['Meu_Resultado'] == "Derrota ❌").sum()
            
            # Monta a mensagem completinha com os emojis para ficar mais visual
            mensagem_sucesso = f"Encontrado(s) {len(df_busca)} confronto(s) contra '{busca_oponente}'! (🏆 {vitorias_busca} vitórias e ❌ {derrotas_busca} derrotas)"
            
            st.success(mensagem_sucesso)
            
            # Ordena da partida mais recente para a mais antiga (Removida a duplicação)
            df_busca = df_busca.sort_values(by=['Data', 'Hora Exata'], ascending=[False, False])
            
            # Cria uma "tabelinha" (Expander) para cada partida encontrada
            for index, row in df_busca.iterrows():
                icone_res = "🟢" if "Vitória" in row['Meu_Resultado'] else ("🔴" if "Derrota" in row['Meu_Resultado'] else "⚪")
                
                titulo_expander = f"{icone_res} {row['Data']} às {row['Hora Exata']} | {row['Meu_Personagem']} vs {row['Oponente_Personagem']} | Placar: {row['Placar']}"
                
                with st.expander(titulo_expander):
                    col_b1, col_b2, col_b3 = st.columns([1, 1.5, 1.5])
                    
                    with col_b1:
                        st.markdown(f"**Modo:** {row['Tipo Partida (Jogo)']}")
                        st.markdown(f"**Resultado:** {row['Meu_Resultado']}")
                        
                    with col_b2:
                        st.markdown("🗡️ **Como venceu os rounds:**")
                        st.info(row['Meus_Golpes_Finais'])
                        
                    with col_b3:
                        st.markdown("🛡️ **Como o OPONENTE venceu os rounds:**")
                        st.error(row['Golpes_Oponente'])


    # ==========================================
    # 📋 SEÇÃO 6: TABELA DE ÚLTIMAS PARTIDAS
    # ==========================================

    st.markdown("---")
    st.markdown("### 📋 Histórico Detalhado")
    
    colunas_exibicao = [
        'Data', 'Hora Exata', 'Tipo Partida (Jogo)', 'Turno', 'Meu_Resultado', 'Placar', 
        'Meu_Personagem', 'Oponente_Nome', 'Oponente_Personagem'
    ]
    
    if total_partidas > 0:
        st.dataframe(
            df_filtrado[colunas_exibicao].sort_values(by=['Data', 'Hora Exata'], ascending=[False, False]), 
            use_container_width=True, 
            hide_index=True
        )


# ==========================================
    # 🎲 SEÇÃO 5.6: HISTÓRICO COMO PLAYER 1 (LADO ESQUERDO)
    # ==========================================
    st.markdown("---")
    st.markdown("### 🎲 Curiosidade: Partidas Iniciadas como Player 1")
    
    # Filtra o dataframe usando a coluna correta: 'Meu_Lado'
    df_p1 = df_filtrado[df_filtrado['Meu_Lado'].astype(str).str.contains('1')]
    
    if not df_p1.empty:
        # Agrupa os oponentes enfrentados como P1 para contar as partidas
        df_p1_agrupado = df_p1.groupby('Oponente_Nome').agg(
            Partidas=('Meu_Resultado', 'count'),
            Vitórias=('Meu_Resultado', lambda x: (x == "Vitória 🏆").sum()),
            Derrotas=('Meu_Resultado', lambda x: (x == "Derrota ❌").sum())
        ).reset_index()
        
        # Ordena para mostrar quem você mais enfrentou como P1 primeiro
        df_p1_agrupado = df_p1_agrupado.sort_values(by='Partidas', ascending=False)
        
        st.write(f"Você iniciou a partida no lado esquerdo da tela (P1) em **{len(df_p1)} partidas**, enfrentando **{len(df_p1_agrupado)} oponentes diferentes**.")
        
        # Colocamos dentro de um expander para não deixar a tela gigante
        with st.expander("Ver lista completa de Oponentes (Como P1)"):
            st.dataframe(
                df_p1_agrupado, 
                use_container_width=True, 
                hide_index=True
            )
    else:
        # Caso o nome dentro da coluna não seja '1', ele vai avisar aqui
        st.info("Nenhuma partida encontrada. Dica: verifique se na coluna 'Meu_Lado' está escrito 'P1', 'Esquerda' ou '1' e ajuste o código!")