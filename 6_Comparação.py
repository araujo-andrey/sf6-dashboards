import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ══════════════════════════════════════════════════════════════════════════════
# ⚙️  CONFIGURAÇÃO — IDs dos jogadores
# ══════════════════════════════════════════════════════════════════════════════
JOGADOR_PRINCIPAL_ID = "4125616529"  # Winter

PRO_PLAYERS_IDS = [
    "1304761987",  # Leshar
    "1224217951",  # Punk
    "3400122682",  # kincho
    "3466993951",  # kosaku
    "1659765966",  # Kawano
    "2862828890",  # Kakeru
    "3381453962",  # Blaz
    "3631316984",  # Kyuki
    "2616132292",  # NotPedro
]

TODOS_IDS = [JOGADOR_PRINCIPAL_ID] + PRO_PLAYERS_IDS

# ── Tier list e Arquétipos padrão (ajuste conforme necessário) ────────────────
ORDEM_TIER  = ["S+","S","A","B","C","D","E"]
ORDEM_NIVEL = ["Muito Inferior","Inferior","Similar","Superior","Muito Superior"]

TIER_MAP = {
    "JP":"S+","Ed":"S+",
    "Blanka":"S","Sagat":"S","M. Bison":"S","Terry":"S","Mai":"S",
    "Akuma":"S","Guile":"S","Rashid":"S","C. Viper":"S",
    "Dee Jay":"A","Ryu":"A","Kimberly":"A","Juri":"A","Dhalsim":"A",
    "Ken":"A","Cammy":"A","Zangief":"A","Alex":"A",
    "Chun-Li":"B","Jamie":"B","Luke":"B","Elena":"B","A.K.I.":"B",
    "Manon":"C","Lily":"C","Edmond Honda":"C",
    "Marisa":"D",
}

ARQ_MAP = {
    "Ryu":"All-Rounder","Ken":"All-Rounder","Akuma":"All-Rounder",
    "Terry":"All-Rounder","Ed":"All-Rounder","Mai":"All-Rounder",
    "Luke":"All-Rounder","Chun-Li":"All-Rounder","Sagat":"All-Rounder",
    "Cammy":"Rushdown","Juri":"Rushdown","Kimberly":"Rushdown",
    "Rashid":"Rushdown","Dee Jay":"Rushdown","Jamie":"Rushdown","M. Bison":"Rushdown",
    "Zangief":"Grappler","Marisa":"Grappler","Manon":"Grappler",
    "Lily":"Grappler","Alex":"Grappler",
    "Guile":"Zoner","Dhalsim":"Zoner","JP":"Zoner",
    "Elena":"Unorthodox","A.K.I.":"Unorthodox","Blanka":"Unorthodox",
    "Edmond Honda":"Unorthodox","C. Viper":"Unorthodox",
}

CORES_TIER = {
    "S+":"#8C00FF","S":"#FF0000","A":"#FF9100",
    "B":"#DEEE05","C":"#63F52A","D":"#308F0B","E":"#2C3E50",
}

# Limites de nível (diferença de MR)
LIM_MUITO_INF = -200
LIM_INF       = -51
LIM_SUP       =  51
LIM_MUITO_SUP =  101

# ══════════════════════════════════════════════════════════════════════════════
# ⚙️  PÁGINA
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="SF6 – Comparativo Pro Players", layout="wide", page_icon="🏆")
st.title("🏆 Comparativo — Winter vs Pro Players")
st.caption("Comparação baseada nos dados ranqueados disponíveis. Pro players têm volumes variados de partidas — interprete com cautela.")

