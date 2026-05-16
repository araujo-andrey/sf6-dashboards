# PARTE 0 - BIBLIOTECAS
import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt

# PARTE 1 - CONFIGURAÇÕES DA PÁGINA
st.set_page_config(
    page_title="SF6 - Ranked Dashboard",
    layout="wide",
    page_icon="❄️"
)

# ==========================================
# ℹ️ INFORMAÇÕES DO PROJETO E BASE DE DADOS
# ==========================================
st.title("❄️🥊 Street Fighter 6 - Temporada 11 Encerrada🥊❄️")
st.markdown("**Dashboard interativo dos jogadores de Rank Master ou Superior.**")

with st.expander("📌 Sobre a Base de Dados", expanded=True):
    st.markdown("""
    * 🤖 **Extração Massiva:** O script operou por **32 horas** para extrair dados de mais de **35.000 páginas** do site da Capcom.
    * 🚧 **Estratégia:** Devido à estrutura dinâmica do site para a temporada atual, essa coleta foi feita na temporada encerrada.
    * ⚡ **Performance:** O Dashboard pode apresentar uma leve lentidão ou levar alguns segundos para carregar ao cruzar um grande volume de informações simultaneamente.
    """)

st.info("""
💡 **Dicas de Navegação:**
* 🎛️ **Totalmente Dinâmico:** Use a barra lateral à esquerda para combinar múltiplos filtros simultaneamente. Todos os gráficos se ajustam em segundos!
* 🔍 **Zoom nos Gráficos:** Dê um duplo clique com o mouse sobre qualquer gráfico para resetar a visualização.
""")

st.write("")

# PARTE 2 - CARREGAMENTO DOS PARQUETs
@st.cache_data
def carregar_dados():
    caminho = "sf6_agregado.parquet"
    return pd.read_parquet(caminho)

df = carregar_dados()


# def carregar_dados2():
#     caminho2 = "sf6_jogadores.parquet"
#     return pd.read_parquet(caminho2)


# df_jogadores = carregar_dados2()

# --- SIDEBAR (FILTROS) ---
st.sidebar.header("🔍 Filtros de Análise")

lista_paises = sorted(df['País'].dropna().unique())
paises_sel = st.sidebar.multiselect("Filtrar por País:", options=lista_paises)

lista_personagens = sorted(df['Personagem'].dropna().unique())
personagens_sel = st.sidebar.multiselect("Filtrar por Personagem:", options=lista_personagens)

ordem_ranks = ["Legend", "Ultimate Master", "Grand Master", "High Master", "Master"]
lista_rank = [r for r in ordem_ranks if r in df['Rank'].unique()]
rank_sel = st.sidebar.multiselect("Filtrar por Rank:", options=lista_rank)

lista_controles = sorted(df['Tipo de Controle'].dropna().unique())
controle_sel = st.sidebar.multiselect("Filtrar por Controle:", options=lista_controles)

# --- LÓGICA DE FILTRAGEM ---
df_filtrado = df.copy()

if paises_sel:
    df_filtrado = df_filtrado[df_filtrado['País'].isin(paises_sel)]
if personagens_sel:
    df_filtrado = df_filtrado[df_filtrado['Personagem'].isin(personagens_sel)]
if rank_sel:
    df_filtrado = df_filtrado[df_filtrado['Rank'].isin(rank_sel)]
if controle_sel:
    df_filtrado = df_filtrado[df_filtrado['Tipo de Controle'].isin(controle_sel)]

# ── GUARDA ÚNICA: para tudo se não tiver dados ────────────────────────────────
if df_filtrado.empty:
    st.warning("⚠️ Nenhum resultado encontrado para a combinação de filtros selecionada. Tente remover algum filtro.")
    st.stop()

# --- CORPO DO DASHBOARD ---
# --- LINHA 1: RESUMO DOS RANKINGS ---
st.subheader("📊 Análise por Ranking")

col1, col2 = st.columns([0.3, 0.7])

with col1:
    cores_rank = {
        "Legend": "#BE1818",
        "Ultimate Master": "#941EE2",
        "Grand Master": "#F0BE1C",
        "High Master": "#c0c0c0",
        "Master": "#22c722"
    }

    contagem_ranking = df_filtrado['Rank'].value_counts().reset_index()
    contagem_ranking.columns = ['Ranking', 'Quantidade']

    fig_pizza = px.pie(
        contagem_ranking,
        values='Quantidade',
        names='Ranking',
        color='Ranking',
        color_discrete_map=cores_rank,
        hole=0,
        title="Distribuição dos Personagens por Ranking",
        template="plotly_dark",
        height=800
    )
    fig_pizza.update_traces(
        textfont_color="white",
        marker_line_color='white',
        marker_line_width=0.5,
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} personagens<extra></extra>"
    )
    fig_pizza.update_layout(
        separators=",.",
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_pizza, use_container_width=True)

