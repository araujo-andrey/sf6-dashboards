import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_sortables import sort_items

# ══════════════════════════════════════════════════════════════════════════════
# ⚙️  PÁGINA
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="SF6 – Análise de Desempenho", layout="wide", page_icon="❄️")
st.title("📊 Análise de Desempenho – Street Fighter 6")

with st.expander("📌 Informações sobre a Base de Dados", expanded=False):
    st.markdown("""
    * ⚠️ **Limite:** A Capcom disponibiliza apenas as últimas 100 partidas por modo de jogo: **Ranqueada, Casual, Sala Personalizada e Battle Hub**.
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
    "All-Rounder": ["Ryu","Ken","Akuma","Terry","Ed","Mai", "Luke","Chun-Li","Sagat"],
    "Rushdown":    ["Cammy","Juri","Kimberly","Rashid","Dee Jay", "Jamie","M. Bison"],
    "Grappler":    ["Zangief","Marisa","Manon","Lily","Alex"],
    "Zoner":       ["Guile","Dhalsim","JP"],
    "Unorthodox":  ["Elena","A.K.I.","Blanka","Edmond Honda", "C. Viper"],
}

TIER_PADRAO = {
    "S+": ["JP","Ed"],
    "S":  ["Blanka","Sagat","M. Bison","Terry","Mai","Akuma","Guile","Rashid","C. Viper"],
    "A":  ["Dee Jay","Ryu","Kimberly","Juri","Dhalsim","Ken","Cammy","Zangief","Alex"],
    "B":  ["Chun-Li","Jamie","Luke","Elena","A.K.I."],
    "C":  ["Manon","Lily","Edmond Honda"],
    "D":  ["Marisa"],
    "E":  [],
}

TODOS_PERSONAGENS = sorted([p for v in ARQUETIPOS_PADRAO.values() for p in v])

CORES_TIER = {
    "S+": "#8C00FF",
    "S":  "#FF0000",
    "A":  "#FF9100",
    "B":  "#DEEE05",
    "C":  "#63F52A",
    "D":  "#308F0B",
    "E":  "#2C3E50",
}

# ══════════════════════════════════════════════════════════════════════════════
# ⚙️  SESSION STATE — inicializa configs padrão
# ══════════════════════════════════════════════════════════════════════════════
def init_state():
    if 'arq_config'    not in st.session_state:
        st.session_state.arq_config  = {k: list(v) for k,v in ARQUETIPOS_PADRAO.items()}
    if 'tier_config'   not in st.session_state:
        st.session_state.tier_config = {k: list(v) for k,v in TIER_PADRAO.items()}
    if 'wr_verde'      not in st.session_state: st.session_state.wr_verde  = 55
    if 'wr_amarelo'    not in st.session_state: st.session_state.wr_amarelo= 45
    if 'lim_muito_inf' not in st.session_state: st.session_state.lim_muito_inf = -200
    if 'lim_inf'       not in st.session_state: st.session_state.lim_inf       = -75
    if 'lim_sup'       not in st.session_state: st.session_state.lim_sup       =  75
    if 'lim_muito_sup' not in st.session_state: st.session_state.lim_muito_sup =  200
    if 'chat_votos'    not in st.session_state: pass  # removido
    if 'cols_ativas'   not in st.session_state:
        st.session_state.cols_ativas = {
            "Tier": True, "Arquétipo": True, "Nível": True, "Mirror Match": True
        }

init_state()

# ══════════════════════════════════════════════════════════════════════════════
# ⚙️  PAINEL DE CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("⚙️ Configurações — Personalize tudo aqui", expanded=False):

    tab_semaforo, tab_nivel, tab_arq, tab_tier, tab_cols = st.tabs([
        "🚦 Semáforo de Win Rate",
        "🎯 Faixas de Nível",
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
        with cs2:
            st.markdown("🟡 **Média — Win Rate ≥**")
            novo_amarelo = st.number_input("Amarelo (%)", min_value=1, max_value=100,
                                            value=st.session_state.wr_amarelo, step=1,
                                            label_visibility="collapsed")
        with cs3:
            st.markdown("🔴 **Ruim — Win Rate <**")
            st.markdown(f"### {novo_amarelo}%")
            st.caption("(automático — abaixo do amarelo)")

        st.write("")
        if st.button("💾 Salvar limites do semáforo"):
            st.session_state.wr_verde   = novo_verde
            st.session_state.wr_amarelo = novo_amarelo
            st.success(f"✅ Semáforo: 🟢 ≥{novo_verde}% · 🟡 ≥{novo_amarelo}% · 🔴 <{novo_amarelo}%")

    # ── Faixas de nível ───────────────────────────────────────────────────────
    with tab_nivel:
        st.markdown("Diferença de MR = **MR oponente − seu MR**. Negativo = oponente mais fraco.")
        st.caption("As 5 faixas são definidas pelos 4 limites abaixo. 'Muito Superior' é automático: qualquer valor acima do limite de Superior.")
        st.write("")
        cn1,cn2,cn3,cn4 = st.columns(4)
        with cn1:
            st.markdown("**🔵 Muito Inferior**")
            st.caption("Diferença ≤ este valor")
            n_mi = st.number_input("MI", value=st.session_state.lim_muito_inf, step=25, label_visibility="collapsed")
        with cn2:
            st.markdown("**🟢 Inferior**")
            st.caption("Entre Muito Inf. e este valor")
            n_i  = st.number_input("I",  value=st.session_state.lim_inf,       step=25, label_visibility="collapsed")
        with cn3:
            st.markdown("**🟡 Similar**")
            st.caption("Entre Inferior e este valor")
            n_s  = st.number_input("S",  value=st.session_state.lim_sup,       step=25, label_visibility="collapsed")
        with cn4:
            st.markdown("**🟠 Superior**")
            st.caption("Entre Similar e este valor")
            n_ms = st.number_input("MS", value=st.session_state.lim_muito_sup, step=25, label_visibility="collapsed")
        st.info(f"🔴 **Muito Superior** = diferença **acima de {st.session_state.lim_muito_sup}** MR (automático)")
        st.write("")
        if st.button("💾 Salvar faixas de nível"):
            st.session_state.lim_muito_inf = n_mi
            st.session_state.lim_inf       = n_i
            st.session_state.lim_sup       = n_s
            st.session_state.lim_muito_sup = n_ms
            st.success("✅ Faixas atualizadas!")
            st.rerun()

    # ── Arquétipos (drag-and-drop) ────────────────────────────────────────────
    with tab_arq:
        st.markdown("**Arraste os personagens entre os arquétipos.** Clique em Salvar para aplicar.")
        st.write("")
        arq_input = [
            {"header": arq, "items": list(pers)}
            for arq, pers in st.session_state.arq_config.items()
        ]
        arq_resultado = sort_items(arq_input, multi_containers=True, key="sort_arq")
        st.write("")
        if st.button("💾 Salvar arquétipos"):
            novo_arq = {bloco["header"]: bloco["items"] for bloco in arq_resultado}
            st.session_state.arq_config = novo_arq
            st.success("✅ Arquétipos atualizados!")
            st.rerun()

        sem_arq = [p for p in TODOS_PERSONAGENS
                   if not any(p in v for v in st.session_state.arq_config.values())]
        if sem_arq:
            st.warning(f"⚠️ Sem arquétipo: **{', '.join(sem_arq)}** → aparecerão como 'Desconhecido'.")

    # ── Tier List (drag-and-drop) ─────────────────────────────────────────────
    with tab_tier:
        st.markdown("**Arraste os personagens entre os tiers.** Clique em Salvar para aplicar.")
        st.caption("Meta de referência: pós-patch abril 2026 (Tierlist feita pelo Winter)")
        st.write("")
        tier_input = [
            {"header": f"Tier {tier}", "items": list(pers)}
            for tier, pers in st.session_state.tier_config.items()
        ]
        tier_resultado = sort_items(tier_input, multi_containers=True, key="sort_tier")
        st.write("")
        if st.button("💾 Salvar tier list"):
            novo_tier = {
                bloco["header"].replace("Tier ", ""): bloco["items"]
                for bloco in tier_resultado
            }
            st.session_state.tier_config = novo_tier
            st.success("✅ Tier list atualizada!")
            st.rerun()

        sem_tier = [p for p in TODOS_PERSONAGENS
                    if not any(p in v for v in st.session_state.tier_config.values())]
        if sem_tier:
            st.warning(f"⚠️ Sem tier: **{', '.join(sem_tier)}** → aparecerão como '?'.")

    # ── Colunas ativas ────────────────────────────────────────────────────────
    with tab_cols:
        st.markdown("Ative ou desative as classificações que aparecem no dashboard e na tabela final.")
        st.write("")
        cc1,cc2,cc3,cc4 = st.columns(4)
        nova_cols = {}
        with cc1: nova_cols["Tier"]        = st.toggle("🏆 Tier List",    value=st.session_state.cols_ativas.get("Tier", True))
        with cc2: nova_cols["Arquétipo"]   = st.toggle("🥋 Arquétipos",   value=st.session_state.cols_ativas.get("Arquétipo", True))
        with cc3: nova_cols["Nível"]       = st.toggle("🎯 Nível",        value=st.session_state.cols_ativas.get("Nível", True))
        with cc4: nova_cols["Mirror Match"]= st.toggle("🪞 Mirror Match", value=st.session_state.cols_ativas.get("Mirror Match", True))
        st.write("")
        if st.button("💾 Salvar preferências de colunas"):
            st.session_state.cols_ativas = nova_cols
            st.success("✅ Preferências salvas!")
            st.rerun()

# Monta dicionários ativos
arq_map  = {p: arq  for arq,  lista in st.session_state.arq_config.items()  for p in lista}
tier_map = {p: tier for tier, lista in st.session_state.tier_config.items() for p in lista}
cols_on  = st.session_state.cols_ativas
VERDE    = st.session_state.wr_verde
AMARELO  = st.session_state.wr_amarelo

def semaforo(taxa):
    if taxa >= VERDE:   return "🟢"
    if taxa >= AMARELO: return "🟡"
    return "🔴"

def classificar_nivel(d):
    mi = st.session_state.lim_muito_inf; i = st.session_state.lim_inf
    s  = st.session_state.lim_sup;       ms= st.session_state.lim_muito_sup
    if d<=mi: return "Muito Inferior"
    elif d<=i: return "Inferior"
    elif d<s:  return "Similar"
    elif d<ms: return "Superior"
    else:      return "Muito Superior"

# ══════════════════════════════════════════════════════════════════════════════
# 📥  CARREGAR DADOS
# ══════════════════════════════════════════════════════════════════════════════
JOGADOR_ID = "4125616529"
ARQUIVO    = f"SF6_historico_LIMPO_{JOGADOR_ID}(Claud 3).csv"

@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv(ARQUIVO)
        df['Data_Datetime']         = pd.to_datetime(df['Data'])
        df['Oponente_MR']           = pd.to_numeric(df['Oponente_MR'],           errors='coerce').fillna(0).astype(int)
        df['Meu_MR']                = pd.to_numeric(df['Meu_MR'],                errors='coerce').fillna(0).astype(int)
        df['Diferenca_MR']          = pd.to_numeric(df['Diferenca_MR'],          errors='coerce').fillna(0).astype(int)
        df['Streak_Atual']          = pd.to_numeric(df['Streak_Atual'],          errors='coerce').fillna(0).astype(int)
        df['Numero_Partida_No_Dia'] = pd.to_numeric(df['Numero_Partida_No_Dia'], errors='coerce').fillna(1).astype(int)
        df['Mirror_Match']          = df['Mirror_Match'].astype(str).str.lower().isin(['true','1','sim'])
        return df
    except FileNotFoundError:
        return None

df_base = carregar_dados()
if df_base is None:
    st.error(f"Arquivo '{ARQUIVO}' não encontrado. Execute o script de limpeza primeiro.")
    st.stop()

# Recalcula colunas dinâmicas com configs atuais
df_base['Arquetipo_Oponente'] = df_base['Oponente_Personagem'].map(arq_map).fillna("Desconhecido")
df_base['Tier_Oponente']      = df_base['Oponente_Personagem'].map(tier_map).fillna("?")
df_base['Nivel_Oponente']     = df_base['Diferenca_MR'].apply(classificar_nivel)
df_base['Nivel_Oponente']     = pd.Categorical(df_base['Nivel_Oponente'], categories=ORDEM_NIVEL, ordered=True)
df_base['Tier_Oponente']      = pd.Categorical(df_base['Tier_Oponente'],  categories=ORDEM_TIER,  ordered=True)

nome_jogador = df_base['Meu_Nome'].iloc[0]
st.subheader(f"**{nome_jogador}** · ID: {JOGADOR_ID}")

# ══════════════════════════════════════════════════════════════════════════════
# 🎛️  SIDEBAR — FILTROS
# ══════════════════════════════════════════════════════════════════════════════
st.sidebar.header("🎛️ Filtros")

lista_meus_chars = sorted(df_base['Meu_Personagem'].dropna().unique())
filtro_meu_char  = st.sidebar.multiselect("Meu Personagem:",         options=lista_meus_chars, default=[], placeholder="Todos")
lista_op_chars   = sorted(df_base['Oponente_Personagem'].dropna().unique())
filtro_op_char   = st.sidebar.multiselect("Personagem do Oponente:", options=lista_op_chars,   default=[], placeholder="Todos")

if cols_on.get("Arquétipo"):
    lista_arq = sorted(df_base['Arquetipo_Oponente'].dropna().unique())
    filtro_arq = st.sidebar.multiselect("Arquétipo do Oponente:", options=lista_arq, default=[], placeholder="Todos")
else:
    filtro_arq = []

if cols_on.get("Tier"):
    filtro_tier = st.sidebar.multiselect("Tier do Oponente:", options=ORDEM_TIER, default=[], placeholder="Todos")
else:
    filtro_tier = []

lista_modos  = sorted(df_base['Tipo Partida (Jogo)'].dropna().unique())
filtro_modo  = st.sidebar.multiselect("Modo de Jogo:", options=lista_modos, default=[], placeholder="Todos")

if cols_on.get("Nível"):
    filtro_nivel = st.sidebar.multiselect("Nível do Oponente:", options=ORDEM_NIVEL, default=[], placeholder="Todos")
else:
    filtro_nivel = []

filtro_resultado = st.sidebar.multiselect("Resultado:",
    options=["Vitória 🏆","Derrota ❌","Empate ➖"], default=[], placeholder="Todos")

if cols_on.get("Mirror Match"):
    filtro_mirror = st.sidebar.selectbox("Mirror Match:",
        options=["Todos","Apenas Mirrors","Excluir Mirrors"], index=0)
else:
    filtro_mirror = "Todos"

filtro_mr = st.sidebar.number_input("MR do Oponente (Mínimo):", min_value=0, max_value=5000, value=0, step=50)

lista_oponentes = sorted(df_base['Oponente_Nome'].dropna().unique())
filtro_oponente = st.sidebar.selectbox("Oponente Específico:",
    options=[None]+list(lista_oponentes), index=0,
    format_func=lambda x: "— Todos —" if x is None else x)

min_date = df_base['Data_Datetime'].min().date()
max_date = df_base['Data_Datetime'].max().date()
filtro_data = st.sidebar.date_input("Intervalo de Data:", value=[], min_value=min_date, max_value=max_date)
st.sidebar.info("📅 1º clique = início · 2º clique = fim")

if st.sidebar.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

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
if filtro_mirror == "Apenas Mirrors":  df_f = df_f[df_f['Mirror_Match']==True]
if filtro_mirror == "Excluir Mirrors": df_f = df_f[df_f['Mirror_Match']==False]
if len(filtro_data)==2:
    df_f = df_f[(df_f['Data_Datetime'].dt.date>=filtro_data[0])&(df_f['Data_Datetime'].dt.date<=filtro_data[1])]
elif len(filtro_data)==1:
    df_f = df_f[df_f['Data_Datetime'].dt.date==filtro_data[0]]

total    = len(df_f)
vitorias = (df_f['Meu_Resultado']=="Vitória 🏆").sum()
derrotas = (df_f['Meu_Resultado']=="Derrota ❌").sum()
win_rate = vitorias/total*100 if total>0 else 0

def wr(sub):
    t=len(sub); return (sub['Meu_Resultado']=="Vitória 🏆").sum()/t*100 if t>0 else 0.0

def tabela_wr(df_grp, col_group, sort_by='WR_num', ascending=False):
    t = df_grp.groupby(col_group, observed=True).agg(
        Lutas=('Meu_Resultado','count'),
        Vitórias=('Meu_Resultado', lambda x:(x=="Vitória 🏆").sum()),
        Derrotas=('Meu_Resultado', lambda x:(x=="Derrota ❌").sum())
    ).reset_index()
    t['WR_num'] = t['Vitórias']/t['Lutas']*100
    t['']       = t['WR_num'].apply(semaforo)
    t['WR (%)'] = t['WR_num'].apply(lambda x:f"{x:.1f}%")
    t = t.sort_values(sort_by, ascending=ascending)
    return t  # mantém WR_num para ordenação correta no st.dataframe via column_config

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 1 — VISÃO GERAL
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🏆 Visão Geral")

# MR máximo histórico geral (todas as partidas ranqueadas, independente de personagem)
df_rank_global = df_base[df_base['Tipo Partida (Jogo)'] == 'Ranqueada']
mr_maximo_geral = int(df_rank_global['Meu_MR'].max()) if len(df_rank_global) > 0 else 0

# Jogadores únicos enfrentados
jogadores_unicos = df_f['Oponente_ID'].nunique() if 'Oponente_ID' in df_f.columns else df_f['Oponente_Nome'].nunique()

k1,k2,k3,k4,k5 = st.columns(5)
k1.metric("MR Máximo Atingido",    f"{mr_maximo_geral:,}".replace(",","."),
          help="Maior MR já registrado em qualquer partida ranqueada, independente do personagem.")
k2.metric("Total de Partidas",     f"{total:,}".replace(",","."))
k3.metric("Vitórias",              f"{vitorias:,}".replace(",","."))
k4.metric("Win Rate Geral",        f"{win_rate:.1f}%")
k5.metric("Jogadores Únicos Enfrentados", f"{jogadores_unicos:,}".replace(",","."))

# Tabela de MR por personagem (arquivo auxiliar gerado pela limpeza)
ARQUIVO_MR = f"SF6_MR_por_personagem_{JOGADOR_ID}.csv"
PERSONAGENS_MASTER = ["Elena", "Mai", "Cammy"]  # ← ajuste conforme necessário

try:
    df_mr_chars = pd.read_csv(ARQUIVO_MR)
    # Filtra apenas personagens Master
    df_mr_master = df_mr_chars[df_mr_chars['Meu_Personagem'].isin(PERSONAGENS_MASTER)].copy()
    if not df_mr_master.empty:
        st.write("")
        st.markdown("##### 🏅 MR por Personagem na Temporada Atual")
        cols_mr = st.columns(len(df_mr_master))
        for i, (_, row) in enumerate(df_mr_master.iterrows()):
            cols_mr[i].metric(
                label=f"{row['Meu_Personagem']}",
                value=f"{int(row['MR_Atual']):,}".replace(",","."),
                delta=f"Máx: {int(row['MR_Maximo']):,}".replace(",","."),
                delta_color="off",
                help=f"{int(row['Partidas'])} partidas ranqueadas registradas"
            )
except FileNotFoundError:
    st.caption("💡 Execute o script de limpeza para ver o MR por personagem.")

if total>0:
    cores_res={"Vitória 🏆":"#119c0c","Derrota ❌":"#b63a24","Empate ➖":"#2f45c4"}
    df_res  = df_f['Meu_Resultado'].value_counts().reset_index(); df_res.columns=['Resultado','Quantidade']
    df_mods = df_f['Tipo Partida (Jogo)'].value_counts().reset_index(); df_mods.columns=['Modo','Quantidade']
    col1,col2=st.columns(2)
    with col1:
        fig=px.pie(df_res,values='Quantidade',names='Resultado',color='Resultado',
                   color_discrete_map=cores_res,title="Distribuição de Resultados",
                   template="plotly_dark",height=300)
        fig.update_traces(textinfo='percent+value',textfont_color="white",
                          marker_line_color='white',marker_line_width=0.5,
                          hovertemplate="<b>%{label}</b><br>%{value} partidas<extra></extra>")
        fig.update_layout(margin=dict(l=10,r=10,t=40,b=10),
                          legend=dict(orientation="h",y=-0.15,x=0.5,xanchor="center"))
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        fig2=px.pie(df_mods,values='Quantidade',names='Modo',
                    title="Distribuição por Modo",template="plotly_dark",height=300)
        fig2.update_traces(textinfo='percent+label',textfont_color="white",
                           marker_line_color='white',marker_line_width=0.5,
                           hovertemplate="<b>%{label}</b><br>%{value} partidas<extra></extra>")
        fig2.update_layout(margin=dict(l=10,r=10,t=40,b=10),showlegend=False)
        st.plotly_chart(fig2,use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 3 — PERSONAGENS UTILIZADOS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🥋 Personagens Utilizados")

if total>0:
    df_ch=df_f['Meu_Personagem'].value_counts().reset_index(); df_ch.columns=['Personagem','Quantidade']
    c3,c4=st.columns(2)
    with c3:
        fig=px.bar(df_ch,x='Personagem',y='Quantidade',color='Personagem',
                   title="Partidas por Personagem",template="plotly_dark",height=340)
        fig.update_traces(texttemplate='%{y}',textposition="outside",textfont_color="white",
                          hovertemplate="<b>%{x}</b><br>%{y} partidas<extra></extra>")
        fig.update_layout(showlegend=False,yaxis=dict(showticklabels=False),margin=dict(l=10,r=10,t=40,b=10))
        st.plotly_chart(fig,use_container_width=True)
    with c4:
        fig=px.pie(df_ch,values='Quantidade',names='Personagem',
                   title="Proporção de Uso (%)",template="plotly_dark",height=340)
        fig.update_traces(textinfo='percent',textfont_color="white",
                          marker_line_color='white',marker_line_width=0.5)
        fig.update_layout(margin=dict(l=10,r=10,t=40,b=10),
                          legend=dict(orientation="h",y=-0.15,x=0.5,xanchor="center"))
        st.plotly_chart(fig,use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 4 — MATCHUPS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🥊 Matchups")

if total>0:
    # 4a — Personagens mais enfrentados
    df_op=df_f['Oponente_Personagem'].value_counts().reset_index(); df_op.columns=['Personagem','Quantidade']
    fig=px.bar(df_op,x='Personagem',y='Quantidade',color='Personagem',
               title="Personagens mais enfrentados",template="plotly_dark",height=380)
    fig.update_traces(texttemplate='%{y}',textposition="outside",textfont_color="white",
                      hovertemplate="<b>%{x}</b><br>%{y} partidas<extra></extra>")
    fig.update_layout(showlegend=False,yaxis=dict(showticklabels=False),margin=dict(l=10,r=10,t=40,b=10))
    st.plotly_chart(fig,use_container_width=True)

    # 4b — Win rate por personagem
    st.markdown("#### 📊 Win Rate por Personagem")
    df_mu = tabela_wr(df_f,'Oponente_Personagem', sort_by='WR_num', ascending=False)
    df_mu = df_mu.rename(columns={'Oponente_Personagem':'Personagem'})
    st.dataframe(
        df_mu[['','Personagem','Lutas','Vitórias','Derrotas','WR (%)','WR_num']],
        use_container_width=True, hide_index=True,
        column_config={"WR_num": None}
    )
    st.info(f"🟢 ≥{VERDE}% · 🟡 ≥{AMARELO}% · 🔴 <{AMARELO}%  |  Clique nos cabeçalhos para ordenar.")

    # 4b.5 — Experiência de matchup: jogadores únicos por personagem
    st.markdown("#### 👥 Diversidade de Oponentes por Personagem")
    st.caption("Quantos jogadores diferentes você enfrentou com cada personagem — ajuda a identificar matchups com pouca variedade de amostra.")

    # Usa Oponente_ID se existir, senão cai para Oponente_Nome como proxy
    col_id = 'Oponente_ID' if 'Oponente_ID' in df_f.columns else 'Oponente_Nome'
    if col_id == 'Oponente_Nome':
        st.caption("⚠️ Coluna Oponente_ID não encontrada — usando Oponente_Nome como substituto. Rode o script de limpeza para ter precisão total.")

    df_uniq = df_f.groupby('Oponente_Personagem').agg(
        Total_Partidas=('Meu_Resultado','count'),
        Jogadores_Unicos=(col_id,'nunique')
    ).reset_index().sort_values('Jogadores_Unicos', ascending=False)
    df_uniq['Partidas_por_Jogador'] = (df_uniq['Total_Partidas'] / df_uniq['Jogadores_Unicos']).round(1)

    total_ids = df_f[col_id].nunique()
    if total_ids <= 1:
        st.warning(f"⚠️ Apenas {total_ids} ID único encontrado — o gráfico mostrará a diversidade correta com os dados reais.")

    fig_uniq = px.bar(
        df_uniq, x='Oponente_Personagem', y='Jogadores_Unicos', color='Oponente_Personagem',
        title="Jogadores Únicos Enfrentados por Personagem",
        template="plotly_dark", height=380,
        custom_data=['Total_Partidas','Partidas_por_Jogador']
    )
    fig_uniq.update_traces(
        texttemplate='%{y}', textposition="outside", textfont_color="white",
        hovertemplate="<b>%{x}</b><br>Jogadores únicos: %{y}<br>Total de partidas: %{customdata[0]}<br>Média partidas/jogador: %{customdata[1]}<extra></extra>"
    )
    fig_uniq.update_layout(showlegend=False,
                           xaxis_title="Personagem do Oponente",
                           yaxis=dict(title="Jogadores Únicos", showticklabels=False),
                           margin=dict(l=10,r=10,t=40,b=10))
    st.plotly_chart(fig_uniq, use_container_width=True)

    df_uniq_view = df_uniq.rename(columns={
        'Oponente_Personagem':'Personagem',
        'Total_Partidas':'Partidas',
        'Jogadores_Unicos':'Jogadores Únicos',
        'Partidas_por_Jogador':'Média Partidas/Jogador'
    })
    st.dataframe(df_uniq_view, use_container_width=True, hide_index=True)
    st.caption("💡 Razão alta = você enfrenta sempre os mesmos jogadores nesse matchup (amostra menos representativa).")

    # 4c — Tier por personagem (se ativo)
    if cols_on.get("Tier"):
        st.markdown("#### 🏆 Tier do Oponente nos Matchups")
        df_mu_tier = tabela_wr(df_f,'Tier_Oponente', sort_by='Tier_Oponente', ascending=True)
        df_mu_tier = df_mu_tier.rename(columns={'Tier_Oponente':'Tier'})
        wr_nums = df_f.groupby('Tier_Oponente',observed=True).apply(
            lambda x: (x['Meu_Resultado']=="Vitória 🏆").sum()/len(x)*100 if len(x)>0 else 0
        ).reset_index(); wr_nums.columns=['Tier','WR']

        chars_por_tier = {
            tier: "<br>".join(sorted(chars))
            for tier, chars in st.session_state.tier_config.items()
            if chars
        }
        wr_nums['chars_hover'] = wr_nums['Tier'].astype(str).map(
            lambda t: chars_por_tier.get(t, "—")
        )

        fig_tier=go.Figure()
        fig_tier.add_trace(go.Bar(
            x=wr_nums['Tier'].astype(str), y=wr_nums['WR'],
            marker_color=[CORES_TIER.get(str(t),'#888') for t in wr_nums['Tier']],
            text=[f"{v:.1f}%" for v in wr_nums['WR']],textposition='outside',
            textfont_color='white',
            customdata=wr_nums[['chars_hover']].values,
            hovertemplate="<b>Tier %{x}</b><br>Win Rate: %{y:.1f}%<br><br>%{customdata[0]}<extra></extra>"
        ))
        fig_tier.update_layout(template="plotly_dark",height=320,xaxis_title="Tier",
                               yaxis=dict(range=[0,115],showticklabels=False),
                               margin=dict(l=10,r=10,t=20,b=10))
        c_tier1,c_tier2=st.columns(2)
        with c_tier1: st.plotly_chart(fig_tier,use_container_width=True)
        with c_tier2:
            st.write(""); st.write("")
            st.dataframe(
                df_mu_tier[['','Tier','Lutas','Vitórias','Derrotas','WR (%)','WR_num']],
                use_container_width=True, hide_index=True,
                column_config={"WR_num": None}
            )
    st.divider()

    # 4d — Mirror Match (se ativo)
    if cols_on.get("Mirror Match"):
        st.markdown("#### 🪞 Mirror Matches")
        df_mir = df_f[df_f['Mirror_Match']==True]
        n_mir  = len(df_mir)
        if n_mir==0:
            st.info("Nenhum mirror match encontrado com os filtros atuais.")
        else:
            wr_mir = wr(df_mir)
            mm1,mm2,mm3=st.columns(3)
            mm1.metric("Total de Mirrors",f"{n_mir}")
            mm2.metric("Win Rate em Mirrors",f"{wr_mir:.1f}%")
            mm3.metric("Win Rate Geral",f"{win_rate:.1f}%",
                       delta=f"{wr_mir-win_rate:+.1f}%",delta_color="normal")
            df_mc = tabela_wr(df_mir,'Meu_Personagem')
            st.dataframe(
                df_mc[['','Meu_Personagem','Lutas','Vitórias','WR (%)','WR_num']],
                use_container_width=True, hide_index=True,
                column_config={"WR_num": None}
            )

    # Personagens não enfrentados
    nao_enf=sorted(set(df_base['Oponente_Personagem'].dropna().unique())-set(df_f['Oponente_Personagem'].dropna().unique()))
    if nao_enf:
        st.info(f"💡 Não enfrentados com os filtros atuais: {', '.join(nao_enf)}.")

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 5 — ARQUÉTIPOS (se ativo)
# ══════════════════════════════════════════════════════════════════════════════
if cols_on.get("Arquétipo") and total>0:
    st.markdown("---")
    st.markdown("### 🎭 Desempenho por Arquétipo")
    df_arq = tabela_wr(df_f,'Arquetipo_Oponente').sort_values('Lutas',ascending=False)
    wr_arq_num = df_f.groupby('Arquetipo_Oponente').apply(
        lambda x: (x['Meu_Resultado']=="Vitória 🏆").sum()/len(x)*100 if len(x)>0 else 0
    ).reset_index(); wr_arq_num.columns=['Arquétipo','WR']

    ca1,ca2=st.columns(2)
    with ca1:
        # Monta lista de personagens por arquétipo para o hover
        chars_por_arq = {
            arq: "<br>".join(sorted(chars))
            for arq, chars in st.session_state.arq_config.items()
            if chars
        }
        wr_arq_num['chars_hover'] = wr_arq_num['Arquétipo'].map(
            lambda a: chars_por_arq.get(a, "—")
        )
        fig=go.Figure()
        for _, row in wr_arq_num.iterrows():
            fig.add_trace(go.Bar(
                x=[row['Arquétipo']], y=[row['WR']],
                name=row['Arquétipo'],
                text=[f"{row['WR']:.1f}%"], textposition='outside',
                textfont_color='white',
                customdata=[[row['chars_hover']]],
                hovertemplate=f"<b>{row['Arquétipo']}</b><br>Win Rate: {row['WR']:.1f}%<br><br>%{{customdata[0]}}<extra></extra>"
            ))
        fig.update_layout(
            title="Win Rate por Arquétipo", template="plotly_dark", height=340,
            showlegend=False, yaxis=dict(range=[0,115],showticklabels=False),
            margin=dict(l=10,r=10,t=40,b=10)
        )
        st.plotly_chart(fig,use_container_width=True)
    with ca2:
        st.write(""); st.write("")
        df_arq_view = df_arq.rename(columns={'Arquetipo_Oponente':'Arquétipo'})
        st.dataframe(
            df_arq_view[['','Arquétipo','Lutas','Vitórias','Derrotas','WR (%)','WR_num']],
            use_container_width=True, hide_index=True,
            column_config={"WR_num": None}
        )
    st.info("💡 Arquétipos configuráveis em **⚙️ Configurações → 🥋 Arquétipos**.")

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 6 — NÍVEL DO OPONENTE (se ativo)
# ══════════════════════════════════════════════════════════════════════════════
if cols_on.get("Nível") and total>0:
    st.markdown("---")
    st.markdown("### 🎯 Desempenho por Nível do Oponente")
    df_nv = tabela_wr(df_f,'Nivel_Oponente')
    wr_nv_num = df_f.groupby('Nivel_Oponente',observed=True).apply(
        lambda x:(x['Meu_Resultado']=="Vitória 🏆").sum()/len(x)*100 if len(x)>0 else 0
    ).reset_index(); wr_nv_num.columns=['Nível','WR']

    cn1,cn2=st.columns(2)
    with cn1:
        # Lista de oponentes por faixa para o hover (máx 10 + "e N outros")
        def oponentes_hover(nivel):
            nomes = sorted(df_f[df_f['Nivel_Oponente']==nivel]['Oponente_Nome'].dropna().unique())
            if len(nomes) <= 10:
                return "<br>".join(nomes)
            return "<br>".join(nomes[:10]) + f"<br>... e {len(nomes)-10} outros"

        wr_nv_num['op_hover'] = wr_nv_num['Nível'].astype(str).map(oponentes_hover)

        fig=go.Figure()
        for _, row in wr_nv_num.iterrows():
            fig.add_trace(go.Bar(
                x=[row['Nível']], y=[row['WR']],
                name=row['Nível'],
                text=[f"{row['WR']:.1f}%"], textposition='outside',
                textfont_color='white',
                customdata=[[row['op_hover']]],
                hovertemplate=f"<b>{row['Nível']}</b><br>Win Rate: {row['WR']:.1f}%<br><br>%{{customdata[0]}}<extra></extra>"
            ))
        fig.update_layout(
            title="Win Rate por Nível", template="plotly_dark", height=320,
            showlegend=False, yaxis=dict(range=[0,115],showticklabels=False),
            xaxis=dict(categoryorder='array', categoryarray=ORDEM_NIVEL),
            margin=dict(l=10,r=10,t=40,b=10)
        )
        st.plotly_chart(fig,use_container_width=True)
    with cn2:
        st.write(""); st.write("")
        df_nv_view = df_nv.rename(columns={'Nivel_Oponente':'Nível'})
        st.dataframe(
            df_nv_view[['','Nível','Lutas','Vitórias','WR (%)','WR_num']],
            use_container_width=True, hide_index=True,
            column_config={"WR_num": None}
        )
        st.caption("Faixas configuráveis em **⚙️ Configurações → 🎯 Faixas de Nível**.")

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 7 — DIA DA SEMANA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 📅 Desempenho por Dia da Semana")

if total>0:
    ordem_dias=['Segunda-feira','Terça-feira','Quarta-feira','Quinta-feira','Sexta-feira','Sábado','Domingo']
    df_dias=df_f['Dia da Semana'].value_counts().reindex(ordem_dias).fillna(0).reset_index()
    df_dias.columns=['Dia da Semana','Quantidade']; df_dias=df_dias[df_dias['Quantidade']>0]

    # Calcula WR por dia
    df_wr_dia = pd.DataFrame([{
        'Dia da Semana': dia,
        'WR': wr(df_f[df_f['Dia da Semana']==dia]),
        'Partidas': len(df_f[df_f['Dia da Semana']==dia])
    } for dia in df_dias['Dia da Semana']])

    # Tabela resumo antes dos gráficos
    df_tabela_dia = df_wr_dia.copy()
    df_tabela_dia[''] = df_tabela_dia['WR'].apply(semaforo)
    df_tabela_dia['Win Rate (%)'] = df_tabela_dia['WR'].apply(lambda x: f"{x:.1f}%")
    df_tabela_dia['WR_num'] = df_tabela_dia['WR']
    st.dataframe(
        df_tabela_dia[['','Dia da Semana','Partidas','Win Rate (%)','WR_num']].sort_values('WR_num', ascending=False),
        use_container_width=True, hide_index=True,
        column_config={"WR_num": None}
    )
 
    st.write("")
    cd1,cd2=st.columns(2)
    with cd1:
        fig=px.bar(df_dias,x='Dia da Semana',y='Quantidade',title="Partidas por Dia",
                   template="plotly_dark",height=300)
        fig.update_traces(texttemplate='%{y}',textposition="outside",textfont_color="white",
                          hovertemplate="<b>%{x}</b><br>%{y} partidas<extra></extra>")
        fig.update_layout(xaxis_title="",yaxis=dict(showticklabels=False,title=""),margin=dict(l=10,r=10,t=40,b=10))
        st.plotly_chart(fig,use_container_width=True)
    with cd2:
        fig2=px.bar(df_wr_dia,x='Dia da Semana',y='WR',title="Win Rate por Dia (%)",
                    template="plotly_dark",height=300)
        fig2.update_traces(texttemplate='%{y:.1f}%',textposition="outside",textfont_color="white",
                           hovertemplate="<b>%{x}</b><br>%{y:.1f}% win rate<br>%{customdata} partidas<extra></extra>",
                           customdata=df_wr_dia['Partidas'])
        fig2.update_layout(xaxis_title="",yaxis=dict(showticklabels=False,title="",range=[0,115]),
                           coloraxis_showscale=False,margin=dict(l=10,r=10,t=40,b=10))
        st.plotly_chart(fig2,use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 8 — HORÁRIO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🕒 Desempenho por Faixa de Horário")

if total>0:
    df_h=df_f.copy(); df_h['Hora_Fixa']=df_h['Hora Exata'].str[:2]
    df_hora=df_h.groupby('Hora_Fixa').agg(
        Lutas=('Meu_Resultado','count'),
        Vitórias=('Meu_Resultado',lambda x:(x=="Vitória 🏆").sum())
    ).reset_index()
    df_hora['WR_num']=df_hora['Vitórias']/df_hora['Lutas']*100
    df_hora['Faixa']=df_hora['Hora_Fixa']+":00 – "+df_hora['Hora_Fixa']+":59"
    df_hora['']=df_hora['WR_num'].apply(semaforo)
    df_hora['WR (%)']=df_hora['WR_num'].apply(lambda x:f"{x:.1f}%")
    df_hora=df_hora.sort_values('Faixa')

    ch1,ch2=st.columns(2)
    with ch1:
        fig=px.bar(df_hora,x='Faixa',y='WR_num',title="Win Rate por Horário (%)",
                   template="plotly_dark",height=320)
        fig.update_traces(texttemplate='%{y:.1f}%',textposition="outside",textfont_color="white",
                          hovertemplate="<b>%{x}</b><br>%{y:.1f}% win rate<br>%{customdata} partidas<extra></extra>",
                          customdata=df_hora['Lutas'])
        fig.update_layout(xaxis_title="",yaxis=dict(showticklabels=False,title="",range=[0,115]),
                          coloraxis_showscale=False,margin=dict(l=10,r=10,t=40,b=10))
        st.plotly_chart(fig,use_container_width=True)
    with ch2:
        st.write(""); st.write("")
        st.dataframe(df_hora[['','Faixa','Lutas','WR (%)']],use_container_width=True,hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 9 — SESSÃO E FADIGA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 😮‍💨 Sessão e Fadiga")
 
if total>0 and 'Numero_Partida_No_Dia' in df_f.columns:
    st.caption("Considera todas as partidas do dia, independente do modo. O aquecimento são as partidas 1 a 5 do dia.")
 
    def faixa_p(n):
        if n<=3:  return "1–3 (aquecimento)"
        if n<=10: return "4–10"
        if n<=15: return "11–15"
        if n<=20: return "16–20"
        if n<=25: return "21–25"
        if n<=30: return "26–30"
        if n<=35: return "31–35"
        if n<=40: return "36–40"
        return "40+"
 
    ordem_fx=["1–3 (aquecimento)","4–10","11–15","16–20","21–25","26–30","31–35","36–40","40+"]
 
    df_fad=df_f.copy(); df_fad['Faixa']=df_fad['Numero_Partida_No_Dia'].apply(faixa_p)
    df_fx=df_fad.groupby('Faixa').agg(
        Lutas=('Meu_Resultado','count'),Vitórias=('Meu_Resultado',lambda x:(x=="Vitória 🏆").sum())
    ).reset_index(); df_fx['WR']=df_fx['Vitórias']/df_fx['Lutas']*100
    df_fx['Faixa']=pd.Categorical(df_fx['Faixa'],categories=ordem_fx,ordered=True)
    df_fx=df_fx.sort_values('Faixa')
    df_fx=df_fx[df_fx['Lutas']>0]  # remove faixas sem dados
 
    cf1,cf2=st.columns(2)
    with cf1:
        fig=px.bar(df_fx,x='Faixa',y='WR',color='Faixa',title="Win Rate por Faixa da Sessão",
                   template="plotly_dark",height=340,
                   custom_data=['Lutas'])
        fig.update_traces(texttemplate='%{y:.1f}%',textposition="outside",textfont_color="white",
                          hovertemplate="<b>%{x}</b><br>%{y:.1f}% win rate<br>%{customdata[0]} partidas<extra></extra>")
        fig.update_layout(showlegend=False,yaxis=dict(range=[0,115],showticklabels=False),
                          margin=dict(l=10,r=10,t=40,b=10))
        st.plotly_chart(fig,use_container_width=True)
    with cf2:
        df_fv=df_fx.copy(); df_fv['']=df_fv['WR'].apply(semaforo); df_fv['WR (%)']=df_fv['WR'].apply(lambda x:f"{x:.1f}%")
        st.write(""); st.write("")
        st.dataframe(df_fv[['','Faixa','Lutas','WR (%)']],use_container_width=True,hide_index=True)
        st.caption("Faixas sem dados não aparecem no gráfico.")

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 10 — FATOR PSICOLÓGICO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🧠 Fator Psicológico")
 
if total>0:
    st.markdown("#### 🥇 Impacto do 1º Round")
    df_v1=df_f[df_f['Venceu_Primeiro_Round']=='Sim']; df_p1=df_f[df_f['Venceu_Primeiro_Round']=='Não']
    cr1,cr2=st.columns(2)
    with cr1:
        tx=wr(df_v1); st.metric("Win Rate SE vencer o 1º Round",f"{tx:.1f}%")
        st.caption(f"🎯 {(df_v1['Meu_Resultado']=='Vitória 🏆').sum()} vitórias de {len(df_v1)} partidas")
    with cr2:
        tx=wr(df_p1); st.metric("Win Rate SE perder o 1º Round",f"{tx:.1f}%")
        st.caption(f"🎯 {(df_p1['Meu_Resultado']=='Vitória 🏆').sum()} vitórias de {len(df_p1)} partidas")
 
 
    st.markdown("#### 🔄 Trajetória da Partida")
    cseq=df_f['Sequencia_Rounds'].value_counts().reset_index(); cseq.columns=['Seq','Qtd']
    trad={"V-V":"Vitória Limpa 2-0","V-D-V":"Vitória Suada 2-1","V-D-D":"Tomou Virada 1-2",
          "D-D":"Derrota Limpa 0-2","D-V-D":"Reagiu mas Perdeu","D-V-V":"Virada Épica 2-1"}
    cores_s={"V-V":"#19a50d","V-D-V":"#005fcc","D-V-V":"#9c00cc",
             "D-D":"#ac1f06","D-V-D":"#4d2d27","V-D-D":"#efec3b"}
    cseq['Desc']=cseq['Seq'].map(trad).fillna(cseq['Seq']); cseq=cseq[cseq['Seq']!="Sem dados"]
    if not cseq.empty:
        cs1,cs2=st.columns(2)
        with cs1:
            fig=px.bar(cseq,x='Qtd',y='Desc',color='Seq',color_discrete_map=cores_s,
                       orientation='h',template="plotly_dark",height=280)
            fig.update_traces(texttemplate='<b>%{x}</b>',textposition="outside",textfont_color="white")
            fig.update_layout(showlegend=False,yaxis={'categoryorder':'total ascending','title':''},
                              xaxis={'showticklabels':False,'title':''},margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig,use_container_width=True)
        with cs2:
            fig=px.pie(cseq,values='Qtd',names='Desc',color='Seq',color_discrete_map=cores_s,
                       template="plotly_dark",height=280)
            fig.update_traces(textinfo='percent',textfont_color="white",
                              marker_line_color='white',marker_line_width=0.5)
            fig.update_layout(showlegend=False,margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig,use_container_width=True)
 
    st.markdown("#### 💥 Como os Rounds Foram Decididos")
    def ex_g(t):
        if pd.isna(t) or t in ("Nenhum","Sem dados"): return []
        return [g.strip() for g in str(t).split(',')]
    dg=df_f[['Meus_Golpes_Finais','Golpes_Oponente']].copy()
    dg['M']=dg['Meus_Golpes_Finais'].apply(ex_g); dg['O']=dg['Golpes_Oponente'].apply(ex_g)
    dmg=dg.explode('M')['M'].value_counts().reset_index(); dmg.columns=['G','Q']; dmg=dmg.sort_values('Q',ascending=True)
    dog=dg.explode('O')['O'].value_counts().reset_index(); dog.columns=['G','Q']; dog=dog.sort_values('Q',ascending=True)
    cg1,cg2=st.columns(2)
    with cg1:
        if not dmg.empty:
            fig=px.bar(dmg,x='Q',y='G',orientation='h',title=f"Como VOCÊ finalizou rounds ({dmg['Q'].sum()})",
                       template="plotly_dark",color_discrete_sequence=["#00cc96"])
            fig.update_traces(texttemplate='<b>%{x}</b>',textposition="outside",textfont_color="white")
            fig.update_layout(xaxis={'showticklabels':False,'title':''},yaxis={'title':''},margin=dict(l=10,r=10,t=40,b=10))
            st.plotly_chart(fig,use_container_width=True)
    with cg2:
        if not dog.empty:
            fig=px.bar(dog,x='Q',y='G',orientation='h',title=f"Como o OPONENTE finalizou rounds ({dog['Q'].sum()})",
                       template="plotly_dark",color_discrete_sequence=["#ef553b"])
            fig.update_traces(texttemplate='<b>%{x}</b>',textposition="outside",textfont_color="white")
            fig.update_layout(xaxis={'showticklabels':False,'title':''},yaxis={'title':''},margin=dict(l=10,r=10,t=40,b=10))
            st.plotly_chart(fig,use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 11 — LADO DA TELA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 📺 Lado da Tela — P1 vs P2")

if total>0:
    df_l=df_f['Meu_Lado'].value_counts().reset_index(); df_l.columns=['Lado','Quantidade']
    cores_l={"Player 1":"#3498db","Player 2":"#e74c3c"}
    cl1,cl2=st.columns(2)
    with cl1:
        fig=px.pie(df_l,values='Quantidade',names='Lado',color='Lado',color_discrete_map=cores_l,
                   title="P1 / P2",template="plotly_dark",height=280)
        fig.update_traces(textinfo='percent+label',textfont_color="white",
                          marker_line_color='white',marker_line_width=0.5)
        fig.update_layout(showlegend=False,margin=dict(l=10,r=10,t=40,b=10))
        st.plotly_chart(fig,use_container_width=True)
    with cl2:
        st.write(""); st.write("")
        for lado in ["Player 1","Player 2"]:
            sub=df_f[df_f['Meu_Lado']==lado]; tx=wr(sub)
            lb="Esquerda (P1)" if lado=="Player 1" else "Direita (P2)"
            st.metric(f"Win Rate como {lb}",f"{tx:.1f}%")
            st.caption(f"🎯 {(sub['Meu_Resultado']=='Vitória 🏆').sum()} vitórias de {len(sub)} partidas")
            st.write("")
    df_p1d=df_f[df_f['Meu_Lado'].astype(str).str.contains('1')]
    if not df_p1d.empty:
        with st.expander(f"📋 Oponentes como P1 ({len(df_p1d)} partidas)"):
            gp1=df_p1d.groupby('Oponente_Nome').agg(
                Partidas=('Meu_Resultado','count'),
                Vitórias=('Meu_Resultado',lambda x:(x=="Vitória 🏆").sum()),
                Derrotas=('Meu_Resultado',lambda x:(x=="Derrota ❌").sum())
            ).reset_index().sort_values('Partidas',ascending=False)
            st.dataframe(gp1,use_container_width=True,hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 12 — OPONENTES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🎯 Oponentes — Jogadores Enfrentados")

if total>0:
    df_rv=df_f.groupby('Oponente_Nome').agg(
        Partidas=('Meu_Resultado','count'),
        Vitórias=('Meu_Resultado',lambda x:(x=="Vitória 🏆").sum()),
        Derrotas=('Meu_Resultado',lambda x:(x=="Derrota ❌").sum())
    ).reset_index(); df_rv['WR']=df_rv['Vitórias']/df_rv['Partidas']*100
    if not df_rv.empty:
        df3=df_rv[df_rv['Partidas']>=3]
        me=df_rv.loc[df_rv['Partidas'].idxmax()]
        mv=(df3 if not df3.empty else df_rv).loc[(df3 if not df3.empty else df_rv)['Vitórias'].idxmax()]
        md=(df3 if not df3.empty else df_rv).loc[(df3 if not df3.empty else df_rv)['Derrotas'].idxmax()]
        df4=df_rv[df_rv['Partidas']>=4].copy()
        if not df4.empty:
            df4['D50']=abs(df4['WR']-50); meq=df4.sort_values(['D50','Partidas'],ascending=[True,False]).iloc[0]
            neq=meq['Oponente_Nome']; deq=f"⚖️ {meq['WR']:.1f}% em {meq['Partidas']} partidas"
        else: neq="Sem dados"; deq="Mín. 4 partidas"
        co1,co2,co3,co4=st.columns(4)
        with co1: st.metric("Mais Enfrentado",me['Oponente_Nome']); st.caption(f"⚔️ {me['Partidas']} partidas")
        with co2: st.metric("Freguês (mín.3)",mv['Oponente_Nome']); st.caption(f"🎯 {mv['Vitórias']} vitórias em {mv['Partidas']} partidas")
        with co3: st.metric("Nêmesis (mín.3)",md['Oponente_Nome']); st.caption(f"💀 {md['Derrotas']} derrotas em {md['Partidas']} partidas")
        with co4: st.metric("Rivalidade Equilíbrada",neq); st.caption(deq)

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 13 — BUSCA DE CONFRONTOS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🔍 Histórico Detalhado contra um Oponente")

lista_busca=sorted(df_f['Oponente_Nome'].dropna().unique())
busca=st.selectbox("Selecione:",options=lista_busca,index=None,placeholder="Digite para filtrar...")
if busca:
    db=df_f[df_f['Oponente_Nome']==busca].sort_values(['Data','Hora Exata'],ascending=[False,False])
    vb=(db['Meu_Resultado']=="Vitória 🏆").sum(); dbb=(db['Meu_Resultado']=="Derrota ❌").sum()
    st.success(f"**{len(db)} confrontos** contra '{busca}' → 🏆 {vb} vitórias · ❌ {dbb} derrotas")
    for _,row in db.iterrows():
        ic="🟢" if "Vitória" in row['Meu_Resultado'] else ("🔴" if "Derrota" in row['Meu_Resultado'] else "⚪")
        with st.expander(f"{ic} {row['Data']} {row['Hora Exata']} | {row['Meu_Personagem']} vs {row['Oponente_Personagem']} | {row['Placar']}"):
            b1,b2,b3=st.columns([1,1.5,1.5])
            with b1:
                st.markdown(f"**Modo:** {row['Tipo Partida (Jogo)']}")
                st.markdown(f"**Resultado:** {row['Meu_Resultado']}")
                if cols_on.get("Nível"):    st.markdown(f"**Nível:** {row.get('Nivel_Oponente','—')}")
                if cols_on.get("Tier"):     st.markdown(f"**Tier:** {row.get('Tier_Oponente','—')}")
                if cols_on.get("Mirror Match"): st.markdown(f"**Mirror:** {'Sim 🪞' if row.get('Mirror_Match') else 'Não'}")
            with b2:
                st.markdown("🗡️ **Como você venceu:**"); st.info(row['Meus_Golpes_Finais'])
            with b3:
                st.markdown("🛡️ **Como o oponente venceu:**"); st.error(row['Golpes_Oponente'])

# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO 14 — HISTÓRICO COMPLETO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 📋 Histórico Detalhado")

colunas_base=['Data','Hora Exata','Tipo Partida (Jogo)','Turno','Meu_Resultado','Placar',
              'Meu_Personagem','Oponente_Nome','Oponente_Personagem','Oponente_MR',
              'Numero_Partida_No_Dia','Streak_Atual']
if cols_on.get("Nível"):       colunas_base.append('Nivel_Oponente')
if cols_on.get("Tier"):        colunas_base.append('Tier_Oponente')
if cols_on.get("Arquétipo"):   colunas_base.append('Arquetipo_Oponente')
if cols_on.get("Mirror Match"):colunas_base.append('Mirror_Match')

colunas_ok=[c for c in colunas_base if c in df_f.columns]
if total>0:
    st.dataframe(df_f[colunas_ok].sort_values(['Data','Hora Exata'],ascending=[False,False]),
                 use_container_width=True,hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# ══  SEÇÃO — AVALIAÇÃO DE MATCHUPS PELO WINTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🎮 Avaliação de Matchups — Winter")
st.caption("Arraste os personagens entre as categorias. O dashboard calcula o win rate de cada grupo automaticamente.")

# Pega personagens enfrentados nos dados filtrados
chars_enfrentados = sorted(df_f['Oponente_Personagem'].dropna().unique().tolist())

# Inicializa session state com todos os personagens em "Sem Opinião"
if 'matchup_gosta' not in st.session_state:
    st.session_state.matchup_gosta    = []
if 'matchup_reclama' not in st.session_state:
    st.session_state.matchup_reclama  = []
if 'matchup_neutro' not in st.session_state:
    st.session_state.matchup_neutro   = chars_enfrentados.copy()

# Sincroniza: se novos personagens apareceram nos dados, adiciona em Neutro
ja_classificados = set(st.session_state.matchup_gosta) | set(st.session_state.matchup_reclama) | set(st.session_state.matchup_neutro)
novos = [c for c in chars_enfrentados if c not in ja_classificados]
if novos:
    st.session_state.matchup_neutro.extend(novos)

# Remove personagens que sumiram dos dados filtrados
for lista in ['matchup_gosta','matchup_reclama','matchup_neutro']:
    st.session_state[lista] = [c for c in st.session_state[lista] if c in chars_enfrentados]

# Drag-and-drop
sort_input = [
    {"header": "😤 Reclama da Matchup",  "items": list(st.session_state.matchup_reclama)},
    {"header": "😊 Gosta da Matchup",    "items": list(st.session_state.matchup_gosta)},
    {"header": "😐 Sem Opinião",         "items": list(st.session_state.matchup_neutro)},
]
sort_resultado = sort_items(sort_input, multi_containers=True, key="sort_matchup_opinion")

if st.button("💾 Salvar classificação"):
    for bloco in sort_resultado:
        if bloco["header"] == "😤 Reclama da Matchup":
            st.session_state.matchup_reclama = bloco["items"]
        elif bloco["header"] == "😊 Gosta da Matchup":
            st.session_state.matchup_gosta   = bloco["items"]
        else:
            st.session_state.matchup_neutro  = bloco["items"]
    st.success("✅ Classificação salva!")
    st.rerun()

# Análise dos grupos
grupos = {
    "😤 Reclama": st.session_state.matchup_reclama,
    "😊 Gosta":   st.session_state.matchup_gosta,
    "😐 Neutro":  st.session_state.matchup_neutro,
}

grupos_com_dados = {k: v for k, v in grupos.items() if v}
if len(grupos_com_dados) >= 2:
    st.markdown("#### 📊 Win Rate por Classificação")

    rows = []
    for label, chars in grupos.items():
        if not chars: continue
        sub = df_f[df_f['Oponente_Personagem'].isin(chars)]
        if len(sub) == 0: continue
        rows.append({
            "Classificação": label,
            "Personagens":   ", ".join(sorted(chars)),
            "Partidas":      len(sub),
            "Vitórias":      (sub['Meu_Resultado']=="Vitória 🏆").sum(),
            "WR_num":        wr(sub),
        })

    if rows:
        df_op_class = pd.DataFrame(rows)
        df_op_class[''] = df_op_class['WR_num'].apply(semaforo)
        df_op_class['Win Rate (%)'] = df_op_class['WR_num'].apply(lambda x: f"{x:.1f}%")

        # Métricas de destaque
        mc1, mc2, mc3 = st.columns(3)
        cores_grupo = {"😤 Reclama": "#b63a24", "😊 Gosta": "#119c0c", "😐 Neutro": "#95A5A6"}
        for i, row in enumerate(rows):
            col = [mc1, mc2, mc3][i % 3]
            col.metric(row['Classificação'], f"{row['WR_num']:.1f}%",
                       f"{row['Partidas']} partidas")

        st.write("")

        # Gráfico comparativo
        fig_op = go.Figure()
        for row in rows:
            fig_op.add_trace(go.Bar(
                x=[row['Classificação']], y=[row['WR_num']],
                name=row['Classificação'],
                marker_color=cores_grupo.get(row['Classificação'], '#888'),
                text=[f"{row['WR_num']:.1f}%"], textposition='outside',
                textfont_color='white',
                customdata=[[row['Partidas'], row['Personagens']]],
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Win Rate: %{y:.1f}%<br>"
                    "%{customdata[0]} partidas<br><br>"
                    "%{customdata[1]}<extra></extra>"
                )
            ))
        fig_op.update_layout(
            template="plotly_dark", height=340, showlegend=False,
            yaxis=dict(range=[0,115], showticklabels=False),
            margin=dict(l=10,r=10,t=20,b=10)
        )
        st.plotly_chart(fig_op, use_container_width=True)

        # Tabela detalhada
        st.dataframe(
            df_op_class[['','Classificação','Partidas','Vitórias','Win Rate (%)','Personagens']],
            use_container_width=True, hide_index=True
        )
        st.caption("💡 O hover do gráfico lista todos os personagens de cada grupo.")
