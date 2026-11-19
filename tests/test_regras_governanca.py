"""Testes das regras de governança e do modelo de 5 estrelas (offline)."""
import pandas as pd
import pytest

import regras_governanca as G

HOJE = pd.Timestamp("2026-11-19", tz="UTC")
DESC = "Lançamentos contábeis consolidados por dia, usados no fechamento mensal."


def meta(**kw):
    base = dict(schema_name="prata", table_name="lancamentos", descricao=DESC, dominio="Contábil",
                data_owner="Ana Lima", data_steward="Maria Santos", classificacao="interno",
                camada="prata", atualizado_em=pd.Timestamp("2026-11-01", tz="UTC"))
    base.update(kw)
    return pd.DataFrame([base])


LINKS = pd.DataFrame([{"schema_name": "prata", "table_name": "lancamentos"}])
LIN = pd.DataFrame([{"origem_schema": "bronze", "origem_tabela": "raw", "destino_schema": "prata", "destino_tabela": "lancamentos"}])


def qual(**kw):
    base = dict(schema_name="prata", table_name="lancamentos", completude_pct=100.0, unicidade_pct=100.0,
                validade_pct=100.0, atualidade_pct=100.0, consistencia_pct=100.0)
    base.update(kw)
    return pd.DataFrame([base])


CERT = pd.DataFrame([{"table_name": "lancamentos", "status_cert": "certificado"}])


def um(m=None, **kw):
    args = dict(links=LINKS, linhagem=LIN, qualidade=qual(), certificacao=CERT, hoje=HOJE)
    args.update(kw)
    return G.avaliar(m if m is not None else meta(), **args)[0]


def test_ativo_completo_para_em_4_estrelas_enquanto_r7_nao_existe():
    a = um()
    assert a.estrelas == 4
    assert a.faltam_proxima() == ["R7"]


@pytest.mark.parametrize("campo,valor,esperado", [
    ("data_owner", "", 0), ("dominio", None, 0),
    ("data_steward", "", 1), ("descricao", "curta", 1), ("descricao", "lancamentos", 1), ("classificacao", "", 1),
])
def test_niveis_sao_cumulativos_e_param_na_primeira_falha(campo, valor, esperado):
    assert um(meta(**{campo: valor})).estrelas == esperado


@pytest.mark.parametrize("coluna,valor", [("unicidade_pct", 99.9), ("completude_pct", 97.9), ("atualidade_pct", 94.0)])
def test_falha_de_qualidade_critica_tira_a_terceira_estrela(coluna, valor):
    assert um(qualidade=qual(**{coluna: valor})).estrelas == 2


def test_sem_medicao_nao_conta_como_aprovada():
    a = um(qualidade=pd.DataFrame())
    assert a.estrelas == 2 and a.resultados["R1"].status == G.NAO_AVALIADA


def test_documentacao_antiga_e_sem_termo_tiram_a_quarta_estrela():
    assert um(meta(atualizado_em=pd.Timestamp("2026-01-01", tz="UTC"))).estrelas == 3
    assert um(links=pd.DataFrame()).estrelas == 3


def test_camada_bronze_nao_exige_linhagem():
    a = um(meta(schema_name="bronze", camada="bronze"), qualidade=qual(schema_name="bronze"),
           links=pd.DataFrame([{"schema_name": "bronze", "table_name": "lancamentos"}]))
    assert a.resultados["M9"].status == G.NAO_APLICAVEL and a.estrelas == 4


def test_pendencias_apontam_responsavel_e_ordenam_por_severidade():
    a = um(meta(data_steward=""), qualidade=qual(unicidade_pct=90.0))
    p = G.pendencias([a])
    assert list(p["regra"])[:1] == ["R1"]
    assert set(p["regra"]) >= {"M2", "R1", "CERT"} - {"CERT"}
    assert p.loc[p["regra"] == "M2", "responsavel"].iloc[0] == "Ana Lima"      # steward vazio → Owner indica
    assert p.loc[p["regra"] == "R1", "responsavel"].iloc[0] == "Ana Lima"      # sem steward, cai para o Owner


def test_tabela_sem_colunas_esperadas_nao_quebra():
    assert G.avaliar(pd.DataFrame()) == []
    a = G.avaliar(meta().drop(columns=["classificacao", "atualizado_em"]), hoje=HOJE)[0]
    assert a.resultados["M5"].status == G.NAO_AVALIADA and a.estrelas == 1


def test_estrelas_txt():
    assert G.estrelas_txt(3) == "★★★☆☆"
