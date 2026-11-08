"""Valor dos Dados — regras de integridade, cálculo e gravação (v3).

Camadas de proteção para cada gravação:
  1. validar_*()  — validação prévia em Python, com mensagens legíveis;
  2. sql_*()      — gravação condicionada: o próprio comando SQL só insere
                    ou atualiza se as relações forem coerentes no momento da
                    gravação (0 linhas afetadas = recusada);
  3. vd_v_integridade (SQL 03) — detecção posterior de qualquer desvio.

Este módulo não acessa o banco; recebe dados e devolve resultados ou SQL
parametrizado (marcadores :nome, aceitos pelo databricks-sql-connector).
"""
from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable, Mapping, Optional

VERSAO_DIAGNOSTICO = "vd_regras 3.2.0"
VERSAO_REGRAS = "R1"
VERSAO_MODELO = "P1"
VERSAO_FORMULA = "F1"

PERFIS = ("consultante", "curador", "aprovador")
NATUREZAS = ("nao_cadastrado", "nao_identificado", "nao_conforme", "nao_aplicavel")
STATUS_INTERVENCAO = ("identificada", "em_analise", "aprovada", "planejada",
                      "em_execucao", "em_validacao", "concluida", "cancelada")
FINAIS = ("concluida", "cancelada")
REF_TIPOS = ("ativo", "produto", "termo_glossario", "regra_negocio", "dominio", "indicador", "responsavel")

# ── Modelo de priorização P1 (espelho de 02; teste garante igualdade) ──
MODELO_P1: dict[str, dict[str, int]] = {
    "prioridade_objetivo": {"alta": 3, "media": 2, "baixa": 1},
    "posicao_ativo": {"saida": 3, "intermediario": 2, "fonte": 1, "nao_aplicavel": 2},
    "tipo_achado": {"nao_conforme": 3, "nao_cadastrado": 2, "nao_identificado": 1},
    "abrangencia": {"0": 0, "1-2": 1, "3-5": 2, "6+": 3, "nao_determinada": 0},
    "esforco": {"baixo": 1, "medio": 0, "alto": -1, "nao_informado": 0},
}
PESOS_P1 = {c: 1 for c in MODELO_P1}
# Entradas ainda não aprovadas pela responsável de negócio: não pontuam intervenções.
PENDENTES_P1 = {("posicao_ativo", "nao_aplicavel")}
FAIXAS_P1 = (("critica", 10, 99), ("alta", 7, 9), ("media", 4, 6), ("baixa", -99, 3))

# ── Máquina de estados (espelho de 02) ────────────────────────────────
TRANSICOES: dict[tuple[str, str], tuple[str, ...]] = {
    ("identificada", "em_analise"): ("curador", "aprovador"),
    ("em_analise", "aprovada"): ("aprovador",),
    ("em_analise", "identificada"): ("curador", "aprovador"),
    ("aprovada", "planejada"): ("curador", "aprovador", "responsavel"),
    ("planejada", "em_execucao"): ("responsavel",),
    ("em_execucao", "planejada"): ("responsavel",),
    ("em_execucao", "em_validacao"): ("responsavel",),
    ("em_validacao", "concluida"): ("aprovador",),
    ("em_validacao", "em_execucao"): ("aprovador",),
    **{(s, "cancelada"): ("curador", "aprovador")
       for s in ("identificada", "em_analise", "aprovada", "planejada", "em_execucao", "em_validacao")},
}
EXIGE_COMENTARIO = {("em_analise", "identificada"), ("em_execucao", "planejada"), ("em_validacao", "em_execucao")}


class DecisaoPendente(ValueError):
    """A priorização depende de uma entrada do modelo ainda não aprovada."""


class ErroIntegridade(ValueError):
    """Gravação recusada: a mensagem lista todas as violações encontradas."""

    def __init__(self, violacoes: list[str]):
        self.violacoes = violacoes
        super().__init__("; ".join(violacoes))


def _exigir(violacoes: list[str]) -> None:
    if violacoes:
        raise ErroIntegridade(violacoes)


# ════════════════════════════════════════════════════════════════════
# Chaves naturais (base do MERGE que impede duplicação)
# ════════════════════════════════════════════════════════════════════
def normalizar(texto: Optional[str]) -> str:
    t = unicodedata.normalize("NFKD", (texto or "").strip().lower())
    return " ".join("".join(c for c in t if not unicodedata.combining(c)).split())


def chave(*partes: Optional[str]) -> str:
    return "|".join(normalizar(p) if p is not None else "" for p in partes)


def chave_evidencia(entidade_tipo: str, entidade_id: str, conteudo: str) -> str:
    return chave(entidade_tipo, entidade_id, hashlib.sha256(conteudo.encode("utf-8")).hexdigest())


# ════════════════════════════════════════════════════════════════════
# Repositório: o que a validação prévia consulta (preenchido pela app)
# ════════════════════════════════════════════════════════════════════
@dataclass
class Repositorio:
    objetivos: Mapping[str, Mapping] = field(default_factory=dict)       # id -> registro
    processos: Mapping[str, Mapping] = field(default_factory=dict)
    indicadores: Mapping[str, Mapping] = field(default_factory=dict)
    vinculos: Mapping[str, Mapping] = field(default_factory=dict)
    achados: Mapping[str, Mapping] = field(default_factory=dict)
    intervencoes: Mapping[str, Mapping] = field(default_factory=dict)
    medicoes: Mapping[str, Mapping] = field(default_factory=dict)
    conversoes: Mapping[str, Mapping] = field(default_factory=dict)
    # Catálogo existente (somente leitura)
    ativos: set = field(default_factory=set)            # {(schema, tabela)}
    produtos: set = field(default_factory=set)          # {produto_id}
    termos: set = field(default_factory=set)            # {glossary_id}
    dominios: set = field(default_factory=set)          # {nome}
    responsaveis: set = field(default_factory=set)      # {e-mail} carregado de vd_v_responsaveis (fonte única)
    chave_regra_confirmada: bool = False                # muda após confirmar business_rules (00, passo 4)
    regras: set = field(default_factory=set)            # {id da regra}, quando confirmada


def _ativo_aberto(reg: Optional[Mapping], campo="status", cancelado="cancelado") -> bool:
    return reg is not None and reg.get(campo) != cancelado