with col2:
    total_personagens = sum(contagem_ranking['Quantidade'])
    total_formatado = f"{total_personagens:,.0f}".replace(",", ".")

    fig_barras_rank = px.bar(
        contagem_ranking,
        x='Ranking',
        y='Quantidade',
        color='Ranking',
        color_discrete_map=cores_rank,
        title=f"Quantidade total de Personagens: {total_formatado}",
        template="plotly_dark",
        height=800
    )
    fig_barras_rank.update_traces(
        texttemplate='%{y:,.0f}',
        textfont_color="white",
        textposition="outside",
        marker_line_color='white',
        marker_line_width=0.5,
        hovertemplate="<b>%{x}</b><br>%{y:,.0f} personagens<extra></extra>"
    )
    fig_barras_rank.update_layout(
        separators=",.",
        yaxis=dict(tickformat=","),
        showlegend=False
    )
    st.plotly_chart(fig_barras_rank, use_container_width=True)

st.divider()

# --- LINHA 2: DISTRIBUIÇÃO DE MR ---
st.subheader("📈 Distribuição dos Personagens por Pontos AM")

if df_filtrado['Pontos AM'].dropna().empty:
    st.warning("⚠️ Nenhum dado de Pontos AM disponível para os filtros selecionados.")
else:
    min_mr = (int(df_filtrado['Pontos AM'].min()) // 100) * 100
    max_mr = (int(df_filtrado['Pontos AM'].max()) // 100) * 100 + 100

    bins   = list(range(min_mr, max_mr + 100, 100))
    labels = [f"{i} - {i+99}" for i in bins[:-1]]

    df_dist = df_filtrado.copy()
    df_dist['Faixa_MR'] = pd.cut(df_dist['Pontos AM'], bins=bins, labels=labels, right=False)
    contagem_faixas = df_dist['Faixa_MR'].value_counts().reset_index()
    contagem_faixas.columns = ['Faixa de Pontos', 'Quantidade']
    contagem_faixas = contagem_faixas.sort_values('Faixa de Pontos')

    fig_hist = px.bar(
        contagem_faixas,
        x="Faixa de Pontos",
        y="Quantidade",
        color_discrete_sequence=["#C21313"],
        template="plotly_dark",
        text_auto=True
    )
    fig_hist.update_layout(
        title="Curva de Distribuição dos Personagens por Pontuação",
        height=600,
        width=2500,
        xaxis_title="Pontos AM",
        yaxis_title="Quantidade de Personagens",
        bargap=0.1,
        separators=",.",
        yaxis=dict(tickformat=","),
        xaxis=dict(type='category', tickmode='linear')
    )
    fig_hist.update_traces(
        marker_line_color='white',
        marker_line_width=0.5,
        texttemplate='%{y:,.0f}',
        textposition='outside',
        hovertemplate="<b>Faixa:</b> %{x} AM<br><b>Jogadores:</b> %{y:,.0f}<extra></extra>"
    )
    st.plotly_chart(fig_hist, use_container_width=False)

st.divider()

# --- LINHA 3: CURVA ACUMULADA ---
st.subheader("📈 % de Personagens acima de X Pontos AM")

if df_filtrado['Pontos AM'].dropna().empty:
    st.warning("⚠️ Nenhum dado de Pontos AM disponível para os filtros selecionados.")
else:
    df_sorted = df_filtrado['Pontos AM'].sort_values(ascending=False).reset_index(drop=True).to_frame()
    df_sorted['Top %'] = ((df_sorted.index + 1) / len(df_sorted)) * 100

    fig_exclusividade = px.area(
        df_sorted,
        x="Pontos AM",
        y="Top %",
        title="Curva de Distribuição Acumulada dos Personagens por Pontos AM",
        template="plotly_dark",
        color_discrete_sequence=["#C21313"]
    )
    fig_exclusividade.update_layout(
        height=600,
        xaxis_title="Pontos AM",
        yaxis_title="% de Personagens",
        yaxis=dict(range=[0, 100], ticksuffix="%"),
        separators=",."
    )
    fig_exclusividade.update_traces(
        hovertemplate="<b>Pontuação:</b> %{x} AM<br>%{y:.2f}% dos personagens possuem pontuação igual ou superior<extra></extra>"
    )
    st.plotly_chart(fig_exclusividade, use_container_width=True)
    st.info("💡 **Como ler este gráfico:** Se você colocar o mouse em 1800 pontos e o gráfico marcar 5%, significa que apenas 5% de todos os personagens conseguiram alcançar ou ultrapassar essa pontuação.")

st.divider()

# --- LINHA 4: POPULARIDADE DOS PERSONAGENS ---
st.subheader("👥 Popularidade dos personagens")
st.info("A opção de jogar a rankeada com personagem aleatório foi considerada como um personagem diferente.")

pop_personagem = df_filtrado['Personagem'].value_counts().reset_index()
pop_personagem.columns = ['Personagem', 'Quantidade']

fig_pop = px.bar(
    pop_personagem,
    x='Quantidade',
    y='Personagem',
    orientation='h',
    title="Total de Jogadores por Personagem",
    template="plotly_dark",
    height=880
)
fig_pop.update_traces(
    marker_color="#1937C0",
    marker_line_color='#FFFFFF',
    marker_line_width=0.5,
    texttemplate='%{x:,.0f}',
    textangle=0,
    textposition="outside",
    hovertemplate="<b>%{y}</b><br>%{x:,.0f} jogadores<extra></extra>"
)
fig_pop.update_layout(
    yaxis={'categoryorder': 'total ascending'},
    margin=dict(l=150, r=50, t=50, b=50),
    xaxis_title=None,
    yaxis_title=None,
    separators=",.",
    xaxis=dict(showgrid=False)
)
st.plotly_chart(fig_pop, use_container_width=True)

# ==========================================
# 🏆 PONTUAÇÃO MÁXIMA POR PERSONAGEM
# ==========================================
st.divider()
st.subheader("🔥 Pontuação Máxima por Personagem")

max_pontos_personagem = df_filtrado.groupby('Personagem', as_index=False)['Pontos AM'].max()
max_pontos_personagem = max_pontos_personagem.sort_values(by='Pontos AM', ascending=True)

fig_max_pontos = px.bar(
    max_pontos_personagem,
    x='Pontos AM',
    y='Personagem',
    orientation='h',
    title="Recorde de Pontos AM",
    template="plotly_dark",
    height=880
)
fig_max_pontos.update_traces(
    marker_color="#24AD1F",
    marker_line_color='#FFFFFF',
    marker_line_width=0.5,
    texttemplate='%{x:,.0f}',
    textposition="outside",
    hovertemplate="<b>%{y}</b><br>Recorde: %{x:,.0f} AM<extra></extra>"
)
fig_max_pontos.update_layout(
    margin=dict(l=150, r=50, t=50, b=50),
    xaxis_title=None,
    yaxis_title=None,
    separators=",.",
    xaxis=dict(showgrid=False)
)
st.plotly_chart(fig_max_pontos, use_container_width=True)

# Aviso de personagens faltantes
total_personagens_base = df['Personagem'].nunique()
personagens_atuais     = df_filtrado['Personagem'].nunique()
faltantes = total_personagens_base - personagens_atuais
if faltantes > 0:
    st.info(f"💡 **Observação:** Baseado nos filtros aplicados, existem **{faltantes}** personagens do jogo que não possuem nenhum jogador representado nestes gráficos.")

st.divider()

# --- LINHA DE PAÍSES ---
st.subheader("🌍 Demografia Global dos Personagens")
st.info("💡 **Observação:** Os dados foram coletados pela bandeira que cada jogador escolheu colocar. O temido Nagoya Kun foi considerado japonês.")

contagem_pais = df_filtrado['País'].value_counts().reset_index()
contagem_pais.columns = ['País', 'Quantidade']

col_pais_1, col_pais_2 = st.columns([0.3, 0.7])

if len(contagem_pais) > 7:
    paises_sem_outros = [p for p in contagem_pais['País'].tolist() if p != 'Outros']
    top_7_lista = paises_sem_outros[:7]
    df_dist_pais = contagem_pais.copy()
    df_dist_pais['País'] = df_dist_pais['País'].apply(lambda x: x if x in top_7_lista else 'Outros')
    df_paises_grafico = df_dist_pais.groupby('País', as_index=False)['Quantidade'].sum()
    ordem_paises = top_7_lista + ['Outros']
    df_paises_grafico['País'] = pd.Categorical(df_paises_grafico['País'], categories=ordem_paises, ordered=True)
    df_paises_grafico = df_paises_grafico.sort_values('País')
else:
    df_paises_grafico = contagem_pais.copy()
    ordem_paises = df_paises_grafico['País'].tolist()

cores_paises_custom = {
    "Japão": "#EB0000", "Estados Unidos": "#1C83E1", "Brasil": "#008000",
    "Coreia do Sul": "#F0F2F6", "França": "#002395", "United Kingdom": "#B10B9B",
    "China": "#AF5501", "Outros": "#555555"
}

with col_pais_1:
    fig_pizza_pais = px.pie(
        df_paises_grafico,
        values='Quantidade',
        names='País',
        color='País',
        color_discrete_map=cores_paises_custom,
        hole=0,
        title="Representatividade Global (%)",
        template="plotly_dark",
        height=500
    )
    fig_pizza_pais.update_traces(
        textfont_color="white", marker_line_color='white', marker_line_width=0.5,
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} personagens<extra></extra>"
    )
    fig_pizza_pais.update_layout(separators=",.")
    st.plotly_chart(fig_pizza_pais, use_container_width=True)

with col_pais_2:
    fig_barras_pais = px.bar(
        df_paises_grafico,
        x='País',
        y='Quantidade',
        color='País',
        color_discrete_map=cores_paises_custom,
        title="Ranking dos países",
        template="plotly_dark",
        height=500
    )
    fig_barras_pais.update_traces(
        texttemplate='%{y:,.0f}', textfont_color="white", textposition="outside",
        marker_line_color='white', marker_line_width=0.5,
        hovertemplate="<b>%{x}</b><br>%{y:,.0f} personagens<extra></extra>"
    )
    fig_barras_pais.update_layout(
        xaxis=dict(categoryorder='array', categoryarray=ordem_paises, showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False, tickformat=','),
        separators=",.", showlegend=False, xaxis_title=None, yaxis_title=None, barmode='group'
    )
    st.plotly_chart(fig_barras_pais, use_container_width=True)

st.divider()

# ==========================================
# 🗺️ MAPA MÚNDI
# ==========================================
dicionario_iso = {
    "Japão": "JPN", "Estados Unidos": "USA", "Brasil": "BRA", "Coreia do Sul": "KOR",
    "França": "FRA", "United Kingdom": "GBR", "Reino Unido": "GBR", "China": "CHN",
    "Canadá": "CAN", "México": "MEX", "Taiwan": "TWN", "Espanha": "ESP",
    "Alemanha": "DEU", "Itália": "ITA", "Austrália": "AUS", "Argentina": "ARG",
    "Chile": "CHL", "Colômbia": "COL", "Peru": "PER", "Porto Rico": "PRI",
    "República Dominicana": "DOM", "Cingapura": "SGP", "Hong Kong": "HKG",
    "Tailândia": "THA", "Malásia": "MYS", "Indonésia": "IDN", "Filipinas": "PHL",
    "Vietnã": "VNM", "Índia": "IND", "Paquistão": "PAK", "Arábia Saudita": "SAU",
    "Emirados Árabes Unidos": "ARE", "África do Sul": "ZAF", "Egito": "EGY",
    "Marrocos": "MAR", "Nigéria": "NGA", "Portugal": "PRT", "Holanda": "NLD",
    "Países Baixos": "NLD", "Bélgica": "BEL", "Suíça": "CHE", "Áustria": "AUT",
    "Suécia": "SWE", "Noruega": "NOR", "Dinamarca": "DNK", "Finlândia": "FIN",
    "Polônia": "POL", "Rússia": "RUS", "Ucrânia": "UKR", "Turquia": "TUR",
    "Grécia": "GRC", "Irlanda": "IRL", "Nova Zelândia": "NZL", "Venezuela": "VEN",
    "Equador": "ECU", "Bolívia": "BOL", "Paraguai": "PRY", "Uruguai": "URY",
    "Costa Rica": "CRI", "Panamá": "PAN", "Guatemala": "GTM", "El Salvador": "SLV",
    "Honduras": "HND", "Nicarágua": "NIC", "Cuba": "CUB", "Jamaica": "JAM",
    "Israel": "ISR", "Kuwait": "KWT", "Catar": "QAT", "Bahrein": "BHR", "Barein": "BHR",
    "Cazaquistão": "KAZ", "Uzbequistão": "UZB", "Sérvia": "SRB", "Croácia": "HRV",
    "Bósnia e Herzegovina": "BIH", "Eslovênia": "SVN", "Eslováquia": "SVK",
    "Tchéquia": "CZE", "República Tcheca": "CZE", "Hungria": "HUN", "Romênia": "ROU",
    "Bulgária": "BGR", "Estônia": "EST", "Letônia": "LVA", "Lituânia": "LTU",
    "Islândia": "ISL", "Macau": "MAC", "Argélia": "DZA", "Algéria": "DZA",
    "Tunísia": "TUN", "Bangladesh": "BGD", "Mongólia": "MNG", "Angola": "AGO",
    "Moçambique": "MOZ", "Quênia": "KEN", "Gana": "GHA", "Senegal": "SEN",
    "Camarões": "CMR", "Costa do Marfim": "CIV", "Madagascar": "MDG", "Zâmbia": "ZMB",
    "Zimbábue": "ZWE", "Uganda": "UGA", "Tanzânia": "TZA", "Etiópia": "ETH",
    "Irã": "IRN", "Iraque": "IRQ", "Síria": "SYR", "Jordânia": "JOR",
    "Líbano": "LBN", "Omã": "OMN", "Iêmen": "YEM", "Afeganistão": "AFG",
    "Nepal": "NPL", "Sri Lanka": "LKA", "Camboja": "KHM", "Mianmar": "MMR",
    "Brunei": "BRN", "Maldivas": "MDV", "Coreia do Norte": "PRK", "Samoa": "WSM",
    "Macedônia": "MKD", "Albânia": "ALB", "Palau": "PLW", "Libéria": "LBR",
    "Trinidad e Tobago": "TTO", "Butão": "BTN", "Serra Leoa": "SLE",
    "Barbados": "BRB", "Santa Lúcia": "LCA", "Chipre": "CYP", "Haiti": "HTI",
    "Seicheles": "SYC", "Somália": "SOM", "Laos": "LAO", "Ilhas Marshall": "MHL",
    "Kiribati": "KIR", "Antígua e Barbuda": "ATG", "Bahamas": "BHS",
    "Geórgia": "GEO", "Micronésia": "FSM", "Guiana": "GUY", "Suazilândia": "SWZ",
    "Bielorrússia": "BLR", "Armênia": "ARM", "Belize": "BLZ", "Sudão": "SDN",
    "Dominica": "DMA", "Grenada": "GRD", "Fiji": "FJI", "Montenegro": "MNE",
    "Tonga": "TON", "Turcomenistão": "TKM", "Gabão": "GAB", "San Marino": "SMR",
    "Papua Nova Guiné": "PNG", "Chade": "TCD", "Benim": "BEN",
    "República do Congo": "COG", "Tuvalu": "TUV", "Botsuana": "BWA",
    "Mônaco": "MCO", "São Vicente e Granadinas": "VCT", "Luxemburgo": "LUX",
    "Quirguistão": "KGZ", "República Democrática do Congo": "COD", "Líbia": "LBY",
    "Níger": "NER", "Suriname": "SUR", "África Central": "CAF", "Malta": "MLT",
    "São Tomé e Príncipe": "STP", "Malaui": "MWI", "Burkina Faso": "BFA",
    "Maurício": "MUS", "Eritreia": "ERI", "Cabo Verde": "CPV", "Azerbaijão": "AZE",
    "Mali": "MLI", "Nauru": "NRU", "São Cristóvão e Névis": "KNA", "Burundi": "BDI",
    "Djibuti": "DJI", "Vanuatu": "VUT", "Lesoto": "LSO", "Guiné-Bissau": "GNB",
    "Ilhas Salomão": "SLB", "Guiné": "GIN", "Comores": "COM", "Liechtenstein": "LIE",
    "Togo": "TGO", "Mauritânia": "MRT", "Moldávia": "MDA", "Andorra": "AND",
    "Namíbia": "NAM", "Tajiquistão": "TJK", "Gâmbia": "GMB", "Timor-Leste": "TLS",
    "Ruanda": "RWA", "Sudão do Sul": "SSD", "Guiné-Equatorial": "GNQ"
}

df_mapa = contagem_pais.copy()
df_mapa['ISO'] = df_mapa['País'].map(dicionario_iso)

# ── Corrigido: nlargest(2) quebra se só houver 1 país ────────────────────────
if len(df_mapa) >= 2:
    limite_cor = df_mapa['Quantidade'].nlargest(2).iloc[-1]
else:
    limite_cor = df_mapa['Quantidade'].max()

fig_mapa = px.choropleth(
    df_mapa,
    locations="ISO",
    color="Quantidade",
    hover_name="País",
    color_continuous_scale="Reds",
    range_color=[0, limite_cor],
    template="plotly_dark",
    title="Mapa de Calor: Concentração Global"
)
fig_mapa.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>%{z:,.0f} personagens<extra></extra>"
)
fig_mapa.update_layout(
    geo=dict(
        showframe=False,
        showcoastlines=True,
        coastlinecolor="gray",
        projection_type='natural earth',
        bgcolor='rgba(0,0,0,0)'
    ),
    margin=dict(l=0, r=0, t=50, b=0),
    height=600
)
st.plotly_chart(fig_mapa, use_container_width=True)

