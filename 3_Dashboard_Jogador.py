import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_sortables import sort_items
import os
from PIL import Image


# ══════════════════════════════════════════════════════════════════════════════
# ⚙️  PÁGINA
# ══════════════════════════════════════════════════════════════════════════════
JOGADOR_ID = "4125616529"
ARQUIVO    = f"SF6_historico_LIMPO_{JOGADOR_ID}.parquet"

st.set_page_config(
    page_title="SF6 – Análise de Desempenho",
    layout="wide",
    page_icon="❄️"
)
st.title("📊 Análise de Desempenho – Street Fighter 6")

with st.expander("📌 Informações sobre a Base de Dados", expanded=False):
    st.markdown("""
    * ⚠️ **Limite:** A Capcom disponibiliza apenas as últimas 100 partidas por modo de jogo.
    * 🔄 **Coleta:** Dados extraídos periodicamente via script de automação.
    * 📅 **Período coberto:** A partir de **20/04/2026**.
    * 🔌 **Rage Quit:** Partidas por desconexão geralmente não são registradas.
    """)

# ══════════════════════════════════════════════════════════════════════════════
# 🗂️  DEFAULTS
# ══════════════════════════════════════════════════════════════════════════════
ORDEM_NIVEL = ["Muito Inferior","Inferior","Similar","Superior","Muito Superior"]
ORDEM_TIER  = ["S+","S","A","B","C","D","E"]

ARQUETIPOS_PADRAO = {
    "All-Rounder": ["Ryu","Ken","Akuma","Terry","Ed","Mai","Luke","Chun-Li","Sagat"],
    "Rushdown":    ["Cammy","Juri","Kimberly","Rashid","Dee Jay","Jamie","M. Bison"],
    "Grappler":    ["Zangief","Marisa","Manon","Lily","Alex"],
    "Zoner":       ["Guile","Dhalsim","JP", "Ingrid"],
    "Unorthodox":  ["Elena","A.K.I.","Blanka","Edmond Honda","C. Viper"],
}

TIER_PADRAO = {
    "S+": ["JP","Ed"],
    "S":  ["Blanka","Sagat","M. Bison","Terry","Mai","Akuma","Guile","Rashid","C. Viper", "Ingrid"],
    "A":  ["Dee Jay","Ryu","Kimberly","Juri","Dhalsim","Ken","Cammy","Zangief","Alex"],
    "B":  ["Chun-Li","Jamie","Luke","Elena","A.K.I."],
    "C":  ["Manon","Lily","Edmond Honda"],
    "D":  ["Marisa"],
    "E":  [],
}

TODOS_PERSONAGENS = sorted([p for v in ARQUETIPOS_PADRAO.values() for p in v])

TODOS_CHARS_SF6 = sorted([
    "A.K.I.", "Akuma", "Alex", "Blanka", "Cammy", "Chun-Li", "C. Viper",
    "Dee Jay", "Dhalsim", "Ed", "Edmond Honda", "Elena", "Guile", "Jamie",
    "JP", "Juri", "Ken", "Kimberly", "Lily", "Luke", "M. Bison", "Mai",
    "Manon", "Marisa", "Rashid", "Ryu", "Sagat", "Terry", "Zangief", "Ingrid"
])

CORES_TIER = {
    "S+": "#8C00FF", "S": "#FF0000", "A": "#FF9100",
    "B":  "#DEEE05", "C": "#63F52A", "D": "#308F0B", "E": "#2C3E50",
}

