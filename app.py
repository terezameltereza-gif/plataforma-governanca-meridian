"""
app.py — Plataforma de Governança de Dados
Banco Meridian | v3.0
"""
import streamlit as st
import pandas as pd
from databricks import sql
import plotly.express as px
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
    padding: 8px 20px !important;
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
}
section[data-testid="stSidebar"] * { color: #E6EDF3 !important; }
div[data-testid="stRadio"] > div { gap: 2px !important; }
div[data-testid="stRadio"] label {
    background: transparent !important; border: none !important;
    border-radius: 6px !important; padding: 6px 10px !important;
    color: #8B949E !important; font-size: 0.85rem !important;
    cursor: pointer !important; width: 100% !important;
    display: block !important;
}
div[data-testid="stRadio"] label:hover {
    background: #161B22 !important; color: #E6EDF3 !important;
}
div[data-testid="stRadio"] label[data-selected="true"] {
    background: #C9A22722 !important; color: #C9A227 !important;
    font-weight: 600 !important;
}
.stDataFrame { background: #161B22 !important; }
.stDataFrame td, .stDataFrame th {
    background: #161B22 !important; color: #E6EDF3 !important;
    border-color: #30363D !important;
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
# SIDEBAR
# ════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Logo
    st.markdown("""
    <div style="padding:16px 8px 8px;display:flex;align-items:center;gap:10px;">
        <div style="background:linear-gradient(135deg,#C9A227,#E6C84A);border-radius:8px;
                    width:36px;height:36px;display:flex;align-items:center;
                    justify-content:center;font-size:1.1rem;flex-shrink:0;">🏦</div>
        <div>
            <div style="font-size:0.78rem;font-weight:800;color:#E6EDF3;
                        line-height:1.1;">PLATAFORMA DE DADOS</div>
            <div style="font-size:0.65rem;color:#8B949E;">GOVERNANÇA CORPORATIVA</div>
        </div>
    </div>
    <div style="height:1px;background:#30363D;margin:8px 0 12px;"></div>
    """, unsafe_allow_html=True)

    # Login
    if "usuario" not in st.session_state:
        st.session_state["usuario"] = None

    if not st.session_state["usuario"]:
        email = st.selectbox("Usuário demo:", list(USUARIOS.keys()),
            format_func=lambda x: f"{USUARIOS[x]['nome']} · {USUARIOS[x]['perfil']}")
        if st.button("Entrar →", key="login"):
            st.session_state["usuario"] = email
            st.rerun()
        st.stop()

    u      = USUARIOS[st.session_state["usuario"]]
    perfil = u["perfil"]
    cor    = PERFIL_COR[perfil]

    st.markdown(f"""
    <div style="background:#161B22;border:1px solid #30363D;border-radius:8px;
                padding:8px 10px;margin-bottom:12px;">
        <div style="font-size:0.65rem;color:#8B949E;text-transform:uppercase;
                    letter-spacing:1px;">Usuário logado</div>
        <div style="font-weight:700;color:#E6EDF3;font-size:0.85rem;">{u['nome']}</div>
        <div style="color:{cor};font-size:0.75rem;font-weight:600;">
            {PERFIL_LABEL[perfil]}</div>
    </div>
    """, unsafe_allow_html=True)

    def nav_label(txt):
        st.markdown(f'<div style="color:#8B949E;font-size:0.65rem;font-weight:700;'
                    f'text-transform:uppercase;letter-spacing:1.5px;'
                    f'padding:8px 10px 2px;">{txt}</div>', unsafe_allow_html=True)

    nav_label("PESSOAL")
    p1 = ["⚡ Meu Espaço"]
    nav_label("DESCOBERTA")
    p2 = ["🏠 Início","📋 Catálogo","📖 Glossário","🏛️ Domínios"]
    nav_label("CONFIABILIDADE")
    p3 = ["🛡️ Scorecard"]
    nav_label("OPERAÇÃO")
    p4 = ["✏️ Curadoria","🕐 Auditoria"]

    pagina = st.radio("", p1+p2+p3+p4, key="nav", label_visibility="collapsed")

    st.markdown('<div style="height:1px;background:#30363D;margin:12px 0 8px;"></div>',
                unsafe_allow_html=True)
    if st.button("Sair", key="logout"):
        st.session_state["usuario"] = None
        st.rerun()

usuario      = st.session_state["usuario"]
u            = USUARIOS[usuario]
perfil       = u["perfil"]
is_curador   = perfil in ["curador","aprovador"]
is_aprovador = perfil == "aprovador"

# ════════════════════════════════════════════════════════════════════
# COMPONENTES
# ════════════════════════════════════════════════════════════════════
def page_header(icone, titulo, subtitulo=""):
    cor = PERFIL_COR[perfil]
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#161B22,#1C2128);
                border:1px solid #30363D;border-radius:12px;
                padding:16px 20px;margin-bottom:20px;
                display:flex;align-items:center;justify-content:space-between;">
        <div style="display:flex;align-items:center;gap:12px;">
            <div style="background:#C9A22722;border-radius:8px;padding:10px;
                        font-size:1.3rem;">{icone}</div>
            <div>
                <div style="color:#E6EDF3;font-size:1.1rem;font-weight:800;">{titulo}</div>
                {f'<div style="color:#8B949E;font-size:0.78rem;">{subtitulo}</div>'
                 if subtitulo else ''}
            </div>
        </div>
        <div style="text-align:right;">
            <div style="color:{cor};font-size:0.75rem;font-weight:600;">
                {PERFIL_LABEL[perfil]}</div>
            <div style="color:#8B949E;font-size:0.7rem;">{u['nome']}</div>
        </div>
    </div>""", unsafe_allow_html=True)

def kpi(valor, label, cor="#C9A227", icone=""):
    return f"""<div style="background:#161B22;border:1px solid #30363D;
        border-radius:10px;padding:14px 16px;border-top:3px solid {cor};">
        <div style="font-size:0.65rem;color:#8B949E;font-weight:700;
                    text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">
            {icone} {label}</div>
        <div style="font-size:1.8rem;font-weight:800;color:{cor};">{valor}</div>
    </div>"""

def badge(txt, cor="#C9A227"):
    return f'<span style="background:{cor}22;color:{cor};border-radius:4px;'\
           f'padding:2px 8px;font-size:0.7rem;font-weight:600;'\
           f'border:1px solid {cor}44;">{txt}</span>'

# ════════════════════════════════════════════════════════════════════
# DADOS COMPARTILHADOS
# ════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def load_meta():
    df, _ = qry("SELECT * FROM meridian_governanca.tabelas_metadata")
    return df

@st.cache_data(ttl=300)
def load_glossario():
    df, _ = qry("""SELECT * FROM meridian_governanca.business_glossary
                   ORDER BY CASE status WHEN 'homologado' THEN 1
                   WHEN 'em_revisao' THEN 2 ELSE 3 END, termo""")
    return df

# ════════════════════════════════════════════════════════════════════
# ⚡ MEU ESPAÇO
# ════════════════════════════════════════════════════════════════════
if pagina == "⚡ Meu Espaço":
    page_header("⚡", f"Olá, {u['nome']} 👋",
                "Você possui ações pendentes na sua área de trabalho.")

    df_meta  = load_meta()
    df_gloss = load_glossario()

    # ── Ações pendentes ──────────────────────────────────────────────
    pendentes_aprovacao = len(df_gloss[df_gloss["status"]=="em_revisao"]) \
                          if not df_gloss.empty else 0
    sem_descricao = len(df_meta[df_meta["descricao"]==""]) \
                    if not df_meta.empty else 0
    sem_owner = len(df_meta[df_meta["data_owner"]==""]) \
                if not df_meta.empty else 0
    sem_dominio = len(df_meta[df_meta["dominio"]==""]) \
                  if not df_meta.empty else 0

    st.markdown('<div style="color:#E6EDF3;font-weight:700;font-size:0.95rem;'
                'margin-bottom:10px;">⚡ O que preciso fazer agora?</div>',
                unsafe_allow_html=True)

    acoes = [
        ("APROVAR",     f"{pendentes_aprovacao} termos aguardam aprovação",
         "#C9A227", "→ Workflow", pendentes_aprovacao > 0),
        ("DOCUMENTAR",  f"{sem_descricao} ativos sem descrição",
         "#58A6FF", "→ Curadoria", sem_descricao > 0),
        ("ATRIBUIR",    f"{sem_owner} ativos sem Owner definido",
         "#F85149", "→ Curadoria", sem_owner > 0),
        ("CLASSIFICAR", f"{sem_dominio} ativos sem domínio",
         "#BC8CFF", "→ Curadoria", sem_dominio > 0),
    ]

    for tipo, msg, cor_a, destino, tem in acoes:
        if tem:
            st.markdown(f"""
            <div style="background:#161B22;border:1px solid #30363D;border-radius:8px;
                        padding:12px 16px;margin-bottom:8px;
                        display:flex;align-items:center;justify-content:space-between;">
                <div style="display:flex;align-items:center;gap:12px;">
                    <span style="background:{cor_a}22;color:{cor_a};border-radius:4px;
                                 padding:2px 8px;font-size:0.7rem;font-weight:700;">
                        {tipo}</span>
                    <span style="color:#E6EDF3;font-size:0.85rem;">{msg}</span>
                </div>
                <span style="color:#8B949E;font-size:0.78rem;">{destino}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── KPIs pessoais ────────────────────────────────────────────────
    st.markdown('<div style="color:#E6EDF3;font-weight:700;font-size:0.95rem;'
                'margin-bottom:10px;">🏛️ Meus Domínios e Ativos</div>',
                unsafe_allow_html=True)

    if not df_meta.empty:
        como_owner   = len(df_meta[df_meta["data_owner"]==usuario])
        como_steward = len(df_meta[df_meta["data_steward"]==usuario])
        dominios_uniq = df_meta["dominio"].nunique()
        doc_media    = df_meta["score_completude"].mean()

        k1,k2,k3,k4 = st.columns(4)
        with k1: st.markdown(kpi(como_owner,"Como Owner","#C9A227"),
                             unsafe_allow_html=True)
        with k2: st.markdown(kpi(como_steward,"Como Steward","#58A6FF"),
                             unsafe_allow_html=True)
        with k3: st.markdown(kpi(dominios_uniq,"Domínios Acompanhados","#BC8CFF"),
                             unsafe_allow_html=True)
        with k4:
            cor_doc = "#3FB950" if doc_media>=80 else \
                      "#C9A227" if doc_media>=60 else "#F85149"
            st.markdown(kpi(f"{doc_media:.0f}%","Documentação Média",cor_doc),
                        unsafe_allow_html=True)

    # ── Fila de aprovação (aprovadores) ──────────────────────────────
    if is_aprovador and pendentes_aprovacao > 0:
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown('<div style="color:#E6EDF3;font-weight:700;font-size:0.95rem;'
                    'margin-bottom:10px;">📋 Fila de Aprovação</div>',
                    unsafe_allow_html=True)
        df_pend = df_gloss[df_gloss["status"]=="em_revisao"]
        for _, row in df_pend.iterrows():
            with st.expander(
                f"📋 **{row['termo']}** · {row['dominio']} · {row['criticidade']}"
            ):
                st.markdown(f"**Definição:** {row['definicao']}")
                st.markdown(f"**Área:** {row['area_negocio']} · "
                            f"**Steward:** {row['steward_email']}")
                ca, cr = st.columns(2)
                with ca:
                    if st.button("✅ Aprovar", key=f"mea_{row['glossary_id']}"):
                        ok, _ = exe(f"""UPDATE meridian_governanca.business_glossary
                            SET status='homologado',atualizado_por='{esc(usuario)}',
                            atualizado_em=current_timestamp()
                            WHERE glossary_id='{row['glossary_id']}'""")
                        if ok:
                            st.success("✅ Homologado!")
                            st.cache_data.clear(); st.rerun()
                with cr:
                    motivo = st.text_input("Motivo", key=f"mem_{row['glossary_id']}")
                    if st.button("❌ Rejeitar", key=f"mer_{row['glossary_id']}"):
                        if motivo:
                            ok, _ = exe(f"""UPDATE meridian_governanca.business_glossary
                                SET status='rascunho',atualizado_por='{esc(usuario)}',
                                atualizado_em=current_timestamp()
                                WHERE glossary_id='{row['glossary_id']}'""")
                            if ok:
                                st.warning("↩️ Devolvido para rascunho.")
                                st.cache_data.clear(); st.rerun()
                        else: st.warning("Informe o motivo.")

    # ── Meus termos (curadores) ───────────────────────────────────────
    if is_curador:
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown('<div style="color:#E6EDF3;font-weight:700;font-size:0.95rem;'
                    'margin-bottom:10px;">📖 Meus Termos no Glossário</div>',
                    unsafe_allow_html=True)
        df_meus = df_gloss[df_gloss["steward_email"]==usuario] \
                  if not df_gloss.empty else pd.DataFrame()
        if not df_meus.empty:
            for _, row in df_meus.iterrows():
                cor_s = {"homologado":"#3FB950","em_revisao":"#58A6FF",
                         "rascunho":"#8B949E"}.get(row["status"],"#8B949E")
                st.markdown(f"""
                <div style="background:#161B22;border:1px solid #30363D;border-radius:8px;
                            padding:10px 14px;margin-bottom:6px;
                            display:flex;justify-content:space-between;align-items:center;">
                    <span style="color:#E6EDF3;font-size:0.85rem;font-weight:600;">
                        {row['termo']}</span>
                    <span style="color:{cor_s};font-size:0.78rem;font-weight:600;">
                        ● {row['status'].replace('_',' ').title()}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Nenhum termo vinculado ao seu e-mail.")

# ════════════════════════════════════════════════════════════════════
# 🏠 INÍCIO
# ════════════════════════════════════════════════════════════════════
elif pagina == "🏠 Início":
    # Header com última atualização
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#161B22,#1C2128);
                border:1px solid #30363D;border-radius:12px;
                padding:16px 20px;margin-bottom:20px;
                display:flex;justify-content:space-between;align-items:center;">
        <div style="display:flex;align-items:center;gap:12px;">
            <div style="background:#C9A22722;border-radius:8px;padding:10px;font-size:1.3rem;">🏦</div>
            <div>
                <div style="color:#E6EDF3;font-size:1.2rem;font-weight:800;">
                    Plataforma de Governança de Dados</div>
                <div style="color:#8B949E;font-size:0.78rem;">
                    Um único ambiente para descobrir, entender e confiar nos dados.</div>
            </div>
        </div>
        <div style="text-align:right;">
            <div style="color:#8B949E;font-size:0.72rem;">Última atualização: {now_str}</div>
            <div style="background:#3FB95022;color:#3FB950;border-radius:20px;
                        padding:2px 10px;font-size:0.72rem;font-weight:600;
                        border:1px solid #3FB95044;margin-top:4px;">● AO VIVO</div>
        </div>
    </div>""", unsafe_allow_html=True)

    df_meta  = load_meta()
    df_gloss = load_glossario()

    total_ativos = len(df_meta) if not df_meta.empty else 0
    total_dom    = df_meta["dominio"].nunique() if not df_meta.empty else 0
    total_termos = len(df_gloss) if not df_gloss.empty else 0
    score_medio  = df_meta["score_completude"].mean() if not df_meta.empty else 0

    k1,k2,k3,k4,k5 = st.columns(5)
    with k1: st.markdown(kpi(total_ativos,"Ativos Catalogados","#C9A227","🗂️"),
                         unsafe_allow_html=True)
    with k2: st.markdown(kpi(total_dom,"Domínios de Negócio","#58A6FF","🏛️"),
                         unsafe_allow_html=True)
    with k3: st.markdown(kpi(total_termos,"Termos de Negócio","#BC8CFF","📖"),
                         unsafe_allow_html=True)
    with k4:
        cor_s = "#3FB950" if score_medio>=80 else \
                "#C9A227" if score_medio>=60 else "#F85149"
        st.markdown(kpi(f"{score_medio:.0f}%","Score Médio de Confiabilidade",cor_s,"🛡️"),
                    unsafe_allow_html=True)
    with k5: st.markdown(kpi("100%","Rastreabilidade e Auditoria","#3FB950","✅"),
                         unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    col_cat, col_sc, col_dom = st.columns(3)

    with col_cat:
        st.markdown("""<div style="background:#161B22;border:1px solid #30363D;
            border-radius:12px;padding:16px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
                <div style="background:#C9A22722;border-radius:6px;padding:6px;font-size:1rem;">🗂️</div>
                <div style="color:#E6EDF3;font-weight:700;font-size:0.9rem;">Catálogo de Dados</div>
            </div>""", unsafe_allow_html=True)
        if not df_meta.empty:
            for _, row in df_meta.head(4).iterrows():
                cor_c = "#3FB950" if row["score_completude"]==100 else \
                        "#C9A227" if row["score_completude"]>=60 else "#F85149"
                desc = row["descricao"][:55]+"..." \
                       if row["descricao"] and len(row["descricao"])>55 \
                       else row["descricao"] or "Sem descrição"
                st.markdown(f"""
                <div style="background:#0D1117;border:1px solid #21262D;border-radius:8px;
                            padding:10px;margin-bottom:8px;">
                    <div style="display:flex;justify-content:space-between;">
                        <span style="color:#C9A227;font-weight:600;font-size:0.82rem;">
                            {row['table_name']}</span>
                        <span style="color:{cor_c};font-weight:700;font-size:0.82rem;">
                            {row['score_completude']}%</span>
                    </div>
                    <div style="color:#8B949E;font-size:0.72rem;margin:4px 0;">
                        {desc}</div>
                    <div style="display:flex;gap:4px;flex-wrap:wrap;">
                        <span style="background:#58A6FF22;color:#58A6FF;border-radius:4px;
                                     padding:1px 6px;font-size:0.68rem;">
                            {row['schema_name']}</span>
                        {f'<span style="background:#C9A22722;color:#C9A227;border-radius:4px;padding:1px 6px;font-size:0.68rem;">{row["dominio"]}</span>' if row['dominio'] else ''}
                    </div>
                </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_sc:
        if not df_meta.empty:
            doc  = df_meta["descricao"].apply(bool).mean()*100
            own  = df_meta["data_owner"].apply(bool).mean()*100
            cert = (len(df_meta[df_meta["selo"]=="certificado"])/len(df_meta))*100
            qual = df_meta["score_completude"].mean()
            ger  = (doc+own+cert+qual)/4
            cor_g = "#3FB950" if ger>=80 else "#C9A227" if ger>=60 else "#F85149"

            st.markdown(f"""
            <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;
                        padding:16px;height:100%;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
                    <div style="background:#3FB95022;border-radius:6px;padding:6px;
                                font-size:1rem;">🛡️</div>
                    <div style="color:#E6EDF3;font-weight:700;font-size:0.9rem;">
                        Scorecard de Confiabilidade</div>
                </div>
                <div style="text-align:center;padding:12px 0;">
                    <div style="font-size:3rem;font-weight:800;color:{cor_g};">{ger:.0f}%</div>
                    <div style="color:#8B949E;font-size:0.78rem;">score médio do domínio</div>
                </div>""", unsafe_allow_html=True)

            for nome, val in [("Documentação",doc),("Ownership",own),
                               ("Certificação",cert),("Qualidade",qual)]:
                cor_p = "#3FB950" if val>=80 else "#C9A227" if val>=60 else "#F85149"
                st.markdown(f"""
                <div style="margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                        <span style="color:#E6EDF3;font-size:0.78rem;">{nome}</span>
                        <span style="color:{cor_p};font-weight:700;font-size:0.78rem;">
                            {val:.0f}%</span>
                    </div>
                    <div style="background:#30363D;border-radius:4px;height:5px;">
                        <div style="background:{cor_p};border-radius:4px;height:5px;
                                    width:{min(val,100):.0f}%;"></div>
                    </div>
                </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with col_dom:
        st.markdown("""<div style="background:#161B22;border:1px solid #30363D;
            border-radius:12px;padding:16px;height:100%;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
                <div style="background:#BC8CFF22;border-radius:6px;padding:6px;
                            font-size:1rem;">🏛️</div>
                <div style="color:#E6EDF3;font-weight:700;font-size:0.9rem;">
                    Domínios de Negócio</div>
            </div>""", unsafe_allow_html=True)
        if not df_meta.empty:
            dom_sc = df_meta[df_meta["dominio"].apply(bool)]\
                        .groupby("dominio")["score_completude"].mean()\
                        .sort_values(ascending=False)
            for dom, sc in dom_sc.items():
                cor_d = "#3FB950" if sc>=80 else "#C9A227" if sc>=60 else "#F85149"
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;
                            padding:7px 0;border-bottom:1px solid #21262D;">
                    <span style="color:#E6EDF3;font-size:0.82rem;">{dom}</span>
                    <span style="color:{cor_d};font-weight:700;font-size:0.82rem;">
                        {sc:.0f}%</span>
                </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Rodapé módulos
    m1,m2,m3,m4 = st.columns(4)
    mods = [
        ("🧠","Curadoria Inteligente",
         "IA sugerindo descrição, domínio e classificação para acelerar a documentação."),
        ("🛡️","Trilha de Auditoria",
         "Rastreabilidade completa de quem alterou, quando e o que mudou."),
        ("⚡","Meu Espaço",
         "Acompanhe suas pendências, aprovações e atividades."),
        ("🔍","Descobrir Dados",
         "Encontre ativos, termos, indicadores e responsáveis de forma rápida."),
    ]
    for col, (ic, tit, desc) in zip([m1,m2,m3,m4], mods):
        with col:
            st.markdown(f"""
            <div style="background:#161B22;border:1px solid #30363D;border-radius:10px;
                        padding:16px;text-align:center;">
                <div style="font-size:1.6rem;margin-bottom:6px;">{ic}</div>
                <div style="color:#E6EDF3;font-weight:700;font-size:0.82rem;
                            margin-bottom:4px;">{tit}</div>
                <div style="color:#8B949E;font-size:0.72rem;line-height:1.4;">{desc}</div>
            </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# 📋 CATÁLOGO
# ════════════════════════════════════════════════════════════════════
elif pagina == "📋 Catálogo":
    page_header("📋","Catálogo de Dados",
                "Descubra, compreenda e confie nos dados antes de utilizá-los.")

    df_cat = load_meta()

    if not df_cat.empty:
        # KPIs
        total = len(df_cat)
        schemas = df_cat["schema_name"].value_counts()
        ouro   = schemas.get("ouro",0)
        prata  = schemas.get("prata",0)
        bronze = schemas.get("bronze",0)
        dominios_n = df_cat["dominio"].nunique()

        k1,k2,k3 = st.columns(3)
        with k1: st.markdown(kpi(total,"Tabelas no Catálogo","#C9A227"),
                             unsafe_allow_html=True)
        with k2: st.markdown(
            kpi(f"{ouro}·{prata}·{bronze}","Ouro · Prata · Bronze","#58A6FF"),
            unsafe_allow_html=True)
        with k3: st.markdown(kpi(dominios_n,"Domínios","#BC8CFF"),
                             unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Busca
        busca = st.text_input("",
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
            docs = ["Todas","Documentadas","Sem documentação"]
            f_doc = st.selectbox("DOCUMENTAÇÃO", docs, key="cf_doc")

        df_f = df_cat.copy()
        if busca:
            mask = (df_f["table_name"].str.contains(busca,case=False,na=False) |
                    df_f["descricao"].str.contains(busca,case=False,na=False) |
                    df_f["dominio"].str.contains(busca,case=False,na=False) |
                    df_f["data_owner"].str.contains(busca,case=False,na=False))
            df_f = df_f[mask]
        if f_dom != "Todos":  df_f = df_f[df_f["dominio"]==f_dom]
        if f_cam != "Todas":  df_f = df_f[df_f["schema_name"]==f_cam]
        if f_own != "Todos":  df_f = df_f[df_f["data_owner"]==f_own]
        if f_stw != "Todos":  df_f = df_f[df_f["data_steward"]==f_stw]
        if f_doc == "Documentadas":      df_f = df_f[df_f["descricao"].apply(bool)]
        if f_doc == "Sem documentação":  df_f = df_f[~df_f["descricao"].apply(bool)]

        st.markdown(f'<div style="color:#8B949E;font-size:0.78rem;margin:8px 0;">'
                    f'{len(df_f)} ativo(s) encontrado(s)</div>', unsafe_allow_html=True)

        # Grid de cards
        cols_per_row = 3
        rows = [df_f.iloc[i:i+cols_per_row].reset_index(drop=True)
                for i in range(0, len(df_f), cols_per_row)]

        for row_df in rows:
            cols = st.columns(cols_per_row)
            for i, (_, item) in enumerate(row_df.iterrows()):
                cor_c = "#3FB950" if item["score_completude"]==100 else \
                        "#C9A227" if item["score_completude"]>=60 else "#F85149"
                desc = item["descricao"][:80]+"..." \
                       if item["descricao"] and len(item["descricao"])>80 \
                       else item["descricao"] or "Sem descrição"
                pii_b = "🔒 PII · " if item["tem_pii"] else ""
                with cols[i]:
                    st.markdown(f"""
                    <div style="background:#161B22;border:1px solid #30363D;border-radius:10px;
                                padding:14px;margin-bottom:10px;min-height:140px;">
                        <div style="display:flex;justify-content:space-between;
                                    align-items:flex-start;margin-bottom:6px;">
                            <span style="color:#C9A227;font-weight:700;font-size:0.85rem;">
                                {item['table_name']}</span>
                            <span style="color:{cor_c};font-weight:800;font-size:0.9rem;">
                                {item['score_completude']}%</span>
                        </div>
                        <div style="color:#8B949E;font-size:0.75rem;
                                    line-height:1.4;margin-bottom:8px;">{desc}</div>
                        <div style="display:flex;gap:4px;flex-wrap:wrap;">
                            <span style="background:#58A6FF22;color:#58A6FF;border-radius:4px;
                                         padding:2px 7px;font-size:0.68rem;">
                                {item['schema_name']}</span>
                            {f'<span style="background:#C9A22722;color:#C9A227;border-radius:4px;padding:2px 7px;font-size:0.68rem;">{item["dominio"]}</span>' if item['dominio'] else ''}
                            {f'<span style="background:#F8514922;color:#F85149;border-radius:4px;padding:2px 7px;font-size:0.68rem;">🔒 PII</span>' if item['tem_pii'] else ''}
                        </div>
                    </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# 📖 GLOSSÁRIO
# ════════════════════════════════════════════════════════════════════
elif pagina == "📖 Glossário":
    page_header("📖","Glossário Corporativo",
                "A linguagem comum da organização — definições, regras e responsáveis.")

    df_g = load_glossario()

    if not df_g.empty:
        # Layout: lista esquerda + detalhe direita
        col_lista, col_detalhe = st.columns([1, 2])

        with col_lista:
            # Filtro de busca
            busca_g = st.text_input("",
                placeholder="🔍 Buscar termo...", key="g_busca")
            g_status = st.selectbox("Status",
                ["Todos","homologado","em_revisao","rascunho"], key="g_st")

            df_gf = df_g.copy()
            if busca_g:
                df_gf = df_gf[df_gf["termo"].str.contains(busca_g,case=False,na=False)]
            if g_status != "Todos":
                df_gf = df_gf[df_gf["status"]==g_status]

            # Tabs de categoria
            gt1, gt2, gt3, gt4 = st.tabs([
                "📋 Termos","📏 Regras","🔗 Relacionamentos","🕐 Histórico"])

            with gt1:
                if "termo_selecionado" not in st.session_state:
                    st.session_state["termo_selecionado"] = None

                for _, row in df_gf.iterrows():
                    cor_st = {"homologado":"#3FB950","em_revisao":"#58A6FF",
                              "rascunho":"#8B949E"}.get(row["status"],"#8B949E")
                    selecionado = st.session_state.get("termo_selecionado") == row["glossary_id"]
                    bg = "#C9A22711" if selecionado else "transparent"
                    brd = "#C9A22744" if selecionado else "#30363D"

                    if st.button(
                        f"{'● ' if selecionado else ''}{row['termo']}",
                        key=f"gbt_{row['glossary_id']}",
                        use_container_width=True
                    ):
                        st.session_state["termo_selecionado"] = row["glossary_id"]
                        st.rerun()

            with gt2:
                df_rules, _ = qry("""SELECT g.termo, r.nome_regra,
                    r.descricao_regra, r.categoria
                    FROM meridian_governanca.business_rules r
                    JOIN meridian_governanca.business_glossary g
                    ON r.glossary_id = g.glossary_id
                    ORDER BY g.termo, r.categoria""")
                if not df_rules.empty:
                    for _, r in df_rules.iterrows():
                        st.markdown(f"""
                        <div style="background:#161B22;border:1px solid #30363D;
                                    border-radius:6px;padding:8px 10px;margin-bottom:6px;">
                            <div style="color:#C9A227;font-size:0.78rem;font-weight:600;">
                                {r['termo']}</div>
                            <div style="color:#E6EDF3;font-size:0.82rem;font-weight:600;">
                                {r['nome_regra']}</div>
                            <div style="color:#8B949E;font-size:0.75rem;">
                                {r['descricao_regra']}</div>
                            <span style="background:#BC8CFF22;color:#BC8CFF;border-radius:4px;
                                         padding:1px 6px;font-size:0.68rem;">
                                {r['categoria']}</span>
                        </div>""", unsafe_allow_html=True)

            with gt3:
                df_links, _ = qry("""SELECT g.termo, l.asset_type,
                    l.schema_name, l.table_name, l.column_name
                    FROM meridian_governanca.glossary_asset_link l
                    JOIN meridian_governanca.business_glossary g
                    ON l.glossary_id = g.glossary_id
                    ORDER BY g.termo""")
                if not df_links.empty:
                    for _, l in df_links.iterrows():
                        col_i = f".`{l['column_name']}`" if l["column_name"] else ""
                        st.markdown(f"""
                        <div style="background:#161B22;border:1px solid #30363D;
                                    border-radius:6px;padding:8px 10px;margin-bottom:6px;">
                            <div style="color:#C9A227;font-size:0.75rem;">{l['termo']}</div>
                            <div style="color:#58A6FF;font-size:0.78rem;font-family:monospace;">
                                {l['schema_name']}.{l['table_name']}{col_i}</div>
                            <span style="background:#58A6FF22;color:#58A6FF;border-radius:4px;
                                         padding:1px 6px;font-size:0.68rem;">
                                {l['asset_type']}</span>
                        </div>""", unsafe_allow_html=True)

            with gt4:
                df_wf, _ = qry("""SELECT g.termo, w.acao, w.status_anterior,
                    w.status_novo, w.aprovador, w.criado_em
                    FROM meridian_governanca.glossary_approval_workflow w
                    JOIN meridian_governanca.business_glossary g
                    ON w.glossary_id = g.glossary_id
                    ORDER BY w.criado_em DESC LIMIT 20""")
                if not df_wf.empty:
                    st.dataframe(df_wf.rename(columns={
                        "termo":"Termo","acao":"Ação",
                        "status_anterior":"De","status_novo":"Para",
                        "aprovador":"Por","criado_em":"Data"}),
                        use_container_width=True, hide_index=True)

        with col_detalhe:
            gid = st.session_state.get("termo_selecionado")
            if gid:
                row = df_g[df_g["glossary_id"]==gid].iloc[0]
                cor_st = {"homologado":"#3FB950","em_revisao":"#58A6FF",
                          "rascunho":"#8B949E"}.get(row["status"],"#8B949E")
                cor_crit = {"Crítico":"#F85149","Alto":"#FF7B72",
                            "Médio":"#C9A227","Baixo":"#3FB950"}.get(row["criticidade"],"#8B949E")

                st.markdown(f"""
                <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;
                            padding:20px;">
                    <div style="display:flex;justify-content:space-between;
                                align-items:flex-start;margin-bottom:12px;">
                        <div style="color:#E6EDF3;font-size:1.3rem;font-weight:800;">
                            {row['termo']}</div>
                        <span style="background:{cor_st}22;color:{cor_st};border-radius:20px;
                                     padding:3px 12px;font-size:0.78rem;font-weight:600;
                                     border:1px solid {cor_st}44;">
                            {'✅ Homologado' if row['status']=='homologado'
                             else '🔵 Em Revisão' if row['status']=='em_revisao'
                             else '📄 Rascunho'}</span>
                    </div>
                    <div style="color:#E6EDF3;font-size:0.88rem;line-height:1.6;
                                margin-bottom:12px;">{row['definicao']}</div>
                    {f'<div style="color:#8B949E;font-size:0.78rem;margin-bottom:12px;">Também conhecido como: <span style="color:#C9A227;">{row["sinonimos"]}</span></div>' if row["sinonimos"] else ''}
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;
                                margin-bottom:12px;">
                        <div style="background:#0D1117;border-radius:8px;padding:10px;">
                            <div style="font-size:0.65rem;color:#8B949E;text-transform:uppercase;
                                        letter-spacing:1px;">DOMÍNIO</div>
                            <div style="color:#E6EDF3;font-weight:600;font-size:0.85rem;">
                                {row['dominio']}</div>
                        </div>
                        <div style="background:#0D1117;border-radius:8px;padding:10px;">
                            <div style="font-size:0.65rem;color:#8B949E;text-transform:uppercase;
                                        letter-spacing:1px;">CRITICIDADE</div>
                            <div style="color:{cor_crit};font-weight:600;font-size:0.85rem;">
                                {row['criticidade']}</div>
                        </div>
                        <div style="background:#0D1117;border-radius:8px;padding:10px;">
                            <div style="font-size:0.65rem;color:#8B949E;text-transform:uppercase;
                                        letter-spacing:1px;">DATA OWNER</div>
                            <div style="color:#E6EDF3;font-size:0.82rem;">
                                {row['owner_email']}</div>
                        </div>
                        <div style="background:#0D1117;border-radius:8px;padding:10px;">
                            <div style="font-size:0.65rem;color:#8B949E;text-transform:uppercase;
                                        letter-spacing:1px;">DATA STEWARD</div>
                            <div style="color:#E6EDF3;font-size:0.82rem;">
                                {row['steward_email']}</div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)

                # Regras
                df_rg, _ = qry(f"""SELECT nome_regra, descricao_regra, categoria
                    FROM meridian_governanca.business_rules
                    WHERE glossary_id='{gid}' ORDER BY categoria""")
                if not df_rg.empty:
                    st.markdown('<div style="color:#E6EDF3;font-weight:700;'
                                'font-size:0.85rem;margin:12px 0 6px;">📏 Regras de Negócio</div>',
                                unsafe_allow_html=True)
                    for _, r in df_rg.iterrows():
                        st.markdown(f"""
                        <div style="background:#161B22;border:1px solid #30363D;border-radius:6px;
                                    padding:8px 12px;margin-bottom:6px;">
                            <div style="display:flex;justify-content:space-between;">
                                <span style="color:#E6EDF3;font-size:0.82rem;font-weight:600;">
                                    {r['nome_regra']}</span>
                                <span style="background:#BC8CFF22;color:#BC8CFF;border-radius:4px;
                                             padding:1px 6px;font-size:0.68rem;">
                                    {r['categoria']}</span>
                            </div>
                            <div style="color:#8B949E;font-size:0.75rem;margin-top:3px;">
                                {r['descricao_regra']}</div>
                        </div>""", unsafe_allow_html=True)

                # Ações workflow
                if is_curador and row["status"] == "rascunho":
                    if st.button("📤 Submeter para Revisão",
                                 key=f"gsub_{gid}"):
                        ok, _ = exe(f"""UPDATE meridian_governanca.business_glossary
                            SET status='em_revisao',atualizado_por='{esc(usuario)}',
                            atualizado_em=current_timestamp()
                            WHERE glossary_id='{gid}'""")
                        if ok:
                            st.success("✅ Submetido!")
                            st.cache_data.clear(); st.rerun()

                if is_aprovador and row["status"] == "em_revisao":
                    ga, gr = st.columns(2)
                    with ga:
                        if st.button("✅ Aprovar", key=f"gap_{gid}"):
                            ok, _ = exe(f"""UPDATE meridian_governanca.business_glossary
                                SET status='homologado',atualizado_por='{esc(usuario)}',
                                atualizado_em=current_timestamp()
                                WHERE glossary_id='{gid}'""")
                            if ok:
                                st.success("✅ Homologado!")
                                st.cache_data.clear(); st.rerun()
                    with gr:
                        if st.button("❌ Rejeitar", key=f"grej_{gid}"):
                            ok, _ = exe(f"""UPDATE meridian_governanca.business_glossary
                                SET status='rascunho',atualizado_por='{esc(usuario)}',
                                atualizado_em=current_timestamp()
                                WHERE glossary_id='{gid}'""")
                            if ok:
                                st.warning("↩️ Devolvido.")
                                st.cache_data.clear(); st.rerun()

                # Novo termo
                if is_curador:
                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                    with st.expander("➕ Criar novo termo"):
                        nt1,nt2 = st.columns(2)
                        with nt1:
                            nn = st.text_input("Termo *", key="nn")
                            nd = st.text_area("Definição *", key="nd", height=80)
                            ns = st.text_input("Sinônimos", key="ns")
                        with nt2:
                            ndom = st.selectbox("Domínio",
                                ["Crédito","Pagamentos","Clientes","Compliance","Produtos"],
                                key="ndom")
                            narea = st.text_input("Área", key="narea")
                            ncrit = st.selectbox("Criticidade",
                                ["Crítico","Alto","Médio","Baixo"], key="ncrit")
                        if st.button("💾 Criar", key="btn_criar"):
                            if nn and nd:
                                gid_new = str(uuid.uuid4())
                                ok, err = exe(f"""INSERT INTO meridian_governanca.business_glossary
                                    VALUES ('{gid_new}','{esc(nn)}','{esc(nd)}',
                                    '{esc(ns)}','{esc(ndom)}','{esc(narea)}',
                                    '{esc(ncrit)}','{esc(usuario)}','{esc(usuario)}',
                                    'rascunho',1,false,'{esc(usuario)}',
                                    current_timestamp(),'{esc(usuario)}',
                                    current_timestamp())""")
                                if ok:
                                    st.success(f"✅ '{nn}' criado!")
                                    st.cache_data.clear(); st.rerun()
                                else: st.error(f"Erro: {err}")
                            else: st.warning("Preencha Termo e Definição.")
            else:
                st.markdown("""
                <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;
                            padding:40px;text-align:center;margin-top:20px;">
                    <div style="font-size:2.5rem;margin-bottom:12px;">📖</div>
                    <div style="color:#E6EDF3;font-weight:700;margin-bottom:8px;">
                        Selecione um termo</div>
                    <div style="color:#8B949E;font-size:0.85rem;">
                        Clique em um termo na lista ao lado para ver seus detalhes,
                        regras de negócio e ativos vinculados.</div>
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
        n_owners  = df_dom["data_owner"].nunique()
        n_stw     = df_dom["data_steward"].nunique()
        termos_v  = len(df_glos) if not df_glos.empty else 0
        cob_termos = round(len(df_glos[df_glos["status"]=="homologado"]) /
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
        with k5: st.markdown(kpi(f"{cob_termos}%","Cobertura de Termos","#C9A227"),
                             unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Cards de domínios
        cols_dom = st.columns(3)
        icones_dom = {"Crédito":"💳","Pagamentos":"💸","Clientes":"👥",
                      "Compliance":"🛡️","Produtos":"📦"}

        for i, dom in enumerate(dominios):
            df_d = df_dom[df_dom["dominio"]==dom]
            score = df_d["score_completude"].mean()
            owners_d  = [o for o in df_d["data_owner"].unique() if o]
            stewards_d = [s for s in df_d["data_steward"].unique() if s]
            n_termos_d = len(df_glos[df_glos["dominio"]==dom]) \
                         if not df_glos.empty else 0
            cor_d = "#3FB950" if score>=80 else "#C9A227" if score>=60 else "#F85149"
            ic = icones_dom.get(dom, "🏛️")

            with cols_dom[i % 3]:
                st.markdown(f"""
                <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;
                            padding:16px;margin-bottom:12px;">
                    <div style="display:flex;justify-content:space-between;
                                align-items:center;margin-bottom:8px;">
                        <div style="display:flex;align-items:center;gap:8px;">
                            <span style="font-size:1.2rem;">{ic}</span>
                            <span style="color:#E6EDF3;font-weight:700;font-size:0.9rem;">
                                {dom}</span>
                        </div>
                        <span style="color:{cor_d};font-weight:800;font-size:1rem;">
                            {score:.0f}%</span>
                    </div>
                    <div style="background:#30363D;border-radius:4px;height:4px;
                                margin-bottom:10px;">
                        <div style="background:{cor_d};border-radius:4px;height:4px;
                                    width:{min(score,100):.0f}%;"></div>
                    </div>
                    <div style="font-size:0.72rem;color:#8B949E;margin-bottom:6px;">
                        Owner: <span style="color:#E6EDF3;">
                        {owners_d[0] if owners_d else '—'}</span> ·
                        Stewards: <span style="color:#E6EDF3;">{len(stewards_d)}</span> ·
                        Termos: <span style="color:#E6EDF3;">{n_termos_d}</span>
                    </div>
                    <div style="display:flex;gap:4px;flex-wrap:wrap;margin-top:6px;">
                """, unsafe_allow_html=True)

                # Schemas deste domínio
                schemas_d = df_d["schema_name"].unique()
                for sc in schemas_d:
                    n_sc = len(df_d[df_d["schema_name"]==sc])
                    st.markdown(
                        f'<span style="background:#58A6FF22;color:#58A6FF;'
                        f'border-radius:4px;padding:2px 7px;font-size:0.68rem;">'
                        f'{sc} ({n_sc})</span>',
                        unsafe_allow_html=True)

                st.markdown("</div></div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# 🛡️ SCORECARD
# ════════════════════════════════════════════════════════════════════
elif pagina == "🛡️ Scorecard":
    page_header("🛡️","Scorecard de Confiabilidade",
                "Visão objetiva da confiabilidade por ativo, domínio e área.")

    df_sc = load_meta()

    if df_sc.empty:
        st.error("Não foi possível carregar os dados.")
    else:
        doc  = df_sc["descricao"].apply(bool).mean()*100
        own  = df_sc["data_owner"].apply(bool).mean()*100
        cert = (len(df_sc[df_sc["selo"]=="certificado"])/len(df_sc))*100
        qual = df_sc["score_completude"].mean()
        ger  = (doc+own+cert+qual)/4
        cor_g = "#3FB950" if ger>=80 else "#C9A227" if ger>=60 else "#F85149"

        # Score geral
        st.markdown(f"""
        <div style="background:#161B22;border:1px solid #30363D;border-radius:16px;
                    padding:28px;text-align:center;margin-bottom:20px;">
            <div style="font-size:0.75rem;color:#8B949E;text-transform:uppercase;
                        letter-spacing:2px;margin-bottom:6px;">
                Score Geral de Confiabilidade</div>
            <div style="font-size:4.5rem;font-weight:800;color:{cor_g};
                        line-height:1;">{ger:.0f}%</div>
            <div style="color:#8B949E;font-size:0.82rem;margin-top:6px;">
                Baseado em Documentação, Ownership, Certificação e Qualidade</div>
        </div>""", unsafe_allow_html=True)

        # 4 pilares
        p1,p2,p3,p4 = st.columns(4)
        for col, nome, val, ic in [
            (p1,"Documentação",doc,"📝"),
            (p2,"Ownership",own,"👤"),
            (p3,"Certificação",cert,"🏆"),
            (p4,"Qualidade",qual,"⭐"),
        ]:
            cor_p = "#3FB950" if val>=80 else "#C9A227" if val>=60 else "#F85149"
            with col:
                st.markdown(f"""
                <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;
                            padding:18px;text-align:center;margin-bottom:16px;">
                    <div style="font-size:1.4rem;margin-bottom:6px;">{ic}</div>
                    <div style="font-size:2rem;font-weight:800;color:{cor_p};">{val:.0f}%</div>
                    <div style="color:#8B949E;font-size:0.78rem;margin-bottom:8px;">{nome}</div>
                    <div style="background:#30363D;border-radius:4px;height:5px;">
                        <div style="background:{cor_p};border-radius:4px;height:5px;
                                    width:{min(val,100):.0f}%;"></div>
                    </div>
                </div>""", unsafe_allow_html=True)

        # Score por domínio (gráfico)
        st.markdown('<div style="color:#E6EDF3;font-weight:700;font-size:0.9rem;'
                    'margin-bottom:10px;">Score por Domínio</div>',
                    unsafe_allow_html=True)
        dom_sc = df_sc[df_sc["dominio"].apply(bool)]\
                    .groupby("dominio")["score_completude"].mean()\
                    .reset_index().sort_values("score_completude",ascending=False)

        fig = px.bar(dom_sc, x="dominio", y="score_completude",
            color="score_completude",
            color_continuous_scale=["#F85149","#C9A227","#3FB950"],
            range_color=[0,100],
            template="plotly_dark",
            labels={"dominio":"","score_completude":"Score (%)"}
        )
        fig.update_layout(
            paper_bgcolor="#161B22", plot_bgcolor="#161B22",
            font_family="Inter", showlegend=False,
            coloraxis_showscale=False, height=280,
            margin=dict(t=10,b=10,l=0,r=0)
        )
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

        # Ranking owners
        st.markdown('<div style="color:#E6EDF3;font-weight:700;font-size:0.9rem;'
                    'margin:12px 0 10px;">Ranking de Owners</div>',
                    unsafe_allow_html=True)
        df_own = df_sc[df_sc["data_owner"].apply(bool)]\
                    .groupby("data_owner")["score_completude"].mean()\
                    .reset_index().sort_values("score_completude",ascending=False)
        for _, row in df_own.iterrows():
            cor_o = "#3FB950" if row["score_completude"]>=80 else \
                    "#C9A227" if row["score_completude"]>=60 else "#F85149"
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                        background:#161B22;border:1px solid #30363D;border-radius:8px;
                        padding:9px 14px;margin-bottom:5px;">
                <span style="color:#E6EDF3;font-size:0.82rem;">{row['data_owner']}</span>
                <div style="display:flex;align-items:center;gap:10px;">
                    <div style="background:#30363D;border-radius:4px;height:5px;width:100px;">
                        <div style="background:{cor_o};border-radius:4px;height:5px;
                                    width:{min(row['score_completude'],100):.0f}%;"></div>
                    </div>
                    <span style="color:{cor_o};font-weight:700;font-size:0.82rem;
                                 width:36px;text-align:right;">
                        {row['score_completude']:.0f}%</span>
                </div>
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
            c_left, c_right = st.columns([1, 2])

            with c_left:
                st.markdown('<div style="color:#8B949E;font-size:0.72rem;'
                            'text-transform:uppercase;letter-spacing:1px;'
                            'margin-bottom:6px;">SCHEMA</div>',
                            unsafe_allow_html=True)
                schemas = sorted(df_cur["schema_name"].unique().tolist())
                sel_s = st.selectbox("", schemas, key="cur_s",
                                     label_visibility="collapsed")

                tabs_s = df_cur[df_cur["schema_name"]==sel_s]["table_name"].tolist()
                st.markdown('<div style="color:#8B949E;font-size:0.72rem;'
                            'text-transform:uppercase;letter-spacing:1px;'
                            'margin:10px 0 6px;">TABELA</div>',
                            unsafe_allow_html=True)
                sel_t = st.selectbox("", tabs_s, key="cur_t",
                                     label_visibility="collapsed")

            with c_right:
                row = df_cur[(df_cur["schema_name"]==sel_s) &
                             (df_cur["table_name"]==sel_t)].iloc[0]

                # Header da tabela
                doc_p  = 100 if row["descricao"] else 0
                own_p  = 100 if row["data_owner"] else 0
                cert_p = 100 if row["selo"]=="certificado" else 0
                qual_p = row["score_completude"]

                st.markdown(f"""
                <div style="background:#161B22;border:1px solid #30363D;border-radius:10px;
                            padding:14px 16px;margin-bottom:14px;
                            display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div style="color:#C9A227;font-weight:700;font-size:0.95rem;">
                            {sel_t}</div>
                        <div style="color:#8B949E;font-size:0.75rem;">
                            {row['descricao'][:60]+'...' if row['descricao'] and
                             len(row['descricao'])>60 else row['descricao'] or 'Sem descrição'}
                        </div>
                    </div>
                    <button style="background:#C9A227;color:#0D1117;border:none;
                                   border-radius:6px;padding:6px 14px;font-weight:700;
                                   font-size:0.78rem;cursor:pointer;">
                        ✨ Sugerir com IA</button>
                </div>""", unsafe_allow_html=True)

                # 4 pilares
                pp1,pp2,pp3,pp4 = st.columns(4)
                for pcol, pnome, pval in [
                    (pp1,"DOCUMENTAÇÃO",doc_p),(pp2,"OWNERSHIP",own_p),
                    (pp3,"CERTIFICAÇÃO",cert_p),(pp4,"QUALIDADE",qual_p)
                ]:
                    cor_pp = "#3FB950" if pval>=80 else \
                             "#C9A227" if pval>0 else "#F85149"
                    with pcol:
                        st.markdown(f"""
                        <div style="background:#0D1117;border:1px solid #30363D;
                                    border-radius:8px;padding:10px;text-align:center;
                                    margin-bottom:12px;">
                            <div style="font-size:0.6rem;color:#8B949E;
                                        text-transform:uppercase;letter-spacing:1px;">
                                {pnome}</div>
                            <div style="font-size:1.3rem;font-weight:800;color:{cor_pp};">
                                {f'{pval}%' if pval > 0 else 'Não Iniciado'}</div>
                        </div>""", unsafe_allow_html=True)

                # Campos de edição
                ed1, ed2 = st.columns(2)
                with ed1:
                    new_desc = st.text_area("DESCRIÇÃO",
                        value=row["descricao"] or "", height=90,
                        key="c_desc",
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

                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("💾 Salvar Alterações", type="primary",
                                 key="c_save", use_container_width=True):
                        filled = sum([bool(new_desc),bool(new_dom),
                                      bool(new_own),bool(new_stw),
                                      bool(row["funcao_negocio"])])
                        new_score = filled * 20
                        new_selo  = ("certificado" if new_score==100 else
                                     "parcial" if new_score>=60 else "pendente")
                        ok, err = exe(f"""UPDATE meridian_governanca.tabelas_metadata
                            SET descricao='{esc(new_desc)}',dominio='{esc(new_dom)}',
                            data_owner='{esc(new_own)}',data_steward='{esc(new_stw)}',
                            score_completude={new_score},selo='{new_selo}',
                            atualizado_em=current_timestamp()
                            WHERE schema_name='{sel_s}' AND table_name='{sel_t}'""")
                        if ok:
                            exe(f"""INSERT INTO meridian_governanca.metadata_audit VALUES
                                ('{uuid.uuid4()}',current_timestamp(),
                                '{sel_s}','{sel_t}','tabela','','metadados',
                                '{row['score_completude']}','{new_score}',
                                'manual','{esc(usuario)}','{esc(usuario[:8])}')""")
                            st.success(f"✅ Salvo! Score: {new_score}%")
                            st.cache_data.clear(); st.rerun()
                        else: st.error(f"Erro: {err}")
                with bc2:
                    if st.button("🤖 Sugerir com IA",
                                 key="c_ai", use_container_width=True):
                        sugestoes = {
                            "clientes_raw": ("Dados brutos de clientes ingeridos do sistema core bancário, contendo informações cadastrais e de contato.", "Clientes"),
                            "contas_raw": ("Dados brutos de contas correntes e poupança dos clientes do banco.", "Clientes"),
                            "transacoes_raw": ("Transações financeiras brutas de todos os canais digitais e físicos.", "Pagamentos"),
                            "propostas_credito_raw": ("Propostas de crédito recebidas pelos canais com status de aprovação.", "Crédito"),
                            "pix_raw": ("Transações PIX brutas do Sistema de Pagamentos Instantâneos do Banco Central.", "Pagamentos"),
                            "dim_clientes": ("Dimensão de clientes tratada e enriquecida com segmentação e score.", "Clientes"),
                            "dim_contas": ("Dimensão de contas com dados consolidados e limites.", "Clientes"),
                            "fato_transacoes": ("Fato de transações financeiras consolidadas por período e canal.", "Pagamentos"),
                            "fato_credito": ("Fato de operações de crédito aprovadas e recusadas.", "Crédito"),
                            "fato_inadimplencia": ("Fato de inadimplência com dias de atraso e valores.", "Crédito"),
                            "fato_pix": ("Fato de transações PIX consolidadas por período.", "Pagamentos"),
                            "dim_produtos": ("Dimensão de produtos financeiros do banco.", "Produtos"),
                            "indicadores_carteira": ("Indicadores consolidados da carteira de crédito.", "Crédito"),
                            "perfil_cliente_360": ("Visão 360 do cliente com score e propensão a churn.", "Clientes"),
                            "dashboard_inadimplencia": ("Base para dashboard executivo de inadimplência.", "Crédito"),
                            "indicadores_pix": ("Indicadores de volume e performance do PIX.", "Pagamentos"),
                            "base_lgpd": ("Mapeamento de dados pessoais para conformidade LGPD.", "Compliance"),
                        }
                        sug = sugestoes.get(sel_t,
                            (f"Tabela {sel_t} do schema {sel_s}.",""))
                        st.session_state["ai_desc"] = sug[0]
                        st.session_state["ai_dom"]  = sug[1]
                        st.rerun()

                # Sugestão IA
                if "ai_desc" in st.session_state:
                    st.markdown("""
                    <div style="background:#C9A22711;border:1px solid #C9A22733;
                                border-radius:8px;padding:10px 14px;margin-top:8px;">
                        <div style="color:#C9A227;font-weight:700;font-size:0.78rem;">
                            🤖 Sugestão da IA — revise antes de salvar</div>
                    </div>""", unsafe_allow_html=True)
                    sug_d = st.text_area("Descrição sugerida",
                        value=st.session_state["ai_desc"], key="sug_d")
                    sug_dom_opts = ["","Crédito","Pagamentos","Clientes",
                                    "Compliance","Produtos"]
                    sug_dom_v = st.session_state["ai_dom"]
                    sug_dom_i = sug_dom_opts.index(sug_dom_v) \
                                if sug_dom_v in sug_dom_opts else 0
                    sug_dom = st.selectbox("Domínio sugerido",
                        sug_dom_opts, index=sug_dom_i, key="sug_dom2")
                    sa1, sa2 = st.columns(2)
                    with sa1:
                        if st.button("✅ Aceitar", key="ai_ac"):
                            filled = sum([bool(sug_d),bool(sug_dom),
                                          bool(new_own),bool(new_stw),
                                          bool(row["funcao_negocio"])])
                            ns = filled*20
                            sl = ("certificado" if ns==100 else
                                  "parcial" if ns>=60 else "pendente")
                            ok, _ = exe(f"""UPDATE meridian_governanca.tabelas_metadata
                                SET descricao='{esc(sug_d)}',dominio='{esc(sug_dom)}',
                                score_completude={ns},selo='{sl}',
                                atualizado_em=current_timestamp()
                                WHERE schema_name='{sel_s}' AND table_name='{sel_t}'""")
                            if ok:
                                exe(f"""INSERT INTO meridian_governanca.metadata_audit VALUES
                                    ('{uuid.uuid4()}',current_timestamp(),
                                    '{sel_s}','{sel_t}','tabela','','metadados',
                                    '{row['score_completude']}','{ns}',
                                    'ia','{esc(usuario)}','{esc(usuario[:8])}')""")
                                st.success("✅ Sugestão aplicada!")
                                del st.session_state["ai_desc"]
                                del st.session_state["ai_dom"]
                                st.cache_data.clear(); st.rerun()
                    with sa2:
                        if st.button("❌ Descartar", key="ai_dc"):
                            del st.session_state["ai_desc"]
                            del st.session_state["ai_dom"]
                            st.rerun()

        with cur2:
            f1c, f2c = st.columns(2)
            with f1c:
                fl_s = st.selectbox("Schema",
                    ["Todos"]+sorted(df_cur["schema_name"].unique().tolist()),
                    key="lote_s")
            with f2c:
                fl_sl = st.selectbox("Selo",
                    ["Todos","certificado","parcial","pendente"], key="lote_sl")

            df_l = df_cur.copy()
            if fl_s != "Todos":  df_l = df_l[df_l["schema_name"]==fl_s]
            if fl_sl != "Todos": df_l = df_l[df_l["selo"]==fl_sl]

            df_l_ed = df_l[["schema_name","table_name",
                             "score_completude","selo"]].copy()
            df_l_ed.insert(0, "Selecionar", False)
            edited = st.data_editor(
                df_l_ed.rename(columns={
                    "schema_name":"Schema","table_name":"Tabela",
                    "score_completude":"Score","selo":"Selo"}),
                use_container_width=True, hide_index=True,
                column_config={"Selecionar":st.column_config.CheckboxColumn()}
            )
            sels = edited[edited["Selecionar"]==True]

            if len(sels) > 0:
                st.markdown(f'<div style="color:#C9A227;font-weight:600;'
                            f'font-size:0.85rem;margin:8px 0;">'
                            f'{len(sels)} tabela(s) selecionada(s)</div>',
                            unsafe_allow_html=True)
                lb1,lb2,lb3 = st.columns(3)
                with lb1:
                    l_dom = st.selectbox("Domínio",
                        ["","Crédito","Pagamentos","Clientes","Compliance","Produtos"],
                        key="l_dom")
                with lb2:
                    l_own = st.text_input("Owner", key="l_own")
                with lb3:
                    l_stw = st.text_input("Steward", key="l_stw")
                if st.button(f"🚀 Aplicar em {len(sels)} tabela(s)",
                             type="primary", key="l_apply"):
                    erros = []
                    for _, r in sels.iterrows():
                        sets = []
                        if l_dom: sets.append(f"dominio='{esc(l_dom)}'")
                        if l_own: sets.append(f"data_owner='{esc(l_own)}'")
                        if l_stw: sets.append(f"data_steward='{esc(l_stw)}'")
                        if sets:
                            sets.append("atualizado_em=current_timestamp()")
                            ok, _ = exe(f"""UPDATE meridian_governanca.tabelas_metadata
                                SET {', '.join(sets)}
                                WHERE schema_name='{r['Schema']}'
                                AND table_name='{r['Tabela']}'""")
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

    df_aud, err = qry("""SELECT timestamp_op, schema_name, table_name,
        tipo_objeto, campo_alterado, valor_anterior, valor_novo,
        origem, alterado_por
        FROM meridian_governanca.metadata_audit
        ORDER BY timestamp_op DESC LIMIT 500""")

    if err:
        st.error(f"Erro: {err}")
    elif df_aud.empty:
        st.markdown("""
        <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;
                    padding:40px;text-align:center;">
            <div style="font-size:2.5rem;margin-bottom:12px;">📭</div>
            <div style="color:#E6EDF3;font-weight:700;">Nenhum registro ainda</div>
            <div style="color:#8B949E;margin-top:8px;">
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

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Filtros
        af1,af2,af3 = st.columns(3)
        with af1:
            f_sc_a = st.selectbox("Schema",
                ["Todos"]+sorted(df_aud["schema_name"].dropna().unique().tolist()),
                key="a_sc")
        with af2:
            f_or_a = st.selectbox("Origem",
                ["Todos","manual","ia"], key="a_or")
        with af3:
            f_lim  = st.selectbox("Linhas",[50,100,200,500],key="a_lim")

        df_af = df_aud.copy()
        if f_sc_a != "Todos": df_af = df_af[df_af["schema_name"]==f_sc_a]
        if f_or_a != "Todos": df_af = df_af[df_af["origem"]==f_or_a]
        df_af = df_af.head(f_lim)

        # Tabela com badges de origem
        st.markdown("""
        <div style="background:#161B22;border:1px solid #30363D;border-radius:10px;
                    overflow:hidden;margin-top:8px;">
            <table style="width:100%;border-collapse:collapse;">
                <thead>
                    <tr style="border-bottom:1px solid #30363D;">
                        <th style="color:#8B949E;font-size:0.72rem;font-weight:600;
                                   text-transform:uppercase;padding:10px 12px;
                                   text-align:left;">DATA/HORA</th>
                        <th style="color:#8B949E;font-size:0.72rem;font-weight:600;
                                   text-transform:uppercase;padding:10px 12px;
                                   text-align:left;">SCHEMA</th>
                        <th style="color:#8B949E;font-size:0.72rem;font-weight:600;
                                   text-transform:uppercase;padding:10px 12px;
                                   text-align:left;">TABELA</th>
                        <th style="color:#8B949E;font-size:0.72rem;font-weight:600;
                                   text-transform:uppercase;padding:10px 12px;
                                   text-align:left;">CAMPO</th>
                        <th style="color:#8B949E;font-size:0.72rem;font-weight:600;
                                   text-transform:uppercase;padding:10px 12px;
                                   text-align:left;">VALOR ANTERIOR</th>
                        <th style="color:#8B949E;font-size:0.72rem;font-weight:600;
                                   text-transform:uppercase;padding:10px 12px;
                                   text-align:left;">VALOR NOVO</th>
                        <th style="color:#8B949E;font-size:0.72rem;font-weight:600;
                                   text-transform:uppercase;padding:10px 12px;
                                   text-align:left;">ORIGEM</th>
                    </tr>
                </thead>
                <tbody>
        """, unsafe_allow_html=True)

        for _, row in df_af.iterrows():
            ts = str(row["timestamp_op"])[:16] if row["timestamp_op"] else "—"
            ori_cor = "#BC8CFF" if row["origem"]=="ia" else "#58A6FF"
            ori_txt = "IA" if row["origem"]=="ia" else "Manual"
            val_ant = str(row["valor_anterior"])[:30] if row["valor_anterior"] else "—"
            val_nov = str(row["valor_novo"])[:40] if row["valor_novo"] else "—"
            st.markdown(f"""
                <tr style="border-bottom:1px solid #21262D;">
                    <td style="color:#8B949E;font-size:0.78rem;padding:9px 12px;">{ts}</td>
                    <td style="color:#58A6FF;font-size:0.78rem;padding:9px 12px;">
                        {row['schema_name'] or '—'}</td>
                    <td style="color:#E6EDF3;font-size:0.78rem;padding:9px 12px;
                               font-weight:600;">{row['table_name'] or '—'}</td>
                    <td style="color:#8B949E;font-size:0.78rem;padding:9px 12px;">
                        {row['campo_alterado'] or '—'}</td>
                    <td style="color:#8B949E;font-size:0.78rem;padding:9px 12px;">
                        {val_ant}</td>
                    <td style="color:#E6EDF3;font-size:0.78rem;padding:9px 12px;">
                        {val_nov}</td>
                    <td style="padding:9px 12px;">
                        <span style="background:{ori_cor}22;color:{ori_cor};
                                     border-radius:4px;padding:2px 8px;
                                     font-size:0.7rem;font-weight:700;">
                            {ori_txt}</span>
                    </td>
                </tr>""", unsafe_allow_html=True)

        st.markdown("</tbody></table></div>", unsafe_allow_html=True)
