"""
app.py — Plataforma de Governança de Dados
Banco Meridian | v5.0
© Tereza Cristina — Todos os direitos reservados.
Reprodução proibida sem autorização expressa.
"""
import streamlit as st
import pandas as pd
import threading, time
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
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;0,700;1,400&family=Inter:wght@300;400;500;600;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box;}
html,body,.stApp{background:#F0F2F5 !important;font-family:'Inter',sans-serif !important;}
h1,h2,h3{font-family:'Lora',serif !important;font-weight:700 !important;color:#0D1B2A !important;}

/* ── Topbar fixa ── */
header[data-testid="stHeader"]{display:none !important;}
.gov-topbar{
    position:fixed !important;top:0 !important;left:0 !important;right:0 !important;
    height:52px !important;background:#0D1B2A !important;z-index:99999 !important;
    display:flex !important;align-items:center !important;padding:0 20px !important;gap:14px !important;
    box-shadow:0 2px 12px rgba(0,0,0,0.4) !important;border-bottom:1px solid #1A3A5C !important;}

/* ── Sidebar ── */
section[data-testid="stSidebar"]{
    background:#0D1B2A !important;border-right:1px solid #1A3A5C !important;
    min-width:220px !important;margin-top:52px !important;padding-top:0 !important;}
section[data-testid="stSidebar"] > div{padding-top:0 !important;}
section[data-testid="stSidebar"] *{color:#6B8299 !important;}
section[data-testid="stSidebar"] .stButton>button{
    background:transparent !important;color:#8DAFC8 !important;border:none !important;
    border-radius:7px !important;font-weight:500 !important;font-size:0.81rem !important;
    text-align:left !important;justify-content:flex-start !important;
    padding:8px 14px !important;width:100% !important;box-shadow:none !important;
    margin-bottom:1px !important;transition:background .15s,color .15s !important;}
section[data-testid="stSidebar"] .stButton>button:hover{background:#162035 !important;color:#D4C49A !important;}

/* ── Main content ── */
.main .block-container{
    padding-top:68px !important;max-width:100% !important;
    padding-left:1.5rem !important;padding-right:1.5rem !important;}

/* ── Componentes gerais ── */
.stButton>button{background:#1E4D9B !important;color:#FFFFFF !important;border:none !important;
    border-radius:8px !important;font-weight:600 !important;font-size:0.82rem !important;}
.stButton>button:hover{background:#1A4280 !important;}
.stTabs [data-baseweb="tab-list"]{background:#FFFFFF;border-radius:10px;padding:4px;gap:4px;border:1px solid #E2E8F0;}
.stTabs [data-baseweb="tab"]{border-radius:7px !important;color:#6B7280 !important;padding:7px 16px !important;font-size:0.82rem !important;font-weight:600 !important;}
.stTabs [aria-selected="true"]{background:#1E4D9B !important;color:#FFFFFF !important;}
.stSelectbox>div>div,.stTextInput>div>div>input,.stTextArea>div>div>textarea{background:#FFFFFF !important;border:1px solid #E2E8F0 !important;border-radius:8px !important;color:#0D1B2A !important;}
.stDataFrame{background:#FFFFFF !important;border-radius:10px !important;}
div[data-testid="stVerticalBlock"]{gap:0.4rem !important;}

/* ── Home: atalhos ── */
.atalho-btn .stButton>button{
    background:#FFFFFF !important;color:#1A202C !important;
    border:1px solid #E2E8F0 !important;border-radius:0 0 10px 10px !important;
    font-weight:600 !important;font-size:0.73rem !important;
    padding:6px 12px !important;text-align:center !important;
    justify-content:center !important;width:100% !important;
    box-shadow:none !important;border-top:1px solid #E8EDF5 !important;}
.atalho-btn .stButton>button:hover{background:#F0F4FF !important;color:#1E4D9B !important;}

/* ── Journey cards ── */
.nav-card-btn{display:none !important;}
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

# ─── KEEP-ALIVE ──────────────────────────────────────────────────────────────
# Roda uma vez por processo do servidor (cache_resource) e mantém o
# SQL Warehouse ativo enviando um SELECT 1 a cada 4 minutos.
@st.cache_resource
def _start_keepalive():
    def _ping():
        while True:
            time.sleep(240)   # 4 minutos — antes do timeout de idle (10 min)
            try:
                conn = get_conn()
                cur  = conn.cursor()
                cur.execute("SELECT 1")
                cur.close()
            except Exception:
                # Sessão expirou — limpa o cache para reconectar
                try: get_conn.clear()
                except: pass
    t = threading.Thread(target=_ping, daemon=True)
    t.start()
    return True

_start_keepalive()
# ─────────────────────────────────────────────────────────────────────────────

def _is_session_err(msg: str) -> bool:
    return "SessionHandle" in msg or ("Session" in msg and "closed" in msg)

@st.cache_data(ttl=300)
def qry(sql_str):
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute(sql_str)
        cols = [d[0] for d in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=cols), None
    except Exception as e:
        err = str(e)
        if _is_session_err(err):
            try: get_conn.clear(); qry.clear()
            except: pass
        return pd.DataFrame(), err

def exe(sql_str):
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute(sql_str)
        return True, None
    except Exception as e:
        err = str(e)
        if _is_session_err(err):
            try: get_conn.clear()
            except: pass
        return False, err

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
MENU_BASE = {
    "PESSOAL":        ["⚡ Meu Espaço"],
    "INÍCIO":         ["🏠 Início"],
    "CONHECIMENTO":   ["📖 Glossário", "🏛️ Domínios"],
    "DADOS":          ["📋 Catálogo", "🔗 Linhagem", "📦 Produtos"],
    "CONFIABILIDADE": ["🛡️ Scorecard", "🏆 Qualidade", "🥇 Certificação"],
}
MENU_OP = {
    "GESTÃO":         ["📊 Indicadores"],
    "OPERAÇÃO":       ["✏️ Curadoria", "🕐 Auditoria"],
}
MENU = {**MENU_BASE, **MENU_OP}

# ════════════════════════════════════════════════════════════════════
# CARREGAMENTO DE DADOS
# ════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def load_meta():
    df, err = qry("SELECT * FROM meridian_governanca.tabelas_metadata")
    if err and df.empty:
        st.session_state["_db_err"] = err
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
def load_timeline():
    df,_=qry("SELECT * FROM meridian_governanca.gd_solicitacoes_timeline ORDER BY iniciado_em DESC"); return df if df is not None else pd.DataFrame()
@st.cache_data(ttl=300)
def load_sla_snap():
    df,_=qry("SELECT * FROM meridian_governanca.gd_sla_atendimento_snapshot ORDER BY data_snapshot ASC"); return df if df is not None else pd.DataFrame()

@st.cache_data(ttl=300)
def load_solicitacoes_acesso():
    df,_ = qry("SELECT * FROM meridian_governanca.solicitacoes_acesso ORDER BY criado_em DESC")
    return df if df is not None else pd.DataFrame()

@st.cache_data(ttl=300)
def load_quality_dimensions():
    df,_ = qry("SELECT * FROM meridian_governanca.gd_quality_dimensions ORDER BY score_final DESC")
    return df if df is not None else pd.DataFrame()

@st.cache_data(ttl=300)
def load_cert():
    df,_ = qry("SELECT * FROM meridian_governanca.gd_certification ORDER BY score_qualidade DESC")
    return df if df is not None else pd.DataFrame()

@st.cache_data(ttl=300)
def load_snap():
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
# SIDEBAR — Navegação principal redesenhada
# ════════════════════════════════════════════════════════════════════
with st.sidebar:
    if "usuario" not in st.session_state:
        st.session_state["usuario"] = None

    if not st.session_state["usuario"]:
        st.markdown("""
        <div style="padding:28px 16px 16px;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:24px;">
                <div style="width:34px;height:34px;border-radius:8px;background:#C9A22722;border:1px solid #C9A22744;
                            display:flex;align-items:center;justify-content:center;
                            font-family:Lora,serif;font-weight:700;font-size:16px;color:#C9A227;">G</div>
                <div>
                    <div style="font-family:Lora,serif;font-size:13px;font-weight:700;color:#E2D4A8;letter-spacing:1.5px;">Governantes</div>
                    <div style="font-size:8.5px;color:#3A5068;letter-spacing:0.8px;text-transform:uppercase;">Governança de Dados</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)
        email = st.selectbox("Usuário", list(USUARIOS.keys()),
            format_func=lambda x: f"{USUARIOS[x]['nome']} · {USUARIOS[x]['perfil']}",
            label_visibility="collapsed")
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

    # ── Espaçamento inicial
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    # ── Navegação flat
    NAV_ITEMS = [
        ("🏠", "Início",                "🏠 Início"),
        ("📋", "Catálogo de Dados",     "📋 Catálogo"),
        ("📖", "Glossário de Negócio",  "📖 Glossário"),
        ("🏆", "Qualidade de Dados",    "🏆 Qualidade"),
        ("🔗", "Linhagem de Dados",     "🔗 Linhagem"),
        ("📬", "Solicitações",          "⚡ Meu Espaço"),
        ("📊", "Gestão e Indicadores",  "📊 Indicadores"),
    ]
    NAV_OP = [
        ("🏛️", "Domínios",     "🏛️ Domínios"),
        ("📦", "Produtos",     "📦 Produtos"),
        ("🛡️", "Scorecard",   "🛡️ Scorecard"),
        ("🥇", "Certificação", "🥇 Certificação"),
        ("✏️", "Curadoria",   "✏️ Curadoria"),
        ("🕐", "Auditoria",   "🕐 Auditoria"),
    ]

    nav_all = NAV_ITEMS + (NAV_OP if is_curador else [])

    for icon, label, dest in nav_all:
        is_active = st.session_state["pagina"] == dest
        if is_active:
            st.markdown(f"""
            <div style="background:linear-gradient(90deg,#1E4D9B22,#1E4D9B0A);
                        border-left:3px solid #1E4D9B;border-radius:0 7px 7px 0;
                        padding:8px 14px;display:flex;align-items:center;gap:10px;
                        margin:1px 8px 1px 0;font-size:0.81rem;font-weight:700;color:#FFFFFF;">
                <span style="font-size:0.9rem;">{icon}</span><span>{label}</span>
            </div>""", unsafe_allow_html=True)
        else:
            if st.button(f"{icon}  {label}", key=f"nav_{dest}_{label}", use_container_width=True):
                st.session_state["pagina"] = dest
                for k in ["gid_sel","cat_sel","dom_sel","sc_pilar"]:
                    st.session_state.pop(k, None)
                st.rerun()

    # ── Perfil (rodapé)
    iniciais_u = "".join([n[0].upper() for n in u["nome"].split()[:2]])
    st.markdown(f"""
    <div style="position:absolute;bottom:0;left:0;right:0;
                border-top:1px solid #1A3A5C;padding:14px 14px 16px;
                background:#0D1B2A;">
        <div style="font-size:0.55rem;text-transform:uppercase;letter-spacing:1.5px;
                    color:#3A5068;margin-bottom:10px;font-weight:700;">Perfil Atual</div>
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:32px;height:32px;border-radius:50%;background:{cor}22;
                        border:1.5px solid {cor}55;display:flex;align-items:center;
                        justify-content:center;color:{cor};font-weight:800;
                        font-size:12px;flex-shrink:0;">{iniciais_u}</div>
            <div style="overflow:hidden;">
                <div style="color:#C8D6E5;font-size:0.78rem;font-weight:700;
                            white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{u['nome']}</div>
                <div style="color:{cor};font-size:0.67rem;">{PERFIL_LABEL[perfil]}</div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)
    st.markdown("<div style='height:106px;'></div>", unsafe_allow_html=True)
    if st.button("↩ Trocar perfil", key="logout", use_container_width=True):
        st.session_state["usuario"] = None
        st.rerun()

# ════════════════════════════════════════════════════════════════════
# TOPBAR — Cabeçalho institucional fixo
# ════════════════════════════════════════════════════════════════════
_nome_tb  = st.session_state.get("nome_atual", "")
_perf_tb  = st.session_state.get("perfil_atual", "consultante")
_perf_lbl = PERFIL_LABEL.get(_perf_tb, "")
_iniciais = "".join([n[0].upper() for n in _nome_tb.split()[:2]]) if _nome_tb else "U"
_cor_tb   = PERFIL_COR.get(_perf_tb, "#58A6FF")

st.markdown(f"""
<div class="gov-topbar">
    <!-- Logo -->
    <div style="display:flex;align-items:center;gap:10px;min-width:190px;">
        <div style="width:30px;height:30px;border-radius:7px;background:#C9A22722;border:1px solid #C9A22744;
                    display:flex;align-items:center;justify-content:center;
                    font-family:Lora,serif;font-weight:700;font-size:15px;color:#C9A227;flex-shrink:0;">G</div>
        <div>
            <div style="font-family:Lora,serif;font-size:12.5px;font-weight:700;color:#E2D4A8;letter-spacing:1.5px;line-height:1.2;">Governantes</div>
            <div style="font-size:8px;color:#3A5068;letter-spacing:0.8px;text-transform:uppercase;line-height:1.2;">Governança de Dados & IA</div>
        </div>
    </div>
    <!-- Jornadas -->
    <div style="display:flex;align-items:center;gap:6px;margin:0 12px;">
        <span style="color:#2A4A6A;font-size:0.68rem;font-weight:600;padding:4px 10px;border-radius:20px;border:1px solid #1A3A5C;cursor:pointer;white-space:nowrap;" title="Catálogo e descoberta de ativos">🔍 Descobrir</span>
        <span style="color:#2A4A6A;font-size:0.68rem;font-weight:600;padding:4px 10px;border-radius:20px;border:1px solid #1A3A5C;cursor:pointer;white-space:nowrap;" title="Glossário e definições">📖 Entender</span>
        <span style="color:#2A4A6A;font-size:0.68rem;font-weight:600;padding:4px 10px;border-radius:20px;border:1px solid #1A3A5C;cursor:pointer;white-space:nowrap;" title="Qualidade e scorecard">🛡️ Confiar</span>
        <span style="color:#2A4A6A;font-size:0.68rem;font-weight:600;padding:4px 10px;border-radius:20px;border:1px solid #1A3A5C;cursor:pointer;white-space:nowrap;" title="Curadoria e solicitações">⚡ Agir</span>
        <span style="color:#2A4A6A;font-size:0.68rem;font-weight:600;padding:4px 10px;border-radius:20px;border:1px solid #1A3A5C;cursor:pointer;white-space:nowrap;" title="Indicadores e gestão">📊 Decidir</span>
    </div>
    <!-- Busca -->
    <div style="flex:1;max-width:380px;">
        <div style="background:#162035;border:1px solid #1E3A5A;border-radius:8px;
                    padding:6px 14px;display:flex;align-items:center;gap:8px;">
            <span style="color:#3A5068;font-size:12px;">🔍</span>
            <span style="color:#3A5068;font-size:0.78rem;">Buscar dados, termos, regras...</span>
        </div>
    </div>
    <!-- Usuário -->
    <div style="display:flex;align-items:center;gap:10px;margin-left:auto;flex-shrink:0;">
        <span style="color:#3A5068;font-size:1rem;cursor:pointer;" title="Notificações">🔔</span>
        <div style="text-align:right;display:none;">
            <div style="color:#C8D6E5;font-size:0.75rem;font-weight:700;line-height:1.2;">{_nome_tb}</div>
            <div style="color:{_cor_tb};font-size:0.65rem;line-height:1.2;">{_perf_lbl}</div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;">
            <div style="color:#C8D6E5;font-size:0.73rem;font-weight:700;line-height:1.2;">{_nome_tb}</div>
            <div style="color:{_cor_tb};font-size:0.63rem;line-height:1.2;">{_perf_lbl}</div>
        </div>
        <div style="width:30px;height:30px;border-radius:50%;background:{_cor_tb}22;
                    border:1.5px solid {_cor_tb}55;display:flex;align-items:center;
                    justify-content:center;color:{_cor_tb};font-weight:800;font-size:11px;flex-shrink:0;">{_iniciais}</div>
    </div>
</div>
""", unsafe_allow_html=True)

pagina       = st.session_state.get("pagina","🏠 Início")
usuario      = st.session_state["usuario"]
u            = USUARIOS[usuario]
perfil       = u["perfil"]
is_curador   = perfil in ["curador","aprovador"]
is_aprovador = perfil == "aprovador"

# ════════════════════════════════════════════════════════════════════
# 🏠 INÍCIO — Plataforma de Governança de Dados
# ════════════════════════════════════════════════════════════════════
if pagina == "🏠 Início":

    # ── Dados para a home ────────────────────────────────────────────
    df_meta   = load_meta()
    df_gloss  = load_glossario()
    df_cert   = load_cert()
    df_qual   = load_quality_dimensions()
    df_sol_ac = load_solicitacoes_acesso()
    df_sol_qu = load_solicitacoes_qualidade()
    df_tl     = load_timeline()

    if df_meta.empty and st.session_state.get("_db_err"):
        st.warning(f"⚠️ Databricks indisponível. Detalhe: `{st.session_state['_db_err'][:200]}`")

    # ── KPIs ─────────────────────────────────────────────────────────
    total_ativos = len(df_meta)  if not df_meta.empty else 0
    total_termos = len(df_gloss) if not df_gloss.empty else 0
    qual_media   = round(df_qual["score_final"].mean(), 1) if not df_qual.empty and "score_final" in df_qual.columns else None
    qual_str     = f"{qual_media}%" if qual_media is not None else "—"

    STATUS_CLOSED = {"concluido","aprovado","cancelado","concluída","aprovada","encerrado"}
    sol_abertas = 0
    if not df_sol_ac.empty and "status" in df_sol_ac.columns:
        sol_abertas += len(df_sol_ac[~df_sol_ac["status"].str.lower().isin(STATUS_CLOSED)])
    if not df_sol_qu.empty and "status" in df_sol_qu.columns:
        sol_abertas += len(df_sol_qu[~df_sol_qu["status"].str.lower().isin(STATUS_CLOSED)])

    # ══════════════════════════════════════════════════════════════════
    # A. BANNER
    # ══════════════════════════════════════════════════════════════════
    st.markdown("""
    <div style="background:linear-gradient(105deg,#0D1B2A 40%,#0D1B2AB8 60%,#1B4A6B66 80%),
                url('https://images.unsplash.com/photo-1506905925346-21bda4d32df4?auto=format&fit=crop&w=1400&q=80') center/cover no-repeat;
                border-radius:14px;padding:38px 36px 34px;margin-bottom:16px;
                position:relative;min-height:170px;overflow:hidden;
                display:flex;align-items:center;justify-content:space-between;gap:24px;">
        <div style="flex:1;min-width:0;max-width:52%;">
            <div style="color:#5A8AAA;font-size:0.62rem;letter-spacing:3px;
                        text-transform:uppercase;margin-bottom:10px;font-weight:700;">
                PLATAFORMA DE GOVERNANÇA DE DADOS
            </div>
            <div style="color:#FFFFFF;font-size:1.7rem;font-weight:800;line-height:1.25;
                        margin-bottom:10px;font-family:'Lora',serif;letter-spacing:-0.3px;">
                Dados bem governados<br>impulsionam grandes decisões
            </div>
            <div style="color:#7AAABF;font-size:0.84rem;line-height:1.6;">
                Encontre, entenda, confie e aja sobre os dados da sua organização.
            </div>
        </div>
        <div style="flex-shrink:0;background:rgba(13,27,42,0.88);border:1px solid #1E3A5C;
                    border-radius:12px;padding:18px 20px;width:210px;
                    backdrop-filter:blur(10px);">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
                <span style="font-size:1.2rem;">📊</span>
                <span style="color:#C9A227;font-size:0.8rem;font-weight:700;">Nossa missão</span>
            </div>
            <div style="color:#6A8EA8;font-size:0.71rem;line-height:1.6;">
                Transformar dados em confiança para impulsionar decisões que geram valor real para a organização.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    # B. ATALHOS — 5 cards horizontais
    # ══════════════════════════════════════════════════════════════════
    ATALHOS = [
        ("📋","Catálogo de Dados",    "📋 Catálogo",   "Encontre e explore ativos de dados",    "#1E6FBF"),
        ("📖","Glossário de Negócio", "📖 Glossário",   "Veja termos, conceitos e regras",        "#C9A227"),
        ("🏆","Qualidade de Dados",   "🏆 Qualidade",   "Monitore a saúde e aponte problemas",   "#3FB950"),
        ("🔗","Linhagem de Dados",    "🔗 Linhagem",    "Veja a origem e o fluxo dos dados",     "#BC8CFF"),
        ("📬","Solicitações",         "⚡ Meu Espaço",  "Peça acessos e melhorias de qualidade", "#FF8C42"),
    ]
    sc_cols = st.columns(5, gap="small")
    for i, (ic, tit, dest, desc, cor_sc) in enumerate(ATALHOS):
        with sc_cols[i]:
            st.markdown(f"""
            <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:10px 10px 0 0;
                        padding:14px 14px 10px;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                <div style="font-size:1.5rem;margin-bottom:7px;">{ic}</div>
                <div style="color:#1A202C;font-weight:700;font-size:0.8rem;
                            margin-bottom:4px;line-height:1.3;">{tit}</div>
                <div style="color:#718096;font-size:0.7rem;line-height:1.4;">{desc}</div>
            </div>""", unsafe_allow_html=True)
            st.markdown('<div class="atalho-btn">', unsafe_allow_html=True)
            if st.button(f"→ Acessar", key=f"sc_{i}", use_container_width=True):
                st.session_state["pagina"] = dest
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    # C. PANORAMA EXECUTIVO
    # ══════════════════════════════════════════════════════════════════
    st.markdown("""
    <div style="font-size:0.6rem;font-weight:800;text-transform:uppercase;letter-spacing:2px;
                color:#94A3B8;margin-bottom:10px;">Panorama Geral</div>
    """, unsafe_allow_html=True)

    pan_left, pan_mid, pan_right = st.columns([2.2, 2.8, 2.0], gap="small")

    # ── KPI tiles ────────────────────────────────────────────────────
    with pan_left:
        st.markdown("""
        <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;
                    padding:16px 18px;height:100%;box-shadow:0 1px 4px rgba(0,0,0,0.05);">
            <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;
                        letter-spacing:1.5px;color:#94A3B8;margin-bottom:14px;">Indicadores</div>
        """, unsafe_allow_html=True)

        kpi_data = [
            (total_ativos,  "Ativos de Dados",      "#1E4D9B", "🗂️"),
            (total_termos,  "Termos de Negócio",    "#C9A227", "📖"),
            (qual_str,      "Qualidade Média",       "#3FB950", "🛡️"),
            (sol_abertas,   "Solicitações em Aberto","#F97316", "📬"),
        ]
        for val, lbl, cor_k, ic_k in kpi_data:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:9px 0;
                        border-bottom:1px solid #F1F5F9;">
                <div style="width:34px;height:34px;border-radius:8px;background:{cor_k}14;
                            display:flex;align-items:center;justify-content:center;
                            font-size:1rem;flex-shrink:0;">{ic_k}</div>
                <div style="flex:1;min-width:0;">
                    <div style="color:#64748B;font-size:0.65rem;">{lbl}</div>
                    <div style="color:{cor_k};font-size:1.35rem;font-weight:800;line-height:1.2;">{val}</div>
                </div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Qualidade por Domínio ────────────────────────────────────────
    with pan_mid:
        st.markdown("""
        <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;
                    padding:16px 18px;box-shadow:0 1px 4px rgba(0,0,0,0.05);">
            <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;
                        letter-spacing:1.5px;color:#94A3B8;margin-bottom:12px;">Qualidade por Domínio</div>
        """, unsafe_allow_html=True)

        if not df_qual.empty and "dominio" in df_qual.columns and "score_final" in df_qual.columns:
            dom_qual = df_qual.groupby("dominio")["score_final"].mean().reset_index()
            dom_qual = dom_qual.sort_values("score_final", ascending=False).head(7)
            CORES_DOM = ["#1E4D9B","#3FB950","#BC8CFF","#F97316","#C9A227","#F85149","#58A6FF"]
            for idx, row in dom_qual.iterrows():
                sc = round(float(row["score_final"]), 1)
                cor_d = CORES_DOM[idx % len(CORES_DOM)]
                cor_bar = "#3FB950" if sc >= 80 else "#C9A227" if sc >= 60 else "#F85149"
                st.markdown(f"""
                <div style="margin-bottom:9px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;">
                        <div style="color:#334155;font-size:0.73rem;font-weight:600;
                                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:65%;">{row['dominio']}</div>
                        <div style="color:{cor_bar};font-size:0.73rem;font-weight:800;margin-left:6px;">{sc}%</div>
                    </div>
                    <div style="background:#F1F5F9;border-radius:99px;height:5px;overflow:hidden;">
                        <div style="width:{sc}%;height:100%;background:{cor_bar};border-radius:99px;"></div>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#94A3B8;font-size:0.78rem;padding:20px 0;text-align:center;">Dados não disponíveis</div>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Rosca Solicitações ───────────────────────────────────────────
    with pan_right:
        st.markdown("""
        <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;
                    padding:16px 18px;box-shadow:0 1px 4px rgba(0,0,0,0.05);">
            <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;
                        letter-spacing:1.5px;color:#94A3B8;margin-bottom:10px;">Status das Solicitações</div>
        """, unsafe_allow_html=True)

        frames = []
        for df_s in [df_sol_ac, df_sol_qu]:
            if not df_s.empty and "status" in df_s.columns:
                frames.append(df_s[["status"]])
        if frames:
            df_all_sol = pd.concat(frames, ignore_index=True)
            st._df_status = df_all_sol  # avoid unused warning
            status_counts = df_all_sol["status"].value_counts().reset_index()
            status_counts.columns = ["status","total"]
            STATUS_COLORS = {
                "pendente":"#F97316","em_analise":"#3B82F6","aprovado":"#3FB950",
                "concluido":"#1E4D9B","cancelado":"#94A3B8","em_revisao":"#BC8CFF",
                "reprovado":"#F85149","concluída":"#1E4D9B","aprovada":"#3FB950",
            }
            cores_rosca = [STATUS_COLORS.get(s,"#CBD5E1") for s in status_counts["status"]]
            total_sol = status_counts["total"].sum()

            fig_donut = go.Figure(go.Pie(
                labels=status_counts["status"],
                values=status_counts["total"],
                hole=0.62,
                marker=dict(colors=cores_rosca, line=dict(color="#FFFFFF", width=2)),
                textinfo="none",
                hovertemplate="%{label}: %{value}<extra></extra>",
            ))
            fig_donut.add_annotation(
                text=f"<b>{total_sol}</b>",
                x=0.5, y=0.55, showarrow=False, font=dict(size=22, color="#0D1B2A"))
            fig_donut.add_annotation(
                text="total", x=0.5, y=0.4, showarrow=False,
                font=dict(size=10, color="#94A3B8"))
            fig_donut.update_layout(
                showlegend=False, margin=dict(t=0,b=0,l=0,r=0),
                height=150, paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar":False})

            # Legenda
            for _, row in status_counts.iterrows():
                cor_l = STATUS_COLORS.get(row["status"],"#CBD5E1")
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                    <div style="width:8px;height:8px;border-radius:50%;background:{cor_l};flex-shrink:0;"></div>
                    <div style="color:#475569;font-size:0.67rem;flex:1;">{row['status']}</div>
                    <div style="color:#0D1B2A;font-size:0.73rem;font-weight:700;">{row['total']}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#94A3B8;font-size:0.78rem;padding:20px 0;text-align:center;">Sem solicitações registradas</div>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    # D. ÁREA OPERACIONAL — 3 colunas
    # ══════════════════════════════════════════════════════════════════
    st.markdown("""
    <div style="font-size:0.6rem;font-weight:800;text-transform:uppercase;letter-spacing:2px;
                color:#94A3B8;margin-bottom:10px;">Área Operacional</div>
    """, unsafe_allow_html=True)

    op1, op2, op3 = st.columns(3, gap="small")

    # ── Ativos de destaque ────────────────────────────────────────────
    with op1:
        st.markdown("""
        <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;
                    padding:14px 16px;box-shadow:0 1px 4px rgba(0,0,0,0.05);">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;
                            letter-spacing:1.5px;color:#94A3B8;">Ativos em Destaque</div>
                <span style="font-size:0.6rem;color:#94A3B8;font-style:italic;">por qualidade</span>
            </div>
        """, unsafe_allow_html=True)

        if not df_meta.empty:
            # Enriquecer com qualidade se disponível
            ativos_dest = df_meta.copy()
            if not df_cert.empty and "dominio" in df_cert.columns and "score_qualidade" in df_cert.columns:
                dom_score = df_cert.groupby("dominio")["score_qualidade"].mean()
                ativos_dest["_score"] = ativos_dest["dominio"].map(dom_score).fillna(0)
                ativos_dest = ativos_dest.sort_values("_score", ascending=False)
            exibir_ativos = ativos_dest[["table_name","dominio"]].head(5)
            for _, row in exibir_ativos.iterrows():
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:8px;padding:7px 0;
                            border-bottom:1px solid #F8FAFC;">
                    <span style="font-size:0.9rem;">🗂️</span>
                    <div style="flex:1;min-width:0;">
                        <div style="color:#1E293B;font-size:0.72rem;font-weight:600;
                                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{row['table_name']}</div>
                        <div style="color:#94A3B8;font-size:0.63rem;">{row['dominio']}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#94A3B8;font-size:0.75rem;padding:10px 0;">Sem dados disponíveis</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Pendências dos meus dados ─────────────────────────────────────
    with op2:
        st.markdown("""
        <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;
                    padding:14px 16px;box-shadow:0 1px 4px rgba(0,0,0,0.05);">
            <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;
                        letter-spacing:1.5px;color:#94A3B8;margin-bottom:10px;">Pendências Abertas</div>
        """, unsafe_allow_html=True)

        pendencias = []
        if not df_sol_ac.empty and "status" in df_sol_ac.columns:
            pend_ac = df_sol_ac[~df_sol_ac["status"].str.lower().isin(STATUS_CLOSED)]
            for _, row in pend_ac.head(3).iterrows():
                tipo = "Acesso"
                desc = str(row.get("tabela",""))[:40] if "tabela" in row else "—"
                st_p = row.get("status","—")
                pendencias.append((tipo, desc, st_p))
        if not df_sol_qu.empty and "status" in df_sol_qu.columns:
            pend_qu = df_sol_qu[~df_sol_qu["status"].str.lower().isin(STATUS_CLOSED)]
            for _, row in pend_qu.head(3).iterrows():
                tipo = "Qualidade"
                desc = str(row.get("descricao",""))[:40] if "descricao" in row else "—"
                st_p = row.get("status","—")
                pendencias.append((tipo, desc, st_p))

        STATUS_COR_PILL = {"pendente":"#F97316","em_analise":"#3B82F6","em_revisao":"#BC8CFF"}
        if pendencias:
            for tipo_p, desc_p, status_p in pendencias[:5]:
                cor_p = STATUS_COR_PILL.get(status_p.lower(),"#94A3B8")
                tipo_ic = "📬" if tipo_p=="Acesso" else "🛡️"
                st.markdown(f"""
                <div style="padding:7px 0;border-bottom:1px solid #F8FAFC;">
                    <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px;">
                        <span style="font-size:0.85rem;">{tipo_ic}</span>
                        <span style="color:#1E293B;font-size:0.71rem;font-weight:600;">{tipo_p}</span>
                        <span style="background:{cor_p}18;color:{cor_p};border-radius:20px;
                                     padding:1px 7px;font-size:0.6rem;font-weight:700;margin-left:auto;">{status_p}</span>
                    </div>
                    <div style="color:#64748B;font-size:0.65rem;padding-left:22px;">{desc_p}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#94A3B8;font-size:0.75rem;padding:16px 0;text-align:center;">✓ Nenhuma pendência em aberto</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Últimas atividades ────────────────────────────────────────────
    with op3:
        st.markdown("""
        <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;
                    padding:14px 16px;box-shadow:0 1px 4px rgba(0,0,0,0.05);">
            <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;
                        letter-spacing:1.5px;color:#94A3B8;margin-bottom:10px;">Últimas Atividades</div>
        """, unsafe_allow_html=True)

        if not df_tl.empty:
            tl_show = df_tl.head(6)
            for _, row in tl_show.iterrows():
                tipo_a = str(row.get("tipo_solicitacao", row.get("tipo","—")))[:30]
                status_a = str(row.get("status","—"))
                responsavel = str(row.get("responsavel", row.get("solicitante","—")))[:20]
                data_a = ""
                for dc in ["iniciado_em","criado_em","data","updated_at"]:
                    if dc in row and pd.notna(row[dc]):
                        try:
                            data_a = pd.to_datetime(row[dc]).strftime("%d/%m %H:%M")
                        except:
                            data_a = str(row[dc])[:10]
                        break
                cor_a = "#3FB950" if "conclu" in status_a.lower() or "aprova" in status_a.lower() \
                        else "#F97316" if "penden" in status_a.lower() else "#94A3B8"
                st.markdown(f"""
                <div style="padding:7px 0;border-bottom:1px solid #F8FAFC;display:flex;align-items:flex-start;gap:8px;">
                    <div style="width:7px;height:7px;border-radius:50%;background:{cor_a};
                                margin-top:4px;flex-shrink:0;"></div>
                    <div style="flex:1;min-width:0;">
                        <div style="color:#1E293B;font-size:0.71rem;font-weight:600;
                                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{tipo_a}</div>
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:2px;">
                            <span style="color:#94A3B8;font-size:0.62rem;">{responsavel}</span>
                            <span style="color:#94A3B8;font-size:0.6rem;">{data_a}</span>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#94A3B8;font-size:0.75rem;padding:16px 0;text-align:center;">Sem atividades registradas</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    # E. JORNADAS — 5 cards de navegação
    # ══════════════════════════════════════════════════════════════════
    st.markdown("""
    <div style="font-size:0.6rem;font-weight:800;text-transform:uppercase;letter-spacing:2px;
                color:#94A3B8;margin-bottom:10px;">Jornadas de Exploração</div>
    """, unsafe_allow_html=True)

    JORNADAS = [
        ("📋","Busca e Catálogo de Dados",   "📋 Catálogo",  "#1E4D9B",
         "Explore o inventário de ativos, filtros e metadados da organização."),
        ("🗂️","Detalhe do Ativo de Dados",   "📋 Catálogo",  "#7C3AED",
         "Acesse informações técnicas, responsáveis e qualidade de cada ativo."),
        ("🏆","Qualidade de Dados",           "🏆 Qualidade", "#059669",
         "Veja as dimensões de qualidade, domínios e indicadores registrados."),
        ("🔗","Linhagem e Atividades",        "🔗 Linhagem",  "#B45309",
         "Rastreie a origem, o fluxo e as transformações dos dados."),
        ("📬","Solicitações e Tarefas",       "⚡ Meu Espaço","#DC2626",
         "Gerencie acessos, relatos de qualidade e suas tarefas pendentes."),
    ]

    j_cols = st.columns(5, gap="small")
    for i, (ic_j, tit_j, dest_j, cor_j, desc_j) in enumerate(JORNADAS):
        with j_cols[i]:
            st.markdown(f"""
            <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;
                        overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.06);">
                <div style="background:{cor_j};padding:14px 14px 12px;min-height:70px;">
                    <div style="font-size:1.6rem;margin-bottom:5px;">{ic_j}</div>
                    <div style="color:rgba(255,255,255,0.95);font-size:0.75rem;
                                font-weight:700;line-height:1.3;">{tit_j}</div>
                </div>
                <div style="padding:10px 14px;">
                    <div style="color:#64748B;font-size:0.68rem;line-height:1.5;
                                min-height:44px;">{desc_j}</div>
                </div>
            </div>""", unsafe_allow_html=True)
            st.markdown('<div class="atalho-btn">', unsafe_allow_html=True)
            if st.button("→ Explorar", key=f"jrn_{i}", use_container_width=True):
                st.session_state["pagina"] = dest_j
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

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

                # Mantém a seleção sincronizada com a lista filtrada.
                # Evita exibir detalhes de um conceito que já não aparece nos resultados.
                ids_visiveis = df_gf["glossary_id"].tolist() if not df_gf.empty else []
                if st.session_state.get("gid_sel") not in ids_visiveis:
                    st.session_state["gid_sel"] = ids_visiveis[0] if ids_visiveis else None

                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

                if df_gf.empty:
                    st.session_state["gid_sel"] = None
                    estado_vazio("🔍","Nenhum conceito encontrado","Tente outros termos de busca ou ajuste os filtros.")
                else:
                    conceitos_por_id = {str(r["glossary_id"]): r for _, r in df_gf.iterrows()}
                    st.radio(
                        "Selecionar conceito",
                        options=list(conceitos_por_id.keys()),
                        format_func=lambda cid: f"{conceitos_por_id[cid]['termo']} · {conceitos_por_id[cid]['dominio']} · {str(conceitos_por_id[cid]['status']).replace('_', ' ')}",
                        key="gid_sel",
                        label_visibility="collapsed",
                    )

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
                                    <div style="color:#E6EDF3;font-size:0.78rem;">{row.get('owner','—')}</div>
                                </div>
                                <div style="background:#0D1117;border-radius:8px;padding:9px;">
                                    <div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;letter-spacing:1px;">CRIADO POR</div>
                                    <div style="color:#E6EDF3;font-size:0.78rem;">{row.get('criado_por','—')}</div>
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
        with f1: f_dom = st.selectbox("Domínio",["Todos"]+sorted([str(d) for d in df_cat["dominio"].dropna().unique() if str(d).strip() and str(d) != "nan"]),key="cf_dom")
        with f2: f_cam = st.selectbox("Camada",["Todas"]+sorted(df_cat["schema_name"].unique().tolist()),key="cf_cam")
        with f3: f_own = st.selectbox("Responsável",["Todos"]+sorted([str(o) for o in df_cat["data_owner"].dropna().unique() if str(o).strip() and str(o) != "nan"]),key="cf_own")
        with f4: f_stw = st.selectbox("Gestor",["Todos"]+sorted([str(s) for s in df_cat["data_steward"].dropna().unique() if str(s).strip() and str(s) != "nan"]),key="cf_stw")
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
                        # Cartão nativo: evita HTML customizado quebrado e o literal </div>
                        # que aparecia na interface. A ação fica curta e sem botão gigante.
                        with st.container(border=True):
                            st.markdown(f"**{item['table_name']}**")
                            st.markdown(f":{('green' if item['score_completude'] == 100 else 'orange' if item['score_completude'] >= 60 else 'red')}[{item['score_completude']}% documentação]")
                            st.caption(desc)
                            tags = [str(item["schema_name"])]
                            if item["dominio"]:
                                tags.append(str(item["dominio"]))
                            if str(item.get("classificacao","")).lower() in ("pii","sensível","sensivel"):
                                tags.append("🔒 Dado pessoal")
                            st.caption(" · ".join(tags))
                            if st.button(
                                "Fechar detalhes" if is_sel else "Detalhes",
                                key=f"csel_{chave}",
                                use_container_width=True,
                                type="secondary",
                            ):
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
                                <div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;margin-bottom:2px;">CLASSIFICAÇÃO</div>
                                <div style="color:#E6EDF3;font-size:0.78rem;">{item.get('classificacao') or '—'}</div>
                            </div>
                            <div style="background:#0D1117;border-radius:8px;padding:8px;">
                                <div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;margin-bottom:2px;">STATUS</div>
                                <div style="color:#E6EDF3;font-size:0.78rem;">{item.get('status') or '—'}</div>
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
    page_header("🏛️", "Domínios de Negócio", "Responsabilidades, ativos e conceitos organizados por área de negócio.")

    df_dom = load_meta()
    df_glos = load_glossario()

    if df_dom.empty:
        estado_vazio("🏛️", "Nenhum domínio encontrado", "Verifique se existem ativos catalogados com domínio definido.")
    else:
        dominios = sorted([
            str(d) for d in df_dom["dominio"].dropna().unique()
            if str(d).strip() and str(d).lower() != "nan"
        ])
        total_owners = df_dom["data_owner"].replace("", pd.NA).dropna().nunique()
        total_stewards = df_dom["data_steward"].replace("", pd.NA).dropna().nunique()
        glos_valid = df_glos if not df_glos.empty else pd.DataFrame(columns=["dominio", "status", "termo"])
        n_conceitos = glos_valid["termo"].nunique() if not glos_valid.empty else 0
        n_homologados = glos_valid[glos_valid["status"] == "homologado"]["termo"].nunique() if not glos_valid.empty else 0
        pct_homologados = round(n_homologados / n_conceitos * 100) if n_conceitos else 0

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(kpi(len(dominios), "Domínios", "#C9A227", tooltip="Domínios presentes nos ativos catalogados."), unsafe_allow_html=True)
        with k2:
            st.markdown(kpi(total_owners, "Owners distintos", "#58A6FF", tooltip="Quantidade de responsáveis distintos associados aos ativos."), unsafe_allow_html=True)
        with k3:
            st.markdown(kpi(total_stewards, "Stewards distintos", "#BC8CFF", tooltip="Quantidade de gestores operacionais distintos associados aos ativos."), unsafe_allow_html=True)
        with k4:
            st.markdown(kpi(f"{pct_homologados}%", "Conceitos homologados", "#3FB950", tooltip="Percentual de conceitos distintos homologados."), unsafe_allow_html=True)

        st.caption("Selecione um domínio para consultar seus responsáveis, ativos e conceitos. A documentação média mede preenchimento de metadados, não qualidade efetiva dos dados.")

        icones_dom = {"Crédito": "💳", "Pagamentos": "💸", "Clientes": "👥", "Compliance": "🛡️", "Produtos": "📦"}
        if st.session_state.get("dom_sel") not in dominios:
            st.session_state["dom_sel"] = dominios[0] if dominios else None

        col_lista, col_detalhe = st.columns([1, 1.6], gap="large")
        with col_lista:
            st.markdown("#### Domínios")
            for dom in dominios:
                df_d = df_dom[df_dom["dominio"] == dom]
                score = float(df_d["score_completude"].fillna(0).mean()) if not df_d.empty else 0
                n_t = glos_valid[glos_valid["dominio"] == dom]["termo"].nunique() if not glos_valid.empty else 0
                selected = st.session_state["dom_sel"] == dom
                with st.container(border=True):
                    row_name, row_score = st.columns([3, 1])
                    with row_name:
                        st.markdown(f"**{icones_dom.get(dom, '🏛️')} {dom}**")
                    with row_score:
                        st.markdown(f"**{score:.0f}%**")
                    st.caption(f"{len(df_d)} ativos · {n_t} conceitos")
                    if st.button("Selecionado" if selected else "Ver domínio", key=f"domsel_{dom}", use_container_width=True, type="primary" if selected else "secondary"):
                        st.session_state["dom_sel"] = dom
                        st.rerun()

        with col_detalhe:
            dom_sel = st.session_state.get("dom_sel")
            if dom_sel and dom_sel in dominios:
                df_d = df_dom[df_dom["dominio"] == dom_sel]
                score = float(df_d["score_completude"].fillna(0).mean()) if not df_d.empty else 0
                owners_d = sorted([str(x) for x in df_d["data_owner"].dropna().unique() if str(x).strip()])
                stw_d = sorted([str(x) for x in df_d["data_steward"].dropna().unique() if str(x).strip()])
                termos_dom = glos_valid[glos_valid["dominio"] == dom_sel] if not glos_valid.empty else glos_valid
                ativos_dom = df_d[["table_name", "schema_name", "score_completude"]].copy()

                st.markdown(f"### {icones_dom.get(dom_sel, '🏛️')} {dom_sel}")
                st.caption("Resumo do domínio e suas responsabilidades")
                m1, m2, m3 = st.columns(3)
                m1.metric("Ativos", len(df_d))
                m2.metric("Owners", len(owners_d))
                m3.metric("Stewards", len(stw_d))
                st.metric("Completude média da documentação", f"{score:.0f}%")
                st.divider()

                left, right = st.columns(2, gap="medium")
                with left:
                    with st.container(border=True):
                        st.markdown("**Data Owners**")
                        st.caption("Responsáveis pelas decisões estratégicas sobre os dados.")
                        if owners_d:
                            for owner in owners_d:
                                nome = owner.replace("@meridian.com", "").replace(".", " ").title()
                                st.write(f"• {nome}")
                        else:
                            st.caption("Nenhum responsável definido.")
                    with st.container(border=True):
                        st.markdown("**Ativos do domínio**")
                        if ativos_dom.empty:
                            st.caption("Nenhum ativo encontrado.")
                        else:
                            ativos_dom = ativos_dom.rename(columns={"table_name": "Ativo", "schema_name": "Camada", "score_completude": "Completude (%)"})
                            st.dataframe(ativos_dom, use_container_width=True, hide_index=True)
                with right:
                    with st.container(border=True):
                        st.markdown("**Data Stewards**")
                        st.caption("Responsáveis pela manutenção operacional e evolução dos dados.")
                        if stw_d:
                            for steward in stw_d:
                                nome = steward.replace("@meridian.com", "").replace(".", " ").title()
                                st.write(f"• {nome}")
                        else:
                            st.caption("Nenhum gestor definido.")
                    with st.container(border=True):
                        st.markdown("**Conceitos de negócio**")
                        if termos_dom.empty:
                            st.caption("Nenhum conceito vinculado a este domínio.")
                        else:
                            conceitos_view = termos_dom[["termo", "status"]].drop_duplicates().rename(columns={"termo": "Conceito", "status": "Status"})
                            st.dataframe(conceitos_view, use_container_width=True, hide_index=True)
            else:
                estado_vazio("🏛️", "Selecione um domínio", "Escolha um domínio na lista para ver seus detalhes.")

    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# 🛡️ SCORECARD — Confiabilidade dos Dados
# ════════════════════════════════════════════════════════════════════
elif pagina == "🛡️ Scorecard":
    page_header("🛡️","Scorecard de Governança",
                "Visão consolidada de documentação, responsabilidade, relacionamentos, completude de metadados e certificação.")

    st.markdown("""
    <div style="background:#161B2299;border:1px solid #30363D;border-radius:8px;
                padding:10px 14px;margin-bottom:16px;">
        <div style="color:#8B949E;font-size:0.78rem;line-height:1.6;">
            O Scorecard resume cinco medidas operacionais com pesos iguais.
            O resultado é um índice indicativo de governança, não uma certificação nem uma avaliação formal de maturidade.
            Selecione um pilar para entender sua definição e como melhorar o resultado.
        </div>
    </div>""", unsafe_allow_html=True)

    df_sc    = load_meta()
    df_links = load_links()

    if df_sc.empty:
        estado_vazio("📊","Não foi possível carregar os dados","Tente recarregar a página. Se o problema persistir, contate a equipe de Governança.")
    else:
        dominios_sc = ["Todos"]+sorted([str(d) for d in df_sc["dominio"].dropna().unique() if str(d).strip() and str(d) != "nan"])
        f_dom_sc = st.selectbox("Filtrar por Domínio", dominios_sc, key="sc_dom")
        df_sc_f  = df_sc if f_dom_sc=="Todos" else df_sc[df_sc["dominio"]==f_dom_sc]

        doc  = df_sc_f["descricao"].apply(bool).mean()*100
        own  = df_sc_f["data_owner"].apply(bool).mean()*100
        rel  = (df_sc_f["table_name"].isin(df_links["table_name"]).sum()/max(len(df_sc_f),1))*100 if not df_links.empty else 0
        qual = df_sc_f["score_completude"].mean()
        df_cert_sc = load_cert()
        if not df_cert_sc.empty:
            cert_tabs = df_cert_sc[df_cert_sc["status_cert"]=="certificado"]["table_name"].tolist()
            cert = (df_sc_f["table_name"].isin(cert_tabs).sum() / max(len(df_sc_f),1)) * 100
        else:
            cert = 0
        ger  = (doc+own+rel+qual+cert)/5
        cor_g = "#3FB950" if ger>=80 else "#C9A227" if ger>=60 else "#F85149"

        st.markdown(f"""
        <div style="background:#161B22;border:1px solid #30363D;border-radius:16px;
                    padding:20px;text-align:center;margin-bottom:20px;">
            <div style="font-size:0.7rem;color:#8B949E;text-transform:uppercase;letter-spacing:2px;margin-bottom:4px;">
                Índice Indicativo de Governança</div>
            <div style="font-size:3.5rem;font-weight:800;color:{cor_g};line-height:1;">{ger:.0f}%</div>
            <div style="color:#8B949E;font-size:0.75rem;margin-top:4px;">
                Média simples dos cinco pilares, com peso igual. Não representa qualidade efetiva dos dados nem maturidade formal.</div>
            <div style="color:#8B949E;font-size:0.7rem;margin-top:6px;">
                Documentação · Responsabilidade · Relacionamentos · Completude de Metadados · Certificação</div>
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
            "Completude de Metadados":     {
                "icone":"⭐","cor":"#3FB950","val":qual,
                "conceito":"Percentual médio de preenchimento dos metadados obrigatórios. Este indicador mede completude documental; não representa, por si só, a qualidade efetiva dos dados.",
                "como_melhorar":"Preencha todos os campos obrigatórios na Curadoria. Cada campo preenchido adiciona 20 pontos ao score do ativo."
            },
            "Certificação":  {
                "icone":"🏆","cor":"#F85149","val":cert,
                "conceito":"Percentual de ativos com status formal de certificação registrado no campo selo. O preenchimento de metadados, isoladamente, não equivale à certificação.",
                "como_melhorar":"Siga o fluxo formal de certificação e confirme o atendimento aos critérios definidos antes de conceder o selo."
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
        # Um único controle de navegação para os cinco pilares evita repetir
        # cinco botões "Entender" e reduz o ruído visual.
        opcoes_pilar = ["Selecione um pilar"] + list(PILARES_INFO.keys())
        selecao_atual = st.session_state.get("sc_pilar")
        if selecao_atual not in PILARES_INFO:
            selecao_atual = "Selecione um pilar"
        escolha_pilar = st.selectbox(
            "Consultar definição do pilar",
            options=opcoes_pilar,
            index=opcoes_pilar.index(selecao_atual),
            key="sc_pilar_select",
        )
        pilar_sel = escolha_pilar if escolha_pilar in PILARES_INFO else None
        st.session_state["sc_pilar"] = pilar_sel
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

        # Workflow timeline
        df_tl2=load_timeline()
        ETAPAS_TIPO={"acesso":["abertura","owner","governanca"],"qualidade":["abertura","owner","governanca","resolucao"],"conceito":["abertura","owner","aprovacao"]}
        todas_sols=[]
        if not meus_acess.empty:
            for _,r in meus_acess.iterrows(): todas_sols.append({"id":r.get("solicitacao_id",""),"titulo":f"Acesso: {r.get('ativo_solicitado','—')}","tipo":"acesso","status":r.get("status","—")})
        if not meus_qual.empty:
            for _,r in meus_qual.iterrows(): todas_sols.append({"id":r.get("solicitacao_id",""),"titulo":f"Qualidade: {r.get('ativo','—')}","tipo":"qualidade","status":r.get("status","—")})
        if not meus_conc.empty:
            for _,r in meus_conc.iterrows(): todas_sols.append({"id":r.get("sugestao_id",""),"titulo":f"Conceito: {r.get('nome_sugerido','—')}","tipo":"conceito","status":r.get("status","—")})
        if todas_sols:
            section_divider("WORKFLOW DAS MINHAS SOLICITAÇÕES")
            for sol in todas_sols:
                sid=sol["id"]
                tl_sol=df_tl2[df_tl2["solicitacao_id"]==sid] if not df_tl2.empty else pd.DataFrame()
                etapas=ETAPAS_TIPO.get(sol["tipo"],["abertura","owner","governanca"])
                cs_sol={"pendente":"#C9A227","aprovado":"#15803D","rejeitado":"#B91C1C"}.get(sol["status"],"#9CA3AF")
                st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E8E4DC;border-radius:12px;padding:14px;margin-bottom:10px;"><div style="display:flex;justify-content:space-between;margin-bottom:10px;"><div style="color:#0D1B2A;font-weight:700;font-size:0.85rem;">{sol["titulo"]}</div><span style="background:{cs_sol}22;color:{cs_sol};border-radius:20px;padding:2px 10px;font-size:0.7rem;font-weight:600;">● {sol["status"]}</span></div>',unsafe_allow_html=True)
                eh=""
                for i,etapa in enumerate(etapas):
                    tl_e=tl_sol[tl_sol["etapa"]==etapa].iloc[0] if not tl_sol.empty and etapa in tl_sol["etapa"].values else None
                    if tl_e is not None:
                        se=tl_e["status_etapa"]; ie={"concluido":"✅","atrasado":"⏰","pendente":"⏳"}.get(se,"🔵")
                        hg=tl_e.get("horas_gastas"); sl_h=tl_e.get("sla_horas",0)
                        dn=tl_e.get("dentro_sla",True); hg_txt=f"{hg:.0f}h/{sl_h}h" if hg is not None else "—"
                        cs2="#15803D" if dn else "#B91C1C"
                        eh+=f'<div style="text-align:center;flex:1;background:{"#F0FDF4" if se=="concluido" else "#FFF0F0" if se=="atrasado" else "#F4F1EC"};border-radius:8px;padding:8px;"><div style="font-size:0.6rem;color:#9CA3AF;text-transform:uppercase;">{etapa.upper()}</div><div style="font-size:1.3rem;">{ie}</div><div style="font-size:0.6rem;color:{cs2};font-weight:600;">{hg_txt}</div></div>'
                    else:
                        eh+=f'<div style="text-align:center;flex:1;background:#F4F1EC;border-radius:8px;padding:8px;opacity:0.4;"><div style="font-size:0.6rem;color:#9CA3AF;text-transform:uppercase;">{etapa.upper()}</div><div style="font-size:1.3rem;">⭕</div><div style="font-size:0.6rem;color:#9CA3AF;">—</div></div>'
                    if i<len(etapas)-1: eh+=f'<div style="flex:0;color:#E8E4DC;font-size:1rem;padding:0 4px;align-self:center;">→</div>'
                st.markdown(f'<div style="display:flex;gap:6px;">{eh}</div></div>',unsafe_allow_html=True)

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

        section_divider("WORKFLOW DE ATENDIMENTO — TODAS AS SOLICITAÇÕES")
        df_tl3=load_timeline()
        if not df_tl3.empty:
            ETAPAS_TIPO3={"acesso":["abertura","owner","governanca"],"qualidade":["abertura","owner","governanca","resolucao"],"conceito":["abertura","owner","aprovacao"],"regra":["abertura","owner","aprovacao"]}
            sols_u=df_tl3.groupby("solicitacao_id").first().reset_index()
            for _,sr in sols_u.iterrows():
                sid=sr["solicitacao_id"]; titulo=sr.get("titulo","—"); tipo=sr.get("tipo_sol","acesso"); dom=sr.get("dominio","—")
                tl_sol=df_tl3[df_tl3["solicitacao_id"]==sid]
                etapas=ETAPAS_TIPO3.get(tipo,["abertura","owner","governanca"])
                tem_atraso=any(tl_sol["status_etapa"]=="atrasado") if not tl_sol.empty else False
                st.markdown(f'<div style="background:#FFFFFF;border:1px solid {"#B91C1C44" if tem_atraso else "#E8E4DC"};border-radius:12px;padding:14px;margin-bottom:8px;"><div style="display:flex;justify-content:space-between;margin-bottom:10px;"><div><div style="color:#0D1B2A;font-weight:700;font-size:0.85rem;">{titulo}</div><div style="color:#9CA3AF;font-size:0.7rem;">{dom} · {tipo}</div></div>{"<span style=background:#B91C1C22;color:#B91C1C;border-radius:20px;padding:2px 10px;font-size:0.7rem;font-weight:600;>⏰ ATRASADO</span>" if tem_atraso else ""}</div>',unsafe_allow_html=True)
                eh=""
                for i,etapa in enumerate(etapas):
                    tl_e=tl_sol[tl_sol["etapa"]==etapa].iloc[0] if etapa in tl_sol["etapa"].values else None
                    if tl_e is not None:
                        se=tl_e["status_etapa"]; ie={"concluido":"✅","atrasado":"⏰","pendente":"⏳"}.get(se,"🔵")
                        hg=tl_e.get("horas_gastas"); sl_h=tl_e.get("sla_horas",0)
                        dn=tl_e.get("dentro_sla",True); resp=str(tl_e.get("responsavel","")).split("@")[0]
                        hg_txt=f"{hg:.0f}h/{sl_h}h" if hg is not None else "—"
                        cs_t="#15803D" if dn else "#B91C1C"
                        eh+=f'<div style="text-align:center;flex:1;background:{"#F0FDF4" if se=="concluido" else "#FFF0F0" if se=="atrasado" else "#F4F1EC"};border-radius:8px;padding:8px;"><div style="font-size:0.6rem;color:#9CA3AF;text-transform:uppercase;">{etapa.upper()}</div><div style="font-size:1.3rem;">{ie}</div><div style="font-size:0.65rem;color:#0D1B2A;font-weight:600;">{resp}</div><div style="font-size:0.6rem;color:{cs_t};">{hg_txt}</div></div>'
                    else:
                        eh+=f'<div style="text-align:center;flex:1;background:#F4F1EC;border-radius:8px;padding:8px;opacity:0.4;"><div style="font-size:0.6rem;color:#9CA3AF;text-transform:uppercase;">{etapa.upper()}</div><div style="font-size:1.3rem;">⭕</div></div>'
                    if i<len(etapas)-1: eh+=f'<div style="flex:0;color:#E8E4DC;font-size:1rem;padding:0 4px;align-self:center;">→</div>'
                st.markdown(f'<div style="display:flex;gap:6px;">{eh}</div></div>',unsafe_allow_html=True)
        else:
            st.info("Nenhuma solicitação no sistema ainda.")

        section_divider("MEUS CONCEITOS NO GLOSSÁRIO")
        df_meus = df_gloss[df_gloss["criado_por"]==usuario] if not df_gloss.empty else pd.DataFrame()
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
                    df_cert_cur = load_cert()
                    cert_tabelas_cur = df_cert_cur[df_cert_cur["status_cert"]=="certificado"]["table_name"].tolist() if not df_cert_cur.empty else []
                    cert_p = 100 if sel_t in cert_tabelas_cur else 0
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
                            filled = sum([bool(new_desc),bool(new_dom),bool(new_own),bool(new_stw)])
                            ns = min(filled*25, 100)
                            # Completude de metadados não concede nem revoga certificação.
                            ok,err = exe(f"UPDATE meridian_governanca.tabelas_metadata SET descricao='{esc(new_desc)}',dominio='{esc(new_dom)}',data_owner='{esc(new_own)}',data_steward='{esc(new_stw)}',score_completude={ns},atualizado_em=current_timestamp() WHERE schema_name='{esc(sel_s)}' AND table_name='{esc(sel_t)}'")
                            if ok:
                                ok_aud, err_aud = exe(f"INSERT INTO meridian_governanca.metadata_audit VALUES ('{uuid.uuid4()}',current_timestamp(),'{esc(sel_s)}','{esc(sel_t)}','tabela','','metadados','{row['score_completude']}','{ns}','manual','{esc(usuario)}','{esc(usuario[:8])}')")
                                if ok_aud:
                                    st.success(f"✅ Metadados salvos e auditados. Completude: {ns}%.")
                                else:
                                    st.error("Os metadados foram salvos, mas o registro de auditoria falhou. A equipe responsável deve reconciliar a trilha.")
                                    st.caption(f"Detalhe da auditoria: {err_aud}")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("Não foi possível salvar os metadados.")
                                st.caption(f"Detalhe técnico: {err}")
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
                                filled = sum([bool(sug_d),bool(sug_dom),bool(new_own),bool(new_stw)])
                                ns = min(filled*25, 100)
                                # Sugestão de metadados não concede nem revoga certificação.
                                ok, err = exe(f"UPDATE meridian_governanca.tabelas_metadata SET descricao='{esc(sug_d)}',dominio='{esc(sug_dom)}',score_completude={ns},atualizado_em=current_timestamp() WHERE schema_name='{esc(sel_s)}' AND table_name='{esc(sel_t)}'")
                                if ok:
                                    ok_aud, err_aud = exe(f"INSERT INTO meridian_governanca.metadata_audit VALUES ('{uuid.uuid4()}',current_timestamp(),'{esc(sel_s)}','{esc(sel_t)}','tabela','','metadados','{row['score_completude']}','{ns}','ia','{esc(usuario)}','{esc(usuario[:8])}')")
                                    if ok_aud:
                                        st.success(f"✅ Metadados aplicados e auditados. Completude: {ns}%.")
                                    else:
                                        st.error("Os metadados foram aplicados, mas o registro de auditoria falhou.")
                                        st.caption(f"Detalhe da auditoria: {err_aud}")
                                    del st.session_state["ai_desc"]
                                    del st.session_state["ai_dom"]
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error("Não foi possível aplicar os metadados sugeridos.")
                                    st.caption(f"Detalhe técnico: {err}")
                        with sa2:
                            if st.button("❌ Descartar",key="ai_dc",use_container_width=True):
                                del st.session_state["ai_desc"]; del st.session_state["ai_dom"]; st.rerun()

            with cur2:
                f1c,f2c = st.columns(2)
                with f1c: fl_s = st.selectbox("Schema",["Todos"]+sorted(df_cur["schema_name"].unique().tolist()),key="lote_s")
                status_opts = ["Todos"]+sorted([str(s) for s in df_cur["status"].dropna().unique() if str(s).strip()]) if not df_cur.empty else ["Todos"]
                with f2c: fl_sl = st.selectbox("Situação",status_opts,key="lote_sl")
                df_l = df_cur.copy()
                if fl_s  != "Todos": df_l = df_l[df_l["schema_name"]==fl_s]
                if fl_sl != "Todos": df_l = df_l[df_l["status"]==fl_sl]
                df_led = df_l[["schema_name","table_name","score_completude","status"]].copy()
                df_led.insert(0,"Selecionar",False)
                edited = st.data_editor(df_led.rename(columns={"schema_name":"Schema","table_name":"Tabela","score_completude":"Score","status":"Status"}),use_container_width=True,hide_index=True,column_config={"Selecionar":st.column_config.CheckboxColumn()})
                sels = edited[edited["Selecionar"]==True]
                if len(sels)>0:
                    st.markdown(f'<div style="color:#C9A227;font-size:0.82rem;margin:6px 0;">{len(sels)} tabela(s) selecionada(s)</div>', unsafe_allow_html=True)
                    lb1,lb2,lb3 = st.columns(3)
                    with lb1: l_dom = st.selectbox("Domínio",["","Crédito","Pagamentos","Clientes","Compliance","Produtos"],key="l_dom")
                    with lb2: l_own = st.text_input("Responsável (Owner)",key="l_own")
                    with lb3: l_stw = st.text_input("Gestor (Steward)",key="l_stw")
                    if st.button(f"🚀 Aplicar em {len(sels)} tabela(s)",type="primary",key="l_apply"):
                        campos_solicitados = bool(l_dom or l_own or l_stw)
                        if not campos_solicitados:
                            st.info("Informe pelo menos um campo para atualizar antes de aplicar.")
                        else:
                            erros = []
                            atualizadas = []
                            for _, r in sels.iterrows():
                                sets = []
                                if l_dom: sets.append(f"dominio='{esc(l_dom)}'")
                                if l_own: sets.append(f"data_owner='{esc(l_own)}'")
                                if l_stw: sets.append(f"data_steward='{esc(l_stw)}'")
                                sets.append("atualizado_em=current_timestamp()")
                                ok, err = exe(
                                    f"UPDATE meridian_governanca.tabelas_metadata "
                                    f"SET {', '.join(sets)} "
                                    f"WHERE schema_name='{esc(r['Schema'])}' AND table_name='{esc(r['Tabela'])}'"
                                )
                                if ok:
                                    atualizadas.append(str(r["Tabela"]))
                                else:
                                    erros.append({"tabela": str(r["Tabela"]), "erro": str(err)})
                            if erros:
                                st.error(f"{len(erros)} de {len(sels)} atualização(ões) falharam.")
                                st.dataframe(pd.DataFrame(erros), use_container_width=True, hide_index=True)
                            if atualizadas:
                                st.success(f"Atualizações concluídas: {len(atualizadas)} de {len(sels)}.")
                                st.cache_data.clear()
                                if not erros:
                                    st.rerun()

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
    if not is_curador:
        st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E8E4DC;border-radius:12px;padding:40px;text-align:center;"><div style="font-size:2.2rem;margin-bottom:10px;">🔒</div><div style="font-family:Lora,serif;color:#0D1B2A;font-weight:700;margin-bottom:6px;">Acesso restrito</div><div style="color:#9CA3AF;font-size:0.8rem;">Esta área é destinada a Curadores e Aprovadores.</div></div>',unsafe_allow_html=True)
        st.stop()
    page_header("📊","Painel de Indicadores de Gestão",
                "Evolução da governança + SLA e atendimento de solicitações.")
    st.markdown("""<div style="background:#161B2299;border:1px solid #30363D;border-radius:8px;
                padding:10px 14px;margin-bottom:16px;"><div style="color:#8B949E;font-size:0.78rem;line-height:1.6;">
                Este painel mostra como os principais indicadores de governança evoluíram ao longo do tempo.
                Use o filtro de domínio para acompanhar a maturidade de uma área específica.</div></div>""",
                unsafe_allow_html=True)
    df_snap = load_snap()
    df_meta = load_meta()
    df_cert = load_cert()
    df_sla = load_sla_snap()

    # Filtros aplicáveis à série histórica agregada.
    # Removidos filtros por ativo (documentação/ownership/qualidade), pois não eram
    # aplicados aos snapshots e sugeriam uma segmentação que o painel não executava.
    ff = st.columns([2, 1, 1])
    with ff[0]:
        doms_ind = ["Todos"] + sorted([
            str(d) for d in df_snap["dominio"].dropna().unique()
            if str(d) != "Todos" and str(d).strip() and str(d) != "nan"
        ]) if not df_snap.empty else ["Todos"]
        fi_dom = st.selectbox("Domínio", doms_ind, key="ind_dom")
    with ff[1]:
        fi_ano = st.selectbox("Ano", ["Todos", "2024", "2025", "2026"], key="ind_ano")
    with ff[2]:
        meses_map = {"Todos":0,"Jan":1,"Fev":2,"Mar":3,"Abr":4,"Mai":5,"Jun":6,"Jul":7,"Ago":8,"Set":9,"Out":10,"Nov":11,"Dez":12}
        fi_mes = st.selectbox("Mês", list(meses_map.keys()), key="ind_mes")

    if df_snap.empty:
        st.info("Nenhum snapshot disponível.")
    else:
        df_sn = df_snap[df_snap["dominio"]==(fi_dom if fi_dom!="Todos" else "Todos")] if fi_dom!="Todos" else df_snap[df_snap["dominio"]=="Todos"]
        if fi_ano!="Todos":
            try: df_sn=df_sn[pd.to_datetime(df_sn["data_snapshot"]).dt.year==int(fi_ano)]
            except: pass
        if fi_mes!="Todos":
            try: df_sn=df_sn[pd.to_datetime(df_sn["data_snapshot"]).dt.month==meses_map[fi_mes]]
            except: pass
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

    # ── PAINEL DE SLA ──────────────────────────────────────────────
    if not df_sla.empty:
        st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin:16px 0 12px;"><div style="height:1px;background:#E8E4DC;flex:1;"></div><span style="color:#9CA3AF;font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;">SLA E ATENDIMENTO DE SOLICITAÇÕES</span><div style="height:1px;background:#E8E4DC;flex:1;"></div></div>',unsafe_allow_html=True)
        df_slaf=df_sla.copy()
        if fi_dom!="Todos": df_slaf=df_slaf[df_slaf["dominio"]==fi_dom]
        ult_sla=df_slaf[df_slaf["data_snapshot"]==df_slaf["data_snapshot"].max()] if not df_slaf.empty else pd.DataFrame()
        if not ult_sla.empty:
            tot_ab=int(ult_sla["total_abertas"].sum()); tot_re=int(ult_sla["total_resolvidas"].sum())
            tot_at=int(ult_sla["total_atrasadas"].sum()); tm=ult_sla["tempo_medio_hrs"].mean(); tsla=ult_sla["taxa_sla_pct"].mean()
            cs_sla="#15803D" if tsla>=90 else "#A16207" if tsla>=70 else "#B91C1C"
            ss=st.columns(5)
            with ss[0]: st.markdown(kpi(tot_ab,"Abertas","#C9A227"),unsafe_allow_html=True)
            with ss[1]: st.markdown(kpi(tot_re,"Resolvidas","#15803D"),unsafe_allow_html=True)
            with ss[2]: st.markdown(kpi(tot_at,"Atrasadas","#B91C1C"),unsafe_allow_html=True)
            with ss[3]: st.markdown(kpi(f"{tm:.0f}h","Tempo Médio","#6366F1",tooltip="Tempo médio de resolução em horas."),unsafe_allow_html=True)
            with ss[4]: st.markdown(kpi(f"{tsla:.0f}%","Taxa SLA",cs_sla,tooltip="% resolvidas dentro do prazo."),unsafe_allow_html=True)

        st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin:12px 0 8px;"><div style="height:1px;background:#E8E4DC;flex:1;"></div><span style="color:#9CA3AF;font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;">GARGALOS POR DOMÍNIO</span><div style="height:1px;background:#E8E4DC;flex:1;"></div></div>',unsafe_allow_html=True)
        for _,row in ult_sla.iterrows() if not ult_sla.empty else []:
            cs_g="#15803D" if row["taxa_sla_pct"]>=90 else "#A16207" if row["taxa_sla_pct"]>=70 else "#B91C1C"
            gb=row.get("gargalo_etapa","—"); gr=str(row.get("gargalo_resp","—")).split("@")[0]
            st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E8E4DC;border-radius:10px;padding:10px 14px;margin-bottom:5px;display:flex;justify-content:space-between;align-items:center;"><div><span style="color:#0D1B2A;font-weight:700;font-size:0.82rem;">{row["dominio"]}</span><span style="color:#9CA3AF;font-size:0.7rem;margin-left:8px;">{row["tipo_sol"]}</span></div><div style="display:flex;gap:16px;font-size:0.7rem;"><span>Abertas: <b style="color:#0D1B2A;">{row["total_abertas"]}</b></span><span>Atrasadas: <b style="color:#B91C1C;">{row["total_atrasadas"]}</b></span><span>Gargalo: <b style="color:#B91C1C;">{gb} ({gr})</b></span><span style="background:{cs_g}22;color:{cs_g};border-radius:20px;padding:2px 8px;font-weight:700;">SLA {row["taxa_sla_pct"]:.0f}%</span></div></div>',unsafe_allow_html=True)
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
        with f1q: fq_dom=st.selectbox("Domínio",["Todos"]+sorted([str(d) for d in df_qual["dominio"].dropna().unique() if str(d).strip() and str(d) != "nan"]),key="q_dom")
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
    df_cert=load_cert()
    if df_cert.empty:
        estado_vazio("🥇","Nenhum ativo certificado ainda","Inicie o processo de certificação na Curadoria.")
    else:
        fc1,fc2,fc3=st.columns(3)
        with fc1: f_cert_dom=st.selectbox("Domínio",["Todos"]+sorted([str(d) for d in df_cert["dominio"].dropna().unique() if str(d).strip() and str(d) != "nan"]),key="fc_dom")
        with fc2: f_cert_st=st.selectbox("Status",["Todos","certificado","em_analise","pendente","nao_iniciado"],key="fc_st")
        with fc3: f_cert_niv=st.selectbox("Nível",["Todos","Ouro","Prata","Bronze"],key="fc_niv")
        df_cf=df_cert.copy()
        if f_cert_dom!="Todos": df_cf=df_cf[df_cf["dominio"]==f_cert_dom]
        if f_cert_st!="Todos":  df_cf=df_cf[df_cf["status_cert"]==f_cert_st]
        if f_cert_niv!="Todos": df_cf=df_cf[df_cf["nivel_cert"]==f_cert_niv]
        if df_cf.empty:
            estado_vazio("🔎", "Nenhum ativo encontrado", "Altere os filtros para consultar outros ativos.")
        else:
            st.caption(f"{len(df_cf)} ativo(s) · Os critérios ficam disponíveis sob demanda.")
            for _, row in df_cf.iterrows():
                status_map = {
                    "certificado": ("Certificado", "green"),
                    "em_analise": ("Em análise", "orange"),
                    "pendente": ("Pendente", "blue"),
                    "nao_iniciado": ("Não iniciado", "gray"),
                }
                label_st, cor_md = status_map.get(row["status_cert"], (str(row["status_cert"]).replace("_", " ").capitalize(), "gray"))
                nivel = str(row["nivel_cert"]) if pd.notna(row["nivel_cert"]) else "Sem nível"
                selo = SELOS.get(nivel, {})
                with st.container(border=True):
                    col_ativo, col_status = st.columns([3, 1])
                    with col_ativo:
                        st.markdown(f"**{row['table_name']}**")
                        st.caption(f"{row['schema_name']} · Selo {nivel}")
                    with col_status:
                        st.markdown(f":{cor_md}[**{label_st}**]")
                        if pd.notna(row["valido_ate"]) and row["valido_ate"]:
                            st.caption(f"Válido até {row['valido_ate']}")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Documentação", f"{float(row['score_doc'] or 0):.0f}%")
                    m2.metric("Qualidade", f"{float(row['score_qualidade'] or 0):.1f}%")
                    m3.metric("Responsabilidades", f"{float(row['score_ownership'] or 0):.0f}%")
                    with st.expander("Critérios de certificação", expanded=False):
                        crit_cols = st.columns(5)
                        criterios = [
                            ("Documentação", bool(row["criterio_doc"])),
                            ("Owner", bool(row["criterio_owner"])),
                            ("Steward", bool(row["criterio_steward"])),
                            ("Domínio", bool(row["criterio_dominio"])),
                            ("Qualidade", bool(row["criterio_qualidade"])),
                        ]
                        for col, (nome, atendido) in zip(crit_cols, criterios):
                            with col:
                                st.write(("✓ " if atendido else "✕ ") + nome)
            if is_aprovador and row["status_cert"]=="em_analise":
                ca2,cr2=st.columns(2)
                with ca2:
                    if st.button(f"✅ Certificar {row['table_name']}",key=f"cert_ap_{row['cert_id']}",use_container_width=True):
                        ok_cert, err_cert = exe(
                            f"UPDATE meridian_governanca.gd_certification "
                            f"SET status_cert='certificado',certificado_por='{esc(usuario)}',"
                            f"certificado_em=current_timestamp(),valido_ate=date_add(current_date(),365) "
                            f"WHERE cert_id='{esc(row['cert_id'])}' AND status_cert='em_analise'"
                        )
                        if not ok_cert:
                            st.error("Não foi possível atualizar o registro de certificação. Nenhuma confirmação foi emitida.")
                            st.caption(f"Detalhe técnico: {err_cert}")
                        else:
                            st.success("✅ Certificado! O registro foi atualizado.")
                            st.cache_data.clear()
                            st.rerun()
                with cr2:
                    if st.button(f"❌ Rejeitar",key=f"cert_rej_{row['cert_id']}",use_container_width=True):
                        ok_rej, err_rej = exe(
                            f"UPDATE meridian_governanca.gd_certification "
                            f"SET status_cert='pendente',certificado_por='{esc(usuario)}',certificado_em=current_timestamp() "
                            f"WHERE cert_id='{esc(row['cert_id'])}' AND status_cert='em_analise'"
                        )
                        if ok_rej:
                            st.warning("↩️ Devolvido.")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("Não foi possível devolver a certificação.")
                            st.caption(f"Detalhe técnico: {err_rej}")
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
        with fp1: fp_dom=st.selectbox("Domínio",["Todos"]+sorted([str(d) for d in df_prod["dominio"].dropna().unique() if str(d).strip() and str(d) != "nan"]),key="fp_dom")
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