# ════════════════════════════════════════════════════════════════════
# Validações prévias (C01–C09)
# ════════════════════════════════════════════════════════════════════
# Fonte única de responsáveis: a visão vd_v_responsaveis (SQL 03), usada tanto
# pela aplicação (carregar_responsaveis) quanto pela validação C11 do SQL.
SQL_RESPONSAVEIS = "SELECT email FROM vd_v_responsaveis"


def carregar_responsaveis(cursor) -> set:
    cursor.execute(SQL_RESPONSAVEIS)
    return {linha[0] for linha in cursor.fetchall()}


def validar_responsavel(repo: Repositorio, email: Optional[str], papel: str) -> list[str]:
    if not email:
        return [f"{papel}: obrigatório"]
    if email not in repo.responsaveis:
        return [f"{papel}: '{email}' não consta em vd_v_responsaveis (Owners e Stewards do catálogo)"]
    return []


def validar_processo(repo: Repositorio, p: Mapping) -> list[str]:
    v = []
    if not _ativo_aberto(repo.objetivos.get(p.get("objetivo_id"))):
        v.append("C01: objetivo inexistente ou cancelado")
    return v + validar_responsavel(repo, p.get("resp_processo"), "Responsável do processo")


def validar_indicador(repo: Repositorio, i: Mapping) -> list[str]:
    v = []
    if not _ativo_aberto(repo.objetivos.get(i.get("objetivo_id"))):
        v.append("C02: objetivo inexistente ou cancelado")
    if i.get("processo_id"):
        p = repo.processos.get(i["processo_id"])
        if p is None or p.get("objetivo_id") != i.get("objetivo_id"):
            v.append("C02: processo inexistente ou de outro objetivo")
    if i.get("sentido_melhora") not in ("reduzir", "aumentar"):
        v.append("Sentido de melhora inválido")
    return v + validar_responsavel(repo, i.get("responsavel"), "Responsável do indicador")


def validar_vinculo(repo: Repositorio, vin: Mapping) -> list[str]:
    v = []
    obj = vin.get("objetivo_id")
    if not _ativo_aberto(repo.objetivos.get(obj)):
        v.append("C03: objetivo inexistente ou cancelado")
    if vin.get("origem_tipo") == "objetivo" and vin.get("origem_id") != obj:
        v.append("C03: origem objetivo diferente do objetivo do vínculo")
    if vin.get("origem_tipo") == "processo":
        p = repo.processos.get(vin.get("origem_id"))
        if p is None or p.get("objetivo_id") != obj:
            v.append("C03: processo de origem inexistente ou de outro objetivo")
    t = vin.get("ref_tipo")
    if t not in REF_TIPOS:
        return v + ["Tipo de referência inválido"]
    if t == "ativo":
        if (vin.get("ref_schema"), vin.get("ref_nome")) not in repo.ativos:
            v.append("C04: ativo não existe em tabelas_metadata")
        if vin.get("papel_no_processo") not in ("fonte", "intermediario", "saida"):
            v.append("Papel do ativo no processo é obrigatório (fonte, intermediario ou saida)")
    elif vin.get("papel_no_processo"):
        v.append("Papel no processo só se aplica a ativos")
    if t == "produto" and vin.get("ref_id") not in repo.produtos:
        v.append("C04: produto inexistente")
    if t == "termo_glossario" and vin.get("ref_id") not in repo.termos:
        v.append("C04: termo do glossário inexistente")
    if t == "dominio" and vin.get("ref_nome") not in repo.dominios:
        v.append("C04: domínio não existe em tabelas_metadata.dominio")
    if t == "responsavel" and vin.get("ref_nome") not in repo.responsaveis:
        v.append("C04: responsável não cadastrado")
    if t == "indicador":
        i = repo.indicadores.get(vin.get("ref_id"))
        if i is None or i.get("objetivo_id") != obj:
            v.append("C04: indicador inexistente ou de outro objetivo")
    if t == "regra_negocio":
        if not repo.chave_regra_confirmada:
            v.append("C04: chave de business_rules ainda não confirmada no catálogo")
        elif vin.get("ref_id") not in repo.regras:
            v.append("C04: regra de negócio inexistente")
    if vin.get("origem") == "metadado" and not vin.get("evidencia_base"):
        v.append("Vínculo derivado de metadado exige o registro que o comprova")
    return v


def validar_intervencao_nova(repo: Repositorio, achado_id: str, objetivo_id: str) -> list[str]:
    a = repo.achados.get(achado_id)
    if a is None:
        return ["C06: achado inexistente"]
    v = []
    if a.get("objetivo_id") != objetivo_id:
        v.append("C06: achado pertence a outro objetivo")
    if a.get("status_validacao") != "validado":
        v.append("C06: achado ainda não validado — pontuação só após validação")
    if a.get("natureza") == "nao_aplicavel":
        v.append("C06: achado marcado como não aplicável")
    if a.get("situacao") != "aberto":
        v.append("C06: achado não está aberto")
    if any(i.get("achado_id") == achado_id and i.get("status") not in FINAIS for i in repo.intervencoes.values()):
        v.append("C06: já existe intervenção não final para este achado")
    return v


def validar_medicao(repo: Repositorio, m: Mapping) -> list[str]:
    i = repo.indicadores.get(m.get("indicador_id"))
    if i is None or i.get("status") == "cancelado":
        return ["C07: indicador inexistente ou cancelado"]
    v = []
    if m.get("objetivo_id") != i.get("objetivo_id"):
        v.append("C07: objetivo da medição difere do objetivo do indicador")
    if m.get("intervencao_id"):
        it = repo.intervencoes.get(m["intervencao_id"])
        if it is None or it.get("objetivo_id") != i.get("objetivo_id"):
            v.append("C07: intervenção inexistente ou de outro objetivo")
    if m.get("tipo") not in ("linha_base", "acompanhamento"):
        v.append("Tipo de medição inválido")
    return v


# ════════════════════════════════════════════════════════════════════
# Priorização (modelo P1) — reproduzível e explicável
# ════════════════════════════════════════════════════════════════════
def faixa_abrangencia(qtd: Optional[int]) -> str:
    if qtd is None:
        return "nao_determinada"
    if qtd < 0:
        raise ValueError("Abrangência negativa")
    return "0" if qtd == 0 else "1-2" if qtd <= 2 else "3-5" if qtd <= 5 else "6+"


