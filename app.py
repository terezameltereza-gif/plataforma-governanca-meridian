# ════════════════════════════════════════════════════════════════════
# CSS DO MENU — botões de navegação sem duplicação
# ════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* Remove estilo dourado dos botões de navegação */
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
    transition: all 0.15s !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: #161B22 !important;
    color: #E6EDF3 !important;
}
/* Botão ativo — identificado por data-active */
section[data-testid="stSidebar"] .stButton > button[data-active="true"] {
    background: #C9A22718 !important;
    color: #C9A227 !important;
    font-weight: 700 !important;
    border-left: 3px solid #C9A227 !important;
    padding-left: 7px !important;
}
/* Botão Sair */
section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    background: #161B22 !important;
    color: #8B949E !important;
    border: 1px solid #30363D !important;
    border-radius: 6px !important;
    margin-top: 4px !important;
}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════
MENU = {
    "PESSOAL":        ["⚡ Meu Espaço"],
    "DESCOBERTA":     ["🏠 Início", "📋 Catálogo", "📖 Glossário", "🏛️ Domínios"],
    "CONFIABILIDADE": ["🛡️ Scorecard"],
    "OPERAÇÃO":       ["✏️ Curadoria", "🕐 Auditoria"],
}

with st.sidebar:
    # Logo
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

    # ── Login ────────────────────────────────────────────────────────
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

    # ── Card do usuário ──────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:#161B22;border:1px solid #30363D;border-radius:8px;
                padding:8px 10px;margin-bottom:10px;">
        <div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;
                    letter-spacing:1px;">Usuário logado</div>
        <div style="font-weight:700;color:#E6EDF3;font-size:0.82rem;">{u['nome']}</div>
        <div style="color:{cor};font-size:0.72rem;font-weight:600;">
            {PERFIL_LABEL[perfil]}</div>
    </div>""", unsafe_allow_html=True)

    # ── Itens de navegação ───────────────────────────────────────────
    # ════════════════════════════════════════════════════════════════════
# CSS DO MENU — botões de navegação sem duplicação
# ════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* Remove estilo dourado dos botões de navegação */
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
    transition: all 0.15s !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: #161B22 !important;
    color: #E6EDF3 !important;
}
/* Botão ativo — identificado por data-active */
section[data-testid="stSidebar"] .stButton > button[data-active="true"] {
    background: #C9A22718 !important;
    color: #C9A227 !important;
    font-weight: 700 !important;
    border-left: 3px solid #C9A227 !important;
    padding-left: 7px !important;
}
/* Botão Sair */
section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    background: #161B22 !important;
    color: #8B949E !important;
    border: 1px solid #30363D !important;
    border-radius: 6px !important;
    margin-top: 4px !important;
}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════
MENU = {
    "PESSOAL":        ["⚡ Meu Espaço"],
    "DESCOBERTA":     ["🏠 Início", "📋 Catálogo", "📖 Glossário", "🏛️ Domínios"],
    "CONFIABILIDADE": ["🛡️ Scorecard"],
    "OPERAÇÃO":       ["✏️ Curadoria", "🕐 Auditoria"],
}

with st.sidebar:
    # Logo
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

    # ── Login ────────────────────────────────────────────────────────
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

    # ── Card do usuário ──────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:#161B22;border:1px solid #30363D;border-radius:8px;
                padding:8px 10px;margin-bottom:10px;">
        <div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;
                    letter-spacing:1px;">Usuário logado</div>
        <div style="font-weight:700;color:#E6EDF3;font-size:0.82rem;">{u['nome']}</div>
        <div style="color:{cor};font-size:0.72rem;font-weight:600;">
            {PERFIL_LABEL[perfil]}</div>
    </div>""", unsafe_allow_html=True)

    # ── Itens de navegação ───────────────────────────────────────────
    for secao, itens in MENU.items():
        # Label da seção
        st.markdown(
            f'<div style="font-size:0.58rem;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:1.5px;color:#484F58;padding:8px 10px 3px;">'
            f'{secao}</div>',
            unsafe_allow_html=True)

        for item in itens:
            is_active = st.session_state["pagina"] == item

            if is_active:
                # Item ativo: fundo dourado + borda esquerda dourada
                st.markdown(f"""
                <div style="background:#C9A22718;border-left:3px solid #C9A227;
                            border-radius:0 6px 6px 0;padding:6px 10px 6px 9px;
                            font-size:0.82rem;font-weight:700;color:#C9A227;
                            margin-bottom:1px;user-select:none;">
                    {item}
                </div>""", unsafe_allow_html=True)
            else:
                # Item inativo: botão nativo estilizado
                if st.button(item, key=f"nav_{item}",
                             use_container_width=True):
                    st.session_state["pagina"] = item
                    for k in ["gid_sel","cat_sel","dom_sel","sc_pilar"]:
                        st.session_state.pop(k, None)
                    st.rerun()

    # ── Sair ─────────────────────────────────────────────────────────
    st.markdown(
        '<div style="height:1px;background:#30363D;margin:10px 0 8px;"></div>',
        unsafe_allow_html=True)
    if st.button("↩ Sair", key="logout",
                 use_container_width=True):
        st.session_state["usuario"] = None
        st.rerun()

# ── Variáveis globais de sessão ──────────────────────────────────────
pagina       = st.session_state.get("pagina", "🏠 Início")
usuario      = st.session_state["usuario"]
u            = USUARIOS[usuario]
perfil       = u["perfil"]
is_curador   = perfil in ["curador", "aprovador"]
is_aprovador = perfil == "aprovador"