# ══════════════════════════════════════════════════════════════════════════════
# 📥  CARREGAMENTO DA LISTA DE IDs
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data
def carregar_todos():
    jogadores = {}
    for jogador_id in TODOS_IDS:
        arquivo = f"SF6_historico_LIMPO_{jogador_id}.csv"
        try:
            df = pd.read_csv(arquivo)
            df['Data_Datetime'] = pd.to_datetime(df['Data'])
            df['Meu_MR']        = pd.to_numeric(df['Meu_MR'],       errors='coerce').fillna(0).astype(int)
            df['Oponente_MR']   = pd.to_numeric(df['Oponente_MR'],  errors='coerce').fillna(0).astype(int)
            df['Diferenca_MR']  = pd.to_numeric(df['Diferenca_MR'], errors='coerce').fillna(0).astype(int)
            df['Mirror_Match']  = df['Mirror_Match'].astype(str).str.lower().isin(['true','1','sim'])
            df['Tier_Oponente'] = df['Oponente_Personagem'].map(TIER_MAP).fillna("?")
            df['Arq_Oponente']  = df['Oponente_Personagem'].map(ARQ_MAP).fillna("Desconhecido")
            df['Nivel_Oponente']= df['Diferenca_MR'].apply(classificar_nivel)
            nome = df['Meu_Nome'].iloc[0]
            jogadores[nome] = {
                "df":        df,
                "id":        jogador_id,
                "principal": jogador_id == JOGADOR_PRINCIPAL_ID,
            }
        except FileNotFoundError:
            st.sidebar.warning(f"⚠️ Não encontrado: SF6_historico_LIMPO_{jogador_id}.csv")
    return jogadores

def classificar_nivel(d):
    if d <= LIM_MUITO_INF:  return "Muito Inferior"
    elif d <= LIM_INF:      return "Inferior"
    elif d <  LIM_SUP:      return "Similar"
    elif d <  LIM_MUITO_SUP:return "Superior"
    else:                   return "Muito Superior"

def wr(df):
    t = len(df)
    return (df['Meu_Resultado'] == "Vitória 🏆").sum() / t * 100 if t > 0 else 0.0

def amostra_tag(n):
    if n < 50:  return "⚠️ muito pequena"
    if n < 150: return "⚠️ pequena"
    return "✅ ok"

jogadores = carregar_todos()

if not jogadores:
    st.error("Nenhum arquivo encontrado. Verifique os IDs e os CSVs na pasta.")
    st.stop()

nomes_todos    = list(jogadores.keys())
nome_principal = next((n for n, d in jogadores.items() if d["principal"]), nomes_todos[0])
nomes_pros     = [n for n in nomes_todos if n != nome_principal]

# ══════════════════════════════════════════════════════════════════════════════
# 🎛️  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
st.sidebar.header("🎛️ Configurações")
pros_selecionados = st.sidebar.multiselect(
    "Pro Players para comparar:",
    options=nomes_pros, default=nomes_pros, placeholder="Selecione..."
)
filtro_modo = st.sidebar.selectbox(
    "Modo de Jogo:", options=["Todos","Ranqueada","Casual"], index=0
)
if st.sidebar.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

if not pros_selecionados:
    st.warning("Selecione ao menos um pro player na barra lateral.")
    st.stop()

nomes_comparar = [nome_principal] + pros_selecionados

def filtrar(df):
    if filtro_modo == "Todos": return df
    return df[df['Tipo Partida (Jogo)'] == filtro_modo]

# Paleta de cores — Winter sempre dourado
paleta = px.colors.qualitative.Set2
cores_jogadores = {}
for i, nome in enumerate(nomes_comparar):
    cores_jogadores[nome] = "#FFD700" if jogadores[nome]["principal"] else paleta[i % len(paleta)]

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 1 — VISÃO GERAL
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 📊 Visão Geral")

rows = []
for nome in nomes_comparar:
    d   = jogadores[nome]
    df  = filtrar(d["df"])
    dfr = df[df['Tipo Partida (Jogo)'] == 'Ranqueada']
    char_prin = df['Meu_Personagem'].value_counts().index[0] if len(df) > 0 else "—"
    rows.append({
        "Jogador":      f"⭐ {nome}" if d["principal"] else nome,
        "Personagem":   char_prin,
        "Win Rate (%)": f"{wr(df):.1f}%",
        "WR_num":       wr(df),
        "MR Máximo":    int(dfr['Meu_MR'].max()) if len(dfr) > 0 else 0,
        "Partidas":     len(df),
        "Amostra":      amostra_tag(len(df)),
    })