st.divider()

# --- NOVA SEÇÃO: ANÁLISE DE JOGADORES ---
st.header("👤 Perfil dos Jogadores")

jogadores_ativos = df_filtrado['ID'].unique()
df_jogadores_ativos_completo = df[df['ID'].isin(jogadores_ativos)]

total_jogadores = len(jogadores_ativos)
total_registros = len(df_jogadores_ativos_completo)

m1, m2 = st.columns(2)
with m1:
    st.metric("Jogadores Únicos", f"{total_jogadores:,.0f}".replace(",", "."))
with m2:
    # ── Corrigido: divisão por zero se total_jogadores == 0 ──────────────────
    media_char_por_player = total_registros / total_jogadores if total_jogadores > 0 else 0
    st.metric("Média de Personagens por Jogador", f"{media_char_por_player:.2f}")

st.info("""
💡 **Como ler estas métricas:**
* **Jogadores Únicos:** Mostra a quantidade real de pessoas (contas). Se um jogador chegou ao rank Master com 3 personagens diferentes, ele é contado apenas uma vez aqui.
* **Média de Personagens:** Indica quantos personagens diferentes, em média, cada jogador possui a partir do rank Master.
""")

st.divider()

# ==========================================
# 📛 TOP 10 NOMES MAIS UTILIZADOS
# ==========================================
st.subheader("📛 TOP 10 Nomes de Jogadores Mais Comuns")

