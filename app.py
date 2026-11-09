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
import vd_telas

st.set_page_config(
    page_title="Plataforma de Governança — Banco Meridian",
    page_icon="🏦", layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;0,700;1,400&family=Inter:wght@300;400;500;600;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box;}
html,body,.stApp{background:#FAFAFA !important;font-family:'Inter',sans-serif !important;color:#000000;
    font-feature-settings:"tnum" 1,"cv11" 1;-webkit-font-smoothing:antialiased;}
.stApp [data-testid="stMain"] p,.stApp [data-testid="stMain"] label,.stApp [data-testid="stMain"] li{color:#1A1A1A;}
.stApp a{color:#000000;text-decoration-color:#C9A227;text-underline-offset:3px;}
h1,h2,h3{font-family:'Inter',sans-serif !important;font-weight:650 !important;letter-spacing:-0.01em !important;color:#000000 !important;}

/* ── Topbar fixa ── */
header[data-testid="stHeader"]{
    background:transparent !important;
    height:0 !important;
    overflow:visible !important;
    border:none !important;}
/* Oculta elementos do header exceto o toolbar (contém o botão de expandir sidebar) */
header[data-testid="stHeader"] > *:not([data-testid="stToolbar"]):not([data-testid="collapsedControl"]){display:none !important;}
/* Sidebar toggle (stExpandSidebarButton — Streamlit ≥ 1.40) e fallback collapsedControl */
[data-testid="stExpandSidebarButton"],
[data-testid="collapsedControl"]{
    display:flex !important;
    position:fixed !important;
    top:10px !important;
    left:4px !important;
    z-index:999999 !important;
    background:#FFFFFF !important;
    border:1px solid #E5E5E5 !important;
    border-radius:6px !important;}
/* Toolbar (container do toggle): posicionado fixo, sem área visível além do botão */
[data-testid="stToolbar"]{
    position:fixed !important;
    top:0 !important;
    left:0 !important;
    height:52px !important;
    width:52px !important;
    overflow:visible !important;
    z-index:999998 !important;
    background:transparent !important;
    pointer-events:none !important;}
[data-testid="stToolbar"] > *{pointer-events:auto !important;}
.gov-topbar{
    position:fixed !important;top:0 !important;left:0 !important;right:0 !important;
    height:52px !important;background:#FFFFFF !important;z-index:99999 !important;
    display:flex !important;align-items:center !important;padding:0 20px !important;gap:14px !important;
    box-shadow:none !important;border-bottom:1px solid #E5E5E5 !important;}

/* ── Sidebar ── */
section[data-testid="stSidebar"]{
    background:#FFFFFF !important;border-right:1px solid #E5E5E5 !important;
    min-width:220px !important;margin-top:52px !important;padding-top:0 !important;}
section[data-testid="stSidebar"] > div{padding-top:0 !important;overflow-y:auto !important;}
section[data-testid="stSidebar"] > div::-webkit-scrollbar{width:4px;}
section[data-testid="stSidebar"] > div::-webkit-scrollbar-track{background:#FFFFFF;}
section[data-testid="stSidebar"] > div::-webkit-scrollbar-thumb{background:#D4D4D4;border-radius:4px;}
section[data-testid="stSidebar"] *{color:#5C5C5C !important;}
section[data-testid="stSidebar"] .stButton>button{
    background:transparent !important;color:#1A1A1A !important;border:none !important;
    border-radius:6px !important;font-weight:500 !important;font-size:0.81rem !important;
    text-align:left !important;justify-content:flex-start !important;
    padding:8px 14px !important;width:100% !important;box-shadow:none !important;
    margin-bottom:1px !important;transition:background .15s,color .15s !important;}
section[data-testid="stSidebar"] .stButton>button *{color:#1A1A1A !important;}
section[data-testid="stSidebar"] .stButton>button > div{justify-content:flex-start !important;}
section[data-testid="stSidebar"] .stButton>button:hover{background:#F5F5F5 !important;}
section[data-testid="stSidebar"] .stButton>button:hover *{color:#000000 !important;}
section[data-testid="stSidebar"] .stSelectbox>div>div{background:#FFFFFF !important;border:1px solid #D4D4D4 !important;}
section[data-testid="stSidebar"] .stSelectbox *{color:#000000 !important;}
section[data-testid="stSidebar"] .st-key-login button{background:#000000 !important;justify-content:center !important;font-weight:600 !important;}
section[data-testid="stSidebar"] .st-key-login button > div{justify-content:center !important;}
section[data-testid="stSidebar"] .st-key-login button *{color:#FFFFFF !important;}
section[data-testid="stSidebar"] .st-key-login button:hover{background:#1A1A1A !important;}

/* ── Main content ── */
.main .block-container{
    padding-top:68px !important;max-width:100% !important;
    padding-left:1.5rem !important;padding-right:1.5rem !important;}

/* ── Componentes gerais ── */
.stButton>button{background:#FFFFFF !important;color:#000000 !important;border:1px solid #D4D4D4 !important;
    border-radius:8px !important;font-weight:600 !important;font-size:0.82rem !important;}
.stButton>button *{color:#000000 !important;}
.stButton>button:hover{border-color:#000000 !important;background:#FAFAFA !important;}
.stButton>button[kind="primary"],.stButton>button[data-testid="stBaseButton-primary"],
.stFormSubmitButton>button{background:#000000 !important;border-color:#000000 !important;}
.stButton>button[kind="primary"] *,.stButton>button[data-testid="stBaseButton-primary"] *,.stFormSubmitButton>button *{color:#FFFFFF !important;}
.stButton>button[kind="primary"]:hover,.stButton>button[data-testid="stBaseButton-primary"]:hover{background:#1A1A1A !important;border-color:#C9A227 !important;}
.stButton>button:focus-visible{outline:2px solid #C9A227 !important;outline-offset:2px !important;}
.stTabs [data-baseweb="tab-list"]{background:transparent;border-radius:0;padding:0;gap:4px;border-bottom:1px solid #E5E5E5;}
.stTabs [data-baseweb="tab"]{border-radius:0 !important;color:#5C5C5C !important;padding:8px 14px !important;font-size:0.82rem !important;font-weight:600 !important;background:transparent !important;}
.stTabs [aria-selected="true"]{background:transparent !important;color:#000000 !important;box-shadow:inset 0 -2px 0 #C9A227 !important;}
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none !important;}
.stSelectbox>div>div,.stTextInput>div>div>input,.stTextArea>div>div>textarea{background:#FFFFFF !important;border:1px solid #D4D4D4 !important;border-radius:6px !important;color:#000000 !important;}
.stTextInput>div>div>input:focus,.stTextArea>div>div>textarea:focus{border-color:#000000 !important;box-shadow:0 0 0 1px #000000 !important;}
.stDataFrame{background:#FFFFFF !important;border:1px solid #E5E5E5 !important;border-radius:8px !important;}
[data-testid="stExpander"]{background:#FFFFFF !important;border:1px solid #E5E5E5 !important;border-radius:8px !important;}
[data-testid="stMetricValue"]{font-variant-numeric:tabular-nums;}
div[data-testid="stVerticalBlock"]{gap:0.4rem !important;}

/* ── Home: atalhos ── */
.atalho-btn .stButton>button{
    background:#FFFFFF !important;color:#000000 !important;
    border:1px solid #E5E5E5 !important;border-top:none !important;
    border-radius:0 0 8px 8px !important;
    font-weight:600 !important;font-size:0.73rem !important;
    padding:6px 12px !important;text-align:center !important;
    justify-content:center !important;width:100% !important;
    box-shadow:none !important;}
.atalho-btn .stButton>button *{color:#000000 !important;}
.atalho-btn .stButton>button:hover{background:#F5F5F5 !important;}

/* ── Ocultar widgets nativos Streamlit Cloud ── */
[data-testid="stStatusWidget"],
.st-emotion-cache-zq5wmm,
.stChatFloatingInputContainer,
[data-testid="chatAvatarIcon-assistant"]{display:none !important;}

/* ── Journey cards ── */
.nav-card-btn{display:none !important;}

/* ── Botões de navegação ocultos da topbar ── */
div[data-testid="stHorizontalBlock"].topbar-nav-row,
.topbar-nav-row{display:none !important;position:absolute !important;left:-9999px !important;}

/* ── Botões JS-bridge ocultos (govnav-*) ──
   O atributo data-govnav-wrap é injetado pelo JS (tagNavBtns) assim que
   os elementos entram no DOM — antes do primeiro paint graças ao
   MutationObserver síncrono.  O CSS garante ocultação mesmo se o JS
   demorar um ciclo extra.
*/
[class*="st-key-topnav-"],
[data-govnav-wrap]{
    display:none !important;
    position:absolute !important;
    left:-9999px !important;
    width:0 !important;height:0 !important;
    overflow:hidden !important;
    pointer-events:none !important;}
button[data-gov-nav],
div[data-testid="stButton"]:has(button[data-gov-nav]){
    display:none !important;
    position:absolute !important;
    left:-9999px !important;}


/* ══════════════════════════════════════════
   MOBILE  ≤ 768 px
   ══════════════════════════════════════════ */
@media (max-width:768px){

  /* Topbar: compacta, esconde jornadas e busca */
  .gov-topbar{
    height:48px !important;
    padding:0 14px !important;
    gap:10px !important;}
  .gov-topbar .topbar-jornadas,
  .gov-topbar .topbar-busca{display:none !important;}
  .gov-topbar .topbar-logo{min-width:0 !important;}

  /* Main: compensa topbar menor, sem rolagem horizontal */
  .main .block-container{
    padding-top:60px !important;
    padding-left:0.75rem !important;
    padding-right:0.75rem !important;
    overflow-x:hidden !important;}

  /* Impede rolagem horizontal global */
  html,body{overflow-x:hidden !important;max-width:100vw !important;}

  /* Sidebar: overlay nativo do Streamlit */
  section[data-testid="stSidebar"]{
    margin-top:0 !important;
    min-width:0 !important;}

  /* Atalhos: 2 colunas no mobile */
  .atalhos-grid{
    display:grid !important;
    grid-template-columns:1fr 1fr !important;
    gap:10px !important;}

  /* Jornadas inferiores: 1 coluna (empilhadas) */
  .jornadas-grid{
    display:grid !important;
    grid-template-columns:1fr !important;
    gap:8px !important;}

  /* KPI panorama: 1 coluna */
  .kpi-panorama{
    display:grid !important;
    grid-template-columns:1fr !important;
    gap:10px !important;}

  /* Banner: empilha, esconde card de missão */
  .banner-missao{display:none !important;}
  .banner-inner{
    flex-direction:column !important;
    gap:16px !important;
    padding:20px 16px 18px !important;}

  /* Tabelas: rolagem horizontal contida na região */
  .stDataFrame,[data-testid="stDataFrame"]{
    overflow-x:auto !important;
    max-width:100% !important;}
  .stDataFrame table{min-width:0 !important;font-size:0.72rem !important;}

  /* Gráficos Plotly: ocupam largura toda */
  .stPlotlyChart{width:100% !important;overflow-x:hidden !important;}

  /* Tabs: fonte e padding menores */
  .stTabs [data-baseweb="tab"]{
    padding:5px 8px !important;
    font-size:0.72rem !important;}
  .stTabs [data-baseweb="tab-list"]{
    flex-wrap:wrap !important;gap:4px !important;}

  /* Textos */
  h1{font-size:1.05rem !important;}
  h2{font-size:0.9rem !important;}

  /* Formulários: campos full-width */
  .stTextInput>div>div>input,
  .stSelectbox>div>div,
  .stTextArea>div>div>textarea{
    font-size:16px !important;}  /* evita zoom automático iOS */

  /* Badge DEMO: menor no mobile */
  .demo-badge{bottom:60px !important;right:8px !important;}

  /* Colunas Streamlit: forçar empilhamento em telas muito estreitas */
  /* (regra movida para root level — CSS não suporta @media aninhado) */
}

/* ══════════════════════════════════════════
   MOBILE EXTRA-ESTREITO  ≤ 480 px
   ══════════════════════════════════════════ */
@media (max-width:480px){
  [data-testid="column"]{min-width:100% !important;flex:1 1 100% !important;}
}

/* ══════════════════════════════════════════
   TABLET  769 – 1024 px
   ══════════════════════════════════════════ */
@media (min-width:769px) and (max-width:1024px){
  .gov-topbar .topbar-busca{max-width:200px !important;}
  .main .block-container{
    padding-left:1rem !important;
    padding-right:1rem !important;}
  .atalhos-grid{
    grid-template-columns:repeat(3,1fr) !important;}
  .jornadas-grid{
    grid-template-columns:repeat(3,1fr) !important;}
}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM — tokens, ícones e layout (identidade Governantes)
# Cores institucionais: preto #000000 · branco #FFFFFF · dourado #C9A227
# Cinzas neutros apenas para superfícies, linhas e texto secundário.
# ════════════════════════════════════════════════════════════════════
TK = {
    "gold": "#C9A227", "black": "#000000", "white": "#FFFFFF",
    "bg": "#FAFAFA", "surface": "#F5F5F5", "line": "#EAEAEA",
    "ink": "#000000", "ink2": "#5C5C5C", "ink3": "#8A8A8A",
    "ok": "#1E7F4F", "warn": "#B26A00", "err": "#C62828",
}
SIDEBAR_W = 260

# Ícones de traço (24×24), consistentes em toda a interface
_ICON_PATHS = {
    "database": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
    "layers": '<path d="M12 3 2 8l10 5 10-5-10-5z"/><path d="m2 13 10 5 10-5"/><path d="m2 17.5 10 5 10-5"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
    "book": '<path d="M2 4h6a4 4 0 0 1 4 4v13a3 3 0 0 0-3-3H2z"/><path d="M22 4h-6a4 4 0 0 0-4 4v13a3 3 0 0 1 3-3h7z"/>',
    "network": '<circle cx="12" cy="12" r="2.5"/><circle cx="4.5" cy="4.5" r="2"/><circle cx="19.5" cy="4.5" r="2"/><circle cx="4.5" cy="19.5" r="2"/><circle cx="19.5" cy="19.5" r="2"/><path d="m6 6 4.3 4.3M18 6l-4.3 4.3M6 18l4.3-4.3M18 18l-4.3-4.3"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "trend": '<path d="m3 17 6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    "check": '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="m8 12 3 3 5-6"/>',
    "inbox": '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.5 5h13L22 12v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-6z"/>',
    "award": '<circle cx="12" cy="8" r="6"/><path d="M8.2 13.2 7 22l5-3 5 3-1.2-8.8"/>',
    "bolt": '<path d="M13 2 3 14h9l-1 8 10-12h-9z"/>',
    "chevron": '<path d="m9 6 6 6-6 6"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "edit": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "box": '<path d="M21 8 12 3 3 8v8l9 5 9-5z"/><path d="m3 8 9 5 9-5M12 13v8"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    "users": '<circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0"/><path d="M17 4.5a4 4 0 0 1 0 7"/><path d="M22 21a7 7 0 0 0-4-6.3"/>',
}


def icon(nome, size=20, cor=TK["gold"], sw=1.8):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{cor}" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            f'{_ICON_PATHS[nome]}</svg>')


LOGO_SVG = """<svg width="{s}" height="{s}" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="Governantes">
  <circle cx="20" cy="20" r="19" stroke="#C9A227" stroke-width="1.6" fill="{bg}"/>
  <circle cx="20" cy="20" r="15.8" stroke="#C9A227" stroke-width="0.8" fill="none"/>
  <text x="20" y="22.5" text-anchor="middle" font-family="Georgia,'Times New Roman',serif" font-size="15" font-weight="bold" fill="#C9A227">G</text>
  <circle cx="15.5" cy="27.5" r="1.6" fill="#C9A227"/><path d="M13.3 32.5 Q15.5 29.8 17.7 32.5" stroke="#C9A227" stroke-width="1.3" fill="#C9A227"/>
  <circle cx="20" cy="27" r="1.9" fill="#C9A227"/><path d="M17.4 32.8 Q20 29.4 22.6 32.8" stroke="#C9A227" stroke-width="1.3" fill="#C9A227"/>
  <circle cx="24.5" cy="27.5" r="1.6" fill="#C9A227"/><path d="M22.3 32.5 Q24.5 29.8 26.7 32.5" stroke="#C9A227" stroke-width="1.3" fill="#C9A227"/>
</svg>"""


def card_link(key, html, destino):
    """Card HTML inteiro clicável: um st.button nativo cobre a área do card."""
    with st.container(key=f"lnk_{key}"):
        st.markdown(html, unsafe_allow_html=True)
        if st.button(" ", key=f"lnkbtn_{key}", use_container_width=True):
            st.session_state["pagina"] = destino
            st.rerun()


st.markdown(f"""
<style>
:root{{
  --gv-gold:{TK['gold']};--gv-black:{TK['black']};--gv-white:{TK['white']};
  --gv-bg:{TK['bg']};--gv-surface:{TK['surface']};--gv-line:{TK['line']};
  --gv-ink:{TK['ink']};--gv-ink2:{TK['ink2']};--gv-ink3:{TK['ink3']};
  --gv-radius:12px;--gv-shadow:0 1px 2px rgba(0,0,0,0.04),0 4px 16px rgba(0,0,0,0.05);
  --gv-sidebar:{SIDEBAR_W}px;
}}
html,body,.stApp{{background:var(--gv-bg) !important;}}

/* ── Menu lateral preto ── */
section[data-testid="stSidebar"]{{
  background:var(--gv-black) !important;border-right:none !important;
  margin-top:0 !important;z-index:1000001 !important;
  width:var(--gv-sidebar) !important;min-width:var(--gv-sidebar) !important;max-width:var(--gv-sidebar) !important;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='260' height='220' viewBox='0 0 260 220'%3E%3Cg fill='none' stroke='%23C9A227' stroke-linecap='round'%3E%3Cpath d='M-10 200 C60 150 120 210 270 110' stroke-opacity='.55' stroke-width='1.2'/%3E%3Cpath d='M-10 212 C70 165 130 222 270 126' stroke-opacity='.3'/%3E%3Cpath d='M-10 222 C80 180 140 232 270 142' stroke-opacity='.18'/%3E%3C/g%3E%3C/svg%3E") !important;
  background-repeat:no-repeat !important;background-position:left bottom !important;}}
section[data-testid="stSidebar"] > div{{background:transparent !important;}}
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"]{{padding:0 14px 24px !important;}}
section[data-testid="stSidebar"] > div::-webkit-scrollbar-track{{background:var(--gv-black);}}
section[data-testid="stSidebar"] > div::-webkit-scrollbar-thumb{{background:#2E2E2E;}}
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"]{{height:8px !important;min-height:0 !important;padding:0 !important;}}
section[data-testid="stSidebar"] *{{color:#FFFFFF !important;}}
section[data-testid="stSidebar"] .gv-nav-label{{color:#8A8A8A !important;font-size:0.6rem;font-weight:700;letter-spacing:1.6px;
  text-transform:uppercase;padding:14px 14px 6px;}}
section[data-testid="stSidebar"] .stButton>button{{
  background:transparent !important;border:none !important;border-radius:8px !important;
  padding:9px 14px !important;min-height:40px !important;font-weight:500 !important;font-size:0.86rem !important;}}
section[data-testid="stSidebar"] .stButton>button *{{color:#FFFFFF !important;}}
section[data-testid="stSidebar"] .stButton>button p{{font-size:0.86rem !important;white-space:nowrap !important;overflow:hidden;text-overflow:ellipsis;}}
[data-testid="stToolbarActions"],[data-testid="stMainMenu"],[data-testid="stAppDeployButton"]{{display:none !important;}}
header[data-testid="stHeader"]{{pointer-events:none !important;}}
header[data-testid="stHeader"] [data-testid="stExpandSidebarButton"],header[data-testid="stHeader"] [data-testid="collapsedControl"]{{pointer-events:auto !important;}}
section[data-testid="stSidebar"] .stButton>button [data-testid="stIconMaterial"]{{font-size:1.2rem !important;margin-right:6px !important;}}
section[data-testid="stSidebar"] .stButton>button:hover{{background:#1A1A1A !important;}}
section[data-testid="stSidebar"] .stButton>button[kind="primary"],
section[data-testid="stSidebar"] .stButton>button[data-testid="stBaseButton-primary"]{{
  background:var(--gv-gold) !important;font-weight:600 !important;}}
section[data-testid="stSidebar"] .stButton>button[kind="primary"] *,
section[data-testid="stSidebar"] .stButton>button[data-testid="stBaseButton-primary"] *{{color:#000000 !important;}}
section[data-testid="stSidebar"] .stSelectbox>div>div{{background:#141414 !important;border:1px solid #2E2E2E !important;}}
section[data-testid="stSidebar"] .stSelectbox *{{color:#FFFFFF !important;}}
section[data-testid="stSidebar"] .st-key-login button{{background:var(--gv-gold) !important;}}
section[data-testid="stSidebar"] .st-key-login button *{{color:#000000 !important;}}
section[data-testid="stSidebar"] .st-key-login button:hover{{background:#D8B23A !important;}}
section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] *{{color:#FFFFFF !important;}}

/* ── Cabeçalho branco ── */
.gov-topbar{{left:0 !important;height:64px !important;background:#FFFFFF !important;
  border-bottom:1px solid var(--gv-line) !important;box-shadow:none !important;padding:0 24px !important;}}
.stApp:has(section[data-testid="stSidebar"][aria-expanded="true"]) .gov-topbar{{left:var(--gv-sidebar) !important;}}
.gov-topbar .gv-sep{{width:1px;height:28px;background:var(--gv-line);}}
.main .block-container,[data-testid="stMainBlockContainer"]{{padding-top:88px !important;
  padding-left:2rem !important;padding-right:2rem !important;max-width:1480px !important;}}
[data-testid="stExpandSidebarButton"],[data-testid="collapsedControl"]{{top:14px !important;left:14px !important;
  background:#FFFFFF !important;border:1px solid var(--gv-line) !important;}}
/* Busca, notificações e perfil: widgets nativos posicionados no cabeçalho */
.st-key-tb_busca{{position:fixed !important;top:12px;right:300px;width:min(420px,34vw) !important;z-index:100000 !important;}}
.st-key-tb_busca .stTextInput input,.st-key-tb_busca input{{height:40px !important;border-radius:10px !important;border:1px solid #DADADA !important;
  background:#FFFFFF url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%235C5C5C' stroke-width='2' stroke-linecap='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='m20 20-3.5-3.5'/%3E%3C/svg%3E") no-repeat 12px center !important;
  padding-left:40px !important;font-size:0.86rem !important;}}
.st-key-tb_busca [data-testid="InputInstructions"]{{display:none !important;}}
.st-key-tb_notif{{position:fixed !important;top:12px;right:236px;width:44px !important;z-index:100000 !important;}}
.st-key-tb_notif button{{background:transparent !important;border:none !important;height:40px !important;width:44px !important;padding:0 !important;}}
.st-key-tb_notif button *{{color:#000000 !important;font-size:1.35rem !important;}}
.st-key-tb_notif button:hover{{background:var(--gv-surface) !important;}}
.st-key-tb_notif .gv-dot{{position:absolute;top:6px;right:8px;min-width:9px;height:9px;border-radius:99px;background:var(--gv-gold);
  border:2px solid #FFFFFF;pointer-events:none;z-index:2;}}
.st-key-tb_perfil{{position:fixed !important;top:12px;right:24px;width:196px !important;z-index:100000 !important;}}
.st-key-tb_perfil button{{background:transparent !important;border:none !important;height:40px !important;
  justify-content:flex-start !important;padding:0 6px !important;}}
.st-key-tb_perfil button *{{color:#000000 !important;font-weight:600 !important;}}
.st-key-tb_perfil button:hover{{background:var(--gv-surface) !important;}}
.st-key-tb_perfil .gv-avatar{{position:absolute;left:6px;top:4px;width:32px;height:32px;border-radius:50%;background:var(--gv-gold);
  color:#000;font-weight:700;font-size:0.75rem;display:flex;align-items:center;justify-content:center;pointer-events:none;z-index:2;}}
.st-key-tb_perfil button p{{padding-left:40px !important;}}

/* ── Componentes ── */
.st-key-pnl_evol,.st-key-pnl_ativ,.st-key-pnl_qa,.st-key-pnl_status{{background:#FFFFFF;border:1px solid var(--gv-line);
  border-radius:var(--gv-radius);box-shadow:var(--gv-shadow);padding:18px 20px 12px;gap:0 !important;}}
.st-key-pnl_evol,.st-key-pnl_ativ{{min-height:300px;}}
.gv-card{{background:#FFFFFF;border:1px solid var(--gv-line);border-radius:var(--gv-radius);box-shadow:var(--gv-shadow);}}
.gv-panel{{padding:18px 20px;height:100%;}}
.gv-panel-title{{display:flex;align-items:center;gap:10px;font-weight:650;font-size:0.98rem;color:#000;margin-bottom:14px;}}
.gv-kpi{{padding:18px 20px 16px;}}
.gv-kpi-val{{font-size:1.9rem;font-weight:700;letter-spacing:-0.02em;color:#000;line-height:1.1;margin-top:10px;font-variant-numeric:tabular-nums;}}
.gv-kpi-lbl{{font-size:0.85rem;color:var(--gv-ink2);margin-top:4px;}}
.gv-kpi-note{{font-size:0.72rem;color:var(--gv-ink3);margin-top:8px;}}
.gv-bar{{display:grid;grid-template-columns:96px 1fr 46px;align-items:center;gap:12px;margin:10px 0;font-size:0.84rem;}}
.gv-bar-track{{height:10px;background:#EFEFEF;border-radius:99px;overflow:hidden;}}
.gv-bar-fill{{height:100%;background:var(--gv-gold);border-radius:99px;}}
.gv-row{{display:flex;align-items:center;gap:12px;padding:11px 2px;border-bottom:1px solid #F0F0F0;font-size:0.86rem;color:#000;}}
.gv-pill{{margin-left:auto;background:#C9A2271F;color:#000;font-weight:650;font-size:0.75rem;border-radius:8px;padding:2px 9px;min-width:28px;text-align:center;}}
.gv-qa{{padding:14px 14px 12px;min-height:118px;display:flex;flex-direction:column;justify-content:space-between;transition:box-shadow .15s,border-color .15s;}}
.gv-qa-t{{font-weight:650;font-size:0.9rem;color:#000;line-height:1.25;display:flex;justify-content:space-between;align-items:flex-end;gap:6px;}}
.gv-qa-d{{font-size:0.72rem;color:var(--gv-ink2);margin-top:4px;line-height:1.35;}}
/* Cards clicáveis: o botão nativo cobre o card */
[class*="st-key-lnk_"]{{position:relative !important;gap:0 !important;}}
[class*="st-key-lnk_"] [data-testid="stButton"],[class*="st-key-lnk_"] .stButton{{position:absolute !important;inset:0 !important;z-index:3 !important;}}
[class*="st-key-lnk_"] .stButton>button{{width:100% !important;height:100% !important;opacity:0 !important;cursor:pointer !important;}}
[class*="st-key-lnk_"]:hover .gv-card{{border-color:#D6D6D6;box-shadow:0 2px 4px rgba(0,0,0,0.05),0 10px 24px rgba(0,0,0,0.07);}}
[class*="st-key-lnk_"] .stButton>button:focus-visible{{opacity:1 !important;background:transparent !important;outline:2px solid var(--gv-gold) !important;}}

/* ── Boas-vindas ── */
.gv-hero{{display:grid;grid-template-columns:minmax(0,1fr) 400px;gap:8px;align-items:start;margin-bottom:10px;}}
.gv-hero h1.gv-h{{font-family:'Inter',sans-serif !important;font-size:clamp(1.6rem,2.6vw,2.35rem) !important;font-weight:750 !important;
  letter-spacing:-0.025em !important;line-height:1.1 !important;margin:6px 0 8px !important;padding:0 !important;color:#000 !important;}}
.gv-hero .gv-sub{{font-size:1rem;color:#1A1A1A;margin-bottom:26px;}}
.gv-kpis{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;}}
.gv-art{{position:relative;margin:-24px -8px -10px 0;}}
.gv-art svg{{width:100%;height:100%;}}

/* ── Área de IA ── */
.gv-ai{{background:radial-gradient(120% 140% at 85% 50%,#2A2205 0%,#0B0B0B 46%,#000 100%);border-radius:var(--gv-radius);
  padding:22px 24px;position:relative;overflow:hidden;min-height:184px;box-shadow:var(--gv-shadow);}}
.gv-ai h3{{font-family:'Inter',sans-serif !important;color:#FFFFFF !important;font-size:1.25rem !important;font-weight:700 !important;
  line-height:1.2 !important;margin:0 0 8px !important;padding:0 !important;max-width:62%;}}
.gv-ai p{{color:#E6E6E6 !important;font-size:0.82rem;line-height:1.45;max-width:60%;margin:0 0 14px;}}
.gv-ai .gv-ai-art{{position:absolute;right:8px;top:50%;transform:translateY(-50%);width:42%;max-width:220px;}}
.gv-ai .gv-ai-cta{{display:inline-flex;align-items:center;gap:8px;background:var(--gv-gold);color:#000;font-weight:650;
  font-size:0.82rem;border-radius:8px;padding:9px 14px;}}
.gv-ai .gv-ai-note{{display:inline-block;color:#BFBFBF !important;font-size:0.74rem;border:1px solid #333;border-radius:8px;padding:7px 12px;}}

/* ── Página pública (antes do login) ── */
.gv-pub{{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,0.95fr);gap:24px;align-items:center;padding:8px 0 4px;}}
.gv-pub-marca{{display:flex;align-items:center;gap:10px;font-size:0.72rem;font-weight:650;letter-spacing:0.22em;color:#000;text-transform:uppercase;}}
.gv-pub-marca span{{height:1px;width:28px;background:var(--gv-gold);}}
.gv-pub-cat{{font-size:0.74rem;font-weight:600;letter-spacing:0.16em;color:#8C6F12;text-transform:uppercase;margin:14px 0 10px;}}
.gv-pub h1.gv-pub-h{{font-family:'Inter',sans-serif !important;font-size:clamp(1.9rem,3.4vw,3.05rem) !important;font-weight:760 !important;
  letter-spacing:-0.03em !important;line-height:1.05 !important;margin:0 0 18px !important;padding:0 !important;color:#000 !important;text-transform:uppercase;}}
.gv-pub h1.gv-pub-h em{{font-style:normal;color:var(--gv-gold);}}
.gv-pub-txt{{font-size:1.02rem;line-height:1.6;color:#1A1A1A;max-width:560px;margin:0 0 10px;}}
.gv-pub-comp{{font-size:0.9rem;line-height:1.6;color:var(--gv-ink2);max-width:560px;margin:0;}}
.gv-pub-art svg{{width:100%;height:auto;max-height:420px;}}
.gv-pilares{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin:30px 0 10px;}}
.gv-pilar{{background:#FFFFFF;border:1px solid var(--gv-line);border-radius:var(--gv-radius);padding:20px 20px 18px;position:relative;
  box-shadow:0 1px 2px rgba(0,0,0,0.04);transition:border-color .2s ease,transform .2s ease;}}
.gv-pilar:hover{{border-color:#D9C27A;transform:translateY(-2px);}}
.gv-pilar::before{{content:"";position:absolute;left:20px;top:0;width:28px;height:2px;background:var(--gv-gold);}}
.gv-pilar-n{{font-size:0.78rem;font-weight:650;color:#8C6F12;letter-spacing:0.08em;font-variant-numeric:tabular-nums;}}
.gv-pilar h3{{font-family:'Inter',sans-serif !important;font-size:1rem !important;font-weight:720 !important;letter-spacing:0.08em !important;
  text-transform:uppercase;margin:8px 0 8px !important;padding:0 !important;color:#000 !important;}}
.gv-pilar p{{font-size:0.86rem;line-height:1.5;color:var(--gv-ink2);margin:0;}}
.gv-pub-rodape{{font-size:0.74rem;color:var(--gv-ink3);margin-top:18px;}}
.st-key-pub_entrar{{margin-top:22px;}}
.st-key-pub_acesso .gv-nav-label{{color:var(--gv-ink2) !important;font-size:0.72rem;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;
  margin:0 0 10px !important;padding:0 !important;line-height:1.3;}}
.st-key-pub_entrar button{{background:#000 !important;border:1px solid #000 !important;border-radius:10px !important;padding:12px 26px !important;
  min-height:50px !important;transition:background .2s ease;}}
.st-key-pub_entrar button *{{color:#FFFFFF !important;font-weight:650 !important;letter-spacing:0.08em !important;}}
.st-key-pub_entrar button:hover{{background:#1A1A1A !important;}}
.st-key-pub_entrar button:hover span[data-testid="stIconMaterial"]{{color:var(--gv-gold) !important;}}
.st-key-pub_acesso{{background:#FFFFFF;border:1px solid var(--gv-line);border-radius:var(--gv-radius);padding:18px 20px;max-width:440px;
  box-shadow:0 1px 2px rgba(0,0,0,0.04),0 8px 24px rgba(0,0,0,0.05);}}
.st-key-pub_acesso .st-key-login_pub button{{background:var(--gv-gold) !important;border:none !important;}}
.st-key-pub_acesso .st-key-login_pub button *{{color:#000 !important;font-weight:650 !important;}}

/* ── Responsividade ── */
@media (max-width:1180px){{
  .gv-hero{{grid-template-columns:1fr;}} .gv-art{{display:none;}}
  .st-key-tb_busca{{right:270px;width:min(300px,30vw) !important;}}
}}
@media (max-width:1024px){{ .gv-kpis,.gv-pilares{{grid-template-columns:repeat(2,minmax(0,1fr));}} }}
@media (max-width:900px){{ .gv-pub{{grid-template-columns:1fr;}} .gv-pub-art{{max-width:380px;margin:0 auto;}} }}
@media (max-width:768px){{
  .gov-topbar,.stApp:has(section[data-testid="stSidebar"][aria-expanded="true"]) .gov-topbar{{left:0 !important;height:56px !important;}}
  .main .block-container,[data-testid="stMainBlockContainer"]{{padding-top:72px !important;padding-left:0.9rem !important;padding-right:0.9rem !important;}}
  .st-key-tb_busca{{top:8px;left:62px;right:116px;width:auto !important;}}
  .st-key-tb_notif{{top:8px;right:62px;}}
  .st-key-tb_perfil{{top:8px;right:10px;width:48px !important;}}
  .st-key-tb_perfil button p{{display:none !important;}}
  [data-testid="stExpandSidebarButton"],[data-testid="collapsedControl"]{{top:10px !important;left:10px !important;}}
  .gv-kpis{{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;}}
  .gv-kpi{{padding:14px;}} .gv-kpi-val{{font-size:1.45rem;}}
  .gv-ai h3,.gv-ai p{{max-width:100%;}} .gv-ai .gv-ai-art{{opacity:.25;}}
  .gv-bar{{grid-template-columns:80px 1fr 42px;}}
  .gv-pilares{{grid-template-columns:1fr;gap:10px;}} .gv-pub-art{{max-width:230px;}}
}}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# CONEXÃO
# ════════════════════════════════════════════════════════════════════
@st.cache_resource
def get_conn():
    conn = sql.connect(
        server_hostname      = st.secrets["DATABRICKS_HOST"],
        http_path            = st.secrets["DATABRICKS_HTTP_PATH"],
        access_token         = st.secrets["DATABRICKS_TOKEN"],
        catalog              = "workspace",
        schema               = "meridian_governanca",
        socket_timeout_seconds = 12,   # falha rápida — não trava mobile
        _connection_timeout  = 15,
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

def _is_limit_err(msg: str) -> bool:
    return "free daily limit" in msg or "BAD_REQUEST" in msg or "daily limit" in msg.lower()

@st.cache_data(ttl=300)
def qry(sql_str):
    cur = None
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute(sql_str)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        return pd.DataFrame(rows, columns=cols), None
    except Exception as e:
        err = str(e)
        if _is_session_err(err):
            try: get_conn.clear(); qry.clear()
            except: pass
        if _is_limit_err(err):
            st.session_state["_db_limit"] = True
        st.session_state["_db_err"] = err
        return pd.DataFrame(), err
    finally:
        if cur is not None:
            try: cur.close()
            except: pass

def exe(sql_str):
    cur = None
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
    finally:
        if cur is not None:
            try: cur.close()
            except: pass

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
PERFIL_COR   = {"consultante":"#1A1A1A","curador":"#000000","aprovador":"#1E7F4F"}
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
    df, err = qry("SELECT * FROM meridian_governanca.linhagem_ativos ORDER BY origem_schema, origem_tabela")
    return (df if df is not None else pd.DataFrame()), err

@st.cache_data(ttl=300)
def load_solicitacoes_qualidade():
    df,_ = qry("SELECT * FROM meridian_governanca.solicitacoes_qualidade ORDER BY criado_em DESC")
    return df if df is not None else pd.DataFrame()

# ════════════════════════════════════════════════════════════════════
# COMPONENTES REUTILIZÁVEIS
# ════════════════════════════════════════════════════════════════════
_EMOJI_ICON = {"📖": "book", "📋": "database", "🗂️": "database", "🏛️": "layers", "🛡️": "shield", "🏆": "shield",
               "⚡": "inbox", "📬": "inbox", "✏️": "edit", "🕐": "clock", "📊": "chart", "🥇": "award",
               "🔗": "network", "📦": "box", "🔍": "search"}


def page_header(icone, titulo, subtitulo=""):
    ic = _EMOJI_ICON.get(icone)
    simbolo = icon(ic, 24) if ic else f'<span style="font-size:1.2rem;">{icone}</span>'
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:14px;margin:2px 0 18px;">
        <div style="width:46px;height:46px;border-radius:12px;background:#FFFFFF;border:1px solid #EAEAEA;
                    box-shadow:0 1px 2px rgba(0,0,0,0.04);display:flex;align-items:center;justify-content:center;flex-shrink:0;">{simbolo}</div>
        <div style="min-width:0;">
            <div style="color:#000000;font-size:1.45rem;font-weight:700;letter-spacing:-0.02em;line-height:1.2;">{titulo}</div>
            {f'<div style="color:#5C5C5C;font-size:0.86rem;margin-top:2px;">{subtitulo}</div>' if subtitulo else ''}
        </div>
    </div>""", unsafe_allow_html=True)

def kpi(valor, label, cor="#C9A227", icone="", tooltip=""):
    tip = f'title="{tooltip}"' if tooltip else ""
    ic = _EMOJI_ICON.get(str(icone).strip())
    simbolo = icon(ic, 18, "#000000", 1.7) if ic else (f'<span>{icone}</span>' if icone else "")
    return f"""<div {tip} class="gv-card" style="padding:16px 18px;cursor:help;height:100%;">
        <div style="display:flex;align-items:center;gap:8px;font-size:0.8rem;color:#5C5C5C;margin-bottom:8px;">
            <span style="width:8px;height:8px;border-radius:50%;background:{cor};flex-shrink:0;"></span>{simbolo}<span>{label}</span></div>
        <div style="font-size:1.65rem;font-weight:700;letter-spacing:-0.02em;color:#000000;font-variant-numeric:tabular-nums;">{valor}</div>
    </div>"""

def section_divider(titulo):
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin:22px 0 12px;">
        <span style="color:#000000;font-size:0.8rem;font-weight:650;text-transform:uppercase;letter-spacing:1.2px;white-space:nowrap;">{titulo}</span>
        <div style="height:1px;background:#EAEAEA;flex:1;"></div>
    </div>""", unsafe_allow_html=True)

def avatar(nome, cor="#C9A227", size=36):
    iniciais = "".join([p[0].upper() for p in nome.split()[:2]])
    return f"""<div style="width:{size}px;height:{size}px;border-radius:50%;
        background:{cor}22;border:2px solid {cor}44;flex-shrink:0;
        display:inline-flex;align-items:center;justify-content:center;
        color:{cor};font-weight:800;font-size:{size//3}px;">{iniciais}</div>"""

def estado_vazio(icone, titulo, descricao):
    st.markdown(f"""
    <div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:12px;
                padding:40px;text-align:center;">
        <div style="font-size:2.5rem;margin-bottom:10px;">{icone}</div>
        <div style="color:#000000;font-weight:700;margin-bottom:6px;">{titulo}</div>
        <div style="color:#5C5C5C;font-size:0.82rem;">{descricao}</div>
    </div>""", unsafe_allow_html=True)

def copyright_footer():
    st.markdown("""
    <div style="border-top:1px solid #E5E5E5;padding:12px 0;margin-top:32px;text-align:center;">
        <div style="color:#5C5C5C;font-size:0.65rem;line-height:1.6;">
            © Plataforma de Governança de Dados — Concepção, arquitetura,
            funcionalidades, regras e estratégias são de propriedade intelectual de
            <span style="color:#000000;font-weight:600;">Tereza Cristina</span>.<br>
            Reprodução, cópia ou adaptação proibidas sem autorização expressa da autora.
        </div>
    </div>""", unsafe_allow_html=True)

# ── Ilustrações vetoriais (leves, sem imagens externas) ──────────────
def _iso_cubo(x, y, w, h, topo, esq, dir_, traco="#E9C766", op=1):
    t = f"{x},{y} {x+w},{y+w/2} {x},{y+w} {x-w},{y+w/2}"
    l = f"{x-w},{y+w/2} {x},{y+w} {x},{y+w+h} {x-w},{y+w/2+h}"
    r = f"{x},{y+w} {x+w},{y+w/2} {x+w},{y+w/2+h} {x},{y+w+h}"
    return (f'<g opacity="{op}"><polygon points="{l}" fill="url(#{esq})" stroke="{traco}" stroke-width="0.8"/>'
            f'<polygon points="{r}" fill="url(#{dir_})" stroke="{traco}" stroke-width="0.8"/>'
            f'<polygon points="{t}" fill="url(#{topo})" stroke="#FFF3C4" stroke-width="0.9"/></g>')


def _painel(x, y, w, h, conteudo, rot=-6):
    return (f'<g transform="translate({x},{y}) skewY({rot})">'
            f'<rect width="{w}" height="{h}" rx="9" fill="url(#gvGlass)" stroke="#E2C25A" stroke-opacity=".75"/>'
            f'<g transform="translate({w/2-14},{h/2-14})" fill="none" stroke="#C9A227" stroke-width="2.2" '
            f'stroke-linecap="round" stroke-linejoin="round">{conteudo}</g></g>')


_ondas = "".join(
    f'<path d="M-20 {268+i*7} C 90 {214+i*9}, 200 {320-i*4}, 420 {214+i*8}" fill="none" stroke="#C9A227" '
    f'stroke-opacity="{0.55-i*0.06:.2f}" stroke-width="1.1" stroke-dasharray="1.2 4.5" stroke-linecap="round"/>'
    for i in range(8))

HERO_ART_SVG = f"""<svg viewBox="0 0 400 330" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Ilustração de dados conectados">
<defs>
  <linearGradient id="gvTop" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFF6D6"/><stop offset="1" stop-color="#F0CF66"/></linearGradient>
  <linearGradient id="gvLeft" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F4D77A" stop-opacity=".95"/><stop offset="1" stop-color="#C9A227" stop-opacity=".85"/></linearGradient>
  <linearGradient id="gvRight" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E7BD3F" stop-opacity=".9"/><stop offset="1" stop-color="#9C7A12" stop-opacity=".9"/></linearGradient>
  <linearGradient id="gvSlabT" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#EDEDED"/></linearGradient>
  <linearGradient id="gvSlabL" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E6E6E6"/><stop offset="1" stop-color="#CFCFCF"/></linearGradient>
  <linearGradient id="gvSlabR" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#D6D6D6"/><stop offset="1" stop-color="#BDBDBD"/></linearGradient>
  <linearGradient id="gvGlass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFFFFF" stop-opacity=".95"/><stop offset="1" stop-color="#FBF3DA" stop-opacity=".75"/></linearGradient>
  <radialGradient id="gvHalo" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#C9A227" stop-opacity=".35"/><stop offset="1" stop-color="#C9A227" stop-opacity="0"/></radialGradient>
  <filter id="gvBlur"><feGaussianBlur stdDeviation="2.2"/></filter>
</defs>
{_ondas}
<ellipse cx="205" cy="190" rx="150" ry="120" fill="url(#gvHalo)"/>
{_iso_cubo(205, 214, 104, 16, "gvSlabT", "gvSlabL", "gvSlabR", traco="#D9D9D9")}
{_iso_cubo(205, 182, 72, 12, "gvSlabT", "gvSlabL", "gvSlabR", traco="#D4D4D4")}
<g filter="url(#gvBlur)" opacity=".55">{_iso_cubo(205, 70, 52, 120, "gvTop", "gvLeft", "gvRight")}</g>
{_iso_cubo(205, 70, 52, 120, "gvTop", "gvLeft", "gvRight")}
<path d="M153 150 L205 176 L257 150 M153 112 L205 138 L257 112" stroke="#FFF3C4" stroke-opacity=".7" fill="none"/>
<g transform="translate(205,86)" fill="none" stroke="#7A5E0A" stroke-width="2.4">
  <ellipse cx="0" cy="0" rx="16" ry="6"/><path d="M-16 0v18c0 3.3 7.2 6 16 6s16-2.7 16-6V0"/><path d="M-16 9c0 3.3 7.2 6 16 6s16-2.7 16-6"/>
</g>
{_painel(48, 48, 62, 56, '<path d="M4 26V16M12 26V9M20 26V13M28 26V4"/>')}
{_painel(60, 150, 54, 52, '<path d="M14 27s9-4.5 9-11.3V7.8L14 4.5 5 7.8v7.9C5 22.5 14 27 14 27z"/><path d="m10 15 3 3 5-6"/>')}
{_painel(300, 34, 60, 54, '<circle cx="14" cy="14" r="3"/><circle cx="4" cy="4" r="2.4"/><circle cx="24" cy="4" r="2.4"/><circle cx="4" cy="24" r="2.4"/><circle cx="24" cy="24" r="2.4"/><path d="m6 6 6 6M22 6l-6 6M6 22l6-6M22 22l-6-6"/>', rot=6)}
{_painel(304, 140, 58, 52, '<path d="M8 22h13a6 6 0 0 0 .8-12A8 8 0 0 0 6.6 12.3 5 5 0 0 0 8 22z"/>', rot=6)}
<g fill="#C9A227">{''.join(f'<circle cx="{cx}" cy="{cy}" r="{r}" opacity="{o}"/>' for cx, cy, r, o in
    [(150,40,1.6,.7),(268,28,1.2,.6),(120,128,1.3,.5),(286,118,1.8,.7),(340,108,1.1,.5),(98,214,1.2,.5),(250,62,1,.6)])}</g>
</svg>"""

AI_ART_SVG = """<svg viewBox="0 0 200 170" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
<defs><filter id="gvAiGlow"><feGaussianBlur stdDeviation="3"/></filter>
<radialGradient id="gvAiHalo" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#C9A227" stop-opacity=".45"/><stop offset="1" stop-color="#C9A227" stop-opacity="0"/></radialGradient></defs>
<circle cx="100" cy="85" r="78" fill="url(#gvAiHalo)"/>
<g stroke="#C9A227" stroke-width="1.4" fill="none" stroke-linecap="round" opacity=".9">
  <path d="M70 70H40l-12-12M70 85H22M70 100H40l-12 12M130 70h30l12-12M130 85h48M130 100h30l12 12"/>
  <path d="M85 55V30l-10-10M100 55V16M115 55V30l10-10M85 115v25l-10 10M100 115v39M115 115v25l10 10"/>
</g>
<g fill="#C9A227">
  <circle cx="28" cy="58" r="3"/><circle cx="22" cy="85" r="3"/><circle cx="28" cy="112" r="3"/><circle cx="172" cy="58" r="3"/><circle cx="178" cy="85" r="3"/>
  <circle cx="172" cy="112" r="3"/><circle cx="75" cy="20" r="3"/><circle cx="100" cy="16" r="3"/><circle cx="125" cy="20" r="3"/><circle cx="75" cy="150" r="3"/>
  <circle cx="100" cy="154" r="3"/><circle cx="125" cy="150" r="3"/>
</g>
<rect x="70" y="55" width="60" height="60" rx="10" fill="#C9A227" opacity=".55" filter="url(#gvAiGlow)"/>
<rect x="70" y="55" width="60" height="60" rx="10" fill="#0B0B0B" stroke="#E2C25A" stroke-width="2.4"/>
<text x="100" y="95" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-size="26" font-weight="800" fill="#F0CF66">IA</text>
</svg>"""


# ════════════════════════════════════════════════════════════════════
# SIDEBAR — Menu lateral preto
# ════════════════════════════════════════════════════════════════════
_LOGO_SIDEBAR = f"""
<div style="padding:18px 8px 18px;text-align:center;">
    <div style="display:flex;justify-content:center;">{LOGO_SVG.format(s=58, bg="#000000")}</div>
    <div style="font-family:Lora,serif;font-size:19px;font-weight:600;color:#FFFFFF;letter-spacing:2px;white-space:nowrap;
                text-transform:uppercase;margin-top:6px;line-height:1.1;">Governantes</div>
    <div style="display:flex;align-items:center;justify-content:center;gap:6px;margin-top:4px;">
        <span style="height:1px;width:12px;background:#C9A227;flex-shrink:0;"></span>
        <span style="font-family:Lora,serif;font-size:8.5px;color:#C9A227 !important;letter-spacing:0.6px;text-transform:uppercase;white-space:nowrap;">Governança de Dados &amp; IA</span>
        <span style="height:1px;width:12px;background:#C9A227;flex-shrink:0;"></span>
    </div>
</div>"""

def form_acesso(sufixo=""):
    """Fluxo de acesso existente (seleção do usuário de demonstração). Usado no menu lateral e na página pública."""
    st.markdown('<div class="gv-nav-label">Acesso à plataforma</div>', unsafe_allow_html=True)
    email = st.selectbox("Usuário", list(USUARIOS.keys()),
        format_func=lambda x: f"{USUARIOS[x]['nome']} · {USUARIOS[x]['perfil']}",
        label_visibility="collapsed", key=f"sel_usuario{sufixo}")
    if st.button("Entrar →", key=f"login{sufixo}", use_container_width=True):
        st.session_state["usuario"]      = email
        st.session_state["perfil_atual"] = USUARIOS[email]["perfil"]
        st.session_state["nome_atual"]   = USUARIOS[email]["nome"]
        st.session_state["pagina"]       = "🏠 Início"
        st.rerun()


PILARES = [
    ("01", "Entender", "Conhecer os dados, seu contexto, significado, origem e utilização."),
    ("02", "Confiar", "Estabelecer qualidade, responsabilidade, segurança e controle."),
    ("03", "Transformar", "Identificar problemas, priorizar ações e melhorar processos."),
    ("04", "Gerar valor", "Medir utilização, eficiência, redução de riscos e resultados."),
]


def pagina_publica():
    """Primeira experiência do visitante. Conteúdo institucional estático: nenhum dado interno é consultado."""
    pilares = "".join(f'<article class="gv-pilar"><div class="gv-pilar-n">{n}</div><h3>{t}</h3><p>{d}</p></article>'
                      for n, t, d in PILARES)
    st.markdown('<style>[data-testid="stMainBlockContainer"],.main .block-container{padding-top:56px !important;}</style>',
                unsafe_allow_html=True)
    st.markdown(f"""
<section class="gv-pub" aria-labelledby="gv-pub-titulo">
  <div>
    <div class="gv-pub-marca">Governantes<span></span></div>
    <div class="gv-pub-cat">Data Intelligence &amp; Governance Platform</div>
    <h1 class="gv-pub-h" id="gv-pub-titulo">Da gestão dos dados à <em>geração de valor</em> para o negócio.</h1>
    <p class="gv-pub-txt">Uma plataforma que conecta estratégia, dados, governança e operação para transformar dados em ativos confiáveis, utilizados e capazes de gerar resultados mensuráveis.</p>
    <p class="gv-pub-comp">A Governantes ajuda as organizações a entender seus dados, estabelecer confiança, identificar oportunidades, resolver problemas e transformar a gestão dos dados em resultados para o negócio.</p>
  </div>
  <div class="gv-pub-art" aria-hidden="true">{HERO_ART_SVG}</div>
</section>""", unsafe_allow_html=True)
    if st.button("ENTRAR NA PLATAFORMA", key="pub_entrar", icon=":material/arrow_forward:"):
        st.session_state["mostrar_acesso"] = True
    if st.session_state.get("mostrar_acesso"):
        with st.container(key="pub_acesso"):
            form_acesso("_pub")
    st.markdown(f'<section class="gv-pilares" aria-label="Pilares">{pilares}</section>'
                f'<div class="gv-pub-rodape">© Governantes. Conteúdo institucional.</div>', unsafe_allow_html=True)


if "usuario" not in st.session_state:
    st.session_state["usuario"] = None

if not st.session_state["usuario"]:
    with st.sidebar:
        st.markdown(_LOGO_SIDEBAR, unsafe_allow_html=True)
        form_acesso()
    pagina_publica()
    st.stop()

with st.sidebar:
    st.markdown(_LOGO_SIDEBAR, unsafe_allow_html=True)

    u      = USUARIOS[st.session_state["usuario"]]
    perfil = u["perfil"]
    cor    = PERFIL_COR[perfil]
    st.session_state["perfil_atual"] = perfil
    st.session_state["nome_atual"]   = u["nome"]
    is_curador   = perfil in ["curador","aprovador"]
    is_aprovador = perfil == "aprovador"

    if "pagina" not in st.session_state:
        st.session_state["pagina"] = "🏠 Início"

    # Valor dos Dados: só aparece com VD_HABILITADO nos secrets e a estrutura instalada
    VD_ATIVO, VD_MOTIVO = vd_telas.estado_instalacao(qry, bool(st.secrets.get("VD_HABILITADO", False)))
    vd_telas.NOMES = {k: v["nome"] for k, v in USUARIOS.items()}

    # (ícone material, rótulo, destino) — destinos inalterados
    NAV_ITEMS = [
        (":material/home:",            "Início",                "🏠 Início"),
        (":material/database:",        "Catálogo de Dados",     "📋 Catálogo"),
        (":material/verified_user:",   "Qualidade de Dados",    "🏆 Qualidade"),
        (":material/menu_book:",       "Glossário de Negócio",  "📖 Glossário"),
        (":material/hub:",             "Linhagem de Dados",     "🔗 Linhagem"),
        (":material/search:",          "Busca Global",          "🔍 Busca Global"),
        (":material/assignment:",      "Solicitações",          "⚡ Meu Espaço"),
        (":material/trending_up:",     "Gestão e Indicadores",  "📊 Indicadores"),
    ]
    if VD_ATIVO:
        NAV_ITEMS.insert(5, (":material/insights:", "Valor dos Dados", vd_telas.DESTINO))
    NAV_OP = [
        (":material/layers:",          "Domínios",     "🏛️ Domínios"),
        (":material/deployed_code:",   "Produtos",     "📦 Produtos"),
        (":material/fact_check:",      "Scorecard",    "🛡️ Scorecard"),
        (":material/workspace_premium:", "Certificação", "🥇 Certificação"),
        (":material/edit_note:",       "Curadoria",    "✏️ Curadoria"),
        (":material/history:",         "Auditoria",    "🕐 Auditoria"),
    ]

    def _nav(itens):
        for ic_nav, label, dest in itens:
            ativo = st.session_state["pagina"] == dest
            if st.button(label, key=f"nav_{dest}_{label}", icon=ic_nav, use_container_width=True,
                         type="primary" if ativo else "secondary"):
                st.session_state["pagina"] = dest
                for k in ["gid_sel","cat_sel","dom_sel","sc_pilar"]:
                    st.session_state.pop(k, None)
                st.rerun()

    _nav(NAV_ITEMS)
    if is_curador:
        st.markdown('<div class="gv-nav-label">Governança</div>', unsafe_allow_html=True)
        _nav(NAV_OP)
    st.markdown("<div style='height:150px;'></div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# CABEÇALHO — busca global, notificações e menu de perfil
# ════════════════════════════════════════════════════════════════════
_nome_tb  = st.session_state.get("nome_atual", "")
_perf_tb  = st.session_state.get("perfil_atual", "consultante")
_perf_lbl = PERFIL_LABEL.get(_perf_tb, "")
_iniciais = "".join([n[0].upper() for n in _nome_tb.split()[:2]]) if _nome_tb else "U"

st.markdown("""
<div class="gov-topbar">
    <div style="margin-left:auto;display:flex;align-items:center;gap:18px;">
        <span style="width:44px;"></span><span class="gv-sep"></span><span style="width:180px;"></span>
    </div>
</div>""", unsafe_allow_html=True)


def _tb_buscar():
    q = st.session_state.get("tb_busca_q", "").strip()
    if q:
        st.session_state["busca_global_query"] = q
        st.session_state["pagina"] = "🔍 Busca Global"
        st.session_state["tb_busca_q"] = ""


with st.container(key="tb_busca"):
    st.text_input("Buscar", key="tb_busca_q", placeholder="Buscar dados, domínios, glossário...",
                  label_visibility="collapsed", on_change=_tb_buscar)

_STATUS_FECHADO = {"concluido","aprovado","cancelado","concluída","aprovada","encerrado"}
_pend_tb = 0
for _df_tb in (load_solicitacoes_acesso(), load_solicitacoes_qualidade()):
    if not _df_tb.empty and "status" in _df_tb.columns:
        _pend_tb += int((~_df_tb["status"].astype(str).str.lower().isin(_STATUS_FECHADO)).sum())

with st.container(key="tb_notif"):
    if _pend_tb:
        st.markdown('<span class="gv-dot"></span>', unsafe_allow_html=True)
    if st.button("", key="tb_notif_btn", icon=":material/notifications:",
                 help=f"{_pend_tb} solicitações em aberto" if _pend_tb else "Sem solicitações em aberto"):
        st.session_state["pagina"] = "⚡ Meu Espaço"
        st.rerun()

with st.container(key="tb_perfil"):
    st.markdown(f'<span class="gv-avatar">{_iniciais}</span>', unsafe_allow_html=True)
    with st.popover(_nome_tb or "Perfil", use_container_width=True):
        st.markdown(f"**{_nome_tb}**  \n{_perf_lbl}")
        if st.button("Trocar perfil", key="logout", icon=":material/swap_horiz:", use_container_width=True):
            st.session_state["usuario"] = None
            st.rerun()


# ── Função JS __govNav: clica nos botões Streamlit ocultos sem reload ──
st.markdown("""
<script>
(function(){
  function __govNav(key){
    // Encontra o botão oculto pelo atributo data-gov-nav
    var sel = 'button[data-gov-nav="'+key+'"]';
    var btn = document.querySelector(sel);
    if(btn){ btn.click(); return; }
    // Fallback: busca por texto "govnav-{key}" nos botões Streamlit
    var mark = 'govnav-'+key;
    document.querySelectorAll('button').forEach(function(b){
      if(b.textContent.trim()===mark){ b.click(); }
    });
  }
  window.__govNav = __govNav;
  // Oculta botões govnav-* via atributo + inline style
  // O atributo data-govnav-wrap ativa o CSS estático imediatamente;
  // o inline style é um reforço para reruns rápidos do Streamlit.
  function tagNavBtns(){
    document.querySelectorAll('button').forEach(function(b){
      var t = b.textContent.trim();
      if(t.startsWith('govnav-')){
        var k = t.replace('govnav-','');
        b.setAttribute('data-gov-nav', k);
        // Sobe até o container stButton e marca com atributo CSS + inline
        var wrap = b.closest('[data-testid="stButton"]') || b.parentElement;
        if(wrap){
          wrap.setAttribute('data-govnav-wrap', k);
          wrap.style.cssText = 'display:none!important;position:absolute;left:-9999px;width:0;height:0;overflow:hidden;pointer-events:none';
        }
      }
    });
  }
  // Executa imediatamente (caso DOM já tenha os botões)
  tagNavBtns();
  document.addEventListener('DOMContentLoaded', tagNavBtns);
  // MutationObserver: esconde cada botão govnav no instante em que
  // o React o insere no DOM, antes do primeiro paint.
  var _obs = new MutationObserver(function(ml){
    var needCheck = false;
    ml.forEach(function(m){
      m.addedNodes.forEach(function(n){
        if(n.nodeType===1){
          // Verifica o próprio nó e seus filhos
          if((n.tagName==='BUTTON'||n.querySelector && n.querySelector('button'))){ needCheck=true; }
        }
      });
    });
    if(needCheck) tagNavBtns();
  });
  // Inicia observação logo que body existir
  function startObs(){
    if(document.body){
      _obs.observe(document.body,{childList:true,subtree:true});
    } else {
      setTimeout(startObs,10);
    }
  }
  startObs();
})();
</script>
""", unsafe_allow_html=True)

# ── Badge ambiente demo ───────────────────────────────────────────────
st.markdown("""
<div class="demo-badge" style="position:fixed;bottom:16px;right:16px;z-index:9999;
            background:#FFFFFF;border:1px solid #E5E5E5;border-radius:6px;
            padding:4px 10px;display:flex;align-items:center;gap:6px;
            box-shadow:0 2px 8px rgba(0,0,0,0.06);">
  <div style="width:7px;height:7px;border-radius:50%;background:#B26A00;animation:pulse 2s infinite;"></div>
  <span style="color:#000000;font-size:0.65rem;font-weight:700;letter-spacing:1px;">AMBIENTE DEMO</span>
  <span style="color:#6E6E6E;font-size:0.6rem;">dados fictícios</span>
</div>
<style>@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}</style>
""", unsafe_allow_html=True)

# ── Navegação via topbar (jornadas + busca) ──────────────────────────
# Mapa de chave de jornada → página interna
_NAV_JORNADAS = {
    "descobrir": "📋 Catálogo",
    "entender":  "📖 Glossário",
    "confiar":   "🏆 Qualidade",
    "agir":      "⚡ Meu Espaço",
    "decidir":   "📊 Indicadores",
    "busca":     "🔍 Busca Global",
    # aliases para query-param legado (mantidos para compatibilidade)
    "catalogo":  "📋 Catálogo",
    "glossario": "📖 Glossário",
    "qualidade": "🏆 Qualidade",
    "linhagem":  "🔗 Linhagem",
    "espacomeu": "⚡ Meu Espaço",
}

# Fallback: query params (mantido para deep-links externos — não causa reload interno)
_qp_nav = st.query_params.get("nav", "")
if _qp_nav in _NAV_JORNADAS:
    st.session_state["pagina"] = _NAV_JORNADAS[_qp_nav]
    st.query_params.clear()
    st.rerun()

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
        if st.session_state.get("_db_limit"):
            st.info("🕐 **Limite diário do Databricks atingido.** O warehouse estará disponível novamente a partir de amanhã. A plataforma continua acessível — os dados serão exibidos quando a conexão for restabelecida.")
        else:
            st.warning(f"⚠️ Databricks indisponível. Detalhe: `{st.session_state['_db_err'][:120]}`")

    # ── KPIs ─────────────────────────────────────────────────────────
    _db_fail = bool(st.session_state.get("_db_err"))
    total_ativos = len(df_meta)  if not df_meta.empty else ("—" if _db_fail else 0)
    total_termos = len(df_gloss) if not df_gloss.empty else ("—" if _db_fail else 0)
    qual_media   = round(df_qual["score_final"].mean(), 1) if not df_qual.empty and "score_final" in df_qual.columns else None
    qual_str     = f"{qual_media}%" if qual_media is not None else ("Indisponível" if _db_fail else "—")

    STATUS_CLOSED = {"concluido","aprovado","cancelado","concluída","aprovada","encerrado"}
    if _db_fail and df_sol_ac.empty and df_sol_qu.empty:
        sol_abertas = "—"
    else:
        sol_abertas = 0
        if not df_sol_ac.empty and "status" in df_sol_ac.columns:
            sol_abertas += len(df_sol_ac[~df_sol_ac["status"].str.lower().isin(STATUS_CLOSED)])
        if not df_sol_qu.empty and "status" in df_sol_qu.columns:
            sol_abertas += len(df_sol_qu[~df_sol_qu["status"].str.lower().isin(STATUS_CLOSED)])

    # ══════════════════════════════════════════════════════════════════
    # A. BOAS-VINDAS + INDICADORES EXECUTIVOS (dados reais)
    # ══════════════════════════════════════════════════════════════════
    df_snap_h = load_snap()
    total_dominios = (df_meta["dominio"].dropna().astype(str).str.strip().replace("", pd.NA).dropna().nunique()
                      if not df_meta.empty and "dominio" in df_meta.columns else ("—" if _db_fail else 0))

    def _fmt(v):
        return f"{v:,}".replace(",", ".") if isinstance(v, int) else str(v)

    _kpis_home = [
        ("database", _fmt(total_ativos),   "Ativos de Dados",    "Tabelas ativas com metadados"),
        ("layers",   _fmt(total_dominios), "Domínios",           "Domínios com ativos catalogados"),
        ("shield",   qual_str,             "Qualidade dos Dados", "Média do score final avaliado"),
        ("book",     _fmt(total_termos),   "Termos de Negócio",  "Conceitos no glossário"),
    ]
    _kpi_html = "".join(f"""
        <div class="gv-card gv-kpi" title="{nota}">
            {icon(ic, 30)}
            <div class="gv-kpi-val">{val}</div>
            <div class="gv-kpi-lbl">{lbl}</div>
        </div>""" for ic, val, lbl, nota in _kpis_home)

    st.markdown(f"""
    <div class="gv-hero">
        <div>
            <h1 class="gv-h">Bem-vindo à plataforma <span style="color:#C9A227;">Governantes</span></h1>
            <div class="gv-sub">Governança de Dados e IA para transformar dados em valor, com confiança, controle e resultados.</div>
            <div class="gv-kpis">{_kpi_html}</div>
        </div>
        <div class="gv-art">{HERO_ART_SVG}</div>
    </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    # B. PAINÉIS — qualidade por domínio · evolução · minhas atividades
    # ══════════════════════════════════════════════════════════════════
    pn1, pn2, pn3 = st.columns([1, 1.05, 0.95], gap="medium")

    with pn1:
        if not df_qual.empty and "dominio" in df_qual.columns and "score_final" in df_qual.columns:
            dom_qual = (df_qual.groupby("dominio").agg(score_final=("score_final", "mean"), total=("score_final", "count"))
                        .reset_index().sort_values("score_final", ascending=False).head(6))
            corpo = "".join(f"""
                <div class="gv-bar" title="{int(r['total'])} registros avaliados">
                    <span style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#000;">{r['dominio']}</span>
                    <div class="gv-bar-track"><div class="gv-bar-fill" style="width:{min(float(r['score_final']),100):.0f}%;"></div></div>
                    <span style="text-align:right;font-weight:600;color:#000;">{float(r['score_final']):.0f}%</span>
                </div>""" for _, r in dom_qual.iterrows())
        elif _db_fail:
            corpo = '<div style="color:#5C5C5C;font-size:0.82rem;padding:28px 0;text-align:center;">Dados indisponíveis no momento</div>'
        else:
            corpo = '<div style="color:#5C5C5C;font-size:0.82rem;padding:28px 0;text-align:center;">Nenhum dado de qualidade encontrado</div>'
        st.markdown(f"""<div class="gv-card gv-panel">
            <div class="gv-panel-title">{icon('chart', 22)} Qualidade de Dados por Domínio</div>{corpo}</div>""",
            unsafe_allow_html=True)

    with pn2:
        with st.container(key="pnl_evol"):
            st.markdown(f'<div class="gv-panel-title" style="margin:0;">{icon("trend", 22)} Evolução da Qualidade de Dados</div>',
                        unsafe_allow_html=True)
            _ev = (df_snap_h[df_snap_h["dominio"] == "Todos"]
                   if not df_snap_h.empty and {"dominio", "score_qualidade", "data_snapshot"} <= set(df_snap_h.columns)
                   else pd.DataFrame())
            if not _ev.empty:
                _ev = _ev.assign(_d=pd.to_datetime(_ev["data_snapshot"])).sort_values("_d").tail(6)
                _mes = ["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"]
                _x = [f"{_mes[d.month-1]}/{str(d.year)[2:]}" if _ev["_d"].dt.month.nunique() < len(_ev) else _mes[d.month-1]
                      for d in _ev["_d"]]
                _y = _ev["score_qualidade"].astype(float).tolist()
                fig_ev = go.Figure(go.Scatter(
                    x=_x, y=_y, mode="lines+markers", line=dict(color="#C9A227", width=2.5, shape="spline", smoothing=0.6),
                    marker=dict(size=8, color="#FFFFFF", line=dict(color="#C9A227", width=2)),
                    fill="tozeroy", fillcolor="rgba(201,162,39,0.10)",
                    hovertemplate="%{x}: %{y:.1f}%<extra></extra>"))
                fig_ev.add_annotation(x=_x[-1], y=_y[-1], text=f"<b>{_y[-1]:.0f}%</b>", showarrow=False, yshift=20,
                                      font=dict(color="#000000", size=12), bgcolor="#C9A227", borderpad=4)
                _lo = max(0, min(_y) - 6)
                fig_ev.update_layout(height=232, margin=dict(t=18, b=6, l=4, r=10), paper_bgcolor="rgba(0,0,0,0)",
                                     plot_bgcolor="rgba(0,0,0,0)", showlegend=False,
                                     font=dict(family="Inter, sans-serif", color="#5C5C5C", size=11),
                                     xaxis=dict(showgrid=False, linecolor="#EAEAEA", fixedrange=True),
                                     yaxis=dict(range=[_lo, 100.5], ticksuffix="%", gridcolor="#F0F0F0", zeroline=False, fixedrange=True))
                st.plotly_chart(fig_ev, use_container_width=True, config={"displayModeBar": False})
            else:
                st.markdown('<div style="color:#5C5C5C;font-size:0.82rem;padding:60px 0;text-align:center;">'
                            + ("Dados indisponíveis no momento" if _db_fail else "Nenhum snapshot de qualidade registrado")
                            + '</div>', unsafe_allow_html=True)

    with pn3:
        def _cnt(df, col, valores, negar=False):
            if df.empty or col not in df.columns:
                return "—" if _db_fail else 0
            m = df[col].astype(str).str.lower().isin(valores)
            return int((~m if negar else m).sum())

        _atividades = [
            ("inbox",  "Solicitações pendentes",   sol_abertas, "⚡ Meu Espaço"),
            ("book",   "Aprovações de glossário",  _cnt(df_gloss, "status", {"em_revisao"}), "📖 Glossário"),
            ("shield", "Tratativas de qualidade",  _cnt(df_sol_qu, "status", STATUS_CLOSED, negar=True), "⚡ Meu Espaço"),
        ]
        if is_curador:
            _atividades.append(("award", "Certificações em andamento",
                                _cnt(df_cert, "status_cert", {"pendente", "em_analise"}), "🥇 Certificação"))
        with st.container(key="pnl_ativ"):
            st.markdown(f'<div class="gv-panel-title" style="margin-bottom:4px;">{icon("check", 22)} Minhas Atividades</div>',
                        unsafe_allow_html=True)
            for i_a, (ic_a, txt_a, n_a, dest_a) in enumerate(_atividades):
                card_link(f"ativ_{i_a}", f"""
                    <div class="gv-row">{icon(ic_a, 18, '#000000', 1.6)}<span>{txt_a}</span>
                    <span class="gv-pill">{n_a}</span>{icon('chevron', 16, '#8A8A8A')}</div>""", dest_a)

    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    # C. ACESSO RÁPIDO + ÁREA DE IA
    # ══════════════════════════════════════════════════════════════════
    qa_col, ai_col = st.columns([2.05, 1], gap="medium")
    with qa_col:
        with st.container(key="pnl_qa"):
            st.markdown(f'<div class="gv-panel-title">{icon("bolt", 22)} Acesso rápido</div>', unsafe_allow_html=True)
            _qa = [
                ("database", "Catálogo de Dados",       "Inventário de ativos e metadados", "📋 Catálogo"),
                ("book",     "Glossário de Negócio",    "Conceitos, regras e responsáveis", "📖 Glossário"),
                ("network",  "Linhagem de Dados",       "Origem e fluxo entre camadas",     "🔗 Linhagem"),
                ("shield",   "Regras de Qualidade",     "Dimensões e scores de qualidade",  "🏆 Qualidade"),
                ("chart",    "Relatórios e Dashboards", "Indicadores de governança",        "📊 Indicadores"),
            ]
            qa_cols = st.columns(5, gap="small")
            for i_q, (ic_q, t_q, d_q, dest_q) in enumerate(_qa):
                with qa_cols[i_q]:
                    card_link(f"qa_{i_q}", f"""
                        <div class="gv-card gv-qa">{icon(ic_q, 30)}
                            <div><div class="gv-qa-t"><span>{t_q}</span>{icon('chevron', 16, '#000000')}</div>
                            <div class="gv-qa-d">{d_q}</div></div>
                        </div>""", dest_q)

    with ai_col:
        _ai_html = f"""
        <div class="gv-ai">
            <h3><span style="color:#C9A227;">IA</span> na Governança de Dados</h3>
            <p>Sugestões assistidas de descrição e domínio para os ativos do catálogo, com a origem registrada na trilha de auditoria.</p>
            {'<span class="gv-ai-cta">Explorar recursos de IA ' + icon('arrow', 16, '#000000', 2) + '</span>' if is_curador
             else '<span class="gv-ai-note">Disponível para curadores e aprovadores</span>'}
            <div class="gv-ai-art">{AI_ART_SVG}</div>
        </div>"""
        if is_curador:
            card_link("ia", _ai_html, "✏️ Curadoria")
        else:
            st.markdown(_ai_html, unsafe_allow_html=True)

    st.markdown("<div style='height:22px;'></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    # D. VISÃO OPERACIONAL — status, ativos, pendências, atividades
    # ══════════════════════════════════════════════════════════════════
    st.markdown('<div class="gv-panel-title" style="margin:4px 0 10px;">Visão operacional</div>', unsafe_allow_html=True)
    op0, op1, op2, op3 = st.columns(4, gap="medium")

    with op0:
        with st.container(key="pnl_status"):
            st.markdown('<div style="font-weight:650;font-size:0.86rem;margin-bottom:6px;">Status das solicitações</div>', unsafe_allow_html=True)
            frames = [d[["status"]] for d in (df_sol_ac, df_sol_qu) if not d.empty and "status" in d.columns]
            if frames:
                status_counts = pd.concat(frames, ignore_index=True)["status"].value_counts().reset_index()
                status_counts.columns = ["status", "total"]
                _paleta = ["#C9A227", "#000000", "#5C5C5C", "#8A8A8A", "#BDBDBD", "#E0E0E0"]
                cores_rosca = [_paleta[i % len(_paleta)] for i in range(len(status_counts))]
                fig_donut = go.Figure(go.Pie(labels=status_counts["status"], values=status_counts["total"], hole=0.66,
                                             marker=dict(colors=cores_rosca, line=dict(color="#FFFFFF", width=2)),
                                             textinfo="none", hovertemplate="%{label}: %{value}<extra></extra>", sort=False))
                fig_donut.add_annotation(text=f"<b>{status_counts['total'].sum()}</b>", x=0.5, y=0.54, showarrow=False,
                                         font=dict(size=22, color="#000000"))
                fig_donut.add_annotation(text="total", x=0.5, y=0.38, showarrow=False, font=dict(size=10, color="#5C5C5C"))
                fig_donut.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=150,
                                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})
                st.markdown("".join(f"""
                    <div style="display:flex;align-items:center;gap:8px;margin:3px 0;font-size:0.74rem;">
                        <span style="width:8px;height:8px;border-radius:50%;background:{c};flex-shrink:0;"></span>
                        <span style="color:#5C5C5C;flex:1;">{r['status']}</span><b>{r['total']}</b></div>"""
                    for c, (_, r) in zip(cores_rosca, status_counts.iterrows())), unsafe_allow_html=True)
            else:
                st.markdown('<div style="color:#5C5C5C;font-size:0.8rem;padding:24px 0;text-align:center;">'
                            + ("Dados indisponíveis no momento" if _db_fail else "Nenhuma solicitação registrada")
                            + '</div>', unsafe_allow_html=True)

    def _lista(titulo, linhas, vazio):
        corpo = "".join(linhas) if linhas else f'<div style="color:#5C5C5C;font-size:0.8rem;padding:24px 0;text-align:center;">{vazio}</div>'
        return f'<div class="gv-card gv-panel"><div style="font-weight:650;font-size:0.86rem;margin-bottom:4px;">{titulo}</div>{corpo}</div>'

    with op1:
        linhas = []
        if not df_meta.empty:
            ativos_dest = df_meta.copy()
            if not df_cert.empty and "dominio" in df_cert.columns and "score_qualidade" in df_cert.columns:
                dom_score = df_cert.groupby("dominio")["score_qualidade"].mean()
                ativos_dest["_score"] = ativos_dest["dominio"].map(dom_score).fillna(0)
                ativos_dest = ativos_dest.sort_values("_score", ascending=False)
            for _, row in ativos_dest[["table_name", "dominio"]].head(5).iterrows():
                linhas.append(f"""<div class="gv-row" style="padding:8px 0;">{icon('database', 16, '#000000', 1.6)}
                    <div style="min-width:0;"><div style="font-weight:600;font-size:0.8rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{row['table_name']}</div>
                    <div style="color:#5C5C5C;font-size:0.7rem;">{row['dominio']}</div></div></div>""")
        st.markdown(_lista("Ativos em destaque", linhas, "Sem dados disponíveis"), unsafe_allow_html=True)

    with op2:
        linhas = []
        for df_p, tipo_p, campo_p in ((df_sol_ac, "Acesso", "tabela"), (df_sol_qu, "Qualidade", "descricao")):
            if not df_p.empty and "status" in df_p.columns:
                for _, row in df_p[~df_p["status"].astype(str).str.lower().isin(STATUS_CLOSED)].head(3).iterrows():
                    desc_p = str(row.get(campo_p, ""))[:40] if campo_p in row else "—"
                    linhas.append(f"""<div class="gv-row" style="padding:8px 0;align-items:flex-start;">
                        {icon('inbox' if tipo_p == 'Acesso' else 'shield', 16, '#000000', 1.6)}
                        <div style="min-width:0;flex:1;"><div style="font-weight:600;font-size:0.8rem;">{tipo_p}</div>
                        <div style="color:#5C5C5C;font-size:0.7rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{desc_p}</div></div>
                        <span class="gv-pill" style="font-size:0.66rem;">{row.get('status', '—')}</span></div>""")
        st.markdown(_lista("Pendências abertas", linhas[:5],
                           "Dados indisponíveis no momento" if _db_fail else "Nenhuma pendência em aberto"),
                    unsafe_allow_html=True)

    with op3:
        linhas = []
        if not df_tl.empty:
            for _, row in df_tl.head(5).iterrows():
                tipo_a = str(row.get("tipo_solicitacao", row.get("tipo", "—")))[:30]
                status_a = str(row.get("status", "—")).lower()
                resp_a = str(row.get("responsavel", row.get("solicitante", "—")))[:20]
                data_a = ""
                for dc in ["iniciado_em", "criado_em", "data", "updated_at"]:
                    if dc in row and pd.notna(row[dc]):
                        try:
                            data_a = pd.to_datetime(row[dc]).strftime("%d/%m %H:%M")
                        except Exception:
                            data_a = str(row[dc])[:10]
                        break
                cor_a = "#1E7F4F" if ("conclu" in status_a or "aprova" in status_a) else "#B26A00" if "penden" in status_a else "#8A8A8A"
                linhas.append(f"""<div class="gv-row" style="padding:8px 0;align-items:flex-start;">
                    <span style="width:8px;height:8px;border-radius:50%;background:{cor_a};margin-top:6px;flex-shrink:0;"></span>
                    <div style="min-width:0;flex:1;"><div style="font-weight:600;font-size:0.8rem;">{tipo_a}</div>
                    <div style="display:flex;justify-content:space-between;color:#5C5C5C;font-size:0.7rem;"><span>{resp_a}</span><span>{data_a}</span></div></div></div>""")
        st.markdown(_lista("Últimas atividades", linhas, "Sem atividades registradas"), unsafe_allow_html=True)

    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# 📖 GLOSSÁRIO — Área de Conhecimento
# ════════════════════════════════════════════════════════════════════
elif pagina == "📖 Glossário":
    page_header("📖","Glossário Corporativo",
                "A linguagem comum da organização — definições, regras e responsáveis.")

    st.markdown("""
    <div style="background:#FFFFFF99;border:1px solid #E5E5E5;border-radius:8px;
                padding:10px 14px;margin-bottom:16px;">
        <div style="color:#5C5C5C;font-size:0.78rem;line-height:1.6;">
            O Glossário reúne as definições oficiais dos conceitos utilizados pela organização.
            Ele garante que diferentes áreas compartilhem o mesmo entendimento sobre termos,
            indicadores e processos — eliminando interpretações divergentes.
        </div>
    </div>""", unsafe_allow_html=True)

    df_g     = load_glossario()
    df_rules = load_rules()
    df_links = load_links()
    _glos_db_fail = bool(st.session_state.get("_db_err"))

    if not df_g.empty:
        m1,m2,m3,m4 = st.columns(4)
        with m1: st.markdown(kpi(len(df_g),"Total de Conceitos","#C9A227","📖",
            "Total de conceitos de negócio cadastrados no glossário."), unsafe_allow_html=True)
        with m2: st.markdown(kpi(len(df_g[df_g["status"]=="homologado"]),"Homologados","#1E7F4F",tooltip=
            "Conceitos revisados e aprovados formalmente pela governança."), unsafe_allow_html=True)
        with m3: st.markdown(kpi(len(df_g[df_g["status"]=="em_revisao"]),"Em Revisão","#1A1A1A",tooltip=
            "Conceitos submetidos e aguardando aprovação."), unsafe_allow_html=True)
        with m4: st.markdown(kpi(len(df_g[df_g["status"]=="rascunho"]),"Rascunho","#5C5C5C",tooltip=
            "Conceitos em elaboração, ainda não submetidos para revisão."), unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        abas = ["📖 Conceitos de Negócio","📏 Regras de Negócio","🔗 Relacionamentos","🕐 Histórico"]
        if is_curador:
            abas.append("⚙️ Workflow")
        tabs_g = st.tabs(abas)

        # ── CONCEITOS ─────────────────────────────────────────────
        with tabs_g[0]:
            st.markdown('<div style="color:#5C5C5C;font-size:0.75rem;margin-bottom:12px;">Conceitos utilizados para representar assuntos relevantes para o negócio que possuem uma definição oficial.</div>', unsafe_allow_html=True)
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
                        st.markdown('<div style="color:#5C5C5C;font-size:0.75rem;margin-bottom:8px;">Sua sugestão será analisada pela equipe de Governança antes de ser publicada.</div>', unsafe_allow_html=True)
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
                        cor_st = {"homologado":"#1E7F4F","em_revisao":"#1A1A1A","rascunho":"#5C5C5C"}.get(row["status"],"#5C5C5C")
                        cor_cr = {"Crítico":"#C62828","Alto":"#C62828","Médio":"#000000","Baixo":"#1E7F4F"}.get(str(row.get("criticidade","")),"#5C5C5C")
                        links_t = df_links[df_links["glossary_id"]==gid] if not df_links.empty else pd.DataFrame()
                        rules_t = df_rules[df_rules["glossary_id"]==gid] if not df_rules.empty else pd.DataFrame()
                        n_tab = links_t["table_name"].nunique() if not links_t.empty else 0
                        n_reg = len(rules_t)

                        st.markdown(f"""
                        <div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:12px;padding:20px;">
                            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
                                <div style="color:#000000;font-size:1.2rem;font-weight:800;">{row['termo']}</div>
                                <span style="background:{cor_st}22;color:{cor_st};border-radius:20px;padding:3px 12px;font-size:0.72rem;font-weight:600;border:1px solid {cor_st}44;">
                                    {'✅ Homologado' if row['status']=='homologado' else '🔵 Em Revisão' if row['status']=='em_revisao' else '📄 Rascunho'}</span>
                            </div>
                            <div style="color:#000000;font-size:0.85rem;line-height:1.6;margin-bottom:12px;">{row['definicao']}</div>
                            {f'<div style="color:#5C5C5C;font-size:0.75rem;margin-bottom:10px;">Também conhecido como: <span style="color:#000000;">{row["sinonimos"]}</span></div>' if row.get("sinonimos") else ''}
                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px;">
                                <div style="background:#F5F5F5;border-radius:8px;padding:9px;">
                                    <div style="font-size:0.6rem;color:#5C5C5C;text-transform:uppercase;letter-spacing:1px;">DOMÍNIO</div>
                                    <div style="color:#000000;font-weight:600;font-size:0.82rem;">{row['dominio']}</div>
                                </div>
                                <div style="background:#F5F5F5;border-radius:8px;padding:9px;">
                                    <div style="font-size:0.6rem;color:#5C5C5C;text-transform:uppercase;letter-spacing:1px;">CRITICIDADE</div>
                                    <div style="color:{cor_cr};font-weight:600;font-size:0.82rem;">{row.get('criticidade','—')}</div>
                                </div>
                                <div style="background:#F5F5F5;border-radius:8px;padding:9px;">
                                    <div style="font-size:0.6rem;color:#5C5C5C;text-transform:uppercase;letter-spacing:1px;">RESPONSÁVEL (OWNER)</div>
                                    <div style="color:#000000;font-size:0.78rem;">{row.get('owner','—')}</div>
                                </div>
                                <div style="background:#F5F5F5;border-radius:8px;padding:9px;">
                                    <div style="font-size:0.6rem;color:#5C5C5C;text-transform:uppercase;letter-spacing:1px;">CRIADO POR</div>
                                    <div style="color:#000000;font-size:0.78rem;">{row.get('criado_por','—')}</div>
                                </div>
                            </div>
                            <div style="background:#F5F5F5;border:1px solid #E5E5E5;border-radius:8px;padding:10px 14px;">
                                <div style="font-size:0.6rem;color:#5C5C5C;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">ONDE ESTE CONCEITO APARECE</div>
                                <div style="display:flex;gap:20px;">
                                    <div title="Tabelas e ativos que utilizam este conceito"><span style="color:#1A1A1A;font-size:1.3rem;font-weight:800;">{n_tab}</span><span style="color:#5C5C5C;font-size:0.7rem;margin-left:4px;">ativos</span></div>
                                    <div title="Regras de negócio vinculadas a este conceito"><span style="color:#3D3D3D;font-size:1.3rem;font-weight:800;">{n_reg}</span><span style="color:#5C5C5C;font-size:0.7rem;margin-left:4px;">regras</span></div>
                                    <div title="Domínio de negócio responsável"><span style="color:#000000;font-size:1.3rem;font-weight:800;">1</span><span style="color:#5C5C5C;font-size:0.7rem;margin-left:4px;">domínio</span></div>
                                </div>
                            </div>
                        </div>""", unsafe_allow_html=True)

                        if not rules_t.empty:
                            st.markdown('<div style="color:#000000;font-weight:700;font-size:0.82rem;margin:12px 0 6px;">📏 Regras vinculadas</div>', unsafe_allow_html=True)
                            for _,r in rules_t.iterrows():
                                st.markdown(f"""
                                <div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:6px;padding:8px 12px;margin-bottom:5px;">
                                    <div style="display:flex;justify-content:space-between;">
                                        <span style="color:#000000;font-size:0.8rem;font-weight:600;">{r['nome_regra']}</span>
                                        <span style="background:#BC8CFF22;color:#3D3D3D;border-radius:4px;padding:1px 6px;font-size:0.65rem;">{r['categoria']}</span>
                                    </div>
                                    <div style="color:#5C5C5C;font-size:0.73rem;margin-top:2px;">{r['descricao_regra']}</div>
                                </div>""", unsafe_allow_html=True)
                        else:
                            st.markdown('<div style="color:#5C5C5C;font-size:0.75rem;padding:8px 0;">Nenhuma regra vinculada a este conceito ainda.</div>', unsafe_allow_html=True)

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
            st.markdown('<div style="color:#5C5C5C;font-size:0.75rem;margin-bottom:12px;">Uma regra de negócio define critérios utilizados para calcular, classificar, validar ou determinar uma informação.</div>', unsafe_allow_html=True)
            df_rg,_ = qry("SELECT g.termo, r.nome_regra, r.descricao_regra, r.categoria FROM meridian_governanca.business_rules r JOIN meridian_governanca.business_glossary g ON r.glossary_id=g.glossary_id ORDER BY g.termo, r.categoria")
            if not df_rg.empty:
                for _,r in df_rg.iterrows():
                    st.markdown(f"""
                    <div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:8px;padding:10px 14px;margin-bottom:6px;">
                        <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                            <span style="color:#000000;font-size:0.75rem;font-weight:700;">{r['termo']}</span>
                            <span style="background:#BC8CFF22;color:#3D3D3D;border-radius:4px;padding:1px 7px;font-size:0.65rem;">{r['categoria']}</span>
                        </div>
                        <div style="color:#000000;font-size:0.82rem;font-weight:600;">{r['nome_regra']}</div>
                        <div style="color:#5C5C5C;font-size:0.73rem;margin-top:2px;">{r['descricao_regra']}</div>
                    </div>""", unsafe_allow_html=True)
            else:
                estado_vazio("📏","Nenhuma regra cadastrada","As regras de negócio serão exibidas aqui quando forem cadastradas.")

            # Sugestão de nova regra — todos os perfis
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if not is_curador:
                with st.expander("💡 Sugerir nova regra de negócio"):
                    st.markdown('<div style="color:#5C5C5C;font-size:0.75rem;margin-bottom:8px;">Sua sugestão será analisada pela equipe de Governança antes de ser publicada.</div>', unsafe_allow_html=True)
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
            st.markdown('<div style="color:#5C5C5C;font-size:0.75rem;margin-bottom:12px;">Mostra como conceitos de negócio estão conectados a ativos de dados técnicos da organização.</div>', unsafe_allow_html=True)
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
                    nx.append(x); ny.append(y); nt.append(t); nc.append("#1A1A1A"); ns.append(16)
                for _,l in df_links.iterrows():
                    if l["glossary_id"] in t_pos and l["table_name"] in a_pos:
                        x0,y0=t_pos[l["glossary_id"]]; x1,y1=a_pos[l["table_name"]]
                        ex+=[x0,x1,None]; ey+=[y0,y1,None]
                fig_g = go.Figure()
                fig_g.add_trace(go.Scatter(x=ex,y=ey,mode="lines",line=dict(color="#CFCFCF",width=1.2),hoverinfo="none"))
                fig_g.add_trace(go.Scatter(x=nx,y=ny,mode="markers+text",marker=dict(color=nc,size=ns,line=dict(color="#FFFFFF",width=2)),text=nt,textposition="middle right",textfont=dict(color="#000000",size=11),hoverinfo="text"))
                fig_g.update_layout(paper_bgcolor="#FFFFFF",plot_bgcolor="#FFFFFF",showlegend=False,height=420,margin=dict(t=10,b=10,l=10,r=10),xaxis=dict(showgrid=False,zeroline=False,showticklabels=False),yaxis=dict(showgrid=False,zeroline=False,showticklabels=False))
                st.plotly_chart(fig_g,use_container_width=True)
                st.markdown('<div style="display:flex;gap:16px;margin-top:4px;"><div style="display:flex;align-items:center;gap:6px;"><div style="width:10px;height:10px;border-radius:50%;background:#C9A227;"></div><span style="color:#5C5C5C;font-size:0.72rem;">Conceitos de Negócio</span></div><div style="display:flex;align-items:center;gap:6px;"><div style="width:10px;height:10px;border-radius:50%;background:#8A8A8A;"></div><span style="color:#5C5C5C;font-size:0.72rem;">Ativos Técnicos</span></div></div>', unsafe_allow_html=True)
            else:
                estado_vazio("🔗","Nenhum relacionamento cadastrado","Os vínculos entre conceitos e ativos técnicos serão exibidos aqui.")

        # ── HISTÓRICO ─────────────────────────────────────────────
        with tabs_g[3]:
            df_wf,_ = qry("SELECT g.termo, w.acao, w.status_anterior, w.status_novo, w.aprovador, w.comentario, w.criado_em FROM meridian_governanca.glossary_approval_workflow w JOIN meridian_governanca.business_glossary g ON w.glossary_id=g.glossary_id ORDER BY w.criado_em DESC LIMIT 50")
            if not df_wf.empty:
                for _,r in df_wf.iterrows():
                    ts = str(r["criado_em"])[:16] if r["criado_em"] else "—"
                    st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:6px;padding:8px 12px;margin-bottom:5px;display:flex;justify-content:space-between;align-items:center;"><div><span style="color:#000000;font-size:0.78rem;font-weight:700;">{r["termo"]}</span><span style="color:#5C5C5C;font-size:0.72rem;margin-left:8px;">{r["acao"]}</span></div><span style="color:#5C5C5C;font-size:0.7rem;">{ts}</span></div>', unsafe_allow_html=True)
            else:
                estado_vazio("🕐","Nenhum histórico ainda","As aprovações e alterações de conceitos aparecerão aqui.")

        # ── WORKFLOW (apenas curador/aprovador) ───────────────────
        if is_curador and len(tabs_g)>4:
            with tabs_g[4]:
                wf_cols = st.columns(3)
                for col,(tit,st_wf,cor_wf) in zip(wf_cols,[("📄 Rascunho","rascunho","#5C5C5C"),("🔵 Em Revisão","em_revisao","#1A1A1A"),("✅ Homologado","homologado","#1E7F4F")]):
                    df_wfc = df_g[df_g["status"]==st_wf]
                    with col:
                        st.markdown(f'<div style="background:#FFFFFF;border:1px solid {cor_wf}44;border-radius:10px;padding:12px;"><div style="color:{cor_wf};font-weight:700;font-size:0.82rem;margin-bottom:8px;">{tit} ({len(df_wfc)})</div>', unsafe_allow_html=True)
                        for _,r in df_wfc.iterrows():
                            st.markdown(f'<div style="background:#F5F5F5;border:1px solid #E5E5E5;border-radius:6px;padding:7px 9px;margin-bottom:5px;"><div style="color:#000000;font-size:0.78rem;font-weight:600;">{r["termo"]}</div><div style="color:#5C5C5C;font-size:0.68rem;">{r["dominio"]}</div></div>', unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
    else:
        if _glos_db_fail:
            estado_vazio("⚠️", "Glossário indisponível",
                         "Não foi possível conectar ao banco de dados. O glossário será exibido quando a conexão for restabelecida.")
        else:
            estado_vazio("📖", "Glossário vazio",
                         "Nenhum conceito foi cadastrado ainda. Adicione o primeiro conceito para começar.")

    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# 📋 CATÁLOGO — Marketplace de Dados
# ════════════════════════════════════════════════════════════════════
elif pagina == "📋 Catálogo":
    page_header("📋","Catálogo de Dados","Descubra, compreenda e confie nos dados antes de utilizá-los.")

    st.markdown("""
    <div style="background:#FFFFFF99;border:1px solid #E5E5E5;border-radius:8px;
                padding:10px 14px;margin-bottom:16px;">
        <div style="color:#5C5C5C;font-size:0.78rem;line-height:1.6;">
            O Catálogo reúne os ativos de dados disponíveis na organização. Cada ativo possui informações
            sobre seu conteúdo, responsáveis, qualidade e relacionamento com conceitos de negócio.
            Use a busca ou os filtros para encontrar o dado que você precisa.
        </div>
    </div>""", unsafe_allow_html=True)

    df_cat = load_meta()
    _cat_db_fail = bool(st.session_state.get("_db_err"))
    if not df_cat.empty:
        schemas = df_cat["schema_name"].value_counts()
        k1,k2,k3 = st.columns(3)
        with k1: st.markdown(kpi(len(df_cat),"Ativos Catalogados","#C9A227",tooltip="Total de tabelas e ativos de dados disponíveis no catálogo."), unsafe_allow_html=True)
        with k2: st.markdown(kpi(f"{schemas.get('ouro',0)} · {schemas.get('prata',0)} · {schemas.get('bronze',0)}","Ouro · Prata · Bronze","#1A1A1A",tooltip="Distribuição dos ativos por camada de maturidade dos dados."), unsafe_allow_html=True)
        with k3: st.markdown(kpi(df_cat["dominio"].nunique(),"Domínios Representados","#3D3D3D",tooltip="Quantidade de domínios de negócio com ativos catalogados."), unsafe_allow_html=True)

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
            st.markdown(f'<div style="color:#5C5C5C;font-size:0.75rem;margin:8px 0;">{len(df_f)} ativo(s) encontrado(s)</div>', unsafe_allow_html=True)

            if "cat_sel" not in st.session_state:
                st.session_state["cat_sel"] = None

            rows_c = [df_f.iloc[i:i+3].reset_index(drop=True) for i in range(0,len(df_f),3)]
            for row_df in rows_c:
                cols_c = st.columns(3)
                for i,(_,item) in enumerate(row_df.iterrows()):
                    cor_c="#1E7F4F" if item["score_completude"]==100 else "#B26A00" if item["score_completude"]>=60 else "#C62828"
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
                    cor_c2= "#1E7F4F" if item["score_completude"]==100 else "#B26A00" if item["score_completude"]>=60 else "#C62828"
                    df_links_ativo = load_links()
                    termos_ativo = df_links_ativo[df_links_ativo["table_name"]==tb] if not df_links_ativo.empty else pd.DataFrame()
                    df_g_full = load_glossario()

                    st.markdown(f"""
                    <div style="background:#FFFFFF;border:1px solid {cor_c2}44;border-radius:12px;padding:18px;margin-top:8px;">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
                            <div style="color:#000000;font-size:1.05rem;font-weight:800;">{item['table_name']}</div>
                            <div style="text-align:right;">
                                <div style="color:{cor_c2};font-size:1.5rem;font-weight:800;" title="Score de documentação: percentual de metadados obrigatórios preenchidos">{item['score_completude']}%</div>
                                <div style="color:#5C5C5C;font-size:0.62rem;">documentação</div>
                            </div>
                        </div>
                        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px;">
                            <div style="background:#F5F5F5;border-radius:8px;padding:8px;">
                                <div style="font-size:0.6rem;color:#5C5C5C;text-transform:uppercase;margin-bottom:2px;">O QUE É</div>
                                <div style="color:#000000;font-size:0.78rem;">{item['descricao'] or '—'}</div>
                            </div>
                            <div style="background:#F5F5F5;border-radius:8px;padding:8px;">
                                <div style="font-size:0.6rem;color:#5C5C5C;text-transform:uppercase;margin-bottom:2px;">DOMÍNIO</div>
                                <div style="color:#000000;font-size:0.78rem;">{item['dominio'] or '—'}</div>
                            </div>
                            <div style="background:#F5F5F5;border-radius:8px;padding:8px;">
                                <div style="font-size:0.6rem;color:#5C5C5C;text-transform:uppercase;margin-bottom:2px;">RESPONSÁVEL (OWNER)</div>
                                <div style="color:#000000;font-size:0.78rem;">{item['data_owner'] or '—'}</div>
                            </div>
                            <div style="background:#F5F5F5;border-radius:8px;padding:8px;">
                                <div style="font-size:0.6rem;color:#5C5C5C;text-transform:uppercase;margin-bottom:2px;">GESTOR DO DADO (STEWARD)</div>
                                <div style="color:#000000;font-size:0.78rem;">{item['data_steward'] or '—'}</div>
                            </div>
                            <div style="background:#F5F5F5;border-radius:8px;padding:8px;">
                                <div style="font-size:0.6rem;color:#5C5C5C;text-transform:uppercase;margin-bottom:2px;">CLASSIFICAÇÃO</div>
                                <div style="color:#000000;font-size:0.78rem;">{item.get('classificacao') or '—'}</div>
                            </div>
                            <div style="background:#F5F5F5;border-radius:8px;padding:8px;">
                                <div style="font-size:0.6rem;color:#5C5C5C;text-transform:uppercase;margin-bottom:2px;">STATUS</div>
                                <div style="color:#000000;font-size:0.78rem;">{item.get('status') or '—'}</div>
                            </div>
                        </div>""", unsafe_allow_html=True)

                    if not termos_ativo.empty and not df_g_full.empty:
                        st.markdown('<div style="background:#F5F5F5;border-radius:8px;padding:10px 14px;margin-bottom:2px;"><div style="font-size:0.6rem;color:#5C5C5C;text-transform:uppercase;margin-bottom:6px;">CONCEITOS DE NEGÓCIO VINCULADOS</div>', unsafe_allow_html=True)
                        for _,lk in termos_ativo.iterrows():
                            t_row = df_g_full[df_g_full["glossary_id"]==lk["glossary_id"]]
                            if not t_row.empty:
                                t = t_row.iloc[0]
                                st.markdown(f'<span style="background:#C9A22722;color:#000000;border-radius:4px;padding:2px 9px;font-size:0.72rem;margin-right:4px;">{t["termo"]}</span>', unsafe_allow_html=True)
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
    else:
        if _cat_db_fail:
            estado_vazio("⚠️", "Catálogo indisponível",
                         "Não foi possível conectar ao banco de dados. O catálogo será exibido assim que a conexão for restabelecida.")
        else:
            estado_vazio("📋", "Catálogo vazio",
                         "Nenhum ativo foi catalogado ainda. Registre os primeiros ativos para começar.")

    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# 🏛️ DOMÍNIOS
# ════════════════════════════════════════════════════════════════════
elif pagina == "🏛️ Domínios":
    page_header("🏛️", "Domínios de Negócio", "Responsabilidades, ativos e conceitos organizados por área de negócio.")

    df_dom = load_meta()
    df_glos = load_glossario()

    if df_dom.empty:
        if st.session_state.get("_db_err"):
            estado_vazio("⚠️", "Domínios indisponíveis", "Não foi possível conectar ao banco de dados. Os domínios serão exibidos quando a conexão for restabelecida.")
        else:
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
            st.markdown(kpi(total_owners, "Owners distintos", "#1A1A1A", tooltip="Quantidade de responsáveis distintos associados aos ativos."), unsafe_allow_html=True)
        with k3:
            st.markdown(kpi(total_stewards, "Stewards distintos", "#3D3D3D", tooltip="Quantidade de gestores operacionais distintos associados aos ativos."), unsafe_allow_html=True)
        with k4:
            st.markdown(kpi(f"{pct_homologados}%", "Conceitos homologados", "#1E7F4F", tooltip="Percentual de conceitos distintos homologados."), unsafe_allow_html=True)

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
    <div style="background:#FFFFFF99;border:1px solid #E5E5E5;border-radius:8px;
                padding:10px 14px;margin-bottom:16px;">
        <div style="color:#5C5C5C;font-size:0.78rem;line-height:1.6;">
            O Scorecard resume cinco medidas operacionais com pesos iguais.
            O resultado é um índice indicativo de governança, não uma certificação nem uma avaliação formal de maturidade.
            Selecione um pilar para entender sua definição e como melhorar o resultado.
        </div>
    </div>""", unsafe_allow_html=True)

    df_sc    = load_meta()
    df_links = load_links()

    if df_sc.empty:
        if bool(st.session_state.get("_db_err")):
            estado_vazio("⚠️","Scorecard indisponível","Não foi possível conectar ao banco de dados. O scorecard será exibido quando a conexão for restabelecida.")
        else:
            estado_vazio("📊","Nenhum dado disponível","Registre ativos no catálogo para que o scorecard seja calculado.")
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
        cor_g="#1E7F4F" if ger>=80 else "#B26A00" if ger>=60 else "#C62828"

        st.markdown(f"""
        <div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:16px;
                    padding:20px;text-align:center;margin-bottom:20px;">
            <div style="font-size:0.7rem;color:#5C5C5C;text-transform:uppercase;letter-spacing:2px;margin-bottom:4px;">
                Índice Indicativo de Governança</div>
            <div style="font-size:3.5rem;font-weight:800;color:{cor_g};line-height:1;">{ger:.0f}%</div>
            <div style="color:#5C5C5C;font-size:0.75rem;margin-top:4px;">
                Média simples dos cinco pilares, com peso igual. Não representa qualidade efetiva dos dados nem maturidade formal.</div>
            <div style="color:#5C5C5C;font-size:0.7rem;margin-top:6px;">
                Documentação · Responsabilidade · Relacionamentos · Completude de Metadados · Certificação</div>
        </div>""", unsafe_allow_html=True)

        PILARES_INFO = {
            "Documentação":  {
                "icone":"📝","cor":"#1A1A1A","val":doc,
                "conceito":"Mede se os ativos possuem descrição de negócio preenchida. Uma boa documentação permite que qualquer usuário entenda o propósito do dado sem precisar consultar o time técnico.",
                "como_melhorar":"Acesse Curadoria → Tabela Individual e preencha a descrição de cada ativo. O botão 'Sugerir com IA' acelera esse processo."
            },
            "Responsabilidade": {
                "icone":"👤","cor":"#000000","val":own,
                "conceito":"Avalia se cada ativo possui um Responsável pelo Dado (Data Owner) formalmente definido. O Owner responde pelas decisões sobre qualidade e uso correto do dado.",
                "como_melhorar":"Acesse Curadoria → Tabela Individual ou Edição em Lote e atribua um Responsável para os ativos sem dono definido."
            },
            "Relacionamentos":{
                "icone":"🔗","cor":"#3D3D3D","val":rel,
                "conceito":"Verifica se os ativos técnicos estão conectados a conceitos de negócio do Glossário. Ativos conectados são mais fáceis de descobrir e entender pelas áreas de negócio.",
                "como_melhorar":"Acesse o Glossário → Relacionamentos e vincule cada conceito às tabelas correspondentes."
            },
            "Completude de Metadados":     {
                "icone":"⭐","cor":"#1E7F4F","val":qual,
                "conceito":"Percentual médio de preenchimento dos metadados obrigatórios. Este indicador mede completude documental; não representa, por si só, a qualidade efetiva dos dados.",
                "como_melhorar":"Preencha todos os campos obrigatórios na Curadoria. Cada campo preenchido adiciona 20 pontos ao score do ativo."
            },
            "Certificação":  {
                "icone":"🏆","cor":"#C62828","val":cert,
                "conceito":"Percentual de ativos com status formal de certificação registrado no campo selo. O preenchimento de metadados, isoladamente, não equivale à certificação.",
                "como_melhorar":"Siga o fluxo formal de certificação e confirme o atendimento aos critérios definidos antes de conceder o selo."
            },
        }

        if "sc_pilar" not in st.session_state:
            st.session_state["sc_pilar"] = None

        cols_p = st.columns(5)
        for col,(nome,info) in zip(cols_p,PILARES_INFO.items()):
            cor_p="#1E7F4F" if info["val"]>=80 else "#B26A00" if info["val"]>=60 else "#C62828"
            is_sel = st.session_state["sc_pilar"] == nome
            with col:
                st.markdown(f"""
                <div style="background:{'#C9A22714' if is_sel else '#FFFFFF'};
                            border:1px solid {'#C9A227' if is_sel else '#E5E5E5'};
                            border-radius:12px;padding:16px;text-align:center;margin-bottom:2px;">
                    <div style="font-size:1.3rem;margin-bottom:5px;">{info['icone']}</div>
                    <div style="font-size:1.8rem;font-weight:800;color:{cor_p};">{info['val']:.0f}%</div>
                    <div style="color:#5C5C5C;font-size:0.72rem;margin-bottom:8px;">{nome}</div>
                    <div style="background:#E5E5E5;border-radius:4px;height:4px;">
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
            cor_p2 = "#1E7F4F" if info["val"]>=80 else "#B26A00" if info["val"]>=60 else "#C62828"
            st.markdown(f"""
            <div style="background:#FFFFFF;border:1px solid {cor_p2}44;border-radius:12px;padding:18px;margin:8px 0 16px;">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
                    <span style="font-size:1.5rem;">{info['icone']}</span>
                    <div>
                        <div style="color:#000000;font-size:1rem;font-weight:800;">{pilar_sel}</div>
                        <div style="color:{cor_p2};font-size:1.3rem;font-weight:800;">{info['val']:.0f}%</div>
                    </div>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                    <div style="background:#F5F5F5;border-radius:8px;padding:12px;">
                        <div style="color:#5C5C5C;font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">💡 O QUE SIGNIFICA</div>
                        <div style="color:#000000;font-size:0.8rem;line-height:1.5;">{info['conceito']}</div>
                    </div>
                    <div style="background:#F5F5F5;border-radius:8px;padding:12px;">
                        <div style="color:#5C5C5C;font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">🚀 COMO MELHORAR</div>
                        <div style="color:#000000;font-size:0.8rem;line-height:1.5;">{info['como_melhorar']}</div>
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

            st.markdown(f'<div style="color:#000000;font-weight:700;font-size:0.82rem;margin-bottom:8px;">📋 Ativos — {pilar_sel}</div>', unsafe_allow_html=True)
            for _,row_p in df_pilar.head(10).iterrows():
                val_campo = row_p.get(label_col,"")
                tem = bool(val_campo)
                cor_t="#1E7F4F" if tem else "#C62828"
                display = str(val_campo)[:30] if tem and label_col != "score_completude" else f"{val_campo}%" if label_col == "score_completude" else "—"
                st.markdown(f"""
                <div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:6px;
                            padding:7px 12px;margin-bottom:4px;
                            display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="color:#000000;font-size:0.78rem;font-weight:600;">{row_p['table_name']}</span>
                        <span style="background:#58A6FF22;color:#1A1A1A;border-radius:3px;padding:1px 5px;font-size:0.62rem;margin-left:5px;">{row_p['schema_name']}</span>
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
                cor_o="#1E7F4F" if row["score_completude"]>=80 else "#B26A00" if row["score_completude"]>=60 else "#C62828"
                medalha = ["🥇","🥈","🥉"][i] if i<3 else f"#{i+1}"
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                            background:#FFFFFF;border:1px solid #E5E5E5;border-radius:8px;
                            padding:10px 14px;margin-bottom:5px;">
                    <div style="display:flex;align-items:center;gap:10px;">
                        <span style="font-size:1.1rem;width:28px;text-align:center;">{medalha}</span>
                        <span style="color:#000000;font-size:0.85rem;font-weight:600;">{row['dominio']}</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div style="background:#E5E5E5;border-radius:4px;height:6px;width:120px;">
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
        with k1: st.markdown(kpi(len(meus_acess),"Solicitações de Acesso","#1A1A1A",tooltip="Suas solicitações de acesso a ativos de dados."), unsafe_allow_html=True)
        with k2: st.markdown(kpi(len(meus_qual),"Solicitações de Qualidade","#3D3D3D",tooltip="Seus reportes de problemas de qualidade."), unsafe_allow_html=True)
        with k3: st.markdown(kpi(len(meus_conc),"Sugestões de Conceitos","#C9A227",tooltip="Conceitos que você sugeriu ao glossário."), unsafe_allow_html=True)
        with k4: st.markdown(kpi(len(meus_reg),"Sugestões de Regras","#1E7F4F",tooltip="Regras de negócio que você sugeriu."), unsafe_allow_html=True)

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
                cs_sol={"pendente":"#000000","aprovado":"#1E7F4F","rejeitado":"#C62828"}.get(sol["status"],"#8A8A8A")
                st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:12px;padding:14px;margin-bottom:10px;"><div style="display:flex;justify-content:space-between;margin-bottom:10px;"><div style="color:#000000;font-weight:700;font-size:0.85rem;">{sol["titulo"]}</div><span style="background:{cs_sol}22;color:{cs_sol};border-radius:20px;padding:2px 10px;font-size:0.7rem;font-weight:600;">● {sol["status"]}</span></div>',unsafe_allow_html=True)
                eh=""
                for i,etapa in enumerate(etapas):
                    tl_e=tl_sol[tl_sol["etapa"]==etapa].iloc[0] if not tl_sol.empty and etapa in tl_sol["etapa"].values else None
                    if tl_e is not None:
                        se=tl_e["status_etapa"]; ie={"concluido":"✅","atrasado":"⏰","pendente":"⏳"}.get(se,"🔵")
                        hg=tl_e.get("horas_gastas"); sl_h=tl_e.get("sla_horas",0)
                        dn=tl_e.get("dentro_sla",True); hg_txt=f"{hg:.0f}h/{sl_h}h" if hg is not None else "—"
                        cs2="#1E7F4F" if dn else "#C62828"
                        eh+=f'<div style="text-align:center;flex:1;background:{"#E8F5EE" if se=="concluido" else "#FDECEA" if se=="atrasado" else "#F5F5F5"};border:1px solid {"#E8F5EE" if se=="concluido" else "#FDECEA" if se=="atrasado" else "#E5E5E5"};border-radius:8px;padding:8px;"><div style="font-size:0.6rem;color:#5C5C5C;text-transform:uppercase;">{etapa.upper()}</div><div style="font-size:1.3rem;">{ie}</div><div style="font-size:0.6rem;color:{cs2};font-weight:600;">{hg_txt}</div></div>'
                    else:
                        eh+=f'<div style="text-align:center;flex:1;background:#F5F5F5;border:1px solid #E5E5E5;border-radius:8px;padding:8px;opacity:0.4;"><div style="font-size:0.6rem;color:#5C5C5C;text-transform:uppercase;">{etapa.upper()}</div><div style="font-size:1.3rem;">⭕</div><div style="font-size:0.6rem;color:#5C5C5C;">—</div></div>'
                    if i<len(etapas)-1: eh+=f'<div style="flex:0;color:#6E6E6E;font-size:1rem;padding:0 4px;align-self:center;">→</div>'
                st.markdown(f'<div style="display:flex;gap:6px;">{eh}</div></div>',unsafe_allow_html=True)

        section_divider("MINHAS SOLICITAÇÕES DE ACESSO")
        if meus_acess.empty:
            estado_vazio("🔑","Nenhuma solicitação de acesso","Quando você solicitar acesso a um ativo no Catálogo, ela aparecerá aqui.")
        else:
            for _,r in meus_acess.iterrows():
                cor_s = {"pendente":"#000000","aprovado":"#1E7F4F","rejeitado":"#C62828"}.get(r["status"],"#5C5C5C")
                st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:8px;padding:10px 14px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;"><div><span style="color:#000000;font-weight:700;font-size:0.82rem;">{r["ativo_solicitado"]}</span><span style="color:#5C5C5C;font-size:0.72rem;margin-left:8px;">{r["tipo_acesso"]}</span></div><span style="color:{cor_s};font-size:0.72rem;font-weight:600;">● {r["status"]}</span></div>', unsafe_allow_html=True)

        section_divider("MINHAS SUGESTÕES")
        tab_conc, tab_reg = st.tabs(["💡 Conceitos sugeridos","📏 Regras sugeridas"])
        with tab_conc:
            if meus_conc.empty:
                estado_vazio("💡","Nenhuma sugestão de conceito","Acesse o Glossário e use '💡 Sugerir novo conceito' para contribuir.")
            else:
                for _,r in meus_conc.iterrows():
                    cor_s = {"pendente":"#000000","aprovado":"#1E7F4F","rejeitado":"#C62828"}.get(r["status"],"#5C5C5C")
                    st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:8px;padding:10px 14px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;"><div><span style="color:#000000;font-weight:700;font-size:0.82rem;">{r["nome_sugerido"]}</span></div><span style="color:{cor_s};font-size:0.72rem;font-weight:600;">● {r["status"]}</span></div>', unsafe_allow_html=True)
        with tab_reg:
            if meus_reg.empty:
                estado_vazio("📏","Nenhuma sugestão de regra","Acesse o Glossário → Regras de Negócio para sugerir.")
            else:
                for _,r in meus_reg.iterrows():
                    cor_s = {"pendente":"#000000","aprovado":"#1E7F4F","rejeitado":"#C62828"}.get(r["status"],"#5C5C5C")
                    st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:8px;padding:10px 14px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;"><div><span style="color:#000000;font-weight:700;font-size:0.82rem;">{r["nome_regra"]}</span></div><span style="color:{cor_s};font-size:0.72rem;font-weight:600;">● {r["status"]}</span></div>', unsafe_allow_html=True)

    # ── CURADOR / APROVADOR ───────────────────────────────────────
    else:
        _meu_db_fail = bool(st.session_state.get("_db_err"))
        pend_aprov  = len(df_gloss[df_gloss["status"]=="em_revisao"]) if not df_gloss.empty else 0
        sem_desc    = len(df_meta[df_meta["descricao"]==""]) if not df_meta.empty else 0
        sem_owner   = len(df_meta[df_meta["data_owner"]==""]) if not df_meta.empty else 0
        sem_steward = len(df_meta[df_meta["data_steward"]==""]) if not df_meta.empty else 0
        sem_dom     = len(df_meta[df_meta["dominio"]==""]) if not df_meta.empty else 0
        total_pend  = pend_aprov+sem_desc+sem_owner+sem_steward+sem_dom

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#FFFFFF,#E5E5E5);border:1px solid #E5E5E5;
                    border-radius:12px;padding:14px 18px;margin-bottom:16px;
                    display:flex;align-items:center;gap:12px;">
            <div style="background:#C9A22722;border-radius:8px;padding:8px;font-size:1.2rem;">⚡</div>
            <div>
                <div style="color:#000000;font-weight:700;font-size:0.9rem;">
                    Você possui <span style="color:#000000;">{total_pend}</span> ações pendentes.</div>
                <div style="color:#5C5C5C;font-size:0.72rem;margin-top:2px;">Revise e tome as ações necessárias.</div>
            </div>
        </div>""", unsafe_allow_html=True)

        section_divider("AÇÕES PRIORITÁRIAS")
        acoes = [
            ("APROVAR",f"{pend_aprov} conceitos aguardam aprovação","#C9A227","→ Workflow",pend_aprov),
            ("DOCUMENTAR",f"{sem_desc} ativos sem descrição","#1A1A1A","→ Curadoria",sem_desc),
            ("ATRIBUIR",f"{sem_owner} ativos sem Responsável definido","#C62828","→ Curadoria",sem_owner),
            ("ALOCAR",f"{sem_steward} ativos sem Gestor definido","#C62828","→ Curadoria",sem_steward),
            ("CLASSIFICAR",f"{sem_dom} ativos sem domínio","#3D3D3D","→ Curadoria",sem_dom),
        ]
        tem_acao = False
        for tipo,msg,cor_a,dest,qtd in acoes:
            if qtd>0:
                tem_acao = True
                st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:8px;padding:11px 16px;margin-bottom:6px;display:flex;align-items:center;justify-content:space-between;"><div style="display:flex;align-items:center;gap:10px;"><span style="background:{cor_a}22;color:{cor_a};border-radius:4px;padding:2px 8px;font-size:0.65rem;font-weight:700;">{tipo}</span><span style="color:#000000;font-size:0.82rem;">{msg}</span></div><span style="color:#5C5C5C;font-size:0.72rem;">{dest}</span></div>', unsafe_allow_html=True)
        if not tem_acao:
            if _meu_db_fail and df_meta.empty and df_gloss.empty:
                estado_vazio("⚠️", "Dados indisponíveis",
                             "Não foi possível conectar ao banco de dados. As pendências serão exibidas quando a conexão for restabelecida.")
            else:
                st.markdown('<div style="color:#1E7F4F;font-size:0.85rem;padding:12px;">✅ Nenhuma pendência no momento. Tudo em dia!</div>', unsafe_allow_html=True)

        section_divider("MINHAS RESPONSABILIDADES")
        if df_meta.empty and _meu_db_fail:
            estado_vazio("⚠️", "Responsabilidades indisponíveis",
                         "Não foi possível conectar ao banco de dados. Suas responsabilidades serão exibidas quando a conexão for restabelecida.")
        elif not df_meta.empty:
            k1,k2,k3,k4 = st.columns(4)
            with k1: st.markdown(kpi(len(df_meta[df_meta["data_owner"]==usuario]),"Como Responsável (Owner)","#C9A227",tooltip="Ativos pelos quais você é o Data Owner."), unsafe_allow_html=True)
            with k2: st.markdown(kpi(len(df_meta[df_meta["data_steward"]==usuario]),"Como Gestor (Steward)","#1A1A1A",tooltip="Ativos pelos quais você é o Data Steward."), unsafe_allow_html=True)
            with k3: st.markdown(kpi(df_meta["dominio"].nunique(),"Domínios Acompanhados","#3D3D3D"), unsafe_allow_html=True)
            with k4:
                doc_media = df_meta["score_completude"].mean()
                cor_d="#1E7F4F" if doc_media>=80 else "#B26A00" if doc_media>=60 else "#C62828"
                st.markdown(kpi(f"{doc_media:.0f}%","Score Médio de Documentação",cor_d,tooltip="Média do score de documentação de todos os ativos."), unsafe_allow_html=True)

        # Sugestões pendentes — visível para curador/aprovador
        df_sug_co = load_sugestoes_conceitos()
        df_sug_re = load_sugestoes_regras()
        pend_conc = df_sug_co[df_sug_co["status"]=="pendente"] if not df_sug_co.empty else pd.DataFrame()
        pend_reg  = df_sug_re[df_sug_re["status"]=="pendente"] if not df_sug_re.empty else pd.DataFrame()

        if not pend_conc.empty or not pend_reg.empty:
            section_divider("SUGESTÕES AGUARDANDO ANÁLISE")
            if not pend_conc.empty:
                st.markdown(f'<div style="color:#000000;font-size:0.78rem;font-weight:700;margin-bottom:6px;">💡 {len(pend_conc)} sugestão(ões) de conceito pendente(s)</div>', unsafe_allow_html=True)
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
        _tl3_db_fail = bool(st.session_state.get("_db_err"))
        if not df_tl3.empty:
            ETAPAS_TIPO3={"acesso":["abertura","owner","governanca"],"qualidade":["abertura","owner","governanca","resolucao"],"conceito":["abertura","owner","aprovacao"],"regra":["abertura","owner","aprovacao"]}
            sols_u=df_tl3.groupby("solicitacao_id").first().reset_index()
            for _,sr in sols_u.iterrows():
                sid=sr["solicitacao_id"]; titulo=sr.get("titulo","—"); tipo=sr.get("tipo_sol","acesso"); dom=sr.get("dominio","—")
                tl_sol=df_tl3[df_tl3["solicitacao_id"]==sid]
                etapas=ETAPAS_TIPO3.get(tipo,["abertura","owner","governanca"])
                tem_atraso=any(tl_sol["status_etapa"]=="atrasado") if not tl_sol.empty else False
                st.markdown(f'<div style="background:#FFFFFF;border:1px solid {"#B91C1C44" if tem_atraso else "#E5E5E5"};border-radius:12px;padding:14px;margin-bottom:8px;"><div style="display:flex;justify-content:space-between;margin-bottom:10px;"><div><div style="color:#000000;font-weight:700;font-size:0.85rem;">{titulo}</div><div style="color:#5C5C5C;font-size:0.7rem;">{dom} · {tipo}</div></div>{"<span style=background:#B91C1C22;color:#C62828;border-radius:20px;padding:2px 10px;font-size:0.7rem;font-weight:600;>⏰ ATRASADO</span>" if tem_atraso else ""}</div>',unsafe_allow_html=True)
                eh=""
                for i,etapa in enumerate(etapas):
                    tl_e=tl_sol[tl_sol["etapa"]==etapa].iloc[0] if etapa in tl_sol["etapa"].values else None
                    if tl_e is not None:
                        se=tl_e["status_etapa"]; ie={"concluido":"✅","atrasado":"⏰","pendente":"⏳"}.get(se,"🔵")
                        hg=tl_e.get("horas_gastas"); sl_h=tl_e.get("sla_horas",0)
                        dn=tl_e.get("dentro_sla",True); resp=str(tl_e.get("responsavel","")).split("@")[0]
                        hg_txt=f"{hg:.0f}h/{sl_h}h" if hg is not None else "—"
                        cs_t="#1E7F4F" if dn else "#C62828"
                        eh+=f'<div style="text-align:center;flex:1;background:{"#E8F5EE" if se=="concluido" else "#FDECEA" if se=="atrasado" else "#F5F5F5"};border:1px solid {"#E8F5EE" if se=="concluido" else "#FDECEA" if se=="atrasado" else "#E5E5E5"};border-radius:8px;padding:8px;"><div style="font-size:0.6rem;color:#5C5C5C;text-transform:uppercase;">{etapa.upper()}</div><div style="font-size:1.3rem;">{ie}</div><div style="font-size:0.65rem;color:#000000;font-weight:600;">{resp}</div><div style="font-size:0.6rem;color:{cs_t};">{hg_txt}</div></div>'
                    else:
                        eh+=f'<div style="text-align:center;flex:1;background:#F5F5F5;border:1px solid #E5E5E5;border-radius:8px;padding:8px;opacity:0.4;"><div style="font-size:0.6rem;color:#5C5C5C;text-transform:uppercase;">{etapa.upper()}</div><div style="font-size:1.3rem;">⭕</div></div>'
                    if i<len(etapas)-1: eh+=f'<div style="flex:0;color:#6E6E6E;font-size:1rem;padding:0 4px;align-self:center;">→</div>'
                st.markdown(f'<div style="display:flex;gap:6px;">{eh}</div></div>',unsafe_allow_html=True)
        elif _tl3_db_fail:
            estado_vazio("⚠️", "Workflow indisponível",
                         "Não foi possível conectar ao banco de dados. O workflow de atendimento será exibido quando a conexão for restabelecida.")
        else:
            estado_vazio("📬", "Nenhuma solicitação no sistema",
                         "As solicitações aparecerão aqui quando forem criadas pelos consultantes.")

        section_divider("MEUS CONCEITOS NO GLOSSÁRIO")
        df_meus = df_gloss[df_gloss["criado_por"]==usuario] if not df_gloss.empty else pd.DataFrame()
        if not df_meus.empty:
            for _,row in df_meus.iterrows():
                cor_s = {"homologado":"#1E7F4F","em_revisao":"#1A1A1A","rascunho":"#5C5C5C"}.get(row["status"],"#5C5C5C")
                st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:8px;padding:9px 14px;margin-bottom:5px;display:flex;justify-content:space-between;align-items:center;"><span style="color:#000000;font-size:0.82rem;font-weight:600;">{row["termo"]}</span><span style="color:{cor_s};font-size:0.75rem;font-weight:600;">● {row["status"].replace("_"," ").title()}</span></div>', unsafe_allow_html=True)
        else:
            estado_vazio("📖","Nenhum conceito vinculado","Não há conceitos vinculados ao seu usuário como Gestor (Steward).")

    if VD_ATIVO:
        vd_telas.secao_meu_espaco(qry, usuario, perfil)

    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# ✏️ CURADORIA — Apenas para curador/aprovador
# ════════════════════════════════════════════════════════════════════
elif pagina == vd_telas.DESTINO:
    if not VD_ATIVO:
        st.session_state["pagina"] = "🏠 Início"
        st.rerun()
    vd_telas.pagina(qry, usuario, perfil, VD_ATIVO, VD_MOTIVO)
    copyright_footer()

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

                    st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:10px;padding:12px 16px;margin-bottom:12px;"><div style="color:#000000;font-weight:700;font-size:0.9rem;">{sel_t}</div><div style="color:#5C5C5C;font-size:0.72rem;margin-top:2px;">{row["descricao"][:60]+"..." if row["descricao"] and len(row["descricao"])>60 else row["descricao"] or "Sem descrição cadastrada."}</div></div>', unsafe_allow_html=True)

                    pp1,pp2,pp3,pp4,pp5 = st.columns(5)
                    for pcol,pn,pv in [(pp1,"DOCUMENTAÇÃO",doc_p),(pp2,"RESPONSÁVEL",own_p),(pp3,"RELACION.",0),(pp4,"QUALIDADE",qual_p),(pp5,"CERTIFICAÇÃO",cert_p)]:
                        cor_pp="#1E7F4F" if pv>=80 else "#B26A00" if pv>0 else "#C62828"
                        with pcol:
                            st.markdown(f'<div style="background:#F5F5F5;border:1px solid #E5E5E5;border-radius:8px;padding:9px;text-align:center;margin-bottom:10px;"><div style="font-size:0.55rem;color:#5C5C5C;text-transform:uppercase;letter-spacing:0.8px;">{pn}</div><div style="font-size:1.1rem;font-weight:800;color:{cor_pp};">{f"{pv}%" if pv>0 else "—"}</div></div>', unsafe_allow_html=True)

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
                        st.markdown('<div style="background:#C9A22711;border:1px solid #E5E5E5;border-radius:8px;padding:10px 14px;margin-top:8px;"><div style="color:#000000;font-weight:700;font-size:0.75rem;">🤖 Sugestão da IA — revise antes de salvar</div></div>', unsafe_allow_html=True)
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
                    st.markdown(f'<div style="color:#000000;font-size:0.82rem;margin:6px 0;">{len(sels)} tabela(s) selecionada(s)</div>', unsafe_allow_html=True)
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
        else:
            if st.session_state.get("_db_err"):
                estado_vazio("⚠️", "Curadoria indisponível",
                             "Não foi possível conectar ao banco de dados. A curadoria estará disponível quando a conexão for restabelecida.")
            else:
                estado_vazio("📋", "Nenhum ativo para curar",
                             "Nenhum ativo foi catalogado ainda. Adicione ativos ao catálogo para começar.")

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
            with k2: st.markdown(kpi(manual,"Alterações Manuais","#1A1A1A"), unsafe_allow_html=True)
            with k3: st.markdown(kpi(ia_c,"Via Inteligência Artificial","#3D3D3D"), unsafe_allow_html=True)

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            af1,af2,af3 = st.columns(3)
            with af1: f_sc = st.selectbox("Schema",["Todos"]+sorted(df_aud["schema_name"].dropna().unique().tolist()),key="a_sc")
            with af2: f_or = st.selectbox("Origem",["Todos","manual","ia"],key="a_or")
            with af3: f_lim = st.selectbox("Linhas exibidas",[50,100,200,500],key="a_lim")

            df_af = df_aud.copy()
            if f_sc != "Todos": df_af = df_af[df_af["schema_name"]==f_sc]
            if f_or != "Todos": df_af = df_af[df_af["origem"]==f_or]
            df_af = df_af.head(f_lim)

            st.markdown('<div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:10px;overflow:hidden;margin-top:8px;"><table style="width:100%;border-collapse:collapse;"><thead><tr style="border-bottom:1px solid #E5E5E5;"><th style="color:#5C5C5C;font-size:0.62rem;font-weight:700;text-transform:uppercase;padding:9px 12px;text-align:left;">DATA/HORA</th><th style="color:#5C5C5C;font-size:0.62rem;font-weight:700;text-transform:uppercase;padding:9px 12px;text-align:left;">SCHEMA</th><th style="color:#5C5C5C;font-size:0.62rem;font-weight:700;text-transform:uppercase;padding:9px 12px;text-align:left;">TABELA</th><th style="color:#5C5C5C;font-size:0.62rem;font-weight:700;text-transform:uppercase;padding:9px 12px;text-align:left;">CAMPO</th><th style="color:#5C5C5C;font-size:0.62rem;font-weight:700;text-transform:uppercase;padding:9px 12px;text-align:left;">VALOR ANTERIOR</th><th style="color:#5C5C5C;font-size:0.62rem;font-weight:700;text-transform:uppercase;padding:9px 12px;text-align:left;">VALOR NOVO</th><th style="color:#5C5C5C;font-size:0.62rem;font-weight:700;text-transform:uppercase;padding:9px 12px;text-align:left;">ORIGEM</th></tr></thead><tbody>', unsafe_allow_html=True)

            for _,row in df_af.iterrows():
                ts = str(row["timestamp_op"])[:16] if row["timestamp_op"] else "—"
                oc="#3D3D3D" if row["origem"]=="ia" else "#1A1A1A"
                ot = "IA" if row["origem"]=="ia" else "Manual"
                va = str(row["valor_anterior"])[:30] if row["valor_anterior"] else "—"
                vn = str(row["valor_novo"])[:40] if row["valor_novo"] else "—"
                st.markdown(f'<tr style="border-bottom:1px solid #E5E5E5;"><td style="color:#5C5C5C;font-size:0.73rem;padding:8px 12px;">{ts}</td><td style="color:#1A1A1A;font-size:0.73rem;padding:8px 12px;">{row["schema_name"] or "—"}</td><td style="color:#000000;font-size:0.73rem;padding:8px 12px;font-weight:600;">{row["table_name"] or "—"}</td><td style="color:#5C5C5C;font-size:0.73rem;padding:8px 12px;">{row["campo_alterado"] or "—"}</td><td style="color:#5C5C5C;font-size:0.73rem;padding:8px 12px;">{va}</td><td style="color:#000000;font-size:0.73rem;padding:8px 12px;">{vn}</td><td style="padding:8px 12px;"><span style="background:{oc}22;color:{oc};border-radius:4px;padding:2px 8px;font-size:0.65rem;font-weight:700;">{ot}</span></td></tr>', unsafe_allow_html=True)

            st.markdown("</tbody></table></div>", unsafe_allow_html=True)

    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# 📊 INDICADORES — Painel de Gestão de Governança
# ════════════════════════════════════════════════════════════════════
elif pagina == "📊 Indicadores":
    if not is_curador:
        st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:12px;padding:40px;text-align:center;"><div style="font-size:2.2rem;margin-bottom:10px;">🔒</div><div style="font-family:Lora,serif;color:#000000;font-weight:700;margin-bottom:6px;">Acesso restrito</div><div style="color:#5C5C5C;font-size:0.8rem;">Esta área é destinada a Curadores e Aprovadores.</div></div>',unsafe_allow_html=True)
        st.stop()
    page_header("📊","Painel de Indicadores de Gestão",
                "Evolução da governança + SLA e atendimento de solicitações.")
    st.markdown("""<div style="background:#FFFFFF99;border:1px solid #E5E5E5;border-radius:8px;
                padding:10px 14px;margin-bottom:16px;"><div style="color:#5C5C5C;font-size:0.78rem;line-height:1.6;">
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

    _ind_db_fail = bool(st.session_state.get("_db_err"))
    if df_snap.empty:
        if _ind_db_fail:
            estado_vazio("⚠️", "Indicadores indisponíveis",
                         "Não foi possível conectar ao banco de dados. Os indicadores de governança serão exibidos quando a conexão for restabelecida.")
        else:
            estado_vazio("📊", "Nenhum snapshot disponível",
                         "Os indicadores serão exibidos após o primeiro snapshot de governança ser gerado.")
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
                d = a[c]-b[c]; cor="#1E7F4F" if d>0 else "#C62828" if d<0 else "#5C5C5C"; s="↑" if d>0 else "↓" if d<0 else "→"
                return f'<span style="color:{cor};font-size:0.65rem;font-weight:700;margin-left:4px;">{s}{abs(d):.1f}%</span>'
            k1,k2,k3,k4 = st.columns(4)
            for col,(lbl,campo,cor_k) in zip([k1,k2,k3,k4],[
                ("Documentação","score_doc","#1A1A1A"),("Ownership","score_ownership","#C9A227"),
                ("Qualidade","score_qualidade","#1E7F4F"),("Score Geral","score_geral","#3D3D3D")]):
                val=ultimo[campo]; d=delta(ultimo,anterior,campo)
                cor_v="#1E7F4F" if val>=80 else "#B26A00" if val>=60 else "#C62828"
                with col:
                    st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:10px;padding:14px 16px;border-top:3px solid {cor_k};"><div style="font-size:0.62rem;color:#5C5C5C;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">{lbl}</div><div style="display:flex;align-items:baseline;gap:4px;"><span style="font-size:1.7rem;font-weight:800;color:{cor_v};">{val:.1f}%</span>{d}</div></div>',unsafe_allow_html=True)
        section_divider("EVOLUÇÃO DOS INDICADORES")
        if not df_sn.empty:
            fig = go.Figure()
            for campo,cor_l,nome_l in [("score_doc","#000000","Documentação"),("score_ownership","#8A8A8A","Ownership"),("score_qualidade","#C9A227","Qualidade"),("score_geral","#BDBDBD","Score Geral")]:
                fig.add_trace(go.Scatter(x=pd.to_datetime(df_sn["data_snapshot"]),y=df_sn[campo],name=nome_l,line=dict(color=cor_l,width=2.5),mode="lines+markers",marker=dict(size=6)))
            fig.update_layout(paper_bgcolor="#FFFFFF",plot_bgcolor="#FFFFFF",font=dict(color="#5C5C5C",size=11),legend=dict(orientation="h",yanchor="bottom",y=1.02,bgcolor="rgba(0,0,0,0)"),height=320,margin=dict(t=40,b=20,l=40,r=20),xaxis=dict(showgrid=False,color="#5C5C5C"),yaxis=dict(showgrid=True,gridcolor="#E5E5E5",range=[0,105],ticksuffix="%"))
            st.plotly_chart(fig,use_container_width=True)
        section_divider("DISTRIBUIÇÃO POR DOMÍNIO")
        if not df_meta.empty:
            dom_agg=df_meta.groupby("dominio").agg(score_medio=("score_completude","mean")).reset_index().sort_values("score_medio",ascending=True)
            fig2=go.Figure(go.Bar(x=dom_agg["score_medio"],y=dom_agg["dominio"],orientation="h",marker=dict(color=dom_agg["score_medio"],colorscale=[[0,"#E8DDB5"],[1,"#C9A227"]],cmin=0,cmax=100),text=[f"{v:.0f}%" for v in dom_agg["score_medio"]],textposition="outside",textfont=dict(color="#000000",size=11)))
            fig2.update_layout(paper_bgcolor="#FFFFFF",plot_bgcolor="#FFFFFF",font=dict(color="#5C5C5C",size=11),height=260,margin=dict(t=10,b=10,l=10,r=60),xaxis=dict(showgrid=True,gridcolor="#E5E5E5",range=[0,115],ticksuffix="%"),yaxis=dict(showgrid=False,color="#000000"))
            st.plotly_chart(fig2,use_container_width=True)
        section_divider("RESUMO DE CERTIFICAÇÃO")
        if not df_cert.empty:
            cert_status=df_cert["status_cert"].value_counts().reset_index(); cert_status.columns=["status","qtd"]
            cor_cert={"certificado":"#1E7F4F","em_analise":"#000000","pendente":"#1A1A1A","nao_iniciado":"#8A8A8A"}
            cols_cert=st.columns(len(cert_status))
            for col,(_,row) in zip(cols_cert,cert_status.iterrows()):
                cor_c=cor_cert.get(row["status"],"#5C5C5C")
                label_c={"certificado":"✅ Certificados","em_analise":"🔵 Em Análise","pendente":"⏳ Pendentes","nao_iniciado":"📋 Não Iniciados"}.get(row["status"],row["status"])
                with col: st.markdown(kpi(row["qtd"],label_c,cor_c),unsafe_allow_html=True)

    # ── PAINEL DE SLA ──────────────────────────────────────────────
    if df_sla.empty:
        if _ind_db_fail:
            estado_vazio("⚠️", "SLA indisponível",
                         "Não foi possível carregar os dados de SLA. A seção será exibida quando a conexão for restabelecida.")
        else:
            estado_vazio("📋", "Nenhum dado de SLA",
                         "Os dados de SLA serão exibidos após o registro das primeiras solicitações.")
    elif not df_sla.empty:
        st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin:16px 0 12px;"><div style="height:1px;background:#F5F5F5;flex:1;"></div><span style="color:#5C5C5C;font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;">SLA E ATENDIMENTO DE SOLICITAÇÕES</span><div style="height:1px;background:#F5F5F5;flex:1;"></div></div>',unsafe_allow_html=True)
        df_slaf=df_sla.copy()
        if fi_dom!="Todos": df_slaf=df_slaf[df_slaf["dominio"]==fi_dom]
        ult_sla=df_slaf[df_slaf["data_snapshot"]==df_slaf["data_snapshot"].max()] if not df_slaf.empty else pd.DataFrame()
        if not ult_sla.empty:
            tot_ab=int(ult_sla["total_abertas"].sum()); tot_re=int(ult_sla["total_resolvidas"].sum())
            tot_at=int(ult_sla["total_atrasadas"].sum()); tm=ult_sla["tempo_medio_hrs"].mean(); tsla=ult_sla["taxa_sla_pct"].mean()
            cs_sla="#1E7F4F" if tsla>=90 else "#B26A00" if tsla>=70 else "#C62828"
            ss=st.columns(5)
            with ss[0]: st.markdown(kpi(tot_ab,"Abertas","#C9A227"),unsafe_allow_html=True)
            with ss[1]: st.markdown(kpi(tot_re,"Resolvidas","#1E7F4F"),unsafe_allow_html=True)
            with ss[2]: st.markdown(kpi(tot_at,"Atrasadas","#C62828"),unsafe_allow_html=True)
            with ss[3]: st.markdown(kpi(f"{tm:.0f}h","Tempo Médio","#3D3D3D",tooltip="Tempo médio de resolução em horas."),unsafe_allow_html=True)
            with ss[4]: st.markdown(kpi(f"{tsla:.0f}%","Taxa SLA",cs_sla,tooltip="% resolvidas dentro do prazo."),unsafe_allow_html=True)

        st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin:12px 0 8px;"><div style="height:1px;background:#F5F5F5;flex:1;"></div><span style="color:#5C5C5C;font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;">GARGALOS POR DOMÍNIO</span><div style="height:1px;background:#F5F5F5;flex:1;"></div></div>',unsafe_allow_html=True)
        for _,row in ult_sla.iterrows() if not ult_sla.empty else []:
            cs_g="#1E7F4F" if row["taxa_sla_pct"]>=90 else "#B26A00" if row["taxa_sla_pct"]>=70 else "#C62828"
            gb=row.get("gargalo_etapa","—"); gr=str(row.get("gargalo_resp","—")).split("@")[0]
            st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:10px;padding:10px 14px;margin-bottom:5px;display:flex;justify-content:space-between;align-items:center;"><div><span style="color:#000000;font-weight:700;font-size:0.82rem;">{row["dominio"]}</span><span style="color:#5C5C5C;font-size:0.7rem;margin-left:8px;">{row["tipo_sol"]}</span></div><div style="display:flex;gap:16px;font-size:0.7rem;"><span>Abertas: <b style="color:#000000;">{row["total_abertas"]}</b></span><span>Atrasadas: <b style="color:#C62828;">{row["total_atrasadas"]}</b></span><span>Gargalo: <b style="color:#C62828;">{gb} ({gr})</b></span><span style="background:{cs_g}22;color:{cs_g};border-radius:20px;padding:2px 8px;font-weight:700;">SLA {row["taxa_sla_pct"]:.0f}%</span></div></div>',unsafe_allow_html=True)
    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# 🏆 QUALIDADE — Score por Dimensão
# ════════════════════════════════════════════════════════════════════
elif pagina == "🏆 Qualidade":
    page_header("🏆","Score de Qualidade de Dados","Avaliação multidimensional — Completude · Unicidade · Validade · Atualidade · Consistência.")
    st.markdown("""<div style="background:#FFFFFF99;border:1px solid #E5E5E5;border-radius:8px;padding:10px 14px;margin-bottom:16px;"><div style="color:#5C5C5C;font-size:0.78rem;line-height:1.6;">A qualidade dos dados é avaliada em <strong style="color:#000000;">5 dimensões independentes</strong>. O Score Final é a média simples das 5 dimensões.</div></div>""",unsafe_allow_html=True)
    DIMENSOES={"completude_pct":{"nome":"Completude","icone":"📋","cor":"#1A1A1A","conceito":"% de campos obrigatórios preenchidos."},"unicidade_pct":{"nome":"Unicidade","icone":"🔑","cor":"#000000","conceito":"% de registros únicos na chave primária."},"validade_pct":{"nome":"Validade","icone":"✅","cor":"#1E7F4F","conceito":"% de valores no formato e domínio esperados."},"atualidade_pct":{"nome":"Atualidade","icone":"🕐","cor":"#3D3D3D","conceito":"% de registros dentro da janela de tempo esperada."},"consistencia_pct":{"nome":"Consistência","icone":"🔗","cor":"#C62828","conceito":"% de registros consistentes com tabelas relacionadas."}}
    df_qual=load_quality_dimensions()
    if df_qual.empty:
        if st.session_state.get("_db_err"):
            estado_vazio("⚠️","Qualidade indisponível","Não foi possível conectar ao banco de dados. Os scores serão exibidos quando a conexão for restabelecida.")
        else:
            estado_vazio("🏆","Nenhum dado de qualidade","Execute a avaliação de qualidade na Curadoria.")
    else:
        media_geral=df_qual["score_final"].mean(); cor_mg="#1E7F4F" if media_geral>=80 else "#B26A00" if media_geral>=60 else "#C62828"
        st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:16px;padding:20px;text-align:center;margin-bottom:20px;"><div style="font-size:0.7rem;color:#5C5C5C;text-transform:uppercase;letter-spacing:2px;margin-bottom:4px;">{len(df_qual)} ativos avaliados</div><div style="font-size:3.5rem;font-weight:800;color:{cor_mg};line-height:1;">{media_geral:.1f}%</div><div style="color:#5C5C5C;font-size:0.75rem;margin-top:6px;">Alta (≥80%): {len(df_qual[df_qual["nivel"]=="Alta"])} · Média (40–79%): {len(df_qual[df_qual["nivel"]=="Media"])} · Baixa (&lt;40%): {len(df_qual[df_qual["nivel"]=="Baixa"])}</div></div>',unsafe_allow_html=True)
        section_divider("MÉDIA POR DIMENSÃO")
        cols_dim=st.columns(5)
        for col,(campo,info) in zip(cols_dim,DIMENSOES.items()):
            media_dim=df_qual[campo].mean(); cor_d="#1E7F4F" if media_dim>=80 else "#B26A00" if media_dim>=60 else "#C62828"
            with col: st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:10px;padding:14px;text-align:center;" title="{info["conceito"]}"><div style="font-size:1.2rem;margin-bottom:4px;">{info["icone"]}</div><div style="font-size:1.6rem;font-weight:800;color:{cor_d};">{media_dim:.1f}%</div><div style="color:#5C5C5C;font-size:0.68rem;margin-bottom:8px;">{info["nome"]}</div><div style="background:#E5E5E5;border-radius:4px;height:3px;"><div style="background:{cor_d};border-radius:4px;height:3px;width:{min(media_dim,100):.0f}%;"></div></div><div style="color:#5C5C5C;font-size:0.6rem;margin-top:6px;line-height:1.3;">{info["conceito"]}</div></div>',unsafe_allow_html=True)
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
            cor_q="#1E7F4F" if row["score_final"]>=80 else "#B26A00" if row["score_final"]>=40 else "#C62828"
            nivel_badge={"Alta":"#1E7F4F","Media":"#000000","Baixa":"#C62828"}.get(row["nivel"],"#5C5C5C")
            dims_html="".join([f'<div style="text-align:center;"><div style="font-size:0.6rem;color:#5C5C5C;margin-bottom:2px;">{info["icone"]} {info["nome"][:4]}.</div><div style="font-size:0.75rem;font-weight:700;color:{"#1E7F4F" if row[campo]>=80 else "#C9A227" if row[campo]>=40 else "#C62828"};">{row[campo]:.0f}%</div></div>' for campo,info in DIMENSOES.items()])
            st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:10px;padding:12px 16px;margin-bottom:6px;"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;"><div><span style="color:#000000;font-weight:700;font-size:0.85rem;">{row["table_name"]}</span><span style="background:#58A6FF22;color:#1A1A1A;border-radius:3px;padding:1px 6px;font-size:0.62rem;margin-left:6px;">{row["schema_name"]}</span><span style="background:{nivel_badge}22;color:{nivel_badge};border-radius:3px;padding:1px 6px;font-size:0.62rem;margin-left:4px;">{row["nivel"]}</span></div><span style="color:{cor_q};font-size:1.1rem;font-weight:800;">{row["score_final"]:.1f}%</span></div><div style="display:grid;grid-template-columns:repeat(5,1fr);gap:6px;">{dims_html}</div></div>',unsafe_allow_html=True)
    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# 🥇 CERTIFICAÇÃO — Selos e Status
# ════════════════════════════════════════════════════════════════════
elif pagina == "🥇 Certificação":
    page_header("🥇","Certificação de Ativos de Dados","Selos de maturidade — Ouro · Prata · Bronze — com critérios transparentes.")
    st.markdown("""<div style="background:#FFFFFF99;border:1px solid #E5E5E5;border-radius:8px;padding:10px 14px;margin-bottom:16px;"><div style="color:#5C5C5C;font-size:0.78rem;line-height:1.6;">A certificação valida que um ativo atende a critérios mínimos de governança e qualidade. Os selos são concedidos após análise formal pela equipe de Governança.</div></div>""",unsafe_allow_html=True)
    SELOS={"Ouro":{"cor":"#000000","icone":"🥇","req_doc":100,"req_qual":90,"desc":"Gov. 100% + Qualidade ≥90% + todos os critérios atendidos"},"Prata":{"cor":"#8A8A8A","icone":"🥈","req_doc":80,"req_qual":70,"desc":"Gov. ≥80% + Qualidade ≥70% + Owner e Domínio definidos"},"Bronze":{"cor":"#A8743F","icone":"🥉","req_doc":60,"req_qual":40,"desc":"Documentação parcial — ativo em processo de curadoria"}}
    col_selos=st.columns(3)
    for col,(nome,info) in zip(col_selos,SELOS.items()):
        with col: st.markdown(f'<div style="background:#FFFFFF;border:2px solid {info["cor"]}44;border-radius:14px;padding:16px;text-align:center;"><div style="font-size:2rem;margin-bottom:6px;">{info["icone"]}</div><div style="color:{info["cor"]};font-weight:800;font-size:1rem;margin-bottom:4px;">Selo {nome}</div><div style="color:#5C5C5C;font-size:0.72rem;line-height:1.4;">{info["desc"]}</div><div style="background:#E5E5E5;border-radius:4px;height:1px;margin:10px 0;"></div><div style="font-size:0.65rem;color:#5C5C5C;">Gov. mín: {info["req_doc"]}% · Qual. mín: {info["req_qual"]}%</div></div>',unsafe_allow_html=True)
    section_divider("STATUS DE CERTIFICAÇÃO POR ATIVO")
    df_cert=load_cert()
    if df_cert.empty:
        if st.session_state.get("_db_err"):
            estado_vazio("⚠️","Certificação indisponível","Não foi possível conectar ao banco de dados. Os dados de certificação serão exibidos quando a conexão for restabelecida.")
        else:
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
    st.markdown("""<div style="background:#FFFFFF99;border:1px solid #E5E5E5;border-radius:8px;padding:10px 14px;margin-bottom:16px;"><div style="color:#5C5C5C;font-size:0.78rem;line-height:1.6;">A linhagem mostra como os dados fluem entre as camadas: Bronze (bruto) → Prata (tratado) → Ouro (pronto para uso).</div></div>""",unsafe_allow_html=True)
    df_lin, _lin_err = load_linhagem()
    if df_lin.empty:
        if _lin_err:
            estado_vazio("⚠️","Linhagem indisponível","Não foi possível conectar ao banco de dados. Verifique a conexão e tente novamente.")
        else:
            estado_vazio("🔗","Nenhuma linhagem cadastrada","A linhagem será exibida quando os relacionamentos entre ativos forem registrados.")
    else:
        CAMADA_COR={"bronze":"#A8743F","prata":"#8A8A8A","ouro":"#000000"}
        CAMADA_X={"bronze":0.5,"prata":2.5,"ouro":4.5}
        k1,k2,k3=st.columns(3)
        b=df_lin["origem_tabela"][df_lin["origem_schema"]=="bronze"].nunique()
        p=df_lin["origem_tabela"][df_lin["origem_schema"]=="prata"].nunique()
        o=df_lin["destino_tabela"][df_lin["destino_schema"]=="ouro"].nunique()
        with k1: st.markdown(kpi(b,"Ativos Bronze","#A8743F","🥉","Dados brutos de origem."),unsafe_allow_html=True)
        with k2: st.markdown(kpi(p,"Ativos Prata","#8A8A8A","🥈","Dados tratados."),unsafe_allow_html=True)
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
                fig_lin.add_trace(go.Scatter(x=[x0,x1],y=[y0,y1],mode="lines",line=dict(color="#CFCFCF",width=1.2),hovertext=row["descricao"],hoverinfo="text",showlegend=False))
        for chave,(x,y) in pos_nos.items():
            cam,tabela=chave.split(".",1); cor_n=CAMADA_COR.get(cam,"#5C5C5C")
            fig_lin.add_trace(go.Scatter(x=[x],y=[y],mode="markers+text",marker=dict(color=cor_n,size=16,line=dict(color="#FFFFFF",width=2)),text=[tabela],textposition="middle right",textfont=dict(color="#000000",size=10),hoverinfo="text",hovertext=chave,showlegend=False))
        for cam,(x_c,cor_c) in [("bronze",(0.5,"#A8743F")),("prata",(2.5,"#8A8A8A")),("ouro",(4.5,"#C9A227"))]:
            ys=[p[1] for k,p in pos_nos.items() if k.startswith(cam)]
            if ys: fig_lin.add_annotation(x=x_c,y=max(ys)+1.2,text=f"🏷️ {cam.upper()}",showarrow=False,font=dict(color=cor_c,size=12),bgcolor="#F5F5F5",borderpad=4)
        fig_lin.update_layout(paper_bgcolor="#FFFFFF",plot_bgcolor="#FFFFFF",height=440,margin=dict(t=30,b=20,l=20,r=200),xaxis=dict(showgrid=False,zeroline=False,showticklabels=False,range=[-0.3,7]),yaxis=dict(showgrid=False,zeroline=False,showticklabels=False))
        st.plotly_chart(fig_lin,use_container_width=True)
        section_divider("DETALHAMENTO DAS TRANSFORMAÇÕES")
        f_lin=st.selectbox("Filtrar por origem",["Todas","bronze","prata"],key="lin_cam")
        df_lf=df_lin if f_lin=="Todas" else df_lin[df_lin["origem_schema"]==f_lin]
        for _,row in df_lf.iterrows():
            cor_o2=CAMADA_COR.get(row["origem_schema"],"#5C5C5C"); cor_d2=CAMADA_COR.get(row["destino_schema"],"#5C5C5C")
            tipo_lbl="⚙️ Transformação" if row["tipo_relacao"]=="transformacao" else "📥 Consumo"
            st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:10px;padding:12px 16px;margin-bottom:6px;"><div style="display:flex;align-items:center;gap:10px;margin-bottom:5px;"><span style="background:{cor_o2}22;color:{cor_o2};border-radius:6px;padding:4px 10px;font-size:0.75rem;font-weight:700;">{row["origem_schema"]}.{row["origem_tabela"]}</span><span style="color:#5C5C5C;font-size:0.75rem;">{tipo_lbl} →</span><span style="background:{cor_d2}22;color:{cor_d2};border-radius:6px;padding:4px 10px;font-size:0.75rem;font-weight:700;">{row["destino_schema"]}.{row["destino_tabela"]}</span></div><div style="color:#5C5C5C;font-size:0.73rem;">{row["descricao"]}</div></div>',unsafe_allow_html=True)
    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# 📦 PRODUTOS DE DADOS
# ════════════════════════════════════════════════════════════════════
elif pagina == "📦 Produtos":
    page_header("📦","Produtos de Dados","Ativos empacotados e prontos para uso por áreas de negócio.")
    st.markdown("""<div style="background:#FFFFFF99;border:1px solid #E5E5E5;border-radius:8px;padding:10px 14px;margin-bottom:16px;"><div style="color:#5C5C5C;font-size:0.78rem;line-height:1.6;">Um Produto de Dados é um conjunto de ativos organizados para atender a uma necessidade específica do negócio, com finalidade, responsável e certificação definidos.</div></div>""",unsafe_allow_html=True)
    df_prod=load_produtos(); df_pat=load_produto_ativos()
    if df_prod.empty:
        if st.session_state.get("_db_err"):
            estado_vazio("⚠️","Produtos indisponíveis","Não foi possível conectar ao banco de dados. Os produtos serão exibidos quando a conexão for restabelecida.")
        else:
            estado_vazio("📦","Nenhum produto cadastrado","Os produtos de dados serão exibidos aqui quando cadastrados pela equipe de Governança.")
    else:
        ativos_total=df_pat["table_name"].nunique() if not df_pat.empty else 0
        k1,k2,k3,k4=st.columns(4)
        with k1: st.markdown(kpi(len(df_prod),"Produtos","#C9A227"),unsafe_allow_html=True)
        with k2: st.markdown(kpi(len(df_prod[df_prod["status"]=="ativo"]),"Ativos","#1E7F4F"),unsafe_allow_html=True)
        with k3: st.markdown(kpi(len(df_prod[df_prod["certificacao"]=="certificado"]),"Certificados","#C9A227"),unsafe_allow_html=True)
        with k4: st.markdown(kpi(ativos_total,"Ativos Vinculados","#1A1A1A"),unsafe_allow_html=True)
        section_divider("CATÁLOGO DE PRODUTOS")
        fp1,fp2=st.columns(2)
        with fp1: fp_dom=st.selectbox("Domínio",["Todos"]+sorted([str(d) for d in df_prod["dominio"].dropna().unique() if str(d).strip() and str(d) != "nan"]),key="fp_dom")
        with fp2: fp_st=st.selectbox("Status",["Todos","ativo","em_dev","inativo"],key="fp_st")
        df_pf=df_prod.copy()
        if fp_dom!="Todos": df_pf=df_pf[df_pf["dominio"]==fp_dom]
        if fp_st!="Todos":  df_pf=df_pf[df_pf["status"]==fp_st]
        if "prod_sel" not in st.session_state: st.session_state["prod_sel"]=None
        col_pl,col_pd=st.columns([1,2])
        CAMADA_COR2={"bronze":"#A8743F","prata":"#8A8A8A","ouro":"#000000"}
        PAPEL_COR={"Principal":"#000000","Origem":"#1A1A1A","Consumo":"#1E7F4F"}
        with col_pl:
            for _,row in df_pf.iterrows():
                cor_st={"ativo":"#1E7F4F","em_dev":"#000000","inativo":"#8A8A8A"}.get(row["status"],"#5C5C5C")
                cor_cert={"certificado":"#000000","em_analise":"#1A1A1A","pendente":"#5C5C5C"}.get(row["certificacao"],"#5C5C5C")
                ic_cert={"certificado":"🥇","em_analise":"🥈","pendente":"🥉"}.get(row["certificacao"],"")
                is_sel=st.session_state["prod_sel"]==row["produto_id"]
                ativos_p=df_pat[df_pat["produto_id"]==row["produto_id"]] if not df_pat.empty else pd.DataFrame()
                st.markdown(f'<div style="background:{"#C9A22714" if is_sel else "#FFFFFF"};border:1px solid {"#C9A227" if is_sel else "#E5E5E5"};border-radius:10px;padding:12px 14px;margin-bottom:4px;"><div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px;"><span style="color:#000000;font-weight:700;font-size:0.85rem;">{row["nome"]}</span><span style="color:{cor_st};font-size:0.65rem;font-weight:700;">● {row["status"]}</span></div><div style="color:#5C5C5C;font-size:0.72rem;margin-bottom:6px;">{row["finalidade"][:65]}...</div><div style="display:flex;gap:6px;"><span style="background:#C9A22722;color:#000000;border-radius:4px;padding:1px 6px;font-size:0.62rem;">{row["dominio"]}</span><span style="background:{cor_cert}22;color:{cor_cert};border-radius:4px;padding:1px 6px;font-size:0.62rem;">{ic_cert} {row["certificacao"]}</span><span style="background:#58A6FF22;color:#1A1A1A;border-radius:4px;padding:1px 6px;font-size:0.62rem;">{len(ativos_p)} ativos</span></div></div>',unsafe_allow_html=True)
                if st.button(f'{"▼ Fechar" if is_sel else "▶ Ver detalhes"}',key=f"psel_{row['produto_id']}",use_container_width=True):
                    st.session_state["prod_sel"]=None if is_sel else row["produto_id"]; st.rerun()
        with col_pd:
            pid=st.session_state.get("prod_sel")
            if pid:
                row_p=df_pf[df_pf["produto_id"]==pid]
                if not row_p.empty:
                    p=row_p.iloc[0]; ativos_p=df_pat[df_pat["produto_id"]==pid] if not df_pat.empty else pd.DataFrame()
                    cor_st2={"ativo":"#1E7F4F","em_dev":"#000000","inativo":"#8A8A8A"}.get(p["status"],"#5C5C5C")
                    cor_cert2={"certificado":"#000000","em_analise":"#1A1A1A","pendente":"#5C5C5C"}.get(p["certificacao"],"#5C5C5C")
                    st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:12px;padding:20px;"><div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px;"><div><div style="color:#000000;font-size:1.1rem;font-weight:800;">{p["nome"]}</div><div style="color:#5C5C5C;font-size:0.72rem;margin-top:2px;">{p["dominio"]} · Produto de Dados</div></div><span style="background:{cor_cert2}22;color:{cor_cert2};border-radius:20px;padding:3px 12px;font-size:0.72rem;font-weight:600;border:1px solid {cor_cert2}44;">{"🥇 Certificado" if p["certificacao"]=="certificado" else "🥈 Em Análise" if p["certificacao"]=="em_analise" else "🥉 Pendente"}</span></div><div style="background:#F5F5F5;border-radius:8px;padding:12px;margin-bottom:10px;"><div style="color:#5C5C5C;font-size:0.6rem;font-weight:700;text-transform:uppercase;margin-bottom:4px;">FINALIDADE</div><div style="color:#000000;font-size:0.82rem;line-height:1.5;">{p["finalidade"]}</div></div><div style="background:#F5F5F5;border-radius:8px;padding:12px;margin-bottom:10px;"><div style="color:#5C5C5C;font-size:0.6rem;font-weight:700;text-transform:uppercase;margin-bottom:4px;">DESCRIÇÃO</div><div style="color:#000000;font-size:0.82rem;line-height:1.5;">{p["descricao"]}</div></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px;"><div style="background:#F5F5F5;border-radius:8px;padding:9px;"><div style="font-size:0.6rem;color:#5C5C5C;margin-bottom:2px;">RESPONSÁVEL</div><div style="color:#000000;font-size:0.78rem;">{p["responsavel"]}</div></div><div style="background:#F5F5F5;border-radius:8px;padding:9px;"><div style="font-size:0.6rem;color:#5C5C5C;margin-bottom:2px;">STATUS</div><div style="color:{cor_st2};font-size:0.78rem;font-weight:700;">{p["status"].replace("_"," ").title()}</div></div></div>',unsafe_allow_html=True)
                    if not ativos_p.empty:
                        st.markdown('<div style="background:#F5F5F5;border-radius:8px;padding:12px;"><div style="color:#5C5C5C;font-size:0.6rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">ATIVOS VINCULADOS</div>',unsafe_allow_html=True)
                        for _,at in ativos_p.iterrows():
                            cor_cam2=CAMADA_COR2.get(at["schema_name"],"#5C5C5C"); cor_pap2=PAPEL_COR.get(at["papel"],"#5C5C5C")
                            st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid #E5E5E5;"><div><span style="color:#000000;font-size:0.75rem;">{at["table_name"]}</span><span style="background:{cor_cam2}22;color:{cor_cam2};border-radius:3px;padding:1px 5px;font-size:0.62rem;margin-left:5px;">{at["schema_name"]}</span></div><span style="background:{cor_pap2}22;color:{cor_pap2};border-radius:3px;padding:1px 7px;font-size:0.62rem;">{at["papel"]}</span></div>',unsafe_allow_html=True)
                        st.markdown('</div></div>',unsafe_allow_html=True)
                    else:
                        st.markdown('</div>',unsafe_allow_html=True)
            else:
                estado_vazio("📦","Selecione um produto","Clique em qualquer produto para ver detalhes e ativos vinculados.")
    copyright_footer()

# ════════════════════════════════════════════════════════════════════
# 🔍 BUSCA GLOBAL — Pesquisa unificada em todos os acervos
# ════════════════════════════════════════════════════════════════════
elif pagina == "🔍 Busca Global":
    st.markdown("## 🔍 Busca Global")
    st.markdown('<p style="color:#888;font-size:0.85rem;margin-top:-6px;margin-bottom:18px;">Pesquise em ativos, termos, regras, domínios e responsáveis de uma só vez.</p>', unsafe_allow_html=True)

    _bg_db_fail = bool(st.session_state.get("_db_err"))

    # ── Campo de busca ──────────────────────────────────────────────
    _busca_q = st.text_input(
        "O que você está procurando?",
        placeholder="Ex.: cliente, faturamento, lgpd, Ana Lima...",
        key="busca_global_query",
        label_visibility="collapsed",
    )

    if not _busca_q or not _busca_q.strip():
        st.markdown("""
        <div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:10px;padding:28px;text-align:center;margin-top:24px;">
            <div style="font-size:2rem;margin-bottom:8px;">🔍</div>
            <div style="color:#000000;font-weight:700;font-size:1rem;margin-bottom:4px;">Digite algo para começar</div>
            <div style="color:#555;font-size:0.82rem;">Busca em ativos do catálogo, termos do glossário, regras de negócio, domínios e produtos.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        _q = _busca_q.strip()
        _q_lower = _q.lower()

        if _bg_db_fail:
            st.warning("⚠️ Banco de dados indisponível. A busca pode estar incompleta ou retornar zero resultados.")

        # ── Carrega fontes de dados ─────────────────────────────────
        _bg_meta    = load_meta()
        _bg_gloss   = load_glossario()
        _bg_rules   = load_rules()
        _bg_produtos = load_produtos()

        # ── Resultados por fonte ────────────────────────────────────
        _resultados = []

        # 1. Ativos do catálogo (tabelas_metadata)
        if not _bg_meta.empty:
            _cols_cat = [c for c in ["table_name","descricao","dominio","schema_name","data_owner"] if c in _bg_meta.columns]
            _mask_cat = _bg_meta[_cols_cat].apply(
                lambda col: col.astype(str).str.lower().str.contains(_q_lower, na=False)
            ).any(axis=1)
            for _, row in _bg_meta[_mask_cat].head(20).iterrows():
                _resultados.append({
                    "tipo": "📊 Ativo",
                    "titulo": str(row.get("table_name","—")),
                    "subtitulo": f'{row.get("schema_name","—")} · {row.get("dominio","—")}',
                    "detalhe": str(row.get("descricao",""))[:120] or "Sem descrição.",
                    "nav_pagina": "📋 Catálogo",
                    "cor": "#1A1A1A",
                })

        # 2. Termos do glossário (business_glossary)
        if not _bg_gloss.empty:
            _cols_gl = [c for c in ["termo","definicao","dominio","responsavel","sinonimos"] if c in _bg_gloss.columns]
            _mask_gl = _bg_gloss[_cols_gl].apply(
                lambda col: col.astype(str).str.lower().str.contains(_q_lower, na=False)
            ).any(axis=1)
            for _, row in _bg_gloss[_mask_gl].head(20).iterrows():
                _resultados.append({
                    "tipo": "📖 Termo",
                    "titulo": str(row.get("termo","—")),
                    "subtitulo": f'Domínio: {row.get("dominio","—")} · Responsável: {row.get("responsavel","—")}',
                    "detalhe": str(row.get("definicao",""))[:120] or "Sem definição.",
                    "nav_pagina": "📖 Glossário",
                    "cor": "#000000",
                })

        # 3. Regras de negócio (business_rules)
        if not _bg_rules.empty:
            _cols_ru = [c for c in ["nome","descricao","dominio","responsavel","categoria"] if c in _bg_rules.columns]
            _mask_ru = _bg_rules[_cols_ru].apply(
                lambda col: col.astype(str).str.lower().str.contains(_q_lower, na=False)
            ).any(axis=1)
            for _, row in _bg_rules[_mask_ru].head(20).iterrows():
                _resultados.append({
                    "tipo": "📋 Regra",
                    "titulo": str(row.get("nome","—")),
                    "subtitulo": f'Domínio: {row.get("dominio","—")} · Cat.: {row.get("categoria","—")}',
                    "detalhe": str(row.get("descricao",""))[:120] or "Sem descrição.",
                    "nav_pagina": "📋 Catálogo",
                    "cor": "#1E7F4F",
                })

        # 4. Produtos de dados (produtos_dados)
        if not _bg_produtos.empty:
            _cols_pr = [c for c in ["nome","finalidade","descricao","dominio","responsavel"] if c in _bg_produtos.columns]
            _mask_pr = _bg_produtos[_cols_pr].apply(
                lambda col: col.astype(str).str.lower().str.contains(_q_lower, na=False)
            ).any(axis=1)
            for _, row in _bg_produtos[_mask_pr].head(10).iterrows():
                _resultados.append({
                    "tipo": "📦 Produto",
                    "titulo": str(row.get("nome","—")),
                    "subtitulo": f'Domínio: {row.get("dominio","—")} · {row.get("status","—")}',
                    "detalhe": str(row.get("finalidade",""))[:120] or str(row.get("descricao",""))[:120] or "Sem descrição.",
                    "nav_pagina": "📦 Produtos",
                    "cor": "#B26A00",
                })

        # ── Exibe resultados ────────────────────────────────────────
        _total = len(_resultados)
        if _total == 0:
            estado_vazio("🔍", f'Nenhum resultado para "{_q}"',
                         "Tente outros termos ou verifique a ortografia. A busca cobre ativos, termos, regras e produtos.")
        else:
            st.markdown(
                f'<div style="color:#888;font-size:0.8rem;margin-bottom:14px;">'
                f'<span style="color:#000000;font-weight:700;">{_total}</span> resultado{"s" if _total!=1 else ""} '
                f'para <em>"{_q}"</em></div>',
                unsafe_allow_html=True
            )

            # Filtro por tipo
            _tipos_disp = sorted(set(r["tipo"] for r in _resultados))
            _tipo_sel = st.selectbox("Filtrar por tipo:", ["Todos"] + _tipos_disp, key="busca_tipo_filtro")
            if _tipo_sel != "Todos":
                _resultados = [r for r in _resultados if r["tipo"] == _tipo_sel]

            # Cards de resultado
            for _idx_res, _res in enumerate(_resultados):
                _nav_lbl = _res["nav_pagina"]
                st.markdown(f"""
                <div style="background:#FFFFFF;border:1px solid #E5E5E5;border-radius:10px;
                            padding:14px 18px;margin-bottom:8px;
                            border-left:3px solid {_res['cor']};">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                        <span style="background:{_res['cor']}22;color:{_res['cor']};
                                     border-radius:4px;padding:2px 8px;font-size:0.67rem;
                                     font-weight:700;">{_res['tipo']}</span>
                        <span style="color:#000000;font-weight:700;font-size:0.92rem;">{_res['titulo']}</span>
                    </div>
                    <div style="color:#888;font-size:0.72rem;margin-bottom:6px;">{_res['subtitulo']}</div>
                    <div style="color:#5C5C5C;font-size:0.78rem;line-height:1.5;">{_res['detalhe']}</div>
                </div>
                """, unsafe_allow_html=True)
                # Botão para navegar à página do resultado
                if st.button(f"Ir para {_nav_lbl}", key=f"busca_nav_{_idx_res}",
                             use_container_width=False):
                    st.session_state["pagina"] = _nav_lbl
                    st.rerun()

    copyright_footer()

# ── Botões JS-bridge (govnav) — renderizados no final para não flash no topo ──
# O JS da topbar clica estes botões; o CSS+JS os oculta antes de pintar.
_topbar_nav_map = [
    ("descobrir", "📋 Catálogo"),
    ("entender",  "📖 Glossário"),
    ("confiar",   "🏆 Qualidade"),
    ("agir",      "⚡ Meu Espaço"),
    ("decidir",   "📊 Indicadores"),
    ("busca",     "🔍 Busca Global"),
]
for _nav_k, _nav_p in _topbar_nav_map:
    if st.button(f"govnav-{_nav_k}", key=f"topnav-{_nav_k}"):
        st.session_state["pagina"] = _nav_p
        st.rerun()
