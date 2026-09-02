"""
app.py — Plataforma de Governança de Dados
Banco Meridian | v5.0
© Tereza Cristina — Todos os direitos reservados.
Reprodução proibida sem autorização expressa.
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
section[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    color: #8B949E !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    text-align: left !important;
    padding: 5px 10px !important;
    width: 100% !important;
    box-shadow: none !important;
    margin-bottom: 1px !important;
    justify-content: flex-start !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: #161B22 !important;
    color: #E6EDF3 !important;
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
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# CONEXÃO
# ════════════════════════════════════════════════════════════════════
@st.cache_resource
def get_conn():
    conn = sql.connect(
        server_hostname = st.secrets["DATABRICKS_HOST"],
        http_path       = st.secrets["DATABRICKS_HTTP_PATH"],
        access_token    = st.secrets["DATABRICKS_TOKEN"],
        catalog         = "workspace",
        schema          = "meridian_governanca"
    )
    return conn

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
# MENU — reorganizado por jornada do usuário
# ════════════════════════════════════════════════════════════════════
MENU = {
    "PESSOAL":        ["⚡ Meu Espaço"],
    "INÍCIO":         ["🏠 Início"],
    "CONHECIMENTO":   ["📖 Glossário", "🏛️ Domínios"],
    "DADOS":          ["📋 Catálogo", "🔗 Linhagem", "📦 Produtos"],
    "CONFIABILIDADE": ["🛡️ Scorecard", "🏆 Qualidade", "🥇 Certificação"],
    "GESTÃO":         ["📊 Indicadores"],
    "OPERAÇÃO":       ["✏️ Curadoria", "🕐 Auditoria"],
}

# ════════════════════════════════════════════════════════════════════
# CARREGAMENTO DE DADOS
# ════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def load_meta():
    df,_ = qry("SELECT * FROM meridian_governanca.tabelas_metadata")
    return df if df is not None else pd.DataFrame()

@st.cache_data(ttl=300)
def load_glossario():
    df,_ = qry("""SELECT * FROM meridian_governanca.business_glossary
                  ORDER BY CASE status WHEN 'homologado' THEN 1
                  WHEN 'em_revisao' THEN 2 ELSE 3 END, termo""")
    return df if df is not None else pd.DataFrame()

@st.cache_data(ttl=300)
def load_links():
    df,_ = qry("SELECT * FROM meridian_governanca.glossary_asset_link")
    return df if df is not None else pd.DataFrame()

@st.cache_data(ttl=300)
def load_rules():
    df,_ = qry("SELECT * FROM meridian_governanca.business_rules")
    return df if df is not None else pd.DataFrame()

@st.cache_data(ttl=300)
def load_sugestoes_conceitos():
    df,_ = qry("SELECT * FROM meridian_governanca.sugestoes_conceitos ORDER BY criado_em DESC")
    return df if df is not None else pd.DataFrame()

@st.cache_data(ttl=300)
def load_sugestoes_regras():
    df,_ = qry("SELECT * FROM meridian_governanca.sugestoes_regras ORDER BY criado_em DESC")
    return df if df is not None else pd.DataFrame()

@st.cache_data(ttl=300)
def load_solicitacoes_acesso():
    df,_ = qry("SELECT * FROM meridian_governanca.solicitacoes_acesso ORDER BY criado_em DESC")
    return df if df is not None else pd.DataFrame()

@st.cache_data(ttl=300)
def load_quality_dimensions():
    df,_ = qry("SELECT * FROM meridian_governanca.gd_quality_dimensions ORDER BY score_final DESC")
    return df if df is not None else pd.DataFrame()

@st.cache_data(ttl=300)
def load_certification():
    df,_ = qry("SELECT * FROM meridian_governanca.gd_certification ORDER BY score_qualidade DESC")
    return df if df is not None else pd.DataFrame()

@st.cache_data(ttl=300)
def load_indicators_snapshot():
    df,_ = qry("SELECT * FROM meridian_governanca.gd_indicators_snapshot ORDER BY data_snapshot ASC")
    return df if df is not None else pd.DataFrame()

@st.cache_data(ttl=300)
def load_produtos():
    df,_ = qry("SELECT * FROM meridian_governanca.produtos_dados ORDER BY status, nome")
    return df if df is not None else pd.DataFrame()

@st.cache_data(ttl=300)
def load_produto_ativos():
    df,_ = qry("SELECT * FROM meridian_governanca.produto_ativos")
    return df if df is not None else pd.DataFrame()

@st.cache_data(ttl=300)
def load_linhagem():
    df,_ = qry("SELECT * FROM meridian_governanca.linhagem_ativos ORDER BY origem_schema, origem_tabela")
    return df if df is not None else pd.DataFrame()

@st.cache_data(ttl=300)
def load_solicitacoes_qualidade():
    df,_ = qry("SELECT * FROM meridian_governanca.solicitacoes_qualidade ORDER BY criado_em DESC")
    return df if df is not None else pd.DataFrame()

# ════════════════════════════════════════════════════════════════════
# COMPONENTES REUTILIZÁVEIS
# ════════════════════════════════════════════════════════════════════
def page_header(icone, titulo, subtitulo=""):
    perfil = st.session_state.get("perfil_atual","consultante")
    cor    = PERFIL_COR.get(perfil,"#58A6FF")
    nome   = st.session_state.get("nome_atual","")
    label  = PERFIL_LABEL.get(perfil,"")
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#161B22,#1C2128);
                border:1px solid #30363D;border-radius:12px;
                padding:14px 20px;margin-bottom:16px;
                display:flex;align-items:center;justify-content:space-between;">
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="background:#C9A22722;border-radius:8px;padding:8px;font-size:1.2rem;">{icone}</div>
            <div>
                <div style="color:#E6EDF3;font-size:1.05rem;font-weight:800;">{titulo}</div>
                {f'<div style="color:#8B949E;font-size:0.75rem;">{subtitulo}</div>' if subtitulo else ''}
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
        border-radius:10px;padding:14px 16px;border-top:3px solid {cor};cursor:help;">
        <div style="font-size:0.62rem;color:#8B949E;font-weight:700;
                    text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">
            {icone} {label}</div>
        <div style="font-size:1.7rem;font-weight:800;color:{cor};">{valor}</div>
    </div>"""

