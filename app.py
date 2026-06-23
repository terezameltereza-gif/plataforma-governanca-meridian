"""
app.py — Plataforma de Governança de Dados
Banco Meridian | v2.0
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
    padding-left: 1rem !important; padding-right: 1rem !important;
}
h1,h2,h3 { color: #C9A227 !important; font-weight: 700 !important; }
.stButton > button {
    background: linear-gradient(135deg,#C9A227,#E6C84A) !important;
    color: #0D1117 !important; border: none !important;
    border-radius: 8px !important; font-weight: 700 !important;
}
.stButton > button:hover { opacity: 0.9 !important; }
.stTabs [data-baseweb="tab-list"] {
    background: #161B22; border-radius: 10px;
    padding: 4px; gap: 4px;
    border: 1px solid #30363D;
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
    background: #161B22 !important;
    border-color: #30363D !important; color: #E6EDF3 !important;
    border-radius: 8px !important;
}
.streamlit-expanderHeader {
    background: #161B22 !important;
    border: 1px solid #30363D !important;
    color: #E6EDF3 !important; border-radius: 8px !important;
}
section[data-testid="stSidebar"] {
    background: #0D1117 !important;
    border-right: 1px solid #30363D !important;
}
section[data-testid="stSidebar"] * { color: #E6EDF3 !important; }
.stRadio > div { gap: 4px !important; }
.stRadio label {
    background: #161B22 !important;
    border: 1px solid #30363D !important;
    border-radius: 8px !important; padding: 8px 12px !important;
    color: #E6EDF3 !important; cursor: pointer !important;
    transition: all 0.2s !important;
}
.stRadio label:hover { border-color: #C9A227 !important; }
.stMetric { background: #161B22 !important; border-radius: 10px !important;
            padding: 12px !important; border: 1px solid #30363D !important; }
.stMetric label { color: #8B949E !important; }
.stMetric [data-testid="stMetricValue"] { color: #C9A227 !important; }
.stDataFrame { background: #161B22 !important; }
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

def s(v): return str(v).replace("'","''") if v else ""

# ════════════════════════════════════════════════════════════════════
# PERFIS E USUÁRIOS DEMO
# ════════════════════════════════════════════════════════════════════
USUARIOS = {
    "consultante@meridian.com":   {"nome":"João Silva",      "perfil":"consultante"},
    "curador@meridian.com":       {"nome":"Maria Santos",    "perfil":"curador"},
    "governanca@meridian.com":    {"nome":"Tereza Cristina", "perfil":"curador"},
    "ana.lima@meridian.com":      {"nome":"Ana Lima",        "perfil":"aprovador"},
    "fernando.dias@meridian.com": {"nome":"Fernando Dias",   "perfil":"aprovador"},
}

PERFIL_COR = {
    "consultante": "#58A6FF",
    "curador":     "#C9A227",
    "aprovador":   "#3FB950",
}
PERFIL_LABEL = {
    "consultante": "👁️ Consultante",
    "curador":     "✏️ Curador",
    "aprovador":   "✅ Aprovador",
}

# ════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding:20px 0 8px;text-align:center;">
        <div style="background:linear-gradient(135deg,#C9A227,#E6C84A);
                    border-radius:12px;width:48px;height:48px;
                    display:flex;align-items:center;justify-content:center;
                    margin:0 auto 8px;font-size:1.4rem;">🏦</div>
        <div style="font-size:0.95rem;font-weight:800;color:#E6EDF3;">Banco Meridian</div>
        <div style="font-size:0.72rem;color:#8B949E;">Plataforma de Governança</div>
    </div>
    <div style="height:1px;background:#30363D;margin:8px 0 16px;"></div>
    """, unsafe_allow_html=True)

    if "usuario" not in st.session_state:
        st.session_state["usuario"] = None

    if not st.session_state["usuario"]:
        st.markdown('<div style="color:#8B949E;font-size:0.75rem;font-weight:600;'
                    'text-transform:uppercase;letter-spacing:1px;'
                    'margin-bottom:8px;">🔐 Acesso</div>', unsafe_allow_html=True)
        email = st.selectbox("Usuário demo:", list(USUARIOS.keys()),
            format_func=lambda x: f"{USUARIOS[x]['nome']} · {USUARIOS[x]['perfil']}")
        if st.button("Entrar →", key="login"):
            st.session_state["usuario"] = email
            st.rerun()
        st.stop()
    else:
        u = USUARIOS[st.session_state["usuario"]]
        cor = PERFIL_COR[u["perfil"]]
        st.markdown(f"""
        <div style="background:#161B22;border:1px solid #30363D;
                    border-radius:10px;padding:10px 12px;margin-bottom:16px;">
            <div style="font-size:0.68rem;color:#8B949E;text-transform:uppercase;
                        letter-spacing:1px;">Usuário logado</div>
            <div style="font-weight:700;color:#E6EDF3;font-size:0.9rem;">{u['nome']}</div>
            <div style="color:{cor};font-size:0.78rem;font-weight:600;">
                {PERFIL_LABEL[u['perfil']]}</div>
        </div>
        """, unsafe_allow_html=True)

        # Navegação
        def nav_section(title):
            st.markdown(f'<div style="color:#8B949E;font-size:0.68rem;font-weight:700;'
                        f'text-transform:uppercase;letter-spacing:1.5px;'
                        f'margin:12px 0 4px 4px;">{title}</div>', unsafe_allow_html=True)

        nav_section("PESSOAL")
        paginas_pessoal = ["⚡ Meu Espaço"]
        nav_section("DESCOBERTA")
        paginas_descoberta = ["🏠 Início","📋 Catálogo","📖 Glossário","🏛️ Domínios"]
        nav_section("CONFIABILIDADE")
        paginas_conf = ["🛡️ Scorecard"]
        nav_section("OPERAÇÃO")
        paginas_op = ["✏️ Curadoria","🕐 Auditoria"]

        todas = (paginas_pessoal + paginas_descoberta +
                 paginas_conf + paginas_op)
        pagina = st.radio("", todas, key="nav", label_visibility="collapsed")

        st.markdown('<div style="height:1px;background:#30363D;margin:16px 0 8px;"></div>',
                    unsafe_allow_html=True)
        if st.button("Sair", key="logout"):
            st.session_state["usuario"] = None
            st.rerun()

# Dados do usuário
usuario    = st.session_state["usuario"]
u          = USUARIOS[usuario]
perfil     = u["perfil"]
is_curador   = perfil in ["curador","aprovador"]
is_aprovador = perfil == "aprovador"

# ════════════════════════════════════════════════════════════════════
# COMPONENTES REUTILIZÁVEIS
# ════════════════════════════════════════════════════════════════════
def card_kpi(valor, label, cor="#C9A227", icone=""):
    return f"""
    <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;
                padding:16px 20px;border-top:3px solid {cor};">
        <div style="font-size:0.7rem;color:#8B949E;font-weight:600;
                    text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">
            {icone} {label}</div>
        <div style="font-size:2rem;font-weight:800;color:{cor};">{valor}</div>
    </div>"""

def badge_selo(selo):
    m = {"certificado":("🟢","#3FB950"),
         "parcial":("🟡","#C9A227"),
         "pendente":("🔴","#F85149")}
    e, c = m.get(selo, ("⚪","#8B949E"))
    return f'<span style="color:{c};font-weight:700">{e} {selo.capitalize()}</span>'