# ══════════════════════════════════════════════════════════════════════════════
# ⚙️  SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
def init_state():
    defaults = {
        'arq_config':    {k: list(v) for k,v in ARQUETIPOS_PADRAO.items()},
        'tier_config':   {k: list(v) for k,v in TIER_PADRAO.items()},
        'wr_verde':      55,
        'wr_amarelo':    45,
        'lim_muito_inf': -200,
        'lim_inf':       -50,
        'lim_sup':        50,
        'lim_muito_sup':  100,
        'cols_ativas': {
            "Tier": True, "Arquétipo": True,
            "Nível": True, "Mirror Match": True
        },
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ══════════════════════════════════════════════════════════════════════════════
# 📥  CARREGAR DADOS
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data
def carregar_dados(arquivo):
    try:
        df = pd.read_parquet(arquivo)
        df['Data_Datetime']         = pd.to_datetime(df['Data'])
        df['Oponente_MR']           = pd.to_numeric(df['Oponente_MR'],           errors='coerce').fillna(0).astype(int)
        df['Meu_MR']                = pd.to_numeric(df['Meu_MR'],                errors='coerce').fillna(0).astype(int)
        df['Diferenca_MR']          = pd.to_numeric(df['Diferenca_MR'],          errors='coerce').fillna(0).astype(int)
        df['Streak_Atual']          = pd.to_numeric(df['Streak_Atual'],          errors='coerce').fillna(0).astype(int)
        df['Numero_Partida_No_Dia'] = pd.to_numeric(df['Numero_Partida_No_Dia'], errors='coerce').fillna(1).astype(int)
        df['Mirror_Match']          = df['Mirror_Match'].astype(str).str.lower().isin(['true','1','sim'])
        df['Oponente_ID']           = df['Oponente_ID'].astype(str)
        return df
    except FileNotFoundError:
        return None

df_base = carregar_dados(ARQUIVO)
if df_base is None:
    st.error(f"Arquivo '{ARQUIVO}' não encontrado. Execute o script de limpeza primeiro.")
    st.stop()

nome_jogador = df_base['Meu_Nome'].iloc[0]

# ── MR por personagem — calculado direto do parquet, sem arquivo auxiliar ─────
@st.cache_data
def calcular_mr_por_char(arquivo):
    df = pd.read_parquet(arquivo)
    df_rank = df[df['Tipo Partida (Jogo)'] == 'Ranqueada'].copy()
    df_rank['Meu_MR'] = pd.to_numeric(df_rank['Meu_MR'], errors='coerce').fillna(0).astype(int)
    df_rank['Data_Datetime'] = pd.to_datetime(df_rank['Data'])
    df_rank = df_rank.sort_values('Data_Datetime', ascending=False)
    mr_chars = (
        df_rank.groupby('Meu_Personagem')
        .agg(MR_Atual=('Meu_MR','first'), MR_Maximo=('Meu_MR','max'), Partidas=('Meu_MR','count'))
        .reset_index()
        .sort_values('MR_Atual', ascending=False)
    )
    # Só mostra personagens com MR > 0 (são Masters) — derivado automaticamente
    return mr_chars[mr_chars['MR_Atual'] > 0]

df_mr_chars = calcular_mr_por_char(ARQUIVO)

# ══════════════════════════════════════════════════════════════════════════════
# 🔧  FUNÇÕES AUXILIARES
# ══════════════════════════════════════════════════════════════════════════════
def semaforo(taxa):
    VERDE   = st.session_state.wr_verde
    AMARELO = st.session_state.wr_amarelo
    if taxa >= VERDE:  return "🟢"
    if taxa > AMARELO: return "🟡"
    return "🔴"

def classificar_nivel(d):
    mi = st.session_state.lim_muito_inf; i  = st.session_state.lim_inf
    s  = st.session_state.lim_sup;       ms = st.session_state.lim_muito_sup
    if d <= mi: return "Muito Inferior"
    elif d <= i: return "Inferior"
    elif d < s:  return "Similar"
    elif d < ms: return "Superior"
    else:        return "Muito Superior"

def wr(sub):
    t = len(sub)
    return (sub['Meu_Resultado'] == "Vitória 🏆").sum() / t * 100 if t > 0 else 0.0

def tabela_wr(df_grp, col_group, sort_by='WR_num', ascending=False):
    t = df_grp.groupby(col_group, observed=True).agg(
        Lutas    =('Meu_Resultado', 'count'),
        Vitórias =('Meu_Resultado', lambda x: (x == "Vitória 🏆").sum()),
        Derrotas =('Meu_Resultado', lambda x: (x == "Derrota ❌").sum())
    ).reset_index()
    t['WR_num'] = t['Vitórias'] / t['Lutas'] * 100
    t['']       = t['WR_num'].apply(semaforo)
    t['WR (%)'] = t['WR_num'].apply(lambda x: f"{x:.1f}%")
    return t.sort_values(sort_by, ascending=ascending)

def aviso_importante(texto):
    """Faixa vermelha discreta para avisos informativos importantes."""
    st.markdown(
        f"""
        <div style="
            background: rgba(230, 57, 70, 0.12);
            border-left: 4px solid #E63946;
            border-radius: 6px;
            padding: 10px 14px;
            margin: 6px 0 14px 0;
            color: #ECF0F1;
            font-size: 13px;
            line-height: 1.5;
        ">
            ⚠️ {texto}
        </div>
        """,
        unsafe_allow_html=True
    )

# ══════════════════════════════════════════════════════════════════════════════
# ⚙️  PAINEL DE CONFIGURAÇÕES  (mantido aqui — será movido para pages/ depois)
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("⚙️ Configurações — Personalize tudo aqui", expanded=False):

    tab_semaforo, tab_nivel, tab_arq, tab_tier, tab_cols = st.tabs([
        "🚦 Indicador de Win Rate",
        "🎯 Nível dos Jogadores",
        "🥋 Arquétipos",
        "🏆 Tier List",
        "👁️ Colunas Ativas",
    ])

    # ── Semáforo ──────────────────────────────────────────────────────────────
    with tab_semaforo:
        st.markdown("Define quando uma taxa de vitória é considerada **boa**, **média** ou **ruim**.")
        st.write("")
        cs1, cs2, cs3 = st.columns(3)
        with cs1:
            st.markdown("🟢 **Boa — Win Rate ≥**")
            novo_verde = st.number_input("Verde (%)", min_value=1, max_value=100,
                                         value=st.session_state.wr_verde, step=1,
                                         label_visibility="collapsed")
        with cs3:
            st.markdown("🔴 **Ruim — Win Rate <**")
            novo_vermelho = st.number_input("Vermelho (%)", min_value=1, max_value=100,
                                            value=st.session_state.wr_amarelo, step=1,
                                            label_visibility="collapsed")
        with cs2:
            st.markdown("🟡 **Média — automático**")
            st.markdown(f"### Entre {novo_vermelho}% e {novo_verde}%")

        st.write("")
        if novo_vermelho >= novo_verde:
            st.error("⚠️ O limite do vermelho precisa ser menor que o verde.")
        else:
            if st.button("💾 Salvar indicador de Win Rate"):
                st.session_state.wr_verde   = novo_verde
                st.session_state.wr_amarelo = novo_vermelho
                st.success(f"✅ 🟢 ≥{novo_verde}% · 🟡 entre {novo_vermelho}% e {novo_verde}% · 🔴 <{novo_vermelho}%")

    # ── Faixas de nível ───────────────────────────────────────────────────────
    with tab_nivel:
        st.markdown(f"Classifica o nível do oponente pela diferença de MR com **{nome_jogador}**.")
        st.write("")
        cn1, cn2, cn3, cn4, cn5 = st.columns(5)
        with cn1:
            st.markdown("**🔵 Muito Inferior**")
            n_mi = st.number_input("MI", value=st.session_state.lim_muito_inf, step=25, label_visibility="collapsed")
        with cn2:
            st.markdown("**🟢 Inferior**")
            n_i = st.number_input("I", value=st.session_state.lim_inf, step=25, label_visibility="collapsed")
        with cn4:
            st.markdown("**🟠 Superior**")
            n_ms_sup = st.number_input("SUP", value=st.session_state.lim_sup, step=25, label_visibility="collapsed")
        with cn5:
            st.markdown("**🔴 Muito Superior**")
            n_ms = st.number_input("MS", value=st.session_state.lim_muito_sup, step=25, label_visibility="collapsed")
        with cn3:
            st.markdown("**🟡 Similar — automático**")
            st.markdown(f"### Entre {n_i + 1} e {n_ms_sup - 1}")

        st.write("")
        erros_nivel = []
        if n_mi >= n_i:       erros_nivel.append("❌ Muito Inferior precisa ser menor que Inferior.")
        if n_i >= n_ms_sup:   erros_nivel.append("❌ Inferior precisa ser menor que Superior.")
        if n_ms_sup >= n_ms:  erros_nivel.append("❌ Superior precisa ser menor que Muito Superior.")
        if n_ms_sup <= 0 or n_ms <= 0: erros_nivel.append("❌ Superior e Muito Superior precisam ser positivos.")
        if n_mi >= 0 or n_i >= 0:      erros_nivel.append("❌ Muito Inferior e Inferior precisam ser negativos.")

        for e in erros_nivel: st.error(e)
        if not erros_nivel:
            if st.button("💾 Salvar faixas de nível"):
                st.session_state.lim_muito_inf = n_mi
                st.session_state.lim_inf       = n_i
                st.session_state.lim_sup       = n_ms_sup
                st.session_state.lim_muito_sup = n_ms
                st.success("✅ Faixas atualizadas!")
                st.rerun()

    # ── Arquétipos ────────────────────────────────────────────────────────────
    with tab_arq:
        st.markdown("**Arraste os personagens entre os arquétipos.**")
        arq_input    = [{"header": arq, "items": list(pers)} for arq, pers in st.session_state.arq_config.items()]
        arq_resultado = sort_items(arq_input, multi_containers=True, key="sort_arq")
        if st.button("💾 Salvar arquétipos"):
            st.session_state.arq_config = {b["header"]: b["items"] for b in arq_resultado}
            st.success("✅ Arquétipos atualizados!")
            st.rerun()
        sem_arq = [p for p in TODOS_PERSONAGENS if not any(p in v for v in st.session_state.arq_config.values())]
        if sem_arq: st.warning(f"⚠️ Sem arquétipo: **{', '.join(sem_arq)}**")

    # ── Tier List ─────────────────────────────────────────────────────────────
    with tab_tier:
        st.markdown("**Arraste os personagens entre os tiers.**")
        st.caption("Meta de referência: pós-patch abril 2026 (Tierlist feita pelo Winter)")
        tier_input    = [{"header": f"Tier {t}", "items": list(p)} for t, p in st.session_state.tier_config.items()]
        tier_resultado = sort_items(tier_input, multi_containers=True, key="sort_tier")
        if st.button("💾 Salvar tier list"):
            st.session_state.tier_config = {b["header"].replace("Tier ",""): b["items"] for b in tier_resultado}
            st.success("✅ Tier list atualizada!")
            st.rerun()
        sem_tier = [p for p in TODOS_PERSONAGENS if not any(p in v for v in st.session_state.tier_config.values())]
        if sem_tier: st.warning(f"⚠️ Sem tier: **{', '.join(sem_tier)}**")

    # ── Colunas ativas ────────────────────────────────────────────────────────
    with tab_cols:
        st.markdown("Ative ou desative classificações no dashboard.")
        cc1, cc2, cc3, cc4 = st.columns(4)
        nova_cols = {}
        with cc1: nova_cols["Tier"]         = st.toggle("🏆 Tier List",    value=st.session_state.cols_ativas.get("Tier", True))
        with cc2: nova_cols["Arquétipo"]    = st.toggle("🥋 Arquétipos",   value=st.session_state.cols_ativas.get("Arquétipo", True))
        with cc3: nova_cols["Nível"]        = st.toggle("🎯 Nível",        value=st.session_state.cols_ativas.get("Nível", True))
        with cc4: nova_cols["Mirror Match"] = st.toggle("🪞 Mirror Match", value=st.session_state.cols_ativas.get("Mirror Match", True))
        if st.button("💾 Salvar preferências"):
            st.session_state.cols_ativas = nova_cols
            st.success("✅ Preferências salvas!")
            st.rerun()

# ── Mapas ativos ──────────────────────────────────────────────────────────────
arq_map  = {p: arq  for arq,  lista in st.session_state.arq_config.items()  for p in lista}
tier_map = {p: tier for tier, lista in st.session_state.tier_config.items() for p in lista}
cols_on  = st.session_state.cols_ativas

# Recalcula colunas dinâmicas
df_base['Arquetipo_Oponente'] = df_base['Oponente_Personagem'].map(arq_map).fillna("Desconhecido")
df_base['Tier_Oponente']      = df_base['Oponente_Personagem'].map(tier_map).fillna("?")
df_base['Nivel_Oponente']     = df_base['Diferenca_MR'].apply(classificar_nivel)
df_base['Nivel_Oponente']     = pd.Categorical(df_base['Nivel_Oponente'], categories=ORDEM_NIVEL, ordered=True)
df_base['Tier_Oponente']      = pd.Categorical(df_base['Tier_Oponente'],  categories=ORDEM_TIER,  ordered=True)

st.subheader(f"**{nome_jogador}** · ID: {JOGADOR_ID}")

# ══════════════════════════════════════════════════════════════════════════════
# 🎛️  SIDEBAR — FILTROS
# ══════════════════════════════════════════════════════════════════════════════
st.sidebar.header("🎛️ Filtros")

lista_meus_chars = sorted(df_base['Meu_Personagem'].dropna().unique())
filtro_meu_char  = st.sidebar.multiselect("Meu Personagem:",         options=lista_meus_chars, default=[], placeholder="Todos")
lista_op_chars   = sorted(df_base['Oponente_Personagem'].dropna().unique())
filtro_op_char   = st.sidebar.multiselect("Personagem do Oponente:", options=lista_op_chars,   default=[], placeholder="Todos")

filtro_arq = []
if cols_on.get("Arquétipo"):
    lista_arq  = sorted(df_base['Arquetipo_Oponente'].dropna().unique())
    filtro_arq = st.sidebar.multiselect("Arquétipo do Oponente:", options=lista_arq, default=[], placeholder="Todos")

filtro_tier = []
if cols_on.get("Tier"):
    filtro_tier = st.sidebar.multiselect("Tier do Oponente:", options=ORDEM_TIER, default=[], placeholder="Todos")

lista_modos  = sorted(df_base['Tipo Partida (Jogo)'].dropna().unique())
filtro_modo  = st.sidebar.multiselect("Modo de Jogo:", options=lista_modos, default=[], placeholder="Todos")

filtro_nivel = []
if cols_on.get("Nível"):
    filtro_nivel = st.sidebar.multiselect("Nível do Oponente:", options=ORDEM_NIVEL, default=[], placeholder="Todos")

filtro_resultado = st.sidebar.multiselect("Resultado:",
    options=["Vitória 🏆","Derrota ❌","Empate ➖"], default=[], placeholder="Todos")

filtro_mirror = "Todos"
if cols_on.get("Mirror Match"):
    filtro_mirror = st.sidebar.selectbox("Mirror Match:",
        options=["Todos","Apenas Mirrors","Excluir Mirrors"], index=0)

filtro_mr = st.sidebar.number_input("MR do Oponente (Mínimo):", min_value=0, max_value=5000, value=0, step=50)

lista_oponentes = sorted(df_base['Oponente_Nome'].dropna().unique())
filtro_oponente = st.sidebar.selectbox("Oponente Específico:",
    options=[None]+list(lista_oponentes), index=0,
    format_func=lambda x: "— Todos —" if x is None else x)

min_date    = df_base['Data_Datetime'].min().date()
max_date    = df_base['Data_Datetime'].max().date()
filtro_data = st.sidebar.date_input("Intervalo de Data:", value=[], min_value=min_date, max_value=max_date)
st.sidebar.caption("📅 1º clique = início · 2º clique = fim")

# ══════════════════════════════════════════════════════════════════════════════
# 🔄  APLICAR FILTROS
# ══════════════════════════════════════════════════════════════════════════════
df_f = df_base.copy()
if filtro_meu_char:  df_f = df_f[df_f['Meu_Personagem'].isin(filtro_meu_char)]
if filtro_op_char:   df_f = df_f[df_f['Oponente_Personagem'].isin(filtro_op_char)]
if filtro_arq:       df_f = df_f[df_f['Arquetipo_Oponente'].isin(filtro_arq)]
if filtro_tier:      df_f = df_f[df_f['Tier_Oponente'].isin(filtro_tier)]
if filtro_modo:      df_f = df_f[df_f['Tipo Partida (Jogo)'].isin(filtro_modo)]
if filtro_nivel:     df_f = df_f[df_f['Nivel_Oponente'].isin(filtro_nivel)]
if filtro_resultado: df_f = df_f[df_f['Meu_Resultado'].isin(filtro_resultado)]
if filtro_mr > 0:    df_f = df_f[df_f['Oponente_MR'] >= filtro_mr]
if filtro_oponente:  df_f = df_f[df_f['Oponente_Nome'] == filtro_oponente]
if filtro_mirror == "Apenas Mirrors":  df_f = df_f[df_f['Mirror_Match'] == True]
if filtro_mirror == "Excluir Mirrors": df_f = df_f[df_f['Mirror_Match'] == False]
if len(filtro_data) == 2:
    df_f = df_f[
        (df_f['Data_Datetime'].dt.date >= filtro_data[0]) &
        (df_f['Data_Datetime'].dt.date <= filtro_data[1])
    ]
elif len(filtro_data) == 1:
    df_f = df_f[df_f['Data_Datetime'].dt.date == filtro_data[0]]

# ── Guarda única ──────────────────────────────────────────────────────────────
if df_f.empty:
    st.warning("⚠️ Nenhuma partida encontrada para os filtros selecionados.")
    st.stop()

total    = len(df_f)
vitorias = (df_f['Meu_Resultado'] == "Vitória 🏆").sum()
derrotas = (df_f['Meu_Resultado'] == "Derrota ❌").sum()
win_rate = vitorias / total * 100 if total > 0 else 0

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 1 — VISÃO GERAL
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🏆 Visão Geral")

df_rank_global  = df_base[df_base['Tipo Partida (Jogo)'] == 'Ranqueada']
mr_maximo_geral = int(df_rank_global['Meu_MR'].max()) if len(df_rank_global) > 0 else 0
jogadores_unicos = df_f['Oponente_ID'].nunique()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("MR Máximo Atingido",            f"{mr_maximo_geral:,}".replace(",","."),
          help="Maior MR registrado em qualquer rankeada, independente do personagem.")
k2.metric("Jogadores Diferentes Enfrentados", f"{jogadores_unicos:,}".replace(",","."),
          help="Quantidade de oponentes distintos enfrentados no recorte atual.")
k3.metric("Total de Partidas",             f"{total:,}".replace(",","."))
k4.metric("Vitórias",                      f"{vitorias:,}".replace(",","."))
k5.metric("Win Rate Geral",                f"{win_rate:.1f}%")

# ── MR por personagem — derivado automaticamente, só Masters ─────────────────
if not df_mr_chars.empty:
    st.write("")
    st.markdown("##### 🏅 MR por Personagem na Temporada Atual")
    cols_mr = st.columns(min(len(df_mr_chars), 6))  # máximo 6 colunas
    for i, (_, row) in enumerate(df_mr_chars.iterrows()):
        if i >= 6: break
        cols_mr[i].metric(
            label=row['Meu_Personagem'],
            value=f"{int(row['MR_Atual']):,}".replace(",","."),
            delta=f"Máx: {int(row['MR_Maximo']):,}".replace(",","."),
            delta_color="off",
            help=f"{int(row['Partidas'])} partidas ranqueadas registradas"
        )

# ── Gráficos de distribuição ──────────────────────────────────────────────────
if total > 0:
    cores_res = {"Vitória 🏆":"#119c0c","Derrota ❌":"#b63a24","Empate ➖":"#2f45c4"}
    df_res  = df_f['Meu_Resultado'].value_counts().reset_index()
    df_res.columns = ['Resultado','Quantidade']
    df_mods = df_f['Tipo Partida (Jogo)'].value_counts().reset_index()
    df_mods.columns = ['Modo','Quantidade']

    col1, col2 = st.columns(2)
    with col1:
        fig = px.pie(df_res, values='Quantidade', names='Resultado', color='Resultado',
                     color_discrete_map=cores_res, title="Distribuição de Resultados",
                     template="plotly_dark", height=300)
        fig.update_traces(textinfo='percent+value', textfont_color="white",
                          marker_line_color='white', marker_line_width=0.5,
                          hovertemplate="<b>%{label}</b><br>%{value} partidas<extra></extra>")
        fig.update_layout(margin=dict(l=10,r=10,t=40,b=10),
                          legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig2 = px.pie(df_mods, values='Quantidade', names='Modo',
                      title="Distribuição por Modo", template="plotly_dark", height=300)
        fig2.update_traces(textinfo='percent+label', textfont_color="white",
                           marker_line_color='white', marker_line_width=0.5,
                           hovertemplate="<b>%{label}</b><br>%{value} partidas<extra></extra>")
        fig2.update_layout(margin=dict(l=10,r=10,t=40,b=10), showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)



# ══════════════════════════════════════════════════════════════════════════════
# 🎨 CORES CANÔNICAS POR PERSONAGEM
# Baseadas nas cores predominantes dos personagens no jogo
# ══════════════════════════════════════════════════════════════════════════════
CORES_PERSONAGENS = {
    "Ryu":          "#4A90D9",   # azul — gi azul clássico
    "Ken":          "#E8A020",   # dourado/laranja — cabelo loiro e gi vermelho
    "Akuma":        "#8B0000",   # vermelho escuro — aura sombria
    "Terry":        "#E74C3C",   # vermelho — jaqueta vermelha icônica
    "Ed":           "#F1C40F",   # amarelo — cabelo loiro e energia dourada
    "Cammy":        "#2ECC71",   # verde — roupa verde militar
    "Juri":         "#9B59B6",   # roxo — energy roxo e personalidade
    "Kimberly":     "#FF6B35",   # laranja — spray e energia
    "Rashid":       "#27AE60",   # verde esmeralda — roupa e turbilhão
    "Dee Jay":      "#F39C12",   # amarelo vivo — energia positiva jamaicana
    "Mai":          "#C0392B",   # vermelho — kimono vermelho
    "Zangief":      "#E74C3C",   # vermelho — roupa de luta vermelha
    "Marisa":       "#D4AC0D",   # dourado — elmo dourado grego
    "Manon":        "#85C1E9",   # azul claro — elegância francesa
    "Lily":         "#8B4513",   # marrom — raízes nativas americanas
    "Alex":         "#1ABC9C",   # verde água — roupa e personalidade
    "Guile":        "#2980B9",   # azul marinho — uniforme militar
    "Dhalsim":      "#E67E22",   # laranja — yogi e fogo
    "JP":           "#6C3483",   # roxo escuro — aura misteriosa
    "Luke":         "#F0B27A",   # bege/areia — cabelo e personalidade americana
    "Chun-Li":      "#3498DB",   # azul — roupa azul icônica
    "Jamie":        "#1A5276",   # azul escuro — roupa e baijiu
    "M. Bison":     "#8E44AD",   # roxo — aura psíquica
    "Sagat":        "#D35400",   # laranja escuro — Muay Thai tailandês
    "Elena":        "#27AE60",   # verde — conexão com a natureza
    "A.K.I.":       "#76D7C4",   # verde água — veneno e misticismo
    "Blanka":       "#28B463",   # verde — cor do personagem
    "Edmond Honda": "#E74C3C",   # vermelho — mawashi vermelho
    "C. Viper":     "#E74C3C",   # vermelho — terno e cabelo ruivo
    "Ingrid":       "#F9E79F",   # amarelo claro — energia solar
}

# Função para obter cor com fallback
def cor_personagem(nome):
    return CORES_PERSONAGENS.get(nome, "#95A5A6")  # cinza como fallback


# ══════════════════════════════════════════════════════════════════════════════
# 🖼️ HELPER — card de personagem com st.image (nativo Streamlit)
# ══════════════════════════════════════════════════════════════════════════════

def card_personagem(col, nome, mr_atual, mr_maximo, partidas):
    cor  = cor_personagem(nome)
    path = f"assets/characters/portrait/{nome}.png"
    with col:
        st.markdown(
            f'<div style="height:3px;background:{cor};border-radius:3px;margin-bottom:8px;"></div>',
            unsafe_allow_html=True
        )
        if os.path.exists(path):
            # Abre com PIL para manter qualidade ao redimensionar
            img = Image.open(path).convert("RGBA")
            st.image(img, width=120)
        else:
            st.markdown(
                f'<div style="width:120px;height:120px;border-radius:8px;background:{cor}22;display:flex;align-items:center;justify-content:center;font-size:32px;">🥊</div>',
                unsafe_allow_html=True
            )
        st.markdown(
            f'<span style="color:{cor};font-weight:700;font-size:12px;letter-spacing:0.5px;">{nome.upper()}</span>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<span style="color:#ECF0F1;font-size:20px;font-weight:700;">{mr_atual:,}</span>'.replace(",","."),
            unsafe_allow_html=True
        )
        st.caption(f"Máx: {mr_maximo:,} · {partidas} lutas".replace(",","."))


# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 2 — EVOLUÇÃO DO MR
# Depende de: df_base já carregado, cor_personagem() e card_personagem() definidos
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 📈 Evolução do MR")
aviso_importante(
    "Esta seção usa o histórico completo de ranqueadas em Master — "
    "filtros globais da sidebar não se aplicam aqui. O MR reseta a cada "
    "temporada, então por padrão mostramos só a temporada atual."
)

# ── Dados base — só ranqueadas EM MASTER (MR > 0), ordem cronológica estável ──
# O filtro Meu_MR > 0 exclui placements e partidas pré-Master que vinham como 0
df_evo = (
    df_base[
        (df_base['Tipo Partida (Jogo)'] == 'Ranqueada') &
        (df_base['Meu_MR'] > 0)
    ]
    .sort_values(['Data_Datetime', 'Hora Exata'], ascending=True)
    .reset_index(drop=True)
    .copy()
)

if df_evo.empty:
    st.info("Nenhuma partida ranqueada em Master encontrada.")
else:
    # ── Filtro de temporada + data (independentes dos filtros globais) ────────
    col_temp, col_filtro = st.columns([2, 3])

    with col_temp:
        if 'Temporada' in df_evo.columns:
            temporadas_disp = sorted(
                df_evo['Temporada'].dropna().unique(),
                reverse=True  # T12 antes de T11
            )
            filtro_temp = st.selectbox(
                "Temporada:",
                options=temporadas_disp,
                index=0,  # default = mais recente
                key="temp_secao2",
                help="O MR reseta a cada temporada — misturar temporadas causa saltos no gráfico"
            )
            df_evo = df_evo[df_evo['Temporada'] == filtro_temp].reset_index(drop=True)
        else:
            st.caption("⚠️ Coluna Temporada ausente — rode a limpeza atualizada.")

    with col_filtro:
        datas_disponiveis = df_evo['Data_Datetime'].dt.date
        filtro_data_evo   = st.date_input(
            "Filtrar por período (opcional):",
            value=[],
            min_value=datas_disponiveis.min(),
            max_value=datas_disponiveis.max(),
            key="data_secao2",
            help="Opcional — refina ainda mais dentro da temporada"
        )

    if len(filtro_data_evo) == 2:
        df_evo = df_evo[
            (df_evo['Data_Datetime'].dt.date >= filtro_data_evo[0]) &
            (df_evo['Data_Datetime'].dt.date <= filtro_data_evo[1])
        ].reset_index(drop=True)
    elif len(filtro_data_evo) == 1:
        df_evo = df_evo[
            df_evo['Data_Datetime'].dt.date == filtro_data_evo[0]
        ].reset_index(drop=True)

    if df_evo.empty:
        st.warning("Nenhuma partida ranqueada em Master no período selecionado.")
    else:
        # ── Numeração sequencial por personagem (ordem já estável) ────────────
        df_evo['Partida_Num'] = df_evo.groupby('Meu_Personagem').cumcount() + 1

        # ── MR máximo global para linha de referência ─────────────────────────
        mr_max_global = int(df_evo['Meu_MR'].max())
        personagens   = sorted(df_evo['Meu_Personagem'].dropna().unique())

        # ── Gráfico de linhas ─────────────────────────────────────────────────
        fig = go.Figure()
        for personagem in personagens:
            df_p = df_evo[df_evo['Meu_Personagem'] == personagem].copy()
            cor  = cor_personagem(personagem)
            fig.add_trace(go.Scatter(
                x    = df_p['Partida_Num'],
                y    = df_p['Meu_MR'],
                mode = 'lines+markers',
                name = personagem,
                line = dict(color=cor, width=2.5),
                marker = dict(color=cor, size=5, line=dict(color='#0d0d0d', width=1)),
                customdata = df_p[['Data_Datetime', 'Meu_Resultado']].values,
                hovertemplate = (
                    f"<b style='color:{cor}'>{personagem}</b><br>"
                    "MR: <b>%{y:,}</b><br>"
                    "Partida %{x}<br>"
                    "%{customdata[0]|%d/%m/%Y}<br>"
                    "%{customdata[1]}<extra></extra>"
                )
            ))

        fig.add_hline(
            y=mr_max_global, line_dash="dash",
            line_color="#F39C12", line_width=1.5,
            annotation_text=f"  Máx: {mr_max_global:,}".replace(",","."),
            annotation_position="right",
            annotation_font_color="#F39C12", annotation_font_size=11,
        )

        fig.update_layout(
            template="plotly_dark", height=420, hovermode="x unified",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,13,30,0.6)",
            xaxis=dict(title="Nº da Partida (por personagem)", gridcolor="#1e2a3a", zeroline=False),
            yaxis=dict(title="MR (Master Rating)", gridcolor="#1e2a3a", zeroline=False),
            legend=dict(orientation="h", yanchor="top", y=-0.18,
                        xanchor="center", x=0.5, font=dict(size=12)),
            margin=dict(l=10, r=80, t=20, b=60),
            hoverlabel=dict(bgcolor="#1a1a2e", font_size=13, font_color="white"),
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── Cards por personagem ──────────────────────────────────────────────
        st.markdown("##### 🏅 Resumo por Personagem")
        resumo = (
            df_evo.sort_values('Data_Datetime', ascending=False)
            .groupby('Meu_Personagem')
            .agg(
                MR_Atual  = ('Meu_MR', 'first'),
                MR_Maximo = ('Meu_MR', 'max'),
                Partidas  = ('Meu_MR', 'count'),
            )
            .reset_index()
            .sort_values('MR_Atual', ascending=False)
        )

        POR_LINHA = 4
        lista = resumo.to_dict('records')
        for inicio in range(0, len(lista), POR_LINHA):
            grupo = lista[inicio:inicio + POR_LINHA]
            cols  = st.columns(POR_LINHA)
            for idx, row in enumerate(grupo):
                card_personagem(
                    cols[idx],
                    row['Meu_Personagem'],
                    int(row['MR_Atual']),
                    int(row['MR_Maximo']),
                    int(row['Partidas']),
                )

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 3 — PERSONAGENS UTILIZADOS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🥋 Personagens Utilizados")

if total > 0:
    df_ch = df_f['Meu_Personagem'].value_counts().reset_index()
    df_ch.columns = ['Personagem', 'Quantidade']

    c3, c4 = st.columns(2)
    with c3:
        fig = px.bar(
            df_ch, x='Personagem', y='Quantidade', color='Personagem',
            color_discrete_map=CORES_PERSONAGENS,
            title="Partidas por Personagem",
            template="plotly_dark", height=340
        )
        fig.update_traces(
            texttemplate='%{y}', textposition="outside", textfont_color="white",
            hovertemplate="<b>%{x}</b><br>%{y} partidas<extra></extra>"
        )
        fig.update_layout(
            showlegend=False,
            yaxis=dict(showticklabels=False),
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        fig = px.pie(
            df_ch, values='Quantidade', names='Personagem',
            color='Personagem',
            color_discrete_map=CORES_PERSONAGENS,
            title="Proporção de Uso",
            template="plotly_dark", height=340
        )
        fig.update_traces(
            textinfo='percent', textfont_color="white",
            marker_line_color='white', marker_line_width=0.5,
            hovertemplate="<b>%{label}</b><br>%{value} partidas (%{percent})<extra></extra>"
        )
        fig.update_layout(
            margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 4 — MATCHUPS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🥊 Matchups")

if total > 0:

    # ── 4a — Personagens mais enfrentados ─────────────────────────────────────
    df_op = df_f['Oponente_Personagem'].value_counts().reset_index()
    df_op.columns = ['Personagem', 'Quantidade']

    fig = px.bar(
        df_op, x='Personagem', y='Quantidade', color='Personagem',
        color_discrete_map=CORES_PERSONAGENS,
        title="Personagens mais enfrentados",
        template="plotly_dark", height=380
    )
    fig.update_traces(
        texttemplate='%{y}', textposition="outside", textfont_color="white",
        hovertemplate="<b>%{x}</b><br>%{y} partidas<extra></extra>"
    )
    fig.update_layout(
        showlegend=False,
        yaxis=dict(showticklabels=False),
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ── 4b — Win rate contra cada personagem ──────────────────────────────────
    st.markdown("#### 📊 Win Rate contra cada Personagem")

    df_mu = tabela_wr(df_f, 'Oponente_Personagem', sort_by='WR_num', ascending=False)
    df_mu = df_mu.rename(columns={'Oponente_Personagem': 'Personagem'})

    st.dataframe(
        df_mu[['', 'Personagem', 'Lutas', 'Vitórias', 'Derrotas', 'WR (%)', 'WR_num']],
        use_container_width=True, hide_index=True,
        column_config={"WR_num": None}
    )
    st.info(
        f"🚦 🟢 ≥ {st.session_state.wr_verde}%   ·   "
        f"🟡 entre {st.session_state.wr_amarelo}% e {st.session_state.wr_verde}%   ·   "
        f"🔴 < {st.session_state.wr_amarelo}%   |   Ajustável em ⚙️ Configurações."
    )

    st.divider()

    # ── 4c — Cobertura de personagens ─────────────────────────────────────────
    st.markdown("#### 🗂️ Cobertura de Personagens no Histórico")
    st.caption("Quais personagens do roster já foram enfrentados e quais ainda não apareceram.")

    nao_enf = sorted(set(TODOS_CHARS_SF6) - set(df_f['Oponente_Personagem'].dropna().unique()))
    ja_enf  = sorted(set(TODOS_CHARS_SF6) & set(df_f['Oponente_Personagem'].dropna().unique()))

    col_cob1, col_cob2 = st.columns(2)
    with col_cob1:
        st.metric("Personagens Enfrentados",       f"{len(ja_enf)} de {len(TODOS_CHARS_SF6)}")
    with col_cob2:
        st.metric("Personagens Nunca Enfrentados", f"{len(nao_enf)} de {len(TODOS_CHARS_SF6)}")

    if nao_enf:
        st.info(f"💡 Nunca enfrentados com os filtros atuais: {', '.join(nao_enf)}.")
    else:
        st.success("✅ Todos os personagens do roster já foram enfrentados!")

    st.divider()

    # ── 4d — Diversidade de Jogadores por Personagem ──────────────────────────
    st.markdown("#### 👥 Diversidade de Jogadores por Personagem")
    st.caption(
        "Quantos jogadores diferentes usaram cada personagem contra você. "
        "Muitos jogadores = personagem popular; poucos jogadores com muitas "
        "partidas = rival recorrente."
    )

    col_id = 'Oponente_ID' if 'Oponente_ID' in df_f.columns else 'Oponente_Nome'

    df_uniq = df_f.groupby('Oponente_Personagem').agg(
        Total_Partidas   = ('Meu_Resultado', 'count'),
        Jogadores_Unicos = (col_id, 'nunique')
    ).reset_index().sort_values('Jogadores_Unicos', ascending=False)
    df_uniq['Partidas_por_Jogador'] = (
        df_uniq['Total_Partidas'] / df_uniq['Jogadores_Unicos']
    ).round(1)

    def jogadores_hover(char):
        sub   = df_f[df_f['Oponente_Personagem'] == char]
        nomes = sorted(sub['Oponente_Nome'].dropna().unique().tolist())
        if len(nomes) <= 8:
            return "<br>".join(nomes)
        return "<br>".join(nomes[:8]) + f"<br>... e {len(nomes)-8} outros"

    df_uniq['Jogadores_Hover'] = df_uniq['Oponente_Personagem'].apply(jogadores_hover)

    fig_uniq = px.bar(
        df_uniq, x='Oponente_Personagem', y='Jogadores_Unicos',
        color='Oponente_Personagem',
        color_discrete_map=CORES_PERSONAGENS,
        title="Jogadores diferentes enfrentados por personagem",
        template="plotly_dark", height=380,
        custom_data=['Total_Partidas', 'Jogadores_Hover', 'Partidas_por_Jogador']
    )
    fig_uniq.update_traces(
        texttemplate='%{y}', textposition="outside", textfont_color="white",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Jogadores diferentes: %{y}<br>"
            "Total de partidas: %{customdata[0]}<br>"
            "Média por jogador: %{customdata[2]}<br><br>"
            "%{customdata[1]}<extra></extra>"
        )
    )
    fig_uniq.update_traces(marker_line_color='rgba(255,255,255,0.3)', marker_line_width=1)
    fig_uniq.update_layout(
        showlegend=False,
        xaxis_title="Personagem do Oponente",
        yaxis=dict(title="Qtde de Jogadores Diferentes", showticklabels=False),
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig_uniq, use_container_width=True)

    st.caption(
        "💡 A média por jogador (no hover) revela rivais recorrentes: "
        "um personagem com poucos jogadores mas muitas partidas indica que "
        "você enfrenta sempre as mesmas pessoas com ele."
    )

    st.divider()

    # ── 4e — Frequência de Encontro por Personagem ────────────────────────────
    st.markdown("#### 🕐 Frequência de Encontro por Personagem")
    st.caption(
        "Há quanto tempo você não enfrenta cada personagem, com que frequência "
        "ele costuma aparecer e qual foi o maior tempo que você ficou sem vê-lo. "
        "Útil para saber quais matchups você anda treinando pouco."
    )

    # Datas de lançamento de personagens DLC — para os demais usa o ponto-zero dos dados
    LANCAMENTO_CHARS = {
        "Alex":   pd.Timestamp("2026-03-17"),
        "Ingrid": pd.Timestamp("2026-05-28"),
    }

    df_f['Data_Datetime_parsed'] = pd.to_datetime(df_f['Data_Datetime'])
    hoje       = pd.Timestamp.now().normalize()
    ponto_zero = df_f['Data_Datetime_parsed'].dt.normalize().min()

    def disponivel_desde(char):
        """Quando o personagem passou a estar disponível no recorte de dados."""
        lanc = LANCAMENTO_CHARS.get(char)
        if lanc is not None and lanc > ponto_zero:
            return lanc.normalize()
        return ponto_zero

    def stats_frequencia(char):
        sub        = df_f[df_f['Oponente_Personagem'] == char].copy()
        disponivel = disponivel_desde(char)
        dias_total = max((hoje - disponivel).days, 1)  # evita divisão por zero

        if sub.empty:
            return pd.Series({
                'Total_Partidas':   0,
                'Ultima_Data':      None,
                'Dias_Desde':       dias_total,
                'Freq_Media':       None,
                'Maior_Gap':        dias_total,  # nunca enfrentado = gap = período todo
                'Nunca_Enfrentado': True,
            })

        dias_unicos = sorted(sub['Data_Datetime_parsed'].dt.normalize().drop_duplicates().tolist())
        ultima      = dias_unicos[-1]
        dias_desde  = (hoje - ultima).days

        # Intervalo médio CORRETO — considera todo o período disponível, não só
        # os dias entre encontros. Pontos de referência: disponível → cada
        # encontro → hoje. A média é o período total / número de encontros.
        freq_media = round(dias_total / len(dias_unicos), 1)

        # Maior gap — maior intervalo entre dois pontos consecutivos
        # (incluindo disponível→1º encontro e último encontro→hoje)
        pontos = [disponivel] + dias_unicos + [hoje]
        gaps   = [(pontos[i+1] - pontos[i]).days for i in range(len(pontos)-1)]
        maior_gap = max(gaps) if gaps else 0

        return pd.Series({
            'Total_Partidas':   len(sub),
            'Ultima_Data':      ultima,
            'Dias_Desde':       dias_desde,
            'Freq_Media':       freq_media,
            'Maior_Gap':        maior_gap,
            'Nunca_Enfrentado': False,
        })

    df_roster = pd.DataFrame({'Oponente_Personagem': TODOS_CHARS_SF6})
    stats     = df_roster['Oponente_Personagem'].apply(stats_frequencia)
    df_roster = pd.concat([df_roster, stats], axis=1)

    def fmt_ultima(row):
        if row['Nunca_Enfrentado']:     return "⚪ Não enfrentado"
        if pd.isna(row['Ultima_Data']): return "—"
        dias     = int(row['Dias_Desde'])
        data_fmt = pd.Timestamp(row['Ultima_Data']).strftime('%d/%m/%Y')
        if dias == 0:   sufixo = "hoje"
        elif dias == 1: sufixo = "ontem"
        else:           sufixo = f"{dias} dias atrás"
        return f"{sufixo} · {data_fmt}"

    def fmt_media(row):
        if row['Nunca_Enfrentado']:    return "—"
        if pd.isna(row['Freq_Media']): return "—"
        return f"a cada {int(row['Freq_Media'])} dias"

    def fmt_gap(row):
        if row['Nunca_Enfrentado']: return "—"
        return f"{int(row['Maior_Gap'])} dias"

    df_roster['Último Encontro']  = df_roster.apply(fmt_ultima, axis=1)
    df_roster['Intervalo Médio']  = df_roster.apply(fmt_media,  axis=1)
    df_roster['Maior Tempo Sem Ver'] = df_roster.apply(fmt_gap, axis=1)
    df_roster['Partidas']         = df_roster['Total_Partidas'].astype(int)

    df_roster_view = df_roster.rename(columns={'Oponente_Personagem': 'Personagem'})
    df_roster_view = df_roster_view.sort_values('Dias_Desde', ascending=False)

    st.dataframe(
        df_roster_view[[
            'Personagem',
            'Último Encontro', 'Intervalo Médio', 'Maior Tempo Sem Ver',
            'Partidas'
        ]],
        use_container_width=True, hide_index=True
    )
    st.info(
        "💡 **Intervalo Médio** = período total que o personagem esteve disponível "
        "÷ número de dias em que você o enfrentou. Considera o tempo real, não só "
        "os intervalos entre encontros."
    )
    st.caption(
        "⚠️ Para Alex (17/03) e Ingrid (28/05) o cálculo parte da data de lançamento. "
        "Para os demais, parte da primeira partida do seu histórico. "
        "As colunas de texto não ordenam numericamente."
    )

    st.divider()

    # ── 4f — Mirror Match ─────────────────────────────────────────────────────
    if cols_on.get("Mirror Match"):
        st.markdown("#### 🪞 Mirror Matches")
        df_mir = df_f[df_f['Mirror_Match'] == True]
        n_mir  = len(df_mir)

        if n_mir == 0:
            st.info("Nenhum mirror match encontrado com os filtros atuais.")
        else:
            wr_mir = wr(df_mir)
            mm1, mm2, mm3 = st.columns(3)
            mm1.metric("Total de Mirrors",    f"{n_mir}")
            mm2.metric("Win Rate em Mirrors", f"{wr_mir:.1f}%")
            mm3.metric("Win Rate Geral",      f"{win_rate:.1f}%",
                       delta=f"{wr_mir - win_rate:+.1f}%", delta_color="normal")

            df_mc = tabela_wr(df_mir, 'Meu_Personagem')
            st.dataframe(
                df_mc[['', 'Meu_Personagem', 'Lutas', 'Vitórias', 'WR (%)', 'WR_num']],
                use_container_width=True, hide_index=True,
                column_config={"WR_num": None}
            )

    st.divider()

    # ── 4f — Desempenho contra Tierlist ──────────────────────────────────────
    if cols_on.get("Tier"):
        st.markdown("#### 🏆 Desempenho contra Tierlist")

        df_mu_tier = tabela_wr(df_f, 'Tier_Oponente', sort_by='Tier_Oponente', ascending=True)
        df_mu_tier = df_mu_tier.rename(columns={'Tier_Oponente': 'Tier'})

        wr_nums = df_f.groupby('Tier_Oponente', observed=True).apply(
            lambda x: (x['Meu_Resultado'] == "Vitória 🏆").sum() / len(x) * 100
            if len(x) > 0 else 0
        ).reset_index()
        wr_nums.columns = ['Tier', 'WR']

        chars_por_tier = {
            tier: "<br>".join(sorted(chars))
            for tier, chars in st.session_state.tier_config.items()
            if chars
        }
        wr_nums['chars_hover'] = wr_nums['Tier'].astype(str).map(
            lambda t: chars_por_tier.get(t, "—")
        )

        fig_tier = go.Figure()
        fig_tier.add_trace(go.Bar(
            x            = wr_nums['Tier'].astype(str),
            y            = wr_nums['WR'],
            marker_color = [CORES_TIER.get(str(t), '#888') for t in wr_nums['Tier']],
            text         = [f"{v:.1f}%" for v in wr_nums['WR']],
            textposition = 'outside',
            textfont_color = 'white',
            customdata   = wr_nums[['chars_hover']].values,
            hovertemplate = (
                "<b>Tier %{x}</b><br>"
                "Win Rate: %{y:.1f}%<br><br>"
                "%{customdata[0]}<extra></extra>"
            )
        ))
        fig_tier.update_layout(
            title    = "Desempenho Contra Tierlist",
            template = "plotly_dark", height=320,
            xaxis_title = "Tier do Personagem",
            yaxis = dict(title="Win Rate (%)", range=[0, 115], showticklabels=False),
            margin = dict(l=10, r=10, t=40, b=10)
        )

        c_tier1, c_tier2 = st.columns(2)
        with c_tier1:
            st.plotly_chart(fig_tier, use_container_width=True)
        with c_tier2:
            st.write("")
            st.write("")
            st.dataframe(
                df_mu_tier[['', 'Tier', 'Lutas', 'Vitórias', 'Derrotas', 'WR (%)', 'WR_num']],
                use_container_width=True, hide_index=True,
                column_config={"WR_num": None}
            )

        st.info("💡 A posição de cada personagem na tierlist pode ser alterada em **⚙️ Configurações → 🏆 Tierlist**.")


# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 5 — ARQUÉTIPOS (se ativo)
# ══════════════════════════════════════════════════════════════════════════════
if cols_on.get("Arquétipo") and total > 0:
    st.markdown("---")
    st.markdown("### 🎭 Desempenho Contra Arquétipos")

    df_arq     = tabela_wr(df_f, 'Arquetipo_Oponente').sort_values('Lutas', ascending=False)
    wr_arq_num = df_f.groupby('Arquetipo_Oponente').apply(
        lambda x: (x['Meu_Resultado'] == "Vitória 🏆").sum() / len(x) * 100
        if len(x) > 0 else 0
    ).reset_index()
    wr_arq_num.columns = ['Arquétipo', 'WR']

    # Cores por arquétipo — usa a cor do primeiro personagem do grupo como referência
    CORES_ARQUETIPOS = {
        "Shoto":        "#4A90D9",   # Ryu — azul
        "Rushdown":     "#2ECC71",   # Cammy — verde
        "Grappler":     "#E74C3C",   # Zangief — vermelho
        "Zoner":        "#2980B9",   # Guile — azul marinho
        "All-Rounder":  "#F39C12",   # Luke — laranja
        "Unorthodox":   "#9B59B6",   # Juri — roxo
        "High-Risk":    "#C0392B",   # C. Viper — vermelho escuro
        "Desconhecido": "#95A5A6",   # cinza
    }

    def cor_arquetipo(nome):
        return CORES_ARQUETIPOS.get(nome, "#95A5A6")

    # Hover com lista de personagens por arquétipo
    chars_por_arq = {
        arq: "<br>".join(sorted(chars))
        for arq, chars in st.session_state.arq_config.items()
        if chars
    }
    wr_arq_num['chars_hover'] = wr_arq_num['Arquétipo'].map(
        lambda a: chars_por_arq.get(a, "—")
    )

    ca1, ca2 = st.columns(2)
    with ca1:
        fig = go.Figure()
        for _, row in wr_arq_num.iterrows():
            cor = cor_arquetipo(row['Arquétipo'])
            fig.add_trace(go.Bar(
                x         = [row['Arquétipo']],
                y         = [row['WR']],
                name      = row['Arquétipo'],
                marker_color = cor,
                text      = [f"{row['WR']:.1f}%"],
                textposition = 'outside',
                textfont_color = 'white',
                customdata = [[row['chars_hover']]],
                hovertemplate = (
                    f"<b>{row['Arquétipo']}</b><br>"
                    f"Win Rate: {row['WR']:.1f}%<br><br>"
                    "%{customdata[0]}<extra></extra>"
                )
            ))
        fig.update_layout(
            title      = "Win Rate Contra Arquétipo",
            template   = "plotly_dark",
            height     = 340,
            showlegend = False,
            yaxis      = dict(range=[0, 115], showticklabels=False),
            margin     = dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    with ca2:
        st.write("")
        st.write("")
        df_arq_view = df_arq.rename(columns={'Arquetipo_Oponente': 'Arquétipo'})
        st.dataframe(
            df_arq_view[['', 'Arquétipo', 'Lutas', 'Vitórias', 'Derrotas', 'WR (%)', 'WR_num']],
            use_container_width=True, hide_index=True,
            column_config={"WR_num": None}
        )

    st.info("💡 O Arquétipo de cada personagem pode ser alterado em **⚙️ Configurações → 🥋 Arquétipos**.")


# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 6 — NÍVEL DO OPONENTE (se ativo)
# ══════════════════════════════════════════════════════════════════════════════
if cols_on.get("Nível") and total > 0:
    st.markdown("---")
    st.markdown("### 🎯 Desempenho Contra Nível do Oponente")

    # Cores por nível — do frio (inferior) ao quente (superior)
    CORES_NIVEL = {
        "Muito Inferior": "#3498DB",   # azul
        "Inferior":       "#2ECC71",   # verde
        "Similar":        "#F39C12",   # laranja
        "Superior":       "#E67E22",   # laranja escuro
        "Muito Superior": "#E74C3C",   # vermelho
    }

    df_nv     = tabela_wr(df_f, 'Nivel_Oponente')
    wr_nv_num = df_f.groupby('Nivel_Oponente', observed=True).apply(
        lambda x: (x['Meu_Resultado'] == "Vitória 🏆").sum() / len(x) * 100
        if len(x) > 0 else 0
    ).reset_index()
    wr_nv_num.columns = ['Nível', 'WR']

    cn1, cn2 = st.columns(2)
    with cn1:
        def oponentes_hover(nivel):
            nomes = sorted(df_f[df_f['Nivel_Oponente'] == nivel]['Oponente_Nome'].dropna().unique())
            if len(nomes) <= 10:
                return "<br>".join(nomes)
            return "<br>".join(nomes[:10]) + f"<br>... e {len(nomes)-10} outros"

        wr_nv_num['op_hover'] = wr_nv_num['Nível'].astype(str).map(oponentes_hover)

        fig = go.Figure()
        for _, row in wr_nv_num.iterrows():
            cor = CORES_NIVEL.get(str(row['Nível']), '#888888')
            fig.add_trace(go.Bar(
                x            = [row['Nível']],
                y            = [row['WR']],
                name         = row['Nível'],
                marker_color = cor,
                text         = [f"{row['WR']:.1f}%"],
                textposition = 'outside',
                textfont_color = 'white',
                customdata   = [[row['op_hover']]],
                hovertemplate = (
                    f"<b>{row['Nível']}</b><br>"
                    f"Win Rate: {row['WR']:.1f}%<br><br>"
                    "%{customdata[0]}<extra></extra>"
                )
            ))
        fig.update_layout(
            title      = "Win Rate Contra Nível do Oponente",
            template   = "plotly_dark",
            height     = 320,
            showlegend = False,
            yaxis      = dict(range=[0, 115], showticklabels=False),
            xaxis      = dict(
                categoryorder = 'array',
                categoryarray = ORDEM_NIVEL,
                title         = "Nível do Oponente"
            ),
            margin = dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    with cn2:
        st.write("")
        st.write("")
        mi = st.session_state.lim_muito_inf
        i  = st.session_state.lim_inf
        s  = st.session_state.lim_sup
        ms = st.session_state.lim_muito_sup

        faixas_desc = {
            "Muito Inferior": f"≤ {mi} MR",
            "Inferior":       f"{mi+1} a {i} MR",
            "Similar":        f"{i+1} a {s-1} MR",
            "Superior":       f"{s} a {ms-1} MR",
            "Muito Superior": f"≥ {ms} MR",
        }

        df_nv_view = df_nv.rename(columns={'Nivel_Oponente': 'Nível'})
        df_nv_view['Faixa de MR'] = df_nv_view['Nível'].map(faixas_desc)
        df_nv_view['_ord']        = df_nv_view['Nível'].map(
            {n: idx for idx, n in enumerate(ORDEM_NIVEL)}
        )
        df_nv_view = df_nv_view.sort_values('_ord')

        st.dataframe(
            df_nv_view[['', 'Nível', 'Faixa de MR', 'Lutas', 'Vitórias', 'WR (%)', 'WR_num']],
            use_container_width=True, hide_index=True,
            column_config={"WR_num": None, "_ord": None}
        )

    st.info(
        f"🎯 O nível do oponente é calculado pela **diferença de MR antes da partida** — "
        f"MR do oponente menos MR do {nome_jogador}. "
        f"As faixas são configuráveis em **⚙️ Configurações → 🎯 Nível dos Jogadores**."
    )
    st.info(
        "📊 **Por que as faixas não são simétricas?** "
        "Na ranked do SF6 subir de 2000 para 2100 MR é muito mais difícil do que de 1600 para 1700. "
        f"Como {nome_jogador} é um top player, uma pequena diferença de pontos acima "
        "já representa um oponente consideravelmente mais forte."
    )


# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 7 — DIA DA SEMANA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 📅 Desempenho por Dia da Semana")

if total > 0:
    ORDEM_DIAS = ['Segunda-feira','Terça-feira','Quarta-feira','Quinta-feira',
                  'Sexta-feira','Sábado','Domingo']
    CORES_DIAS = {
        'Segunda-feira': '#3498DB', 'Terça-feira':  '#2ECC71',
        'Quarta-feira':  '#F39C12', 'Quinta-feira': '#9B59B6',
        'Sexta-feira':   '#E74C3C', 'Sábado':       '#1ABC9C',
        'Domingo':       '#E67E22',
    }

    df_dias = (
        df_f['Dia da Semana'].value_counts()
        .reindex(ORDEM_DIAS).fillna(0).reset_index()
    )
    df_dias.columns = ['Dia da Semana', 'Quantidade']
    df_dias = df_dias[df_dias['Quantidade'] > 0]

    df_wr_dia = pd.DataFrame([{
        'Dia da Semana': dia,
        'WR':      wr(df_f[df_f['Dia da Semana'] == dia]),
        'Partidas': len(df_f[df_f['Dia da Semana'] == dia]),
    } for dia in df_dias['Dia da Semana']])

    # Tabela resumo
    df_tabela_dia = df_wr_dia.copy()
    df_tabela_dia['']           = df_tabela_dia['WR'].apply(semaforo)
    df_tabela_dia['Win Rate (%)'] = df_tabela_dia['WR'].apply(lambda x: f"{x:.1f}%")
    df_tabela_dia['_ord']        = df_tabela_dia['Dia da Semana'].map(
        {d: i for i, d in enumerate(ORDEM_DIAS)}
    )
    st.dataframe(
        df_tabela_dia[['', 'Dia da Semana', 'Partidas', 'Win Rate (%)', 'WR', '_ord']]
        .sort_values('_ord'),
        use_container_width=True, hide_index=True,
        column_config={"WR": None, "_ord": None}
    )

    st.write("")
    cd1, cd2 = st.columns(2)
    with cd1:
        fig = px.bar(
            df_dias, x='Dia da Semana', y='Quantidade',
            color='Dia da Semana', color_discrete_map=CORES_DIAS,
            title="Partidas por Dia", template="plotly_dark", height=300
        )
        fig.update_traces(
            texttemplate='%{y}', textposition="outside", textfont_color="white",
            hovertemplate="<b>%{x}</b><br>%{y} partidas<extra></extra>"
        )
        fig.update_layout(
            showlegend=False,
            xaxis_title="", yaxis=dict(showticklabels=False, title=""),
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    with cd2:
        fig2 = px.bar(
            df_wr_dia, x='Dia da Semana', y='WR',
            color='Dia da Semana', color_discrete_map=CORES_DIAS,
            title="Win Rate por Dia (%)", template="plotly_dark", height=300,
            custom_data=['Partidas']
        )
        fig2.update_traces(
            texttemplate='%{y:.1f}%', textposition="outside", textfont_color="white",
            hovertemplate="<b>%{x}</b><br>%{y:.1f}% win rate<br>%{customdata[0]} partidas<extra></extra>"
        )
        fig2.update_layout(
            showlegend=False,
            xaxis_title="", yaxis=dict(showticklabels=False, title="", range=[0, 115]),
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig2, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 8 — HORÁRIO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🕒 Desempenho por Faixa de Horário")

if total > 0:
    df_h = df_f.copy()
    df_h['Hora_Fixa'] = df_h['Hora Exata'].str[:2]
    df_hora = df_h.groupby('Hora_Fixa').agg(
        Lutas    = ('Meu_Resultado', 'count'),
        Vitórias = ('Meu_Resultado', lambda x: (x == "Vitória 🏆").sum())
    ).reset_index()
    df_hora['WR_num'] = df_hora['Vitórias'] / df_hora['Lutas'] * 100
    df_hora['Faixa']  = df_hora['Hora_Fixa'] + ":00 – " + df_hora['Hora_Fixa'] + ":59"
    df_hora['']       = df_hora['WR_num'].apply(semaforo)
    df_hora['WR (%)'] = df_hora['WR_num'].apply(lambda x: f"{x:.1f}%")
    df_hora = df_hora.sort_values('Faixa')

    ch1, ch2 = st.columns(2)
    with ch1:
        fig = px.bar(
            df_hora, x='Faixa', y='WR_num',
            title="Win Rate por Horário (%)",
            template="plotly_dark", height=320,
            custom_data=['Lutas']
        )
        fig.update_traces(
            texttemplate='%{y:.1f}%', textposition="outside", textfont_color="white",
            marker_color='#3498DB',
            hovertemplate="<b>%{x}</b><br>%{y:.1f}% win rate<br>%{customdata[0]} partidas<extra></extra>"
        )
        fig.update_layout(
            xaxis_title="",
            yaxis=dict(showticklabels=False, title="", range=[0, 115]),
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    with ch2:
        st.write("")
        st.write("")
        st.dataframe(
            df_hora[['', 'Faixa', 'Lutas', 'WR (%)', 'WR_num']],
            use_container_width=True, hide_index=True,
            column_config={"WR_num": None}
        )


# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 9 — SESSÃO E FADIGA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 😮‍💨 Sessão e Fadiga")

if total > 0 and 'Numero_Partida_No_Dia' in df_f.columns:
    st.caption("A sessão de jogo é considerada por dia — mesmo jogando de manhã e à noite, conta como 1 sessão.")
    st.caption("O aquecimento são as partidas 1, 2 e 3 do dia.")
    st.caption("Se aplicar filtro de personagem ou modo, o aquecimento será relativo àquele filtro.")

    def faixa_p(n):
        if n <= 3:  return "1–3 (aquecimento)"
        if n <= 10: return "4–10"
        if n <= 15: return "11–15"
        if n <= 20: return "16–20"
        if n <= 25: return "21–25"
        if n <= 30: return "26–30"
        if n <= 35: return "31–35"
        if n <= 40: return "36–40"
        return "40+"

    ORDEM_FX = ["1–3 (aquecimento)","4–10","11–15","16–20",
                "21–25","26–30","31–35","36–40","40+"]

    # Cores de fadiga — verde no início, vermelho no fim
    CORES_FADIGA = {
        "1–3 (aquecimento)": "#F39C12",
        "4–10":              "#2ECC71",
        "11–15":             "#27AE60",
        "16–20":             "#F1C40F",
        "21–25":             "#E67E22",
        "26–30":             "#E74C3C",
        "31–35":             "#C0392B",
        "36–40":             "#922B21",
        "40+":               "#641E16",
    }

    df_fad = df_f.copy()
    df_fad['Faixa'] = df_fad['Numero_Partida_No_Dia'].apply(faixa_p)
    df_fx = df_fad.groupby('Faixa').agg(
        Lutas    = ('Meu_Resultado', 'count'),
        Vitórias = ('Meu_Resultado', lambda x: (x == "Vitória 🏆").sum())
    ).reset_index()
    df_fx['WR']    = df_fx['Vitórias'] / df_fx['Lutas'] * 100
    df_fx['Faixa'] = pd.Categorical(df_fx['Faixa'], categories=ORDEM_FX, ordered=True)
    df_fx = df_fx.sort_values('Faixa')
    df_fx = df_fx[df_fx['Lutas'] > 0]

    cf1, cf2 = st.columns(2)
    with cf1:
        fig = px.bar(
            df_fx, x='Faixa', y='WR',
            color='Faixa', color_discrete_map=CORES_FADIGA,
            title="Win Rate por Faixa da Sessão",
            template="plotly_dark", height=340,
            custom_data=['Lutas']
        )
        fig.update_traces(
            texttemplate='%{y:.1f}%', textposition="outside", textfont_color="white",
            hovertemplate="<b>%{x}</b><br>%{y:.1f}% win rate<br>%{customdata[0]} partidas<extra></extra>"
        )
        fig.update_layout(
            showlegend=False,
            yaxis=dict(range=[0, 115], showticklabels=False),
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    with cf2:
        df_fv = df_fx.copy()
        df_fv['']       = df_fv['WR'].apply(semaforo)
        df_fv['WR (%)'] = df_fv['WR'].apply(lambda x: f"{x:.1f}%")
        st.write("")
        st.write("")
        st.dataframe(
            df_fv[['', 'Faixa', 'Lutas', 'WR (%)', 'WR']],
            use_container_width=True, hide_index=True,
            column_config={"WR": None}
        )
        st.caption("Faixas sem dados não aparecem no gráfico.")

    st.info("📌 Faixa '1–3 (aquecimento)' = soma de todas as vezes que o jogador jogou a 1ª, 2ª ou 3ª partida do dia.")
    st.info("📌 Faixa '11–15' = soma de todas as vezes que o jogador jogou da 11ª até a 15ª partida do dia.")


# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 10 — FATOR PSICOLÓGICO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🧠 Fator Psicológico")

if total > 0:
    # ── 10a — Impacto do 1º Round ─────────────────────────────────────────────
    st.markdown("#### 🥇 Impacto do 1º Round")
    df_v1 = df_f[df_f['Venceu_Primeiro_Round'] == 'Sim']
    df_p1 = df_f[df_f['Venceu_Primeiro_Round'] == 'Não']

    cr1, cr2 = st.columns(2)
    with cr1:
        tx = wr(df_v1)
        st.metric("Win Rate SE vencer o 1º Round", f"{tx:.1f}%")
        st.caption(f"🎯 {(df_v1['Meu_Resultado']=='Vitória 🏆').sum()} vitórias de {len(df_v1)} partidas")
    with cr2:
        tx = wr(df_p1)
        st.metric("Win Rate SE perder o 1º Round", f"{tx:.1f}%")
        st.caption(f"🎯 {(df_p1['Meu_Resultado']=='Vitória 🏆').sum()} vitórias de {len(df_p1)} partidas")

    # ── 10b — Trajetória da Partida ───────────────────────────────────────────
    st.markdown("#### 🔄 Trajetória da Partida")

    cseq = df_f['Sequencia_Rounds'].value_counts().reset_index()
    cseq.columns = ['Seq', 'Qtd']

    trad = {
        "V-V":   "Vitória Limpa 2-0",
        "V-D-V": "Vitória Suada 2-1",
        "V-D-D": "Tomou Virada 1-2",
        "D-D":   "Derrota Limpa 0-2",
        "D-V-D": "Reagiu mas Perdeu",
        "D-V-V": "Virada Épica 2-1",
    }
    cores_s = {
        "V-V":   "#19a50d", "V-D-V": "#005fcc", "D-V-V": "#9c00cc",
        "D-D":   "#ac1f06", "D-V-D": "#4d2d27", "V-D-D": "#efec3b",
    }

    cseq['Desc'] = cseq['Seq'].map(trad).fillna(cseq['Seq'])
    cseq = cseq[cseq['Seq'] != "Sem dados"]

    if not cseq.empty:
        cs1, cs2 = st.columns(2)
        with cs1:
            fig = px.bar(
                cseq, x='Qtd', y='Desc', color='Seq',
                color_discrete_map=cores_s,
                orientation='h', template="plotly_dark", height=280,
                custom_data=['Seq']
            )
            fig.update_traces(
                texttemplate='<b>%{x}</b>', textposition="outside", textfont_color="white",
                hovertemplate="<b>%{customdata[0]}</b><br>%{x} partidas<extra></extra>"
            )
            fig.update_layout(
                showlegend=False,
                yaxis=dict(categoryorder='total ascending', title=''),
                xaxis=dict(showticklabels=False, title=''),
                margin=dict(l=10, r=10, t=10, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)

        with cs2:
            fig = px.pie(
                cseq, values='Qtd', names='Desc', color='Seq',
                color_discrete_map=cores_s,
                template="plotly_dark", height=280
            )
            fig.update_traces(
                textinfo='percent', textfont_color="white",
                marker_line_color='white', marker_line_width=0.5,
                hovertemplate="<b>%{label}</b><br>%{value} partidas<extra></extra>"
            )
            fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)

    # ── 10c — Como os Rounds Foram Decididos ──────────────────────────────────
    st.markdown("#### 💥 Como os Rounds Foram Decididos")

    def ex_g(t):
        if pd.isna(t) or t in ("Nenhum", "Sem dados"): return []
        return [g.strip() for g in str(t).split(',')]

    dg = df_f[['Meus_Golpes_Finais', 'Golpes_Oponente']].copy()
    dg['M'] = dg['Meus_Golpes_Finais'].apply(ex_g)
    dg['O'] = dg['Golpes_Oponente'].apply(ex_g)

    dmg = dg.explode('M')['M'].value_counts().reset_index()
    dmg.columns = ['G', 'Q']
    dmg = dmg.sort_values('Q', ascending=True)

    dog = dg.explode('O')['O'].value_counts().reset_index()
    dog.columns = ['G', 'Q']
    dog = dog.sort_values('Q', ascending=True)

    cg1, cg2 = st.columns(2)
    with cg1:
        if not dmg.empty:
            fig = px.bar(
                dmg, x='Q', y='G', orientation='h',
                title=f"Como VOCÊ finalizou rounds ({dmg['Q'].sum()})",
                template="plotly_dark", color_discrete_sequence=["#00cc96"]
            )
            fig.update_traces(
                texttemplate='<b>%{x}</b>', textposition="outside", textfont_color="white",
                hovertemplate="<b>%{y}</b><br>%{x} rounds<extra></extra>"
            )
            fig.update_layout(
                xaxis=dict(showticklabels=False, title=''),
                yaxis=dict(title=''),
                margin=dict(l=10, r=10, t=40, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)

    with cg2:
        if not dog.empty:
            fig = px.bar(
                dog, x='Q', y='G', orientation='h',
                title=f"Como o OPONENTE finalizou rounds ({dog['Q'].sum()})",
                template="plotly_dark", color_discrete_sequence=["#ef553b"]
            )
            fig.update_traces(
                texttemplate='<b>%{x}</b>', textposition="outside", textfont_color="white",
                hovertemplate="<b>%{y}</b><br>%{x} rounds<extra></extra>"
            )
            fig.update_layout(
                xaxis=dict(showticklabels=False, title=''),
                yaxis=dict(title=''),
                margin=dict(l=10, r=10, t=40, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 11 — LADO DA TELA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 📺 Lado da Tela — P1 vs P2")

if total > 0:
    df_l = df_f['Meu_Lado'].value_counts().reset_index()
    df_l.columns = ['Lado', 'Quantidade']
    cores_l = {"Player 1": "#3498DB", "Player 2": "#E74C3C"}

    cl1, cl2 = st.columns(2)
    with cl1:
        fig = px.pie(
            df_l, values='Quantidade', names='Lado',
            color='Lado', color_discrete_map=cores_l,
            title="P1 / P2", template="plotly_dark", height=280
        )
        fig.update_traces(
            textinfo='percent+label', textfont_color="white",
            marker_line_color='white', marker_line_width=0.5,
            hovertemplate="<b>%{label}</b><br>%{value} partidas<extra></extra>"
        )
        fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with cl2:
        st.write("")
        st.write("")
        for lado in ["Player 1", "Player 2"]:
            sub = df_f[df_f['Meu_Lado'] == lado]
            tx  = wr(sub)
            lb  = "Esquerda (P1)" if lado == "Player 1" else "Direita (P2)"
            st.metric(f"Win Rate como {lb}", f"{tx:.1f}%")
            st.caption(f"🎯 {(sub['Meu_Resultado']=='Vitória 🏆').sum()} vitórias de {len(sub)} partidas")
            st.write("")

    df_p1d = df_f[df_f['Meu_Lado'].astype(str).str.contains('1')]
    if not df_p1d.empty:
        with st.expander(f"📋 Oponentes como P1 ({len(df_p1d)} partidas)"):
            gp1 = df_p1d.groupby('Oponente_Nome').agg(
                Partidas = ('Meu_Resultado', 'count'),
                Vitórias = ('Meu_Resultado', lambda x: (x == "Vitória 🏆").sum()),
                Derrotas = ('Meu_Resultado', lambda x: (x == "Derrota ❌").sum())
            ).reset_index().sort_values('Partidas', ascending=False)
            st.dataframe(gp1, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 12 — OPONENTES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🎯 Oponentes — Jogadores Enfrentados")

if total > 0:
    MIN_PARTIDAS = 5  # mínimo de confrontos para entrar nos rankings

    # ── Agrega dados por oponente ─────────────────────────────────────────────
    df_rv = df_f.groupby('Oponente_Nome').agg(
        Partidas = ('Meu_Resultado', 'count'),
        Vitórias = ('Meu_Resultado', lambda x: (x == "Vitória 🏆").sum()),
        Derrotas = ('Meu_Resultado', lambda x: (x == "Derrota ❌").sum()),
    ).reset_index()
    df_rv['WR_Pct']    = (df_rv['Vitórias'] / df_rv['Partidas'] * 100).round(1)
    df_rv['Derrota_Pct'] = (df_rv['Derrotas'] / df_rv['Partidas'] * 100).round(1)
    df_rv['']          = df_rv['WR_Pct'].apply(semaforo)
    df_rv['WR (%)']    = df_rv['WR_Pct'].apply(lambda x: f"{x:.1f}%")

    df_min = df_rv[df_rv['Partidas'] >= MIN_PARTIDAS].copy()

    # ── 4 métricas rápidas ────────────────────────────────────────────────────
    # Destaques usam valores ABSOLUTOS (mais robustos que % com pouco volume).
    # As taxas percentuais aparecem nos Top 5 abaixo, com contexto completo.
    me = df_rv.loc[df_rv['Partidas'].idxmax()]

    if not df_min.empty:
        fre_abs = df_min.loc[df_min['Vitórias'].idxmax()]   # mais vitórias absolutas
        nem_abs = df_min.loc[df_min['Derrotas'].idxmax()]   # mais derrotas absolutas
        df_eq   = df_min.copy()
        df_eq['D50'] = abs(df_eq['WR_Pct'] - 50)
        eq = df_eq.sort_values(['D50', 'Partidas'], ascending=[True, False]).iloc[0]
    else:
        fre_abs = nem_abs = eq = None

    co1, co2, co3, co4 = st.columns(4)
    with co1:
        st.metric("Mais Enfrentado", me['Oponente_Nome'])
        st.caption(f"⚔️ {me['Partidas']} partidas")
    with co2:
        if fre_abs is not None:
            st.metric("Maior Freguês", fre_abs['Oponente_Nome'])
            st.caption(f"🏆 {fre_abs['Vitórias']} vitórias em {fre_abs['Partidas']} partidas ({fre_abs['WR_Pct']:.0f}%)")
        else:
            st.metric("Maior Freguês", "—")
            st.caption(f"Mín. {MIN_PARTIDAS} partidas")
    with co3:
        if nem_abs is not None:
            st.metric("Maior Nêmesis", nem_abs['Oponente_Nome'])
            st.caption(f"💀 {nem_abs['Derrotas']} derrotas em {nem_abs['Partidas']} partidas ({nem_abs['Derrota_Pct']:.0f}%)")
        else:
            st.metric("Maior Nêmesis", "—")
            st.caption(f"Mín. {MIN_PARTIDAS} partidas")
    with co4:
        if eq is not None:
            st.metric("Rivalidade Equilibrada", eq['Oponente_Nome'])
            st.caption(f"⚖️ {eq['WR_Pct']:.0f}% em {eq['Partidas']} partidas")
        else:
            st.metric("Rivalidade Equilibrada", "—")
            st.caption(f"Mín. {MIN_PARTIDAS} partidas")

    st.divider()

    # ── Top 5 — Mais Confrontados ─────────────────────────────────────────────
    st.markdown(f"#### ⚔️ Top 5 — Mais Confrontados (mín. {MIN_PARTIDAS} partidas)")
    if not df_min.empty:
        top_conf = df_min.nlargest(5, 'Partidas')[
            ['', 'Oponente_Nome', 'Partidas', 'Vitórias', 'Derrotas', 'WR (%)', 'WR_Pct']
        ]
        st.dataframe(top_conf, use_container_width=True, hide_index=True,
                     column_config={"WR_Pct": None})
    else:
        st.info(f"Nenhum oponente com {MIN_PARTIDAS}+ confrontos nos filtros atuais.")

    st.divider()

    # ── Top 5 — Fregueses ─────────────────────────────────────────────────────
    st.markdown(f"#### 🏆 Top 5 — Fregueses (mín. {MIN_PARTIDAS} partidas)")
    if not df_min.empty:
        tf1, tf2 = st.columns(2)
        with tf1:
            st.caption("Por vitórias absolutas")
            top_fre_abs = df_min.nlargest(5, 'Vitórias')[
                ['', 'Oponente_Nome', 'Partidas', 'Vitórias', 'WR (%)', 'WR_Pct']
            ]
            st.dataframe(top_fre_abs, use_container_width=True, hide_index=True,
                         column_config={"WR_Pct": None})
        with tf2:
            st.caption("Por % de vitória")
            top_fre_pct = df_min.nlargest(5, 'WR_Pct')[
                ['', 'Oponente_Nome', 'Partidas', 'Vitórias', 'WR (%)', 'WR_Pct']
            ]
            st.dataframe(top_fre_pct, use_container_width=True, hide_index=True,
                         column_config={"WR_Pct": None})
    else:
        st.info(f"Nenhum oponente com {MIN_PARTIDAS}+ confrontos nos filtros atuais.")

    st.divider()

    # ── Top 5 — Nêmesis ───────────────────────────────────────────────────────
    st.markdown(f"#### 💀 Top 5 — Nêmesis (mín. {MIN_PARTIDAS} partidas)")
    if not df_min.empty:
        tn1, tn2 = st.columns(2)
        with tn1:
            st.caption("Por derrotas absolutas")
            top_nem_abs = df_min.nlargest(5, 'Derrotas')[
                ['', 'Oponente_Nome', 'Partidas', 'Derrotas', 'WR (%)', 'Derrota_Pct']
            ]
            top_nem_abs['Derrota (%)'] = top_nem_abs['Derrota_Pct'].apply(lambda x: f"{x:.1f}%")
            st.dataframe(
                top_nem_abs[['', 'Oponente_Nome', 'Partidas', 'Derrotas', 'Derrota (%)']],
                use_container_width=True, hide_index=True
            )
        with tn2:
            st.caption("Por % de derrota")
            top_nem_pct = df_min.nlargest(5, 'Derrota_Pct')[
                ['', 'Oponente_Nome', 'Partidas', 'Derrotas', 'Derrota_Pct']
            ]
            top_nem_pct['Derrota (%)'] = top_nem_pct['Derrota_Pct'].apply(lambda x: f"{x:.1f}%")
            st.dataframe(
                top_nem_pct[['', 'Oponente_Nome', 'Partidas', 'Derrotas', 'Derrota (%)']],
                use_container_width=True, hide_index=True
            )
    else:
        st.info(f"Nenhum oponente com {MIN_PARTIDAS}+ confrontos nos filtros atuais.")

    st.divider()

    # ── Top 5 — Rivalidades Equilibradas ─────────────────────────────────────
    st.markdown(f"#### ⚖️ Top 5 — Rivalidades Equilibradas (mín. {MIN_PARTIDAS} partidas)")
    st.caption("Oponentes com WR mais próximo de 50% — ninguém domina a série.")
    if not df_min.empty:
        df_eq_top = df_min.copy()
        df_eq_top['Dist_50'] = abs(df_eq_top['WR_Pct'] - 50)
        top_eq = df_eq_top.nsmallest(5, 'Dist_50')[
            ['', 'Oponente_Nome', 'Partidas', 'Vitórias', 'Derrotas', 'WR (%)', 'WR_Pct']
        ]
        st.dataframe(top_eq, use_container_width=True, hide_index=True,
                     column_config={"WR_Pct": None})
    else:
        st.info(f"Nenhum oponente com {MIN_PARTIDAS}+ confrontos nos filtros atuais.")

    st.divider()

    # ── Jogadores por Dia da Semana ───────────────────────────────────────────
    st.markdown("#### 📅 Jogadores por Dia da Semana")
    st.caption(
        "O mesmo jogador pode aparecer em vários dias. "
        "Útil para lembrar em qual dia você enfrentou alguém específico."
    )

    ORDEM_DIAS = ['Segunda-feira','Terça-feira','Quarta-feira','Quinta-feira',
                  'Sexta-feira','Sábado','Domingo']

    # Monta dicionário dia → lista de jogadores únicos ordenados
    jogadores_por_dia = {}
    for dia in ORDEM_DIAS:
        df_dia = df_f[df_f['Dia da Semana'] == dia]
        if df_dia.empty:
            jogadores_por_dia[dia] = []
        else:
            jogadores_por_dia[dia] = sorted(df_dia['Oponente_Nome'].dropna().unique().tolist())

    # Métricas de jogadores únicos por dia
    cols_metricas = st.columns(7)
    for idx, dia in enumerate(ORDEM_DIAS):
        qtd = len(jogadores_por_dia[dia])
        with cols_metricas[idx]:
            st.metric(
                label=dia[:3],  # abreviação: Seg, Ter, Qua...
                value=f"{qtd}",
                help=f"{dia} — {qtd} jogadores únicos"
            )

    # DataFrame transposto — dias como colunas, jogadores nas linhas
    max_linhas = max((len(v) for v in jogadores_por_dia.values()), default=0)

    if max_linhas > 0:
        df_dias_jogadores = pd.DataFrame({
            dia[:3]: (
                jogadores_por_dia[dia] +
                [''] * (max_linhas - len(jogadores_por_dia[dia]))
            )
            for dia in ORDEM_DIAS
        })

        st.dataframe(
            df_dias_jogadores,
            use_container_width=True,
            hide_index=True,
            height=min(max_linhas * 35 + 38, 500),  # altura proporcional, máx 500px
        )
        st.caption("⚠️ Células vazias indicam que o dia teve menos jogadores que o dia com mais confrontos.")
    else:
        st.info("Nenhum dado disponível para os filtros selecionados.")


# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 13 — BUSCA DE CONFRONTOS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🔍 Histórico Detalhado contra um Oponente")

lista_busca = sorted(df_f['Oponente_Nome'].dropna().unique())
busca = st.selectbox(
    "Selecione um oponente:",
    options=lista_busca, index=None,
    placeholder="Digite para filtrar..."
)

if busca:
    db = df_f[df_f['Oponente_Nome'] == busca].sort_values(
        ['Data', 'Hora Exata'], ascending=[False, False]
    )
    vb   = (db['Meu_Resultado'] == "Vitória 🏆").sum()
    dbb  = (db['Meu_Resultado'] == "Derrota ❌").sum()
    wr_b = vb / len(db) * 100 if len(db) > 0 else 0

    # Personagem mais usado pelo oponente (para a arte grande)
    char_mais_usado = db['Oponente_Personagem'].value_counts().idxmax()
    cor_char        = cor_personagem(char_mais_usado)

    # ── Cabeçalho: full body do main + métricas ───────────────────────────────
    col_arte, col_metricas = st.columns([1, 3])

    with col_arte:
        path_full = f"assets/characters/full/{char_mais_usado}.png"
        if os.path.exists(path_full):
            st.image(Image.open(path_full).convert("RGBA"), use_container_width=True)
        else:
            # fallback para portrait se não tiver full body
            path_portrait = f"assets/characters/portrait/{char_mais_usado}.png"
            if os.path.exists(path_portrait):
                st.image(Image.open(path_portrait).convert("RGBA"), width=120)
        st.markdown(
            f'<div style="text-align:center;color:{cor_char};font-weight:700;'
            f'font-size:13px;margin-top:4px;">{char_mais_usado.upper()}</div>',
            unsafe_allow_html=True
        )
        st.caption(f"<div style='text-align:center;'>Personagem mais usado</div>",
                   unsafe_allow_html=True)

    with col_metricas:
        st.markdown(f"#### vs **{busca}**")
        mb1, mb2, mb3, mb4 = st.columns(4)
        mb1.metric("Confrontos",  len(db))
        mb2.metric("Vitórias 🏆", vb)
        mb3.metric("Derrotas ❌", dbb)
        mb4.metric("Win Rate",    f"{wr_b:.1f}%")

        # Personagens que o oponente usou
        chars_op = db['Oponente_Personagem'].value_counts()
        chars_txt = " · ".join([f"{c} ({n})" for c, n in chars_op.items()])
        st.caption(f"🎭 Personagens usados por {busca}: {chars_txt}")

        # MR range do oponente nessas partidas
        mrs = db[db['Oponente_MR'] > 0]['Oponente_MR']
        if not mrs.empty:
            st.caption(f"📊 MR do oponente: {int(mrs.min())} – {int(mrs.max())}")

    st.write("")

    # ── Lista de confrontos individuais ───────────────────────────────────────
    for _, row in db.iterrows():
        ic = ("🟢" if "Vitória" in row['Meu_Resultado']
              else "🔴" if "Derrota" in row['Meu_Resultado']
              else "⚪")

        label = (
            f"{ic} {row['Data']} {row['Hora Exata']} | "
            f"{row['Meu_Personagem']} vs {row['Oponente_Personagem']} | "
            f"{row['Placar']}"
        )

        with st.expander(label):

            # Reconstrói rounds a partir da sequência e golpes finais
            seq_str = str(row.get('Sequencia_Rounds', ''))
            seq     = [s.strip() for s in seq_str.split('-') if s.strip() in ('V','D')] \
                      if seq_str not in ('', 'Sem dados') else []

            meus_golpes = [g.strip() for g in str(row.get('Meus_Golpes_Finais','')).split(',')
                           if g.strip() not in ('', 'Nenhum', 'Sem dados', 'Erro de Leitura')]
            op_golpes   = [g.strip() for g in str(row.get('Golpes_Oponente','')).split(',')
                           if g.strip() not in ('', 'Nenhum', 'Sem dados', 'Erro de Leitura')]

            meus_iter = iter(meus_golpes)
            op_iter   = iter(op_golpes)
            rounds = []
            for r in seq:
                if r == 'V':
                    rounds.append({'meu': next(meus_iter, 'Vitória'), 'op': ''})
                else:
                    rounds.append({'meu': '', 'op': next(op_iter, 'Vitória')})

            cor_meu = cor_personagem(row['Meu_Personagem'])
            cor_op  = cor_personagem(row['Oponente_Personagem'])

            col_eu, col_op, col_info = st.columns([1, 1, 2])

            with col_eu:
                st.markdown(
                    f'<div style="color:{cor_meu};font-weight:700;font-size:12px;'
                    f'margin-bottom:4px;">{row["Meu_Nome"].upper()}</div>',
                    unsafe_allow_html=True
                )
                path_meu = f"assets/characters/portrait/{row['Meu_Personagem']}.png"
                if os.path.exists(path_meu):
                    st.image(Image.open(path_meu).convert("RGBA"), width=80)
                st.markdown(
                    f'<span style="color:{cor_meu};font-weight:700;font-size:11px;">'
                    f'{row["Meu_Personagem"].upper()}</span>',
                    unsafe_allow_html=True
                )
                st.write("")
                for i, r in enumerate(rounds, 1):
                    if r['meu']:
                        st.markdown(f"**Round {i}:** {r['meu']}")
                    else:
                        st.markdown(f"Round {i}: —")

            with col_op:
                st.markdown(
                    f'<div style="color:{cor_op};font-weight:700;font-size:12px;'
                    f'margin-bottom:4px;">{row["Oponente_Nome"].upper()}</div>',
                    unsafe_allow_html=True
                )
                path_op = f"assets/characters/portrait/{row['Oponente_Personagem']}.png"
                if os.path.exists(path_op):
                    st.image(Image.open(path_op).convert("RGBA"), width=80)
                st.markdown(
                    f'<span style="color:{cor_op};font-weight:700;font-size:11px;">'
                    f'{row["Oponente_Personagem"].upper()}</span>',
                    unsafe_allow_html=True
                )
                st.write("")
                for i, r in enumerate(rounds, 1):
                    if r['op']:
                        st.markdown(f"**Round {i}:** {r['op']}")
                    else:
                        st.markdown(f"Round {i}: —")

            with col_info:
                st.write("")
                st.markdown(f"**Modo:** {row['Tipo Partida (Jogo)']}")
                st.markdown(f"**Resultado:** {row['Meu_Resultado']}")
                st.markdown(f"**Placar:** {row['Placar']}")
                st.markdown(f"**MR Oponente:** {row['Oponente_MR']}")
                if cols_on.get("Nível"):
                    st.markdown(f"**Nível:** {row.get('Nivel_Oponente','—')}")
                if cols_on.get("Tier"):
                    st.markdown(f"**Tier:** {row.get('Tier_Oponente','—')}")
                if cols_on.get("Mirror Match"):
                    st.markdown(f"**Mirror:** {'Sim 🪞' if row.get('Mirror_Match') else 'Não'}")


# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 14 — HISTÓRICO COMPLETO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 📋 Histórico Detalhado")

if total > 0:
    colunas_base = [
        'Data', 'Hora Exata', 'Tipo Partida (Jogo)', 'Turno',
        'Meu_Resultado', 'Placar',
        'Meu_Personagem', 'Meu_MR',
        'Oponente_Nome', 'Oponente_Personagem', 'Oponente_MR', 'Oponente_Rank_Nome',
        'Numero_Partida_No_Dia', 'Streak_Atual',
        'Venceu_Primeiro_Round', 'Sequencia_Rounds',
    ]
    if cols_on.get("Nível"):        colunas_base.append('Nivel_Oponente')
    if cols_on.get("Tier"):         colunas_base.append('Tier_Oponente')
    if cols_on.get("Arquétipo"):    colunas_base.append('Arquetipo_Oponente')
    if cols_on.get("Mirror Match"): colunas_base.append('Mirror_Match')

    colunas_ok = [c for c in colunas_base if c in df_f.columns]

    st.dataframe(
        df_f[colunas_ok].sort_values(['Data', 'Hora Exata'], ascending=[False, False]),
        use_container_width=True, hide_index=True
    )
    st.caption(f"📊 {total:,} partidas exibidas com os filtros atuais.".replace(",","."))

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO — OS 3 PERSONAGENS MAIS USADOS
# Fixa em ranqueadas da temporada atual — filtros globais não se aplicam.
# Tier e Arquétipo SEGUEM as Configurações (mudam se o usuário ajustar lá).
# Depende de: df_base, cor_personagem(), arq_map, tier_map, semaforo(), ORDEM_TIER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### ⚔️ Os 3 Personagens Mais Usados")
aviso_importante(
    "Compara os personagens mais usados em ranqueada na temporada atual. "
    "Filtros da sidebar não se aplicam, mas a Tier List e os Arquétipos "
    "seguem o que estiver configurado em ⚙️ Configurações."
)

# ── Base: ranqueadas da temporada mais recente ────────────────────────────────
df_mains = df_base[df_base['Tipo Partida (Jogo)'] == 'Ranqueada'].copy()

if 'Temporada' in df_mains.columns and not df_mains['Temporada'].dropna().empty:
    temp_atual = sorted(df_mains['Temporada'].dropna().unique(), reverse=True)[0]
    df_mains   = df_mains[df_mains['Temporada'] == temp_atual]
    st.caption(f"📅 Temporada analisada: **{temp_atual}**")
else:
    temp_atual = None

if df_mains.empty:
    st.info("Nenhuma partida ranqueada na temporada atual.")
else:
    # ── Filtro local de mínimo de partidas ────────────────────────────────────
    col_min, _ = st.columns([1, 3])
    with col_min:
        min_conf = st.slider(
            "Mín. de confrontos para análise:",
            min_value=3, max_value=15, value=5, step=1,
            key="min_conf_mains",
            help="Só conta matchups com pelo menos este número de partidas"
        )

    # ── Top 3 personagens mais usados ─────────────────────────────────────────
    top3 = df_mains['Meu_Personagem'].value_counts().head(3).index.tolist()

    if not top3:
        st.info("Sem personagens suficientes para comparar.")
    else:
        def wr_pct(sub):
            t = len(sub)
            return (sub['Meu_Resultado'] == "Vitória 🏆").sum() / t * 100 if t > 0 else 0.0

        # Garante colunas dinâmicas (seguem as Configurações via arq_map/tier_map)
        if 'Arquetipo_Oponente' not in df_mains.columns:
            df_mains['Arquetipo_Oponente'] = (
                df_mains['Oponente_Personagem'].map(arq_map).fillna("Desconhecido")
            )
        if 'Tier_Oponente' not in df_mains.columns:
            df_mains['Tier_Oponente'] = (
                df_mains['Oponente_Personagem'].map(tier_map).fillna("?")
            )

        def analisa_personagem(personagem):
            """Métricas de desempenho — só matchup específico nos cards."""
            sub = df_mains[df_mains['Meu_Personagem'] == personagem]
            resultado = {
                'wr_geral': wr_pct(sub),
                'partidas': len(sub),
                'vitorias': (sub['Meu_Resultado'] == "Vitória 🏆").sum(),
            }
            char_stats = []
            for char, grupo in sub.groupby('Oponente_Personagem'):
                if len(grupo) >= min_conf:
                    char_stats.append((char, wr_pct(grupo), len(grupo)))
            char_stats.sort(key=lambda x: x[1], reverse=True)
            resultado['melhor_char'] = char_stats[0]  if char_stats else None
            resultado['pior_char']   = char_stats[-1] if char_stats else None
            resultado['tem_char']    = len(char_stats) > 0
            return resultado

        analises = {p: analisa_personagem(p) for p in top3}

        # ── Cards lado a lado — WR geral + melhor/pior matchup específico ──────
        cols = st.columns(len(top3))
        for idx, personagem in enumerate(top3):
            a   = analises[personagem]
            cor = cor_personagem(personagem)
            with cols[idx]:
                path = f"assets/characters/portrait/{personagem}.png"
                if os.path.exists(path):
                    st.image(Image.open(path).convert("RGBA"), width=90)
                st.markdown(
                    f'<div style="color:{cor};font-weight:700;font-size:15px;">'
                    f'{personagem.upper()}</div>',
                    unsafe_allow_html=True
                )
                st.metric("WR Geral", f"{a['wr_geral']:.1f}%")
                st.caption(f"🎯 {a['vitorias']} vitórias em {a['partidas']} partidas")

                st.markdown("---")

                if a['tem_char']:
                    char, w, n = a['melhor_char']
                    st.markdown(f"🥇 **Melhor matchup:** {char}")
                    st.caption(f"{semaforo(w)} {w:.1f}% em {n} partidas")
                    if a['pior_char'] and a['pior_char'] != a['melhor_char']:
                        char, w, n = a['pior_char']
                        st.markdown(f"🥊 **Pior matchup:** {char}")
                        st.caption(f"{semaforo(w)} {w:.1f}% em {n} partidas")
                else:
                    st.caption(
                        f"⚠️ Nenhum matchup específico com {min_conf}+ confrontos. "
                        f"Baixe o mínimo para ver mais."
                    )

        st.divider()

        # ── Helper genérico de recomendação por categoria ─────────────────────
        def tabela_recomendacao(coluna_categoria, valores_ordenados=None, label="Categoria"):
            """Para cada valor da categoria, qual main tem melhor WR (mín. confrontos)."""
            categorias = (
                valores_ordenados if valores_ordenados is not None
                else sorted(df_mains[df_mains[coluna_categoria] != "Desconhecido"][coluna_categoria].dropna().unique())
            )
            linhas = []
            for cat in categorias:
                melhor_p, melhor_wr, melhor_n = None, -1, 0
                cobertura = []  # personagens que tiveram dados suficientes
                for personagem in top3:
                    sub = df_mains[
                        (df_mains['Meu_Personagem'] == personagem) &
                        (df_mains[coluna_categoria] == cat)
                    ]
                    if len(sub) >= min_conf:
                        cobertura.append(personagem)
                        w = wr_pct(sub)
                        if w > melhor_wr:
                            melhor_p, melhor_wr, melhor_n = personagem, w, len(sub)
                if melhor_p is not None:
                    # Monta a observação listando quais mains tiveram dados
                    if len(cobertura) == len(top3):
                        obs = f"Todos tiveram {min_conf}+ partidas"
                    elif len(cobertura) == 1:
                        obs = f"Só {cobertura[0]} teve {min_conf}+ partidas"
                    else:
                        # 2 ou mais (mas não todos) — lista os nomes
                        if len(cobertura) > 2:
                            nomes = ", ".join(cobertura[:-1]) + " e " + cobertura[-1]
                        else:
                            nomes = " e ".join(cobertura)
                        obs = f"Só {nomes} tiveram {min_conf}+ partidas"
                    linhas.append({
                        label:       str(cat),
                        'Use':       melhor_p,
                        'Win Rate':  f"{melhor_wr:.1f}%",
                        'Partidas':  melhor_n,
                        'Observação': obs,
                    })
            return pd.DataFrame(linhas)

        # ── 3 tabelas de recomendação empilhadas ──────────────────────────────
        st.markdown("#### 💡 Recomendação de Uso")
        st.caption(f"Qual dos seus {len(top3)} mains rende mais em cada categoria (mín. {min_conf} confrontos).")

        # Tabela 1 — Por Arquétipo
        st.markdown("##### 🥋 Por Arquétipo")
        df_arq_rec = tabela_recomendacao('Arquetipo_Oponente', label='Arquétipo')
        if not df_arq_rec.empty:
            st.dataframe(df_arq_rec, use_container_width=True, hide_index=True)
        else:
            st.info(f"Nenhum arquétipo com {min_conf}+ confrontos. Baixe o mínimo.")

        st.write("")

        # Tabela 2 — Por Tier
        st.markdown("##### 🏆 Por Tier")
        tiers_ordenados = [t for t in ORDEM_TIER
                           if t in df_mains['Tier_Oponente'].unique()]
        df_tier_rec = tabela_recomendacao('Tier_Oponente', tiers_ordenados, label='Tier')
        if not df_tier_rec.empty:
            st.dataframe(df_tier_rec, use_container_width=True, hide_index=True)
        else:
            st.info(f"Nenhum tier com {min_conf}+ confrontos. Baixe o mínimo.")

        st.write("")

        # Tabela 3 — Por Personagem
        st.markdown("##### 🎯 Por Personagem")
        df_char_rec = tabela_recomendacao('Oponente_Personagem', label='Personagem')
        if not df_char_rec.empty:
            st.dataframe(df_char_rec, use_container_width=True, hide_index=True)
            st.caption("⚠️ Personagens específicos podem ter amostras menores — confira a coluna Partidas.")
        else:
            st.info(f"Nenhum personagem com {min_conf}+ confrontos. Baixe o mínimo.")
