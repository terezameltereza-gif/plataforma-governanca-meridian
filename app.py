"""
app.py — Plataforma de Governança de Dados
Banco Meridian | v4.2
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

USUARIOS = {
    "consultante@meridian.com":   {"nome":"João Silva",      "perfil":"consultante"},
    "curador@meridian.com":       {"nome":"Maria Santos",    "perfil":"curador"},
    "governanca@meridian.com":    {"nome":"Tereza Cristina", "perfil":"curador"},
    "ana.lima@meridian.com":      {"nome":"Ana Lima",        "perfil":"aprovador"},
    "fernando.dias@meridian.com": {"nome":"Fernando Dias",   "perfil":"aprovador"},
}
PERFIL_COR   = {"consultante":"#58A6FF","curador":"#C9A227","aprovador":"#3FB950"}
PERFIL_LABEL = {"consultante":"👁️ Consultante","curador":"✏️ Curador","aprovador":"✅ Aprovador"}

MENU = {
    "PESSOAL":        ["⚡ Meu Espaço"],
    "DESCOBERTA":     ["🏠 Início","📋 Catálogo","📖 Glossário","🏛️ Domínios"],
    "CONFIABILIDADE": ["🛡️ Scorecard"],
    "OPERAÇÃO":       ["✏️ Curadoria","🕐 Auditoria"],
}

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
            <div style="background:#C9A22722;border-radius:8px;padding:8px;
                        font-size:1.2rem;">{icone}</div>
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
        border-radius:10px;padding:14px 16px;border-top:3px solid {cor};">
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
        email = st.selectbox("", list(USUARIOS.keys()),
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

    if "pagina" not in st.session_state:
        st.session_state["pagina"] = "🏠 Início"

    st.markdown(f"""
    <div style="background:#161B22;border:1px solid #30363D;border-radius:8px;
                padding:8px 10px;margin-bottom:10px;">
        <div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;
                    letter-spacing:1px;">Usuário logado</div>
        <div style="font-weight:700;color:#E6EDF3;font-size:0.82rem;">{u['nome']}</div>
        <div style="color:{cor};font-size:0.72rem;font-weight:600;">
            {PERFIL_LABEL[perfil]}</div>
    </div>""", unsafe_allow_html=True)

    for secao, itens in MENU.items():
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
                if st.button(item, key=f"nav_{item}",
                             use_container_width=True):
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
# 🏠 INÍCIO
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
                <div style="color:#8B949E;font-size:0.85rem;max-width:520px;line-height:1.5;">
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
    with k1: st.markdown(kpi(total_termos,"Termos de Negócio","#C9A227","📖","Definições oficiais da organização"), unsafe_allow_html=True)
    with k2: st.markdown(kpi(total_ativos,"Ativos de Dados","#58A6FF","🗂️","Tabelas e estruturas catalogadas"), unsafe_allow_html=True)
    with k3: st.markdown(kpi(total_dom,"Domínios de Negócio","#BC8CFF","🏛️","Áreas responsáveis pelos dados"), unsafe_allow_html=True)
    with k4: st.markdown(kpi(total_regras,"Regras de Negócio","#3FB950","📏","Critérios para calcular ou validar informações"), unsafe_allow_html=True)
    with k5: st.markdown(kpi(f"{cobertura}%","Cobertura Semântica",cor_cob,"🔗","Ativos conectados a conceitos de negócio"), unsafe_allow_html=True)

    section_divider("COMECE POR UMA PERGUNTA")
    perguntas = [
        ("🤔","O que significa?","Definição oficial de qualquer conceito.","📖 Glossário"),
        ("🧮","Como é calculado?","Regras e critérios de cada métrica.","📖 Glossário"),
        ("🔍","Onde encontro?","Tabela ou estrutura que armazena o dado.","📋 Catálogo"),
        ("👤","Quem responde?","Owner e Steward responsáveis.","🏛️ Domínios"),
        ("🔗","Onde é utilizado?","Relacionamentos entre conceitos e ativos.","📖 Glossário"),
        ("🛡️","Posso confiar?","Scorecard de confiabilidade do ativo.","🛡️ Scorecard"),
    ]
    cols_p = st.columns(3)
    for i,(ic,tit,desc,dest) in enumerate(perguntas):
        with cols_p[i%3]:
            if st.button(f"{ic}  {tit}", key=f"perg_{i}", use_container_width=True):
                st.session_state["pagina"] = dest
                st.rerun()
            st.markdown(f'<div style="color:#8B949E;font-size:0.7rem;margin:-4px 0 8px;padding:0 2px;">{desc}</div>', unsafe_allow_html=True)

    section_divider("IMPACTO DA GOVERNANÇA")
    im1,im2,im3,im4 = st.columns(4)
    for col,(ic,tit,desc) in zip([im1,im2,im3,im4],[
        ("🎯","Uma única verdade","Definições unificadas eliminam ambiguidade."),
        ("🔒","Confiança nos dados","Ownership definido e auditoria completa."),
        ("⚡","Decisões mais rápidas","Qualquer informação em segundos."),
        ("📋","Compliance embarcado","Rastreabilidade nativa para auditorias."),
    ]):
        with col:
            st.markdown(f"""
            <div style="background:#161B22;border:1px solid #30363D;border-radius:10px;
                        padding:14px;text-align:center;">
                <div style="font-size:1.4rem;margin-bottom:6px;">{ic}</div>
                <div style="color:#E6EDF3;font-weight:700;font-size:0.8rem;margin-bottom:4px;">{tit}</div>
                <div style="color:#8B949E;font-size:0.72rem;line-height:1.4;">{desc}</div>
            </div>""", unsafe_allow_html=True)

    copyright_footer()

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
        m1,m2,m3,m4 = st.columns(4)
        with m1: st.markdown(kpi(len(df_g),"Total de Termos","#C9A227","📖"), unsafe_allow_html=True)
        with m2: st.markdown(kpi(len(df_g[df_g["status"]=="homologado"]),"Homologados","#3FB950"), unsafe_allow_html=True)
        with m3: st.markdown(kpi(len(df_g[df_g["status"]=="em_revisao"]),"Em Revisão","#58A6FF"), unsafe_allow_html=True)
        with m4: st.markdown(kpi(len(df_g[df_g["status"]=="rascunho"]),"Rascunho","#8B949E"), unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        abas = ["📋 Termos de Negócio","📏 Regras de Negócio","🔗 Relacionamentos","🕐 Histórico"]
        if is_curador: abas.append("⚙️ Workflow")
        tabs_g = st.tabs(abas)

        with tabs_g[0]:
            col_lista, col_det = st.columns([1,2])
            with col_lista:
                busca_g = st.text_input("",placeholder="🔍 Buscar termo...",key="g_busca")
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
                    if st.button(f"↳ {row['termo']}", key=f"gc_{row['glossary_id']}",
                                 use_container_width=True):
                        st.session_state["gid_sel"] = row["glossary_id"]
                        st.rerun()

                if is_curador:
                    with st.expander("➕ Criar novo termo"):
                        nn  = st.text_input("Termo *",key="nn")
                        nd  = st.text_area("Definição *",key="nd",height=70)
                        ns  = st.text_input("Sinônimos",key="ns")
                        ndo = st.selectbox("Domínio",["Crédito","Pagamentos","Clientes","Compliance","Produtos"],key="ndo")
                        na  = st.text_input("Área",key="na")
                        nc  = st.selectbox("Criticidade",["Crítico","Alto","Médio","Baixo"],key="nc")
                        if st.button("💾 Criar",key="btn_criar"):
                            if nn and nd:
                                gid_new = str(uuid.uuid4())
                                ok,err = exe(f"INSERT INTO meridian_governanca.business_glossary VALUES ('{gid_new}','{esc(nn)}','{esc(nd)}','{esc(ns)}','{esc(ndo)}','{esc(na)}','{esc(nc)}','{esc(usuario)}','{esc(usuario)}','rascunho',1,false,'{esc(usuario)}',current_timestamp(),'{esc(usuario)}',current_timestamp())")
                                if ok: st.success(f"✅ '{nn}' criado!"); st.cache_data.clear(); st.rerun()
                                else: st.error(f"Erro: {err}")
                            else: st.warning("Preencha Termo e Definição.")

            with col_det:
                gid = st.session_state.get("gid_sel")
                if gid:
                    row_d = df_g[df_g["glossary_id"]==gid]
                    if not row_d.empty:
                        row    = row_d.iloc[0]
                        cor_st = {"homologado":"#3FB950","em_revisao":"#58A6FF","rascunho":"#8B949E"}.get(row["status"],"#8B949E")
                        cor_cr = {"Crítico":"#F85149","Alto":"#FF7B72","Médio":"#C9A227","Baixo":"#3FB950"}.get(row["criticidade"],"#8B949E")
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
                                    <div style="color:{cor_cr};font-weight:600;font-size:0.82rem;">{row['criticidade']}</div>
                                </div>
                                <div style="background:#0D1117;border-radius:8px;padding:9px;">
                                    <div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;letter-spacing:1px;">DATA OWNER</div>
                                    <div style="color:#E6EDF3;font-size:0.78rem;">{row['owner_email']}</div>
                                </div>
                                <div style="background:#0D1117;border-radius:8px;padding:9px;">
                                    <div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;letter-spacing:1px;">DATA STEWARD</div>
                                    <div style="color:#E6EDF3;font-size:0.78rem;">{row['steward_email']}</div>
                                </div>
                            </div>
                            <div style="background:#0D1117;border:1px solid #30363D;border-radius:8px;padding:10px 14px;">
                                <div style="font-size:0.6rem;color:#8B949E;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">IMPACTO DO TERMO</div>
                                <div style="display:flex;gap:20px;">
                                    <div><span style="color:#58A6FF;font-size:1.3rem;font-weight:800;">{n_tab}</span><span style="color:#8B949E;font-size:0.7rem;margin-left:4px;">tabelas</span></div>
                                    <div><span style="color:#BC8CFF;font-size:1.3rem;font-weight:800;">{n_reg}</span><span style="color:#8B949E;font-size:0.7rem;margin-left:4px;">regras</span></div>
                                    <div><span style="color:#C9A227;font-size:1.3rem;font-weight:800;">1</span><span style="color:#8B949E;font-size:0.7rem;margin-left:4px;">domínio</span></div>
                                </div>
                            </div>
                        </div>""", unsafe_allow_html=True)

                        if not rules_t.empty:
                            st.markdown('<div style="color:#E6EDF3;font-weight:700;font-size:0.82rem;margin:12px 0 6px;">📏 Regras de Negócio</div>', unsafe_allow_html=True)
                            for _,r in rules_t.iterrows():
                                st.markdown(f"""
                                <div style="background:#161B22;border:1px solid #30363D;border-radius:6px;padding:8px 12px;margin-bottom:5px;">
                                    <div style="display:flex;justify-content:space-between;">
                                        <span style="color:#E6EDF3;font-size:0.8rem;font-weight:600;">{r['nome_regra']}</span>
                                        <span style="background:#BC8CFF22;color:#BC8CFF;border-radius:4px;padding:1px 6px;font-size:0.65rem;">{r['categoria']}</span>
                                    </div>
                                    <div style="color:#8B949E;font-size:0.73rem;margin-top:2px;">{r['descricao_regra']}</div>
                                </div>""", unsafe_allow_html=True)

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
                    st.markdown("""
                    <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;padding:40px;text-align:center;">
                        <div style="font-size:2rem;margin-bottom:10px;">📖</div>
                        <div style="color:#E6EDF3;font-weight:700;margin-bottom:6px;">Selecione um termo</div>
                        <div style="color:#8B949E;font-size:0.82rem;">Clique em qualquer termo da lista para ver seus detalhes.</div>
                    </div>""", unsafe_allow_html=True)

        with tabs_g[1]:
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

        with tabs_g[2]:
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
                st.markdown('<div style="display:flex;gap:16px;margin-top:4px;"><div style="display:flex;align-items:center;gap:6px;"><div style="width:10px;height:10px;border-radius:50%;background:#C9A227;"></div><span style="color:#8B949E;font-size:0.72rem;">Termos de Negócio</span></div><div style="display:flex;align-items:center;gap:6px;"><div style="width:10px;height:10px;border-radius:50%;background:#58A6FF;"></div><span style="color:#8B949E;font-size:0.72rem;">Ativos Técnicos</span></div></div>', unsafe_allow_html=True)

        with tabs_g[3]:
            df_wf,_ = qry("SELECT g.termo, w.acao, w.status_anterior, w.status_novo, w.aprovador, w.comentario, w.criado_em FROM meridian_governanca.glossary_approval_workflow w JOIN meridian_governanca.business_glossary g ON w.glossary_id=g.glossary_id ORDER BY w.criado_em DESC LIMIT 50")
            if not df_wf.empty:
                for _,r in df_wf.iterrows():
                    ts = str(r["criado_em"])[:16] if r["criado_em"] else "—"
                    st.markdown(f'<div style="background:#161B22;border:1px solid #30363D;border-radius:6px;padding:8px 12px;margin-bottom:5px;display:flex;justify-content:space-between;align-items:center;"><div><span style="color:#C9A227;font-size:0.78rem;font-weight:700;">{r["termo"]}</span><span style="color:#8B949E;font-size:0.72rem;margin-left:8px;">{r["acao"]}</span></div><span style="color:#8B949E;font-size:0.7rem;">{ts}</span></div>', unsafe_allow_html=True)
            else: st.info("Nenhum histórico disponível.")

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
# 📋 CATÁLOGO
# ════════════════════════════════════════════════════════════════════
elif pagina == "📋 Catálogo":
    page_header("📋","Catálogo de Dados","Descubra, compreenda e confie nos dados antes de utilizá-los.")

    df_cat = load_meta()
    if not df_cat.empty:
        schemas = df_cat["schema_name"].value_counts()
        k1,k2,k3 = st.columns(3)
        with k1: st.markdown(kpi(len(df_cat),"Tabelas no Catálogo","#C9A227"), unsafe_allow_html=True)
        with k2: st.markdown(kpi(f"{schemas.get('ouro',0)} · {schemas.get('prata',0)} · {schemas.get('bronze',0)}","Ouro · Prata · Bronze","#58A6FF"), unsafe_allow_html=True)
        with k3: st.markdown(kpi(df_cat["dominio"].nunique(),"Domínios","#BC8CFF"), unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        busca_c = st.text_input("",placeholder="🔍 Pesquise por conceito, responsável, domínio ou ativo...",key="cat_busca")

        f1,f2,f3,f4,f5 = st.columns(5)
        with f1: f_dom = st.selectbox("DOMÍNIO",["Todos"]+sorted([d for d in df_cat["dominio"].unique() if d]),key="cf_dom")
        with f2: f_cam = st.selectbox("CAMADA",["Todas"]+sorted(df_cat["schema_name"].unique().tolist()),key="cf_cam")
        with f3: f_own = st.selectbox("OWNER",["Todos"]+sorted([o for o in df_cat["data_owner"].unique() if o]),key="cf_own")
        with f4: f_stw = st.selectbox("STEWARD",["Todos"]+sorted([s for s in df_cat["data_steward"].unique() if s]),key="cf_stw")
        with f5: f_doc = st.selectbox("DOCUMENTAÇÃO",["Todas","Documentadas","Sem documentação"],key="cf_doc")

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

        st.markdown(f'<div style="color:#8B949E;font-size:0.75rem;margin:8px 0;">{len(df_f)} ativo(s) encontrado(s)</div>', unsafe_allow_html=True)

        if "cat_sel" not in st.session_state:
            st.session_state["cat_sel"] = None

        rows_c = [df_f.iloc[i:i+3].reset_index(drop=True) for i in range(0,len(df_f),3)]
        for row_df in rows_c:
            cols_c = st.columns(3)
            for i,(_,item) in enumerate(row_df.iterrows()):
                cor_c  = "#3FB950" if item["score_completude"]==100 else "#C9A227" if item["score_completude"]>=60 else "#F85149"
                desc   = item["descricao"][:75]+"..." if item["descricao"] and len(item["descricao"])>75 else item["descricao"] or "Sem descrição"
                chave  = f"{item['schema_name']}.{item['table_name']}"
                is_sel = st.session_state["cat_sel"] == chave
                with cols_c[i]:
                    st.markdown(f"""
                    <div style="background:{'#C9A22708' if is_sel else '#161B22'};
                                border:1px solid {'#C9A227' if is_sel else '#30363D'};
                                border-radius:10px;padding:14px;margin-bottom:2px;">
                        <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                            <span style="color:#C9A227;font-weight:700;font-size:0.83rem;">{item['table_name']}</span>
                            <span style="color:{cor_c};font-weight:800;font-size:0.88rem;">{item['score_completude']}%</span>
                        </div>
                        <div style="color:#8B949E;font-size:0.73rem;line-height:1.4;margin-bottom:8px;">{desc}</div>
                        <div style="display:flex;gap:4px;flex-wrap:wrap;">
                            <span style="background:#58A6FF22;color:#58A6FF;border-radius:4px;padding:2px 7px;font-size:0.67rem;">{item['schema_name']}</span>
                            {f'<span style="background:#C9A22722;color:#C9A227;border-radius:4px;padding:2px 7px;font-size:0.67rem;">{item["dominio"]}</span>' if item['dominio'] else ''}
                            {f'<span style="background:#F8514922;color:#F85149;border-radius:4px;padding:2px 7px;font-size:0.67rem;">🔒 PII</span>' if item['tem_pii'] else ''}
                        </div>
                    </div>""", unsafe_allow_html=True)
                    if st.button(f"{'▼ Fechar' if is_sel else '▶ Detalhes'}",
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
                st.markdown(f"""
                <div style="background:#161B22;border:1px solid {cor_c2}44;border-radius:12px;padding:18px;margin-top:8px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                        <div style="color:#E6EDF3;font-size:1.05rem;font-weight:800;">{item['table_name']}</div>
                        <div style="color:{cor_c2};font-size:1.5rem;font-weight:800;">{item['score_completude']}%</div>
                    </div>
                    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">
                        <div style="background:#0D1117;border-radius:8px;padding:8px;"><div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;">DESCRIÇÃO</div><div style="color:#E6EDF3;font-size:0.78rem;">{item['descricao'] or '—'}</div></div>
                        <div style="background:#0D1117;border-radius:8px;padding:8px;"><div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;">DOMÍNIO</div><div style="color:#E6EDF3;font-size:0.78rem;">{item['dominio'] or '—'}</div></div>
                        <div style="background:#0D1117;border-radius:8px;padding:8px;"><div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;">OWNER</div><div style="color:#E6EDF3;font-size:0.78rem;">{item['data_owner'] or '—'}</div></div>
                        <div style="background:#0D1117;border-radius:8px;padding:8px;"><div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;">STEWARD</div><div style="color:#E6EDF3;font-size:0.78rem;">{item['data_steward'] or '—'}</div></div>
                        <div style="background:#0D1117;border-radius:8px;padding:8px;"><div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;">FUNÇÃO</div><div style="color:#E6EDF3;font-size:0.78rem;">{item['funcao_negocio'] or '—'}</div></div>
                        <div style="background:#0D1117;border-radius:8px;padding:8px;"><div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;">PII</div><div style="color:#F85149;font-size:0.78rem;">{'🔒 Contém dado pessoal' if item['tem_pii'] else '—'}</div></div>
                    </div>
                </div>""", unsafe_allow_html=True)

    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# 🏛️ DOMÍNIOS
# ════════════════════════════════════════════════════════════════════
elif pagina == "🏛️ Domínios":
    page_header("🏛️","Domínios de Dados Corporativos","Áreas de negócio responsáveis pela gestão e uso dos dados.")

    df_dom  = load_meta()
    df_glos = load_glossario()

    if not df_dom.empty:
        dominios = sorted([d for d in df_dom["dominio"].unique() if d])
        k1,k2,k3,k4,k5 = st.columns(5)
        with k1: st.markdown(kpi(len(dominios),"Domínios Ativos","#C9A227"), unsafe_allow_html=True)
        with k2: st.markdown(kpi(df_dom["data_owner"].nunique(),"Data Owners","#58A6FF"), unsafe_allow_html=True)
        with k3: st.markdown(kpi(df_dom["data_steward"].nunique(),"Data Stewards","#BC8CFF"), unsafe_allow_html=True)
        with k4: st.markdown(kpi(len(df_glos) if not df_glos.empty else 0,"Termos Vinculados","#3FB950"), unsafe_allow_html=True)
        with k5:
            cob = round(len(df_glos[df_glos["status"]=="homologado"])/max(len(df_glos),1)*100) if not df_glos.empty else 0
            st.markdown(kpi(f"{cob}%","Cobertura de Termos","#C9A227"), unsafe_allow_html=True)

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
                        <span style="color:{cor_d};font-weight:800;font-size:1rem;">{score:.0f}%</span>
                    </div>
                    <div style="background:#30363D;border-radius:4px;height:3px;margin:8px 0 6px;">
                        <div style="background:{cor_d};border-radius:4px;height:3px;width:{min(score,100):.0f}%;"></div>
                    </div>
                    <div style="font-size:0.68rem;color:#8B949E;">{len(df_d)} ativos · {n_t} termos</div>
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
                            <div style="color:{cor_d};font-size:2rem;font-weight:800;">{score:.0f}%</div>
                            <div style="color:#8B949E;font-size:0.65rem;">score de governança</div>
                        </div>
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:6px;">
                        <div style="background:#0D1117;border-radius:6px;padding:8px;text-align:center;">
                            <div style="color:#C9A227;font-size:1.3rem;font-weight:800;">{len(df_d)}</div>
                            <div style="color:#8B949E;font-size:0.62rem;">Ativos</div>
                        </div>
                        <div style="background:#0D1117;border-radius:6px;padding:8px;text-align:center;">
                            <div style="color:#58A6FF;font-size:1.3rem;font-weight:800;">{len(owners_d)}</div>
                            <div style="color:#8B949E;font-size:0.62rem;">Owners</div>
                        </div>
                        <div style="background:#0D1117;border-radius:6px;padding:8px;text-align:center;">
                            <div style="color:#BC8CFF;font-size:1.3rem;font-weight:800;">{len(stw_d)}</div>
                            <div style="color:#8B949E;font-size:0.62rem;">Stewards</div>
                        </div>
                        <div style="background:#0D1117;border-radius:6px;padding:8px;text-align:center;">
                            <div style="color:#3FB950;font-size:1.3rem;font-weight:800;">{n_t}</div>
                            <div style="color:#8B949E;font-size:0.62rem;">Termos</div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)

                dd1,dd2 = st.columns(2)
                with dd1:
                    st.markdown('<div style="background:#161B22;border:1px solid #30363D;border-radius:10px;padding:12px;margin-bottom:8px;">', unsafe_allow_html=True)
                    st.markdown('<div style="color:#8B949E;font-size:0.6rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">DATA OWNERS</div>', unsafe_allow_html=True)
                    for owner in owners_d:
                        nome_fmt = owner.replace("@meridian.com","").replace("."," ").title()
                        st.markdown(f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #21262D;">{avatar(nome_fmt,"#C9A227",32)}<div><div style="color:#E6EDF3;font-size:0.78rem;font-weight:600;">{nome_fmt}</div><div style="color:#8B949E;font-size:0.65rem;">Data Owner · {dom_sel}</div></div></div>', unsafe_allow_html=True)
                    if not owners_d:
                        st.markdown('<div style="color:#8B949E;font-size:0.75rem;">Nenhum owner definido</div>', unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                    st.markdown('<div style="background:#161B22;border:1px solid #30363D;border-radius:10px;padding:12px;">', unsafe_allow_html=True)
                    st.markdown('<div style="color:#8B949E;font-size:0.6rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">📋 ATIVOS DO DOMÍNIO</div>', unsafe_allow_html=True)
                    for _,row_t in df_d.iterrows():
                        cor_t = "#3FB950" if row_t["score_completude"]==100 else "#C9A227" if row_t["score_completude"]>=60 else "#F85149"
                        st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid #21262D;"><div><span style="color:#C9A227;font-size:0.75rem;font-weight:600;">{row_t["table_name"]}</span><span style="background:#58A6FF22;color:#58A6FF;border-radius:3px;padding:1px 5px;font-size:0.62rem;margin-left:5px;">{row_t["schema_name"]}</span></div><span style="color:{cor_t};font-weight:700;font-size:0.78rem;">{row_t["score_completude"]}%</span></div>', unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                with dd2:
                    st.markdown('<div style="background:#161B22;border:1px solid #30363D;border-radius:10px;padding:12px;margin-bottom:8px;">', unsafe_allow_html=True)
                    st.markdown('<div style="color:#8B949E;font-size:0.6rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">DATA STEWARDS</div>', unsafe_allow_html=True)
                    for stw in stw_d:
                        nome_stw = stw.replace("@meridian.com","").replace("."," ").title()
                        st.markdown(f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #21262D;">{avatar(nome_stw,"#58A6FF",32)}<div><div style="color:#E6EDF3;font-size:0.78rem;font-weight:600;">{nome_stw}</div><div style="color:#8B949E;font-size:0.65rem;">Data Steward · {dom_sel}</div></div></div>', unsafe_allow_html=True)
                    if not stw_d:
                        st.markdown('<div style="color:#8B949E;font-size:0.75rem;">Nenhum steward definido</div>', unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                    if not df_glos.empty:
                        termos_dom = df_glos[df_glos["dominio"]==dom_sel]
                        if not termos_dom.empty:
                            st.markdown('<div style="background:#161B22;border:1px solid #30363D;border-radius:10px;padding:12px;">', unsafe_allow_html=True)
                            st.markdown('<div style="color:#8B949E;font-size:0.6rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">📖 TERMOS DO GLOSSÁRIO</div>', unsafe_allow_html=True)
                            for _,t in termos_dom.iterrows():
                                cor_ts = {"homologado":"#3FB950","em_revisao":"#58A6FF","rascunho":"#8B949E"}.get(t["status"],"#8B949E")
                                st.markdown(f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #21262D;"><span style="color:#E6EDF3;font-size:0.75rem;">{t["termo"]}</span><span style="color:{cor_ts};font-size:0.68rem;">● {t["status"]}</span></div>', unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;padding:40px;text-align:center;margin-top:10px;">
                    <div style="font-size:2rem;margin-bottom:10px;">🏛️</div>
                    <div style="color:#E6EDF3;font-weight:700;margin-bottom:6px;">Selecione um domínio</div>
                    <div style="color:#8B949E;font-size:0.82rem;">Clique em "Ver detalhes" para visualizar responsáveis, ativos e termos vinculados.</div>
                </div>""", unsafe_allow_html=True)

    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# 🛡️ SCORECARD
# ════════════════════════════════════════════════════════════════════
elif pagina == "🛡️ Scorecard":
    page_header("🛡️","Scorecard de Confiabilidade","Visão objetiva da maturidade dos dados por pilar, domínio e responsável.")

    df_sc    = load_meta()
    df_links = load_links()

    if df_sc.empty:
        st.error("Não foi possível carregar os dados.")
    else:
        dominios_sc = ["Todos"]+sorted([d for d in df_sc["dominio"].unique() if d])
        f_dom_sc = st.selectbox("🏛️ Filtrar por Domínio", dominios_sc, key="sc_dom")
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
            <div style="font-size:0.7rem;color:#8B949E;text-transform:uppercase;letter-spacing:2px;margin-bottom:4px;">Score Geral de Confiabilidade</div>
            <div style="font-size:3.5rem;font-weight:800;color:{cor_g};line-height:1;">{ger:.0f}%</div>
            <div style="color:#8B949E;font-size:0.75rem;margin-top:4px;">
                Baseado em 5 pilares: Documentação, Ownership, Relacionamentos, Qualidade e Certificação</div>
        </div>""", unsafe_allow_html=True)

        PILARES_INFO = {
            "Documentação":  {"icone":"📝","cor":"#58A6FF","val":doc,"conceito":"Mede se os ativos possuem descrição de negócio preenchida. Uma boa documentação permite que qualquer usuário entenda o propósito do dado sem precisar consultar o time técnico.","como_melhorar":"Acesse Curadoria → Individual e preencha a descrição de cada tabela. Use 'Sugerir com IA' para acelerar."},
            "Ownership":     {"icone":"👤","cor":"#C9A227","val":own,"conceito":"Avalia se cada ativo possui um Data Owner formalmente definido. O Owner é o responsável de negócio pelo dado — quem responde pela qualidade e uso correto.","como_melhorar":"Acesse Curadoria → Individual ou Em Lote e atribua um Data Owner para os ativos sem responsável."},
            "Relacionamentos":{"icone":"🔗","cor":"#BC8CFF","val":rel,"conceito":"Verifica se os ativos técnicos estão conectados a conceitos de negócio do Glossário. Ativos conectados são mais fáceis de descobrir e entender pelo negócio.","como_melhorar":"Acesse o Glossário → Relacionamentos e vincule cada termo às tabelas correspondentes."},
            "Qualidade":     {"icone":"⭐","cor":"#3FB950","val":qual,"conceito":"Score médio de completude dos metadados (0 a 100%). Calculado com base nos 5 campos obrigatórios: Descrição, Domínio, Owner, Steward e Função de Negócio.","como_melhorar":"Preencha todos os campos obrigatórios na Curadoria. Cada campo vale 20 pontos no score."},
            "Certificação":  {"icone":"🏆","cor":"#F85149","val":cert,"conceito":"Percentual de ativos com score 100% — todos os 5 campos obrigatórios preenchidos. Ativos certificados estão prontos para uso confiável pelo negócio.","como_melhorar":"Complete todos os 5 campos de metadados de cada ativo para atingir o selo Certificado."},
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
                if st.button(f"{'▼ Fechar' if is_sel else '▶ Detalhe'}",
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
                        <div style="color:#8B949E;font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">💡 CONCEITO</div>
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
            elif pilar_sel == "Ownership":
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

        section_divider("RANKING DE OWNERS")
        df_own = df_sc_f[df_sc_f["data_owner"].apply(bool)]\
                    .groupby("data_owner")["score_completude"].mean()\
                    .reset_index().sort_values("score_completude",ascending=False)\
                    .reset_index(drop=True)
        for i,(_,row) in enumerate(df_own.iterrows()):
            cor_o   = "#3FB950" if row["score_completude"]>=80 else "#C9A227" if row["score_completude"]>=60 else "#F85149"
            medalha = ["🥇","🥈","🥉"][i] if i<3 else f"#{i+1}"
            nome_fmt = row['data_owner'].replace("@meridian.com","").replace("."," ").title()
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                        background:#161B22;border:1px solid #30363D;border-radius:8px;
                        padding:9px 14px;margin-bottom:5px;">
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="font-size:1rem;width:28px;text-align:center;">{medalha}</span>
                    {avatar(nome_fmt,"#C9A227",28)}
                    <span style="color:#E6EDF3;font-size:0.82rem;">{nome_fmt}</span>
                </div>
                <div style="display:flex;align-items:center;gap:10px;">
                    <div style="background:#30363D;border-radius:4px;height:5px;width:100px;">
                        <div style="background:{cor_o};border-radius:4px;height:5px;width:{min(row['score_completude'],100):.0f}%;"></div>
                    </div>
                    <span style="color:{cor_o};font-weight:700;font-size:0.82rem;width:36px;text-align:right;">{row['score_completude']:.0f}%</span>
                </div>
            </div>""", unsafe_allow_html=True)

    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# ⚡ MEU ESPAÇO
# ════════════════════════════════════════════════════════════════════
elif pagina == "⚡ Meu Espaço":
    page_header("⚡",f"Olá, {u['nome']} 👋","Suas pendências, responsabilidades e atividades de governança.")

    df_meta  = load_meta()
    df_gloss = load_glossario()

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

    section_divider("O QUE PRECISO FAZER AGORA?")
    for tipo,msg,cor_a,dest,qtd in [
        ("APROVAR",f"{pend_aprov} termos aguardam aprovação","#C9A227","→ Workflow",pend_aprov),
        ("DOCUMENTAR",f"{sem_desc} ativos sem descrição","#58A6FF","→ Curadoria",sem_desc),
        ("ATRIBUIR",f"{sem_owner} ativos sem Owner definido","#F85149","→ Curadoria",sem_owner),
        ("ALOCAR",f"{sem_steward} ativos sem Steward definido","#FF7B72","→ Curadoria",sem_steward),
        ("CLASSIFICAR",f"{sem_dom} ativos sem domínio","#BC8CFF","→ Curadoria",sem_dom),
    ]:
        if qtd>0:
            st.markdown(f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:11px 16px;margin-bottom:6px;display:flex;align-items:center;justify-content:space-between;"><div style="display:flex;align-items:center;gap:10px;"><span style="background:{cor_a}22;color:{cor_a};border-radius:4px;padding:2px 8px;font-size:0.65rem;font-weight:700;">{tipo}</span><span style="color:#E6EDF3;font-size:0.82rem;">{msg}</span></div><span style="color:#8B949E;font-size:0.72rem;">{dest}</span></div>', unsafe_allow_html=True)

    section_divider("MINHAS RESPONSABILIDADES")
    if not df_meta.empty:
        k1,k2,k3,k4 = st.columns(4)
        with k1: st.markdown(kpi(len(df_meta[df_meta["data_owner"]==usuario]),"Como Owner","#C9A227"), unsafe_allow_html=True)
        with k2: st.markdown(kpi(len(df_meta[df_meta["data_steward"]==usuario]),"Como Steward","#58A6FF"), unsafe_allow_html=True)
        with k3: st.markdown(kpi(df_meta["dominio"].nunique(),"Domínios Acompanhados","#BC8CFF"), unsafe_allow_html=True)
        with k4:
            doc_media = df_meta["score_completude"].mean()
            cor_d = "#3FB950" if doc_media>=80 else "#C9A227" if doc_media>=60 else "#F85149"
            st.markdown(kpi(f"{doc_media:.0f}%","Documentação Média",cor_d), unsafe_allow_html=True)

    if is_aprovador and pend_aprov>0:
        section_divider("MINHAS APROVAÇÕES")
        for _,row in df_gloss[df_gloss["status"]=="em_revisao"].iterrows():
            with st.expander(f"📋 **{row['termo']}** · {row['dominio']} · {row['criticidade']}"):
                st.markdown(f"**Definição:** {row['definicao']}")
                ca,cr = st.columns(2)
                with ca:
                    if st.button("✅ Aprovar",key=f"mea_{row['glossary_id']}",use_container_width=True):
                        ok,_ = exe(f"UPDATE meridian_governanca.business_glossary SET status='homologado',atualizado_por='{esc(usuario)}',atualizado_em=current_timestamp() WHERE glossary_id='{row['glossary_id']}'")
                        if ok: st.success("✅ Homologado!"); st.cache_data.clear(); st.rerun()
                with cr:
                    motivo = st.text_input("Motivo",key=f"mem_{row['glossary_id']}")
                    if st.button("❌ Rejeitar",key=f"mer_{row['glossary_id']}",use_container_width=True):
                        if motivo:
                            ok,_ = exe(f"UPDATE meridian_governanca.business_glossary SET status='rascunho',atualizado_por='{esc(usuario)}',atualizado_em=current_timestamp() WHERE glossary_id='{row['glossary_id']}'")
                            if ok: st.warning("↩️ Devolvido."); st.cache_data.clear(); st.rerun()
                        else: st.warning("Informe o motivo.")

    section_divider("MEUS TERMOS NO GLOSSÁRIO")
    df_meus = df_gloss[df_gloss["steward_email"]==usuario] if not df_gloss.empty else pd.DataFrame()
    if not df_meus.empty:
        for _,row in df_meus.iterrows():
            cor_s = {"homologado":"#3FB950","em_revisao":"#58A6FF","rascunho":"#8B949E"}.get(row["status"],"#8B949E")
            st.markdown(f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:9px 14px;margin-bottom:5px;display:flex;justify-content:space-between;align-items:center;"><span style="color:#E6EDF3;font-size:0.82rem;font-weight:600;">{row["termo"]}</span><span style="color:{cor_s};font-size:0.75rem;font-weight:600;">● {row["status"].replace("_"," ").title()}</span></div>', unsafe_allow_html=True)
    else:
        st.info("Nenhum termo vinculado ao seu e-mail.")

    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# ✏️ CURADORIA
# ════════════════════════════════════════════════════════════════════
elif pagina == "✏️ Curadoria":
    page_header("✏️","Curadoria de Conhecimento","Enriqueça o entendimento — documente, classifique e atribua responsáveis.")

    df_cur = load_meta()
    if not df_cur.empty:
        cur1,cur2 = st.tabs(["📋 Individual","⚡ Em Lote"])
        with cur1:
            c_left,c_right = st.columns([1,2])
            with c_left:
                sel_s = st.selectbox("SCHEMA",sorted(df_cur["schema_name"].unique().tolist()),key="cur_s")
                sel_t = st.selectbox("TABELA",df_cur[df_cur["schema_name"]==sel_s]["table_name"].tolist(),key="cur_t")
            with c_right:
                row = df_cur[(df_cur["schema_name"]==sel_s)&(df_cur["table_name"]==sel_t)].iloc[0]
                doc_p  = 100 if row["descricao"] else 0
                own_p  = 100 if row["data_owner"] else 0
                cert_p = 100 if row["selo"]=="certificado" else 0
                qual_p = row["score_completude"]

                st.markdown(f'<div style="background:#161B22;border:1px solid #30363D;border-radius:10px;padding:12px 16px;margin-bottom:12px;"><div style="color:#C9A227;font-weight:700;font-size:0.9rem;">{sel_t}</div><div style="color:#8B949E;font-size:0.72rem;margin-top:2px;">{row["descricao"][:60]+"..." if row["descricao"] and len(row["descricao"])>60 else row["descricao"] or "Sem descrição"}</div></div>', unsafe_allow_html=True)

                pp1,pp2,pp3,pp4,pp5 = st.columns(5)
                for pcol,pn,pv in [(pp1,"DOCUMENTAÇÃO",doc_p),(pp2,"OWNERSHIP",own_p),(pp3,"RELACION.",0),(pp4,"QUALIDADE",qual_p),(pp5,"CERTIFICAÇÃO",cert_p)]:
                    cor_pp = "#3FB950" if pv>=80 else "#C9A227" if pv>0 else "#F85149"
                    with pcol:
                        st.markdown(f'<div style="background:#0D1117;border:1px solid #30363D;border-radius:8px;padding:9px;text-align:center;margin-bottom:10px;"><div style="font-size:0.55rem;color:#8B949E;text-transform:uppercase;letter-spacing:0.8px;">{pn}</div><div style="font-size:1.1rem;font-weight:800;color:{cor_pp};">{f"{pv}%" if pv>0 else "—"}</div></div>', unsafe_allow_html=True)

                ed1,ed2 = st.columns(2)
                with ed1:
                    new_desc = st.text_area("DESCRIÇÃO",value=row["descricao"] or "",height=80,key="c_desc",placeholder="Descreva o propósito desta tabela...")
                    doms = ["","Crédito","Pagamentos","Clientes","Compliance","Produtos"]
                    dom_i = doms.index(row["dominio"]) if row["dominio"] in doms else 0
                    new_dom = st.selectbox("DOMÍNIO",doms,index=dom_i,key="c_dom")
                with ed2:
                    new_own = st.text_input("DATA OWNER",value=row["data_owner"] or "",key="c_own")
                    new_stw = st.text_input("DATA STEWARD",value=row["data_steward"] or "",key="c_stw")

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
                        else: st.error(f"Erro: {err}")
                with bc2:
                    if st.button("🤖 Sugerir com IA",key="c_ai",use_container_width=True):
                        sugestoes = {"clientes_raw":("Dados brutos de clientes ingeridos do sistema core bancário.","Clientes"),"contas_raw":("Dados brutos de contas correntes e poupança dos clientes.","Clientes"),"transacoes_raw":("Transações financeiras brutas de todos os canais.","Pagamentos"),"propostas_credito_raw":("Propostas de crédito com status de aprovação.","Crédito"),"pix_raw":("Transações PIX brutas do SPI do Banco Central.","Pagamentos"),"dim_clientes":("Dimensão de clientes tratada e enriquecida.","Clientes"),"dim_contas":("Dimensão de contas com dados consolidados.","Clientes"),"fato_transacoes":("Fato de transações financeiras por período e canal.","Pagamentos"),"fato_credito":("Fato de operações de crédito aprovadas e recusadas.","Crédito"),"fato_inadimplencia":("Fato de inadimplência com dias de atraso.","Crédito"),"fato_pix":("Fato de transações PIX consolidadas.","Pagamentos"),"dim_produtos":("Dimensão de produtos financeiros do banco.","Produtos"),"indicadores_carteira":("Indicadores consolidados da carteira de crédito.","Crédito"),"perfil_cliente_360":("Visão 360 do cliente com score e churn.","Clientes"),"dashboard_inadimplencia":("Base para dashboard executivo de inadimplência.","Crédito"),"indicadores_pix":("Indicadores de volume e performance do PIX.","Pagamentos"),"base_lgpd":("Mapeamento de dados pessoais para conformidade LGPD.","Compliance")}
                        sug = sugestoes.get(sel_t,(f"Tabela {sel_t} do schema {sel_s}.",""))
                        st.session_state["ai_desc"] = sug[0]; st.session_state["ai_dom"] = sug[1]; st.rerun()

                if "ai_desc" in st.session_state:
                    st.markdown('<div style="background:#C9A22711;border:1px solid #C9A22733;border-radius:8px;padding:10px 14px;margin-top:8px;"><div style="color:#C9A227;font-weight:700;font-size:0.75rem;">🤖 Sugestão da IA — revise antes de salvar</div></div>', unsafe_allow_html=True)
                    sug_d = st.text_area("Descrição sugerida",value=st.session_state["ai_desc"],key="sug_d")
                    so = ["","Crédito","Pagamentos","Clientes","Compliance","Produtos"]
                    sv = st.session_state["ai_dom"]; si = so.index(sv) if sv in so else 0
                    sug_dom = st.selectbox("Domínio sugerido",so,index=si,key="sd2")
                    sa1,sa2 = st.columns(2)
                    with sa1:
                        if st.button("✅ Aceitar",key="ai_ac",use_container_width=True):
                            filled = sum([bool(sug_d),bool(sug_dom),bool(new_own),bool(new_stw),bool(row["funcao_negocio"])]); ns = filled*20; sl = "certificado" if ns==100 else "parcial" if ns>=60 else "pendente"
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
            with f2c: fl_sl = st.selectbox("Selo",["Todos","certificado","parcial","pendente"],key="lote_sl")
            df_l = df_cur.copy()
            if fl_s  != "Todos": df_l = df_l[df_l["schema_name"]==fl_s]
            if fl_sl != "Todos": df_l = df_l[df_l["selo"]==fl_sl]
            df_led = df_l[["schema_name","table_name","score_completude","selo"]].copy()
            df_led.insert(0,"Selecionar",False)
            edited = st.data_editor(df_led.rename(columns={"schema_name":"Schema","table_name":"Tabela","score_completude":"Score","selo":"Selo"}),use_container_width=True,hide_index=True,column_config={"Selecionar":st.column_config.CheckboxColumn()})
            sels = edited[edited["Selecionar"]==True]
            if len(sels)>0:
                st.markdown(f'<div style="color:#C9A227;font-size:0.82rem;margin:6px 0;">{len(sels)} tabela(s) selecionada(s)</div>', unsafe_allow_html=True)
                lb1,lb2,lb3 = st.columns(3)
                with lb1: l_dom = st.selectbox("Domínio",["","Crédito","Pagamentos","Clientes","Compliance","Produtos"],key="l_dom")
                with lb2: l_own = st.text_input("Owner",key="l_own")
                with lb3: l_stw = st.text_input("Steward",key="l_stw")
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
                    if erros: st.warning(f"Erros: {erros}")
                    else: st.success(f"✅ {len(sels)} tabelas atualizadas!"); st.cache_data.clear(); st.rerun()

    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# 🕐 AUDITORIA
# ════════════════════════════════════════════════════════════════════
elif pagina == "🕐 Auditoria":
    page_header("🕐","Trilha de Auditoria","Rastreabilidade — quem alterou, quando e por quê.")

    df_aud,err = qry("SELECT timestamp_op, schema_name, table_name, tipo_objeto, campo_alterado, valor_anterior, valor_novo, origem, alterado_por FROM meridian_governanca.metadata_audit ORDER BY timestamp_op DESC LIMIT 500")

    if err: st.error(f"Erro: {err}")
    elif df_aud.empty:
        st.markdown('<div style="background:#161B22;border:1px solid #30363D;border-radius:12px;padding:40px;text-align:center;"><div style="font-size:2.5rem;margin-bottom:10px;">📭</div><div style="color:#E6EDF3;font-weight:700;">Nenhum registro ainda</div><div style="color:#8B949E;margin-top:6px;font-size:0.82rem;">As alterações feitas na Curadoria e no Glossário aparecerão aqui.</div></div>', unsafe_allow_html=True)
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
        with af3: f_lim = st.selectbox("Linhas",[50,100,200,500],key="a_lim")

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