def abrangencia_jusante(ativo: tuple[str, str], linhagem: Iterable[tuple[str, str, str, str]]) -> Optional[set]:
    """Ativos a jusante (fecho transitivo) pela linhagem cadastrada.
    Retorna None quando o ativo não aparece em nenhuma relação (não determinada)."""
    arestas: dict[tuple[str, str], set] = {}
    presentes = set()
    for os_, ot, ds, dt in linhagem:
        arestas.setdefault((os_, ot), set()).add((ds, dt))
        presentes.update({(os_, ot), (ds, dt)})
    if ativo not in presentes:
        return None
    visitados, pilha = set(), [ativo]
    while pilha:
        for nxt in arestas.get(pilha.pop(), ()):
            if nxt not in visitados and nxt != ativo:
                visitados.add(nxt)
                pilha.append(nxt)
    return visitados


@dataclass(frozen=True)
class Priorizacao:
    entradas: dict
    pontos: dict
    total: int
    prioridade: str
    versao_modelo: str = VERSAO_MODELO

    def explicacao(self) -> str:
        nomes = {"prioridade_objetivo": "Prioridade do objetivo", "posicao_ativo": "Posição do ativo",
                 "tipo_achado": "Tipo do achado", "abrangencia": "Abrangência", "esforco": "Esforço"}
        partes = [f"{nomes[c]} ({self.entradas[c]}): {self.pontos[c]:+d}" for c in MODELO_P1]
        return f"{' · '.join(partes)} = {self.total} → {self.prioridade} (modelo {self.versao_modelo})"


def priorizar(prioridade_objetivo: str, posicao_ativo: Optional[str], tipo_achado: str,
              abrangencia_ativos: Optional[int], esforco: Optional[str]) -> Priorizacao:
    entradas = {
        "prioridade_objetivo": prioridade_objetivo,
        "posicao_ativo": posicao_ativo or "nao_aplicavel",
        "tipo_achado": tipo_achado,
        "abrangencia": faixa_abrangencia(abrangencia_ativos),
        "esforco": esforco or "nao_informado",
    }
    if tipo_achado == "nao_aplicavel":
        raise ValueError("Achado não aplicável não gera intervenção")
    pontos = {}
    for crit, entrada in entradas.items():
        if entrada not in MODELO_P1[crit]:
            raise ValueError(f"Entrada '{entrada}' inválida para o critério {crit}")
        if (crit, entrada) in PENDENTES_P1:
            raise DecisaoPendente(f"Pontuação de {crit}='{entrada}' ainda não aprovada no modelo {VERSAO_MODELO}")
        pontos[crit] = MODELO_P1[crit][entrada] * PESOS_P1[crit]
    total = sum(pontos.values())
    faixa = [p for p, lo, hi in FAIXAS_P1 if lo <= total <= hi]
    if len(faixa) != 1:
        raise ValueError(f"Pontuação {total} sem faixa única")
    return Priorizacao(entradas, pontos, total, faixa[0])


# ════════════════════════════════════════════════════════════════════
# Benefícios — fórmula F1
# ════════════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class CalculoBeneficio:
    valor_antes: Decimal
    valor_depois: Decimal
    melhoria: Decimal
    melhoria_pct: Optional[Decimal]
    valor_financeiro: Optional[Decimal]
    moeda: Optional[str]
    metodo: str
    pode_validar: bool