df_jogadores_unicos = df_filtrado.drop_duplicates(subset=['ID'])

if df_jogadores_unicos.empty:
    st.warning("⚠️ Nenhum dado disponível para os filtros selecionados.")
else:
    top_5_nomes = df_jogadores_unicos['Jogador'].value_counts().head(10).reset_index()
    top_5_nomes.columns = ['Nome do Jogador', 'Quantidade']

    fig_nomes = px.bar(
        top_5_nomes,
        x='Quantidade',
        y='Nome do Jogador',
        orientation='h',
        template="plotly_dark",
        height=300
    )
    fig_nomes.update_traces(
        marker_color="#1C83E1",
        texttemplate='%{x:,.0f}',
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x} jogadores<extra></extra>"
    )
    fig_nomes.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        xaxis_title=None,
        yaxis_title=None,
        separators=",.",
        margin=dict(l=10, r=50, t=10, b=10)
    )
    st.plotly_chart(fig_nomes, use_container_width=True)

st.divider()

# ==========================================
# 🎮 TIPO DE CONTROLE
# ==========================================
st.subheader("🎮 Preferência de Controle (Clássico vs Moderno)")

contagem_controle = df_filtrado['Tipo de Controle'].value_counts().reset_index()
contagem_controle.columns = ['Controle', 'Quantidade']