df_visao = pd.DataFrame(rows).sort_values("WR_num", ascending=False)
st.dataframe(
    df_visao[["Jogador","Personagem","Win Rate (%)","MR Máximo","Partidas","Amostra"]],
    use_container_width=True, hide_index=True
)
st.info("⭐ = Winter (jogador principal)  ·  ✅ ≥ 150 partidas  ·  ⚠️ < 150 partidas — resultados menos confiáveis.")

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 2 — WIN RATE GERAL
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🎯 Win Rate — A Variância é Normal Mesmo nos Tops?")
st.caption(
    "Mesmo top players ficam longe de 100%. Perder partidas é estrutural do Street Fighter — "
    "o formato curto (FT2) garante alta variância independente do nível."
)

df_wr = pd.DataFrame([{
    "Jogador":  nome,
    "WR":       wr(filtrar(jogadores[nome]["df"])),
    "Partidas": len(filtrar(jogadores[nome]["df"])),
} for nome in nomes_comparar]).sort_values("WR", ascending=True)

fig_wr = go.Figure()
for _, row in df_wr.iterrows():
    fig_wr.add_trace(go.Bar(
        x=[row["WR"]], y=[row["Jogador"]],
        orientation='h',
        marker_color=cores_jogadores.get(row["Jogador"], "#888"),
        text=[f"{row['WR']:.1f}%"],
        textposition="outside", textfont_color="white",
        customdata=[[row["Partidas"]]],
        hovertemplate=f"<b>{row['Jogador']}</b><br>Win Rate: {row['WR']:.1f}%<br>%{{customdata[0]}} partidas<extra></extra>"
    ))
fig_wr.add_vline(x=50, line_dash="dot", line_color="white")
fig_wr.update_layout(
    template="plotly_dark", height=60 + 45 * len(df_wr),
    showlegend=False,
    xaxis=dict(range=[0,100], title="Win Rate (%)"),
    yaxis_title="",
    margin=dict(l=10, r=60, t=20, b=10)
)
st.plotly_chart(fig_wr, use_container_width=True)
st.caption("🟡 Dourado = Winter  ·  Linha tracejada = 50%")

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 3 — DISTRIBUIÇÃO DE TRAJETÓRIAS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🔄 Distribuição de Trajetórias de Partida")
st.caption(
    "Se até os pro players têm muitas sequências D-D e V-D-D, "
    "isso confirma que a variância alta é estrutural do jogo — não uma fraqueza individual."
)

trad = {
    "V-V":"Vitória Limpa 2-0","V-D-V":"Vitória Suada 2-1","D-V-V":"Virada Épica 2-1",
    "D-D":"Derrota Limpa 0-2","D-V-D":"Reagiu mas Perdeu 1-2","V-D-D":"Tomou Virada 1-2",
}
cores_seq = {
    "Vitória Limpa 2-0":"#19a50d","Vitória Suada 2-1":"#005fcc","Virada Épica 2-1":"#9c00cc",
    "Derrota Limpa 0-2":"#ac1f06","Reagiu mas Perdeu 1-2":"#4d2d27","Tomou Virada 1-2":"#efec3b",
}

rows_seq = []
for nome in nomes_comparar:
    df    = filtrar(jogadores[nome]["df"])
    total = len(df)
    if total == 0: continue
    for seq, desc in trad.items():
        qtd = (df['Sequencia_Rounds'] == seq).sum()
        rows_seq.append({
            "Jogador":    nome,
            "Sequência":  desc,
            "Proporção":  round(qtd / total * 100, 1),
            "Quantidade": int(qtd),
        })

