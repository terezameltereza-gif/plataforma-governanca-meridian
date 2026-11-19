"""Regras de governança e modelo de maturidade de 5 estrelas.

Avalia cada ativo de `tabelas_metadata` com as regras de metadados (M) e de qualidade (R)
usando apenas tabelas que já existem no schema:
  tabelas_metadata · glossary_asset_link · linhagem_ativos · gd_quality_dimensions · gd_certification
As regras de qualidade usam as medições já registradas em gd_quality_dimensions; enquanto não houver
varredura própria, essa é a evidência disponível e a tela informa a origem.
Nenhuma função grava no banco.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

APROVADA, REPROVADA, NAO_APLICAVEL, NAO_AVALIADA = "aprovada", "reprovada", "nao_aplicavel", "nao_avaliada"
DIAS_REVISAO = 180
MIN_DESCRICAO = 40


@dataclass(frozen=True)
class Regra:
    codigo: str
    nome: str
    tipo: str            # metadados | qualidade | certificacao
    criterio: str
    acao: str
    papel: str           # owner | steward | dominio | governanca
    severidade: str      # critica | alta | media


REGRAS = {r.codigo: r for r in [
    Regra("M1", "Ativo sem Data Owner", "metadados", "Data Owner preenchido", "Indicar o Data Owner", "dominio", "alta"),
    Regra("M2", "Ativo sem Data Steward", "metadados", "Data Steward preenchido", "Indicar o Data Steward", "owner", "alta"),
    Regra("M3", "Ativo sem domínio", "metadados", "Domínio preenchido", "Classificar o domínio", "steward", "media"),
    Regra("M4", "Descrição insuficiente", "metadados",
          f"Descrição com pelo menos {MIN_DESCRICAO} caracteres e diferente do nome da tabela",
          "Reescrever a descrição", "steward", "media"),
    Regra("M5", "Sem classificação de sensibilidade", "metadados", "Classificação preenchida",
          "Classificar a sensibilidade", "owner", "alta"),
    Regra("M7", "Sem termo de negócio", "metadados", "Ao menos um termo do glossário vinculado",
          "Vincular ao termo do glossário", "steward", "media"),
    Regra("M8", "Documentação desatualizada", "metadados", f"Metadados atualizados há até {DIAS_REVISAO} dias",
          "Revisar e confirmar a documentação", "steward", "media"),
    Regra("M9", "Sem linhagem", "metadados", "Origem registrada na linhagem (exceto camada bronze)",
          "Registrar a origem do ativo", "steward", "media"),
    Regra("R1", "Chave duplicada", "qualidade", "Unicidade = 100%", "Corrigir a carga e remover duplicados", "steward", "critica"),
    Regra("R2", "Campo crítico vazio", "qualidade", "Completude ≥ 98%", "Corrigir na origem e reprocessar", "steward", "critica"),
    Regra("R3", "Valor fora do domínio", "qualidade", "Validade ≥ 98%", "Corrigir o valor ou a lista permitida", "steward", "alta"),
    Regra("R4", "Carga atrasada", "qualidade", "Atualidade ≥ 95%", "Reexecutar a carga e avisar os consumidores", "steward", "critica"),
    Regra("R6", "Registro órfão", "qualidade", "Consistência ≥ 98%", "Corrigir a referência ou a ordem das cargas", "steward", "alta"),
    Regra("R7", "Total não reconcilia", "qualidade", "Diferença ≤ 0,01% contra o total de controle",
          "Configurar o total de controle com a área de negócio", "owner", "critica"),
    Regra("CERT", "Aprovação formal do Data Owner", "certificacao", "Ativo certificado na Certificação",
          "Solicitar a certificação", "owner", "media"),
]}

# Medição usada por cada regra de qualidade: (coluna em gd_quality_dimensions, limite mínimo em %)
MEDICAO_QUALIDADE = {"R1": ("unicidade_pct", 100.0), "R2": ("completude_pct", 98.0), "R3": ("validade_pct", 98.0),
                     "R4": ("atualidade_pct", 95.0), "R6": ("consistencia_pct", 98.0)}

NIVEIS = [
    (1, "Identificado", ("M1", "M3")),
    (2, "Documentado", ("M2", "M4", "M5")),
    (3, "Confiável", ("R1", "R2", "R4")),
    (4, "Conectado", ("M7", "M8", "M9")),
    (5, "Certificado", ("R3", "R6", "R7", "CERT")),
]
NOME_NIVEL = {0: "Sem estrela", **{n: nome for n, nome, _ in NIVEIS}}


@dataclass
class Resultado:
    status: str
    observado: str = ""


@dataclass
class Avaliacao:
    schema: str
    tabela: str
    dominio: str
    owner: str
    steward: str
    resultados: dict = field(default_factory=dict)
    estrelas: int = 0

    @property
    def ativo(self) -> str:
        return f"{self.schema}.{self.tabela}"

    def responsavel(self, codigo: str) -> str:
        papel = REGRAS[codigo].papel
        if papel == "owner":
            return self.owner or "Líder do domínio"
        if papel == "steward":
            return self.steward or self.owner or "Líder do domínio"
        return "Líder do domínio"

    def faltam_proxima(self) -> list[str]:
        """Regras que impedem a próxima estrela."""
        if self.estrelas >= 5:
            return []
        _, _, codigos = NIVEIS[self.estrelas]
        return [c for c in codigos if self.resultados[c].status in (REPROVADA, NAO_AVALIADA)]


def _texto(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def _chave(schema, tabela) -> tuple:
    return (_texto(schema).lower(), _texto(tabela).lower())


def _preenchido(v) -> Resultado:
    return Resultado(APROVADA if _texto(v) else REPROVADA, _texto(v) or "vazio")


def _avaliar_m4(descricao, tabela) -> Resultado:
    d = _texto(descricao)
    if not d:
        return Resultado(REPROVADA, "vazia")
    if len(d) < MIN_DESCRICAO:
        return Resultado(REPROVADA, f"{len(d)} caracteres")
    if d.lower() == _texto(tabela).lower():
        return Resultado(REPROVADA, "igual ao nome da tabela")
    return Resultado(APROVADA, f"{len(d)} caracteres")


def _avaliar_m8(atualizado_em, hoje: pd.Timestamp) -> Resultado:
    t = pd.to_datetime(atualizado_em, errors="coerce", utc=True)
    if pd.isna(t):
        return Resultado(NAO_AVALIADA, "sem data de atualização")
    dias = (hoje - t).days
    return Resultado(APROVADA if dias <= DIAS_REVISAO else REPROVADA, f"{dias} dias")


def _nivel(resultados: dict) -> int:
    estrelas = 0
    for n, _, codigos in NIVEIS:
        if all(resultados[c].status in (APROVADA, NAO_APLICAVEL) for c in codigos):
            estrelas = n
        else:
            break
    return estrelas


def avaliar(meta: pd.DataFrame, links: Optional[pd.DataFrame] = None, linhagem: Optional[pd.DataFrame] = None,
            qualidade: Optional[pd.DataFrame] = None, certificacao: Optional[pd.DataFrame] = None,
            hoje: Optional[pd.Timestamp] = None) -> list[Avaliacao]:
    if meta is None or meta.empty or not {"schema_name", "table_name"} <= set(meta.columns):
        return []
    hoje = hoje or pd.Timestamp.now(tz="UTC")
    links = links if links is not None else pd.DataFrame()
    linhagem = linhagem if linhagem is not None else pd.DataFrame()
    qualidade = qualidade if qualidade is not None else pd.DataFrame()
    certificacao = certificacao if certificacao is not None else pd.DataFrame()

    com_termo = ({_chave(s, t) for s, t in zip(links["schema_name"], links["table_name"])}
                 if {"schema_name", "table_name"} <= set(links.columns) else set())
    com_origem = ({_chave(s, t) for s, t in zip(linhagem["destino_schema"], linhagem["destino_tabela"])}
                  if {"destino_schema", "destino_tabela"} <= set(linhagem.columns) else None)
    medidas = ({_chave(r["schema_name"], r["table_name"]): r for _, r in qualidade.iterrows()}
               if {"schema_name", "table_name"} <= set(qualidade.columns) else {})
    certificados = ({_texto(t).lower() for t in certificacao.loc[certificacao["status_cert"] == "certificado", "table_name"]}
                    if {"status_cert", "table_name"} <= set(certificacao.columns) else set())

    saida = []
    for _, m in meta.iterrows():
        chave = _chave(m["schema_name"], m["table_name"])
        r: dict[str, Resultado] = {
            "M1": _preenchido(m.get("data_owner")),
            "M2": _preenchido(m.get("data_steward")),
            "M3": _preenchido(m.get("dominio")),
            "M4": _avaliar_m4(m.get("descricao"), m["table_name"]),
            "M5": (_preenchido(m.get("classificacao")) if "classificacao" in meta.columns
                   else Resultado(NAO_AVALIADA, "coluna de classificação ausente")),
            "M7": Resultado(APROVADA if chave in com_termo else REPROVADA,
                            "termo vinculado" if chave in com_termo else "nenhum termo"),
            "M8": (_avaliar_m8(m.get("atualizado_em"), hoje) if "atualizado_em" in meta.columns
                   else Resultado(NAO_AVALIADA, "sem data de atualização")),
        }
        if _texto(m.get("camada")).lower() == "bronze" or chave[0] == "bronze":
            r["M9"] = Resultado(NAO_APLICAVEL, "camada de origem")
        elif com_origem is None:
            r["M9"] = Resultado(NAO_AVALIADA, "linhagem indisponível")
        else:
            r["M9"] = Resultado(APROVADA if chave in com_origem else REPROVADA,
                                "origem registrada" if chave in com_origem else "sem origem")
        medida = medidas.get(chave)
        for codigo, (coluna, limite) in MEDICAO_QUALIDADE.items():
            valor = None if medida is None else medida.get(coluna)
            if valor is None or pd.isna(valor):
                r[codigo] = Resultado(NAO_AVALIADA, "sem medição")
            else:
                r[codigo] = Resultado(APROVADA if float(valor) >= limite else REPROVADA, f"{float(valor):.1f}%")
        r["R7"] = Resultado(NAO_AVALIADA, "total de controle não configurado")
        r["CERT"] = Resultado(APROVADA if chave[1] in certificados else REPROVADA,
                              "certificado" if chave[1] in certificados else "não certificado")

        av = Avaliacao(schema=_texto(m["schema_name"]), tabela=_texto(m["table_name"]), dominio=_texto(m.get("dominio")),
                       owner=_texto(m.get("data_owner")), steward=_texto(m.get("data_steward")), resultados=r)
        av.estrelas = _nivel(r)
        saida.append(av)
    return saida


def pendencias(avaliacoes: list[Avaliacao]) -> pd.DataFrame:
    """Uma linha por regra reprovada: o trabalho concreto de cada responsável."""
    linhas = [{"ativo": a.ativo, "dominio": a.dominio, "regra": c, "nome": REGRAS[c].nome,
               "observado": res.observado, "acao": REGRAS[c].acao, "responsavel": a.responsavel(c),
               "severidade": REGRAS[c].severidade, "estrelas": a.estrelas}
              for a in avaliacoes for c, res in a.resultados.items() if res.status == REPROVADA]
    ordem = {"critica": 0, "alta": 1, "media": 2}
    df = pd.DataFrame(linhas, columns=["ativo", "dominio", "regra", "nome", "observado", "acao", "responsavel",
                                       "severidade", "estrelas"])
    return df.sort_values(["severidade", "ativo"], key=lambda s: s.map(ordem) if s.name == "severidade" else s,
                          ignore_index=True) if not df.empty else df


def estrelas_txt(n: int) -> str:
    return "★" * n + "☆" * (5 - n)