cores_controle = {"Classic": "#9B26B6", "Modern": "#FF7F00"}

fig_controle = px.pie(
    contagem_controle,
    values='Quantidade',
    names='Controle',
    color='Controle',
    color_discrete_map=cores_controle,
    hole=0,
    template="plotly_dark",
    height=500
)
fig_controle.update_traces(
    textfont_color="white",
    marker_line_color='white',
    marker_line_width=0.5,
    hovertemplate="<b>%{label}</b><br>%{value:,.0f} personagens<extra></extra>"
)
fig_controle.update_layout(
    separators=",.",
    legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5)
)
st.plotly_chart(fig_controle, use_container_width=True)

st.divider()

# ==========================================
# 🤹 MÚLTIPLOS PERSONAGENS
# ==========================================
st.markdown("### 🤹‍♂️ Desempenho com Múltiplos Personagens")
st.info("💡 **Como funciona este filtro:** O botão deslizante abaixo é **exclusivo desta seção**. Ele altera apenas os dois gráficos de 'Top 20' a seguir, ajudando você a descobrir quem são os jogadores mais fortes que dominam vários personagens ao mesmo tempo.")

contagem_multi_chars = df_jogadores_ativos_completo.groupby(['ID', 'Jogador'], as_index=False)['Personagem'].count()
contagem_multi_chars.columns = ['ID', 'Jogador', 'Qtd Personagens']