def badge_status(status):
    m = {"homologado":("✅","#3FB950","Homologado"),
         "em_revisao":("🔵","#58A6FF","Em Revisão"),
         "rascunho":  ("📄","#8B949E","Rascunho")}
    e, c, l = m.get(status, ("⚪","#8B949E", status))
    return f'<span style="background:{c}22;color:{c};border:1px solid {c}44;'\
           f'border-radius:20px;padding:2px 10px;font-size:0.78rem;font-weight:600;">'\
           f'{e} {l}</span>'

def header_pagina(titulo, subtitulo=""):
    cor = PERFIL_COR[perfil]
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#161B22,#1C2128);
                border:1px solid #30363D;border-radius:12px;
                padding:20px 24px;margin-bottom:20px;
                border-left:4px solid #C9A227;">
        <div style="display:flex;align-items:center;justify-content:space-between;">
            <div>
                <div style="color:#E6EDF3;font-size:1.3rem;font-weight:800;">{titulo}</div>
                {f'<div style="color:#8B949E;font-size:0.82rem;margin-top:2px;">{subtitulo}</div>'
                 if subtitulo else ''}
            </div>
            <div style="text-align:right;">
                <div style="color:{cor};font-size:0.8rem;font-weight:600;">
                    {PERFIL_LABEL[perfil]}</div>
                <div style="color:#8B949E;font-size:0.72rem;">{u['nome']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# PÁGINA: INÍCIO
# ════════════════════════════════════════════════════════════════════
if pagina == "🏠 Início":
    st.markdown("""
    <div style="background:linear-gradient(135deg,#161B22 0%,#1C2128 100%);
                border:1px solid #30363D;border-radius:16px;
                padding:32px;margin-bottom:24px;
                border-top:3px solid #C9A227;">
        <div style="display:flex;align-items:center;gap:16px;margin-bottom:8px;">
            <div style="background:linear-gradient(135deg,#C9A227,#E6C84A);
                        border-radius:12px;padding:12px;font-size:1.8rem;">🏦</div>
            <div>
                <div style="color:#E6EDF3;font-size:1.6rem;font-weight:800;
                            line-height:1.2;">Plataforma de Governança de Dados</div>
                <div style="color:#8B949E;font-size:0.9rem;margin-top:4px;">
                    Um único ambiente para descobrir, entender e confiar nos dados.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    df_meta, _ = qry("SELECT * FROM meridian_governanca.tabelas_metadata")
    df_gloss, _ = qry("SELECT * FROM meridian_governanca.business_glossary")

    total_ativos  = len(df_meta) if not df_meta.empty else 0
    total_dom     = df_meta["dominio"].nunique() if not df_meta.empty else 0
    total_termos  = len(df_gloss) if not df_gloss.empty else 0
    score_medio   = df_meta["score_completude"].mean() if not df_meta.empty else 0
    total_cert    = len(df_meta[df_meta["selo"]=="certificado"]) if not df_meta.empty else 0
    pct_cert      = (total_cert/total_ativos*100) if total_ativos else 0

    # KPIs principais
    k1,k2,k3,k4,k5 = st.columns(5)
    with k1: st.markdown(card_kpi(total_ativos,"Ativos Catalogados","#C9A227","🗂️"),
                         unsafe_allow_html=True)
    with k2: st.markdown(card_kpi(total_dom,"Domínios de Negócio","#58A6FF","🏛️"),
                         unsafe_allow_html=True)
    with k3: st.markdown(card_kpi(total_termos,"Termos de Negócio","#BC8CFF","📖"),
                         unsafe_allow_html=True)
    with k4: st.markdown(card_kpi(f"{score_medio:.0f}%","Score Médio de Confiabilidade",
                         "#3FB950" if score_medio>=80 else "#C9A227" if score_medio>=60
                         else "#F85149","🛡️"), unsafe_allow_html=True)
    with k5: st.markdown(card_kpi("100%","Rastreabilidade e Auditoria","#3FB950","✅"),
                         unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # Grid de módulos
    col_cat, col_score, col_dom = st.columns(3)

    with col_cat:
        st.markdown("""
        <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;
                    padding:20px;height:100%;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
                <div style="background:#C9A22722;border-radius:8px;padding:8px;
                            font-size:1.2rem;">🗂️</div>
                <div style="color:#E6EDF3;font-weight:700;">Catálogo de Dados</div>
            </div>
        """, unsafe_allow_html=True)
        if not df_meta.empty:
            for _, row in df_meta.head(4).iterrows():
                cor_score = "#3FB950" if row["score_completude"]==100 else \
                            "#C9A227" if row["score_completude"]>=60 else "#F85149"
                st.markdown(f"""
                <div style="background:#0D1117;border:1px solid #30363D;border-radius:8px;
                            padding:10px 12px;margin-bottom:8px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div style="color:#C9A227;font-weight:600;font-size:0.85rem;">
                            {row['table_name']}</div>
                        <div style="color:{cor_score};font-weight:700;font-size:0.85rem;">
                            {row['score_completude']}%</div>
                    </div>
                    <div style="color:#8B949E;font-size:0.75rem;margin-top:4px;
                                white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                        {row['descricao'][:60] + '...' if row['descricao'] and
                         len(row['descricao'])>60 else row['descricao'] or 'Sem descrição'}</div>
                    <div style="margin-top:6px;">
                        <span style="background:#58A6FF22;color:#58A6FF;border-radius:4px;
                                     padding:2px 8px;font-size:0.7rem;">{row['schema_name']}</span>
                        {f'<span style="background:#C9A22722;color:#C9A227;border-radius:4px;padding:2px 8px;font-size:0.7rem;margin-left:4px;">{row["dominio"]}</span>' if row['dominio'] else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_score:
        st.markdown("""
        <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;
                    padding:20px;height:100%;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
                <div style="background:#3FB95022;border-radius:8px;padding:8px;
                            font-size:1.2rem;">🛡️</div>
                <div style="color:#E6EDF3;font-weight:700;">Scorecard de Confiabilidade</div>
            </div>
        """, unsafe_allow_html=True)
        if not df_meta.empty:
            pilares = {
                "Documentação": df_meta["descricao"].apply(lambda x: bool(x)).mean()*100,
                "Ownership":    df_meta["data_owner"].apply(lambda x: bool(x)).mean()*100,
                "Certificação": (len(df_meta[df_meta["selo"]=="certificado"])/len(df_meta))*100,
                "Qualidade":    df_meta["score_completude"].mean(),
            }
            score_geral = sum(pilares.values())/len(pilares)
            st.markdown(f"""
            <div style="text-align:center;padding:16px 0;">
                <div style="font-size:3.5rem;font-weight:800;color:#C9A227;">
                    {score_geral:.0f}%</div>
                <div style="color:#8B949E;font-size:0.85rem;">score médio do domínio</div>
            </div>
            """, unsafe_allow_html=True)
            for pilar, val in pilares.items():
                cor = "#3FB950" if val>=80 else "#C9A227" if val>=60 else "#F85149"
                st.markdown(f"""
                <div style="margin-bottom:12px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                        <span style="color:#E6EDF3;font-size:0.82rem;">{pilar}</span>
                        <span style="color:{cor};font-weight:700;font-size:0.82rem;">
                            {val:.0f}%</span>
                    </div>
                    <div style="background:#30363D;border-radius:4px;height:6px;">
                        <div style="background:{cor};border-radius:4px;height:6px;
                                    width:{min(val,100):.0f}%;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_dom:
        st.markdown("""
        <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;
                    padding:20px;height:100%;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
                <div style="background:#BC8CFF22;border-radius:8px;padding:8px;
                            font-size:1.2rem;">🏛️</div>
                <div style="color:#E6EDF3;font-weight:700;">Domínios de Negócio</div>
            </div>
        """, unsafe_allow_html=True)
        if not df_meta.empty:
            dom_scores = df_meta.groupby("dominio")["score_completude"].mean()\
                               .sort_values(ascending=False)
            for dom, score in dom_scores.items():
                if not dom: continue
                cor = "#3FB950" if score>=80 else "#C9A227" if score>=60 else "#F85149"
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:8px 0;border-bottom:1px solid #21262D;">
                    <span style="color:#E6EDF3;font-size:0.85rem;">{dom}</span>
                    <span style="color:{cor};font-weight:700;font-size:0.85rem;">
                        {score:.0f}%</span>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # Rodapé de módulos
    m1,m2,m3,m4 = st.columns(4)
    modulos = [
        ("🧠","Curadoria Inteligente","IA sugerindo descrição, domínio e classificação para acelerar a documentação com qualidade.","✏️ Curadoria"),
        ("🛡️","Trilha de Auditoria","Rastreabilidade completa de quem alterou, quando e o que mudou.","🕐 Auditoria"),
        ("⚡","Meu Espaço","Acompanhe suas pendências, aprovações e atividades.","⚡ Meu Espaço"),
        ("🔍","Descobrir Dados","Encontre ativos, termos, indicadores e responsáveis de forma rápida.","📋 Catálogo"),
    ]
    for col, (icone, titulo, desc, link) in zip([m1,m2,m3,m4], modulos):
        with col:
            st.markdown(f"""
            <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;
                        padding:16px;text-align:center;">
                <div style="font-size:1.8rem;margin-bottom:8px;">{icone}</div>
                <div style="color:#E6EDF3;font-weight:700;font-size:0.85rem;
                            margin-bottom:6px;">{titulo}</div>
                <div style="color:#8B949E;font-size:0.75rem;line-height:1.4;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# PÁGINA: MEU ESPAÇO
# ════════════════════════════════════════════════════════════════════
elif pagina == "⚡ Meu Espaço":
    header_pagina("⚡ Meu Espaço", f"Olá, {u['nome']}! Suas atividades e pendências.")

    if is_aprovador:
        # Fila de aprovação
        df_pend, _ = qry(f"""
            SELECT g.termo, g.dominio, g.area_negocio, g.criticidade,
                   g.glossary_id, g.steward_email
            FROM meridian_governanca.business_glossary g
            WHERE g.status = 'em_revisao'
        """)
        st.markdown("""
        <div style="background:#161B22;border:1px solid #F8514933;border-radius:12px;
                    padding:16px 20px;margin-bottom:16px;border-left:4px solid #F85149;">
            <div style="color:#F85149;font-weight:700;font-size:0.9rem;">
                🔔 Fila de Aprovação</div>
            <div style="color:#8B949E;font-size:0.78rem;">
                Termos aguardando sua aprovação</div>
        </div>
        """, unsafe_allow_html=True)
        if not df_pend.empty:
            for _, row in df_pend.iterrows():
                with st.expander(
                    f"📋 **{row['termo']}** · {row['dominio']} · "
                    f"Criticidade: {row['criticidade']}"
                ):
                    df_detail, _ = qry(f"""
                        SELECT termo, definicao, sinonimos, dominio,
                               area_negocio, criticidade, steward_email
                        FROM meridian_governanca.business_glossary
                        WHERE glossary_id = '{row['glossary_id']}'
                    """)
                    if not df_detail.empty:
                        r = df_detail.iloc[0]
                        st.markdown(f"**Definição:** {r['definicao']}")
                        st.markdown(f"**Sinônimos:** {r['sinonimos']}")
                        st.markdown(f"**Submetido por:** {r['steward_email']}")

                    col_ap, col_rej = st.columns(2)
                    with col_ap:
                        if st.button("✅ Aprovar", key=f"ap_{row['glossary_id']}"):
                            ok, err = exe(f"""
                                UPDATE meridian_governanca.business_glossary
                                SET status='homologado', atualizado_por='{s(usuario)}',
                                    atualizado_em=current_timestamp()
                                WHERE glossary_id='{row['glossary_id']}'
                            """)
                            if ok:
                                exe(f"""
                                    INSERT INTO meridian_governanca.glossary_approval_workflow
                                    VALUES ('{uuid.uuid4()}','{row['glossary_id']}',
                                    'aprovacao','em_revisao','homologado',
                                    '{s(usuario)}','Aprovado via Meu Espaço',
                                    current_timestamp())
                                """)
                                st.success("✅ Termo homologado!")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(f"Erro: {err}")
                    with col_rej:
                        motivo = st.text_input("Motivo da rejeição",
                                               key=f"mot_{row['glossary_id']}")
                        if st.button("❌ Rejeitar", key=f"rej_{row['glossary_id']}"):
                            if motivo:
                                ok, err = exe(f"""
                                    UPDATE meridian_governanca.business_glossary
                                    SET status='rascunho',
                                        atualizado_por='{s(usuario)}',
                                        atualizado_em=current_timestamp()
                                    WHERE glossary_id='{row['glossary_id']}'
                                """)
                                if ok:
                                    exe(f"""
                                        INSERT INTO meridian_governanca.glossary_approval_workflow
                                        VALUES ('{uuid.uuid4()}','{row['glossary_id']}',
                                        'rejeicao','em_revisao','rascunho',
                                        '{s(usuario)}','{s(motivo)}',
                                        current_timestamp())
                                    """)
                                    st.warning("↩️ Termo devolvido para rascunho.")
                                    st.cache_data.clear()
                                    st.rerun()
                            else:
                                st.warning("Informe o motivo da rejeição.")
        else:
            st.success("✅ Nenhum termo pendente de aprovação!")

    if is_curador:
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        df_meus, _ = qry(f"""
            SELECT termo, status, dominio, versao, atualizado_em
            FROM meridian_governanca.business_glossary
            WHERE steward_email = '{s(usuario)}'
            ORDER BY atualizado_em DESC
        """)
        st.markdown("""
        <div style="background:#161B22;border:1px solid #C9A22733;border-radius:12px;
                    padding:16px 20px;margin-bottom:16px;border-left:4px solid #C9A227;">
            <div style="color:#C9A227;font-weight:700;font-size:0.9rem;">
                ✏️ Meus Termos no Glossário</div>
        </div>
        """, unsafe_allow_html=True)
        if not df_meus.empty:
            df_meus["status_fmt"] = df_meus["status"].map({
                "homologado":"✅ Homologado",
                "em_revisao":"🔵 Em Revisão",
                "rascunho":"📄 Rascunho"
            })
            st.dataframe(df_meus[["termo","status_fmt","dominio","versao"]]\
                         .rename(columns={"termo":"Termo","status_fmt":"Status",
                                         "dominio":"Domínio","versao":"Versão"}),
                         use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum termo vinculado ao seu e-mail ainda.")

    if perfil == "consultante":
        st.markdown("""
        <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;
                    padding:32px;text-align:center;">
            <div style="font-size:2.5rem;margin-bottom:12px;">👁️</div>
            <div style="color:#E6EDF3;font-weight:700;margin-bottom:8px;">
                Perfil Consultante</div>
            <div style="color:#8B949E;">
                Você tem acesso de leitura à plataforma.<br>
                Para solicitar acesso de curadoria, entre em contato com a equipe de Governança.
            </div>
        </div>
        """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# PÁGINA: CATÁLOGO
# ════════════════════════════════════════════════════════════════════
elif pagina == "📋 Catálogo":
    header_pagina("📋 Catálogo de Dados",
                  "Busque por conceito, ativo, domínio, owner ou steward")

    df_cat, err = qry("""
        SELECT schema_name, table_name, descricao, dominio,
               data_owner, data_steward, funcao_negocio,
               score_completude, selo, tem_pii
        FROM meridian_governanca.tabelas_metadata
        ORDER BY score_completude DESC
    """)

    if err:
        st.error(f"Erro: {err}")
    elif not df_cat.empty:
        # Barra de busca
        busca = st.text_input("🔍 Buscar...",
            placeholder="Busque por nome, domínio, owner, steward...")

        f1,f2,f3,f4 = st.columns(4)
        with f1:
            f_schema = st.selectbox("Schema",
                ["Todos"]+sorted(df_cat["schema_name"].unique().tolist()))
        with f2:
            f_selo = st.selectbox("Selo",
                ["Todos","certificado","parcial","pendente"])
        with f3:
            doms = ["Todos"]+sorted([d for d in df_cat["dominio"].unique() if d])
            f_dom = st.selectbox("Domínio", doms)
        with f4:
            f_pii = st.selectbox("PII", ["Todos","Com PII","Sem PII"])

        df_f = df_cat.copy()
        if busca:
            mask = (df_f["table_name"].str.contains(busca, case=False, na=False) |
                    df_f["descricao"].str.contains(busca, case=False, na=False) |
                    df_f["dominio"].str.contains(busca, case=False, na=False) |
                    df_f["data_owner"].str.contains(busca, case=False, na=False))
            df_f = df_f[mask]
        if f_schema != "Todos": df_f = df_f[df_f["schema_name"]==f_schema]
        if f_selo   != "Todos": df_f = df_f[df_f["selo"]==f_selo]
        if f_dom    != "Todos": df_f = df_f[df_f["dominio"]==f_dom]
        if f_pii == "Com PII":  df_f = df_f[df_f["tem_pii"]==True]
        if f_pii == "Sem PII":  df_f = df_f[df_f["tem_pii"]==False]

        st.markdown(f'<div style="color:#8B949E;font-size:0.8rem;margin:8px 0;">'
                    f'{len(df_f)} ativo(s) encontrado(s)</div>', unsafe_allow_html=True)

        for _, row in df_f.iterrows():
            cor_score = ("#3FB950" if row["score_completude"]==100 else
                         "#C9A227" if row["score_completude"]>=60 else "#F85149")
            pii_badge = ('🔒 PII' if row["tem_pii"] else "")
            with st.expander(
                f"**{row['table_name']}** · {row['schema_name']} · "
                f"{row['score_completude']}% · {pii_badge}"
            ):
                c1, c2, c3 = st.columns([3,2,1])
                with c1:
                    st.markdown(f"**📝 Descrição**")
                    st.markdown(row["descricao"] or "*Sem descrição*")
                    if row["funcao_negocio"]:
                        st.markdown(f"**⚙️ Função:** {row['funcao_negocio']}")
                with c2:
                    st.markdown(f"**👤 Owner:** {row['data_owner'] or '—'}")
                    st.markdown(f"**🔧 Steward:** {row['data_steward'] or '—'}")
                    st.markdown(f"**🏛️ Domínio:** {row['dominio'] or '—'}")
                with c3:
                    st.markdown(f"""
                    <div style="text-align:center;background:#0D1117;
                                border-radius:10px;padding:12px;">
                        <div style="font-size:1.8rem;font-weight:800;color:{cor_score};">
                            {row['score_completude']}%</div>
                        <div style="font-size:0.7rem;color:#8B949E;">Score</div>
                    </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# PÁGINA: GLOSSÁRIO
# ════════════════════════════════════════════════════════════════════
elif pagina == "📖 Glossário":
    header_pagina("📖 Glossário de Negócio",
                  "O coração semântico da governança")

    df_g, err = qry("""
        SELECT glossary_id, termo, definicao, sinonimos, dominio,
               area_negocio, criticidade, owner_email, steward_email,
               status, versao, tem_pii
        FROM meridian_governanca.business_glossary
        ORDER BY CASE status WHEN 'homologado' THEN 1
                             WHEN 'em_revisao' THEN 2 ELSE 3 END, termo
    """)

    if err:
        st.error(f"Erro: {err}")
    elif not df_g.empty:
        # Métricas
        m1,m2,m3,m4 = st.columns(4)
        with m1: st.markdown(card_kpi(len(df_g),"Total de Termos","#C9A227","📖"),
                             unsafe_allow_html=True)
        with m2: st.markdown(card_kpi(
            len(df_g[df_g["status"]=="homologado"]),"✅ Homologados","#3FB950"),
            unsafe_allow_html=True)
        with m3: st.markdown(card_kpi(
            len(df_g[df_g["status"]=="em_revisao"]),"🔵 Em Revisão","#58A6FF"),
            unsafe_allow_html=True)
        with m4: st.markdown(card_kpi(
            len(df_g[df_g["status"]=="rascunho"]),"📄 Rascunho","#8B949E"),
            unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Filtros
        gf1,gf2,gf3,gf4 = st.columns(4)
        with gf1:
            busca_g = st.text_input("🔍 Buscar termo...", key="busca_g")
        with gf2:
            g_dom = st.selectbox("Domínio",
                ["Todos"]+sorted(df_g["dominio"].unique().tolist()), key="g_dom")
        with gf3:
            g_status = st.selectbox("Status",
                ["Todos","homologado","em_revisao","rascunho"], key="g_status")
        with gf4:
            g_crit = st.selectbox("Criticidade",
                ["Todos","Crítico","Alto","Médio","Baixo"], key="g_crit")

        df_gf = df_g.copy()
        if busca_g:
            df_gf = df_gf[df_gf["termo"].str.contains(busca_g, case=False, na=False) |
                          df_gf["definicao"].str.contains(busca_g, case=False, na=False)]
        if g_dom    != "Todos": df_gf = df_gf[df_gf["dominio"]==g_dom]
        if g_status != "Todos": df_gf = df_gf[df_gf["status"]==g_status]
        if g_crit   != "Todos": df_gf = df_gf[df_gf["criticidade"]==g_crit]

        # Novo termo (curador/aprovador)
        if is_curador:
            with st.expander("➕ Criar novo termo"):
                nt1,nt2 = st.columns(2)
                with nt1:
                    n_termo  = st.text_input("Termo *", key="n_termo")
                    n_def    = st.text_area("Definição *", key="n_def", height=80)
                    n_sino   = st.text_input("Sinônimos", key="n_sino")
                with nt2:
                    n_dom   = st.selectbox("Domínio *",
                        ["Crédito","Pagamentos","Clientes","Compliance","Produtos"],
                        key="n_dom")
                    n_area  = st.text_input("Área de Negócio", key="n_area")
                    n_crit  = st.selectbox("Criticidade",
                        ["Crítico","Alto","Médio","Baixo"], key="n_crit")
                    n_pii   = st.checkbox("Contém PII?", key="n_pii")
                if st.button("💾 Criar Termo", key="btn_criar_termo"):
                    if n_termo and n_def:
                        gid = str(uuid.uuid4())
                        ok, err2 = exe(f"""
                            INSERT INTO meridian_governanca.business_glossary VALUES
                            ('{gid}','{s(n_termo)}','{s(n_def)}','{s(n_sino)}',
                            '{s(n_dom)}','{s(n_area)}','{s(n_crit)}',
                            '{s(usuario)}','{s(usuario)}','rascunho',1,
                            {'true' if n_pii else 'false'},
                            '{s(usuario)}',current_timestamp(),
                            '{s(usuario)}',current_timestamp())
                        """)
                        if ok:
                            exe(f"""
                                INSERT INTO meridian_governanca.glossary_approval_workflow
                                VALUES ('{uuid.uuid4()}','{gid}','criacao','',
                                'rascunho','','{s(usuario)}',current_timestamp())
                            """)
                            st.success(f"✅ Termo '{n_termo}' criado em Rascunho!")
                            st.cache_data.clear()
                            st.rerun()
                        else: st.error(f"Erro: {err2}")
                    else: st.warning("Preencha Termo e Definição.")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Cards dos termos
        for _, row in df_gf.iterrows():
            cor_crit = {"Crítico":"#F85149","Alto":"#FF7B72",
                        "Médio":"#C9A227","Baixo":"#3FB950"}.get(row["criticidade"],"#8B949E")
            with st.expander(
                f"**{row['termo']}** · "
                f"{'✅' if row['status']=='homologado' else '🔵' if row['status']=='em_revisao' else '📄'}"
                f" {row['status'].replace('_',' ').title()} · "
                f"{row['dominio']} · v{row['versao']}"
            ):
                gc1, gc2 = st.columns([3,1])
                with gc1:
                    st.markdown(f"**📝 Definição**")
                    st.markdown(f"> {row['definicao']}")
                    if row["sinonimos"]:
                        st.markdown(f"**Sinônimos:** `{row['sinonimos']}`")

                    df_rules, _ = qry(f"""
                        SELECT nome_regra, descricao_regra, categoria
                        FROM meridian_governanca.business_rules
                        WHERE glossary_id = '{row['glossary_id']}'
                        ORDER BY categoria
                    """)
                    if not df_rules.empty:
                        st.markdown("**📏 Regras de Negócio**")
                        for _, r in df_rules.iterrows():
                            st.markdown(f"- **{r['nome_regra']}** "
                                        f"`{r['categoria']}` — {r['descricao_regra']}")

                    df_links, _ = qry(f"""
                        SELECT asset_type, schema_name, table_name, column_name
                        FROM meridian_governanca.glossary_asset_link
                        WHERE glossary_id = '{row['glossary_id']}'
                    """)
                    if not df_links.empty:
                        st.markdown("**🔗 Ativos Técnicos Vinculados**")
                        for _, l in df_links.iterrows():
                            col_info = f".`{l['column_name']}`" if l["column_name"] else ""
                            st.markdown(f"- `{l['schema_name']}.{l['table_name']}"
                                        f"{col_info}` ({l['asset_type']})")

                    # Ações curador
                    if is_curador and row["status"] == "rascunho":
                        if st.button("📤 Submeter para Revisão",
                                     key=f"sub_{row['glossary_id']}"):
                            ok, err2 = exe(f"""
                                UPDATE meridian_governanca.business_glossary
                                SET status='em_revisao',
                                    atualizado_por='{s(usuario)}',
                                    atualizado_em=current_timestamp()
                                WHERE glossary_id='{row['glossary_id']}'
                            """)
                            if ok:
                                exe(f"""
                                    INSERT INTO meridian_governanca.glossary_approval_workflow
                                    VALUES ('{uuid.uuid4()}','{row['glossary_id']}',
                                    'submissao','rascunho','em_revisao','',
                                    '{s(usuario)}',current_timestamp())
                                """)
                                st.success("✅ Submetido para revisão!")
                                st.cache_data.clear()
                                st.rerun()
                            else: st.error(f"Erro: {err2}")

                    # Ações aprovador
                    if is_aprovador and row["status"] == "em_revisao":
                        ca, cr = st.columns(2)
                        with ca:
                            if st.button("✅ Aprovar",
                                         key=f"ap2_{row['glossary_id']}"):
                                ok, _ = exe(f"""
                                    UPDATE meridian_governanca.business_glossary
                                    SET status='homologado',
                                        atualizado_por='{s(usuario)}',
                                        atualizado_em=current_timestamp()
                                    WHERE glossary_id='{row['glossary_id']}'
                                """)
                                if ok:
                                    exe(f"""
                                        INSERT INTO meridian_governanca.glossary_approval_workflow
                                        VALUES ('{uuid.uuid4()}','{row['glossary_id']}',
                                        'aprovacao','em_revisao','homologado',
                                        '{s(usuario)}','Aprovado',current_timestamp())
                                    """)
                                    st.success("✅ Homologado!")
                                    st.cache_data.clear()
                                    st.rerun()
                        with cr:
                            if st.button("❌ Rejeitar",
                                         key=f"rej2_{row['glossary_id']}"):
                                ok, _ = exe(f"""
                                    UPDATE meridian_governanca.business_glossary
                                    SET status='rascunho',
                                        atualizado_por='{s(usuario)}',
                                        atualizado_em=current_timestamp()
                                    WHERE glossary_id='{row['glossary_id']}'
                                """)
                                if ok:
                                    st.warning("↩️ Devolvido para rascunho.")
                                    st.cache_data.clear()
                                    st.rerun()

                with gc2:
                    st.markdown(f"""
                    <div style="background:#0D1117;border:1px solid #30363D;
                                border-radius:10px;padding:14px;">
                        <div style="font-size:0.68rem;color:#8B949E;font-weight:600;
                                    text-transform:uppercase;">CRITICIDADE</div>
                        <div style="color:{cor_crit};font-weight:700;
                                    margin-bottom:10px;">{row['criticidade']}</div>
                        <div style="font-size:0.68rem;color:#8B949E;font-weight:600;
                                    text-transform:uppercase;">VERSÃO</div>
                        <div style="color:#E6EDF3;font-weight:700;
                                    margin-bottom:10px;">v{row['versao']}</div>
                        <div style="font-size:0.68rem;color:#8B949E;font-weight:600;
                                    text-transform:uppercase;">OWNER</div>
                        <div style="color:#E6EDF3;font-size:0.78rem;
                                    margin-bottom:10px;">{row['owner_email']}</div>
                        <div style="font-size:0.68rem;color:#8B949E;font-weight:600;
                                    text-transform:uppercase;">STEWARD</div>
                        <div style="color:#E6EDF3;font-size:0.78rem;
                                    margin-bottom:10px;">{row['steward_email']}</div>
                        {f'<div style="color:#F85149;font-weight:600;font-size:0.8rem;">🔒 Contém PII</div>' if row['tem_pii'] else ''}
                    </div>
                    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# PÁGINA: DOMÍNIOS
# ════════════════════════════════════════════════════════════════════
elif pagina == "🏛️ Domínios":
    header_pagina("🏛️ Domínios de Negócio",
                  "Cada domínio possui seu próprio espaço de governança")

    df_dom, _ = qry("""
        SELECT dominio, schema_name, table_name, data_owner,
               data_steward, score_completude, selo, tem_pii
        FROM meridian_governanca.tabelas_metadata
        WHERE dominio IS NOT NULL AND dominio != ''
    """)
    df_termos, _ = qry("""
        SELECT dominio, COUNT(*) as total_termos
        FROM meridian_governanca.business_glossary
        WHERE dominio IS NOT NULL
        GROUP BY dominio
    """)

    if not df_dom.empty:
        dominios = sorted(df_dom["dominio"].unique().tolist())
        termos_por_dom = dict(zip(df_termos["dominio"], df_termos["total_termos"])) \
                         if not df_termos.empty else {}

        for dom in dominios:
            df_d = df_dom[df_dom["dominio"]==dom]
            score_medio = df_d["score_completude"].mean()
            owners   = df_d["data_owner"].dropna().unique().tolist()
            stewards = df_d["data_steward"].dropna().unique().tolist()
            total_pii = df_d["tem_pii"].sum()
            cor = "#3FB950" if score_medio>=80 else \
                  "#C9A227" if score_medio>=60 else "#F85149"
            n_termos = termos_por_dom.get(dom, 0)

            with st.expander(
                f"**{dom}** · {len(df_d)} tabelas · "
                f"Score: {score_medio:.0f}% · {n_termos} termos"
            ):
                d1,d2,d3,d4 = st.columns(4)
                with d1: st.markdown(card_kpi(len(df_d),"Tabelas","#58A6FF"),
                                     unsafe_allow_html=True)
                with d2: st.markdown(card_kpi(f"{score_medio:.0f}%",
                                              "Score Médio", cor),
                                     unsafe_allow_html=True)
                with d3: st.markdown(card_kpi(n_termos,"Termos Glossário","#BC8CFF"),
                                     unsafe_allow_html=True)
                with d4: st.markdown(card_kpi(int(total_pii),"Tabelas com PII","#F85149"),
                                     unsafe_allow_html=True)

                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                dc1, dc2 = st.columns(2)
                with dc1:
                    st.markdown("**👤 Data Owners**")
                    for o in owners:
                        if o: st.markdown(f"- {o}")
                    if not owners: st.markdown("*Nenhum owner definido*")
                with dc2:
                    st.markdown("**🔧 Data Stewards**")
                    for s_val in stewards:
                        if s_val: st.markdown(f"- {s_val}")
                    if not stewards: st.markdown("*Nenhum steward definido*")

                st.markdown("**📋 Tabelas do Domínio**")
                df_tab = df_d[["schema_name","table_name",
                               "score_completude","selo","tem_pii"]]\
                    .rename(columns={
                        "schema_name":"Schema","table_name":"Tabela",
                        "score_completude":"Score","selo":"Selo","tem_pii":"PII"
                    })
                df_tab["Selo"] = df_tab["Selo"].map({
                    "certificado":"🟢","parcial":"🟡","pendente":"🔴"})
                df_tab["PII"] = df_tab["PII"].map({True:"🔒",False:""})
                st.dataframe(df_tab, use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════════════════════
# PÁGINA: SCORECARD
# ════════════════════════════════════════════════════════════════════
elif pagina == "🛡️ Scorecard":
    header_pagina("🛡️ Scorecard de Confiabilidade",
                  "Visão objetiva da confiabilidade por ativo, domínio e área")

    df_sc, _ = qry("""
        SELECT schema_name, table_name, dominio, data_owner,
               data_steward, descricao, score_completude, selo, tem_pii
        FROM meridian_governanca.tabelas_metadata
    """)

    if not df_sc.empty:
        # Score geral por pilar
        doc   = df_sc["descricao"].apply(bool).mean()*100
        own   = df_sc["data_owner"].apply(bool).mean()*100
        cert  = (len(df_sc[df_sc["selo"]=="certificado"])/len(df_sc))*100
        qual  = df_sc["score_completude"].mean()
        geral = (doc+own+cert+qual)/4

        st.markdown(f"""
        <div style="background:#161B22;border:1px solid #30363D;border-radius:16px;
                    padding:32px;text-align:center;margin-bottom:24px;">
            <div style="font-size:0.85rem;color:#8B949E;text-transform:uppercase;
                        letter-spacing:2px;margin-bottom:8px;">Score Geral de Confiabilidade</div>
            <div style="font-size:5rem;font-weight:800;
                        color:{'#3FB950' if geral>=80 else '#C9A227' if geral>=60 else '#F85149'};">
                {geral:.0f}%</div>
            <div style="color:#8B949E;font-size:0.85rem;">
                Baseado em Documentação, Ownership, Certificação e Qualidade</div>
        </div>
        """, unsafe_allow_html=True)

        p1,p2,p3,p4 = st.columns(4)
        for col, nome, val, icone in [
            (p1,"Documentação",doc,"📝"),
            (p2,"Ownership",own,"👤"),
            (p3,"Certificação",cert,"🏆"),
            (p4,"Qualidade",qual,"⭐"),
        ]:
            cor = "#3FB950" if val>=80 else "#C9A227" if val>=60 else "#F85149"
            with col:
                st.markdown(f"""
                <div style="background:#161B22;border:1px solid #30363D;
                            border-radius:12px;padding:20px;text-align:center;">
                    <div style="font-size:1.5rem;margin-bottom:8px;">{icone}</div>
                    <div style="font-size:2rem;font-weight:800;color:{cor};">{val:.0f}%</div>
                    <div style="color:#8B949E;font-size:0.78rem;">{nome}</div>
                    <div style="background:#30363D;border-radius:4px;height:6px;margin-top:10px;">
                        <div style="background:{cor};border-radius:4px;height:6px;
                                    width:{min(val,100):.0f}%;"></div>
                    </div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        # Score por domínio
        st.markdown('<div style="color:#E6EDF3;font-weight:700;'
                    'font-size:1rem;margin-bottom:12px;">Score por Domínio</div>',
                    unsafe_allow_html=True)
        dom_scores = df_sc.groupby("dominio")["score_completude"].mean()\
                         .reset_index().sort_values("score_completude", ascending=False)
        dom_scores = dom_scores[dom_scores["dominio"].apply(bool)]

        fig = px.bar(dom_scores, x="dominio", y="score_completude",
            color="score_completude",
            color_continuous_scale=["#F85149","#C9A227","#3FB950"],
            range_color=[0,100],
            labels={"dominio":"Domínio","score_completude":"Score (%)"},
            template="plotly_dark")
        fig.update_layout(
            paper_bgcolor="#161B22", plot_bgcolor="#161B22",
            font_family="Inter", showlegend=False,
            coloraxis_showscale=False, height=300,
            margin=dict(t=10,b=10,l=0,r=0)
        )
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

        # Ranking owners
        st.markdown('<div style="color:#E6EDF3;font-weight:700;'
                    'font-size:1rem;margin:16px 0 12px;">Ranking de Owners</div>',
                    unsafe_allow_html=True)
        df_own = df_sc[df_sc["data_owner"].apply(bool)]\
                    .groupby("data_owner")["score_completude"].mean()\
                    .reset_index().sort_values("score_completude", ascending=False)
        if not df_own.empty:
            for i, row in df_own.iterrows():
                cor = "#3FB950" if row["score_completude"]>=80 else \
                      "#C9A227" if row["score_completude"]>=60 else "#F85149"
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                            background:#161B22;border:1px solid #30363D;border-radius:8px;
                            padding:10px 16px;margin-bottom:6px;">
                    <span style="color:#E6EDF3;font-size:0.85rem;">{row['data_owner']}</span>
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div style="background:#30363D;border-radius:4px;height:6px;width:120px;">
                            <div style="background:{cor};border-radius:4px;height:6px;
                                        width:{min(row['score_completude'],100):.0f}%;"></div>
                        </div>
                        <span style="color:{cor};font-weight:700;font-size:0.85rem;
                                     width:40px;text-align:right;">
                            {row['score_completude']:.0f}%</span>
                    </div>
                </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# PÁGINA: CURADORIA
# ════════════════════════════════════════════════════════════════════
elif pagina == "✏️ Curadoria":
    if not is_curador:
        st.markdown("""
        <div style="background:#161B22;border:1px solid #F8514933;border-radius:12px;
                    padding:32px;text-align:center;">
            <div style="font-size:2.5rem;margin-bottom:12px;">🔒</div>
            <div style="color:#F85149;font-weight:700;">Acesso Restrito</div>
            <div style="color:#8B949E;">Esta área é exclusiva para Curadores e Aprovadores.</div>
        </div>""", unsafe_allow_html=True)
        st.stop()

    header_pagina("✏️ Curadoria de Metadados",
                  "Curadoria manual e assistida por IA")

    df_cur, _ = qry("""
        SELECT schema_name, table_name, descricao, dominio,
               data_owner, data_steward, funcao_negocio,
               score_completude, selo
        FROM meridian_governanca.tabelas_metadata
        ORDER BY score_completude ASC
    """)

    if not df_cur.empty:
        cur_tab1, cur_tab2 = st.tabs(["📋 Edição Individual","⚡ Edição em Lote"])

        with cur_tab1:
            schemas = sorted(df_cur["schema_name"].unique().tolist())
            c1, c2 = st.columns(2)
            with c1:
                sel_schema = st.selectbox("Schema", schemas, key="cur_schema")
            with c2:
                tabelas = df_cur[df_cur["schema_name"]==sel_schema]["table_name"].tolist()
                sel_tab = st.selectbox("Tabela", tabelas, key="cur_tab")

            row = df_cur[(df_cur["schema_name"]==sel_schema) &
                         (df_cur["table_name"]==sel_tab)].iloc[0]

            cor_s = ("#3FB950" if row["score_completude"]==100 else
                     "#C9A227" if row["score_completude"]>=60 else "#F85149")
            st.markdown(f"""
            <div style="background:#161B22;border:1px solid #30363D;border-radius:10px;
                        padding:12px 16px;margin:8px 0;
                        display:flex;justify-content:space-between;align-items:center;">
                <span style="color:#E6EDF3;font-weight:600;">
                    {sel_schema}.{sel_tab}</span>
                <span style="color:{cor_s};font-weight:800;font-size:1.1rem;">
                    {row['score_completude']}%</span>
            </div>""", unsafe_allow_html=True)

            ed1, ed2 = st.columns(2)
            with ed1:
                new_desc = st.text_area("📝 Descrição",
                    value=row["descricao"] or "", height=100, key="cur_desc")
                dominios_list = ["","Crédito","Pagamentos","Clientes",
                                 "Compliance","Produtos"]
                dom_idx = dominios_list.index(row["dominio"]) \
                          if row["dominio"] in dominios_list else 0
                new_dom = st.selectbox("🏛️ Domínio", dominios_list,
                    index=dom_idx, key="cur_dom")
                new_func = st.text_input("⚙️ Função de Negócio",
                    value=row["funcao_negocio"] or "", key="cur_func")
            with ed2:
                new_owner   = st.text_input("👤 Data Owner",
                    value=row["data_owner"] or "", key="cur_owner")
                new_steward = st.text_input("🔧 Data Steward",
                    value=row["data_steward"] or "", key="cur_steward")

                # Preview score
                filled = sum([bool(new_desc), bool(new_dom),
                              bool(new_owner), bool(new_steward), bool(new_func)])
                new_score = filled * 20
                new_cor = ("#3FB950" if new_score==100 else
                           "#C9A227" if new_score>=60 else "#F85149")
                st.markdown(f"""
                <div style="background:#0D1117;border:1px solid #30363D;
                            border-radius:10px;padding:16px;text-align:center;margin-top:8px;">
                    <div style="color:#8B949E;font-size:0.72rem;text-transform:uppercase;">
                        Novo Score</div>
                    <div style="font-size:2.5rem;font-weight:800;color:{new_cor};">
                        {new_score}%</div>
                    <div style="color:#8B949E;font-size:0.75rem;">{filled}/5 campos</div>
                </div>""", unsafe_allow_html=True)

            bc1, bc2 = st.columns(2)
            with bc1:
                if st.button("💾 Salvar", type="primary", key="cur_save"):
                    new_selo = ("certificado" if new_score==100 else
                                "parcial" if new_score>=60 else "pendente")
                    ok, err2 = exe(f"""
                        UPDATE meridian_governanca.tabelas_metadata
                        SET descricao='{s(new_desc)}', dominio='{s(new_dom)}',
                            data_owner='{s(new_owner)}',
                            data_steward='{s(new_steward)}',
                            funcao_negocio='{s(new_func)}',
                            score_completude={new_score}, selo='{new_selo}',
                            atualizado_em=current_timestamp()
                        WHERE schema_name='{sel_schema}'
                          AND table_name='{sel_tab}'
                    """)
                    if ok:
                        exe(f"""
                            INSERT INTO meridian_governanca.metadata_audit VALUES
                            ('{uuid.uuid4()}', current_timestamp(),
                            '{sel_schema}','{sel_tab}','tabela','',
                            'metadados_completos',
                            '{row["score_completude"]}','{new_score}',
                            'manual','{s(usuario)}','{s(usuario[:8])}')
                        """)
                        st.success(f"✅ Salvo! Novo score: {new_score}%")
                        st.cache_data.clear()
                        st.rerun()
                    else: st.error(f"Erro: {err2}")
            with bc2:
                if st.button("🤖 Sugerir com IA", key="cur_ai"):
                    with st.spinner("🧠 IA analisando a tabela..."):
                        import time; time.sleep(1)
                    # Sugestão simulada baseada no nome da tabela
                    sugestoes = {
                        "clientes_raw": ("Dados brutos de clientes ingeridos do sistema core bancário, contendo informações cadastrais e de contato.", "Clientes"),
                        "contas_raw": ("Dados brutos de contas correntes e poupança dos clientes do banco.", "Clientes"),
                        "transacoes_raw": ("Transações financeiras brutas de todos os canais digitais e físicos.", "Pagamentos"),
                        "propostas_credito_raw": ("Propostas de crédito recebidas pelos canais digitais e físicos, com status de aprovação.", "Crédito"),
                        "pix_raw": ("Transações PIX brutas recebidas do Sistema de Pagamentos Instantâneos (SPI) do Banco Central.", "Pagamentos"),
                        "dim_clientes": ("Dimensão de clientes tratada e enriquecida com segmentação e score interno.", "Clientes"),
                        "fato_transacoes": ("Fato de transações financeiras consolidadas por período e canal.", "Pagamentos"),
                        "fato_credito": ("Fato de operações de crédito aprovadas e recusadas com taxa e prazo.", "Crédito"),
                        "fato_inadimplencia": ("Fato de inadimplência com dias de atraso e valores em aberto.", "Crédito"),
                        "indicadores_carteira": ("Indicadores consolidados da carteira de crédito por período de referência.", "Crédito"),
                        "perfil_cliente_360": ("Visão 360 do cliente com score interno, saldo consolidado e propensão a churn.", "Clientes"),
                        "base_lgpd": ("Mapeamento de dados pessoais por cliente para conformidade com a LGPD.", "Compliance"),
                        "indicadores_pix": ("Indicadores de volume e performance das transações PIX por período.", "Pagamentos"),
                    }
                    sug = sugestoes.get(sel_tab, (f"Tabela {sel_tab} do schema {sel_schema}.", ""))
                    st.session_state["ai_sug_desc"] = sug[0]
                    st.session_state["ai_sug_dom"]  = sug[1]

                if "ai_sug_desc" in st.session_state:
                    st.markdown("""
                    <div style="background:#C9A22711;border:1px solid #C9A22733;
                                border-radius:8px;padding:12px;margin-top:8px;">
                        <div style="color:#C9A227;font-weight:700;font-size:0.82rem;
                                    margin-bottom:6px;">🤖 Sugestão da IA</div>
                    </div>""", unsafe_allow_html=True)
                    sug_d = st.text_area("Descrição sugerida",
                        value=st.session_state["ai_sug_desc"], key="sug_d")
                    sug_dom_opts = ["","Crédito","Pagamentos","Clientes",
                                    "Compliance","Produtos"]
                    sug_dom_v = st.session_state["ai_sug_dom"]
                    sug_dom_i = sug_dom_opts.index(sug_dom_v) \
                                if sug_dom_v in sug_dom_opts else 0
                    sug_dom = st.selectbox("Domínio sugerido", sug_dom_opts,
                        index=sug_dom_i, key="sug_dom2")
                    sa1, sa2 = st.columns(2)
                    with sa1:
                        if st.button("✅ Aceitar Sugestão", key="ai_aceitar"):
                            new_score_ai = sum([
                                bool(sug_d), bool(sug_dom),
                                bool(new_owner), bool(new_steward), bool(new_func)
                            ]) * 20
                            new_selo_ai = ("certificado" if new_score_ai==100 else
                                          "parcial" if new_score_ai>=60 else "pendente")
                            ok, _ = exe(f"""
                                UPDATE meridian_governanca.tabelas_metadata
                                SET descricao='{s(sug_d)}', dominio='{s(sug_dom)}',
                                    score_completude={new_score_ai},
                                    selo='{new_selo_ai}',
                                    atualizado_em=current_timestamp()
                                WHERE schema_name='{sel_schema}'
                                  AND table_name='{sel_tab}'
                            """)
                            if ok:
                                exe(f"""
                                    INSERT INTO meridian_governanca.metadata_audit VALUES
                                    ('{uuid.uuid4()}',current_timestamp(),
                                    '{sel_schema}','{sel_tab}','tabela','',
                                    'metadados_ia',
                                    '{row["score_completude"]}','{new_score_ai}',
                                    'ia','{s(usuario)}','{s(usuario[:8])}')
                                """)
                                st.success("✅ Sugestão da IA aplicada!")
                                del st.session_state["ai_sug_desc"]
                                del st.session_state["ai_sug_dom"]
                                st.cache_data.clear()
                                st.rerun()
                    with sa2:
                        if st.button("❌ Descartar", key="ai_descartar"):
                            del st.session_state["ai_sug_desc"]
                            del st.session_state["ai_sug_dom"]
                            st.rerun()

        with cur_tab2:
            st.markdown('<div style="color:#8B949E;font-size:0.85rem;margin-bottom:12px;">'
                        'Selecione tabelas e aplique o mesmo valor em lote.</div>',
                        unsafe_allow_html=True)
            f_lote_schema = st.selectbox("Filtrar por Schema",
                ["Todos"]+sorted(df_cur["schema_name"].unique().tolist()),
                key="lote_schema")
            f_lote_selo = st.selectbox("Filtrar por Selo",
                ["Todos","certificado","parcial","pendente"], key="lote_selo")

            df_lote = df_cur.copy()
            if f_lote_schema != "Todos":
                df_lote = df_lote[df_lote["schema_name"]==f_lote_schema]
            if f_lote_selo != "Todos":
                df_lote = df_lote[df_lote["selo"]==f_lote_selo]

            df_lote["Selecionar"] = False
            edited = st.data_editor(
                df_lote[["Selecionar","schema_name","table_name",
                         "score_completude","selo"]]\
                    .rename(columns={
                        "schema_name":"Schema","table_name":"Tabela",
                        "score_completude":"Score","selo":"Selo"
                    }),
                use_container_width=True, hide_index=True,
                column_config={"Selecionar": st.column_config.CheckboxColumn()}
            )
            selecionadas = edited[edited["Selecionar"]==True]

            if len(selecionadas) > 0:
                st.markdown(f'<div style="color:#C9A227;font-weight:600;">'
                            f'{len(selecionadas)} tabela(s) selecionada(s)</div>',
                            unsafe_allow_html=True)
                lb1, lb2, lb3 = st.columns(3)
                with lb1:
                    lote_dom = st.selectbox("Domínio (lote)",
                        ["","Crédito","Pagamentos","Clientes","Compliance","Produtos"],
                        key="lote_dom")
                with lb2:
                    lote_own = st.text_input("Owner (lote)", key="lote_own")
                with lb3:
                    lote_ste = st.text_input("Steward (lote)", key="lote_ste")

                if st.button(f"🚀 Aplicar em {len(selecionadas)} tabela(s)",
                             type="primary", key="lote_apply"):
                    erros = []
                    for _, r in selecionadas.iterrows():
                        sets = []
                        if lote_dom: sets.append(f"dominio='{s(lote_dom)}'")
                        if lote_own: sets.append(f"data_owner='{s(lote_own)}'")
                        if lote_ste: sets.append(f"data_steward='{s(lote_ste)}'")
                        if sets:
                            sets.append("atualizado_em=current_timestamp()")
                            ok, err2 = exe(f"""
                                UPDATE meridian_governanca.tabelas_metadata
                                SET {', '.join(sets)}
                                WHERE schema_name='{r['Schema']}'
                                  AND table_name='{r['Tabela']}'
                            """)
                            if not ok: erros.append(r["Tabela"])
                    if erros:
                        st.warning(f"Erros em: {erros}")
                    else:
                        st.success(f"✅ {len(selecionadas)} tabelas atualizadas!")
                        st.cache_data.clear()
                        st.rerun()

# ════════════════════════════════════════════════════════════════════
# PÁGINA: AUDITORIA
# ════════════════════════════════════════════════════════════════════
elif pagina == "🕐 Auditoria":
    if not is_curador:
        st.markdown("""
        <div style="background:#161B22;border:1px solid #F8514933;border-radius:12px;
                    padding:32px;text-align:center;">
            <div style="font-size:2.5rem;margin-bottom:12px;">🔒</div>
            <div style="color:#F85149;font-weight:700;">Acesso Restrito</div>
            <div style="color:#8B949E;">Esta área é exclusiva para Curadores e Aprovadores.
            </div></div>""", unsafe_allow_html=True)
        st.stop()

    header_pagina("🕐 Trilha de Auditoria",
                  "Rastreabilidade completa — quem alterou, quando e o que mudou")

    df_aud, err = qry("""
        SELECT timestamp_op, schema_name, table_name, tipo_objeto,
               campo_alterado, valor_anterior, valor_novo,
               origem, alterado_por
        FROM meridian_governanca.metadata_audit
        ORDER BY timestamp_op DESC
        LIMIT 500
    """)

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
        total = len(df_aud)
        manual = len(df_aud[df_aud["origem"]=="manual"])
        ia_c   = len(df_aud[df_aud["origem"]=="ia"])

        a1,a2,a3 = st.columns(3)
        with a1: st.markdown(card_kpi(total,"Total Registros","#C9A227"),
                             unsafe_allow_html=True)
        with a2: st.markdown(card_kpi(manual,"Alterações Manuais","#58A6FF"),
                             unsafe_allow_html=True)
        with a3: st.markdown(card_kpi(ia_c,"Alterações via IA","#BC8CFF"),
                             unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        af1,af2,af3 = st.columns(3)
        with af1:
            f_schema_a = st.selectbox("Schema",
                ["Todos"]+sorted(df_aud["schema_name"].dropna().unique().tolist()),
                key="aud_schema")
        with af2:
            f_orig_a = st.selectbox("Origem",
                ["Todos","manual","ia"], key="aud_orig")
        with af3:
            f_lim = st.selectbox("Linhas", [50,100,200,500], key="aud_lim")

        df_af = df_aud.copy()
        if f_schema_a != "Todos":
            df_af = df_af[df_af["schema_name"]==f_schema_a]
        if f_orig_a != "Todos":
            df_af = df_af[df_af["origem"]==f_orig_a]
        df_af = df_af.head(f_lim)

        st.dataframe(
            df_af.rename(columns={
                "timestamp_op":"Data/Hora","schema_name":"Schema",
                "table_name":"Tabela","tipo_objeto":"Tipo",
                "campo_alterado":"Campo","valor_anterior":"Valor Anterior",
                "valor_novo":"Valor Novo","origem":"Origem",
                "alterado_por":"Alterado Por"
            }),
            use_container_width=True, hide_index=True
        )
