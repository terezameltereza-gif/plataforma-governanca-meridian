"""Telas do módulo Valor dos Dados (etapa 1: consulta).

Lê exclusivamente as tabelas vd_* e o catálogo existente. Nenhum número é
fixo no código: sem registro, a tela mostra o estado vazio com o próximo passo.
Todo texto vindo do banco passa por html.escape antes de ir para a página.

O módulo só aparece quando a configuração VD_HABILITADO for verdadeira e a
estrutura estiver instalada (vd_controle_versao com a versão esperada).
"""
from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Callable, Optional

import pandas as pd
import streamlit as st

SCHEMA = "meridian_governanca"
VERSAO_ESTRUTURA = "v3"
DESTINO = "💠 Valor dos Dados"

ROTULO_STATUS = {
    "identificada": "Identificada", "em_analise": "Em análise", "aprovada": "Aprovada", "planejada": "Planejada",
    "em_execucao": "Em execução", "em_validacao": "Em validação", "concluida": "Concluída", "cancelada": "Cancelada",
}
ETAPAS = ["identificada", "em_analise", "aprovada", "planejada", "em_execucao", "em_validacao", "concluida"]
ROTULO_NATUREZA = {"nao_cadastrado": "Não cadastrado", "nao_identificado": "Não identificado",
                   "nao_conforme": "Não conforme", "nao_aplicavel": "Não aplicável"}
ROTULO_VALIDACAO = {"pendente": "Pendente de validação", "validado": "Validado", "rejeitado": "Rejeitado"}
ROTULO_PRIORIDADE = {"critica": "Crítica", "alta": "Alta", "media": "Média", "baixa": "Baixa"}
ROTULO_ESTAGIO = {"estimado": "Estimado", "em_validacao": "Em validação", "validado": "Validado"}
ROTULO_ENTRADA = {
    "saida": "Saída", "intermediario": "Intermediário", "fonte": "Fonte", "nao_aplicavel": "Não aplicável",
    "0": "Nenhum ativo a jusante", "1-2": "1 a 2 ativos a jusante", "3-5": "3 a 5 ativos a jusante",
    "6+": "6 ou mais ativos a jusante", "nao_determinada": "Não determinada",
    "baixo": "Baixo", "medio": "Médio", "alto": "Alto", "nao_informado": "Não informado",
    **{k: v for k, v in [("alta", "Alta"), ("media", "Média"), ("baixa", "Baixa")]},
}
ROTULO_ACAO = {"criacao": "Criação", "edicao": "Edição", "transicao": "Mudança de etapa", "validacao": "Validação",
               "evidencia": "Evidência", "cancelamento": "Cancelamento", "reincidencia": "Reincidência",
               "resolucao": "Resolução", "comentario": "Comentário"}
ROTULO_PAPEL = {"principal": "principal", "complementar": "complementar", "saida": "saída", "intermediario": "intermediário",
                "fonte": "fonte"}
ROTULO_TIPO_MEDICAO = {"linha_base": "Linha de base", "acompanhamento": "Acompanhamento"}
ABERTAS = {"identificada", "em_analise", "aprovada", "planejada", "em_execucao", "em_validacao"}

CSS = """
<style>
.vd-lbl{font-size:.7rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--gv-ink2,#5C5C5C);}
.vd-num{font-size:1.85rem;font-weight:750;letter-spacing:-.02em;margin-top:6px;font-variant-numeric:tabular-nums;}
.vd-sub{font-size:.78rem;color:var(--gv-ink2,#5C5C5C);margin-top:4px;line-height:1.45;}
.vd-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:6px 0 14px;}
.vd-card{background:#FFF;border:1px solid #EAEAEA;border-radius:12px;padding:16px 18px;box-sizing:border-box;}
.vd-row{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;padding:12px 0;border-bottom:1px solid #F1F1F1;}
.vd-row:last-child{border-bottom:none;}
.vd-tag{display:inline-block;font-size:.66rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase;border-radius:6px;padding:3px 8px;}
.vd-t-escuro{background:#000;color:#C9A227;} .vd-t-claro{background:#F3F3F3;color:#1A1A1A;}
.vd-t-alerta{background:#FFF4E0;color:#7A4600;} .vd-t-borda{border:1px solid #000;color:#000;}
.vd-ok{color:#1E7F4F;font-weight:600;font-size:.8rem;} .vd-pend{color:#5C5C5C;font-size:.8rem;}
.vd-mono{font-family:ui-monospace,Menlo,monospace;font-size:.8rem;}
.vd-tree{margin-left:18px;padding-left:16px;border-left:2px solid #EFEFEF;display:flex;flex-direction:column;gap:8px;margin-top:8px;}
.vd-no{border:1px solid #EFEFEF;border-radius:10px;padding:10px 12px;background:#FFF;font-size:.86rem;}
.vd-tp{font-size:.64rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#8C6F12;margin-right:8px;}
.vd-lacuna{font-size:.74rem;color:#9A5B00;background:#FFF4E0;border-radius:6px;padding:1px 7px;margin-left:4px;}
.vd-etapas{display:flex;flex-wrap:wrap;gap:6px;align-items:center;font-size:.75rem;color:#8A8A8A;margin:4px 0 10px;}
.vd-etapas b{color:#000;}
.vd-vazio{border:1px dashed #D0D0D0;border-radius:12px;padding:18px 20px;font-size:.88rem;color:#3A3A3A;line-height:1.55;}
@media (max-width:1024px){.vd-grid{grid-template-columns:repeat(2,minmax(0,1fr));}}
@media (max-width:640px){.vd-grid{grid-template-columns:1fr;}}
</style>"""