df_seq = pd.DataFrame(rows_seq)
if not df_seq.empty:
    fig_seq = px.bar(
        df_seq, x="Jogador", y="Proporção", color="Sequência",
        barmode="stack", template="plotly_dark", height=420,
        color_discrete_map=cores_seq, custom_data=["Quantidade"]
    )
    fig_seq.update_traces(
        hovertemplate="<b>%{fullData.name}</b><br>%{y:.1f}% (%{customdata[0]} partidas)<extra></extra>"
    )
    fig_seq.update_layout(
        yaxis_title="Proporção (%)", xaxis_title="",
        legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center"),
        margin=dict(l=10, r=10, t=20, b=10)
    )
    st.plotly_chart(fig_seq, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 4 — IMPACTO DO 1º ROUND
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🥇 Impacto do 1º Round")
st.caption("O 1º round é decisivo para todos ou é uma característica específica do Winter?")

rows_r1 = []
for nome in nomes_comparar:
    df  = filtrar(jogadores[nome]["df"])
    dfv = df[df['Venceu_Primeiro_Round'] == 'Sim']
    dfp = df[df['Venceu_Primeiro_Round'] == 'Não']
    rows_r1.append({
        "Jogador":            nome,
        "WR se vencer 1º R":  round(wr(dfv), 1),
        "WR se perder 1º R":  round(wr(dfp), 1),
        "Diferença (pp)":     round(wr(dfv) - wr(dfp), 1),
    })

df_r1 = pd.DataFrame(rows_r1).sort_values("Diferença (pp)", ascending=False)

cr1, cr2 = st.columns(2)
for col, campo, cor_base, titulo in [
    (cr1, "WR se vencer 1º R", "#00cc96", "Win Rate SE vencer o 1º Round"),
    (cr2, "WR se perder 1º R", "#ef553b", "Win Rate SE perder o 1º Round"),
]:
    with col:
        fig = go.Figure()
        for _, row in df_r1.sort_values(campo, ascending=True).iterrows():
            cor = "#FFD700" if jogadores[row["Jogador"]]["principal"] else cor_base
            fig.add_trace(go.Bar(
                x=[row[campo]], y=[row["Jogador"]],
                orientation='h', marker_color=cor,
                text=[f"{row[campo]:.1f}%"],
                textposition="outside", textfont_color="white",
                hovertemplate=f"<b>{row['Jogador']}</b><br>{titulo}: {row[campo]:.1f}%<extra></extra>"
            ))
        fig.update_layout(
            title=titulo, template="plotly_dark",
            height=60 + 45 * len(df_r1), showlegend=False,
            xaxis=dict(range=[0,115], title="Win Rate (%)"),
            yaxis_title="", margin=dict(l=10, r=60, t=40, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

st.dataframe(df_r1, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 5 — WIN RATE POR TIER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🏆 Win Rate por Tier do Oponente")
st.caption("Todos sofrem mais contra S+ e S? Ou é específico de alguns jogadores?")

rows_tier = []
for nome in nomes_comparar:
    df = filtrar(jogadores[nome]["df"])
    if len(df) == 0: continue
    for tier in ORDEM_TIER:
        sub = df[df['Tier_Oponente'] == tier]
        if len(sub) < 3: continue
        rows_tier.append({
            "Jogador":  nome,
            "Tier":     tier,
            "WR":       round(wr(sub), 1),
            "Partidas": len(sub),
        })

df_tier = pd.DataFrame(rows_tier)
if not df_tier.empty:
    fig_tier = px.line(
        df_tier, x="Tier", y="WR", color="Jogador",
        markers=True, template="plotly_dark", height=400,
        category_orders={"Tier": ORDEM_TIER},
        color_discrete_map=cores_jogadores,
        custom_data=["Partidas"]
    )
    fig_tier.update_traces(
        hovertemplate="<b>%{fullData.name}</b><br>Tier %{x}: %{y:.1f}%<br>%{customdata[0]} partidas<extra></extra>"
    )
    fig_tier.update_layout(
        yaxis_title="Win Rate (%)", xaxis_title="Tier do Oponente",
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
        margin=dict(l=10, r=10, t=20, b=10)
    )
    st.plotly_chart(fig_tier, use_container_width=True)
    st.caption("🟡 Dourado = Winter  ·  Tiers com menos de 3 partidas são omitidos.")

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 6 — WIN RATE POR ARQUÉTIPO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🥋 Win Rate por Arquétipo do Oponente")
st.caption("Grapplers são difíceis para todos ou só para alguns? Zoners são fáceis de lidar?")

arquetipos_ordem = ["All-Rounder","Rushdown","Grappler","Zoner","Unorthodox"]
rows_arq = []
for nome in nomes_comparar:
    df = filtrar(jogadores[nome]["df"])
    if len(df) == 0: continue
    for arq in arquetipos_ordem:
        sub = df[df['Arq_Oponente'] == arq]
        if len(sub) < 3: continue
        rows_arq.append({
            "Jogador":   nome,
            "Arquétipo": arq,
            "WR":        round(wr(sub), 1),
            "Partidas":  len(sub),
        })

df_arq = pd.DataFrame(rows_arq)
if not df_arq.empty:
    fig_arq = px.line(
        df_arq, x="Arquétipo", y="WR", color="Jogador",
        markers=True, template="plotly_dark", height=400,
        category_orders={"Arquétipo": arquetipos_ordem},
        color_discrete_map=cores_jogadores,
        custom_data=["Partidas"]
    )
    fig_arq.update_traces(
        hovertemplate="<b>%{fullData.name}</b><br>%{x}: %{y:.1f}%<br>%{customdata[0]} partidas<extra></extra>"
    )
    fig_arq.update_layout(
        yaxis_title="Win Rate (%)", xaxis_title="Arquétipo do Oponente",
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
        margin=dict(l=10, r=10, t=20, b=10)
    )
    st.plotly_chart(fig_arq, use_container_width=True)
    st.caption("🟡 Dourado = Winter  ·  Arquétipos com menos de 3 partidas são omitidos.")

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 7 — WIN RATE POR NÍVEL DO OPONENTE
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🎯 Win Rate por Nível do Oponente")
st.caption(
    "Nível baseado na diferença de MR antes da partida. "
    "Todos performam pior contra oponentes muito superiores? "
    "Ou o Winter sofre mais que os tops nessa faixa?"
)

rows_nivel = []
for nome in nomes_comparar:
    df = filtrar(jogadores[nome]["df"])
    if len(df) == 0: continue
    for nivel in ORDEM_NIVEL:
        sub = df[df['Nivel_Oponente'] == nivel]
        if len(sub) < 3: continue
        rows_nivel.append({
            "Jogador":  nome,
            "Nível":    nivel,
            "WR":       round(wr(sub), 1),
            "Partidas": len(sub),
        })

df_nivel = pd.DataFrame(rows_nivel)
if not df_nivel.empty:
    fig_nivel = px.line(
        df_nivel, x="Nível", y="WR", color="Jogador",
        markers=True, template="plotly_dark", height=400,
        category_orders={"Nível": ORDEM_NIVEL},
        color_discrete_map=cores_jogadores,
        custom_data=["Partidas"]
    )
    fig_nivel.update_traces(
        hovertemplate="<b>%{fullData.name}</b><br>%{x}: %{y:.1f}%<br>%{customdata[0]} partidas<extra></extra>"
    )
    fig_nivel.update_layout(
        yaxis_title="Win Rate (%)", xaxis_title="Nível do Oponente",
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
        margin=dict(l=10, r=10, t=20, b=10)
    )
    st.plotly_chart(fig_nivel, use_container_width=True)
    st.caption("🟡 Dourado = Winter  ·  Níveis com menos de 3 partidas são omitidos.")

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 8 — MIRROR MATCH
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🪞 Mirror Match")
st.caption("Como cada jogador performa nos confrontos espelhados?")

rows_mir = []
for nome in nomes_comparar:
    df     = filtrar(jogadores[nome]["df"])
    df_mir = df[df['Mirror_Match'] == True]
    df_nor = df[df['Mirror_Match'] == False]
    if len(df) == 0: continue
    rows_mir.append({
        "Jogador":          nome,
        "WR Mirror":        round(wr(df_mir), 1) if len(df_mir) > 0 else None,
        "WR Não-Mirror":    round(wr(df_nor), 1) if len(df_nor) > 0 else None,
        "Mirrors":          len(df_mir),
        "Delta (pp)":       round(wr(df_mir) - wr(df_nor), 1) if len(df_mir) > 0 and len(df_nor) > 0 else None,
    })

df_mir_view = pd.DataFrame(rows_mir).sort_values("WR Mirror", ascending=False)

cm1, cm2 = st.columns(2)
with cm1:
    fig_mir = go.Figure()
    for _, row in df_mir_view.sort_values("WR Mirror", ascending=True).iterrows():
        if pd.isna(row["WR Mirror"]): continue
        cor = "#FFD700" if jogadores[row["Jogador"]]["principal"] else "#9c00cc"
        fig_mir.add_trace(go.Bar(
            x=[row["WR Mirror"]], y=[row["Jogador"]],
            orientation='h', marker_color=cor,
            text=[f"{row['WR Mirror']:.1f}%"],
            textposition="outside", textfont_color="white",
            customdata=[[row["Mirrors"]]],
            hovertemplate=f"<b>{row['Jogador']}</b><br>Win Rate Mirror: {row['WR Mirror']:.1f}%<br>%{{customdata[0]}} mirrors<extra></extra>"
        ))
    fig_mir.update_layout(
        title="Win Rate em Mirrors",
        template="plotly_dark", height=60 + 45*len(df_mir_view),
        showlegend=False,
        xaxis=dict(range=[0,115], title="Win Rate (%)"),
        yaxis_title="", margin=dict(l=10, r=60, t=40, b=10)
    )
    st.plotly_chart(fig_mir, use_container_width=True)

with cm2:
    st.write(""); st.write("")
    st.dataframe(
        df_mir_view[["Jogador","WR Mirror","WR Não-Mirror","Mirrors","Delta (pp)"]],
        use_container_width=True, hide_index=True
    )
    st.caption("Delta = WR Mirror − WR Não-Mirror. Positivo = performa melhor em mirrors.")

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 9 — WIN RATE CONTRA CADA PERSONAGEM
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🥊 Win Rate contra cada Personagem")
st.caption("Selecione um personagem para comparar como cada jogador performa contra ele.")

# Pega todos os personagens presentes nos dados
todos_chars = sorted(set(
    c for nome in nomes_comparar
    for c in jogadores[nome]["df"]['Oponente_Personagem'].dropna().unique()
))

char_selecionado = st.selectbox(
    "Selecione o personagem do oponente:",
    options=todos_chars,
    index=0
)

rows_char = []
for nome in nomes_comparar:
    df  = filtrar(jogadores[nome]["df"])
    sub = df[df['Oponente_Personagem'] == char_selecionado]
    rows_char.append({
        "Jogador":  nome,
        "WR":       round(wr(sub), 1) if len(sub) > 0 else None,
        "Partidas": len(sub),
    })

df_char = pd.DataFrame(rows_char).dropna(subset=["WR"]).sort_values("WR", ascending=True)

if df_char.empty:
    st.info(f"Nenhum jogador enfrentou {char_selecionado} com os filtros atuais.")
else:
    fig_char = go.Figure()
    for _, row in df_char.iterrows():
        cor = "#FFD700" if jogadores[row["Jogador"]]["principal"] else "#4ECDC4"
        fig_char.add_trace(go.Bar(
            x=[row["WR"]], y=[row["Jogador"]],
            orientation='h', marker_color=cor,
            text=[f"{row['WR']:.1f}%"],
            textposition="outside", textfont_color="white",
            customdata=[[row["Partidas"]]],
            hovertemplate=f"<b>{row['Jogador']}</b><br>Win Rate vs {char_selecionado}: {row['WR']:.1f}%<br>%{{customdata[0]}} partidas<extra></extra>"
        ))
    fig_char.add_vline(x=50, line_dash="dot", line_color="white")
    fig_char.update_layout(
        title=f"Win Rate contra {char_selecionado}",
        template="plotly_dark", height=60 + 45*len(df_char),
        showlegend=False,
        xaxis=dict(range=[0,115], title="Win Rate (%)"),
        yaxis_title="", margin=dict(l=10, r=60, t=40, b=10)
    )
    st.plotly_chart(fig_char, use_container_width=True)
    st.dataframe(
        df_char[["Jogador","WR","Partidas"]].rename(columns={"WR":"Win Rate (%)"}),
        use_container_width=True, hide_index=True
    )

# ══════════════════════════════════════════════════════════════════════════════
# ══  AVISO FINAL
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.info(
    "⚠️ **Atenção na interpretação:** jogadores com menos de 150 partidas têm maior margem de erro. "
    "As comparações mais confiáveis são Win Rate Geral, Impacto do 1º Round e Trajetórias de Partida. "
    "Métricas granulares (por personagem, tier, arquétipo) exigem pelo menos 20 partidas por categoria."
)