min_chars = st.slider(
    "Quantidade mínima de personagens utilizados pelo jogador:",
    min_value=1, max_value=29, value=5,
    help="Arraste para filtrar apenas os jogadores que utilizam essa quantidade (ou mais) de personagens nos ranques altos."
)

jogadores_validos = contagem_multi_chars[contagem_multi_chars['Qtd Personagens'] >= min_chars]
jogadores_acima_filtro = len(jogadores_validos)

st.success(f"🎯 **{jogadores_acima_filtro} jogadores** na seleção atual possuem **{min_chars} ou mais** personagens de Rank Master ou Superior.")

col_jog_1, col_jog_2 = st.columns(2)

with col_jog_1:
    st.subheader("🏆 Top 20: Mais Personagens")
    if jogadores_acima_filtro > 0:
        top_multi = jogadores_validos.sort_values(by='Qtd Personagens', ascending=False).head(20)
        fig_multi = px.bar(
            top_multi, x='Qtd Personagens', y='Jogador', orientation='h',
            template="plotly_dark", height=600, text_auto=True
        )
        fig_multi.update_traces(
            marker_color="#E53935",
            textfont_color="white",
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>%{x} personagens<extra></extra>"
        )
        fig_multi.update_layout(
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'},
            xaxis={'showgrid': False, 'zeroline': False},
            xaxis_title=None, yaxis_title=None,
            margin=dict(r=50)
        )
        st.plotly_chart(fig_multi, use_container_width=True)
    else:
        st.warning(f"Nenhum jogador possui {min_chars} ou mais personagens com os filtros atuais.")