def tem(v) -> bool:
    return v is not None and not (isinstance(v, float) and pd.isna(v)) and str(v) != ""


NOMES: dict = {}


def pessoa(email) -> str:
    """Nome de exibição quando o e-mail pertence a um usuário conhecido da plataforma."""
    return e(NOMES.get(email, email))


def e(v) -> str:
    """Texto do banco para HTML."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return html.escape(str(v))


def _fmt_num(v, unidade: str = "") -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    f = float(v)
    txt = f"{f:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if "," in txt:
        txt = txt.rstrip("0").rstrip(",")
    return f"{txt} {e(unidade)}".strip()


def _data(v) -> str:
    try:
        return pd.to_datetime(v).strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return "—"


def vazio(texto: str) -> None:
    st.markdown(f'<div class="vd-vazio">{texto}</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
# Acesso aos dados (somente leitura nesta etapa)
# ════════════════════════════════════════════════════════════════════
@dataclass
class Dados:
    qry: Callable[[str], tuple]

    def _df(self, sql: str) -> pd.DataFrame:
        df, err = self.qry(sql)
        if err:
            raise ErroLeitura(err)
        return df if df is not None else pd.DataFrame()

    def tabela(self, nome: str, ordem: Optional[str] = None) -> pd.DataFrame:
        return self._df(f"SELECT * FROM {SCHEMA}.{nome}" + (f" ORDER BY {ordem}" if ordem else ""))

    def ultima_execucao(self) -> pd.DataFrame:
        return self._df(f"SELECT * FROM {SCHEMA}.vd_execucoes_diagnostico ORDER BY iniciado_em DESC LIMIT 1")

    def ocorrencias_por_resultado(self, execucao_id: str) -> dict:
        df = self._df(f"SELECT resultado, regra_codigo, motivo_nao_avaliada, COUNT(*) AS n "
                      f"FROM {SCHEMA}.vd_achados_ocorrencias WHERE execucao_id = '{_lit(execucao_id)}' "
                      f"GROUP BY resultado, regra_codigo, motivo_nao_avaliada")
        return df

    def historico(self, entidade_tipo: str, entidade_id: str) -> pd.DataFrame:
        return self._df(f"SELECT * FROM {SCHEMA}.vd_historico WHERE entidade_tipo = '{_lit(entidade_tipo)}' "
                        f"AND entidade_id = '{_lit(entidade_id)}' ORDER BY executado_em DESC")

    def evidencias(self, entidade_tipo: str, entidade_id: str) -> pd.DataFrame:
        return self._df(f"SELECT * FROM {SCHEMA}.vd_evidencias WHERE entidade_tipo = '{_lit(entidade_tipo)}' "
                        f"AND entidade_id = '{_lit(entidade_id)}' ORDER BY registrado_em DESC")

    def catalogo_ativos(self) -> pd.DataFrame:
        return self._df(f"SELECT * FROM {SCHEMA}.tabelas_metadata")


class ErroLeitura(RuntimeError):
    pass


def _lit(v: str) -> str:
    """Identificadores internos (UUIDs gerados pelo módulo) em literal SQL; aspas são recusadas."""
    s = str(v)
    if "'" in s or "\\" in s:
        raise ValueError("identificador inválido")
    return s


def estado_instalacao(qry, habilitado_cfg: bool) -> tuple[bool, str]:
    """(disponível, motivo). Não lança: a navegação nunca quebra por causa do módulo."""
    if not habilitado_cfg:
        return False, "desabilitado"
    df, err = qry(f"SELECT versao FROM {SCHEMA}.vd_controle_versao WHERE versao = '{VERSAO_ESTRUTURA}'")
    if err:
        return False, "estrutura não encontrada ou banco indisponível"
    if df is None or df.empty:
        return False, f"versão {VERSAO_ESTRUTURA} da estrutura não registrada"
    return True, ""


# ════════════════════════════════════════════════════════════════════
# Página do módulo
# ════════════════════════════════════════════════════════════════════
def pagina(qry, usuario: str, perfil: str, disponivel: bool, motivo: str) -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown("""
<div style="margin:4px 0 14px">
  <div class="vd-lbl" style="color:#8C6F12">Data Intelligence &amp; Governance</div>
  <h1 style="margin:6px 0 4px;font-size:1.9rem;font-weight:800;letter-spacing:-.02em">Valor dos Dados</h1>
  <p style="margin:0;color:#5C5C5C;font-size:.92rem">Do objetivo de negócio ao benefício validado: dados que sustentam o processo, achados, intervenções e resultados.</p>