def _q4(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def calcular_beneficio(sentido_melhora: str, tipo_unidade: str, unidade: str,
                       antes: Mapping, depois: Mapping, conversao: Optional[Mapping] = None) -> CalculoBeneficio:
    v = []
    if antes.get("indicador_id") != depois.get("indicador_id"):
        v.append("C08: medições de indicadores diferentes")
    if antes.get("tipo") != "linha_base" or depois.get("tipo") != "acompanhamento":
        v.append("C08: exige linha de base (antes) e acompanhamento (depois)")
    if not depois.get("data_referencia") or not antes.get("data_referencia") or depois["data_referencia"] <= antes["data_referencia"]:
        v.append("C08: medição posterior deve ter data de referência maior que a linha de base")
    if antes.get("status_validacao") != "validado" or depois.get("status_validacao") != "validado":
        v.append("C08: as duas medições precisam estar validadas")
    if sentido_melhora not in ("reduzir", "aumentar"):
        v.append("Sentido de melhora inválido")
    _exigir(v)
    a, d = Decimal(str(antes["valor"])), Decimal(str(depois["valor"]))
    melhoria = _q4(a - d if sentido_melhora == "reduzir" else d - a)
    pct = _q4(melhoria / abs(a) * 100) if a != 0 else None
    financeiro, moeda = None, None
    metodo = (f"F1: melhoria = {'antes − depois' if sentido_melhora == 'reduzir' else 'depois − antes'} "
              f"= {melhoria} {unidade}")
    if conversao is not None:
        cv = []
        if tipo_unidade == "percentual":
            cv.append("C08: indicador percentual não admite conversão financeira")
        if conversao.get("unidade_indicador") != unidade:
            cv.append("C08: conversão de unidade diferente da do indicador")
        if conversao.get("status_validacao") != "validado":
            cv.append("C08: conversão financeira não validada")
        ref = depois["data_referencia"]
        if ref < conversao["vigencia_inicio"] or (conversao.get("vigencia_fim") and ref > conversao["vigencia_fim"]):
            cv.append("C08: conversão fora da vigência na data da medição")
        _exigir(cv)
        fator, custo = Decimal(str(conversao["fator"])), Decimal(str(conversao["custo_unitario"]))
        financeiro = (melhoria * fator * custo).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        moeda = conversao["moeda"]
        metodo += (f"; valor financeiro = melhoria × fator {fator} × {custo} {moeda}/{conversao['unidade_custo']}"
                   f" = {financeiro} {moeda} (fonte: {conversao['fonte']})")
    return CalculoBeneficio(a, d, melhoria, pct, financeiro, moeda, metodo, pode_validar=melhoria > 0)


# ════════════════════════════════════════════════════════════════════
# Máquina de estados
# ════════════════════════════════════════════════════════════════════
def validar_transicao(interv: Mapping, para: str, perfil: str, usuario: str,
                      comentario: Optional[str] = None, tem_evidencia: bool = False,
                      justificativa_cancelamento: Optional[str] = None) -> list[str]:
    de = interv.get("status")
    permitidos = TRANSICOES.get((de, para))
    if permitidos is None:
        return [f"Transição {de} → {para} não permitida"]
    eh_responsavel = usuario == interv.get("responsavel")
    if perfil not in permitidos and not ("responsavel" in permitidos and eh_responsavel):
        return [f"Perfil '{perfil}' não pode executar {de} → {para}"]
    v = []
    if (de, para) in EXIGE_COMENTARIO and not (comentario or "").strip():
        v.append("Comentário obrigatório nesta transição")
    if (de, para) == ("em_analise", "aprovada") and not (interv.get("recomendacao") and interv.get("criterio_conclusao")):
        v.append("Aprovação exige recomendação e critério de conclusão")
    if para == "planejada" and not (interv.get("responsavel") and interv.get("prazo")):
        v.append("Planejamento exige responsável e prazo")
    if para == "em_validacao" and not tem_evidencia:
        v.append("Enviar para validação exige ao menos uma evidência")
    if para == "cancelada" and not (justificativa_cancelamento or "").strip():
        v.append("Cancelamento exige justificativa")
    return v


# ════════════════════════════════════════════════════════════════════
# Diagnóstico: natureza dos achados e reconciliação entre execuções
# ════════════════════════════════════════════════════════════════════
def _vazio(x) -> bool:
    return x is None or (isinstance(x, str) and not x.strip())


def avaliar_ativo(regra: str, meta: Optional[Mapping], *, papel: str, limite_qualidade: Optional[float],
                  qualidade: Optional[float], tem_qualidade: bool, tem_linhagem_destino: bool,
                  termos_vinculados: Optional[int], colunas_opcionais: set) -> tuple[str, Optional[str], Optional[str]]:
    """Retorna (resultado, natureza, valor_observado). resultado ∈ disparou | nao_disparou | nao_avaliada:<motivo>.
    Ausência de informação nunca vira 'nao_conforme'."""
    if meta is None:
        return "disparou", "nao_identificado", "ativo ausente de tabelas_metadata"
    if regra == "DG-01":
        return ("disparou", "nao_cadastrado", "data_owner vazio") if _vazio(meta.get("data_owner")) else ("nao_disparou", None, None)
    if regra == "DG-02":
        return ("disparou", "nao_cadastrado", "data_steward vazio") if _vazio(meta.get("data_steward")) else ("nao_disparou", None, None)
    if regra == "DG-03":
        if termos_vinculados is None:
            return "disparou", "nao_identificado", "vínculo por table_name ambíguo entre schemas"
        return ("disparou", "nao_cadastrado", "0 termos vinculados") if termos_vinculados == 0 else ("nao_disparou", None, None)
    if regra == "DG-04":
        if "tabelas_metadata.classificacao" not in colunas_opcionais:
            return "nao_avaliada:coluna classificacao ausente no catálogo", None, None
        return ("disparou", "nao_cadastrado", "classificacao vazia") if _vazio(meta.get("classificacao")) else ("nao_disparou", None, None)
    if regra == "DG-05":
        return ("disparou", "nao_identificado", "sem registro em gd_quality_dimensions") if not tem_qualidade else ("nao_disparou", None, None)
    if regra == "DG-06":
        if limite_qualidade is None:
            return "nao_avaliada:objetivo sem limite de qualidade", None, None
        if not tem_qualidade or qualidade is None:
            return "nao_avaliada:sem avaliação de qualidade (ver DG-05)", None, None
        return ("disparou", "nao_conforme", f"score_final={qualidade}") if qualidade < limite_qualidade else ("nao_disparou", None, None)
    if regra == "DG-07":
        if papel == "fonte":
            return "nao_avaliada:ativo de origem não tem linhagem a montante", None, None
        return ("disparou", "nao_identificado", "sem linhagem como destino") if not tem_linhagem_destino else ("nao_disparou", None, None)
    raise ValueError(f"Regra {regra} não se aplica a ativos")


@dataclass(frozen=True)
class AcaoAchado:
    tipo: str            # novo | reincidente | resolvido | reaberto
    chave_natural: str
    natureza: Optional[str] = None
    valor_observado: Optional[str] = None


def reconciliar(existentes: Mapping[str, Mapping], disparados: Mapping[str, tuple[str, Optional[str]]],
                avaliados: set) -> list[AcaoAchado]:
    """Evita duplicação entre diagnósticos sucessivos.
    existentes: chave_natural -> achado atual; disparados: chave -> (natureza, valor);
    avaliados: chaves cujas regras foram de fato avaliadas nesta execução.
    Regra: chave nova → 'novo'; chave aberta que disparou de novo → 'reincidente' (mesmo registro);
    chave aberta avaliada que não disparou → 'resolvido'; chave resolvida que volta a disparar → 'reaberto'.
    Regra não avaliada não resolve nada (falta de informação ≠ correção)."""
    acoes = []
    for k, (nat, val) in disparados.items():
        atual = existentes.get(k)
        if atual is None:
            acoes.append(AcaoAchado("novo", k, nat, val))
        elif atual.get("situacao") == "resolvido":
            acoes.append(AcaoAchado("reaberto", k, nat, val))
        elif atual.get("situacao") == "aberto":
            acoes.append(AcaoAchado("reincidente", k, nat, val))
    for k, atual in existentes.items():
        if atual.get("situacao") == "aberto" and k in avaliados and k not in disparados:
            acoes.append(AcaoAchado("resolvido", k))
    return acoes


# ════════════════════════════════════════════════════════════════════
# Gravações condicionadas (SQL parametrizado). 0 linhas afetadas = recusa.
# ════════════════════════════════════════════════════════════════════
SQL_INSERIR_INTERVENCAO = """
MERGE INTO vd_intervencoes t
USING (
  SELECT :intervencao_id AS intervencao_id, concat(a.achado_id, '|1') AS chave_natural, :codigo AS codigo,
         a.achado_id, 1 AS sequencia, CAST(NULL AS STRING) AS intervencao_anterior_id, a.objetivo_id,
         :titulo AS titulo, :recomendacao AS recomendacao, :tipo_afirmacao AS tipo_afirmacao,
         :causa_provavel AS causa_provavel, :responsavel AS responsavel, :area AS area,
         m1.versao_modelo, o.prioridade AS entrada_prioridade_obj,
         coalesce(v.papel_no_processo, 'nao_aplicavel') AS entrada_posicao_ativo, a.natureza AS entrada_tipo_achado,
         CAST(:abrangencia_ativos AS INT) AS abrangencia_ativos, :abrangencia_base AS abrangencia_base,
         m4.entrada AS entrada_abrangencia, m5.entrada AS esforco,
         m1.pontos * m1.peso AS pts_prioridade_objetivo, m2.pontos * m2.peso AS pts_posicao_ativo,
         m3.pontos * m3.peso AS pts_tipo_achado, m4.pontos * m4.peso AS pts_abrangencia, m5.pontos * m5.peso AS pts_esforco,
         m1.pontos * m1.peso + m2.pontos * m2.peso + m3.pontos * m3.peso + m4.pontos * m4.peso + m5.pontos * m5.peso AS pontuacao_total,
         f.prioridade, :criterio_conclusao AS criterio_conclusao, 'identificada' AS status, current_timestamp() AS aberta_em,
         CAST(NULL AS DATE) AS prazo, CAST(NULL AS STRING) AS aprovado_por, CAST(NULL AS TIMESTAMP) AS aprovado_em,
         CAST(NULL AS STRING) AS concluido_por, CAST(NULL AS TIMESTAMP) AS concluida_em,
         CAST(NULL AS STRING) AS justificativa_cancelamento, 'calculado' AS origem, :usuario AS criado_por,
         current_timestamp() AS criado_em, CAST(NULL AS STRING) AS atualizado_por, CAST(NULL AS TIMESTAMP) AS atualizado_em, 1 AS versao
  FROM vd_achados a
  JOIN vd_objetivos o ON o.objetivo_id = a.objetivo_id AND o.status <> 'cancelado'
  JOIN vd_vinculos v  ON v.vinculo_id = a.vinculo_id AND v.objetivo_id = a.objetivo_id
  JOIN vd_modelo_priorizacao m1 ON m1.versao_modelo = :versao_modelo AND m1.situacao = 'aprovado' AND m1.criterio = 'prioridade_objetivo' AND m1.entrada = o.prioridade
  JOIN vd_modelo_priorizacao m2 ON m2.versao_modelo = :versao_modelo AND m2.situacao = 'aprovado' AND m2.criterio = 'posicao_ativo' AND m2.entrada = coalesce(v.papel_no_processo, 'nao_aplicavel')
  JOIN vd_modelo_priorizacao m3 ON m3.versao_modelo = :versao_modelo AND m3.situacao = 'aprovado' AND m3.criterio = 'tipo_achado' AND m3.entrada = a.natureza
  JOIN vd_modelo_priorizacao m4 ON m4.versao_modelo = :versao_modelo AND m4.situacao = 'aprovado' AND m4.criterio = 'abrangencia' AND m4.entrada = :entrada_abrangencia
  JOIN vd_modelo_priorizacao m5 ON m5.versao_modelo = :versao_modelo AND m5.situacao = 'aprovado' AND m5.criterio = 'esforco' AND m5.entrada = :esforco
  JOIN vd_faixas_prioridade f ON f.versao_modelo = :versao_modelo
       AND (m1.pontos * m1.peso + m2.pontos * m2.peso + m3.pontos * m3.peso + m4.pontos * m4.peso + m5.pontos * m5.peso)
           BETWEEN f.pontuacao_min AND f.pontuacao_max
  WHERE a.achado_id = :achado_id AND a.objetivo_id = :objetivo_id
    AND a.status_validacao = 'validado' AND a.situacao = 'aberto' AND a.natureza <> 'nao_aplicavel'
    AND NOT EXISTS (SELECT 1 FROM vd_intervencoes x WHERE x.achado_id = a.achado_id AND x.status NOT IN ('concluida','cancelada'))
) s
ON t.chave_natural = s.chave_natural
WHEN NOT MATCHED THEN INSERT *
"""

# As condições ficam na origem (USING): o Delta não aceita subconsultas na
# cláusula ON do MERGE.
SQL_TRANSICIONAR = """
MERGE INTO vd_intervencoes t
USING (
  SELECT i.intervencao_id, i.versao, tr.status_de, tr.status_para
  FROM vd_intervencoes i
  JOIN vd_transicoes_intervencao tr ON tr.status_de = i.status AND tr.status_para = :status_para
  WHERE i.intervencao_id = :intervencao_id AND i.status = :status_de AND i.versao = :versao_lida
    AND (array_contains(split(tr.perfis, ','), :perfil)
         OR (array_contains(split(tr.perfis, ','), 'responsavel') AND i.responsavel = :usuario))
    AND (tr.status_para <> 'em_validacao' OR EXISTS (SELECT 1 FROM vd_evidencias e
         WHERE e.entidade_tipo = 'intervencao' AND e.entidade_id = i.intervencao_id))
    AND (tr.status_para <> 'aprovada' OR (length(trim(coalesce(i.recomendacao, ''))) > 0
         AND length(trim(coalesce(i.criterio_conclusao, ''))) > 0))
    AND (tr.status_para <> 'planejada' OR coalesce(CAST(:prazo AS DATE), i.prazo) IS NOT NULL)
    AND (tr.status_para <> 'cancelada' OR length(trim(coalesce(:justificativa, ''))) > 0)
    AND (concat(tr.status_de, '>', tr.status_para) NOT IN ('em_analise>identificada', 'em_execucao>planejada', 'em_validacao>em_execucao')
         OR length(trim(coalesce(:comentario, ''))) > 0)
) s
ON t.intervencao_id = s.intervencao_id AND t.versao = s.versao
WHEN MATCHED THEN UPDATE SET
  status = s.status_para,
  prazo = CASE WHEN s.status_para = 'planejada' THEN coalesce(CAST(:prazo AS DATE), t.prazo) ELSE t.prazo END,
  aprovado_por = CASE WHEN s.status_para = 'aprovada' THEN :usuario ELSE t.aprovado_por END,
  aprovado_em  = CASE WHEN s.status_para = 'aprovada' THEN current_timestamp() ELSE t.aprovado_em END,
  concluido_por = CASE WHEN s.status_para = 'concluida' THEN :usuario ELSE t.concluido_por END,
  concluida_em  = CASE WHEN s.status_para = 'concluida' THEN current_timestamp() ELSE t.concluida_em END,
  justificativa_cancelamento = CASE WHEN s.status_para = 'cancelada' THEN :justificativa ELSE t.justificativa_cancelamento END,
  atualizado_por = :usuario, atualizado_em = current_timestamp(), versao = t.versao + 1
"""

SQL_INSERIR_BENEFICIO_MEDIDO = """
MERGE INTO vd_beneficios t
USING (
  SELECT :beneficio_id AS beneficio_id, concat(i.indicador_id, '|', it.intervencao_id) AS chave_natural,
         i.objetivo_id, i.indicador_id, it.intervencao_id, 'F1' AS formula_versao, i.sentido_melhora,
         :premissas AS premissas, CAST(:valor_estimado AS DECIMAL(18,4)) AS valor_estimado,
         a.medicao_id AS medicao_antes_id, d.medicao_id AS medicao_depois_id, a.valor AS valor_antes, d.valor AS valor_depois,
         CAST(CASE i.sentido_melhora WHEN 'reduzir' THEN a.valor - d.valor ELSE d.valor - a.valor END AS DECIMAL(18,4)) AS melhoria,
         CAST(CASE WHEN a.valor <> 0 THEN (CASE i.sentido_melhora WHEN 'reduzir' THEN a.valor - d.valor ELSE d.valor - a.valor END)
              / abs(a.valor) * 100 END AS DECIMAL(9,4)) AS melhoria_pct,
         c.conversao_id, c.moeda,
         CAST(round((CASE i.sentido_melhora WHEN 'reduzir' THEN a.valor - d.valor ELSE d.valor - a.valor END) * c.fator * c.custo_unitario, 2) AS DECIMAL(18,2)) AS valor_financeiro,
         :metodo_calculo AS metodo_calculo, 'em_validacao' AS estagio,
         'Resultado associado à intervenção; não comprova causalidade exclusiva.' AS ressalva_causalidade,
         CAST(NULL AS STRING) AS validado_por, CAST(NULL AS TIMESTAMP) AS validado_em, CAST(NULL AS STRING) AS justificativa_validacao,
         'calculado' AS origem, :usuario AS criado_por, current_timestamp() AS criado_em,
         CAST(NULL AS STRING) AS atualizado_por, CAST(NULL AS TIMESTAMP) AS atualizado_em, 1 AS versao
  FROM vd_indicadores i
  JOIN vd_intervencoes it ON it.intervencao_id = :intervencao_id AND it.objetivo_id = i.objetivo_id AND it.status = 'concluida'
  JOIN vd_medicoes a ON a.medicao_id = :medicao_antes_id AND a.indicador_id = i.indicador_id AND a.tipo = 'linha_base'
                     AND a.status = 'ativo' AND a.status_validacao = 'validado'
  JOIN vd_medicoes d ON d.medicao_id = :medicao_depois_id AND d.indicador_id = i.indicador_id AND d.tipo = 'acompanhamento'
                     AND d.status = 'ativo' AND d.status_validacao = 'validado' AND d.data_referencia > a.data_referencia
  LEFT JOIN vd_conversoes_financeiras c ON c.conversao_id = :conversao_id AND c.unidade_indicador = i.unidade
                     AND c.status_validacao = 'validado' AND i.tipo_unidade <> 'percentual'
                     AND d.data_referencia >= c.vigencia_inicio AND (c.vigencia_fim IS NULL OR d.data_referencia <= c.vigencia_fim)
  WHERE i.indicador_id = :indicador_id AND i.status = 'ativo'
    AND (:conversao_id IS NULL OR c.conversao_id IS NOT NULL)
) s
ON t.chave_natural = s.chave_natural
WHEN NOT MATCHED THEN INSERT *
"""

# Tabelas imutáveis (appendOnly): inclusão idempotente sem MERGE
SQL_INSERIR_HISTORICO = """
INSERT INTO vd_historico
SELECT :historico_id, :chave_natural, :entidade_tipo, :entidade_id, :acao, CAST(:versao_entidade AS INT),
       :status_anterior, :status_novo, :campos_alterados, :comentario, :evidencia_id,
       :usuario, :perfil, current_timestamp()
FROM (SELECT 1) d
WHERE NOT EXISTS (SELECT 1 FROM vd_historico h WHERE h.chave_natural = :chave_natural)
"""

SQL_INSERIR_EVIDENCIA = """
INSERT INTO vd_evidencias
SELECT :evidencia_id, :chave_natural, :entidade_tipo, :entidade_id, :tipo, :descricao, :conteudo,
       :origem, :usuario, :perfil, current_timestamp()
FROM (SELECT 1) d
WHERE NOT EXISTS (SELECT 1 FROM vd_evidencias e WHERE e.chave_natural = :chave_natural)
"""


# ── Confirmação de gravações ─────────────────────────────────────────
# Comandos INSERT/MERGE NÃO são lidos com fetchone(). A confirmação é feita por
# LEITURA POSTERIOR do estado esperado (consulta SELECT), o que independe da
# versão do databricks-sql-connector. Quando o conector informa a contagem em
# cursor.rowcount (versões que expõem numModifiedRows), ela é conferida contra a
# leitura; divergência impede a confirmação. rowcount = -1 significa "não
# informado" e não é usado como evidência.
VERIFICACOES = {
    "intervencao_inserida": "SELECT COUNT(*) FROM vd_intervencoes WHERE intervencao_id = :intervencao_id AND versao = 1",
    "transicao": ("SELECT COUNT(*) FROM vd_intervencoes WHERE intervencao_id = :intervencao_id AND status = :status_para "
                  "AND versao = :versao_nova AND atualizado_por = :usuario"),
    "beneficio_inserido": "SELECT COUNT(*) FROM vd_beneficios WHERE beneficio_id = :beneficio_id",
    "historico": "SELECT COUNT(*) FROM vd_historico WHERE chave_natural = :chave_natural",
    "evidencia": "SELECT COUNT(*) FROM vd_evidencias WHERE chave_natural = :chave_natural",
    "ocorrencia": "SELECT COUNT(*) FROM vd_achados_ocorrencias WHERE chave_natural = :chave_natural",
    "ocorrencias": "SELECT COUNT(*) FROM vd_achados_ocorrencias WHERE execucao_id = :execucao_id",
    "execucao_concluida": ("SELECT COUNT(*) FROM vd_execucoes_diagnostico WHERE execucao_id = :execucao_id "
                           "AND status = 'concluida'"),
}


def _consultar_contagem(cursor, sql: str, params: Mapping) -> int:
    """Executa um SELECT COUNT(*) e devolve o valor. Só é usado para consultas."""
    if not sql.lstrip().upper().startswith("SELECT"):
        raise ValueError("_consultar_contagem aceita apenas SELECT")
    cursor.execute(sql, dict(params))
    linha = cursor.fetchone()
    return int(linha[0]) if linha else 0


def _contagem_informada(cursor) -> Optional[int]:
    rc = getattr(cursor, "rowcount", -1)
    return rc if isinstance(rc, int) and rc >= 0 else None


def executar_gravacao(cursor, operacao: str, sql: str, params: Mapping, verificacao: str,
                      params_verificacao: Mapping, esperado: int = 1, aceita_ja_existente: bool = False) -> int:
    """Executa a gravação condicionada e confirma pela leitura posterior.
    aceita_ja_existente: para inclusões idempotentes (histórico, evidência), uma
    repetição que não insere nada é aceita se o registro já existir."""
    cursor.execute(sql, dict(params))
    informada = _contagem_informada(cursor)
    lida = _consultar_contagem(cursor, VERIFICACOES[verificacao], params_verificacao)
    if lida != esperado:
        raise ErroIntegridade([f"{operacao}: recusada — estado esperado não encontrado após a gravação "
                               f"(leitura={lida}, esperado={esperado})"])
    if informada is not None and informada != esperado and not (aceita_ja_existente and informada == 0):
        raise ErroIntegridade([f"{operacao}: divergência entre a contagem do conector ({informada}) e a leitura ({lida})"])
    return lida


# ════════════════════════════════════════════════════════════════════
# Cobertura do diagnóstico: toda regra aplicável a todo vínculo analisado
# ════════════════════════════════════════════════════════════════════
# Espelho de 02 (aplica_a por regra); teste garante igualdade.
REGRAS_R1 = {"DG-01": "ativo", "DG-02": "ativo", "DG-03": "ativo", "DG-04": "ativo", "DG-05": "ativo",
             "DG-06": "ativo", "DG-07": "ativo", "DG-08": "produto", "DG-09": "vinculo"}


def regras_aplicaveis(ref_tipo: str, regras: Mapping[str, str] = REGRAS_R1) -> list[str]:
    return sorted(c for c, alvo in regras.items() if alvo == "vinculo" or alvo == ref_tipo)


@dataclass(frozen=True)
class Ocorrencia:
    vinculo_id: str
    regra_codigo: str
    resultado: str                      # disparou | nao_disparou | nao_avaliada
    natureza: Optional[str] = None
    valor_observado: Optional[str] = None
    motivo_nao_avaliada: Optional[str] = None


def montar_ocorrencias(vinculos: Mapping[str, str], habilitacao: Mapping[str, tuple[bool, str]],
                       resultados: Mapping[tuple[str, str], tuple]) -> list[Ocorrencia]:
    """vinculos: vinculo_id -> ref_tipo; habilitacao: regra -> (habilitada, motivo);
    resultados: (vinculo_id, regra) -> (resultado, natureza, valor) das regras avaliadas.
    Garante uma ocorrência por par (vínculo, regra aplicável). Falta de resultado
    para regra habilitada impede concluir a execução."""
    ocorrencias, faltando = [], []
    for vid, ref_tipo in sorted(vinculos.items()):
        for regra in regras_aplicaveis(ref_tipo):
            habilitada, motivo = habilitacao.get(regra, (False, "regra sem registro de habilitação"))
            if not habilitada:
                if (vid, regra) in resultados:
                    raise ErroIntegridade([f"{regra} está desabilitada ({motivo}) e não pode ter resultado avaliado"])
                ocorrencias.append(Ocorrencia(vid, regra, "nao_avaliada", motivo_nao_avaliada=motivo))
                continue
            r = resultados.get((vid, regra))
            if r is None:
                faltando.append(f"{vid}/{regra}")
                continue
            resultado, natureza, valor = r
            if resultado.startswith("nao_avaliada"):
                ocorrencias.append(Ocorrencia(vid, regra, "nao_avaliada", motivo_nao_avaliada=resultado.split(":", 1)[-1]))
            elif resultado in ("disparou", "nao_disparou"):
                if (resultado == "disparou") != (natureza is not None):
                    raise ErroIntegridade([f"{vid}/{regra}: natureza incompatível com o resultado"])
                ocorrencias.append(Ocorrencia(vid, regra, resultado, natureza, valor))
            else:
                raise ErroIntegridade([f"{vid}/{regra}: resultado desconhecido '{resultado}'"])
    if faltando:
        raise ErroIntegridade([f"Execução incompleta: sem resultado para {', '.join(faltando)}"])
    return ocorrencias


# ════════════════════════════════════════════════════════════════════
# Operação confirmada = entidade gravada + histórico gravado
# ════════════════════════════════════════════════════════════════════
class ErroAuditoria(RuntimeError):
    """A entidade foi alterada, mas o histórico não foi gravado. A operação NÃO
    está confirmada: a interface deve exibir erro e a entidade fica bloqueada
    até a reconciliação (verificação I03)."""


SQL_PENDENCIA_ENTIDADE = """
SELECT COUNT(*) FROM vd_v_integridade
WHERE codigo = 'I03' AND entidade = :entidade_tipo AND registro = :entidade_id
"""


@dataclass(frozen=True)
class ResultadoOperacao:
    confirmada: bool
    versao_nova: int
    mensagem: str


def executar_com_historico(cursor, operacao: str, sql: str, params: Mapping, verificacao: str,
                           params_verificacao: Mapping, historico: Mapping, entidade_tipo: str,
                           entidade_id: str) -> ResultadoOperacao:
    """1) recusa se a entidade tem histórico pendente; 2) grava a entidade e confirma por
    leitura; 3) grava o histórico e confirma por leitura; 4) só então confirma.
    Falha em 3 → ErroAuditoria (operação NÃO confirmada, entidade bloqueada)."""
    if _consultar_contagem(cursor, SQL_PENDENCIA_ENTIDADE, {"entidade_tipo": entidade_tipo, "entidade_id": entidade_id}) > 0:
        raise ErroAuditoria(f"{operacao}: {entidade_tipo} {entidade_id} tem alteração sem histórico; reconciliar antes de continuar")
    executar_gravacao(cursor, operacao, sql, params, verificacao, params_verificacao)
    try:
        executar_gravacao(cursor, f"{operacao} (histórico)", SQL_INSERIR_HISTORICO, historico, "historico",
                          {"chave_natural": historico["chave_natural"]}, aceita_ja_existente=True)
    except Exception as exc:  # noqa: BLE001 — qualquer falha no histórico impede a confirmação
        raise ErroAuditoria(f"{operacao}: alteração gravada sem histórico ({exc}); operação NÃO confirmada") from exc
    return ResultadoOperacao(True, int(historico["versao_entidade"]), f"{operacao}: confirmada")


def transicionar(cursor, interv: Mapping, para: str, perfil: str, usuario: str, *, historico_id: str,
                 comentario: Optional[str] = None, tem_evidencia: bool = False, prazo=None,
                 justificativa_cancelamento: Optional[str] = None) -> ResultadoOperacao:
    """Fluxo completo de uma transição: validação prévia → gravação condicionada → histórico."""
    _exigir(validar_transicao({**interv, "prazo": prazo or interv.get("prazo")}, para, perfil, usuario,
                              comentario, tem_evidencia, justificativa_cancelamento))
    de, versao = interv["status"], int(interv["versao"])
    params = {"intervencao_id": interv["intervencao_id"], "status_de": de, "status_para": para, "perfil": perfil,
              "usuario": usuario, "versao_lida": versao, "prazo": prazo, "justificativa": justificativa_cancelamento,
              "comentario": comentario}
    hist = {"historico_id": historico_id, "chave_natural": chave("intervencao", interv["intervencao_id"], str(versao + 1), "transicao"),
            "entidade_tipo": "intervencao", "entidade_id": interv["intervencao_id"], "acao": "transicao",
            "versao_entidade": versao + 1, "status_anterior": de, "status_novo": para, "campos_alterados": None,
            "comentario": comentario or justificativa_cancelamento, "evidencia_id": None, "usuario": usuario, "perfil": perfil}
    verif = {"intervencao_id": interv["intervencao_id"], "status_para": para, "versao_nova": versao + 1, "usuario": usuario}
    return executar_com_historico(cursor, f"Transição {de} → {para}", SQL_TRANSICIONAR, params, "transicao", verif,
                                  hist, "intervencao", interv["intervencao_id"])


# ════════════════════════════════════════════════════════════════════
# Gravação das ocorrências e conclusão da execução (I04)
# ════════════════════════════════════════════════════════════════════
SQL_INSERIR_OCORRENCIA = """
INSERT INTO vd_achados_ocorrencias
SELECT :ocorrencia_id, :chave_natural, :execucao_id, :vinculo_id, :regra_codigo, :achado_id, :resultado,
       :natureza, :valor_observado, :motivo_nao_avaliada, current_timestamp()
FROM (SELECT 1) d
WHERE NOT EXISTS (SELECT 1 FROM vd_achados_ocorrencias o WHERE o.chave_natural = :chave_natural)
"""

# Só conclui se o banco tiver exatamente o número de ocorrências esperado.
SQL_CONCLUIR_EXECUCAO = """
MERGE INTO vd_execucoes_diagnostico t
USING (
  SELECT e.execucao_id FROM vd_execucoes_diagnostico e
  WHERE e.execucao_id = :execucao_id AND e.status = 'em_execucao'
    AND (SELECT COUNT(*) FROM vd_achados_ocorrencias o WHERE o.execucao_id = e.execucao_id) = CAST(:ocorrencias_esperadas AS INT)
) s
ON t.execucao_id = s.execucao_id
WHEN MATCHED THEN UPDATE SET
  status = 'concluida', finalizado_em = current_timestamp(),
  vinculos_analisados = CAST(:vinculos_analisados AS INT), achados_novos = CAST(:achados_novos AS INT),
  achados_reincidentes = CAST(:achados_reincidentes AS INT), achados_resolvidos = CAST(:achados_resolvidos AS INT)
"""


def gravar_ocorrencias_e_concluir(cursor, execucao_id: str, ocorrencias: list[Ocorrencia],
                                  achado_por_par: Mapping[tuple[str, str], str], novo_id, resumo: Mapping) -> int:
    """Grava UMA ocorrência por (vínculo, regra) — disparou, nao_disparou e nao_avaliada —,
    confirma pela contagem lida do banco e só então conclui a execução.
    novo_id: função que gera identificadores (uuid na aplicação)."""
    for o in ocorrencias:
        chave_oc = chave(execucao_id, o.vinculo_id, o.regra_codigo)
        executar_gravacao(cursor, f"Ocorrência {o.vinculo_id}/{o.regra_codigo}", SQL_INSERIR_OCORRENCIA, {
            "ocorrencia_id": novo_id(), "chave_natural": chave_oc, "execucao_id": execucao_id, "vinculo_id": o.vinculo_id,
            "regra_codigo": o.regra_codigo, "achado_id": achado_por_par.get((o.vinculo_id, o.regra_codigo)),
            "resultado": o.resultado, "natureza": o.natureza, "valor_observado": o.valor_observado,
            "motivo_nao_avaliada": o.motivo_nao_avaliada}, "ocorrencia", {"chave_natural": chave_oc},
            aceita_ja_existente=True)
    gravadas = _consultar_contagem(cursor, VERIFICACOES["ocorrencias"], {"execucao_id": execucao_id})
    if gravadas != len(ocorrencias):
        raise ErroIntegridade([f"Execução {execucao_id}: {gravadas} ocorrências no banco, {len(ocorrencias)} esperadas"])
    executar_gravacao(cursor, f"Concluir execução {execucao_id}", SQL_CONCLUIR_EXECUCAO, {
        "execucao_id": execucao_id, "ocorrencias_esperadas": len(ocorrencias),
        "vinculos_analisados": len({o.vinculo_id for o in ocorrencias}), **resumo},
        "execucao_concluida", {"execucao_id": execucao_id})
    return gravadas