def section_divider(titulo):
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;margin:18px 0 12px;">
        <div style="height:1px;background:#30363D;flex:1;"></div>
        <span style="color:#8B949E;font-size:0.65rem;font-weight:700;
                     text-transform:uppercase;letter-spacing:1.5px;">{titulo}</span>
        <div style="height:1px;background:#30363D;flex:1;"></div>
    </div>""", unsafe_allow_html=True)

def avatar(nome, cor="#C9A227", size=36):
    iniciais = "".join([p[0].upper() for p in nome.split()[:2]])
    return f"""<div style="width:{size}px;height:{size}px;border-radius:50%;
        background:{cor}22;border:2px solid {cor}44;flex-shrink:0;
        display:inline-flex;align-items:center;justify-content:center;
        color:{cor};font-weight:800;font-size:{size//3}px;">{iniciais}</div>"""

def estado_vazio(icone, titulo, descricao):
    st.markdown(f"""
    <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;
                padding:40px;text-align:center;">
        <div style="font-size:2.5rem;margin-bottom:10px;">{icone}</div>
        <div style="color:#E6EDF3;font-weight:700;margin-bottom:6px;">{titulo}</div>
        <div style="color:#8B949E;font-size:0.82rem;">{descricao}</div>
    </div>""", unsafe_allow_html=True)

def copyright_footer():
    st.markdown("""
    <div style="border-top:1px solid #21262D;padding:12px 0;margin-top:32px;text-align:center;">
        <div style="color:#484F58;font-size:0.65rem;line-height:1.6;">
            © Plataforma de Governança de Dados — Concepção, arquitetura,
            funcionalidades, regras e estratégias são de propriedade intelectual de
            <span style="color:#C9A227;font-weight:600;">Tereza Cristina</span>.<br>
            Reprodução, cópia ou adaptação proibidas sem autorização expressa da autora.
        </div>
    </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# SIDEBAR
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
        email = st.selectbox(
            "Selecione seu usuário",
            list(USUARIOS.keys()),
            format_func=lambda x: f"{USUARIOS[x]['nome']} · {USUARIOS[x]['perfil']}",
            label_visibility="collapsed"
        )
        if st.button("Entrar →", key="login", use_container_width=True):
            st.session_state["usuario"]      = email
            st.session_state["perfil_atual"] = USUARIOS[email]["perfil"]
            st.session_state["nome_atual"]   = USUARIOS[email]["nome"]
            st.session_state["pagina"]       = "🏠 Início"
            st.rerun()
        st.stop()

    u      = USUARIOS[st.session_state["usuario"]]
    perfil = u["perfil"]
    cor    = PERFIL_COR[perfil]
    st.session_state["perfil_atual"] = perfil
    st.session_state["nome_atual"]   = u["nome"]
    is_curador   = perfil in ["curador","aprovador"]
    is_aprovador = perfil == "aprovador"

    if "pagina" not in st.session_state:
        st.session_state["pagina"] = "🏠 Início"

    st.markdown(f"""
    <div style="background:#161B22;border:1px solid #30363D;border-radius:8px;
                padding:8px 10px;margin-bottom:10px;">
        <div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;
                    letter-spacing:1px;">Usuário logado</div>
        <div style="font-weight:700;color:#E6EDF3;font-size:0.82rem;">{u['nome']}</div>
        <div style="color:{cor};font-size:0.72rem;font-weight:600;">{PERFIL_LABEL[perfil]}</div>
    </div>""", unsafe_allow_html=True)

    for secao, itens in MENU.items():
        # Ocultar OPERAÇÃO para consultante
        if secao == "OPERAÇÃO" and perfil == "consultante":
            continue
        st.markdown(
            f'<div style="font-size:0.58rem;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:1.5px;color:#484F58;padding:8px 10px 3px;">{secao}</div>',
            unsafe_allow_html=True)
        for item in itens:
            is_active = st.session_state["pagina"] == item
            if is_active:
                st.markdown(f"""
                <div style="background:#C9A22718;border-left:3px solid #C9A227;
                            border-radius:0 6px 6px 0;padding:6px 10px 6px 9px;
                            font-size:0.82rem;font-weight:700;color:#C9A227;
                            margin-bottom:1px;">{item}</div>""",
                            unsafe_allow_html=True)
            else:
                if st.button(item, key=f"nav_{item}", use_container_width=True):
                    st.session_state["pagina"] = item
                    for k in ["gid_sel","cat_sel","dom_sel","sc_pilar"]:
                        st.session_state.pop(k, None)
                    st.rerun()

    st.markdown('<div style="height:1px;background:#30363D;margin:10px 0 8px;"></div>',
                unsafe_allow_html=True)
    if st.button("↩ Sair", key="logout", use_container_width=True):
        st.session_state["usuario"] = None
        st.rerun()

pagina       = st.session_state.get("pagina","🏠 Início")
usuario      = st.session_state["usuario"]
u            = USUARIOS[usuario]
perfil       = u["perfil"]
is_curador   = perfil in ["curador","aprovador"]
is_aprovador = perfil == "aprovador"

# ════════════════════════════════════════════════════════════════════
# 🏠 INÍCIO — Central de Conhecimento e Descoberta
# ════════════════════════════════════════════════════════════════════
if pagina == "🏠 Início":
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#161B22,#1C2128);
                border:1px solid #30363D;border-radius:16px;
                padding:28px 32px;margin-bottom:20px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div style="color:#E6EDF3;font-size:1.5rem;font-weight:800;margin-bottom:6px;">
                    Plataforma de Governança de Dados</div>
                <div style="color:#8B949E;font-size:0.85rem;max-width:560px;line-height:1.6;">
                    Um espaço para descobrir, entender e utilizar os dados do Banco Meridian
                    com mais clareza e confiança.</div>
                <div style="color:#8B949E;font-size:0.78rem;max-width:560px;line-height:1.5;margin-top:6px;">
                    Explore conceitos, dados, responsáveis, regras, qualidade e relacionamentos da organização.</div>
                <div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;">
                    <span style="background:#3FB95022;color:#3FB950;border-radius:20px;
                                 padding:3px 12px;font-size:0.72rem;font-weight:600;
                                 border:1px solid #3FB95044;">✓ Dados Confiáveis</span>
                    <span style="background:#58A6FF22;color:#58A6FF;border-radius:20px;
                                 padding:3px 12px;font-size:0.72rem;font-weight:600;
                                 border:1px solid #58A6FF44;">✓ Responsabilidade Definida</span>
                    <span style="background:#BC8CFF22;color:#BC8CFF;border-radius:20px;
                                 padding:3px 12px;font-size:0.72rem;font-weight:600;
                                 border:1px solid #BC8CFF44;">✓ IA Ready</span>
                </div>
            </div>
            <div style="text-align:right;flex-shrink:0;">
                <div style="color:#8B949E;font-size:0.68rem;">Última atualização</div>
                <div style="color:#E6EDF3;font-size:0.82rem;font-weight:600;">{now_str}</div>
                <div style="background:#3FB95022;color:#3FB950;border-radius:20px;
                            padding:2px 10px;font-size:0.68rem;font-weight:600;
                            border:1px solid #3FB95044;margin-top:4px;
                            display:inline-block;">● AO VIVO</div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    df_meta  = load_meta()
    df_gloss = load_glossario()
    df_links = load_links()
    df_rules = load_rules()

    total_ativos = len(df_meta)  if not df_meta.empty else 0
    total_dom    = df_meta["dominio"].nunique() if not df_meta.empty else 0
    total_termos = len(df_gloss) if not df_gloss.empty else 0
    total_regras = len(df_rules) if not df_rules.empty else 0
    tabs_link    = df_links["table_name"].nunique() if not df_links.empty else 0
    cobertura    = round(tabs_link/max(total_ativos,1)*100)
    cor_cob      = "#3FB950" if cobertura>=70 else "#C9A227" if cobertura>=40 else "#F85149"

    k1,k2,k3,k4,k5 = st.columns(5)
    with k1: st.markdown(kpi(total_termos,"Conceitos de Negócio","#C9A227","📖",
        "Definições oficiais dos principais assuntos utilizados pela organização."), unsafe_allow_html=True)
    with k2: st.markdown(kpi(total_ativos,"Ativos de Dados","#58A6FF","🗂️",
        "Tabelas e outros ativos de dados catalogados na plataforma."), unsafe_allow_html=True)
    with k3: st.markdown(kpi(total_dom,"Domínios de Negócio","#BC8CFF","🏛️",
        "Agrupamentos de dados e assuntos de negócio com responsabilidades definidas."), unsafe_allow_html=True)
    with k4: st.markdown(kpi(total_regras,"Regras de Negócio","#3FB950","📏",
        "Critérios documentados utilizados para definição, cálculo ou validação de informações."), unsafe_allow_html=True)
    with k5: st.markdown(kpi(f"{cobertura}%","Dados Conectados ao Negócio",cor_cob,"🔗",
        f"Percentual de ativos de dados que possuem relacionamento documentado com conceitos de negócio. ({tabs_link} de {total_ativos} ativos vinculados)"), unsafe_allow_html=True)

    section_divider("O QUE VOCÊ ENCONTRA AQUI?")

    cards_info = [
        ("📖","Conceitos de Negócio","Glossário",
         "Definições oficiais dos principais assuntos utilizados pela organização, ajudando diferentes áreas a compartilhar o mesmo entendimento."),
        ("📏","Regras de Negócio","📖 Glossário",
         "Critérios utilizados para definir, calcular, classificar ou validar informações utilizadas nos processos e indicadores."),
        ("🗂️","Ativos de Dados","📋 Catálogo",
         "Dados disponíveis para consulta e utilização, como tabelas, views e outros ativos catalogados na organização."),
        ("🏛️","Domínios de Negócio","🏛️ Domínios",
         "Agrupamentos de assuntos e dados relacionados a uma área de negócio, com responsabilidades claramente definidas."),
        ("🔗","Relacionamentos","📖 Glossário",
         "Mostram como conceitos, regras, indicadores, ativos e produtos de dados estão conectados entre si."),
        ("🛡️","Qualidade dos Dados","🛡️ Scorecard",
         "Mostra o quanto os dados atendem aos critérios de qualidade definidos para sua utilização confiável."),
    ]

    cols_cards = st.columns(3)
    for i, (ic, tit, dest, desc) in enumerate(cards_info):
        with cols_cards[i%3]:
            st.markdown(f"""
            <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;
                        padding:16px;margin-bottom:12px;border-top:3px solid #C9A22744;">
                <div style="font-size:1.3rem;margin-bottom:8px;">{ic}</div>
                <div style="color:#E6EDF3;font-weight:700;font-size:0.9rem;margin-bottom:6px;">{tit}</div>
                <div style="color:#8B949E;font-size:0.75rem;line-height:1.5;">{desc}</div>
            </div>""", unsafe_allow_html=True)
            if st.button(f"Explorar {tit} →", key=f"card_{i}", use_container_width=True):
                st.session_state["pagina"] = dest
                st.rerun()

    section_divider("COMO OS DADOS SE CONECTAM")
    st.markdown("""
    <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;padding:20px 24px;margin-bottom:8px;">
        <div style="color:#8B949E;font-size:0.75rem;margin-bottom:16px;">
            Toda informação utilizada pela organização segue uma jornada — do conceito à decisão.
        </div>
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
            <div style="background:#C9A22722;border:1px solid #C9A22744;border-radius:8px;padding:10px 16px;text-align:center;">
                <div style="font-size:0.6rem;color:#8B949E;margin-bottom:2px;">CONCEITO</div>
                <div style="color:#C9A227;font-weight:700;font-size:0.82rem;">Inadimplência</div>
            </div>
            <div style="color:#C9A227;font-size:1.2rem;">→</div>
            <div style="background:#58A6FF22;border:1px solid #58A6FF44;border-radius:8px;padding:10px 16px;text-align:center;">
                <div style="font-size:0.6rem;color:#8B949E;margin-bottom:2px;">REGRA</div>
                <div style="color:#58A6FF;font-weight:700;font-size:0.82rem;">Janela 90 dias</div>
            </div>
            <div style="color:#C9A227;font-size:1.2rem;">→</div>
            <div style="background:#BC8CFF22;border:1px solid #BC8CFF44;border-radius:8px;padding:10px 16px;text-align:center;">
                <div style="font-size:0.6rem;color:#8B949E;margin-bottom:2px;">ATIVO</div>
                <div style="color:#BC8CFF;font-weight:700;font-size:0.82rem;">fato_inadimplencia</div>
            </div>
            <div style="color:#C9A227;font-size:1.2rem;">→</div>
            <div style="background:#3FB95022;border:1px solid #3FB95044;border-radius:8px;padding:10px 16px;text-align:center;">
                <div style="font-size:0.6rem;color:#8B949E;margin-bottom:2px;">INDICADOR</div>
                <div style="color:#3FB950;font-weight:700;font-size:0.82rem;">Taxa NPL</div>
            </div>
            <div style="color:#C9A227;font-size:1.2rem;">→</div>
            <div style="background:#F8514922;border:1px solid #F8514944;border-radius:8px;padding:10px 16px;text-align:center;">
                <div style="font-size:0.6rem;color:#8B949E;margin-bottom:2px;">DECISÃO</div>
                <div style="color:#F85149;font-weight:700;font-size:0.82rem;">Gestão de Risco</div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# 📖 GLOSSÁRIO — Área de Conhecimento
# ════════════════════════════════════════════════════════════════════
elif pagina == "📖 Glossário":
    page_header("📖","Glossário Corporativo",
                "A linguagem comum da organização — definições, regras e responsáveis.")

    st.markdown("""
    <div style="background:#161B2299;border:1px solid #30363D;border-radius:8px;
                padding:10px 14px;margin-bottom:16px;">
        <div style="color:#8B949E;font-size:0.78rem;line-height:1.6;">
            O Glossário reúne as definições oficiais dos conceitos utilizados pela organização.
            Ele garante que diferentes áreas compartilhem o mesmo entendimento sobre termos,
            indicadores e processos — eliminando interpretações divergentes.
        </div>
    </div>""", unsafe_allow_html=True)

    df_g     = load_glossario()
    df_rules = load_rules()
    df_links = load_links()

    if not df_g.empty:
        m1,m2,m3,m4 = st.columns(4)
        with m1: st.markdown(kpi(len(df_g),"Total de Conceitos","#C9A227","📖",
            "Total de conceitos de negócio cadastrados no glossário."), unsafe_allow_html=True)
        with m2: st.markdown(kpi(len(df_g[df_g["status"]=="homologado"]),"Homologados","#3FB950",tooltip=
            "Conceitos revisados e aprovados formalmente pela governança."), unsafe_allow_html=True)
        with m3: st.markdown(kpi(len(df_g[df_g["status"]=="em_revisao"]),"Em Revisão","#58A6FF",tooltip=
            "Conceitos submetidos e aguardando aprovação."), unsafe_allow_html=True)
        with m4: st.markdown(kpi(len(df_g[df_g["status"]=="rascunho"]),"Rascunho","#8B949E",tooltip=
            "Conceitos em elaboração, ainda não submetidos para revisão."), unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        abas = ["📖 Conceitos de Negócio","📏 Regras de Negócio","🔗 Relacionamentos","🕐 Histórico"]
        if is_curador:
            abas.append("⚙️ Workflow")
        tabs_g = st.tabs(abas)

        # ── CONCEITOS ─────────────────────────────────────────────
        with tabs_g[0]:
            st.markdown('<div style="color:#8B949E;font-size:0.75rem;margin-bottom:12px;">Conceitos utilizados para representar assuntos relevantes para o negócio que possuem uma definição oficial.</div>', unsafe_allow_html=True)
            col_lista, col_det = st.columns([1,2])
            with col_lista:
                busca_g = st.text_input("Buscar conceito", placeholder="🔍 Nome, definição ou domínio...", key="g_busca", label_visibility="collapsed")
                g_dom   = st.selectbox("Domínio",["Todos"]+sorted(df_g["dominio"].unique().tolist()),key="g_dom")
                g_st    = st.selectbox("Status",["Todos","homologado","em_revisao","rascunho"],key="g_st")

                df_gf = df_g.copy()
                if busca_g:
                    df_gf = df_gf[df_gf["termo"].str.contains(busca_g,case=False,na=False)|
                                  df_gf["definicao"].str.contains(busca_g,case=False,na=False)]
                if g_dom != "Todos": df_gf = df_gf[df_gf["dominio"]==g_dom]
                if g_st  != "Todos": df_gf = df_gf[df_gf["status"]==g_st]

                if "gid_sel" not in st.session_state:
                    st.session_state["gid_sel"] = df_gf.iloc[0]["glossary_id"] if not df_gf.empty else None

                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

                if df_gf.empty:
                    estado_vazio("🔍","Nenhum conceito encontrado","Tente outros termos de busca ou ajuste os filtros.")
                else:
                    for _, row in df_gf.iterrows():
                        cor_st = {"homologado":"#3FB950","em_revisao":"#58A6FF","rascunho":"#8B949E"}.get(row["status"],"#8B949E")
                        is_sel = st.session_state["gid_sel"] == row["glossary_id"]
                        st.markdown(f"""
                        <div style="background:{'#C9A22708' if is_sel else '#161B22'};
                                    border:1px solid {'#C9A227' if is_sel else '#30363D'};
                                    border-radius:8px;padding:8px 10px;margin-bottom:2px;">
                            <div style="color:#E6EDF3;font-weight:600;font-size:0.82rem;">{row['termo']}</div>
                            <div style="display:flex;justify-content:space-between;margin-top:2px;">
                                <span style="color:#8B949E;font-size:0.68rem;">{row['dominio']}</span>
                                <span style="color:{cor_st};font-size:0.65rem;font-weight:600;">● {row['status'].replace('_',' ')}</span>
                            </div>
                        </div>""", unsafe_allow_html=True)
                        if st.button(f"↳ {row['termo']}", key=f"gc_{row['glossary_id']}", use_container_width=True):
                            st.session_state["gid_sel"] = row["glossary_id"]
                            st.rerun()

                # Sugestão de novo conceito — para todos os perfis
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                if is_curador:
                    with st.expander("➕ Criar novo conceito"):
                        nn  = st.text_input("Nome do conceito *",key="nn")
                        nd  = st.text_area("Definição *",key="nd",height=70)
                        ns  = st.text_input("Também conhecido como",key="ns")
                        ndo = st.selectbox("Domínio",["Crédito","Pagamentos","Clientes","Compliance","Produtos"],key="ndo")
                        na  = st.text_input("Área",key="na")
                        nc  = st.selectbox("Criticidade",["Crítico","Alto","Médio","Baixo"],key="nc")
                        if st.button("💾 Criar",key="btn_criar"):
                            if nn and nd:
                                gid_new = str(uuid.uuid4())
                                ok,err = exe(f"INSERT INTO meridian_governanca.business_glossary VALUES ('{gid_new}','{esc(nn)}','{esc(nd)}','{esc(ns)}','{esc(ndo)}','{esc(na)}','{esc(nc)}','{esc(usuario)}','{esc(usuario)}','rascunho',1,false,'{esc(usuario)}',current_timestamp(),'{esc(usuario)}',current_timestamp())")
                                if ok: st.success(f"✅ '{nn}' criado!"); st.cache_data.clear(); st.rerun()
                                else: st.error(f"Erro: {err}")
                            else: st.warning("Preencha Nome e Definição.")
                else:
                    with st.expander("💡 Sugerir novo conceito"):
                        st.markdown('<div style="color:#8B949E;font-size:0.75rem;margin-bottom:8px;">Sua sugestão será analisada pela equipe de Governança antes de ser publicada.</div>', unsafe_allow_html=True)
                        sn_nome  = st.text_input("Nome sugerido *", key="sn_nome")
                        sn_def   = st.text_area("Definição *", key="sn_def", height=70)
                        sn_just  = st.text_area("Por que este conceito é importante?", key="sn_just", height=50)
                        sn_area  = st.text_input("Área relacionada", key="sn_area")
                        sn_ex    = st.text_input("Exemplos de uso", key="sn_ex")
                        if st.button("📤 Enviar sugestão", key="btn_sug_conceito"):
                            if sn_nome and sn_def:
                                ok,err = exe(f"INSERT INTO meridian_governanca.sugestoes_conceitos VALUES ('{uuid.uuid4()}','{esc(usuario)}','{esc(sn_nome)}','{esc(sn_def)}','{esc(sn_just)}','{esc(sn_area)}','{esc(sn_ex)}','pendente',null,null,current_timestamp(),current_timestamp())")
                                if ok: st.success("✅ Sugestão enviada! A equipe de Governança irá analisar."); st.rerun()
                                else: st.error(f"Erro: {err}")
                            else: st.warning("Preencha pelo menos o nome e a definição.")

            with col_det:
                gid = st.session_state.get("gid_sel")
                if gid:
                    row_d = df_g[df_g["glossary_id"]==gid]
                    if not row_d.empty:
                        row    = row_d.iloc[0]
                        cor_st = {"homologado":"#3FB950","em_revisao":"#58A6FF","rascunho":"#8B949E"}.get(row["status"],"#8B949E")
                        cor_cr = {"Crítico":"#F85149","Alto":"#FF7B72","Médio":"#C9A227","Baixo":"#3FB950"}.get(str(row.get("criticidade","")),"#8B949E")
                        links_t = df_links[df_links["glossary_id"]==gid] if not df_links.empty else pd.DataFrame()
                        rules_t = df_rules[df_rules["glossary_id"]==gid] if not df_rules.empty else pd.DataFrame()
                        n_tab = links_t["table_name"].nunique() if not links_t.empty else 0
                        n_reg = len(rules_t)

                        st.markdown(f"""
                        <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;padding:20px;">
                            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
                                <div style="color:#E6EDF3;font-size:1.2rem;font-weight:800;">{row['termo']}</div>
                                <span style="background:{cor_st}22;color:{cor_st};border-radius:20px;padding:3px 12px;font-size:0.72rem;font-weight:600;border:1px solid {cor_st}44;">
                                    {'✅ Homologado' if row['status']=='homologado' else '🔵 Em Revisão' if row['status']=='em_revisao' else '📄 Rascunho'}</span>
                            </div>
                            <div style="color:#E6EDF3;font-size:0.85rem;line-height:1.6;margin-bottom:12px;">{row['definicao']}</div>
                            {f'<div style="color:#8B949E;font-size:0.75rem;margin-bottom:10px;">Também conhecido como: <span style="color:#C9A227;">{row["sinonimos"]}</span></div>' if row.get("sinonimos") else ''}
                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px;">
                                <div style="background:#0D1117;border-radius:8px;padding:9px;">
                                    <div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;letter-spacing:1px;">DOMÍNIO</div>
                                    <div style="color:#E6EDF3;font-weight:600;font-size:0.82rem;">{row['dominio']}</div>
                                </div>
                                <div style="background:#0D1117;border-radius:8px;padding:9px;">
                                    <div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;letter-spacing:1px;">CRITICIDADE</div>
                                    <div style="color:{cor_cr};font-weight:600;font-size:0.82rem;">{row.get('criticidade','—')}</div>
                                </div>
                                <div style="background:#0D1117;border-radius:8px;padding:9px;">
                                    <div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;letter-spacing:1px;">RESPONSÁVEL (OWNER)</div>
                                    <div style="color:#E6EDF3;font-size:0.78rem;">{row.get('owner_email','—')}</div>
                                </div>
                                <div style="background:#0D1117;border-radius:8px;padding:9px;">
                                    <div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;letter-spacing:1px;">GESTOR DO DADO (STEWARD)</div>
                                    <div style="color:#E6EDF3;font-size:0.78rem;">{row.get('steward_email','—')}</div>
                                </div>
                            </div>
                            <div style="background:#0D1117;border:1px solid #30363D;border-radius:8px;padding:10px 14px;">
                                <div style="font-size:0.6rem;color:#8B949E;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">ONDE ESTE CONCEITO APARECE</div>
                                <div style="display:flex;gap:20px;">
                                    <div title="Tabelas e ativos que utilizam este conceito"><span style="color:#58A6FF;font-size:1.3rem;font-weight:800;">{n_tab}</span><span style="color:#8B949E;font-size:0.7rem;margin-left:4px;">ativos</span></div>
                                    <div title="Regras de negócio vinculadas a este conceito"><span style="color:#BC8CFF;font-size:1.3rem;font-weight:800;">{n_reg}</span><span style="color:#8B949E;font-size:0.7rem;margin-left:4px;">regras</span></div>
                                    <div title="Domínio de negócio responsável"><span style="color:#C9A227;font-size:1.3rem;font-weight:800;">1</span><span style="color:#8B949E;font-size:0.7rem;margin-left:4px;">domínio</span></div>
                                </div>
                            </div>
                        </div>""", unsafe_allow_html=True)

                        if not rules_t.empty:
                            st.markdown('<div style="color:#E6EDF3;font-weight:700;font-size:0.82rem;margin:12px 0 6px;">📏 Regras vinculadas</div>', unsafe_allow_html=True)
                            for _,r in rules_t.iterrows():
                                st.markdown(f"""
                                <div style="background:#161B22;border:1px solid #30363D;border-radius:6px;padding:8px 12px;margin-bottom:5px;">
                                    <div style="display:flex;justify-content:space-between;">
                                        <span style="color:#E6EDF3;font-size:0.8rem;font-weight:600;">{r['nome_regra']}</span>
                                        <span style="background:#BC8CFF22;color:#BC8CFF;border-radius:4px;padding:1px 6px;font-size:0.65rem;">{r['categoria']}</span>
                                    </div>
                                    <div style="color:#8B949E;font-size:0.73rem;margin-top:2px;">{r['descricao_regra']}</div>
                                </div>""", unsafe_allow_html=True)
                        else:
                            st.markdown('<div style="color:#8B949E;font-size:0.75rem;padding:8px 0;">Nenhuma regra vinculada a este conceito ainda.</div>', unsafe_allow_html=True)

                        if is_curador and row["status"]=="rascunho":
                            if st.button("📤 Submeter para Revisão",key=f"gsub_{gid}",use_container_width=True):
                                ok,_ = exe(f"UPDATE meridian_governanca.business_glossary SET status='em_revisao',atualizado_por='{esc(usuario)}',atualizado_em=current_timestamp() WHERE glossary_id='{gid}'")
                                if ok: st.success("✅ Submetido!"); st.cache_data.clear(); st.rerun()

                        if is_aprovador and row["status"]=="em_revisao":
                            ga,gr = st.columns(2)
                            with ga:
                                if st.button("✅ Aprovar",key=f"gap_{gid}",use_container_width=True):
                                    ok,_ = exe(f"UPDATE meridian_governanca.business_glossary SET status='homologado',atualizado_por='{esc(usuario)}',atualizado_em=current_timestamp() WHERE glossary_id='{gid}'")
                                    if ok: st.success("✅ Homologado!"); st.cache_data.clear(); st.rerun()
                            with gr:
                                if st.button("❌ Rejeitar",key=f"grej_{gid}",use_container_width=True):
                                    ok,_ = exe(f"UPDATE meridian_governanca.business_glossary SET status='rascunho',atualizado_por='{esc(usuario)}',atualizado_em=current_timestamp() WHERE glossary_id='{gid}'")
                                    if ok: st.warning("↩️ Devolvido."); st.cache_data.clear(); st.rerun()
                else:
                    estado_vazio("📖","Selecione um conceito","Clique em qualquer conceito da lista para ver seus detalhes.")

        # ── REGRAS DE NEGÓCIO ─────────────────────────────────────
        with tabs_g[1]:
            st.markdown('<div style="color:#8B949E;font-size:0.75rem;margin-bottom:12px;">Uma regra de negócio define critérios utilizados para calcular, classificar, validar ou determinar uma informação.</div>', unsafe_allow_html=True)
            df_rg,_ = qry("SELECT g.termo, r.nome_regra, r.descricao_regra, r.categoria FROM meridian_governanca.business_rules r JOIN meridian_governanca.business_glossary g ON r.glossary_id=g.glossary_id ORDER BY g.termo, r.categoria")
            if not df_rg.empty:
                for _,r in df_rg.iterrows():
                    st.markdown(f"""
                    <div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:10px 14px;margin-bottom:6px;">
                        <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                            <span style="color:#C9A227;font-size:0.75rem;font-weight:700;">{r['termo']}</span>
                            <span style="background:#BC8CFF22;color:#BC8CFF;border-radius:4px;padding:1px 7px;font-size:0.65rem;">{r['categoria']}</span>
                        </div>
                        <div style="color:#E6EDF3;font-size:0.82rem;font-weight:600;">{r['nome_regra']}</div>
                        <div style="color:#8B949E;font-size:0.73rem;margin-top:2px;">{r['descricao_regra']}</div>
                    </div>""", unsafe_allow_html=True)
            else:
                estado_vazio("📏","Nenhuma regra cadastrada","As regras de negócio serão exibidas aqui quando forem cadastradas.")

            # Sugestão de nova regra — todos os perfis
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if not is_curador:
                with st.expander("💡 Sugerir nova regra de negócio"):
                    st.markdown('<div style="color:#8B949E;font-size:0.75rem;margin-bottom:8px;">Sua sugestão será analisada pela equipe de Governança antes de ser publicada.</div>', unsafe_allow_html=True)
                    sr_nome = st.text_input("Nome da regra *", key="sr_nome")
                    sr_desc = st.text_area("Descrição *", key="sr_desc", height=70)
                    sr_regra = st.text_area("Como deve ser aplicada", key="sr_regra", height=50)
                    sr_just = st.text_area("Por que esta regra é necessária?", key="sr_just", height=50)
                    sr_conc = st.text_input("Conceito relacionado", key="sr_conc")
                    sr_ind  = st.text_input("Indicador relacionado (se aplicável)", key="sr_ind")
                    if st.button("📤 Enviar sugestão de regra", key="btn_sug_regra"):
                        if sr_nome and sr_desc:
                            ok,err = exe(f"INSERT INTO meridian_governanca.sugestoes_regras VALUES ('{uuid.uuid4()}','{esc(usuario)}','{esc(sr_nome)}','{esc(sr_desc)}','{esc(sr_regra)}','{esc(sr_just)}','{esc(sr_conc)}','{esc(sr_ind)}','pendente',null,null,current_timestamp(),current_timestamp())")
                            if ok: st.success("✅ Sugestão enviada!"); st.rerun()
                            else: st.error(f"Erro: {err}")
                        else: st.warning("Preencha pelo menos o nome e a descrição.")

        # ── RELACIONAMENTOS ───────────────────────────────────────
        with tabs_g[2]:
            st.markdown('<div style="color:#8B949E;font-size:0.75rem;margin-bottom:12px;">Mostra como conceitos de negócio estão conectados a ativos de dados técnicos da organização.</div>', unsafe_allow_html=True)
            if not df_links.empty and not df_g.empty:
                termos_dict  = dict(zip(df_g["glossary_id"],df_g["termo"]))
                termos_uniq  = df_links["glossary_id"].unique().tolist()
                tabelas_uniq = df_links["table_name"].unique().tolist()
                t_pos = {g:(0,i*1.5) for i,g in enumerate(termos_uniq)}
                a_pos = {t:(3,i*1.5-(len(tabelas_uniq)-len(termos_uniq))*0.75) for i,t in enumerate(tabelas_uniq)}
                nx,ny,nt,nc,ns = [],[],[],[],[]
                ex,ey = [],[]
                for g,(x,y) in t_pos.items():
                    nx.append(x); ny.append(y); nt.append(termos_dict.get(g,g[:8])); nc.append("#C9A227"); ns.append(20)
                for t,(x,y) in a_pos.items():
                    nx.append(x); ny.append(y); nt.append(t); nc.append("#58A6FF"); ns.append(16)
                for _,l in df_links.iterrows():
                    if l["glossary_id"] in t_pos and l["table_name"] in a_pos:
                        x0,y0=t_pos[l["glossary_id"]]; x1,y1=a_pos[l["table_name"]]
                        ex+=[x0,x1,None]; ey+=[y0,y1,None]
                fig_g = go.Figure()
                fig_g.add_trace(go.Scatter(x=ex,y=ey,mode="lines",line=dict(color="#30363D",width=1.5),hoverinfo="none"))
                fig_g.add_trace(go.Scatter(x=nx,y=ny,mode="markers+text",marker=dict(color=nc,size=ns,line=dict(color="#0D1117",width=2)),text=nt,textposition="middle right",textfont=dict(color="#E6EDF3",size=11),hoverinfo="text"))
                fig_g.update_layout(paper_bgcolor="#161B22",plot_bgcolor="#161B22",showlegend=False,height=420,margin=dict(t=10,b=10,l=10,r=10),xaxis=dict(showgrid=False,zeroline=False,showticklabels=False),yaxis=dict(showgrid=False,zeroline=False,showticklabels=False))
                st.plotly_chart(fig_g,use_container_width=True)
                st.markdown('<div style="display:flex;gap:16px;margin-top:4px;"><div style="display:flex;align-items:center;gap:6px;"><div style="width:10px;height:10px;border-radius:50%;background:#C9A227;"></div><span style="color:#8B949E;font-size:0.72rem;">Conceitos de Negócio</span></div><div style="display:flex;align-items:center;gap:6px;"><div style="width:10px;height:10px;border-radius:50%;background:#58A6FF;"></div><span style="color:#8B949E;font-size:0.72rem;">Ativos Técnicos</span></div></div>', unsafe_allow_html=True)
            else:
                estado_vazio("🔗","Nenhum relacionamento cadastrado","Os vínculos entre conceitos e ativos técnicos serão exibidos aqui.")

        # ── HISTÓRICO ─────────────────────────────────────────────
        with tabs_g[3]:
            df_wf,_ = qry("SELECT g.termo, w.acao, w.status_anterior, w.status_novo, w.aprovador, w.comentario, w.criado_em FROM meridian_governanca.glossary_approval_workflow w JOIN meridian_governanca.business_glossary g ON w.glossary_id=g.glossary_id ORDER BY w.criado_em DESC LIMIT 50")
            if not df_wf.empty:
                for _,r in df_wf.iterrows():
                    ts = str(r["criado_em"])[:16] if r["criado_em"] else "—"
                    st.markdown(f'<div style="background:#161B22;border:1px solid #30363D;border-radius:6px;padding:8px 12px;margin-bottom:5px;display:flex;justify-content:space-between;align-items:center;"><div><span style="color:#C9A227;font-size:0.78rem;font-weight:700;">{r["termo"]}</span><span style="color:#8B949E;font-size:0.72rem;margin-left:8px;">{r["acao"]}</span></div><span style="color:#8B949E;font-size:0.7rem;">{ts}</span></div>', unsafe_allow_html=True)
            else:
                estado_vazio("🕐","Nenhum histórico ainda","As aprovações e alterações de conceitos aparecerão aqui.")

        # ── WORKFLOW (apenas curador/aprovador) ───────────────────
        if is_curador and len(tabs_g)>4:
            with tabs_g[4]:
                wf_cols = st.columns(3)
                for col,(tit,st_wf,cor_wf) in zip(wf_cols,[("📄 Rascunho","rascunho","#8B949E"),("🔵 Em Revisão","em_revisao","#58A6FF"),("✅ Homologado","homologado","#3FB950")]):
                    df_wfc = df_g[df_g["status"]==st_wf]
                    with col:
                        st.markdown(f'<div style="background:#161B22;border:1px solid {cor_wf}44;border-radius:10px;padding:12px;"><div style="color:{cor_wf};font-weight:700;font-size:0.82rem;margin-bottom:8px;">{tit} ({len(df_wfc)})</div>', unsafe_allow_html=True)
                        for _,r in df_wfc.iterrows():
                            st.markdown(f'<div style="background:#0D1117;border:1px solid #30363D;border-radius:6px;padding:7px 9px;margin-bottom:5px;"><div style="color:#E6EDF3;font-size:0.78rem;font-weight:600;">{r["termo"]}</div><div style="color:#8B949E;font-size:0.68rem;">{r["dominio"]}</div></div>', unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# 📋 CATÁLOGO — Marketplace de Dados
# ════════════════════════════════════════════════════════════════════
elif pagina == "📋 Catálogo":
    page_header("📋","Catálogo de Dados","Descubra, compreenda e confie nos dados antes de utilizá-los.")

    st.markdown("""
    <div style="background:#161B2299;border:1px solid #30363D;border-radius:8px;
                padding:10px 14px;margin-bottom:16px;">
        <div style="color:#8B949E;font-size:0.78rem;line-height:1.6;">
            O Catálogo reúne os ativos de dados disponíveis na organização. Cada ativo possui informações
            sobre seu conteúdo, responsáveis, qualidade e relacionamento com conceitos de negócio.
            Use a busca ou os filtros para encontrar o dado que você precisa.
        </div>
    </div>""", unsafe_allow_html=True)

    df_cat = load_meta()
    if not df_cat.empty:
        schemas = df_cat["schema_name"].value_counts()
        k1,k2,k3 = st.columns(3)
        with k1: st.markdown(kpi(len(df_cat),"Ativos Catalogados","#C9A227",tooltip="Total de tabelas e ativos de dados disponíveis no catálogo."), unsafe_allow_html=True)
        with k2: st.markdown(kpi(f"{schemas.get('ouro',0)} · {schemas.get('prata',0)} · {schemas.get('bronze',0)}","Ouro · Prata · Bronze","#58A6FF",tooltip="Distribuição dos ativos por camada de maturidade dos dados."), unsafe_allow_html=True)
        with k3: st.markdown(kpi(df_cat["dominio"].nunique(),"Domínios Representados","#BC8CFF",tooltip="Quantidade de domínios de negócio com ativos catalogados."), unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        busca_c = st.text_input("Buscar no catálogo", placeholder="🔍 Pesquise por conceito, responsável, domínio ou ativo...", key="cat_busca", label_visibility="collapsed")

        f1,f2,f3,f4,f5 = st.columns(5)
        with f1: f_dom = st.selectbox("Domínio",["Todos"]+sorted([d for d in df_cat["dominio"].unique() if d]),key="cf_dom")
        with f2: f_cam = st.selectbox("Camada",["Todas"]+sorted(df_cat["schema_name"].unique().tolist()),key="cf_cam")
        with f3: f_own = st.selectbox("Responsável",["Todos"]+sorted([o for o in df_cat["data_owner"].unique() if o]),key="cf_own")
        with f4: f_stw = st.selectbox("Gestor",["Todos"]+sorted([s for s in df_cat["data_steward"].unique() if s]),key="cf_stw")
        with f5: f_doc = st.selectbox("Documentação",["Todas","Documentadas","Sem documentação"],key="cf_doc")

        df_f = df_cat.copy()
        if busca_c:
            mask = (df_f["table_name"].str.contains(busca_c,case=False,na=False)|df_f["descricao"].str.contains(busca_c,case=False,na=False)|df_f["dominio"].str.contains(busca_c,case=False,na=False)|df_f["data_owner"].str.contains(busca_c,case=False,na=False))
            df_f = df_f[mask]
        if f_dom != "Todos": df_f = df_f[df_f["dominio"]==f_dom]
        if f_cam != "Todas": df_f = df_f[df_f["schema_name"]==f_cam]
        if f_own != "Todos": df_f = df_f[df_f["data_owner"]==f_own]
        if f_stw != "Todos": df_f = df_f[df_f["data_steward"]==f_stw]
        if f_doc == "Documentadas":     df_f = df_f[df_f["descricao"].apply(bool)]
        if f_doc == "Sem documentação": df_f = df_f[~df_f["descricao"].apply(bool)]

        if df_f.empty:
            estado_vazio("🔍","Nenhum ativo encontrado","Tente outros termos ou ajuste os filtros acima.")
        else:
            st.markdown(f'<div style="color:#8B949E;font-size:0.75rem;margin:8px 0;">{len(df_f)} ativo(s) encontrado(s)</div>', unsafe_allow_html=True)

            if "cat_sel" not in st.session_state:
                st.session_state["cat_sel"] = None

            rows_c = [df_f.iloc[i:i+3].reset_index(drop=True) for i in range(0,len(df_f),3)]
            for row_df in rows_c:
                cols_c = st.columns(3)
                for i,(_,item) in enumerate(row_df.iterrows()):
                    cor_c  = "#3FB950" if item["score_completude"]==100 else "#C9A227" if item["score_completude"]>=60 else "#F85149"
                    desc   = item["descricao"][:80]+"..." if item["descricao"] and len(item["descricao"])>80 else item["descricao"] or "Sem descrição cadastrada."
                    chave  = f"{item['schema_name']}.{item['table_name']}"
                    is_sel = st.session_state["cat_sel"] == chave
                    with cols_c[i]:
                        st.markdown(f"""
                        <div style="background:{'#C9A22708' if is_sel else '#161B22'};
                                    border:1px solid {'#C9A227' if is_sel else '#30363D'};
                                    border-radius:10px;padding:14px;margin-bottom:2px;
                                    cursor:pointer;">
                            <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                                <span style="color:#C9A227;font-weight:700;font-size:0.83rem;">{item['table_name']}</span>
                                <span style="color:{cor_c};font-weight:800;font-size:0.88rem;" title="Score de documentação: {item['score_completude']}% dos metadados obrigatórios preenchidos.">{item['score_completude']}%</span>
                            </div>
                            <div style="color:#8B949E;font-size:0.73rem;line-height:1.4;margin-bottom:8px;">{desc}</div>
                            <div style="display:flex;gap:4px;flex-wrap:wrap;">
                                <span style="background:#58A6FF22;color:#58A6FF;border-radius:4px;padding:2px 7px;font-size:0.67rem;" title="Camada de dados">{item['schema_name']}</span>
                                {f'<span style="background:#C9A22722;color:#C9A227;border-radius:4px;padding:2px 7px;font-size:0.67rem;" title="Domínio de negócio">{item["dominio"]}</span>' if item['dominio'] else ''}
                                {f'<span style="background:#F8514922;color:#F85149;border-radius:4px;padding:2px 7px;font-size:0.67rem;">🔒 PII</span>' if item['tem_pii'] else ''}
                            </div>
                        </div>""", unsafe_allow_html=True)
                        if st.button(f"{'▼ Fechar' if is_sel else '▶ Ver detalhes'}",
                                     key=f"csel_{chave}", use_container_width=True):
                            st.session_state["cat_sel"] = None if is_sel else chave
                            st.rerun()

            if st.session_state.get("cat_sel"):
                chave = st.session_state["cat_sel"]
                sc,tb = chave.split(".",1)
                row_c = df_cat[(df_cat["schema_name"]==sc)&(df_cat["table_name"]==tb)]
                if not row_c.empty:
                    item  = row_c.iloc[0]
                    cor_c2= "#3FB950" if item["score_completude"]==100 else "#C9A227" if item["score_completude"]>=60 else "#F85149"
                    df_links_ativo = load_links()
                    termos_ativo = df_links_ativo[df_links_ativo["table_name"]==tb] if not df_links_ativo.empty else pd.DataFrame()
                    df_g_full = load_glossario()

                    st.markdown(f"""
                    <div style="background:#161B22;border:1px solid {cor_c2}44;border-radius:12px;padding:18px;margin-top:8px;">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
                            <div style="color:#E6EDF3;font-size:1.05rem;font-weight:800;">{item['table_name']}</div>
                            <div style="text-align:right;">
                                <div style="color:{cor_c2};font-size:1.5rem;font-weight:800;" title="Score de documentação: percentual de metadados obrigatórios preenchidos">{item['score_completude']}%</div>
                                <div style="color:#8B949E;font-size:0.62rem;">documentação</div>
                            </div>
                        </div>
                        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px;">
                            <div style="background:#0D1117;border-radius:8px;padding:8px;">
                                <div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;margin-bottom:2px;">O QUE É</div>
                                <div style="color:#E6EDF3;font-size:0.78rem;">{item['descricao'] or '—'}</div>
                            </div>
                            <div style="background:#0D1117;border-radius:8px;padding:8px;">
                                <div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;margin-bottom:2px;">DOMÍNIO</div>
                                <div style="color:#E6EDF3;font-size:0.78rem;">{item['dominio'] or '—'}</div>
                            </div>
                            <div style="background:#0D1117;border-radius:8px;padding:8px;">
                                <div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;margin-bottom:2px;">RESPONSÁVEL (OWNER)</div>
                                <div style="color:#E6EDF3;font-size:0.78rem;">{item['data_owner'] or '—'}</div>
                            </div>
                            <div style="background:#0D1117;border-radius:8px;padding:8px;">
                                <div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;margin-bottom:2px;">GESTOR DO DADO (STEWARD)</div>
                                <div style="color:#E6EDF3;font-size:0.78rem;">{item['data_steward'] or '—'}</div>
                            </div>
                            <div style="background:#0D1117;border-radius:8px;padding:8px;">
                                <div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;margin-bottom:2px;">FUNÇÃO</div>
                                <div style="color:#E6EDF3;font-size:0.78rem;">{item['funcao_negocio'] or '—'}</div>
                            </div>
                            <div style="background:#0D1117;border-radius:8px;padding:8px;">
                                <div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;margin-bottom:2px;">DADO PESSOAL (PII)</div>
                                <div style="color:#F85149;font-size:0.78rem;">{'🔒 Contém dado pessoal' if item['tem_pii'] else '—'}</div>
                            </div>
                        </div>""", unsafe_allow_html=True)

                    if not termos_ativo.empty and not df_g_full.empty:
                        st.markdown('<div style="background:#0D1117;border-radius:8px;padding:10px 14px;margin-bottom:2px;"><div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;margin-bottom:6px;">CONCEITOS DE NEGÓCIO VINCULADOS</div>', unsafe_allow_html=True)
                        for _,lk in termos_ativo.iterrows():
                            t_row = df_g_full[df_g_full["glossary_id"]==lk["glossary_id"]]
                            if not t_row.empty:
                                t = t_row.iloc[0]
                                st.markdown(f'<span style="background:#C9A22722;color:#C9A227;border-radius:4px;padding:2px 9px;font-size:0.72rem;margin-right:4px;">{t["termo"]}</span>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown('</div>', unsafe_allow_html=True)

                    # Solicitação de acesso — para consultantes
                    if perfil == "consultante":
                        with st.expander("🔑 Solicitar acesso a este ativo"):
                            sa_just = st.text_area("Por que você precisa deste dado?", key="sa_just", height=70)
                            sa_tipo = st.selectbox("Tipo de acesso", ["Leitura","Leitura e Escrita"], key="sa_tipo")
                            if st.button("📤 Enviar solicitação de acesso", key="btn_sol_acesso"):
                                if sa_just:
                                    ok,err = exe(f"INSERT INTO meridian_governanca.solicitacoes_acesso VALUES ('{uuid.uuid4()}','{esc(usuario)}','{esc(tb)}','{esc(sc)}','{esc(sa_just)}','{esc(sa_tipo)}','pendente',null,null,current_timestamp(),current_timestamp())")
                                    if ok: st.success("✅ Solicitação enviada! O responsável será notificado.")
                                    else: st.error(f"Erro: {err}")
                                else: st.warning("Informe o motivo da solicitação.")

                    # Editar na Curadoria — apenas para curador/aprovador
                    if is_curador:
                        if st.button("✏️ Editar metadados na Curadoria", key="btn_ir_curadoria"):
                            st.session_state["pagina"] = "✏️ Curadoria"
                            st.rerun()

    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# 🏛️ DOMÍNIOS
# ════════════════════════════════════════════════════════════════════
elif pagina == "🏛️ Domínios":
    page_header("🏛️","Domínios de Negócio","Áreas de negócio responsáveis pela gestão e uso dos dados.")

    st.markdown("""
    <div style="background:#161B2299;border:1px solid #30363D;border-radius:8px;
                padding:10px 14px;margin-bottom:16px;">
        <div style="color:#8B949E;font-size:0.78rem;line-height:1.6;">
            Domínios organizam os dados e assuntos relacionados ao negócio, ajudando a definir
            responsabilidades sobre as informações. Cada domínio possui um
            <span style="color:#C9A227;">Data Owner</span> responsável pelas decisões estratégicas e
            um ou mais <span style="color:#58A6FF;">Data Stewards</span> responsáveis pela gestão operacional dos dados.
        </div>
    </div>""", unsafe_allow_html=True)

    df_dom  = load_meta()
    df_glos = load_glossario()

    if not df_dom.empty:
        dominios = sorted([d for d in df_dom["dominio"].unique() if d])
        k1,k2,k3,k4,k5 = st.columns(5)
        with k1: st.markdown(kpi(len(dominios),"Domínios Ativos","#C9A227",tooltip="Total de domínios de negócio com dados catalogados."), unsafe_allow_html=True)
        with k2: st.markdown(kpi(df_dom["data_owner"].nunique(),"Responsáveis (Owner)","#58A6FF",tooltip="Pessoas responsáveis pelas decisões relacionadas aos dados de cada domínio."), unsafe_allow_html=True)
        with k3: st.markdown(kpi(df_dom["data_steward"].nunique(),"Gestores (Steward)","#BC8CFF",tooltip="Pessoas que atuam na manutenção, qualidade e evolução dos dados de cada domínio."), unsafe_allow_html=True)
        with k4: st.markdown(kpi(len(df_glos) if not df_glos.empty else 0,"Conceitos Vinculados","#3FB950",tooltip="Total de conceitos de negócio relacionados a domínios."), unsafe_allow_html=True)
        with k5:
            cob = round(len(df_glos[df_glos["status"]=="homologado"])/max(len(df_glos),1)*100) if not df_glos.empty else 0
            st.markdown(kpi(f"{cob}%","Conceitos Homologados","#C9A227",tooltip="Percentual de conceitos que passaram pelo processo formal de aprovação."), unsafe_allow_html=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        icones_dom = {"Crédito":"💳","Pagamentos":"💸","Clientes":"👥","Compliance":"🛡️","Produtos":"📦"}

        if "dom_sel" not in st.session_state:
            st.session_state["dom_sel"] = None

        col_cards, col_det_dom = st.columns([1,2])

        with col_cards:
            for dom in dominios:
                df_d  = df_dom[df_dom["dominio"]==dom]
                score = df_d["score_completude"].mean()
                n_t   = len(df_glos[df_glos["dominio"]==dom]) if not df_glos.empty else 0
                cor_d = "#3FB950" if score>=80 else "#C9A227" if score>=60 else "#F85149"
                ic    = icones_dom.get(dom,"🏛️")
                is_sel = st.session_state["dom_sel"] == dom

                st.markdown(f"""
                <div style="background:{'#C9A22708' if is_sel else '#161B22'};
                            border:1px solid {'#C9A227' if is_sel else '#30363D'};
                            border-radius:10px;padding:12px 14px;margin-bottom:2px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div style="display:flex;align-items:center;gap:8px;">
                            <span style="font-size:1.1rem;">{ic}</span>
                            <span style="color:#E6EDF3;font-weight:700;font-size:0.88rem;">{dom}</span>
                        </div>
                        <span style="color:{cor_d};font-weight:800;font-size:1rem;" title="Score médio de documentação dos ativos deste domínio">{score:.0f}%</span>
                    </div>
                    <div style="background:#30363D;border-radius:4px;height:3px;margin:8px 0 6px;">
                        <div style="background:{cor_d};border-radius:4px;height:3px;width:{min(score,100):.0f}%;"></div>
                    </div>
                    <div style="font-size:0.68rem;color:#8B949E;">{len(df_d)} ativos · {n_t} conceitos</div>
                </div>""", unsafe_allow_html=True)

                if st.button(f"{'▼ Fechar' if is_sel else '▶ Ver detalhes'}",
                             key=f"domsel_{dom}", use_container_width=True):
                    st.session_state["dom_sel"] = None if is_sel else dom
                    st.rerun()

        with col_det_dom:
            dom_sel = st.session_state.get("dom_sel")
            if dom_sel:
                df_d     = df_dom[df_dom["dominio"]==dom_sel]
                score    = df_d["score_completude"].mean()
                owners_d = [o for o in df_d["data_owner"].unique() if o]
                stw_d    = [s for s in df_d["data_steward"].unique() if s]
                n_t      = len(df_glos[df_glos["dominio"]==dom_sel]) if not df_glos.empty else 0
                cor_d    = "#3FB950" if score>=80 else "#C9A227" if score>=60 else "#F85149"
                ic       = icones_dom.get(dom_sel,"🏛️")

                st.markdown(f"""
                <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;padding:16px;margin-bottom:10px;">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
                        <div style="display:flex;align-items:center;gap:8px;">
                            <span style="font-size:1.6rem;">{ic}</span>
                            <div>
                                <div style="color:#E6EDF3;font-size:1rem;font-weight:800;">{dom_sel}</div>
                                <div style="color:#8B949E;font-size:0.72rem;">Domínio de dados · Banco Meridian</div>
                            </div>
                        </div>
                        <div style="text-align:right;">
                            <div style="color:{cor_d};font-size:2rem;font-weight:800;" title="Score médio de documentação dos ativos">{score:.0f}%</div>
                            <div style="color:#8B949E;font-size:0.65rem;">documentação média</div>
                        </div>
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:6px;">
                        <div style="background:#0D1117;border-radius:6px;padding:8px;text-align:center;">
                            <div style="color:#C9A227;font-size:1.3rem;font-weight:800;">{len(df_d)}</div>
                            <div style="color:#8B949E;font-size:0.62rem;">Ativos</div>
                        </div>
                        <div style="background:#0D1117;border-radius:6px;padding:8px;text-align:center;">
                            <div style="color:#58A6FF;font-size:1.3rem;font-weight:800;">{len(owners_d)}</div>
                            <div style="color:#8B949E;font-size:0.62rem;" title="Responsável pelas decisões">Owners</div>
                        </div>
                        <div style="background:#0D1117;border-radius:6px;padding:8px;text-align:center;">
                            <div style="color:#BC8CFF;font-size:1.3rem;font-weight:800;">{len(stw_d)}</div>
                            <div style="color:#8B949E;font-size:0.62rem;" title="Responsável pela gestão operacional">Stewards</div>
                        </div>
                        <div style="background:#0D1117;border-radius:6px;padding:8px;text-align:center;">
                            <div style="color:#3FB950;font-size:1.3rem;font-weight:800;">{n_t}</div>
                            <div style="color:#8B949E;font-size:0.62rem;">Conceitos</div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)

                dd1,dd2 = st.columns(2)
                with dd1:
                    st.markdown('<div style="background:#161B22;border:1px solid #30363D;border-radius:10px;padding:12px;margin-bottom:8px;">', unsafe_allow_html=True)
                    st.markdown('<div style="color:#8B949E;font-size:0.6rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">RESPONSÁVEL PELO DADO (DATA OWNER)</div>', unsafe_allow_html=True)
                    st.markdown('<div style="color:#484F58;font-size:0.65rem;margin-bottom:8px;">Responsável pelas decisões estratégicas sobre os dados do domínio.</div>', unsafe_allow_html=True)
                    for owner in owners_d:
                        nome_fmt = owner.replace("@meridian.com","").replace("."," ").title()
                        st.markdown(f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #21262D;">{avatar(nome_fmt,"#C9A227",32)}<div><div style="color:#E6EDF3;font-size:0.78rem;font-weight:600;">{nome_fmt}</div><div style="color:#8B949E;font-size:0.65rem;">Responsável · {dom_sel}</div></div></div>', unsafe_allow_html=True)
                    if not owners_d:
                        st.markdown('<div style="color:#8B949E;font-size:0.75rem;">Nenhum responsável definido ainda.</div>', unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                    st.markdown('<div style="background:#161B22;border:1px solid #30363D;border-radius:10px;padding:12px;">', unsafe_allow_html=True)
                    st.markdown('<div style="color:#8B949E;font-size:0.6rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">📋 ATIVOS DO DOMÍNIO</div>', unsafe_allow_html=True)
                    for _,row_t in df_d.iterrows():
                        cor_t = "#3FB950" if row_t["score_completude"]==100 else "#C9A227" if row_t["score_completude"]>=60 else "#F85149"
                        st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid #21262D;"><div><span style="color:#C9A227;font-size:0.75rem;font-weight:600;">{row_t["table_name"]}</span><span style="background:#58A6FF22;color:#58A6FF;border-radius:3px;padding:1px 5px;font-size:0.62rem;margin-left:5px;">{row_t["schema_name"]}</span></div><span style="color:{cor_t};font-weight:700;font-size:0.78rem;" title="Score de documentação">{row_t["score_completude"]}%</span></div>', unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                with dd2:
                    st.markdown('<div style="background:#161B22;border:1px solid #30363D;border-radius:10px;padding:12px;margin-bottom:8px;">', unsafe_allow_html=True)
                    st.markdown('<div style="color:#8B949E;font-size:0.6rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">GESTOR DO DADO (DATA STEWARD)</div>', unsafe_allow_html=True)
                    st.markdown('<div style="color:#484F58;font-size:0.65rem;margin-bottom:8px;">Responsável pela manutenção, qualidade e evolução dos dados do domínio.</div>', unsafe_allow_html=True)
                    for stw in stw_d:
                        nome_stw = stw.replace("@meridian.com","").replace("."," ").title()
                        st.markdown(f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #21262D;">{avatar(nome_stw,"#58A6FF",32)}<div><div style="color:#E6EDF3;font-size:0.78rem;font-weight:600;">{nome_stw}</div><div style="color:#8B949E;font-size:0.65rem;">Gestor · {dom_sel}</div></div></div>', unsafe_allow_html=True)
                    if not stw_d:
                        st.markdown('<div style="color:#8B949E;font-size:0.75rem;">Nenhum gestor definido ainda.</div>', unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                    if not df_glos.empty:
                        termos_dom = df_glos[df_glos["dominio"]==dom_sel]
                        if not termos_dom.empty:
                            st.markdown('<div style="background:#161B22;border:1px solid #30363D;border-radius:10px;padding:12px;">', unsafe_allow_html=True)
                            st.markdown('<div style="color:#8B949E;font-size:0.6rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">📖 CONCEITOS DO DOMÍNIO</div>', unsafe_allow_html=True)
                            for _,t in termos_dom.iterrows():
                                cor_ts = {"homologado":"#3FB950","em_revisao":"#58A6FF","rascunho":"#8B949E"}.get(t["status"],"#8B949E")
                                st.markdown(f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #21262D;"><span style="color:#E6EDF3;font-size:0.75rem;">{t["termo"]}</span><span style="color:{cor_ts};font-size:0.68rem;">● {t["status"].replace("_"," ")}</span></div>', unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)
            else:
                estado_vazio("🏛️","Selecione um domínio","Clique em um domínio para ver responsáveis, ativos e conceitos vinculados.")

    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# 🛡️ SCORECARD — Confiabilidade dos Dados
# ════════════════════════════════════════════════════════════════════
elif pagina == "🛡️ Scorecard":
    page_header("🛡️","Scorecard de Confiabilidade",
                "O quanto os dados estão documentados, sob responsabilidade e avaliados segundo os critérios da organização.")

    st.markdown("""
    <div style="background:#161B2299;border:1px solid #30363D;border-radius:8px;
                padding:10px 14px;margin-bottom:16px;">
        <div style="color:#8B949E;font-size:0.78rem;line-height:1.6;">
            O Scorecard avalia a maturidade dos dados em cinco dimensões independentes.
            Cada indicador possui um conceito e uma forma de melhoria explicados ao clicar no pilar.
            <strong style="color:#C9A227;">Nenhum número aparece sem definição.</strong>
        </div>
    </div>""", unsafe_allow_html=True)

    df_sc    = load_meta()
    df_links = load_links()

    if df_sc.empty:
        estado_vazio("📊","Não foi possível carregar os dados","Tente recarregar a página. Se o problema persistir, contate a equipe de Governança.")
    else:
        dominios_sc = ["Todos"]+sorted([d for d in df_sc["dominio"].unique() if d])
        f_dom_sc = st.selectbox("Filtrar por Domínio", dominios_sc, key="sc_dom")
        df_sc_f  = df_sc if f_dom_sc=="Todos" else df_sc[df_sc["dominio"]==f_dom_sc]

        doc  = df_sc_f["descricao"].apply(bool).mean()*100
        own  = df_sc_f["data_owner"].apply(bool).mean()*100
        rel  = (df_sc_f["table_name"].isin(df_links["table_name"]).sum()/max(len(df_sc_f),1))*100 if not df_links.empty else 0
        qual = df_sc_f["score_completude"].mean()
        cert = (len(df_sc_f[df_sc_f["selo"]=="certificado"])/max(len(df_sc_f),1))*100
        ger  = (doc+own+rel+qual+cert)/5
        cor_g = "#3FB950" if ger>=80 else "#C9A227" if ger>=60 else "#F85149"

        st.markdown(f"""
        <div style="background:#161B22;border:1px solid #30363D;border-radius:16px;
                    padding:20px;text-align:center;margin-bottom:20px;">
            <div style="font-size:0.7rem;color:#8B949E;text-transform:uppercase;letter-spacing:2px;margin-bottom:4px;">
                Score Geral de Confiabilidade</div>
            <div style="font-size:3.5rem;font-weight:800;color:{cor_g};line-height:1;">{ger:.0f}%</div>
            <div style="color:#8B949E;font-size:0.75rem;margin-top:4px;">
                Média dos 5 pilares: Documentação · Responsabilidade · Relacionamentos · Qualidade · Certificação</div>
        </div>""", unsafe_allow_html=True)

        PILARES_INFO = {
            "Documentação":  {
                "icone":"📝","cor":"#58A6FF","val":doc,
                "conceito":"Mede se os ativos possuem descrição de negócio preenchida. Uma boa documentação permite que qualquer usuário entenda o propósito do dado sem precisar consultar o time técnico.",
                "como_melhorar":"Acesse Curadoria → Tabela Individual e preencha a descrição de cada ativo. O botão 'Sugerir com IA' acelera esse processo."
            },
            "Responsabilidade": {
                "icone":"👤","cor":"#C9A227","val":own,
                "conceito":"Avalia se cada ativo possui um Responsável pelo Dado (Data Owner) formalmente definido. O Owner responde pelas decisões sobre qualidade e uso correto do dado.",
                "como_melhorar":"Acesse Curadoria → Tabela Individual ou Edição em Lote e atribua um Responsável para os ativos sem dono definido."
            },
            "Relacionamentos":{
                "icone":"🔗","cor":"#BC8CFF","val":rel,
                "conceito":"Verifica se os ativos técnicos estão conectados a conceitos de negócio do Glossário. Ativos conectados são mais fáceis de descobrir e entender pelas áreas de negócio.",
                "como_melhorar":"Acesse o Glossário → Relacionamentos e vincule cada conceito às tabelas correspondentes."
            },
            "Qualidade":     {
                "icone":"⭐","cor":"#3FB950","val":qual,
                "conceito":"Score médio de completude dos metadados (0 a 100%). Calculado com base nos campos obrigatórios: Descrição, Domínio, Responsável, Gestor e Função de Negócio. Cada campo representa 20% do score.",
                "como_melhorar":"Preencha todos os campos obrigatórios na Curadoria. Cada campo preenchido adiciona 20 pontos ao score do ativo."
            },
            "Certificação":  {
                "icone":"🏆","cor":"#F85149","val":cert,
                "conceito":"Percentual de ativos com score 100% — todos os campos obrigatórios preenchidos. Ativos certificados estão prontos para uso confiável pelo negócio.",
                "como_melhorar":"Complete todos os 5 campos de metadados para que o ativo receba automaticamente o status de Certificado."
            },
        }

        if "sc_pilar" not in st.session_state:
            st.session_state["sc_pilar"] = None

        cols_p = st.columns(5)
        for col,(nome,info) in zip(cols_p,PILARES_INFO.items()):
            cor_p  = "#3FB950" if info["val"]>=80 else "#C9A227" if info["val"]>=60 else "#F85149"
            is_sel = st.session_state["sc_pilar"] == nome
            with col:
                st.markdown(f"""
                <div style="background:{'#C9A22708' if is_sel else '#161B22'};
                            border:1px solid {'#C9A227' if is_sel else '#30363D'};
                            border-radius:12px;padding:16px;text-align:center;margin-bottom:2px;">
                    <div style="font-size:1.3rem;margin-bottom:5px;">{info['icone']}</div>
                    <div style="font-size:1.8rem;font-weight:800;color:{cor_p};">{info['val']:.0f}%</div>
                    <div style="color:#8B949E;font-size:0.72rem;margin-bottom:8px;">{nome}</div>
                    <div style="background:#30363D;border-radius:4px;height:4px;">
                        <div style="background:{cor_p};border-radius:4px;height:4px;width:{min(info['val'],100):.0f}%;"></div>
                    </div>
                </div>""", unsafe_allow_html=True)
                if st.button(f"{'▼ Fechar' if is_sel else '▶ Entender'}",
                             key=f"scp_{nome}", use_container_width=True):
                    st.session_state["sc_pilar"] = None if is_sel else nome
                    st.rerun()

        pilar_sel = st.session_state.get("sc_pilar")
        if pilar_sel and pilar_sel in PILARES_INFO:
            info  = PILARES_INFO[pilar_sel]
            cor_p2 = "#3FB950" if info["val"]>=80 else "#C9A227" if info["val"]>=60 else "#F85149"
            st.markdown(f"""
            <div style="background:#161B22;border:1px solid {cor_p2}44;border-radius:12px;padding:18px;margin:8px 0 16px;">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
                    <span style="font-size:1.5rem;">{info['icone']}</span>
                    <div>
                        <div style="color:#E6EDF3;font-size:1rem;font-weight:800;">{pilar_sel}</div>
                        <div style="color:{cor_p2};font-size:1.3rem;font-weight:800;">{info['val']:.0f}%</div>
                    </div>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                    <div style="background:#0D1117;border-radius:8px;padding:12px;">
                        <div style="color:#8B949E;font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">💡 O QUE SIGNIFICA</div>
                        <div style="color:#E6EDF3;font-size:0.8rem;line-height:1.5;">{info['conceito']}</div>
                    </div>
                    <div style="background:#0D1117;border-radius:8px;padding:12px;">
                        <div style="color:#8B949E;font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">🚀 COMO MELHORAR</div>
                        <div style="color:#E6EDF3;font-size:0.8rem;line-height:1.5;">{info['como_melhorar']}</div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

            if pilar_sel == "Documentação":
                df_pilar = df_sc_f.sort_values("descricao",ascending=True,key=lambda x: x.apply(bool))
                label_col = "descricao"
            elif pilar_sel == "Responsabilidade":
                df_pilar = df_sc_f.sort_values("data_owner",ascending=True,key=lambda x: x.apply(bool))
                label_col = "data_owner"
            else:
                df_pilar = df_sc_f.sort_values("score_completude",ascending=False)
                label_col = "score_completude"

            st.markdown(f'<div style="color:#E6EDF3;font-weight:700;font-size:0.82rem;margin-bottom:8px;">📋 Ativos — {pilar_sel}</div>', unsafe_allow_html=True)
            for _,row_p in df_pilar.head(10).iterrows():
                val_campo = row_p.get(label_col,"")
                tem = bool(val_campo)
                cor_t = "#3FB950" if tem else "#F85149"
                display = str(val_campo)[:30] if tem and label_col != "score_completude" else f"{val_campo}%" if label_col == "score_completude" else "—"
                st.markdown(f"""
                <div style="background:#161B22;border:1px solid #30363D;border-radius:6px;
                            padding:7px 12px;margin-bottom:4px;
                            display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="color:#C9A227;font-size:0.78rem;font-weight:600;">{row_p['table_name']}</span>
                        <span style="background:#58A6FF22;color:#58A6FF;border-radius:3px;padding:1px 5px;font-size:0.62rem;margin-left:5px;">{row_p['schema_name']}</span>
                    </div>
                    <span style="color:{cor_t};font-size:0.75rem;font-weight:600;">
                        {'✅ ' if tem else '❌ '}{display}
                    </span>
                </div>""", unsafe_allow_html=True)

        section_divider("RANKING POR DOMÍNIO")
        dom_sc = df_sc_f[df_sc_f["dominio"].apply(bool)]\
                    .groupby("dominio")["score_completude"].mean()\
                    .reset_index().sort_values("score_completude",ascending=False)\
                    .reset_index(drop=True)
        if dom_sc.empty:
            estado_vazio("📊","Nenhum dado disponível","Atribua domínios aos ativos na Curadoria para ver o ranking.")
        else:
            for i,(_,row) in enumerate(dom_sc.iterrows()):
                cor_o   = "#3FB950" if row["score_completude"]>=80 else "#C9A227" if row["score_completude"]>=60 else "#F85149"
                medalha = ["🥇","🥈","🥉"][i] if i<3 else f"#{i+1}"
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                            background:#161B22;border:1px solid #30363D;border-radius:8px;
                            padding:10px 14px;margin-bottom:5px;">
                    <div style="display:flex;align-items:center;gap:10px;">
                        <span style="font-size:1.1rem;width:28px;text-align:center;">{medalha}</span>
                        <span style="color:#E6EDF3;font-size:0.85rem;font-weight:600;">{row['dominio']}</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div style="background:#30363D;border-radius:4px;height:6px;width:120px;">
                            <div style="background:{cor_o};border-radius:4px;height:6px;width:{min(row['score_completude'],100):.0f}%;"></div>
                        </div>
                        <span style="color:{cor_o};font-weight:800;font-size:0.88rem;width:40px;text-align:right;">{row['score_completude']:.0f}%</span>
                    </div>
                </div>""", unsafe_allow_html=True)

    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# ⚡ MEU ESPAÇO — Área operacional por perfil
# ════════════════════════════════════════════════════════════════════
elif pagina == "⚡ Meu Espaço":
    page_header("⚡",f"Olá, {u['nome']} 👋","Suas pendências, responsabilidades e solicitações.")

    df_meta  = load_meta()
    df_gloss = load_glossario()

    # ── CONSULTANTE ───────────────────────────────────────────────
    if perfil == "consultante":
        df_sol_ac  = load_solicitacoes_acesso()
        df_sol_qu  = load_solicitacoes_qualidade()
        df_sug_co  = load_sugestoes_conceitos()
        df_sug_re  = load_sugestoes_regras()

        meus_acess = df_sol_ac[df_sol_ac["solicitante"]==usuario] if not df_sol_ac.empty else pd.DataFrame()
        meus_qual  = df_sol_qu[df_sol_qu["solicitante"]==usuario] if not df_sol_qu.empty else pd.DataFrame()
        meus_conc  = df_sug_co[df_sug_co["solicitante"]==usuario] if not df_sug_co.empty else pd.DataFrame()
        meus_reg   = df_sug_re[df_sug_re["solicitante"]==usuario] if not df_sug_re.empty else pd.DataFrame()

        k1,k2,k3,k4 = st.columns(4)
        with k1: st.markdown(kpi(len(meus_acess),"Solicitações de Acesso","#58A6FF",tooltip="Suas solicitações de acesso a ativos de dados."), unsafe_allow_html=True)
        with k2: st.markdown(kpi(len(meus_qual),"Solicitações de Qualidade","#BC8CFF",tooltip="Seus reportes de problemas de qualidade."), unsafe_allow_html=True)
        with k3: st.markdown(kpi(len(meus_conc),"Sugestões de Conceitos","#C9A227",tooltip="Conceitos que você sugeriu ao glossário."), unsafe_allow_html=True)
        with k4: st.markdown(kpi(len(meus_reg),"Sugestões de Regras","#3FB950",tooltip="Regras de negócio que você sugeriu."), unsafe_allow_html=True)

        section_divider("MINHAS SOLICITAÇÕES DE ACESSO")
        if meus_acess.empty:
            estado_vazio("🔑","Nenhuma solicitação de acesso","Quando você solicitar acesso a um ativo no Catálogo, ela aparecerá aqui.")
        else:
            for _,r in meus_acess.iterrows():
                cor_s = {"pendente":"#C9A227","aprovado":"#3FB950","rejeitado":"#F85149"}.get(r["status"],"#8B949E")
                st.markdown(f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:10px 14px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;"><div><span style="color:#C9A227;font-weight:700;font-size:0.82rem;">{r["ativo_solicitado"]}</span><span style="color:#8B949E;font-size:0.72rem;margin-left:8px;">{r["tipo_acesso"]}</span></div><span style="color:{cor_s};font-size:0.72rem;font-weight:600;">● {r["status"]}</span></div>', unsafe_allow_html=True)

        section_divider("MINHAS SUGESTÕES")
        tab_conc, tab_reg = st.tabs(["💡 Conceitos sugeridos","📏 Regras sugeridas"])
        with tab_conc:
            if meus_conc.empty:
                estado_vazio("💡","Nenhuma sugestão de conceito","Acesse o Glossário e use '💡 Sugerir novo conceito' para contribuir.")
            else:
                for _,r in meus_conc.iterrows():
                    cor_s = {"pendente":"#C9A227","aprovado":"#3FB950","rejeitado":"#F85149"}.get(r["status"],"#8B949E")
                    st.markdown(f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:10px 14px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;"><div><span style="color:#C9A227;font-weight:700;font-size:0.82rem;">{r["nome_sugerido"]}</span></div><span style="color:{cor_s};font-size:0.72rem;font-weight:600;">● {r["status"]}</span></div>', unsafe_allow_html=True)
        with tab_reg:
            if meus_reg.empty:
                estado_vazio("📏","Nenhuma sugestão de regra","Acesse o Glossário → Regras de Negócio para sugerir.")
            else:
                for _,r in meus_reg.iterrows():
                    cor_s = {"pendente":"#C9A227","aprovado":"#3FB950","rejeitado":"#F85149"}.get(r["status"],"#8B949E")
                    st.markdown(f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:10px 14px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;"><div><span style="color:#C9A227;font-weight:700;font-size:0.82rem;">{r["nome_regra"]}</span></div><span style="color:{cor_s};font-size:0.72rem;font-weight:600;">● {r["status"]}</span></div>', unsafe_allow_html=True)

    # ── CURADOR / APROVADOR ───────────────────────────────────────
    else:
        pend_aprov  = len(df_gloss[df_gloss["status"]=="em_revisao"]) if not df_gloss.empty else 0
        sem_desc    = len(df_meta[df_meta["descricao"]==""]) if not df_meta.empty else 0
        sem_owner   = len(df_meta[df_meta["data_owner"]==""]) if not df_meta.empty else 0
        sem_steward = len(df_meta[df_meta["data_steward"]==""]) if not df_meta.empty else 0
        sem_dom     = len(df_meta[df_meta["dominio"]==""]) if not df_meta.empty else 0
        total_pend  = pend_aprov+sem_desc+sem_owner+sem_steward+sem_dom

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1C2128,#21262D);border:1px solid #C9A22733;
                    border-radius:12px;padding:14px 18px;margin-bottom:16px;
                    display:flex;align-items:center;gap:12px;">
            <div style="background:#C9A22722;border-radius:8px;padding:8px;font-size:1.2rem;">⚡</div>
            <div>
                <div style="color:#E6EDF3;font-weight:700;font-size:0.9rem;">
                    Você possui <span style="color:#C9A227;">{total_pend}</span> ações pendentes.</div>
                <div style="color:#8B949E;font-size:0.72rem;margin-top:2px;">Revise e tome as ações necessárias.</div>
            </div>
        </div>""", unsafe_allow_html=True)

        section_divider("AÇÕES PRIORITÁRIAS")
        acoes = [
            ("APROVAR",f"{pend_aprov} conceitos aguardam aprovação","#C9A227","→ Workflow",pend_aprov),
            ("DOCUMENTAR",f"{sem_desc} ativos sem descrição","#58A6FF","→ Curadoria",sem_desc),
            ("ATRIBUIR",f"{sem_owner} ativos sem Responsável definido","#F85149","→ Curadoria",sem_owner),
            ("ALOCAR",f"{sem_steward} ativos sem Gestor definido","#FF7B72","→ Curadoria",sem_steward),
            ("CLASSIFICAR",f"{sem_dom} ativos sem domínio","#BC8CFF","→ Curadoria",sem_dom),
        ]
        tem_acao = False
        for tipo,msg,cor_a,dest,qtd in acoes:
            if qtd>0:
                tem_acao = True
                st.markdown(f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:11px 16px;margin-bottom:6px;display:flex;align-items:center;justify-content:space-between;"><div style="display:flex;align-items:center;gap:10px;"><span style="background:{cor_a}22;color:{cor_a};border-radius:4px;padding:2px 8px;font-size:0.65rem;font-weight:700;">{tipo}</span><span style="color:#E6EDF3;font-size:0.82rem;">{msg}</span></div><span style="color:#8B949E;font-size:0.72rem;">{dest}</span></div>', unsafe_allow_html=True)
        if not tem_acao:
            st.markdown('<div style="color:#3FB950;font-size:0.85rem;padding:12px;">✅ Nenhuma pendência no momento. Tudo em dia!</div>', unsafe_allow_html=True)

        section_divider("MINHAS RESPONSABILIDADES")
        if not df_meta.empty:
            k1,k2,k3,k4 = st.columns(4)
            with k1: st.markdown(kpi(len(df_meta[df_meta["data_owner"]==usuario]),"Como Responsável (Owner)","#C9A227",tooltip="Ativos pelos quais você é o Data Owner."), unsafe_allow_html=True)
            with k2: st.markdown(kpi(len(df_meta[df_meta["data_steward"]==usuario]),"Como Gestor (Steward)","#58A6FF",tooltip="Ativos pelos quais você é o Data Steward."), unsafe_allow_html=True)
            with k3: st.markdown(kpi(df_meta["dominio"].nunique(),"Domínios Acompanhados","#BC8CFF"), unsafe_allow_html=True)
            with k4:
                doc_media = df_meta["score_completude"].mean()
                cor_d = "#3FB950" if doc_media>=80 else "#C9A227" if doc_media>=60 else "#F85149"
                st.markdown(kpi(f"{doc_media:.0f}%","Score Médio de Documentação",cor_d,tooltip="Média do score de documentação de todos os ativos."), unsafe_allow_html=True)

        # Sugestões pendentes — visível para curador/aprovador
        df_sug_co = load_sugestoes_conceitos()
        df_sug_re = load_sugestoes_regras()
        pend_conc = df_sug_co[df_sug_co["status"]=="pendente"] if not df_sug_co.empty else pd.DataFrame()
        pend_reg  = df_sug_re[df_sug_re["status"]=="pendente"] if not df_sug_re.empty else pd.DataFrame()

        if not pend_conc.empty or not pend_reg.empty:
            section_divider("SUGESTÕES AGUARDANDO ANÁLISE")
            if not pend_conc.empty:
                st.markdown(f'<div style="color:#C9A227;font-size:0.78rem;font-weight:700;margin-bottom:6px;">💡 {len(pend_conc)} sugestão(ões) de conceito pendente(s)</div>', unsafe_allow_html=True)
                for _,r in pend_conc.iterrows():
                    with st.expander(f"💡 {r['nome_sugerido']} — por {r['solicitante']}"):
                        st.markdown(f"**Definição:** {r['definicao']}")
                        st.markdown(f"**Justificativa:** {r['justificativa'] or '—'}")
                        ca,cr = st.columns(2)
                        with ca:
                            if st.button("✅ Encaminhar para Glossário",key=f"ap_conc_{r['sugestao_id']}",use_container_width=True):
                                ok,_ = exe(f"UPDATE meridian_governanca.sugestoes_conceitos SET status='aprovado',analisado_por='{esc(usuario)}',atualizado_em=current_timestamp() WHERE sugestao_id='{r['sugestao_id']}'")
                                if ok: st.success("✅ Aprovado!"); st.cache_data.clear(); st.rerun()
                        with cr:
                            if st.button("❌ Rejeitar",key=f"rej_conc_{r['sugestao_id']}",use_container_width=True):
                                ok,_ = exe(f"UPDATE meridian_governanca.sugestoes_conceitos SET status='rejeitado',analisado_por='{esc(usuario)}',atualizado_em=current_timestamp() WHERE sugestao_id='{r['sugestao_id']}'")
                                if ok: st.warning("↩️ Rejeitado."); st.cache_data.clear(); st.rerun()

        if is_aprovador and pend_aprov>0:
            section_divider("CONCEITOS AGUARDANDO APROVAÇÃO")
            for _,row in df_gloss[df_gloss["status"]=="em_revisao"].iterrows():
                with st.expander(f"📋 {row['termo']} · {row['dominio']} · {row.get('criticidade','—')}"):
                    st.markdown(f"**Definição:** {row['definicao']}")
                    ca,cr = st.columns(2)
                    with ca:
                        if st.button("✅ Aprovar",key=f"mea_{row['glossary_id']}",use_container_width=True):
                            ok,_ = exe(f"UPDATE meridian_governanca.business_glossary SET status='homologado',atualizado_por='{esc(usuario)}',atualizado_em=current_timestamp() WHERE glossary_id='{row['glossary_id']}'")
                            if ok: st.success("✅ Homologado!"); st.cache_data.clear(); st.rerun()
                    with cr:
                        motivo = st.text_input("Motivo da rejeição",key=f"mem_{row['glossary_id']}")
                        if st.button("❌ Rejeitar",key=f"mer_{row['glossary_id']}",use_container_width=True):
                            if motivo:
                                ok,_ = exe(f"UPDATE meridian_governanca.business_glossary SET status='rascunho',atualizado_por='{esc(usuario)}',atualizado_em=current_timestamp() WHERE glossary_id='{row['glossary_id']}'")
                                if ok: st.warning("↩️ Devolvido."); st.cache_data.clear(); st.rerun()
                            else: st.warning("Informe o motivo.")

        section_divider("MEUS CONCEITOS NO GLOSSÁRIO")
        df_meus = df_gloss[df_gloss["steward_email"]==usuario] if not df_gloss.empty else pd.DataFrame()
        if not df_meus.empty:
            for _,row in df_meus.iterrows():
                cor_s = {"homologado":"#3FB950","em_revisao":"#58A6FF","rascunho":"#8B949E"}.get(row["status"],"#8B949E")
                st.markdown(f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:9px 14px;margin-bottom:5px;display:flex;justify-content:space-between;align-items:center;"><span style="color:#E6EDF3;font-size:0.82rem;font-weight:600;">{row["termo"]}</span><span style="color:{cor_s};font-size:0.75rem;font-weight:600;">● {row["status"].replace("_"," ").title()}</span></div>', unsafe_allow_html=True)
        else:
            estado_vazio("📖","Nenhum conceito vinculado","Não há conceitos vinculados ao seu usuário como Gestor (Steward).")

    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# ✏️ CURADORIA — Apenas para curador/aprovador
# ════════════════════════════════════════════════════════════════════
elif pagina == "✏️ Curadoria":
    if not is_curador:
        estado_vazio("🔒","Acesso restrito","Esta área é destinada a Curadores e Aprovadores. Entre em contato com a equipe de Governança se precisar de acesso.")
    else:
        page_header("✏️","Curadoria de Conhecimento","Enriqueça o entendimento — documente, classifique e atribua responsáveis.")

        df_cur = load_meta()
        if not df_cur.empty:
            cur1,cur2 = st.tabs(["📋 Tabela Individual","⚡ Edição em Lote"])
            with cur1:
                c_left,c_right = st.columns([1,2])
                with c_left:
                    sel_s = st.selectbox("Schema",sorted(df_cur["schema_name"].unique().tolist()),key="cur_s")
                    sel_t = st.selectbox("Tabela",df_cur[df_cur["schema_name"]==sel_s]["table_name"].tolist(),key="cur_t")
                with c_right:
                    row = df_cur[(df_cur["schema_name"]==sel_s)&(df_cur["table_name"]==sel_t)].iloc[0]
                    doc_p  = 100 if row["descricao"] else 0
                    own_p  = 100 if row["data_owner"] else 0
                    cert_p = 100 if row["selo"]=="certificado" else 0
                    qual_p = row["score_completude"]

                    st.markdown(f'<div style="background:#161B22;border:1px solid #30363D;border-radius:10px;padding:12px 16px;margin-bottom:12px;"><div style="color:#C9A227;font-weight:700;font-size:0.9rem;">{sel_t}</div><div style="color:#8B949E;font-size:0.72rem;margin-top:2px;">{row["descricao"][:60]+"..." if row["descricao"] and len(row["descricao"])>60 else row["descricao"] or "Sem descrição cadastrada."}</div></div>', unsafe_allow_html=True)

                    pp1,pp2,pp3,pp4,pp5 = st.columns(5)
                    for pcol,pn,pv in [(pp1,"DOCUMENTAÇÃO",doc_p),(pp2,"RESPONSÁVEL",own_p),(pp3,"RELACION.",0),(pp4,"QUALIDADE",qual_p),(pp5,"CERTIFICAÇÃO",cert_p)]:
                        cor_pp = "#3FB950" if pv>=80 else "#C9A227" if pv>0 else "#F85149"
                        with pcol:
                            st.markdown(f'<div style="background:#0D1117;border:1px solid #30363D;border-radius:8px;padding:9px;text-align:center;margin-bottom:10px;"><div style="font-size:0.55rem;color:#8B949E;text-transform:uppercase;letter-spacing:0.8px;">{pn}</div><div style="font-size:1.1rem;font-weight:800;color:{cor_pp};">{f"{pv}%" if pv>0 else "—"}</div></div>', unsafe_allow_html=True)

                    ed1,ed2 = st.columns(2)
                    with ed1:
                        new_desc = st.text_area("Descrição",value=row["descricao"] or "",height=80,key="c_desc",placeholder="Descreva o propósito desta tabela...")
                        doms = ["","Crédito","Pagamentos","Clientes","Compliance","Produtos"]
                        dom_i = doms.index(row["dominio"]) if row["dominio"] in doms else 0
                        new_dom = st.selectbox("Domínio",doms,index=dom_i,key="c_dom")
                    with ed2:
                        new_own = st.text_input("Responsável (Data Owner)",value=row["data_owner"] or "",key="c_own")
                        new_stw = st.text_input("Gestor (Data Steward)",value=row["data_steward"] or "",key="c_stw")

                    bc1,bc2 = st.columns(2)
                    with bc1:
                        if st.button("💾 Salvar",type="primary",key="c_save",use_container_width=True):
                            filled = sum([bool(new_desc),bool(new_dom),bool(new_own),bool(new_stw),bool(row["funcao_negocio"])])
                            ns = filled*20
                            sl = "certificado" if ns==100 else "parcial" if ns>=60 else "pendente"
                            ok,err = exe(f"UPDATE meridian_governanca.tabelas_metadata SET descricao='{esc(new_desc)}',dominio='{esc(new_dom)}',data_owner='{esc(new_own)}',data_steward='{esc(new_stw)}',score_completude={ns},selo='{sl}',atualizado_em=current_timestamp() WHERE schema_name='{sel_s}' AND table_name='{sel_t}'")
                            if ok:
                                exe(f"INSERT INTO meridian_governanca.metadata_audit VALUES ('{uuid.uuid4()}',current_timestamp(),'{sel_s}','{sel_t}','tabela','','metadados','{row['score_completude']}','{ns}','manual','{esc(usuario)}','{esc(usuario[:8])}')")
                                st.success(f"✅ Salvo! Score: {ns}%"); st.cache_data.clear(); st.rerun()
                            else: st.error(f"Não foi possível salvar. Tente novamente.")
                    with bc2:
                        if st.button("🤖 Sugerir com IA",key="c_ai",use_container_width=True):
                            sugestoes = {
                                "clientes_raw":("Dados brutos de clientes ingeridos do sistema core bancário.","Clientes"),
                                "contas_raw":("Dados brutos de contas correntes e poupança dos clientes.","Clientes"),
                                "transacoes_raw":("Transações financeiras brutas de todos os canais.","Pagamentos"),
                                "propostas_credito_raw":("Propostas de crédito com status de aprovação.","Crédito"),
                                "pix_raw":("Transações PIX brutas do SPI do Banco Central.","Pagamentos"),
                                "dim_clientes":("Dimensão de clientes tratada e enriquecida.","Clientes"),
                                "dim_contas":("Dimensão de contas com dados consolidados.","Clientes"),
                                "fato_transacoes":("Fato de transações financeiras por período e canal.","Pagamentos"),
                                "fato_credito":("Fato de operações de crédito aprovadas e recusadas.","Crédito"),
                                "fato_inadimplencia":("Fato de inadimplência com dias de atraso.","Crédito"),
                                "fato_pix":("Fato de transações PIX consolidadas.","Pagamentos"),
                                "dim_produtos":("Dimensão de produtos financeiros do banco.","Produtos"),
                                "indicadores_carteira":("Indicadores consolidados da carteira de crédito.","Crédito"),
                                "perfil_cliente_360":("Visão 360 do cliente com score e churn.","Clientes"),
                                "dashboard_inadimplencia":("Base para dashboard executivo de inadimplência.","Crédito"),
                                "indicadores_pix":("Indicadores de volume e performance do PIX.","Pagamentos"),
                                "base_lgpd":("Mapeamento de dados pessoais para conformidade LGPD.","Compliance"),
                            }
                            sug = sugestoes.get(sel_t,(f"Tabela {sel_t} pertencente ao schema {sel_s}.",""))
                            st.session_state["ai_desc"] = sug[0]; st.session_state["ai_dom"] = sug[1]; st.rerun()

                    if "ai_desc" in st.session_state:
                        st.markdown('<div style="background:#C9A22711;border:1px solid #C9A22733;border-radius:8px;padding:10px 14px;margin-top:8px;"><div style="color:#C9A227;font-weight:700;font-size:0.75rem;">🤖 Sugestão da IA — revise antes de salvar</div></div>', unsafe_allow_html=True)
                        sug_d = st.text_area("Descrição sugerida",value=st.session_state["ai_desc"],key="sug_d")
                        so = ["","Crédito","Pagamentos","Clientes","Compliance","Produtos"]
                        sv = st.session_state["ai_dom"]; si = so.index(sv) if sv in so else 0
                        sug_dom = st.selectbox("Domínio sugerido",so,index=si,key="sd2")
                        sa1,sa2 = st.columns(2)
                        with sa1:
                            if st.button("✅ Aceitar e salvar",key="ai_ac",use_container_width=True):
                                filled = sum([bool(sug_d),bool(sug_dom),bool(new_own),bool(new_stw),bool(row["funcao_negocio"])])
                                ns = filled*20; sl = "certificado" if ns==100 else "parcial" if ns>=60 else "pendente"
                                ok,_ = exe(f"UPDATE meridian_governanca.tabelas_metadata SET descricao='{esc(sug_d)}',dominio='{esc(sug_dom)}',score_completude={ns},selo='{sl}',atualizado_em=current_timestamp() WHERE schema_name='{sel_s}' AND table_name='{sel_t}'")
                                if ok:
                                    exe(f"INSERT INTO meridian_governanca.metadata_audit VALUES ('{uuid.uuid4()}',current_timestamp(),'{sel_s}','{sel_t}','tabela','','metadados','{row['score_completude']}','{ns}','ia','{esc(usuario)}','{esc(usuario[:8])}')")
                                    st.success("✅ Aplicado!"); del st.session_state["ai_desc"]; del st.session_state["ai_dom"]; st.cache_data.clear(); st.rerun()
                        with sa2:
                            if st.button("❌ Descartar",key="ai_dc",use_container_width=True):
                                del st.session_state["ai_desc"]; del st.session_state["ai_dom"]; st.rerun()

            with cur2:
                f1c,f2c = st.columns(2)
                with f1c: fl_s = st.selectbox("Schema",["Todos"]+sorted(df_cur["schema_name"].unique().tolist()),key="lote_s")
                with f2c: fl_sl = st.selectbox("Situação",["Todos","certificado","parcial","pendente"],key="lote_sl")
                df_l = df_cur.copy()
                if fl_s  != "Todos": df_l = df_l[df_l["schema_name"]==fl_s]
                if fl_sl != "Todos": df_l = df_l[df_l["selo"]==fl_sl]
                df_led = df_l[["schema_name","table_name","score_completude","selo"]].copy()
                df_led.insert(0,"Selecionar",False)
                edited = st.data_editor(df_led.rename(columns={"schema_name":"Schema","table_name":"Tabela","score_completude":"Score","selo":"Situação"}),use_container_width=True,hide_index=True,column_config={"Selecionar":st.column_config.CheckboxColumn()})
                sels = edited[edited["Selecionar"]==True]
                if len(sels)>0:
                    st.markdown(f'<div style="color:#C9A227;font-size:0.82rem;margin:6px 0;">{len(sels)} tabela(s) selecionada(s)</div>', unsafe_allow_html=True)
                    lb1,lb2,lb3 = st.columns(3)
                    with lb1: l_dom = st.selectbox("Domínio",["","Crédito","Pagamentos","Clientes","Compliance","Produtos"],key="l_dom")
                    with lb2: l_own = st.text_input("Responsável (Owner)",key="l_own")
                    with lb3: l_stw = st.text_input("Gestor (Steward)",key="l_stw")
                    if st.button(f"🚀 Aplicar em {len(sels)} tabela(s)",type="primary",key="l_apply"):
                        erros = []
                        for _,r in sels.iterrows():
                            sets = []
                            if l_dom: sets.append(f"dominio='{esc(l_dom)}'")
                            if l_own: sets.append(f"data_owner='{esc(l_own)}'")
                            if l_stw: sets.append(f"data_steward='{esc(l_stw)}'")
                            if sets:
                                sets.append("atualizado_em=current_timestamp()")
                                ok,_ = exe(f"UPDATE meridian_governanca.tabelas_metadata SET {', '.join(sets)} WHERE schema_name='{r['Schema']}' AND table_name='{r['Tabela']}'")
                                if not ok: erros.append(r["Tabela"])
                        if erros: st.warning(f"Não foi possível atualizar: {erros}")
                        else: st.success(f"✅ {len(sels)} tabelas atualizadas!"); st.cache_data.clear(); st.rerun()

    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# 🕐 AUDITORIA
# ════════════════════════════════════════════════════════════════════
elif pagina == "🕐 Auditoria":
    if not is_curador:
        estado_vazio("🔒","Acesso restrito","Esta área é destinada a Curadores e Aprovadores.")
    else:
        page_header("🕐","Trilha de Auditoria","Rastreabilidade — quem alterou, quando e por quê.")

        df_aud,err = qry("SELECT timestamp_op, schema_name, table_name, tipo_objeto, campo_alterado, valor_anterior, valor_novo, origem, alterado_por FROM meridian_governanca.metadata_audit ORDER BY timestamp_op DESC LIMIT 500")

        if err:
            st.error("Não foi possível carregar os dados de auditoria. Tente recarregar a página.")
        elif df_aud.empty:
            estado_vazio("📭","Nenhum registro ainda","As alterações feitas na Curadoria e no Glossário aparecerão aqui.")
        else:
            total = len(df_aud); manual = len(df_aud[df_aud["origem"]=="manual"]); ia_c = len(df_aud[df_aud["origem"]=="ia"])
            k1,k2,k3 = st.columns(3)
            with k1: st.markdown(kpi(total,"Total de Registros","#C9A227"), unsafe_allow_html=True)
            with k2: st.markdown(kpi(manual,"Alterações Manuais","#58A6FF"), unsafe_allow_html=True)
            with k3: st.markdown(kpi(ia_c,"Via Inteligência Artificial","#BC8CFF"), unsafe_allow_html=True)

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            af1,af2,af3 = st.columns(3)
            with af1: f_sc = st.selectbox("Schema",["Todos"]+sorted(df_aud["schema_name"].dropna().unique().tolist()),key="a_sc")
            with af2: f_or = st.selectbox("Origem",["Todos","manual","ia"],key="a_or")
            with af3: f_lim = st.selectbox("Linhas exibidas",[50,100,200,500],key="a_lim")

            df_af = df_aud.copy()
            if f_sc != "Todos": df_af = df_af[df_af["schema_name"]==f_sc]
            if f_or != "Todos": df_af = df_af[df_af["origem"]==f_or]
            df_af = df_af.head(f_lim)

            st.markdown('<div style="background:#161B22;border:1px solid #30363D;border-radius:10px;overflow:hidden;margin-top:8px;"><table style="width:100%;border-collapse:collapse;"><thead><tr style="border-bottom:1px solid #30363D;"><th style="color:#8B949E;font-size:0.62rem;font-weight:700;text-transform:uppercase;padding:9px 12px;text-align:left;">DATA/HORA</th><th style="color:#8B949E;font-size:0.62rem;font-weight:700;text-transform:uppercase;padding:9px 12px;text-align:left;">SCHEMA</th><th style="color:#8B949E;font-size:0.62rem;font-weight:700;text-transform:uppercase;padding:9px 12px;text-align:left;">TABELA</th><th style="color:#8B949E;font-size:0.62rem;font-weight:700;text-transform:uppercase;padding:9px 12px;text-align:left;">CAMPO</th><th style="color:#8B949E;font-size:0.62rem;font-weight:700;text-transform:uppercase;padding:9px 12px;text-align:left;">VALOR ANTERIOR</th><th style="color:#8B949E;font-size:0.62rem;font-weight:700;text-transform:uppercase;padding:9px 12px;text-align:left;">VALOR NOVO</th><th style="color:#8B949E;font-size:0.62rem;font-weight:700;text-transform:uppercase;padding:9px 12px;text-align:left;">ORIGEM</th></tr></thead><tbody>', unsafe_allow_html=True)

            for _,row in df_af.iterrows():
                ts = str(row["timestamp_op"])[:16] if row["timestamp_op"] else "—"
                oc = "#BC8CFF" if row["origem"]=="ia" else "#58A6FF"
                ot = "IA" if row["origem"]=="ia" else "Manual"
                va = str(row["valor_anterior"])[:30] if row["valor_anterior"] else "—"
                vn = str(row["valor_novo"])[:40] if row["valor_novo"] else "—"
                st.markdown(f'<tr style="border-bottom:1px solid #21262D;"><td style="color:#8B949E;font-size:0.73rem;padding:8px 12px;">{ts}</td><td style="color:#58A6FF;font-size:0.73rem;padding:8px 12px;">{row["schema_name"] or "—"}</td><td style="color:#E6EDF3;font-size:0.73rem;padding:8px 12px;font-weight:600;">{row["table_name"] or "—"}</td><td style="color:#8B949E;font-size:0.73rem;padding:8px 12px;">{row["campo_alterado"] or "—"}</td><td style="color:#8B949E;font-size:0.73rem;padding:8px 12px;">{va}</td><td style="color:#E6EDF3;font-size:0.73rem;padding:8px 12px;">{vn}</td><td style="padding:8px 12px;"><span style="background:{oc}22;color:{oc};border-radius:4px;padding:2px 8px;font-size:0.65rem;font-weight:700;">{ot}</span></td></tr>', unsafe_allow_html=True)

            st.markdown("</tbody></table></div>", unsafe_allow_html=True)

    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# 📊 INDICADORES — Painel de Gestão de Governança
# ════════════════════════════════════════════════════════════════════
elif pagina == "📊 Indicadores":
    page_header("📊","Painel de Indicadores de Gestão",
                "Evolução temporal da governança de dados — documentação, ownership e qualidade.")
    st.markdown("""<div style="background:#161B2299;border:1px solid #30363D;border-radius:8px;
                padding:10px 14px;margin-bottom:16px;"><div style="color:#8B949E;font-size:0.78rem;line-height:1.6;">
                Este painel mostra como os principais indicadores de governança evoluíram ao longo do tempo.
                Use o filtro de domínio para acompanhar a maturidade de uma área específica.</div></div>""",
                unsafe_allow_html=True)
    df_snap = load_indicators_snapshot()
    df_meta = load_meta()
    df_cert = load_certification()
    if df_snap.empty:
        estado_vazio("📊","Nenhum snapshot disponível","Os indicadores serão calculados a cada ciclo de curadoria.")
    else:
        dominios_snap = ["Todos"] + sorted([d for d in df_snap["dominio"].unique() if d != "Todos"])
        f_dom_ind = st.selectbox("Filtrar por Domínio", dominios_snap, key="ind_dom")
        df_sn = df_snap[df_snap["dominio"]==f_dom_ind] if f_dom_ind != "Todos" else df_snap[df_snap["dominio"]=="Todos"]
        ultimo   = df_sn.sort_values("data_snapshot").iloc[-1]  if not df_sn.empty    else None
        anterior = df_sn.sort_values("data_snapshot").iloc[-2]  if len(df_sn)>1      else None
        if ultimo is not None:
            def delta(a,b,c):
                if b is None: return ""
                d = a[c]-b[c]; cor="#3FB950" if d>0 else "#F85149" if d<0 else "#8B949E"; s="↑" if d>0 else "↓" if d<0 else "→"
                return f'<span style="color:{cor};font-size:0.65rem;font-weight:700;margin-left:4px;">{s}{abs(d):.1f}%</span>'
            k1,k2,k3,k4 = st.columns(4)
            for col,(lbl,campo,cor_k) in zip([k1,k2,k3,k4],[
                ("Documentação","score_doc","#58A6FF"),("Ownership","score_ownership","#C9A227"),
                ("Qualidade","score_qualidade","#3FB950"),("Score Geral","score_geral","#BC8CFF")]):
                val=ultimo[campo]; d=delta(ultimo,anterior,campo)
                cor_v="#3FB950" if val>=80 else "#C9A227" if val>=60 else "#F85149"
                with col:
                    st.markdown(f'<div style="background:#161B22;border:1px solid #30363D;border-radius:10px;padding:14px 16px;border-top:3px solid {cor_k};"><div style="font-size:0.62rem;color:#8B949E;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">{lbl}</div><div style="display:flex;align-items:baseline;gap:4px;"><span style="font-size:1.7rem;font-weight:800;color:{cor_v};">{val:.1f}%</span>{d}</div></div>',unsafe_allow_html=True)
        section_divider("EVOLUÇÃO DOS INDICADORES")
        if not df_sn.empty:
            fig = go.Figure()
            for campo,cor_l,nome_l in [("score_doc","#58A6FF","Documentação"),("score_ownership","#C9A227","Ownership"),("score_qualidade","#3FB950","Qualidade"),("score_geral","#BC8CFF","Score Geral")]:
                fig.add_trace(go.Scatter(x=pd.to_datetime(df_sn["data_snapshot"]),y=df_sn[campo],name=nome_l,line=dict(color=cor_l,width=2.5),mode="lines+markers",marker=dict(size=6)))
            fig.update_layout(paper_bgcolor="#161B22",plot_bgcolor="#161B22",font=dict(color="#8B949E",size=11),legend=dict(orientation="h",yanchor="bottom",y=1.02,bgcolor="rgba(0,0,0,0)"),height=320,margin=dict(t=40,b=20,l=40,r=20),xaxis=dict(showgrid=False,color="#484F58"),yaxis=dict(showgrid=True,gridcolor="#21262D",range=[0,105],ticksuffix="%"))
            st.plotly_chart(fig,use_container_width=True)
        section_divider("DISTRIBUIÇÃO POR DOMÍNIO")
        if not df_meta.empty:
            dom_agg=df_meta.groupby("dominio").agg(score_medio=("score_completude","mean")).reset_index().sort_values("score_medio",ascending=True)
            fig2=go.Figure(go.Bar(x=dom_agg["score_medio"],y=dom_agg["dominio"],orientation="h",marker=dict(color=dom_agg["score_medio"],colorscale=[[0,"#F85149"],[0.6,"#C9A227"],[1,"#3FB950"]],cmin=0,cmax=100),text=[f"{v:.0f}%" for v in dom_agg["score_medio"]],textposition="outside",textfont=dict(color="#E6EDF3",size=11)))
            fig2.update_layout(paper_bgcolor="#161B22",plot_bgcolor="#161B22",font=dict(color="#8B949E",size=11),height=260,margin=dict(t=10,b=10,l=10,r=60),xaxis=dict(showgrid=True,gridcolor="#21262D",range=[0,115],ticksuffix="%"),yaxis=dict(showgrid=False,color="#E6EDF3"))
            st.plotly_chart(fig2,use_container_width=True)
        section_divider("RESUMO DE CERTIFICAÇÃO")
        if not df_cert.empty:
            cert_status=df_cert["status_cert"].value_counts().reset_index(); cert_status.columns=["status","qtd"]
            cor_cert={"certificado":"#3FB950","em_analise":"#C9A227","pendente":"#58A6FF","nao_iniciado":"#484F58"}
            cols_cert=st.columns(len(cert_status))
            for col,(_,row) in zip(cols_cert,cert_status.iterrows()):
                cor_c=cor_cert.get(row["status"],"#8B949E")
                label_c={"certificado":"✅ Certificados","em_analise":"🔵 Em Análise","pendente":"⏳ Pendentes","nao_iniciado":"📋 Não Iniciados"}.get(row["status"],row["status"])
                with col: st.markdown(kpi(row["qtd"],label_c,cor_c),unsafe_allow_html=True)
    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# 🏆 QUALIDADE — Score por Dimensão
# ════════════════════════════════════════════════════════════════════
elif pagina == "🏆 Qualidade":
    page_header("🏆","Score de Qualidade de Dados","Avaliação multidimensional — Completude · Unicidade · Validade · Atualidade · Consistência.")
    st.markdown("""<div style="background:#161B2299;border:1px solid #30363D;border-radius:8px;padding:10px 14px;margin-bottom:16px;"><div style="color:#8B949E;font-size:0.78rem;line-height:1.6;">A qualidade dos dados é avaliada em <strong style="color:#C9A227;">5 dimensões independentes</strong>. O Score Final é a média simples das 5 dimensões.</div></div>""",unsafe_allow_html=True)
    DIMENSOES={"completude_pct":{"nome":"Completude","icone":"📋","cor":"#58A6FF","conceito":"% de campos obrigatórios preenchidos."},"unicidade_pct":{"nome":"Unicidade","icone":"🔑","cor":"#C9A227","conceito":"% de registros únicos na chave primária."},"validade_pct":{"nome":"Validade","icone":"✅","cor":"#3FB950","conceito":"% de valores no formato e domínio esperados."},"atualidade_pct":{"nome":"Atualidade","icone":"🕐","cor":"#BC8CFF","conceito":"% de registros dentro da janela de tempo esperada."},"consistencia_pct":{"nome":"Consistência","icone":"🔗","cor":"#FF7B72","conceito":"% de registros consistentes com tabelas relacionadas."}}
    df_qual=load_quality_dimensions()
    if df_qual.empty:
        estado_vazio("🏆","Nenhum dado de qualidade","Execute a avaliação de qualidade na Curadoria.")
    else:
        media_geral=df_qual["score_final"].mean(); cor_mg="#3FB950" if media_geral>=80 else "#C9A227" if media_geral>=60 else "#F85149"
        st.markdown(f'<div style="background:#161B22;border:1px solid #30363D;border-radius:16px;padding:20px;text-align:center;margin-bottom:20px;"><div style="font-size:0.7rem;color:#8B949E;text-transform:uppercase;letter-spacing:2px;margin-bottom:4px;">{len(df_qual)} ativos avaliados</div><div style="font-size:3.5rem;font-weight:800;color:{cor_mg};line-height:1;">{media_geral:.1f}%</div><div style="color:#8B949E;font-size:0.75rem;margin-top:6px;">Alta (≥80%): {len(df_qual[df_qual["nivel"]=="Alta"])} · Média (40–79%): {len(df_qual[df_qual["nivel"]=="Media"])} · Baixa (&lt;40%): {len(df_qual[df_qual["nivel"]=="Baixa"])}</div></div>',unsafe_allow_html=True)
        section_divider("MÉDIA POR DIMENSÃO")
        cols_dim=st.columns(5)
        for col,(campo,info) in zip(cols_dim,DIMENSOES.items()):
            media_dim=df_qual[campo].mean(); cor_d="#3FB950" if media_dim>=80 else "#C9A227" if media_dim>=60 else "#F85149"
            with col: st.markdown(f'<div style="background:#161B22;border:1px solid #30363D;border-radius:10px;padding:14px;text-align:center;" title="{info["conceito"]}"><div style="font-size:1.2rem;margin-bottom:4px;">{info["icone"]}</div><div style="font-size:1.6rem;font-weight:800;color:{cor_d};">{media_dim:.1f}%</div><div style="color:#8B949E;font-size:0.68rem;margin-bottom:8px;">{info["nome"]}</div><div style="background:#30363D;border-radius:4px;height:3px;"><div style="background:{cor_d};border-radius:4px;height:3px;width:{min(media_dim,100):.0f}%;"></div></div><div style="color:#484F58;font-size:0.6rem;margin-top:6px;line-height:1.3;">{info["conceito"]}</div></div>',unsafe_allow_html=True)
        section_divider("AVALIAÇÃO POR ATIVO")
        f1q,f2q,f3q=st.columns(3)
        with f1q: fq_dom=st.selectbox("Domínio",["Todos"]+sorted([d for d in df_qual["dominio"].unique() if d]),key="q_dom")
        with f2q: fq_cam=st.selectbox("Camada",["Todas"]+sorted(df_qual["schema_name"].unique().tolist()),key="q_cam")
        with f3q: fq_niv=st.selectbox("Nível",["Todos","Alta","Media","Baixa"],key="q_niv")
        df_qf=df_qual.copy()
        if fq_dom!="Todos": df_qf=df_qf[df_qf["dominio"]==fq_dom]
        if fq_cam!="Todas": df_qf=df_qf[df_qf["schema_name"]==fq_cam]
        if fq_niv!="Todos": df_qf=df_qf[df_qf["nivel"]==fq_niv]
        df_qf=df_qf.sort_values("score_final",ascending=False)
        for _,row in df_qf.iterrows():
            cor_q="#3FB950" if row["score_final"]>=80 else "#C9A227" if row["score_final"]>=40 else "#F85149"
            nivel_badge={"Alta":"#3FB950","Media":"#C9A227","Baixa":"#F85149"}.get(row["nivel"],"#8B949E")
            dims_html="".join([f'<div style="text-align:center;"><div style="font-size:0.6rem;color:#484F58;margin-bottom:2px;">{info["icone"]} {info["nome"][:4]}.</div><div style="font-size:0.75rem;font-weight:700;color:{"#3FB950" if row[campo]>=80 else "#C9A227" if row[campo]>=40 else "#F85149"};">{row[campo]:.0f}%</div></div>' for campo,info in DIMENSOES.items()])
            st.markdown(f'<div style="background:#161B22;border:1px solid #30363D;border-radius:10px;padding:12px 16px;margin-bottom:6px;"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;"><div><span style="color:#C9A227;font-weight:700;font-size:0.85rem;">{row["table_name"]}</span><span style="background:#58A6FF22;color:#58A6FF;border-radius:3px;padding:1px 6px;font-size:0.62rem;margin-left:6px;">{row["schema_name"]}</span><span style="background:{nivel_badge}22;color:{nivel_badge};border-radius:3px;padding:1px 6px;font-size:0.62rem;margin-left:4px;">{row["nivel"]}</span></div><span style="color:{cor_q};font-size:1.1rem;font-weight:800;">{row["score_final"]:.1f}%</span></div><div style="display:grid;grid-template-columns:repeat(5,1fr);gap:6px;">{dims_html}</div></div>',unsafe_allow_html=True)
    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# 🥇 CERTIFICAÇÃO — Selos e Status
# ════════════════════════════════════════════════════════════════════
elif pagina == "🥇 Certificação":
    page_header("🥇","Certificação de Ativos de Dados","Selos de maturidade — Ouro · Prata · Bronze — com critérios transparentes.")
    st.markdown("""<div style="background:#161B2299;border:1px solid #30363D;border-radius:8px;padding:10px 14px;margin-bottom:16px;"><div style="color:#8B949E;font-size:0.78rem;line-height:1.6;">A certificação valida que um ativo atende a critérios mínimos de governança e qualidade. Os selos são concedidos após análise formal pela equipe de Governança.</div></div>""",unsafe_allow_html=True)
    SELOS={"Ouro":{"cor":"#C9A227","icone":"🥇","req_doc":100,"req_qual":90,"desc":"Gov. 100% + Qualidade ≥90% + todos os critérios atendidos"},"Prata":{"cor":"#A8A9AD","icone":"🥈","req_doc":80,"req_qual":70,"desc":"Gov. ≥80% + Qualidade ≥70% + Owner e Domínio definidos"},"Bronze":{"cor":"#CD7F32","icone":"🥉","req_doc":60,"req_qual":40,"desc":"Documentação parcial — ativo em processo de curadoria"}}
    col_selos=st.columns(3)
    for col,(nome,info) in zip(col_selos,SELOS.items()):
        with col: st.markdown(f'<div style="background:#161B22;border:2px solid {info["cor"]}44;border-radius:14px;padding:16px;text-align:center;"><div style="font-size:2rem;margin-bottom:6px;">{info["icone"]}</div><div style="color:{info["cor"]};font-weight:800;font-size:1rem;margin-bottom:4px;">Selo {nome}</div><div style="color:#8B949E;font-size:0.72rem;line-height:1.4;">{info["desc"]}</div><div style="background:#30363D;border-radius:4px;height:1px;margin:10px 0;"></div><div style="font-size:0.65rem;color:#484F58;">Gov. mín: {info["req_doc"]}% · Qual. mín: {info["req_qual"]}%</div></div>',unsafe_allow_html=True)
    section_divider("STATUS DE CERTIFICAÇÃO POR ATIVO")
    df_cert=load_certification()
    if df_cert.empty:
        estado_vazio("🥇","Nenhum ativo certificado ainda","Inicie o processo de certificação na Curadoria.")
    else:
        fc1,fc2,fc3=st.columns(3)
        with fc1: f_cert_dom=st.selectbox("Domínio",["Todos"]+sorted([d for d in df_cert["dominio"].unique() if d]),key="fc_dom")
        with fc2: f_cert_st=st.selectbox("Status",["Todos","certificado","em_analise","pendente","nao_iniciado"],key="fc_st")
        with fc3: f_cert_niv=st.selectbox("Nível",["Todos","Ouro","Prata","Bronze"],key="fc_niv")
        df_cf=df_cert.copy()
        if f_cert_dom!="Todos": df_cf=df_cf[df_cf["dominio"]==f_cert_dom]
        if f_cert_st!="Todos":  df_cf=df_cf[df_cf["status_cert"]==f_cert_st]
        if f_cert_niv!="Todos": df_cf=df_cf[df_cf["nivel_cert"]==f_cert_niv]
        for _,row in df_cf.iterrows():
            cor_st={"certificado":"#3FB950","em_analise":"#C9A227","pendente":"#58A6FF","nao_iniciado":"#484F58"}.get(row["status_cert"],"#8B949E")
            label_st={"certificado":"✅ Certificado","em_analise":"🔵 Em Análise","pendente":"⏳ Pendente","nao_iniciado":"📋 Não Iniciado"}.get(row["status_cert"],row["status_cert"])
            cor_nv=SELOS.get(row["nivel_cert"],{}).get("cor","#8B949E"); ic_nv=SELOS.get(row["nivel_cert"],{}).get("icone","")
            criterios=[("Doc.",row["criterio_doc"]),("Owner",row["criterio_owner"]),("Steward",row["criterio_steward"]),("Domínio",row["criterio_dominio"]),("Qualidade",row["criterio_qualidade"])]
            crit_items = [(n, ok) for n,ok in criterios]
            crit_html = "".join([
                f'<span style="color:{"#3FB950" if ok else "#F85149"};font-size:0.68rem;margin-right:10px;">{"OK" if ok else "X"} {n}</span>'
                for n,ok in crit_items
            ])
            validade_html = f'<span>Válido até: <b style="color:#3FB950;">{str(row["valido_ate"])}</b></span>' if row["valido_ate"] else ""
            st.markdown(
                f'<div style="background:#161B22;border:1px solid #30363D;border-radius:12px;padding:14px 18px;margin-bottom:8px;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">'
                f'<div><span style="color:#E6EDF3;font-weight:800;font-size:0.9rem;">{row["table_name"]}</span>'
                f'<span style="background:#58A6FF22;color:#58A6FF;border-radius:4px;padding:2px 7px;font-size:0.65rem;margin-left:6px;">{row["schema_name"]}</span>'
                f'<span style="background:{cor_nv}22;color:{cor_nv};border-radius:4px;padding:2px 7px;font-size:0.65rem;margin-left:4px;">{ic_nv} {row["nivel_cert"]}</span></div>'
                f'<span style="background:{cor_st}22;color:{cor_st};border-radius:20px;padding:3px 12px;font-size:0.72rem;font-weight:600;border:1px solid {cor_st}44;">{label_st}</span></div>'
                f'<div style="margin-bottom:8px;">{crit_html}</div>'
                f'<div style="display:flex;gap:16px;font-size:0.7rem;color:#8B949E;">'
                f'<span>Doc: <b style="color:#E6EDF3;">{row["score_doc"]:.0f}%</b></span>'
                f'<span>Qualidade: <b style="color:#E6EDF3;">{row["score_qualidade"]:.1f}%</b></span>'
                f'<span>Ownership: <b style="color:#E6EDF3;">{row["score_ownership"]:.0f}%</b></span>'
                f'{validade_html}</div></div>',
                unsafe_allow_html=True
            )
            if is_aprovador and row["status_cert"]=="em_analise":
                ca2,cr2=st.columns(2)
                with ca2:
                    if st.button(f"✅ Certificar {row['table_name']}",key=f"cert_ap_{row['cert_id']}",use_container_width=True):
                        exe(f"UPDATE meridian_governanca.gd_certification SET status_cert='certificado',certificado_por='{esc(usuario)}',certificado_em=current_timestamp(),valido_ate=date_add(current_date(),365) WHERE cert_id='{row['cert_id']}'")
                        exe(f"UPDATE meridian_governanca.tabelas_metadata SET selo='certificado',atualizado_em=current_timestamp() WHERE schema_name='{row['schema_name']}' AND table_name='{row['table_name']}'")
                        st.success("✅ Certificado!"); st.cache_data.clear(); st.rerun()
                with cr2:
                    if st.button(f"❌ Rejeitar",key=f"cert_rej_{row['cert_id']}",use_container_width=True):
                        exe(f"UPDATE meridian_governanca.gd_certification SET status_cert='pendente',certificado_por='{esc(usuario)}',certificado_em=current_timestamp() WHERE cert_id='{row['cert_id']}'")
                        st.warning("↩️ Devolvido."); st.cache_data.clear(); st.rerun()
    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# 🔗 LINHAGEM — Origem e Destino dos Dados
# ════════════════════════════════════════════════════════════════════
elif pagina == "🔗 Linhagem":
    page_header("🔗","Linhagem de Dados","Rastreie a origem e o destino de cada ativo — do dado bruto ao produto final.")
    st.markdown("""<div style="background:#161B2299;border:1px solid #30363D;border-radius:8px;padding:10px 14px;margin-bottom:16px;"><div style="color:#8B949E;font-size:0.78rem;line-height:1.6;">A linhagem mostra como os dados fluem entre as camadas: Bronze (bruto) → Prata (tratado) → Ouro (pronto para uso).</div></div>""",unsafe_allow_html=True)
    df_lin=load_linhagem()
    if df_lin.empty:
        estado_vazio("🔗","Nenhuma linhagem cadastrada","A linhagem será exibida quando os relacionamentos entre ativos forem registrados.")
    else:
        CAMADA_COR={"bronze":"#CD7F32","prata":"#A8A9AD","ouro":"#C9A227"}
        CAMADA_X={"bronze":0.5,"prata":2.5,"ouro":4.5}
        k1,k2,k3=st.columns(3)
        b=df_lin["origem_tabela"][df_lin["origem_schema"]=="bronze"].nunique()
        p=df_lin["origem_tabela"][df_lin["origem_schema"]=="prata"].nunique()
        o=df_lin["destino_tabela"][df_lin["destino_schema"]=="ouro"].nunique()
        with k1: st.markdown(kpi(b,"Ativos Bronze","#CD7F32","🥉","Dados brutos de origem."),unsafe_allow_html=True)
        with k2: st.markdown(kpi(p,"Ativos Prata","#A8A9AD","🥈","Dados tratados."),unsafe_allow_html=True)
        with k3: st.markdown(kpi(o,"Ativos Ouro","#C9A227","🥇","Dados prontos para uso."),unsafe_allow_html=True)
        section_divider("MAPA VISUAL DE LINHAGEM")
        nos_o=df_lin[["origem_schema","origem_tabela"]].drop_duplicates().rename(columns={"origem_schema":"schema","origem_tabela":"tabela"})
        nos_d=df_lin[["destino_schema","destino_tabela"]].drop_duplicates().rename(columns={"destino_schema":"schema","destino_tabela":"tabela"})
        todos=pd.concat([nos_o,nos_d]).drop_duplicates().reset_index(drop=True)
        por_cam={}
        for _,n in todos.iterrows(): por_cam.setdefault(n["schema"],[]).append(n["tabela"])
        pos_nos={}
        for cam,tabs in por_cam.items():
            for i,t in enumerate(tabs): pos_nos[f"{cam}.{t}"]=(CAMADA_X.get(cam,1.5),i*1.3-(len(tabs)-1)*0.65)
        fig_lin=go.Figure()
        for _,row in df_lin.iterrows():
            ko=f"{row['origem_schema']}.{row['origem_tabela']}"; kd=f"{row['destino_schema']}.{row['destino_tabela']}"
            if ko in pos_nos and kd in pos_nos:
                x0,y0=pos_nos[ko]; x1,y1=pos_nos[kd]
                fig_lin.add_trace(go.Scatter(x=[x0,x1],y=[y0,y1],mode="lines",line=dict(color="#30363D",width=1.5),hovertext=row["descricao"],hoverinfo="text",showlegend=False))
        for chave,(x,y) in pos_nos.items():
            cam,tabela=chave.split(".",1); cor_n=CAMADA_COR.get(cam,"#8B949E")
            fig_lin.add_trace(go.Scatter(x=[x],y=[y],mode="markers+text",marker=dict(color=cor_n,size=16,line=dict(color="#0D1117",width=2)),text=[tabela],textposition="middle right",textfont=dict(color="#E6EDF3",size=10),hoverinfo="text",hovertext=chave,showlegend=False))
        for cam,(x_c,cor_c) in [("bronze",(0.5,"#CD7F32")),("prata",(2.5,"#A8A9AD")),("ouro",(4.5,"#C9A227"))]:
            ys=[p[1] for k,p in pos_nos.items() if k.startswith(cam)]
            if ys: fig_lin.add_annotation(x=x_c,y=max(ys)+1.2,text=f"🏷️ {cam.upper()}",showarrow=False,font=dict(color=cor_c,size=12),bgcolor="#0D1117",borderpad=4)
        fig_lin.update_layout(paper_bgcolor="#161B22",plot_bgcolor="#161B22",height=440,margin=dict(t=30,b=20,l=20,r=200),xaxis=dict(showgrid=False,zeroline=False,showticklabels=False,range=[-0.3,7]),yaxis=dict(showgrid=False,zeroline=False,showticklabels=False))
        st.plotly_chart(fig_lin,use_container_width=True)
        section_divider("DETALHAMENTO DAS TRANSFORMAÇÕES")
        f_lin=st.selectbox("Filtrar por origem",["Todas","bronze","prata"],key="lin_cam")
        df_lf=df_lin if f_lin=="Todas" else df_lin[df_lin["origem_schema"]==f_lin]
        for _,row in df_lf.iterrows():
            cor_o2=CAMADA_COR.get(row["origem_schema"],"#8B949E"); cor_d2=CAMADA_COR.get(row["destino_schema"],"#8B949E")
            tipo_lbl="⚙️ Transformação" if row["tipo_relacao"]=="transformacao" else "📥 Consumo"
            st.markdown(f'<div style="background:#161B22;border:1px solid #30363D;border-radius:10px;padding:12px 16px;margin-bottom:6px;"><div style="display:flex;align-items:center;gap:10px;margin-bottom:5px;"><span style="background:{cor_o2}22;color:{cor_o2};border-radius:6px;padding:4px 10px;font-size:0.75rem;font-weight:700;">{row["origem_schema"]}.{row["origem_tabela"]}</span><span style="color:#484F58;font-size:0.75rem;">{tipo_lbl} →</span><span style="background:{cor_d2}22;color:{cor_d2};border-radius:6px;padding:4px 10px;font-size:0.75rem;font-weight:700;">{row["destino_schema"]}.{row["destino_tabela"]}</span></div><div style="color:#8B949E;font-size:0.73rem;">{row["descricao"]}</div></div>',unsafe_allow_html=True)
    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# 📦 PRODUTOS DE DADOS
# ════════════════════════════════════════════════════════════════════
elif pagina == "📦 Produtos":
    page_header("📦","Produtos de Dados","Ativos empacotados e prontos para uso por áreas de negócio.")
    st.markdown("""<div style="background:#161B2299;border:1px solid #30363D;border-radius:8px;padding:10px 14px;margin-bottom:16px;"><div style="color:#8B949E;font-size:0.78rem;line-height:1.6;">Um Produto de Dados é um conjunto de ativos organizados para atender a uma necessidade específica do negócio, com finalidade, responsável e certificação definidos.</div></div>""",unsafe_allow_html=True)
    df_prod=load_produtos(); df_pat=load_produto_ativos()
    if df_prod.empty:
        estado_vazio("📦","Nenhum produto cadastrado","Os produtos de dados serão exibidos aqui quando cadastrados pela equipe de Governança.")
    else:
        ativos_total=df_pat["table_name"].nunique() if not df_pat.empty else 0
        k1,k2,k3,k4=st.columns(4)
        with k1: st.markdown(kpi(len(df_prod),"Produtos","#C9A227"),unsafe_allow_html=True)
        with k2: st.markdown(kpi(len(df_prod[df_prod["status"]=="ativo"]),"Ativos","#3FB950"),unsafe_allow_html=True)
        with k3: st.markdown(kpi(len(df_prod[df_prod["certificacao"]=="certificado"]),"Certificados","#C9A227"),unsafe_allow_html=True)
        with k4: st.markdown(kpi(ativos_total,"Ativos Vinculados","#58A6FF"),unsafe_allow_html=True)
        section_divider("CATÁLOGO DE PRODUTOS")
        fp1,fp2=st.columns(2)
        with fp1: fp_dom=st.selectbox("Domínio",["Todos"]+sorted([d for d in df_prod["dominio"].unique() if d]),key="fp_dom")
        with fp2: fp_st=st.selectbox("Status",["Todos","ativo","em_dev","inativo"],key="fp_st")
        df_pf=df_prod.copy()
        if fp_dom!="Todos": df_pf=df_pf[df_pf["dominio"]==fp_dom]
        if fp_st!="Todos":  df_pf=df_pf[df_pf["status"]==fp_st]
        if "prod_sel" not in st.session_state: st.session_state["prod_sel"]=None
        col_pl,col_pd=st.columns([1,2])
        CAMADA_COR2={"bronze":"#CD7F32","prata":"#A8A9AD","ouro":"#C9A227"}
        PAPEL_COR={"Principal":"#C9A227","Origem":"#58A6FF","Consumo":"#3FB950"}
        with col_pl:
            for _,row in df_pf.iterrows():
                cor_st={"ativo":"#3FB950","em_dev":"#C9A227","inativo":"#484F58"}.get(row["status"],"#8B949E")
                cor_cert={"certificado":"#C9A227","em_analise":"#58A6FF","pendente":"#8B949E"}.get(row["certificacao"],"#8B949E")
                ic_cert={"certificado":"🥇","em_analise":"🥈","pendente":"🥉"}.get(row["certificacao"],"")
                is_sel=st.session_state["prod_sel"]==row["produto_id"]
                ativos_p=df_pat[df_pat["produto_id"]==row["produto_id"]] if not df_pat.empty else pd.DataFrame()
                st.markdown(f'<div style="background:{"#C9A22708" if is_sel else "#161B22"};border:1px solid {"#C9A227" if is_sel else "#30363D"};border-radius:10px;padding:12px 14px;margin-bottom:4px;"><div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px;"><span style="color:#E6EDF3;font-weight:700;font-size:0.85rem;">{row["nome"]}</span><span style="color:{cor_st};font-size:0.65rem;font-weight:700;">● {row["status"]}</span></div><div style="color:#8B949E;font-size:0.72rem;margin-bottom:6px;">{row["finalidade"][:65]}...</div><div style="display:flex;gap:6px;"><span style="background:#C9A22722;color:#C9A227;border-radius:4px;padding:1px 6px;font-size:0.62rem;">{row["dominio"]}</span><span style="background:{cor_cert}22;color:{cor_cert};border-radius:4px;padding:1px 6px;font-size:0.62rem;">{ic_cert} {row["certificacao"]}</span><span style="background:#58A6FF22;color:#58A6FF;border-radius:4px;padding:1px 6px;font-size:0.62rem;">{len(ativos_p)} ativos</span></div></div>',unsafe_allow_html=True)
                if st.button(f'{"▼ Fechar" if is_sel else "▶ Ver detalhes"}',key=f"psel_{row['produto_id']}",use_container_width=True):
                    st.session_state["prod_sel"]=None if is_sel else row["produto_id"]; st.rerun()
        with col_pd:
            pid=st.session_state.get("prod_sel")
            if pid:
                row_p=df_pf[df_pf["produto_id"]==pid]
                if not row_p.empty:
                    p=row_p.iloc[0]; ativos_p=df_pat[df_pat["produto_id"]==pid] if not df_pat.empty else pd.DataFrame()
                    cor_st2={"ativo":"#3FB950","em_dev":"#C9A227","inativo":"#484F58"}.get(p["status"],"#8B949E")
                    cor_cert2={"certificado":"#C9A227","em_analise":"#58A6FF","pendente":"#8B949E"}.get(p["certificacao"],"#8B949E")
                    st.markdown(f'<div style="background:#161B22;border:1px solid #30363D;border-radius:12px;padding:20px;"><div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px;"><div><div style="color:#E6EDF3;font-size:1.1rem;font-weight:800;">{p["nome"]}</div><div style="color:#8B949E;font-size:0.72rem;margin-top:2px;">{p["dominio"]} · Produto de Dados</div></div><span style="background:{cor_cert2}22;color:{cor_cert2};border-radius:20px;padding:3px 12px;font-size:0.72rem;font-weight:600;border:1px solid {cor_cert2}44;">{"🥇 Certificado" if p["certificacao"]=="certificado" else "🥈 Em Análise" if p["certificacao"]=="em_analise" else "🥉 Pendente"}</span></div><div style="background:#0D1117;border-radius:8px;padding:12px;margin-bottom:10px;"><div style="color:#8B949E;font-size:0.6rem;font-weight:700;text-transform:uppercase;margin-bottom:4px;">FINALIDADE</div><div style="color:#E6EDF3;font-size:0.82rem;line-height:1.5;">{p["finalidade"]}</div></div><div style="background:#0D1117;border-radius:8px;padding:12px;margin-bottom:10px;"><div style="color:#8B949E;font-size:0.6rem;font-weight:700;text-transform:uppercase;margin-bottom:4px;">DESCRIÇÃO</div><div style="color:#E6EDF3;font-size:0.82rem;line-height:1.5;">{p["descricao"]}</div></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px;"><div style="background:#0D1117;border-radius:8px;padding:9px;"><div style="font-size:0.6rem;color:#8B949E;margin-bottom:2px;">RESPONSÁVEL</div><div style="color:#E6EDF3;font-size:0.78rem;">{p["responsavel"]}</div></div><div style="background:#0D1117;border-radius:8px;padding:9px;"><div style="font-size:0.6rem;color:#8B949E;margin-bottom:2px;">STATUS</div><div style="color:{cor_st2};font-size:0.78rem;font-weight:700;">{p["status"].replace("_"," ").title()}</div></div></div>',unsafe_allow_html=True)
                    if not ativos_p.empty:
                        st.markdown('<div style="background:#0D1117;border-radius:8px;padding:12px;"><div style="color:#8B949E;font-size:0.6rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">ATIVOS VINCULADOS</div>',unsafe_allow_html=True)
                        for _,at in ativos_p.iterrows():
                            cor_cam2=CAMADA_COR2.get(at["schema_name"],"#8B949E"); cor_pap2=PAPEL_COR.get(at["papel"],"#8B949E")
                            st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid #21262D;"><div><span style="color:#E6EDF3;font-size:0.75rem;">{at["table_name"]}</span><span style="background:{cor_cam2}22;color:{cor_cam2};border-radius:3px;padding:1px 5px;font-size:0.62rem;margin-left:5px;">{at["schema_name"]}</span></div><span style="background:{cor_pap2}22;color:{cor_pap2};border-radius:3px;padding:1px 7px;font-size:0.62rem;">{at["papel"]}</span></div>',unsafe_allow_html=True)
                        st.markdown('</div></div>',unsafe_allow_html=True)
                    else:
                        st.markdown('</div>',unsafe_allow_html=True)
            else:
                estado_vazio("📦","Selecione um produto","Clique em qualquer produto para ver detalhes e ativos vinculados.")
    copyright_footer()