with col_jog_2:
    st.subheader("📈 Top 20: Média de Pontos")
    if jogadores_acima_filtro > 0:
        df_validos  = df_jogadores_ativos_completo[df_jogadores_ativos_completo['ID'].isin(jogadores_validos['ID'])]
        top_media   = df_validos.groupby(['ID', 'Jogador'], as_index=False)['Pontos AM'].mean()
        top_media.columns = ['ID', 'Jogador', 'Média Pontos']
        top_media   = top_media.sort_values(by='Média Pontos', ascending=False).head(20)
        top_media['Média Pontos'] = top_media['Média Pontos'].astype(int)
        top_media   = top_media.merge(jogadores_validos[['ID', 'Qtd Personagens']], on='ID')
        top_media['Jogador (Qtd)'] = top_media['Jogador'] + " (" + top_media['Qtd Personagens'].astype(str) + " chars)"
        top_media['Texto_Barra']   = top_media['Média Pontos'].apply(lambda x: f"{x:,.0f} AM".replace(",", "."))

        fig_media = px.bar(
            top_media, x='Média Pontos', y='Jogador (Qtd)', orientation='h',
            template="plotly_dark", height=600, text='Texto_Barra'
        )
        fig_media.update_traces(
            marker_color="#1E88E5",
            textfont_color="white",
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>%{x:,.0f} pontos AM médios<extra></extra>"
        )
        fig_media.update_layout(
            separators=",.",
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'},
            xaxis={'showgrid': False, 'zeroline': False},
            xaxis_title=None, yaxis_title=None,
            margin=dict(r=100)
        )
        st.plotly_chart(fig_media, use_container_width=True)
    else:
        st.warning(f"Nenhum jogador possui {min_chars} ou mais personagens com os filtros atuais.")

# ==========================================
# ⏳ TOP 10: MAIORES GRINDERS
# ==========================================
st.divider()
st.subheader("⏳ Top 10: Jogadores Com Maior Tempo de Jogo")
st.caption("Descubra quem são os jogadores mais dedicados.")

df_tempos = (
    df_filtrado[['Jogador', 'Tempo Total', 'Tempo de Fighting Ground', 'Tempo de Battle Hub']]
    .drop_duplicates(subset=['Jogador'])
    .dropna()
)

# ── Corrigido: bloco inteiro dentro do if para evitar crash com df vazio ──────
if df_tempos.empty:
    st.warning("⚠️ Nenhum dado de tempo de jogo disponível para os filtros selecionados.")