</div>""", unsafe_allow_html=True)
    if not disponivel:
        vazio(f"O módulo não está disponível neste ambiente ({e(motivo)}). "
              "A instalação segue o roteiro de homologação e depende de aprovação.")
        return
    d = Dados(qry)
    try:
        abas = st.tabs(["Visão Executiva", "Objetivos e Desafios", "Mapa de Dependência",
                        "Diagnóstico", "Plano de Intervenções", "Resultados e Benefícios"])
        objetivos = d.tabela("vd_objetivos", "criado_em")
        intervencoes = d.tabela("vd_intervencoes", "pontuacao_total DESC, aberta_em")
        achados = d.tabela("vd_achados", "ultima_deteccao_em DESC")
        beneficios = d.tabela("vd_beneficios", "criado_em DESC")
        with abas[0]:
            _visao_executiva(d, objetivos, achados, intervencoes, beneficios)
        with abas[1]:
            _objetivos(d, objetivos)
        with abas[2]:
            _mapa(d, objetivos)
        with abas[3]:
            _diagnostico(d, achados, intervencoes)
        with abas[4]:
            _intervencoes(d, intervencoes, achados, perfil)
        with abas[5]:
            _resultados(d, beneficios)
    except ErroLeitura as exc:
        vazio("Não foi possível ler os dados do módulo agora. Nenhuma informação foi alterada. "
              f"<span class='vd-sub'>Detalhe: {e(str(exc)[:160])}</span>")


def _cartao(rotulo: str, numero, sub: str = "", destaque: bool = False) -> str:
    borda = "border-color:#E9D79A;" if destaque else ""
    return (f'<div class="vd-card" style="{borda}"><div class="vd-lbl">{rotulo}</div>'
            f'<div class="vd-num">{numero}</div><div class="vd-sub">{sub}</div></div>')


def _contar(df: pd.DataFrame, col: str, valor) -> int:
    return int((df[col] == valor).sum()) if not df.empty and col in df.columns else 0


def _visao_executiva(d: Dados, objetivos, achados, intervencoes, beneficios) -> None:
    if objetivos.empty:
        vazio("Nenhum objetivo cadastrado. O ciclo começa em <b>Objetivos e Desafios</b>: registre o objetivo do piloto, "
              "o processo relacionado e os indicadores.")
        return
    ativos = objetivos[objetivos["status"] == "ativo"] if "status" in objetivos.columns else objetivos
    abertos = achados[achados["situacao"] == "aberto"] if not achados.empty else achados
    nat = " · ".join(f"{_contar(abertos, 'natureza', k)} {v.lower()}" for k, v in ROTULO_NATUREZA.items()
                     if k != "nao_aplicavel")
    n_abertas = int(intervencoes["status"].isin(ABERTAS).sum()) if not intervencoes.empty else 0
    n_concl = _contar(intervencoes, "status", "concluida")
    n_crit = int(((intervencoes["prioridade"] == "critica") & intervencoes["status"].isin(ABERTAS)).sum()) \
        if not intervencoes.empty else 0
    ben = " · ".join(f"{_contar(beneficios, 'estagio', k)} {v.lower()}" for k, v in ROTULO_ESTAGIO.items())
    st.markdown('<div class="vd-grid">'
                + _cartao("Objetivos ativos", len(ativos))
                + _cartao("Achados abertos", len(abertos), nat)
                + _cartao("Intervenções abertas", n_abertas, f"{n_concl} concluída(s) · {n_crit} crítica(s)")
                + _cartao("Benefícios", len(beneficios), ben, destaque=True)
                + "</div>", unsafe_allow_html=True)

    indicadores = d.tabela("vd_indicadores")
    medicoes = d.tabela("vd_medicoes", "data_referencia")
    for _, o in ativos.iterrows():
        inds = indicadores[indicadores["objetivo_id"] == o["objetivo_id"]] if not indicadores.empty else indicadores
        blocos = []
        for _, i in inds.sort_values("papel", ascending=False).iterrows() if not inds.empty else []:
            m = medicoes[(medicoes["indicador_id"] == i["indicador_id"]) & (medicoes["status_validacao"] == "validado")] \
                if not medicoes.empty else medicoes
            base = m[m["tipo"] == "linha_base"].tail(1) if not m.empty else m
            atual = m[m["tipo"] == "acompanhamento"].tail(1) if not m.empty else m
            vb = _fmt_num(base["valor"].iloc[0], i.get("unidade")) if not base.empty else "—"
            va = _fmt_num(atual["valor"].iloc[0], i.get("unidade")) if not atual.empty else "—"
            nota = "" if not atual.empty else '<div class="vd-sub">Sem medição de acompanhamento validada</div>'
            blocos.append(f'<div class="vd-no"><div class="vd-lbl">Indicador {e(i.get("papel"))}</div>'
                          f'<div style="font-weight:650;margin-top:4px">{e(i["nome"])}</div>'
                          f'<div style="display:flex;gap:18px;margin-top:8px;flex-wrap:wrap">'
                          f'<div><div class="vd-sub">Linha de base</div><div style="font-size:1.3rem;font-weight:750">{vb}</div></div>'
                          f'<div><div class="vd-sub">Medição mais recente</div><div style="font-size:1.3rem;font-weight:750">{va}</div></div>'
                          f'</div>{nota}</div>')
        corpo = "".join(blocos) or '<div class="vd-sub">Nenhum indicador cadastrado para este objetivo.</div>'
        st.markdown(f'<div class="vd-card" style="margin-bottom:12px"><div style="font-weight:700;font-size:1rem">{e(o["nome"])}</div>'
                    f'<div class="vd-sub">Prioridade {e(ROTULO_PRIORIDADE.get(o.get("prioridade"), o.get("prioridade")))}</div>'
                    f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:12px">{corpo}</div>'
                    f'<div class="vd-sub" style="margin-top:10px">Resultado associado às intervenções; não comprova causalidade exclusiva.</div></div>',
                    unsafe_allow_html=True)


def _rastro(d: Dados, tipo: str, ident: str) -> str:
    h = d.historico(tipo, ident)
    if h.empty:
        return '<div class="vd-sub">Sem registros no histórico.</div>'
    linhas = "".join(f'<li><span style="color:#5C5C5C">{_data(r["executado_em"])}</span> · {e(ROTULO_ACAO.get(r["acao"], r["acao"]))}'
                     f'{" · " + e(ROTULO_STATUS.get(r["status_novo"], r["status_novo"])) if tem(r.get("status_novo")) else ""}'
                     f' · {pessoa(r["executado_por"])} ({e(r["perfil"])})'
                     f'{"<br><span class=vd-sub>" + e(r["comentario"]) + "</span>" if tem(r.get("comentario")) else ""}</li>'
                     for _, r in h.head(8).iterrows())
    return f'<ul style="margin:6px 0 0;padding-left:16px;font-size:.82rem;line-height:1.7">{linhas}</ul>'


def _objetivos(d: Dados, objetivos) -> None:
    if objetivos.empty:
        vazio("Nenhum objetivo ou desafio cadastrado. O cadastro fica disponível a curadores e aprovadores na próxima etapa.")
        return
    processos = d.tabela("vd_processos")
    indicadores = d.tabela("vd_indicadores")
    for _, o in objetivos.iterrows():
        val = ROTULO_VALIDACAO.get(o["status_validacao"], o["status_validacao"])
        with st.expander(f'{o["nome"]} · {ROTULO_PRIORIDADE.get(o.get("prioridade"), "")} · {val}',
                         expanded=len(objetivos) == 1):
            procs = processos[processos["objetivo_id"] == o["objetivo_id"]] if not processos.empty else processos
            inds = indicadores[indicadores["objetivo_id"] == o["objetivo_id"]] if not indicadores.empty else indicadores
            st.markdown(
                f'<div class="vd-sub">{e(o.get("tipo", "")).capitalize()} · {e(o.get("area_negocio"))} · negócio: {pessoa(o.get("resp_negocio"))}'
                f' · acompanhamento: {pessoa(o.get("resp_acompanhamento"))}</div>'
                f'<div style="margin-top:10px;font-size:.88rem;line-height:1.55">{e(o.get("descricao"))}</div>'
                f'<div style="margin-top:10px"><span class="vd-lbl">Critério de sucesso</span>'
                f'<div style="font-size:.88rem;margin-top:4px">{e(o.get("criterio_sucesso")) or "—"}</div></div>'
                f'<div style="margin-top:10px"><span class="vd-lbl">Processos</span><div style="font-size:.86rem;margin-top:4px">'
                + ("<br>".join(f'{e(p["nome"])} · criticidade {e(p.get("criticidade"))} · {pessoa(p.get("resp_processo"))}'
                               for _, p in procs.iterrows()) or "Nenhum processo relacionado")
                + '</div></div><div style="margin-top:10px"><span class="vd-lbl">Indicadores</span><div style="font-size:.86rem;margin-top:4px">'
                + ("<br>".join(f'{e(i["nome"])} · {e(i.get("papel"))} · {e(i.get("unidade"))} · {e(i.get("sentido_melhora"))}'
                               for _, i in inds.iterrows()) or "Nenhum indicador cadastrado")
                + f'</div></div><div style="margin-top:12px"><span class="vd-lbl">Rastreabilidade</span>'
                  f'<div class="vd-sub">Origem: {e(o.get("origem"))} · criado por {pessoa(o.get("criado_por"))} em {_data(o.get("criado_em"))} · versão {e(o.get("versao"))}</div>'
                + _rastro(d, "objetivo", o["objetivo_id"]) + "</div>", unsafe_allow_html=True)


def _mapa(d: Dados, objetivos) -> None:
    vinculos = d.tabela("vd_vinculos")
    if objetivos.empty or vinculos.empty:
        vazio("Nenhum dado vinculado. Os vínculos usam identificadores reais do catálogo e entram como pendentes de validação.")
        return
    processos = d.tabela("vd_processos")
    cat = d.catalogo_ativos()
    chave_cat = {}
    if not cat.empty and {"schema_name", "table_name"} <= set(cat.columns):
        for _, c in cat.iterrows():
            chave_cat[(str(c["schema_name"]).lower(), str(c["table_name"]).lower())] = c
    for _, o in objetivos.iterrows():
        procs = processos[processos["objetivo_id"] == o["objetivo_id"]] if not processos.empty else processos
        partes = [f'<div class="vd-no" style="border-color:#E9D79A;background:#FFFBEF"><span class="vd-tp">Objetivo</span><b>{e(o["nome"])}</b></div>']
        for _, p in procs.iterrows():
            filhos = []
            vs = vinculos[(vinculos["origem_tipo"] == "processo") & (vinculos["origem_id"] == p["processo_id"])]
            for _, v in vs.iterrows():
                filhos.append(_no_vinculo(v, chave_cat))
            partes.append(f'<div class="vd-tree"><div class="vd-no"><span class="vd-tp">Processo</span><b>{e(p["nome"])}</b> '
                          f'<span class="vd-sub">{pessoa(p.get("resp_processo"))}</span></div>'
                          f'<div class="vd-tree">{"".join(filhos) or "<div class=vd-sub>Nenhum vínculo neste processo.</div>"}</div></div>')
        st.markdown('<div class="vd-card" style="margin-bottom:12px">' + "".join(partes) + "</div>", unsafe_allow_html=True)
    st.markdown('<div class="vd-sub">Lacuna é ausência de informação no catálogo, não falha comprovada. '
                'Owner, Steward e classificação são lidos do catálogo, não copiados.</div>', unsafe_allow_html=True)


def _no_vinculo(v, chave_cat) -> str:
    val = '<span class="vd-ok">vínculo validado</span>' if v["status_validacao"] == "validado" \
        else f'<span class="vd-pend">{e(ROTULO_VALIDACAO.get(v["status_validacao"], v["status_validacao"]))}</span>'
    papel = f' · {e(ROTULO_PAPEL.get(v.get("papel_no_processo"), v.get("papel_no_processo")))}' if tem(v.get("papel_no_processo")) else ""
    nome = f'{e(v.get("ref_schema"))}.{e(v.get("ref_nome"))}' if v.get("ref_schema") else e(v.get("ref_nome") or v.get("ref_id"))
    detalhe = ""
    if v["ref_tipo"] == "ativo":
        c = chave_cat.get((str(v.get("ref_schema")).lower(), str(v.get("ref_nome")).lower()))
        if c is None:
            detalhe = '<span class="vd-lacuna">ativo não localizado no catálogo</span>'
        else:
            itens = []
            for campo, rotulo in (("data_owner", "Owner"), ("data_steward", "Steward"), ("classificacao", "Classificação")):
                if campo not in c.index:
                    continue
                valor = c.get(campo)
                itens.append(f"{rotulo}: {pessoa(valor) if campo != 'classificacao' else e(valor)}" if tem(valor)
                             else f'<span class="vd-lacuna">{rotulo.lower()} não cadastrado</span>')
            detalhe = " · ".join(itens)
    return (f'<div class="vd-no"><span class="vd-tp">{e(v["ref_tipo"])}{papel}</span>'
            f'<span class="vd-mono">{nome}</span> {val}<div class="vd-sub" style="margin-top:6px">{detalhe}</div></div>')


def _diagnostico(d: Dados, achados, intervencoes) -> None:
    ex = d.ultima_execucao()
    if ex.empty:
        vazio("Nenhum diagnóstico executado. A execução fica disponível a curadores na próxima etapa.")
    else:
        x = ex.iloc[0]
        oc = d.ocorrencias_por_resultado(x["execucao_id"])
        tot = oc.groupby("resultado")["n"].sum().to_dict() if not oc.empty else {}
        st.markdown(
            f'<div class="vd-card" style="margin-bottom:12px"><div class="vd-lbl">Última execução · regras {e(x["versao_regras"])}</div>'
            f'<div style="font-weight:700;margin-top:6px">{_data(x["iniciado_em"])} · {pessoa(x["executado_por"])} · {e(x["status"])}</div>'
            f'<div class="vd-sub">{e(x.get("vinculos_analisados"))} vínculos analisados</div>'
            f'<div class="vd-grid" style="grid-template-columns:repeat(3,minmax(0,1fr));margin-top:10px">'
            + _cartao("Dispararam", int(tot.get("disparou", 0)))
            + _cartao("Não dispararam", int(tot.get("nao_disparou", 0)))
            + _cartao("Não avaliadas", int(tot.get("nao_avaliada", 0)))
            + "</div></div>", unsafe_allow_html=True)
        nao_av = oc[oc["resultado"] == "nao_avaliada"] if not oc.empty else oc
        if not nao_av.empty:
            st.markdown('<div class="vd-lbl" style="margin:6px 0">Não avaliadas nesta execução</div>'
                        + "".join(f'<div class="vd-sub">{e(r["regra_codigo"])} em {int(r["n"])} vínculo(s) · {e(r["motivo_nao_avaliada"])}</div>'
                                  for _, r in nao_av.iterrows()), unsafe_allow_html=True)
    if achados.empty:
        return
    com_interv = set(intervencoes["achado_id"]) if not intervencoes.empty else set()
    filtros = (["Todos"] + [v for k, v in ROTULO_NATUREZA.items() if k != "nao_aplicavel"]
               + ["Oportunidades (validados sem intervenção)"])
    escolha = st.radio("Filtrar achados", filtros, horizontal=True, key="vd_filtro_achados", label_visibility="collapsed")
    df = achados[achados["situacao"] == "aberto"]
    if escolha.startswith("Oportunidades"):
        df = df[(df["status_validacao"] == "validado") & (~df["achado_id"].isin(com_interv))]
    elif escolha != "Todos":
        df = df[df["natureza"] == {v: k for k, v in ROTULO_NATUREZA.items()}[escolha]]
    if df.empty:
        vazio("Nenhum achado aberto neste filtro.")
        return
    vinculos = d.tabela("vd_vinculos")
    nomes = {r["vinculo_id"]: (f'{r.get("ref_schema")}.{r.get("ref_nome")}' if r.get("ref_schema") else r.get("ref_nome"))
             for _, r in vinculos.iterrows()} if not vinculos.empty else {}
    regras = d.tabela("vd_regras_diagnostico")
    nome_regra = ({(r["regra_codigo"], r["versao_regras"]): r["nome"] for _, r in regras.iterrows()}
                  if not regras.empty else {})
    linhas = []
    for _, a in df.iterrows():
        tag = {"nao_conforme": "vd-t-escuro", "nao_identificado": "vd-t-alerta"}.get(a["natureza"], "vd-t-claro")
        if a["vinculo_id"] in nomes and a["natureza"] != "nao_aplicavel":
            alvo = f'<span class="vd-mono">{e(nomes[a["vinculo_id"]])}</span>'
        else:
            alvo = e(nomes.get(a["vinculo_id"], ""))
        situacao = (f'<span class="vd-ok">Validado{" · intervenção aberta" if a["achado_id"] in com_interv else ""}</span>'
                    if a["status_validacao"] == "validado"
                    else f'<span class="vd-pend">{e(ROTULO_VALIDACAO.get(a["status_validacao"]))}</span>')
        linhas.append(f'<div class="vd-row"><div style="flex:1 1 420px;min-width:0">'
                      f'<span class="vd-tag {tag}">{e(ROTULO_NATUREZA.get(a["natureza"]))}</span> '
                      f'<b>{e(a["regra_codigo"])} · {e(nome_regra.get((a["regra_codigo"], a.get("versao_regras")), ""))}</b><div class="vd-sub">{alvo} · fato: {e(a["evidencia_fato"])}'
                      f'{" · valor observado: " + e(a["valor_observado"]) if tem(a.get("valor_observado")) else ""}</div></div>'
                      f'<div>{situacao}</div></div>')
    st.markdown('<div class="vd-card">' + "".join(linhas) + "</div>", unsafe_allow_html=True)


def _intervencoes(d: Dados, intervencoes, achados, perfil: str) -> None:
    if intervencoes.empty:
        vazio("Nenhuma intervenção aberta. Intervenções nascem de achados validados.")
        return
    so_abertas = st.toggle("Somente abertas", value=True, key="vd_so_abertas")
    df = intervencoes[intervencoes["status"].isin(ABERTAS)] if so_abertas else intervencoes
    if df.empty:
        vazio("Nenhuma intervenção aberta.")
        return
    opcoes = {r["intervencao_id"]: f'{r["codigo"]} · {r["titulo"]} · {ROTULO_PRIORIDADE.get(r["prioridade"], "")} '
                                   f'· {ROTULO_STATUS.get(r["status"], r["status"])}' for _, r in df.iterrows()}
    sel = st.selectbox("Intervenção", list(opcoes), format_func=opcoes.get, key="vd_interv_sel")
    detalhe_intervencao(d, intervencoes[intervencoes["intervencao_id"] == sel].iloc[0], achados, perfil)


def detalhe_intervencao(d: Dados, i, achados, perfil: str) -> None:
    """Componente único: usado no Plano de Intervenções e no Meu Espaço."""
    etapas = " — ".join(f"<b>{ROTULO_STATUS[s]}</b>" if s == i["status"] else ROTULO_STATUS[s] for s in ETAPAS)
    if i["status"] == "cancelada":
        etapas = "<b>Cancelada</b>"
    a = achados[achados["achado_id"] == i["achado_id"]] if not achados.empty else achados
    fato = (f'{e(a.iloc[0]["regra_codigo"])} · {e(a.iloc[0]["evidencia_fato"])}' if not a.empty else "Achado não localizado")
    criterios = [("Prioridade do objetivo", "entrada_prioridade_obj", "pts_prioridade_objetivo"),
                 ("Posição do ativo", "entrada_posicao_ativo", "pts_posicao_ativo"),
                 ("Tipo de achado", "entrada_tipo_achado", "pts_tipo_achado"),
                 ("Abrangência", "entrada_abrangencia", "pts_abrangencia"),
                 ("Esforço", "esforco", "pts_esforco")]
    tabela = "".join(f'<tr><td style="padding:6px 8px;border-bottom:1px solid #F3F3F3">{r}</td>'
                     f'<td style="padding:6px 8px;border-bottom:1px solid #F3F3F3;color:#5C5C5C">{e(ROTULO_ENTRADA.get(str(i.get(c1)), ROTULO_NATUREZA.get(i.get(c1), i.get(c1))))}</td>'
                     f'<td style="padding:6px 8px;border-bottom:1px solid #F3F3F3;text-align:right;font-weight:650">{int(i.get(c2)):+d}</td></tr>'
                     for r, c1, c2 in criterios if i.get(c2) is not None and not pd.isna(i.get(c2)))
    ev = d.evidencias("intervencao", i["intervencao_id"])
    ev_html = ("".join(f'<li>{e(r["tipo"])} · {e(r["descricao"])} · {pessoa(r["registrado_por"])} em {_data(r["registrado_em"])}</li>'
                       for _, r in ev.iterrows()) if not ev.empty else "")
    ev_bloco = (f'<ul style="margin:6px 0 0;padding-left:16px;font-size:.82rem">{ev_html}</ul>' if ev_html
                else '<div class="vd-sub">Nenhuma evidência anexada.</div>')
    st.markdown(
        f'<div class="vd-card"><div class="vd-lbl">{e(i["codigo"])} · aberta em {_data(i.get("aberta_em"))} · responsável {pessoa(i["responsavel"])}'
        f'{" · prazo " + _data(i.get("prazo")) if tem(i.get("prazo")) else ""}</div>'
        f'<div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-top:6px">'
        f'<div style="font-size:1.15rem;font-weight:750">{e(i["titulo"])}</div>'
        f'<span class="vd-tag vd-t-escuro" style="font-size:.72rem">{e(ROTULO_PRIORIDADE.get(i["prioridade"], i["prioridade"]))} · {e(i["pontuacao_total"])} pontos</span></div>'
        f'<div class="vd-etapas">{etapas}</div>'
        f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px">'
        f'<div class="vd-no"><div class="vd-lbl">Fato que originou</div><div style="margin-top:6px">{fato}</div></div>'
        f'<div class="vd-no"><div class="vd-lbl">Recomendação e critério de conclusão</div><div style="margin-top:6px">{e(i["recomendacao"])}'
        f'<div class="vd-sub">{e(i.get("criterio_conclusao"))}</div></div></div></div>'
        f'<div class="vd-lbl" style="margin-top:14px">Por que esta prioridade · modelo {e(i.get("versao_modelo"))}</div>'
        f'<table style="width:100%;border-collapse:collapse;font-size:.85rem;margin-top:6px">{tabela}'
        f'<tr><td style="padding:6px 8px;font-weight:700">Total</td><td></td><td style="padding:6px 8px;text-align:right;font-weight:800">{e(i["pontuacao_total"])}</td></tr></table>'
        f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin-top:12px">'
        f'<div><div class="vd-lbl">Evidências</div>'
        f'{ev_bloco}</div>'
        f'<div><div class="vd-lbl">Histórico</div>{_rastro(d, "intervencao", i["intervencao_id"])}</div></div></div>',
        unsafe_allow_html=True)


def _resultados(d: Dados, beneficios) -> None:
    indicadores = d.tabela("vd_indicadores")
    medicoes = d.tabela("vd_medicoes", "data_referencia")
    st.markdown('<div class="vd-grid" style="grid-template-columns:repeat(3,minmax(0,1fr))">'
                + "".join(_cartao(v, _contar(beneficios, "estagio", k), destaque=k == "em_validacao")
                          for k, v in ROTULO_ESTAGIO.items()) + "</div>", unsafe_allow_html=True)
    nomes = dict(zip(indicadores["indicador_id"], indicadores["nome"])) if not indicadores.empty else {}
    unid = dict(zip(indicadores["indicador_id"], indicadores["unidade"])) if not indicadores.empty else {}
    if beneficios.empty:
        vazio("Nenhum benefício registrado. O benefício medido é calculado pelo banco a partir de duas medições validadas "
              "e de uma intervenção concluída.")
    for _, b in beneficios.iterrows():
        u = unid.get(b["indicador_id"], "")
        fin = (f'{e(b["moeda"])} {_fmt_num(b["valor_financeiro"])}' if tem(b.get("valor_financeiro")) else "Não calculado: sem conversão validada e vigente para a unidade.")
        st.markdown(
            f'<div class="vd-card" style="margin-bottom:12px"><div class="vd-lbl">Benefício · fórmula {e(b.get("formula_versao"))} · '
            f'{e(ROTULO_ESTAGIO.get(b["estagio"], b["estagio"]))}</div>'
            f'<div style="font-weight:750;font-size:1.05rem;margin-top:6px">{e(nomes.get(b["indicador_id"], b["indicador_id"]))}</div>'
            f'<div class="vd-grid" style="margin-top:10px">'
            + _cartao("Antes", _fmt_num(b.get("valor_antes"), u)) + _cartao("Depois", _fmt_num(b.get("valor_depois"), u))
            + _cartao("Melhoria", _fmt_num(b.get("melhoria"), u))
            + _cartao("Percentual", (_fmt_num(b.get("melhoria_pct")) + "%") if tem(b.get("melhoria_pct")) else "—")
            + f'</div><div class="vd-sub"><b>Valor financeiro:</b> {fin}</div>'
              f'<div class="vd-sub">{e(b.get("ressalva_causalidade")) if tem(b.get("ressalva_causalidade")) else "Resultado associado às intervenções; não comprova causalidade exclusiva."}</div></div>',
            unsafe_allow_html=True)
    if not medicoes.empty:
        tab = medicoes.assign(indicador=medicoes["indicador_id"].map(nomes),
                              tipo=medicoes["tipo"].map(lambda t: ROTULO_TIPO_MEDICAO.get(t, t)),
                              data_referencia=medicoes["data_referencia"].map(_data),
                              validacao=medicoes["status_validacao"].map(ROTULO_VALIDACAO))
        st.markdown('<div class="vd-lbl" style="margin:10px 0 6px">Medições</div>', unsafe_allow_html=True)
        st.dataframe(tab[["indicador", "tipo", "data_referencia", "valor", "metodo", "validacao"]].rename(columns={
            "indicador": "Indicador", "tipo": "Tipo", "data_referencia": "Referência", "valor": "Valor",
            "metodo": "Método", "validacao": "Validação"}), hide_index=True, use_container_width=True)


# ════════════════════════════════════════════════════════════════════
# Meu Espaço — Minhas intervenções
# ════════════════════════════════════════════════════════════════════
def secao_meu_espaco(qry, usuario: str, perfil: str) -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    d = Dados(qry)
    try:
        minhas = d._df(f"SELECT * FROM {SCHEMA}.vd_intervencoes WHERE responsavel = '{_lit(usuario)}' "
                       f"ORDER BY pontuacao_total DESC, aberta_em")
    except (ErroLeitura, ValueError):
        return
    st.markdown('<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px;margin-top:18px">'
                '<h3 style="margin:0">Minhas intervenções</h3><span class="vd-sub">Intervenções do Valor dos Dados em que você é o responsável</span></div>',
                unsafe_allow_html=True)
    hoje = pd.Timestamp.today().normalize()
    prazo = pd.to_datetime(minhas["prazo"], errors="coerce") if not minhas.empty else pd.Series(dtype="datetime64[ns]")
    grupos = {
        "Minhas ações": minhas[minhas["status"].isin({"planejada", "em_execucao"})] if not minhas.empty else minhas,
        "Atrasadas": minhas[minhas["status"].isin(ABERTAS) & (prazo < hoje)] if not minhas.empty else minhas,
        "Aguardando validação": minhas[minhas["status"] == "em_validacao"] if not minhas.empty else minhas,
        "Concluídas": minhas[minhas["status"] == "concluida"] if not minhas.empty else minhas,
    }
    abas = st.tabs([f"{k} · {len(v)}" for k, v in grupos.items()])
    achados = d.tabela("vd_achados") if not minhas.empty else pd.DataFrame()
    for aba, (nome, df) in zip(abas, grupos.items()):
        with aba:
            if df.empty:
                vazio("Nada nesta visão.")
                continue
            for _, i in df.iterrows():
                detalhe_intervencao(d, i, achados, perfil)
