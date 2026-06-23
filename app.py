"""
app.py — Plataforma de Governança de Dados
Banco Meridian | v4.0
Portal de Conhecimento, Dados e Confiança
"""
import streamlit as st
import pandas as pd
from databricks import sql
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import uuid

st.set_page_config(
    page_title="Plataforma de Governança — Banco Meridian",
    page_icon="🏦", layout="wide"
)

# ════════════════════════════════════════════════════════════════════
# DARK THEME
# ════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif !important; }
.stApp { background: #0D1117 !important; color: #E6EDF3 !important; }
.main .block-container {
    padding-top: 0rem !important; max-width: 100% !important;
    padding-left: 1.5rem !important; padding-right: 1.5rem !important;
}
h1,h2,h3 { color: #C9A227 !important; font-weight: 700 !important; }
.stButton > button {
    background: linear-gradient(135deg,#C9A227,#E6C84A) !important;
    color: #0D1117 !important; border: none !important;
    border-radius: 8px !important; font-weight: 700 !important;
}
.stTabs [data-baseweb="tab-list"] {
    background: #161B22; border-radius: 10px;
    padding: 4px; gap: 4px; border: 1px solid #30363D;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important; font-weight: 600 !important;
    color: #8B949E !important; padding: 8px 18px !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg,#C9A227,#E6C84A) !important;
    color: #0D1117 !important;
}
.stSelectbox > div > div {
    background: #161B22 !important;
    border-color: #30363D !important; color: #E6EDF3 !important;
}
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #161B22 !important; border-color: #30363D !important;
    color: #E6EDF3 !important; border-radius: 8px !important;
}
.streamlit-expanderHeader {
    background: #161B22 !important; border: 1px solid #30363D !important;
    color: #E6EDF3 !important; border-radius: 8px !important;
}
section[data-testid="stSidebar"] {
    background: #0D1117 !important;
    border-right: 1px solid #30363D !important;
    min-width: 220px !important;
}
section[data-testid="stSidebar"] * { color: #E6EDF3 !important; }
.stDataFrame { background: #161B22 !important; }
div[data-testid="stRadio"] > div { gap: 0px !important; }
div[data-testid="stRadio"] label {
    background: transparent !important; border: none !important;
    border-radius: 6px !important; padding: 5px 10px 5px 8px !important;
    color: #8B949E !important; font-size: 0.82rem !important;
    cursor: pointer !important; width: 100% !important;
    margin-bottom: 1px !important;
}
div[data-testid="stRadio"] label:hover {
    background: #161B22 !important; color: #E6EDF3 !important;
}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# CONEXÃO
# ════════════════════════════════════════════════════════════════════
@st.cache_resource
def get_conn():
    return sql.connect(
        server_hostname=st.secrets["DATABRICKS_HOST"],
        http_path=st.secrets["DATABRICKS_HTTP_PATH"],
        access_token=st.secrets["DATABRICKS_TOKEN"]
    )

@st.cache_data(ttl=300)
def qry(sql_str):
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute(sql_str)
        cols = [d[0] for d in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=cols), None
    except Exception as e:
        return pd.DataFrame(), str(e)

def exe(sql_str):
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute(sql_str)
        return True, None
    except Exception as e:
        return False, str(e)

def esc(v): return str(v).replace("'","''") if v else ""

# ════════════════════════════════════════════════════════════════════
# PERFIS
# ════════════════════════════════════════════════════════════════════
USUARIOS = {
    "consultante@meridian.com":   {"nome":"João Silva",      "perfil":"consultante"},
    "curador@meridian.com":       {"nome":"Maria Santos",    "perfil":"curador"},
    "governanca@meridian.com":    {"nome":"Tereza Cristina", "perfil":"curador"},
    "ana.lima@meridian.com":      {"nome":"Ana Lima",        "perfil":"aprovador"},
    "fernando.dias@meridian.com": {"nome":"Fernando Dias",   "perfil":"aprovador"},
}
PERFIL_COR   = {"consultante":"#58A6FF","curador":"#C9A227","aprovador":"#3FB950"}
PERFIL_LABEL = {"consultante":"👁️ Consultante","curador":"✏️ Curador","aprovador":"✅ Aprovador"}

# ════════════════════════════════════════════════════════════════════
# CACHE DE DADOS
# ════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def load_meta():
    df, _ = qry("SELECT * FROM meridian_governanca.tabelas_metadata")
    return df if df is not None else pd.DataFrame()

@st.cache_data(ttl=300)
def load_glossario():
    df, _ = qry("""SELECT * FROM meridian_governanca.business_glossary
                   ORDER BY CASE status WHEN 'homologado' THEN 1
                   WHEN 'em_revisao' THEN 2 ELSE 3 END, termo""")
    return df if df is not None else pd.DataFrame()

@st.cache_data(ttl=300)
def load_links():
    df, _ = qry("SELECT * FROM meridian_governanca.glossary_asset_link")
    return df if df is not None else pd.DataFrame()

@st.cache_data(ttl=300)
def load_rules():
    df, _ = qry("SELECT * FROM meridian_governanca.business_rules")
    return df if df is not None else pd.DataFrame()

# ════════════════════════════════════════════════════════════════════
# COMPONENTES
# ════════════════════════════════════════════════════════════════════
def page_header(icone, titulo, subtitulo=""):
    cor = PERFIL_COR.get(
        st.session_state.get("perfil_atual","consultante"),"#58A6FF")
    nome = st.session_state.get("nome_atual","")
    label = PERFIL_LABEL.get(
        st.session_state.get("perfil_atual","consultante"),"")
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#161B22,#1C2128);
                border:1px solid #30363D;border-radius:12px;
                padding:14px 20px;margin-bottom:16px;
                display:flex;align-items:center;justify-content:space-between;">
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="background:#C9A22722;border-radius:8px;padding:8px;
                        font-size:1.2rem;">{icone}</div>
            <div>
                <div style="color:#E6EDF3;font-size:1.05rem;font-weight:800;">
                    {titulo}</div>
                {f'<div style="color:#8B949E;font-size:0.75rem;">{subtitulo}</div>'
                 if subtitulo else ''}
            </div>
        </div>
        <div style="text-align:right;">
            <div style="color:{cor};font-size:0.72rem;font-weight:600;">{label}</div>
            <div style="color:#8B949E;font-size:0.68rem;">{nome}</div>
        </div>
    </div>""", unsafe_allow_html=True)

def kpi(valor, label, cor="#C9A227", icone="", tooltip=""):
    tip = f'title="{tooltip}"' if tooltip else ""
    return f"""<div {tip} style="background:#161B22;border:1px solid #30363D;
        border-radius:10px;padding:14px 16px;border-top:3px solid {cor};
        cursor:{'help' if tooltip else 'default'};">
        <div style="font-size:0.62rem;color:#8B949E;font-weight:700;
                    text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">
            {icone} {label}</div>
        <div style="font-size:1.7rem;font-weight:800;color:{cor};">{valor}</div>
    </div>"""

def section_divider(titulo):
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;margin:20px 0 12px;">
        <div style="height:1px;background:#30363D;flex:1;"></div>
        <span style="color:#8B949E;font-size:0.7rem;font-weight:700;
                     text-transform:uppercase;letter-spacing:1.5px;">{titulo}</span>
        <div style="height:1px;background:#30363D;flex:1;"></div>
    </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# SIDEBAR — LOGIN E NAVEGAÇÃO
# ════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding:14px 8px 8px;display:flex;align-items:center;gap:8px;">
        <div style="background:linear-gradient(135deg,#C9A227,#E6C84A);border-radius:8px;
                    width:32px;height:32px;display:flex;align-items:center;
                    justify-content:center;font-size:1rem;flex-shrink:0;">🏦</div>
        <div>
            <div style="font-size:0.7rem;font-weight:800;color:#E6EDF3;line-height:1.1;">
                PLATAFORMA DE DADOS</div>
            <div style="font-size:0.6rem;color:#8B949E;">GOVERNANÇA CORPORATIVA</div>
        </div>
    </div>
    <div style="height:1px;background:#30363D;margin:8px 0 10px;"></div>
    """, unsafe_allow_html=True)

    if "usuario" not in st.session_state:
        st.session_state["usuario"] = None

    if not st.session_state["usuario"]:
        email = st.selectbox("",list(USUARIOS.keys()),
            format_func=lambda x: f"{USUARIOS[x]['nome']} · {USUARIOS[x]['perfil']}",
            label_visibility="collapsed")
        if st.button("Entrar →", key="login", use_container_width=True):
            st.session_state["usuario"]      = email
            st.session_state["perfil_atual"] = USUARIOS[email]["perfil"]
            st.session_state["nome_atual"]   = USUARIOS[email]["nome"]
            st.rerun()
        st.stop()

    u      = USUARIOS[st.session_state["usuario"]]
    perfil = u["perfil"]
    cor    = PERFIL_COR[perfil]
    st.session_state["perfil_atual"] = perfil
    st.session_state["nome_atual"]   = u["nome"]
    is_curador   = perfil in ["curador","aprovador"]
    is_aprovador = perfil == "aprovador"

    st.markdown(f"""
    <div style="background:#161B22;border:1px solid #30363D;border-radius:8px;
                padding:8px 10px;margin-bottom:10px;">
        <div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;
                    letter-spacing:1px;">Usuário logado</div>
        <div style="font-weight:700;color:#E6EDF3;font-size:0.82rem;">{u['nome']}</div>
        <div style="color:{cor};font-size:0.72rem;font-weight:600;">
            {PERFIL_LABEL[perfil]}</div>
    </div>""", unsafe_allow_html=True)

    # ── INSTITUCIONAL ────────────────────────────────────────────────
    st.markdown('<div style="color:#8B949E;font-size:0.6rem;font-weight:700;'
                'text-transform:uppercase;letter-spacing:1.5px;'
                'padding:6px 10px 2px;">INSTITUCIONAL</div>',
                unsafe_allow_html=True)

    menu_inst = ["🏠 Início","📖 Glossário","📋 Catálogo","🏛️ Domínios","🛡️ Scorecard"]

    # ── OPERACIONAL (só curadores/aprovadores) ───────────────────────
    menu_op = []
    if is_curador:
        st.markdown('<div style="color:#8B949E;font-size:0.6rem;font-weight:700;'
                    'text-transform:uppercase;letter-spacing:1.5px;'
                    'padding:10px 10px 2px;">OPERACIONAL</div>',
                    unsafe_allow_html=True)
        menu_op = ["⚡ Meu Espaço","✏️ Curadoria","🕐 Auditoria"]

    todas = menu_inst + menu_op
    pagina = st.radio("", todas, key="nav", label_visibility="collapsed")

    st.markdown('<div style="height:1px;background:#30363D;margin:10px 0 8px;"></div>',
                unsafe_allow_html=True)
    if st.button("Sair", key="logout", use_container_width=True):
        st.session_state["usuario"] = None
        st.rerun()

usuario = st.session_state["usuario"]

# ════════════════════════════════════════════════════════════════════
# 🏠 INÍCIO — Portal de Conhecimento
# ════════════════════════════════════════════════════════════════════
if pagina == "🏠 Início":
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Hero
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#161B22 0%,#1C2128 100%);
                border:1px solid #30363D;border-radius:16px;
                padding:28px 32px;margin-bottom:20px;
                position:relative;overflow:hidden;">
        <div style="position:absolute;top:0;right:0;width:300px;height:100%;
                    background:linear-gradient(135deg,transparent,#C9A22708);
                    border-radius:16px;"></div>
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div style="color:#E6EDF3;font-size:1.5rem;font-weight:800;
                            line-height:1.2;margin-bottom:6px;">
                    Plataforma de Governança de Dados</div>
                <div style="color:#8B949E;font-size:0.85rem;max-width:520px;
                            line-height:1.5;">
                    Encontre definições, indicadores, responsáveis e ativos de dados
                    do Banco Meridian em um único lugar.</div>
                <div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;">
                    <span style="background:#3FB95022;color:#3FB950;border-radius:20px;
                                 padding:3px 12px;font-size:0.72rem;font-weight:600;
                                 border:1px solid #3FB95044;">✓ Dados Confiáveis</span>
                    <span style="background:#58A6FF22;color:#58A6FF;border-radius:20px;
                                 padding:3px 12px;font-size:0.72rem;font-weight:600;
                                 border:1px solid #58A6FF44;">✓ Ownership Definido</span>
                    <span style="background:#BC8CFF22;color:#BC8CFF;border-radius:20px;
                                 padding:3px 12px;font-size:0.72rem;font-weight:600;
                                 border:1px solid #BC8CFF44;">✓ IA Ready</span>
                </div>
            </div>
            <div style="text-align:right;flex-shrink:0;">
                <div style="color:#8B949E;font-size:0.68rem;">Última atualização</div>
                <div style="color:#E6EDF3;font-size:0.82rem;font-weight:600;">
                    {now_str}</div>
                <div style="background:#3FB95022;color:#3FB950;border-radius:20px;
                            padding:2px 10px;font-size:0.68rem;font-weight:600;
                            border:1px solid #3FB95044;margin-top:4px;
                            display:inline-block;">● AO VIVO</div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # KPIs com tooltips
    df_meta  = load_meta()
    df_gloss = load_glossario()
    df_links = load_links()
    df_rules = load_rules()

    total_ativos  = len(df_meta)  if not df_meta.empty  else 0
    total_dom     = df_meta["dominio"].nunique() if not df_meta.empty else 0
    total_termos  = len(df_gloss) if not df_gloss.empty else 0
    total_regras  = len(df_rules) if not df_rules.empty else 0
    ativos_com_link = df_links["table_name"].nunique() if not df_links.empty else 0
    cobertura = round(ativos_com_link/max(total_ativos,1)*100)

    k1,k2,k3,k4,k5 = st.columns(5)
    with k1: st.markdown(kpi(total_termos,"Termos de Negócio","#C9A227","📖",
        "Definições oficiais utilizadas pela organização"), unsafe_allow_html=True)
    with k2: st.markdown(kpi(total_ativos,"Ativos de Dados","#58A6FF","🗂️",
        "Tabelas e estruturas catalogadas"), unsafe_allow_html=True)
    with k3: st.markdown(kpi(total_dom,"Domínios de Negócio","#BC8CFF","🏛️",
        "Áreas responsáveis pelos dados"), unsafe_allow_html=True)
    with k4: st.markdown(kpi(total_regras,"Regras de Negócio","#3FB950","📏",
        "Critérios para criar, calcular ou validar informações"), unsafe_allow_html=True)
    with k5: st.markdown(kpi(f"{cobertura}%","Cobertura Semântica","#F85149" if cobertura<40 else "#C9A227" if cobertura<70 else "#3FB950","🔗",
        "Percentual de ativos conectados a conceitos de negócio"), unsafe_allow_html=True)

    section_divider("COMECE POR UMA PERGUNTA")

    # 6 perguntas clicáveis
    perguntas = [
        ("🤔","O que significa?",
         "Encontre a definição oficial de qualquer conceito ou indicador.",
         "#C9A227","📖 Glossário"),
        ("🧮","Como é calculado?",
         "Consulte as regras e critérios que definem cada métrica.",
         "#58A6FF","📖 Glossário"),
        ("🔍","Onde encontro?",
         "Descubra em qual tabela ou estrutura o dado está armazenado.",
         "#BC8CFF","📋 Catálogo"),
        ("👤","Quem responde?",
         "Identifique o Owner e Steward responsáveis pelo dado.",
         "#3FB950","🏛️ Domínios"),
        ("🔗","Onde é utilizado?",
         "Veja os relacionamentos entre conceitos, ativos e indicadores.",
         "#F85149","📖 Glossário"),
        ("🛡️","Posso confiar?",
         "Consulte o scorecard de confiabilidade do ativo.",
         "#FF7B72","🛡️ Scorecard"),
    ]

    cols_p = st.columns(3)
    for i, (ic, titulo_p, desc_p, cor_p, destino_p) in enumerate(perguntas):
        with cols_p[i % 3]:
            st.markdown(f"""
            <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;
                        padding:16px;margin-bottom:10px;cursor:pointer;
                        transition:border-color 0.2s;"
                 onmouseover="this.style.borderColor='{cor_p}'"
                 onmouseout="this.style.borderColor='#30363D'">
                <div style="font-size:1.4rem;margin-bottom:6px;">{ic}</div>
                <div style="color:{cor_p};font-weight:700;font-size:0.88rem;
                            margin-bottom:4px;">{titulo_p}</div>
                <div style="color:#8B949E;font-size:0.75rem;line-height:1.4;
                            margin-bottom:8px;">{desc_p}</div>
                <div style="color:#8B949E;font-size:0.7rem;">→ {destino_p}</div>
            </div>""", unsafe_allow_html=True)

    section_divider("IMPACTO DA GOVERNANÇA")

    im1,im2,im3,im4 = st.columns(4)
    impactos = [
        ("🎯","Uma única verdade","Definições unificadas eliminam ambiguidade nas decisões."),
        ("🔒","Confiança nos dados","Ownership definido e auditoria completa em cada ativo."),
        ("⚡","Decisões mais rápidas","Encontre qualquer informação em segundos, não em dias."),
        ("📋","Compliance embarcado","Rastreabilidade nativa para auditorias e regulatórios."),
    ]
    for col, (ic, tit, desc) in zip([im1,im2,im3,im4], impactos):
        with col:
            st.markdown(f"""
            <div style="background:#161B22;border:1px solid #30363D;border-radius:10px;
                        padding:14px;text-align:center;">
                <div style="font-size:1.4rem;margin-bottom:6px;">{ic}</div>
                <div style="color:#E6EDF3;font-weight:700;font-size:0.8rem;
                            margin-bottom:4px;">{tit}</div>
                <div style="color:#8B949E;font-size:0.72rem;line-height:1.4;">{desc}</div>
            </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# 📖 GLOSSÁRIO
# ════════════════════════════════════════════════════════════════════
elif pagina == "📖 Glossário":
    page_header("📖","Glossário Corporativo",
                "A linguagem comum da organização — definições, regras e responsáveis.")

    df_g     = load_glossario()
    df_rules = load_rules()
    df_links = load_links()

    if not df_g.empty:
        # Métricas
        m1,m2,m3,m4 = st.columns(4)
        with m1: st.markdown(kpi(len(df_g),"Total de Termos","#C9A227","📖"),
                             unsafe_allow_html=True)
        with m2: st.markdown(kpi(
            len(df_g[df_g["status"]=="homologado"]),"✅ Homologados","#3FB950"),
            unsafe_allow_html=True)
        with m3: st.markdown(kpi(
            len(df_g[df_g["status"]=="em_revisao"]),"🔵 Em Revisão","#58A6FF"),
            unsafe_allow_html=True)
        with m4: st.markdown(kpi(
            len(df_g[df_g["status"]=="rascunho"]),"📄 Rascunho","#8B949E"),
            unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Abas — Workflow só para curadores
        abas_base = ["📋 Termos de Negócio","📏 Regras de Negócio",
                     "🔗 Relacionamentos","🕐 Histórico"]
        if is_curador:
            abas_base.append("⚙️ Workflow")
        tabs_g = st.tabs(abas_base)

        # ── ABA 1: TERMOS ────────────────────────────────────────────
        with tabs_g[0]:
            col_lista, col_det = st.columns([1, 2])

            with col_lista:
                busca_g = st.text_input("",
                    placeholder="🔍 Buscar termo...", key="g_busca")
                g_dom = st.selectbox("Domínio",
                    ["Todos"]+sorted(df_g["dominio"].unique().tolist()),
                    key="g_dom")
                g_st = st.selectbox("Status",
                    ["Todos","homologado","em_revisao","rascunho"],
                    key="g_st")

                df_gf = df_g.copy()
                if busca_g:
                    df_gf = df_gf[
                        df_gf["termo"].str.contains(busca_g,case=False,na=False)|
                        df_gf["definicao"].str.contains(busca_g,case=False,na=False)]
                if g_dom != "Todos": df_gf = df_gf[df_gf["dominio"]==g_dom]
                if g_st  != "Todos": df_gf = df_gf[df_gf["status"]==g_st]

                if "gid_sel" not in st.session_state:
                    st.session_state["gid_sel"] = None

                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

                for _, row in df_gf.iterrows():
                    cor_st = {"homologado":"#3FB950","em_revisao":"#58A6FF",
                              "rascunho":"#8B949E"}.get(row["status"],"#8B949E")
                    is_sel = st.session_state["gid_sel"] == row["glossary_id"]
                    bg = f"background:#C9A22711;border-color:#C9A22744;" if is_sel else ""
                    st.markdown(f"""
                    <div style="background:#161B22;border:1px solid #30363D;
                                border-radius:8px;padding:8px 10px;margin-bottom:4px;
                                {bg}">
                        <div style="color:#E6EDF3;font-weight:600;font-size:0.82rem;">
                            {row['termo']}</div>
                        <div style="display:flex;justify-content:space-between;
                                    margin-top:2px;">
                            <span style="color:#8B949E;font-size:0.7rem;">
                                {row['dominio']}</span>
                            <span style="color:{cor_st};font-size:0.68rem;
                                         font-weight:600;">● {row['status']}</span>
                        </div>
                    </div>""", unsafe_allow_html=True)
                    if st.button(f"Ver detalhes",
                                 key=f"gsel_{row['glossary_id']}",
                                 use_container_width=True):
                        st.session_state["gid_sel"] = row["glossary_id"]
                        st.rerun()

                # Novo termo
                if is_curador:
                    st.markdown("<div style='height:8px'></div>",
                                unsafe_allow_html=True)
                    with st.expander("➕ Criar novo termo"):
                        nn  = st.text_input("Termo *", key="nn")
                        nd  = st.text_area("Definição *", key="nd", height=70)
                        ns  = st.text_input("Sinônimos", key="ns")
                        ndo = st.selectbox("Domínio",
                            ["Crédito","Pagamentos","Clientes",
                             "Compliance","Produtos"], key="ndo")
                        na  = st.text_input("Área de Negócio", key="na")
                        nc  = st.selectbox("Criticidade",
                            ["Crítico","Alto","Médio","Baixo"], key="nc")
                        if st.button("💾 Criar Termo", key="btn_criar"):
                            if nn and nd:
                                gid_new = str(uuid.uuid4())
                                ok, err = exe(
                                    f"INSERT INTO meridian_governanca.business_glossary "
                                    f"VALUES ('{gid_new}','{esc(nn)}','{esc(nd)}',"
                                    f"'{esc(ns)}','{esc(ndo)}','{esc(na)}',"
                                    f"'{esc(nc)}','{esc(usuario)}',"
                                    f"'{esc(usuario)}','rascunho',1,false,"
                                    f"'{esc(usuario)}',current_timestamp(),"
                                    f"'{esc(usuario)}',current_timestamp())"
                                )
                                if ok:
                                    st.success(f"✅ '{nn}' criado!")
                                    st.cache_data.clear(); st.rerun()
                                else: st.error(f"Erro: {err}")
                            else: st.warning("Preencha Termo e Definição.")

            with col_det:
                gid = st.session_state.get("gid_sel")
                if gid:
                    row_d = df_g[df_g["glossary_id"]==gid]
                    if not row_d.empty:
                        row = row_d.iloc[0]
                        cor_st = {"homologado":"#3FB950","em_revisao":"#58A6FF",
                                  "rascunho":"#8B949E"}.get(row["status"],"#8B949E")
                        cor_crit = {"Crítico":"#F85149","Alto":"#FF7B72",
                                    "Médio":"#C9A227","Baixo":"#3FB950"}.get(
                                    row["criticidade"],"#8B949E")

                        st.markdown(f"""
                        <div style="background:#161B22;border:1px solid #30363D;
                                    border-radius:12px;padding:20px;">
                            <div style="display:flex;justify-content:space-between;
                                        align-items:flex-start;margin-bottom:12px;">
                                <div style="color:#E6EDF3;font-size:1.2rem;
                                            font-weight:800;">{row['termo']}</div>
                                <span style="background:{cor_st}22;color:{cor_st};
                                             border-radius:20px;padding:3px 12px;
                                             font-size:0.75rem;font-weight:600;
                                             border:1px solid {cor_st}44;">
                                    {'✅ Homologado' if row['status']=='homologado'
                                     else '🔵 Em Revisão' if row['status']=='em_revisao'
                                     else '📄 Rascunho'}</span>
                            </div>
                            <div style="color:#E6EDF3;font-size:0.85rem;line-height:1.6;
                                        margin-bottom:12px;">{row['definicao']}</div>
                            {f'<div style="color:#8B949E;font-size:0.75rem;margin-bottom:10px;">Também conhecido como: <span style="color:#C9A227;">{row["sinonimos"]}</span></div>' if row.get("sinonimos") else ''}
                            <div style="display:grid;grid-template-columns:1fr 1fr;
                                        gap:8px;margin-bottom:12px;">
                                <div style="background:#0D1117;border-radius:8px;padding:9px;">
                                    <div style="font-size:0.6rem;color:#8B949E;
                                                text-transform:uppercase;letter-spacing:1px;">
                                        DOMÍNIO</div>
                                    <div style="color:#E6EDF3;font-weight:600;
                                                font-size:0.82rem;">{row['dominio']}</div>
                                </div>
                                <div style="background:#0D1117;border-radius:8px;padding:9px;">
                                    <div style="font-size:0.6rem;color:#8B949E;
                                                text-transform:uppercase;letter-spacing:1px;">
                                        CRITICIDADE</div>
                                    <div style="color:{cor_crit};font-weight:600;
                                                font-size:0.82rem;">{row['criticidade']}</div>
                                </div>
                                <div style="background:#0D1117;border-radius:8px;padding:9px;">
                                    <div style="font-size:0.6rem;color:#8B949E;
                                                text-transform:uppercase;letter-spacing:1px;">
                                        DATA OWNER</div>
                                    <div style="color:#E6EDF3;font-size:0.78rem;">
                                        {row['owner_email']}</div>
                                </div>
                                <div style="background:#0D1117;border-radius:8px;padding:9px;">
                                    <div style="font-size:0.6rem;color:#8B949E;
                                                text-transform:uppercase;letter-spacing:1px;">
                                        DATA STEWARD</div>
                                    <div style="color:#E6EDF3;font-size:0.78rem;">
                                        {row['steward_email']}</div>
                                </div>
                            </div>
                        </div>""", unsafe_allow_html=True)

                        # Impacto do termo
                        links_t = df_links[df_links["glossary_id"]==gid] \
                                  if not df_links.empty else pd.DataFrame()
                        rules_t = df_rules[df_rules["glossary_id"]==gid] \
                                  if not df_rules.empty else pd.DataFrame()
                        n_tab = links_t["table_name"].nunique() if not links_t.empty else 0
                        n_reg = len(rules_t)

                        st.markdown(f"""
                        <div style="background:#0D1117;border:1px solid #30363D;
                                    border-radius:10px;padding:12px 16px;margin-top:10px;">
                            <div style="color:#8B949E;font-size:0.65rem;font-weight:700;
                                        text-transform:uppercase;letter-spacing:1px;
                                        margin-bottom:8px;">IMPACTO DO TERMO</div>
                            <div style="display:flex;gap:16px;flex-wrap:wrap;">
                                <div>
                                    <span style="color:#58A6FF;font-size:1.2rem;
                                                 font-weight:800;">{n_tab}</span>
                                    <span style="color:#8B949E;font-size:0.72rem;
                                                 margin-left:4px;">tabelas</span>
                                </div>
                                <div>
                                    <span style="color:#BC8CFF;font-size:1.2rem;
                                                 font-weight:800;">{n_reg}</span>
                                    <span style="color:#8B949E;font-size:0.72rem;
                                                 margin-left:4px;">regras</span>
                                </div>
                                <div>
                                    <span style="color:#C9A227;font-size:1.2rem;
                                                 font-weight:800;">1</span>
                                    <span style="color:#8B949E;font-size:0.72rem;
                                                 margin-left:4px;">domínio</span>
                                </div>
                            </div>
                        </div>""", unsafe_allow_html=True)

                        # Regras
                        if not rules_t.empty:
                            st.markdown('<div style="color:#E6EDF3;font-weight:700;'
                                        'font-size:0.82rem;margin:12px 0 6px;">'
                                        '📏 Regras de Negócio</div>',
                                        unsafe_allow_html=True)
                            for _, r in rules_t.iterrows():
                                st.markdown(f"""
                                <div style="background:#161B22;border:1px solid #30363D;
                                            border-radius:6px;padding:8px 12px;
                                            margin-bottom:5px;">
                                    <div style="display:flex;justify-content:space-between;">
                                        <span style="color:#E6EDF3;font-size:0.8rem;
                                                     font-weight:600;">{r['nome_regra']}</span>
                                        <span style="background:#BC8CFF22;color:#BC8CFF;
                                                     border-radius:4px;padding:1px 6px;
                                                     font-size:0.65rem;">{r['categoria']}</span>
                                    </div>
                                    <div style="color:#8B949E;font-size:0.73rem;
                                                margin-top:2px;">{r['descricao_regra']}</div>
                                </div>""", unsafe_allow_html=True)

                        # Ações workflow
                        if is_curador and row["status"]=="rascunho":
                            if st.button("📤 Submeter para Revisão",
                                         key=f"gsub_{gid}",
                                         use_container_width=True):
                                ok,_ = exe(
                                    f"UPDATE meridian_governanca.business_glossary "
                                    f"SET status='em_revisao',"
                                    f"atualizado_por='{esc(usuario)}',"
                                    f"atualizado_em=current_timestamp() "
                                    f"WHERE glossary_id='{gid}'"
                                )
                                if ok:
                                    st.success("✅ Submetido!")
                                    st.cache_data.clear(); st.rerun()

                        if is_aprovador and row["status"]=="em_revisao":
                            ga,gr = st.columns(2)
                            with ga:
                                if st.button("✅ Aprovar",key=f"gap_{gid}",
                                             use_container_width=True):
                                    ok,_ = exe(
                                        f"UPDATE meridian_governanca.business_glossary "
                                        f"SET status='homologado',"
                                        f"atualizado_por='{esc(usuario)}',"
                                        f"atualizado_em=current_timestamp() "
                                        f"WHERE glossary_id='{gid}'"
                                    )
                                    if ok:
                                        st.success("✅ Homologado!")
                                        st.cache_data.clear(); st.rerun()
                            with gr:
                                if st.button("❌ Rejeitar",key=f"grej_{gid}",
                                             use_container_width=True):
                                    ok,_ = exe(
                                        f"UPDATE meridian_governanca.business_glossary "
                                        f"SET status='rascunho',"
                                        f"atualizado_por='{esc(usuario)}',"
                                        f"atualizado_em=current_timestamp() "
                                        f"WHERE glossary_id='{gid}'"
                                    )
                                    if ok:
                                        st.warning("↩️ Devolvido.")
                                        st.cache_data.clear(); st.rerun()
                else:
                    st.markdown("""
                    <div style="background:#161B22;border:1px solid #30363D;
                                border-radius:12px;padding:40px;text-align:center;">
                        <div style="font-size:2rem;margin-bottom:10px;">📖</div>
                        <div style="color:#E6EDF3;font-weight:700;margin-bottom:6px;">
                            Selecione um termo</div>
                        <div style="color:#8B949E;font-size:0.82rem;">
                            Clique em "Ver detalhes" para visualizar a definição,
                            regras e ativos vinculados.</div>
                    </div>""", unsafe_allow_html=True)

        # ── ABA 2: REGRAS ────────────────────────────────────────────
        with tabs_g[1]:
            if df_rules.empty:
                st.info("Nenhuma regra cadastrada.")
            else:
                df_rg_view, _ = qry("""
                    SELECT g.termo, r.nome_regra, r.descricao_regra, r.categoria
                    FROM meridian_governanca.business_rules r
                    JOIN meridian_governanca.business_glossary g
                    ON r.glossary_id = g.glossary_id
                    ORDER BY g.termo, r.categoria
                """)
                if not df_rg_view.empty:
                    for _, r in df_rg_view.iterrows():
                        st.markdown(f"""
                        <div style="background:#161B22;border:1px solid #30363D;
                                    border-radius:8px;padding:10px 14px;margin-bottom:6px;">
                            <div style="display:flex;justify-content:space-between;
                                        align-items:center;margin-bottom:4px;">
                                <span style="color:#C9A227;font-size:0.78rem;
                                             font-weight:700;">{r['termo']}</span>
                                <span style="background:#BC8CFF22;color:#BC8CFF;
                                             border-radius:4px;padding:1px 7px;
                                             font-size:0.65rem;">{r['categoria']}</span>
                            </div>
                            <div style="color:#E6EDF3;font-size:0.82rem;
                                        font-weight:600;">{r['nome_regra']}</div>
                            <div style="color:#8B949E;font-size:0.75rem;
                                        margin-top:2px;">{r['descricao_regra']}</div>
                        </div>""", unsafe_allow_html=True)

        # ── ABA 3: RELACIONAMENTOS (grafo interativo) ─────────────────
        with tabs_g[2]:
            if df_links.empty or df_g.empty:
                st.info("Nenhum relacionamento cadastrado.")
            else:
                st.markdown("""
                <div style="background:#161B22;border:1px solid #30363D;
                            border-radius:10px;padding:12px 16px;margin-bottom:14px;">
                    <div style="color:#E6EDF3;font-size:0.82rem;line-height:1.5;">
                        Visualização da linhagem de negócio: como conceitos se conectam
                        a ativos técnicos. Cada nó representa um elemento;
                        cada aresta representa uma dependência.</div>
                </div>""", unsafe_allow_html=True)

                # Constrói o grafo
                termos_dict = dict(zip(df_g["glossary_id"], df_g["termo"]))

                nodes_x, nodes_y, nodes_text, nodes_color, nodes_size = [], [], [], [], []
                edge_x, edge_y = [], []

                # Posiciona termos à esquerda e tabelas à direita
                termos_uniq = df_links["glossary_id"].unique().tolist()
                tabelas_uniq = df_links["table_name"].unique().tolist()

                # Coordenadas
                t_pos = {gid: (0, i * 1.5) for i, gid in enumerate(termos_uniq)}
                a_pos = {tab: (3, i * 1.5 - (len(tabelas_uniq)-len(termos_uniq))*0.75)
                         for i, tab in enumerate(tabelas_uniq)}

                # Nós — termos
                for gid, (x, y) in t_pos.items():
                    nodes_x.append(x); nodes_y.append(y)
                    nodes_text.append(termos_dict.get(gid, gid[:8]))
                    nodes_color.append("#C9A227"); nodes_size.append(20)

                # Nós — tabelas
                for tab, (x, y) in a_pos.items():
                    nodes_x.append(x); nodes_y.append(y)
                    nodes_text.append(tab)
                    nodes_color.append("#58A6FF"); nodes_size.append(16)

                # Arestas
                for _, l in df_links.iterrows():
                    if l["glossary_id"] in t_pos and l["table_name"] in a_pos:
                        x0,y0 = t_pos[l["glossary_id"]]
                        x1,y1 = a_pos[l["table_name"]]
                        edge_x += [x0,x1,None]; edge_y += [y0,y1,None]

                fig_g = go.Figure()
                fig_g.add_trace(go.Scatter(
                    x=edge_x, y=edge_y, mode="lines",
                    line=dict(color="#30363D", width=1.5),
                    hoverinfo="none"
                ))
                fig_g.add_trace(go.Scatter(
                    x=nodes_x, y=nodes_y, mode="markers+text",
                    marker=dict(color=nodes_color, size=nodes_size,
                                line=dict(color="#0D1117",width=2)),
                    text=nodes_text, textposition="middle right",
                    textfont=dict(color="#E6EDF3", size=11),
                    hoverinfo="text"
                ))
                fig_g.update_layout(
                    paper_bgcolor="#161B22", plot_bgcolor="#161B22",
                    showlegend=False, height=420,
                    margin=dict(t=10,b=10,l=10,r=10),
                    xaxis=dict(showgrid=False,zeroline=False,showticklabels=False),
                    yaxis=dict(showgrid=False,zeroline=False,showticklabels=False),
                )
                st.plotly_chart(fig_g, use_container_width=True)

                # Legenda
                st.markdown("""
                <div style="display:flex;gap:16px;margin-top:4px;">
                    <div style="display:flex;align-items:center;gap:6px;">
                        <div style="width:12px;height:12px;border-radius:50%;
                                    background:#C9A227;"></div>
                        <span style="color:#8B949E;font-size:0.72rem;">Termos de Negócio</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:6px;">
                        <div style="width:12px;height:12px;border-radius:50%;
                                    background:#58A6FF;"></div>
                        <span style="color:#8B949E;font-size:0.72rem;">Ativos Técnicos</span>
                    </div>
                </div>""", unsafe_allow_html=True)

        # ── ABA 4: HISTÓRICO ─────────────────────────────────────────
        with tabs_g[3]:
            df_wf, _ = qry("""
                SELECT g.termo, w.acao, w.status_anterior,
                       w.status_novo, w.aprovador, w.comentario, w.criado_em
                FROM meridian_governanca.glossary_approval_workflow w
                JOIN meridian_governanca.business_glossary g
                ON w.glossary_id = g.glossary_id
                ORDER BY w.criado_em DESC LIMIT 50
            """)
            if not df_wf.empty:
                for _, r in df_wf.iterrows():
                    ts = str(r["criado_em"])[:16] if r["criado_em"] else "—"
                    st.markdown(f"""
                    <div style="background:#161B22;border:1px solid #30363D;
                                border-radius:6px;padding:8px 12px;margin-bottom:5px;
                                display:flex;justify-content:space-between;
                                align-items:center;">
                        <div>
                            <span style="color:#C9A227;font-size:0.78rem;
                                         font-weight:700;">{r['termo']}</span>
                            <span style="color:#8B949E;font-size:0.72rem;
                                         margin-left:8px;">{r['acao']}</span>
                            {f'<div style="color:#8B949E;font-size:0.7rem;margin-top:2px;">{r["comentario"]}</div>' if r.get("comentario") else ''}
                        </div>
                        <span style="color:#8B949E;font-size:0.7rem;">{ts}</span>
                    </div>""", unsafe_allow_html=True)
            else:
                st.info("Nenhum histórico disponível.")

        # ── ABA 5: WORKFLOW (só curadores) ────────────────────────────
        if is_curador and len(tabs_g) > 4:
            with tabs_g[4]:
                st.markdown("""
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;
                            gap:12px;">""", unsafe_allow_html=True)

                colunas_wf = [
                    ("📄 Rascunho","rascunho","#8B949E"),
                    ("🔵 Em Revisão","em_revisao","#58A6FF"),
                    ("✅ Homologado","homologado","#3FB950"),
                ]
                wf_cols = st.columns(3)
                for col, (titulo_wf, status_wf, cor_wf) in \
                        zip(wf_cols, colunas_wf):
                    df_wf_col = df_g[df_g["status"]==status_wf]
                    with col:
                        st.markdown(f"""
                        <div style="background:#161B22;border:1px solid {cor_wf}44;
                                    border-radius:10px;padding:12px;">
                            <div style="color:{cor_wf};font-weight:700;
                                        font-size:0.82rem;margin-bottom:8px;">
                                {titulo_wf} ({len(df_wf_col)})</div>""",
                                    unsafe_allow_html=True)
                        for _, r in df_wf_col.iterrows():
                            st.markdown(f"""
                            <div style="background:#0D1117;border:1px solid #30363D;
                                        border-radius:6px;padding:7px 9px;
                                        margin-bottom:5px;">
                                <div style="color:#E6EDF3;font-size:0.78rem;
                                            font-weight:600;">{r['termo']}</div>
                                <div style="color:#8B949E;font-size:0.68rem;">
                                    {r['dominio']}</div>
                            </div>""", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# 📋 CATÁLOGO
# ════════════════════════════════════════════════════════════════════
elif pagina == "📋 Catálogo":
    page_header("📋","Catálogo de Dados",
                "Descubra, compreenda e confie nos dados antes de utilizá-los.")

    df_cat = load_meta()

    if not df_cat.empty:
        total = len(df_cat)
        schemas = df_cat["schema_name"].value_counts()
        ouro   = schemas.get("ouro",0)
        prata  = schemas.get("prata",0)
        bronze = schemas.get("bronze",0)

        k1,k2,k3 = st.columns(3)
        with k1: st.markdown(kpi(total,"Tabelas no Catálogo","#C9A227"),
                             unsafe_allow_html=True)
        with k2: st.markdown(kpi(f"{ouro} · {prata} · {bronze}",
                                 "Ouro · Prata · Bronze","#58A6FF"),
                             unsafe_allow_html=True)
        with k3: st.markdown(kpi(df_cat["dominio"].nunique(),"Domínios","#BC8CFF"),
                             unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        # Busca
        busca_c = st.text_input("",
            placeholder="🔍 O que você procura? Pesquise por conceito, responsável, domínio ou ativo...",
            key="cat_busca")

        # Filtros
        f1,f2,f3,f4,f5 = st.columns(5)
        with f1:
            doms = ["Todos"]+sorted([d for d in df_cat["dominio"].unique() if d])
            f_dom = st.selectbox("DOMÍNIO", doms, key="cf_dom")
        with f2:
            cams = ["Todas"]+sorted(df_cat["schema_name"].unique().tolist())
            f_cam = st.selectbox("CAMADA", cams, key="cf_cam")
        with f3:
            owns = ["Todos"]+sorted([o for o in df_cat["data_owner"].unique() if o])
            f_own = st.selectbox("OWNER", owns, key="cf_own")
        with f4:
            stws = ["Todos"]+sorted([s for s in df_cat["data_steward"].unique() if s])
            f_stw = st.selectbox("STEWARD", stws, key="cf_stw")
        with f5:
            f_doc = st.selectbox("DOCUMENTAÇÃO",
                ["Todas","Documentadas","Sem documentação"], key="cf_doc")

        df_f = df_cat.copy()
        if busca_c:
            mask = (
                df_f["table_name"].str.contains(busca_c,case=False,na=False)|
                df_f["descricao"].str.contains(busca_c,case=False,na=False)|
                df_f["dominio"].str.contains(busca_c,case=False,na=False)|
                df_f["data_owner"].str.contains(busca_c,case=False,na=False)
            )
            df_f = df_f[mask]
        if f_dom != "Todos": df_f = df_f[df_f["dominio"]==f_dom]
        if f_cam != "Todas": df_f = df_f[df_f["schema_name"]==f_cam]
        if f_own != "Todos": df_f = df_f[df_f["data_owner"]==f_own]
        if f_stw != "Todos": df_f = df_f[df_f["data_steward"]==f_stw]
        if f_doc == "Documentadas":
            df_f = df_f[df_f["descricao"].apply(bool)]
        if f_doc == "Sem documentação":
            df_f = df_f[~df_f["descricao"].apply(bool)]

        st.markdown(f'<div style="color:#8B949E;font-size:0.75rem;margin:8px 0;">'
                    f'{len(df_f)} ativo(s) encontrado(s)</div>',
                    unsafe_allow_html=True)

        # Cards em grid 3 colunas
        if "cat_sel" not in st.session_state:
            st.session_state["cat_sel"] = None

        rows = [df_f.iloc[i:i+3].reset_index(drop=True)
                for i in range(0, len(df_f), 3)]

        for row_df in rows:
            cols_c = st.columns(3)
            for i, (_, item) in enumerate(row_df.iterrows()):
                cor_c = ("#3FB950" if item["score_completude"]==100 else
                         "#C9A227" if item["score_completude"]>=60 else "#F85149")
                desc  = (item["descricao"][:75]+"..."
                         if item["descricao"] and len(item["descricao"])>75
                         else item["descricao"] or "Sem descrição")
                is_sel = (st.session_state["cat_sel"] ==
                          f"{item['schema_name']}.{item['table_name']}")
                brd = f"border-color:{cor_c};" if is_sel else ""
                with cols_c[i]:
                    st.markdown(f"""
                    <div style="background:#161B22;border:1px solid #30363D;
                                border-radius:10px;padding:14px;margin-bottom:8px;
                                min-height:130px;{brd}">
                        <div style="display:flex;justify-content:space-between;
                                    align-items:flex-start;margin-bottom:5px;">
                            <span style="color:#C9A227;font-weight:700;
                                         font-size:0.83rem;">{item['table_name']}</span>
                            <span style="color:{cor_c};font-weight:800;
                                         font-size:0.88rem;">
                                {item['score_completude']}%</span>
                        </div>
                        <div style="color:#8B949E;font-size:0.73rem;line-height:1.4;
                                    margin-bottom:8px;">{desc}</div>
                        <div style="display:flex;gap:4px;flex-wrap:wrap;">
                            <span style="background:#58A6FF22;color:#58A6FF;
                                         border-radius:4px;padding:2px 7px;
                                         font-size:0.67rem;">{item['schema_name']}</span>
                            {f'<span style="background:#C9A22722;color:#C9A227;border-radius:4px;padding:2px 7px;font-size:0.67rem;">{item["dominio"]}</span>' if item['dominio'] else ''}
                            {f'<span style="background:#F8514922;color:#F85149;border-radius:4px;padding:2px 7px;font-size:0.67rem;">🔒 PII</span>' if item['tem_pii'] else ''}
                        </div>
                    </div>""", unsafe_allow_html=True)
                    if st.button("ℹ️ Detalhes",
                                 key=f"csel_{item['schema_name']}_{item['table_name']}",
                                 use_container_width=True):
                        chave = f"{item['schema_name']}.{item['table_name']}"
                        st.session_state["cat_sel"] = \
                            None if st.session_state["cat_sel"]==chave else chave
                        st.rerun()

        # Detalhe do ativo selecionado
        if st.session_state.get("cat_sel"):
            chave = st.session_state["cat_sel"]
            sc, tb = chave.split(".",1)
            row_c = df_cat[(df_cat["schema_name"]==sc)&
                           (df_cat["table_name"]==tb)]
            if not row_c.empty:
                item = row_c.iloc[0]
                cor_c2 = ("#3FB950" if item["score_completude"]==100 else
                          "#C9A227" if item["score_completude"]>=60 else "#F85149")
                st.markdown(f"""
                <div style="background:#161B22;border:1px solid {cor_c2}44;
                            border-radius:12px;padding:18px;margin-top:16px;">
                    <div style="display:flex;justify-content:space-between;
                                align-items:center;margin-bottom:12px;">
                        <div style="color:#E6EDF3;font-size:1.05rem;font-weight:800;">
                            {item['table_name']}</div>
                        <div style="color:{cor_c2};font-size:1.5rem;font-weight:800;">
                            {item['score_completude']}%</div>
                    </div>
                    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">
                        <div style="background:#0D1117;border-radius:8px;padding:8px;">
                            <div style="font-size:0.6rem;color:#8B949E;
                                        text-transform:uppercase;">DESCRIÇÃO</div>
                            <div style="color:#E6EDF3;font-size:0.78rem;">
                                {item['descricao'] or '—'}</div>
                        </div>
                        <div style="background:#0D1117;border-radius:8px;padding:8px;">
                            <div style="font-size:0.6rem;color:#8B949E;
                                        text-transform:uppercase;">DOMÍNIO</div>
                            <div style="color:#E6EDF3;font-size:0.78rem;">
                                {item['dominio'] or '—'}</div>
                        </div>
                        <div style="background:#0D1117;border-radius:8px;padding:8px;">
                            <div style="font-size:0.6rem;color:#8B949E;
                                        text-transform:uppercase;">OWNER</div>
                            <div style="color:#E6EDF3;font-size:0.78rem;">
                                {item['data_owner'] or '—'}</div>
                        </div>
                        <div style="background:#0D1117;border-radius:8px;padding:8px;">
                            <div style="font-size:0.6rem;color:#8B949E;
                                        text-transform:uppercase;">STEWARD</div>
                            <div style="color:#E6EDF3;font-size:0.78rem;">
                                {item['data_steward'] or '—'}</div>
                        </div>
                        <div style="background:#0D1117;border-radius:8px;padding:8px;">
                            <div style="font-size:0.6rem;color:#8B949E;
                                        text-transform:uppercase;">FUNÇÃO</div>
                            <div style="color:#E6EDF3;font-size:0.78rem;">
                                {item['funcao_negocio'] or '—'}</div>
                        </div>
                        <div style="background:#0D1117;border-radius:8px;padding:8px;">
                            <div style="font-size:0.6rem;color:#8B949E;
                                        text-transform:uppercase;">PII</div>
                            <div style="color:#F85149;font-size:0.78rem;">
                                {'🔒 Contém dado pessoal' if item['tem_pii'] else '—'}</div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# 🏛️ DOMÍNIOS
# ════════════════════════════════════════════════════════════════════
elif pagina == "🏛️ Domínios":
    page_header("🏛️","Domínios de Dados Corporativos",
                "Áreas de negócio responsáveis pela gestão e uso dos dados.")

    df_dom  = load_meta()
    df_glos = load_glossario()

    if not df_dom.empty:
        dominios = sorted([d for d in df_dom["dominio"].unique() if d])
        n_owners = df_dom["data_owner"].nunique()
        n_stw    = df_dom["data_steward"].nunique()
        termos_v = len(df_glos) if not df_glos.empty else 0
        cob      = round(len(df_glos[df_glos["status"]=="homologado"]) /
                         max(termos_v,1)*100) if termos_v else 0

        k1,k2,k3,k4,k5 = st.columns(5)
        with k1: st.markdown(kpi(len(dominios),"Domínios Ativos","#C9A227"),
                             unsafe_allow_html=True)
        with k2: st.markdown(kpi(n_owners,"Data Owners","#58A6FF"),
                             unsafe_allow_html=True)
        with k3: st.markdown(kpi(n_stw,"Data Stewards","#BC8CFF"),
                             unsafe_allow_html=True)
        with k4: st.markdown(kpi(termos_v,"Termos Vinculados","#3FB950"),
                             unsafe_allow_html=True)
        with k5: st.markdown(kpi(f"{cob}%","Cobertura de Termos","#C9A227"),
                             unsafe_allow_html=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        icones_dom = {"Crédito":"💳","Pagamentos":"💸","Clientes":"👥",
                      "Compliance":"🛡️","Produtos":"📦"}

        # Cards 3 colunas
        rows_d = [dominios[i:i+3] for i in range(0, len(dominios), 3)]
        for row_d in rows_d:
            cols_d = st.columns(3)
            for col_d, dom in zip(cols_d, row_d):
                df_d     = df_dom[df_dom["dominio"]==dom]
                score    = df_d["score_completude"].mean()
                owners_d = [o for o in df_d["data_owner"].unique() if o]
                stw_d    = [s for s in df_d["data_steward"].unique() if s]
                n_t      = len(df_glos[df_glos["dominio"]==dom]) \
                           if not df_glos.empty else 0
                cor_d    = ("#3FB950" if score>=80 else
                            "#C9A227" if score>=60 else "#F85149")
                ic       = icones_dom.get(dom,"🏛️")

                with col_d:
                    st.markdown(f"""
                    <div style="background:#161B22;border:1px solid #30363D;
                                border-radius:12px;padding:16px;margin-bottom:12px;">
                        <div style="display:flex;justify-content:space-between;
                                    align-items:center;margin-bottom:8px;">
                            <div style="display:flex;align-items:center;gap:6px;">
                                <span style="font-size:1.1rem;">{ic}</span>
                                <span style="color:#E6EDF3;font-weight:700;
                                             font-size:0.88rem;">{dom}</span>
                            </div>
                            <span style="color:{cor_d};font-weight:800;
                                         font-size:1.1rem;">{score:.0f}%</span>
                        </div>
                        <div style="background:#30363D;border-radius:4px;
                                    height:4px;margin-bottom:10px;">
                            <div style="background:{cor_d};border-radius:4px;
                                        height:4px;width:{min(score,100):.0f}%;"></div>
                        </div>
                        <div style="font-size:0.7rem;color:#8B949E;
                                    line-height:1.6;margin-bottom:8px;">
                            <span style="color:#E6EDF3;">Owner:</span>
                            {owners_d[0] if owners_d else '—'}<br>
                            <span style="color:#E6EDF3;">Stewards:</span>
                            {len(stw_d)} ·
                            <span style="color:#E6EDF3;">Termos:</span> {n_t} ·
                            <span style="color:#E6EDF3;">Ativos:</span> {len(df_d)}
                        </div>
                        <div style="display:flex;gap:4px;flex-wrap:wrap;">""",
                                unsafe_allow_html=True)
                    for sc_d in df_d["schema_name"].unique():
                        n_sc = len(df_d[df_d["schema_name"]==sc_d])
                        st.markdown(
                            f'<span style="background:#58A6FF22;color:#58A6FF;'
                            f'border-radius:4px;padding:2px 7px;font-size:0.65rem;">'
                            f'{sc_d} ({n_sc})</span>',
                            unsafe_allow_html=True)
                    st.markdown("</div></div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# 🛡️ SCORECARD
# ════════════════════════════════════════════════════════════════════
elif pagina == "🛡️ Scorecard":
    page_header("🛡️","Scorecard de Confiabilidade",
                "Avalie a maturidade e confiabilidade dos ativos de dados.")

    df_sc    = load_meta()
    df_links = load_links()

    if df_sc.empty:
        st.error("Não foi possível carregar os dados.")
    else:
        # 5 pilares
        doc  = df_sc["descricao"].apply(bool).mean()*100
        own  = df_sc["data_owner"].apply(bool).mean()*100
        # Relacionamentos: % de tabelas com ao menos 1 vínculo no glossary_asset_link
        tabs_com_link = df_links["table_name"].nunique() if not df_links.empty else 0
        rel  = (tabs_com_link / max(len(df_sc),1)) * 100
        qual = df_sc["score_completude"].mean()
        cert = (len(df_sc[df_sc["selo"]=="certificado"])/len(df_sc))*100
        ger  = (doc+own+rel+qual+cert)/5
        cor_g = "#3FB950" if ger>=80 else "#C9A227" if ger>=60 else "#F85149"

        # Score geral
        st.markdown(f"""
        <div style="background:#161B22;border:1px solid #30363D;border-radius:16px;
                    padding:24px;text-align:center;margin-bottom:20px;">
            <div style="font-size:0.72rem;color:#8B949E;text-transform:uppercase;
                        letter-spacing:2px;margin-bottom:6px;">
                Score Geral de Confiabilidade</div>
            <div style="font-size:4rem;font-weight:800;color:{cor_g};
                        line-height:1;">{ger:.0f}%</div>
            <div style="color:#8B949E;font-size:0.78rem;margin-top:4px;">
                Baseado em 5 pilares: Documentação, Ownership, Relacionamentos,
                Qualidade e Certificação</div>
        </div>""", unsafe_allow_html=True)

        # 5 pilares
        p1,p2,p3,p4,p5 = st.columns(5)
        for col, nome, val, ic in [
            (p1,"Documentação",doc,"📝"),
            (p2,"Ownership",own,"👤"),
            (p3,"Relacionamentos",rel,"🔗"),
            (p4,"Qualidade",qual,"⭐"),
            (p5,"Certificação",cert,"🏆"),
        ]:
            cor_p = "#3FB950" if val>=80 else "#C9A227" if val>=60 else "#F85149"
            with col:
                st.markdown(f"""
                <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;
                            padding:16px;text-align:center;margin-bottom:16px;">
                    <div style="font-size:1.3rem;margin-bottom:5px;">{ic}</div>
                    <div style="font-size:1.8rem;font-weight:800;color:{cor_p};">
                        {val:.0f}%</div>
                    <div style="color:#8B949E;font-size:0.72rem;margin-bottom:8px;">
                        {nome}</div>
                    <div style="background:#30363D;border-radius:4px;height:4px;">
                        <div style="background:{cor_p};border-radius:4px;height:4px;
                                    width:{min(val,100):.0f}%;"></div>
                    </div>
                </div>""", unsafe_allow_html=True)

        # Score por domínio
        section_divider("SCORE POR DOMÍNIO")
        dom_sc = df_sc[df_sc["dominio"].apply(bool)]\
                    .groupby("dominio")["score_completude"].mean()\
                    .reset_index().sort_values("score_completude",ascending=False)
        fig = px.bar(dom_sc, x="dominio", y="score_completude",
            color="score_completude",
            color_continuous_scale=["#F85149","#C9A227","#3FB950"],
            range_color=[0,100], template="plotly_dark",
            labels={"dominio":"","score_completude":"Score (%)"})
        fig.update_layout(
            paper_bgcolor="#161B22", plot_bgcolor="#161B22",
            font_family="Inter", showlegend=False,
            coloraxis_showscale=False, height=260,
            margin=dict(t=10,b=10,l=0,r=0))
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

        # Ranking owners
        section_divider("RANKING DE OWNERS")
        df_own = df_sc[df_sc["data_owner"].apply(bool)]\
                    .groupby("data_owner")["score_completude"].mean()\
                    .reset_index().sort_values("score_completude",ascending=False)
        for _, row in df_own.iterrows():
            cor_o = ("#3FB950" if row["score_completude"]>=80 else
                     "#C9A227" if row["score_completude"]>=60 else "#F85149")
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                        background:#161B22;border:1px solid #30363D;border-radius:8px;
                        padding:8px 14px;margin-bottom:5px;">
                <span style="color:#E6EDF3;font-size:0.8rem;">{row['data_owner']}</span>
                <div style="display:flex;align-items:center;gap:10px;">
                    <div style="background:#30363D;border-radius:4px;height:4px;width:100px;">
                        <div style="background:{cor_o};border-radius:4px;height:4px;
                                    width:{min(row['score_completude'],100):.0f}%;"></div>
                    </div>
                    <span style="color:{cor_o};font-weight:700;font-size:0.8rem;
                                 width:35px;text-align:right;">
                        {row['score_completude']:.0f}%</span>
                </div>
            </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# ⚡ MEU ESPAÇO — Área Operacional
# ════════════════════════════════════════════════════════════════════
elif pagina == "⚡ Meu Espaço":
    page_header("⚡",f"Olá, {u['nome']} 👋",
                "Suas pendências, responsabilidades e atividades de governança.")

    df_meta  = load_meta()
    df_gloss = load_glossario()

    # Contadores de pendências
    pend_aprov  = len(df_gloss[df_gloss["status"]=="em_revisao"]) \
                  if not df_gloss.empty else 0
    sem_desc    = len(df_meta[df_meta["descricao"]==""]) \
                  if not df_meta.empty else 0
    sem_owner   = len(df_meta[df_meta["data_owner"]==""]) \
                  if not df_meta.empty else 0
    sem_steward = len(df_meta[df_meta["data_steward"]==""]) \
                  if not df_meta.empty else 0
    sem_dom     = len(df_meta[df_meta["dominio"]==""]) \
                  if not df_meta.empty else 0
    total_pend  = pend_aprov + sem_desc + sem_owner + sem_steward + sem_dom

    # Header de pendências
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1C2128,#21262D);
                border:1px solid #C9A22733;border-radius:12px;
                padding:14px 18px;margin-bottom:16px;
                display:flex;align-items:center;gap:12px;">
        <div style="background:#C9A22722;border-radius:8px;padding:8px;
                    font-size:1.2rem;">⚡</div>
        <div>
            <div style="color:#E6EDF3;font-weight:700;font-size:0.9rem;">
                Você possui <span style="color:#C9A227;">{total_pend}</span>
                ações pendentes na sua área de trabalho.</div>
            <div style="color:#8B949E;font-size:0.75rem;margin-top:2px;">
                Revise as pendências abaixo e tome as ações necessárias.</div>
        </div>
    </div>""", unsafe_allow_html=True)

    section_divider("O QUE PRECISO FAZER AGORA?")

    acoes = [
        ("APROVAR",     f"{pend_aprov} termos aguardam aprovação",
         "#C9A227","→ Workflow", pend_aprov),
        ("DOCUMENTAR",  f"{sem_desc} ativos sem descrição",
         "#58A6FF","→ Curadoria", sem_desc),
        ("ATRIBUIR",    f"{sem_owner} ativos sem Owner definido",
         "#F85149","→ Curadoria", sem_owner),
        ("ALOCAR",      f"{sem_steward} ativos sem Steward definido",
         "#FF7B72","→ Curadoria", sem_steward),
        ("CLASSIFICAR", f"{sem_dom} ativos sem domínio",
         "#BC8CFF","→ Curadoria", sem_dom),
    ]
    for tipo, msg, cor_a, destino, qtd in acoes:
        if qtd > 0:
            st.markdown(f"""
            <div style="background:#161B22;border:1px solid #30363D;border-radius:8px;
                        padding:11px 16px;margin-bottom:6px;
                        display:flex;align-items:center;justify-content:space-between;">
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="background:{cor_a}22;color:{cor_a};border-radius:4px;
                                 padding:2px 8px;font-size:0.68rem;font-weight:700;">
                        {tipo}</span>
                    <span style="color:#E6EDF3;font-size:0.83rem;">{msg}</span>
                </div>
                <span style="color:#8B949E;font-size:0.75rem;">{destino}</span>
            </div>""", unsafe_allow_html=True)

    section_divider("MINHAS RESPONSABILIDADES")

    if not df_meta.empty:
        como_owner   = len(df_meta[df_meta["data_owner"]==usuario])
        como_steward = len(df_meta[df_meta["data_steward"]==usuario])
        doc_media    = df_meta["score_completude"].mean()
        dom_uniq     = df_meta["dominio"].nunique()

        k1,k2,k3,k4 = st.columns(4)
        with k1: st.markdown(kpi(como_owner,"Como Owner","#C9A227"),
                             unsafe_allow_html=True)
        with k2: st.markdown(kpi(como_steward,"Como Steward","#58A6FF"),
                             unsafe_allow_html=True)
        with k3: st.markdown(kpi(dom_uniq,"Domínios Acompanhados","#BC8CFF"),
                             unsafe_allow_html=True)
        with k4:
            cor_d = ("#3FB950" if doc_media>=80 else
                     "#C9A227" if doc_media>=60 else "#F85149")
            st.markdown(kpi(f"{doc_media:.0f}%","Documentação Média",cor_d),
                        unsafe_allow_html=True)

    # Fila de aprovação
    if is_aprovador and pend_aprov > 0:
        section_divider("MINHAS APROVAÇÕES")
        df_pend = df_gloss[df_gloss["status"]=="em_revisao"]
        for _, row in df_pend.iterrows():
            with st.expander(
                f"📋 **{row['termo']}** · {row['dominio']} · {row['criticidade']}"
            ):
                st.markdown(f"**Definição:** {row['definicao']}")
                st.markdown(f"**Steward:** {row['steward_email']}")
                ca,cr = st.columns(2)
                with ca:
                    if st.button("✅ Aprovar",
                                 key=f"mea_{row['glossary_id']}",
                                 use_container_width=True):
                        ok,_ = exe(
                            f"UPDATE meridian_governanca.business_glossary "
                            f"SET status='homologado',"
                            f"atualizado_por='{esc(usuario)}',"
                            f"atualizado_em=current_timestamp() "
                            f"WHERE glossary_id='{row['glossary_id']}'"
                        )
                        if ok:
                            st.success("✅ Homologado!")
                            st.cache_data.clear(); st.rerun()
                with cr:
                    motivo = st.text_input("Motivo",
                                           key=f"mem_{row['glossary_id']}")
                    if st.button("❌ Rejeitar",
                                 key=f"mer_{row['glossary_id']}",
                                 use_container_width=True):
                        if motivo:
                            ok,_ = exe(
                                f"UPDATE meridian_governanca.business_glossary "
                                f"SET status='rascunho',"
                                f"atualizado_por='{esc(usuario)}',"
                                f"atualizado_em=current_timestamp() "
                                f"WHERE glossary_id='{row['glossary_id']}'"
                            )
                            if ok:
                                st.warning("↩️ Devolvido.")
                                st.cache_data.clear(); st.rerun()
                        else: st.warning("Informe o motivo.")

    # Meus termos
    section_divider("MEUS TERMOS NO GLOSSÁRIO")
    df_meus = df_gloss[df_gloss["steward_email"]==usuario] \
              if not df_gloss.empty else pd.DataFrame()
    if not df_meus.empty:
        for _, row in df_meus.iterrows():
            cor_s = {"homologado":"#3FB950","em_revisao":"#58A6FF",
                     "rascunho":"#8B949E"}.get(row["status"],"#8B949E")
            st.markdown(f"""
            <div style="background:#161B22;border:1px solid #30363D;border-radius:8px;
                        padding:9px 14px;margin-bottom:5px;
                        display:flex;justify-content:space-between;align-items:center;">
                <span style="color:#E6EDF3;font-size:0.82rem;font-weight:600;">
                    {row['termo']}</span>
                <span style="color:{cor_s};font-size:0.75rem;font-weight:600;">
                    ● {row['status'].replace('_',' ').title()}</span>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#161B22;border:1px solid #30363D;border-radius:8px;
                    padding:16px;text-align:center;">
            <div style="color:#8B949E;font-size:0.82rem;">
                Nenhum termo vinculado ao seu e-mail.</div>
        </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# ✏️ CURADORIA
# ════════════════════════════════════════════════════════════════════
elif pagina == "✏️ Curadoria":
    page_header("✏️","Curadoria de Conhecimento",
                "Enriqueça o entendimento — documente, classifique e atribua responsáveis.")

    df_cur = load_meta()

    if not df_cur.empty:
        cur1, cur2 = st.tabs(["📋 Individual","⚡ Em Lote"])

        with cur1:
            c_left, c_right = st.columns([1,2])
            with c_left:
                schemas = sorted(df_cur["schema_name"].unique().tolist())
                sel_s = st.selectbox("SCHEMA", schemas, key="cur_s")
                tabs_s = df_cur[df_cur["schema_name"]==sel_s]["table_name"].tolist()
                sel_t = st.selectbox("TABELA", tabs_s, key="cur_t")

            with c_right:
                row = df_cur[(df_cur["schema_name"]==sel_s)&
                             (df_cur["table_name"]==sel_t)].iloc[0]
                doc_p  = 100 if row["descricao"] else 0
                own_p  = 100 if row["data_owner"] else 0
                cert_p = 100 if row["selo"]=="certificado" else 0
                qual_p = row["score_completude"]
                rel_p  = 0  # sem dado de relacionamento por tabela ainda

                # Header
                st.markdown(f"""
                <div style="background:#161B22;border:1px solid #30363D;border-radius:10px;
                            padding:12px 16px;margin-bottom:12px;">
                    <div style="color:#C9A227;font-weight:700;font-size:0.9rem;">
                        {sel_t}</div>
                    <div style="color:#8B949E;font-size:0.72rem;margin-top:2px;">
                        {row['descricao'][:60]+'...' if row['descricao'] and
                         len(row['descricao'])>60 else row['descricao'] or 'Sem descrição'}
                    </div>
                </div>""", unsafe_allow_html=True)

                # 5 pilares
                pp1,pp2,pp3,pp4,pp5 = st.columns(5)
                for pcol, pn, pv in [
                    (pp1,"DOCUMENTAÇÃO",doc_p),(pp2,"OWNERSHIP",own_p),
                    (pp3,"RELACIONAMENTOS",rel_p),(pp4,"QUALIDADE",qual_p),
                    (pp5,"CERTIFICAÇÃO",cert_p)
                ]:
                    cor_pp = ("#3FB950" if pv>=80 else
                              "#C9A227" if pv>0 else "#F85149")
                    with pcol:
                        st.markdown(f"""
                        <div style="background:#0D1117;border:1px solid #30363D;
                                    border-radius:8px;padding:9px;text-align:center;
                                    margin-bottom:10px;">
                            <div style="font-size:0.58rem;color:#8B949E;
                                        text-transform:uppercase;letter-spacing:1px;">
                                {pn}</div>
                            <div style="font-size:1.2rem;font-weight:800;color:{cor_pp};">
                                {f'{pv}%' if pv>0 else 'Não Iniciado'}</div>
                        </div>""", unsafe_allow_html=True)

                ed1, ed2 = st.columns(2)
                with ed1:
                    new_desc = st.text_area("DESCRIÇÃO",
                        value=row["descricao"] or "", height=80, key="c_desc",
                        placeholder="Descreva o propósito desta tabela...")
                    doms = ["","Crédito","Pagamentos","Clientes","Compliance","Produtos"]
                    dom_i = doms.index(row["dominio"]) \
                            if row["dominio"] in doms else 0
                    new_dom = st.selectbox("DOMÍNIO", doms, index=dom_i, key="c_dom")
                with ed2:
                    new_own = st.text_input("DATA OWNER",
                        value=row["data_owner"] or "", key="c_own")
                    new_stw = st.text_input("DATA STEWARD",
                        value=row["data_steward"] or "", key="c_stw")

                bc1,bc2 = st.columns(2)
                with bc1:
                    if st.button("💾 Salvar Alterações",type="primary",
                                 key="c_save",use_container_width=True):
                        filled = sum([bool(new_desc),bool(new_dom),
                                      bool(new_own),bool(new_stw),
                                      bool(row["funcao_negocio"])])
                        ns = filled*20
                        sl = ("certificado" if ns==100 else
                              "parcial" if ns>=60 else "pendente")
                        ok,err = exe(
                            f"UPDATE meridian_governanca.tabelas_metadata "
                            f"SET descricao='{esc(new_desc)}',"
                            f"dominio='{esc(new_dom)}',"
                            f"data_owner='{esc(new_own)}',"
                            f"data_steward='{esc(new_stw)}',"
                            f"score_completude={ns},selo='{sl}',"
                            f"atualizado_em=current_timestamp() "
                            f"WHERE schema_name='{sel_s}' AND table_name='{sel_t}'"
                        )
                        if ok:
                            exe(f"INSERT INTO meridian_governanca.metadata_audit "
                                f"VALUES ('{uuid.uuid4()}',current_timestamp(),"
                                f"'{sel_s}','{sel_t}','tabela','','metadados',"
                                f"'{row['score_completude']}','{ns}',"
                                f"'manual','{esc(usuario)}','{esc(usuario[:8])}')")
                            st.success(f"✅ Salvo! Score: {ns}%")
                            st.cache_data.clear(); st.rerun()
                        else: st.error(f"Erro: {err}")
                with bc2:
                    if st.button("🤖 Sugerir com IA",key="c_ai",
                                 use_container_width=True):
                        sugestoes = {
                            "clientes_raw":("Dados brutos de clientes ingeridos do sistema core bancário, contendo informações cadastrais e de contato.","Clientes"),
                            "contas_raw":("Dados brutos de contas correntes e poupança dos clientes do banco.","Clientes"),
                            "transacoes_raw":("Transações financeiras brutas de todos os canais digitais e físicos.","Pagamentos"),
                            "propostas_credito_raw":("Propostas de crédito recebidas pelos canais com status de aprovação.","Crédito"),
                            "pix_raw":("Transações PIX brutas do Sistema de Pagamentos Instantâneos do Banco Central.","Pagamentos"),
                            "dim_clientes":("Dimensão de clientes tratada e enriquecida com segmentação e score.","Clientes"),
                            "dim_contas":("Dimensão de contas com dados consolidados e limites.","Clientes"),
                            "fato_transacoes":("Fato de transações financeiras consolidadas por período e canal.","Pagamentos"),
                            "fato_credito":("Fato de operações de crédito aprovadas e recusadas.","Crédito"),
                            "fato_inadimplencia":("Fato de inadimplência com dias de atraso e valores.","Crédito"),
                            "fato_pix":("Fato de transações PIX consolidadas por período.","Pagamentos"),
                            "dim_produtos":("Dimensão de produtos financeiros do banco.","Produtos"),
                            "indicadores_carteira":("Indicadores consolidados da carteira de crédito.","Crédito"),
                            "perfil_cliente_360":("Visão 360 do cliente com score e propensão a churn.","Clientes"),
                            "dashboard_inadimplencia":("Base para dashboard executivo de inadimplência.","Crédito"),
                            "indicadores_pix":("Indicadores de volume e performance do PIX.","Pagamentos"),
                            "base_lgpd":("Mapeamento de dados pessoais para conformidade LGPD.","Compliance"),
                        }
                        sug = sugestoes.get(sel_t,
                            (f"Tabela {sel_t} do schema {sel_s}.",""))
                        st.session_state["ai_desc"] = sug[0]
                        st.session_state["ai_dom"]  = sug[1]
                        st.rerun()

                if "ai_desc" in st.session_state:
                    st.markdown("""
                    <div style="background:#C9A22711;border:1px solid #C9A22733;
                                border-radius:8px;padding:10px 14px;margin-top:8px;">
                        <div style="color:#C9A227;font-weight:700;font-size:0.75rem;">
                            🤖 Sugestão da IA — revise antes de salvar</div>
                    </div>""", unsafe_allow_html=True)
                    sug_d = st.text_area("Descrição sugerida",
                        value=st.session_state["ai_desc"], key="sug_d")
                    so = ["","Crédito","Pagamentos","Clientes","Compliance","Produtos"]
                    sv = st.session_state["ai_dom"]
                    si = so.index(sv) if sv in so else 0
                    sug_dom = st.selectbox("Domínio sugerido",so,index=si,key="sd2")
                    sa1,sa2 = st.columns(2)
                    with sa1:
                        if st.button("✅ Aceitar",key="ai_ac",use_container_width=True):
                            filled = sum([bool(sug_d),bool(sug_dom),
                                          bool(new_own),bool(new_stw),
                                          bool(row["funcao_negocio"])])
                            ns = filled*20
                            sl = ("certificado" if ns==100 else
                                  "parcial" if ns>=60 else "pendente")
                            ok,_ = exe(
                                f"UPDATE meridian_governanca.tabelas_metadata "
                                f"SET descricao='{esc(sug_d)}',"
                                f"dominio='{esc(sug_dom)}',"
                                f"score_completude={ns},selo='{sl}',"
                                f"atualizado_em=current_timestamp() "
                                f"WHERE schema_name='{sel_s}' AND table_name='{sel_t}'"
                            )
                            if ok:
                                exe(f"INSERT INTO meridian_governanca.metadata_audit "
                                    f"VALUES ('{uuid.uuid4()}',current_timestamp(),"
                                    f"'{sel_s}','{sel_t}','tabela','','metadados',"
                                    f"'{row['score_completude']}','{ns}',"
                                    f"'ia','{esc(usuario)}','{esc(usuario[:8])}')")
                                st.success("✅ Sugestão aplicada!")
                                del st.session_state["ai_desc"]
                                del st.session_state["ai_dom"]
                                st.cache_data.clear(); st.rerun()
                    with sa2:
                        if st.button("❌ Descartar",key="ai_dc",use_container_width=True):
                            del st.session_state["ai_desc"]
                            del st.session_state["ai_dom"]
                            st.rerun()

        with cur2:
            f1c,f2c = st.columns(2)
            with f1c:
                fl_s = st.selectbox("Schema",
                    ["Todos"]+sorted(df_cur["schema_name"].unique().tolist()),
                    key="lote_s")
            with f2c:
                fl_sl = st.selectbox("Selo",
                    ["Todos","certificado","parcial","pendente"],key="lote_sl")
            df_l = df_cur.copy()
            if fl_s  != "Todos": df_l = df_l[df_l["schema_name"]==fl_s]
            if fl_sl != "Todos": df_l = df_l[df_l["selo"]==fl_sl]
            df_l_ed = df_l[["schema_name","table_name",
                             "score_completude","selo"]].copy()
            df_l_ed.insert(0,"Selecionar",False)
            edited = st.data_editor(
                df_l_ed.rename(columns={
                    "schema_name":"Schema","table_name":"Tabela",
                    "score_completude":"Score","selo":"Selo"}),
                use_container_width=True,hide_index=True,
                column_config={"Selecionar":st.column_config.CheckboxColumn()}
            )
            sels = edited[edited["Selecionar"]==True]
            if len(sels)>0:
                st.markdown(f'<div style="color:#C9A227;font-weight:600;'
                            f'font-size:0.82rem;margin:6px 0;">'
                            f'{len(sels)} tabela(s) selecionada(s)</div>',
                            unsafe_allow_html=True)
                lb1,lb2,lb3 = st.columns(3)
                with lb1:
                    l_dom = st.selectbox("Domínio",
                        ["","Crédito","Pagamentos","Clientes",
                         "Compliance","Produtos"], key="l_dom")
                with lb2: l_own = st.text_input("Owner",key="l_own")
                with lb3: l_stw = st.text_input("Steward",key="l_stw")
                if st.button(f"🚀 Aplicar em {len(sels)} tabela(s)",
                             type="primary",key="l_apply"):
                    erros = []
                    for _,r in sels.iterrows():
                        sets = []
                        if l_dom: sets.append(f"dominio='{esc(l_dom)}'")
                        if l_own: sets.append(f"data_owner='{esc(l_own)}'")
                        if l_stw: sets.append(f"data_steward='{esc(l_stw)}'")
                        if sets:
                            sets.append("atualizado_em=current_timestamp()")
                            ok,_ = exe(
                                f"UPDATE meridian_governanca.tabelas_metadata "
                                f"SET {', '.join(sets)} "
                                f"WHERE schema_name='{r['Schema']}' "
                                f"AND table_name='{r['Tabela']}'"
                            )
                            if not ok: erros.append(r["Tabela"])
                    if erros: st.warning(f"Erros: {erros}")
                    else:
                        st.success(f"✅ {len(sels)} tabelas atualizadas!")
                        st.cache_data.clear(); st.rerun()

# ════════════════════════════════════════════════════════════════════
# 🕐 AUDITORIA
# ════════════════════════════════════════════════════════════════════
elif pagina == "🕐 Auditoria":
    page_header("🕐","Trilha de Auditoria",
                "Rastreabilidade — quem alterou, quando e por quê.")

    df_aud, err = qry("""
        SELECT timestamp_op, schema_name, table_name, tipo_objeto,
               campo_alterado, valor_anterior, valor_novo,
               origem, alterado_por
        FROM meridian_governanca.metadata_audit
        ORDER BY timestamp_op DESC LIMIT 500
    """)

    if err:
        st.error(f"Erro: {err}")
    elif df_aud.empty:
        st.markdown("""
        <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;
                    padding:40px;text-align:center;">
            <div style="font-size:2.5rem;margin-bottom:10px;">📭</div>
            <div style="color:#E6EDF3;font-weight:700;">Nenhum registro ainda</div>
            <div style="color:#8B949E;margin-top:6px;font-size:0.82rem;">
                As alterações feitas na Curadoria e no Glossário aparecerão aqui.</div>
        </div>""", unsafe_allow_html=True)
    else:
        total  = len(df_aud)
        manual = len(df_aud[df_aud["origem"]=="manual"])
        ia_c   = len(df_aud[df_aud["origem"]=="ia"])

        k1,k2,k3 = st.columns(3)
        with k1: st.markdown(kpi(total,"Total de Registros","#C9A227"),
                             unsafe_allow_html=True)
        with k2: st.markdown(kpi(manual,"Alterações Manuais","#58A6FF"),
                             unsafe_allow_html=True)
        with k3: st.markdown(kpi(ia_c,"Via Inteligência Artificial","#BC8CFF"),
                             unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        af1,af2,af3 = st.columns(3)
        with af1:
            f_sc = st.selectbox("Schema",
                ["Todos"]+sorted(df_aud["schema_name"].dropna().unique().tolist()),
                key="a_sc")
        with af2:
            f_or = st.selectbox("Origem",["Todos","manual","ia"],key="a_or")
        with af3:
            f_lim = st.selectbox("Linhas",[50,100,200,500],key="a_lim")

        df_af = df_aud.copy()
        if f_sc != "Todos": df_af = df_af[df_af["schema_name"]==f_sc]
        if f_or != "Todos": df_af = df_af[df_af["origem"]==f_or]
        df_af = df_af.head(f_lim)

        # Tabela customizada com badges
        st.markdown("""
        <div style="background:#161B22;border:1px solid #30363D;border-radius:10px;
                    overflow:hidden;margin-top:8px;">
        <table style="width:100%;border-collapse:collapse;">
        <thead><tr style="border-bottom:1px solid #30363D;">
            <th style="color:#8B949E;font-size:0.65rem;font-weight:700;text-transform:uppercase;padding:9px 12px;text-align:left;">DATA/HORA</th>
            <th style="color:#8B949E;font-size:0.65rem;font-weight:700;text-transform:uppercase;padding:9px 12px;text-align:left;">SCHEMA</th>
            <th style="color:#8B949E;font-size:0.65rem;font-weight:700;text-transform:uppercase;padding:9px 12px;text-align:left;">TABELA</th>
            <th style="color:#8B949E;font-size:0.65rem;font-weight:700;text-transform:uppercase;padding:9px 12px;text-align:left;">CAMPO</th>
            <th style="color:#8B949E;font-size:0.65rem;font-weight:700;text-transform:uppercase;padding:9px 12px;text-align:left;">VALOR ANTERIOR</th>
            <th style="color:#8B949E;font-size:0.65rem;font-weight:700;text-transform:uppercase;padding:9px 12px;text-align:left;">VALOR NOVO</th>
            <th style="color:#8B949E;font-size:0.65rem;font-weight:700;text-transform:uppercase;padding:9px 12px;text-align:left;">ORIGEM</th>
        </tr></thead><tbody>
        """, unsafe_allow_html=True)

        for _, row in df_af.iterrows():
            ts      = str(row["timestamp_op"])[:16] if row["timestamp_op"] else "—"
            oc      = "#BC8CFF" if row["origem"]=="ia" else "#58A6FF"
            ot      = "IA" if row["origem"]=="ia" else "Manual"
            va      = str(row["valor_anterior"])[:30] if row["valor_anterior"] else "—"
            vn      = str(row["valor_novo"])[:40] if row["valor_novo"] else "—"
            st.markdown(f"""
            <tr style="border-bottom:1px solid #21262D;">
                <td style="color:#8B949E;font-size:0.75rem;padding:8px 12px;">{ts}</td>
                <td style="color:#58A6FF;font-size:0.75rem;padding:8px 12px;">
                    {row['schema_name'] or '—'}</td>
                <td style="color:#E6EDF3;font-size:0.75rem;padding:8px 12px;
                           font-weight:600;">{row['table_name'] or '—'}</td>
                <td style="color:#8B949E;font-size:0.75rem;padding:8px 12px;">
                    {row['campo_alterado'] or '—'}</td>
                <td style="color:#8B949E;font-size:0.75rem;padding:8px 12px;">{va}</td>
                <td style="color:#E6EDF3;font-size:0.75rem;padding:8px 12px;">{vn}</td>
                <td style="padding:8px 12px;">
                    <span style="background:{oc}22;color:{oc};border-radius:4px;
                                 padding:2px 8px;font-size:0.68rem;font-weight:700;">
                        {ot}</span></td>
            </tr>""", unsafe_allow_html=True)

        st.markdown("</tbody></table></div>", unsafe_allow_html=True)