else:
    aba_total, aba_fg, aba_bh = st.tabs(["🕒 Tempo Total", "🥊 Fighting Ground", "🌐 Battle Hub"])

    with aba_total:
        top10_total = df_tempos.nlargest(10, 'Tempo Total')
        grafico_total = alt.Chart(top10_total).mark_bar().encode(
            x=alt.X('Tempo Total:Q', title='Horas Jogadas'),
            y=alt.Y('Jogador:N', sort='-x', title='Jogador'),
            tooltip=['Jogador', 'Tempo Total']
        ).properties(height=400)
        st.altair_chart(grafico_total, use_container_width=True)

    with aba_fg:
        top10_fg = df_tempos.nlargest(10, 'Tempo de Fighting Ground')
        grafico_fg = alt.Chart(top10_fg).mark_bar(color='#E53935').encode(
            x=alt.X('Tempo de Fighting Ground:Q', title='Horas no Fighting Ground'),
            y=alt.Y('Jogador:N', sort='-x', title='Jogador'),
            tooltip=['Jogador', 'Tempo de Fighting Ground']
        ).properties(height=400)
        st.altair_chart(grafico_fg, use_container_width=True)

    with aba_bh:
        top10_bh = df_tempos.nlargest(10, 'Tempo de Battle Hub')
        grafico_bh = alt.Chart(top10_bh).mark_bar(color='#1E88E5').encode(
            x=alt.X('Tempo de Battle Hub:Q', title='Horas no Battle Hub'),
            y=alt.Y('Jogador:N', sort='-x', title='Jogador'),
            tooltip=['Jogador', 'Tempo de Battle Hub']
        ).properties(height=400)
        st.altair_chart(grafico_bh, use_container_width=True)

st.write("")
st.info("""
💡 **Contagem de tempo:**
Nas páginas que foram coletados esses dados, a Capcom divulga o tempo de jogo dividido nestas 3 categorias. Não sei se as Rankeds vão para tempo total ou Fighting Ground.

*O **Winter** possui Tempo Total = **950.5 horas**, Fighting Ground = **18.4h** e Battle Hub = **0h**.
""")

# ==========================================
# 🔍 BUSCA POR JOGADOR
# ==========================================
# st.divider()
# st.subheader("🔍 Consultar Ficha Completa do Jogador")

# st.info("""
# *⚠️ **Aviso de Performance:** Esta busca vasculha uma quantidade massiva de dados. Pode levar alguns segundos para processar e carregar após o primeiro click, mas funciona perfeitamente! Se filtrar por país antes, fica bem mais rápido.

# *🏆 **Dica Estratégica:** Investigue os dados do seu oponente antes de partidas em campeonatos.
# """)

# df_busca = df_filtrado[['ID', 'Jogador']].drop_duplicates().dropna()
# df_busca['Opcao_Busca'] = df_busca['ID'].astype(str) + " - " + df_busca['Jogador'].astype(str)
# lista_busca = sorted(df_busca['Opcao_Busca'].tolist())

# busca_selecionada = st.selectbox(
#     "Selecione ou digite o ID ou Nome do jogador:",
#     options=[""] + lista_busca
# )

# if busca_selecionada:
#     id_selecionado = busca_selecionada.split(" - ")[0]
#     dados_jogador  = df_jogadores[df_jogadores['ID'] == id_selecionado]

#     if not dados_jogador.empty:
#         row = dados_jogador.iloc[0]
#         st.success(f"Exibindo: **{row['Jogador']}** (ID: {id_selecionado})")

#         c_p1, c_p2 = st.columns([0.4, 0.6])
#         with c_p1:
#             st.write(f"🌍 **País:** {row['País']}")
#             st.write(f"🎮 **Personagem Principal:** {row['Personagem_Principal']}")
#             st.write(f"🏆 **Maior Pontuação:** {row['MR_Maximo']:,.0f} AM".replace(",", "."))
#             st.write(f"📊 **Total de Personagens:** {row['Total_Personagens']}")
#             st.write(f"⚖️ **Média Geral:** {row['Media_MR']:,.0f} AM".replace(",", "."))

#         with c_p2:
#             st.markdown("**Dados dos personagens utilizados:**")

#             # Reconstrói a tabela a partir da string armazenada
#             personagens = []
#             for item in row['Personagens_Str'].split("|"):
#                 partes = item.split(";")
#                 if len(partes) == 4:
#                     personagens.append({
#                         "Personagem":       partes[0],
#                         "Rank":             partes[1],
#                         "Tipo de Controle": partes[2],
#                         "Pontos AM":        f"{int(partes[3]):,.0f}".replace(",", ".")
#                     })

#             if personagens:
#                 st.dataframe(
#                     pd.DataFrame(personagens),
#                     hide_index=True,
#                     use_container_width=True
#                 )
#             else:
#                 st.info("Nenhum detalhe de personagem disponível.")
#     else:
#         st.error(f"Não foi possível localizar os detalhes para o ID {id_selecionado}.")