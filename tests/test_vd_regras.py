"""Testes offline das regras do Valor dos Dados (sem banco).

Provam as regras de lógica (fórmulas, priorização, estados, coerência,
reconciliação) e a consistência entre o código e o SQL publicado.
Os registros abaixo são insumos de teste, não evidência sobre dados reais.
"""
import re
from datetime import date
from decimal import Decimal
from itertools import product
from pathlib import Path

import pytest
import sqlglot
from sqlglot import exp

import vd_regras as R

SQL = Path(__file__).resolve().parents[1] / "sql" / "valor_dos_dados"


# ── Repositório mínimo de teste ──────────────────────────────────────
@pytest.fixture
def repo():
    return R.Repositorio(
        objetivos={"O1": {"status": "ativo", "prioridade": "alta"}, "O2": {"status": "ativo"}, "OX": {"status": "cancelado"}},
        processos={"P1": {"objetivo_id": "O1"}, "P2": {"objetivo_id": "O2"}},
        indicadores={"I1": {"objetivo_id": "O1", "status": "ativo"}, "I2": {"objetivo_id": "O2", "status": "ativo"}},
        achados={
            "A1": {"objetivo_id": "O1", "status_validacao": "validado", "natureza": "nao_cadastrado", "situacao": "aberto"},
            "A2": {"objetivo_id": "O1", "status_validacao": "pendente", "natureza": "nao_cadastrado", "situacao": "aberto"},
            "A3": {"objetivo_id": "O1", "status_validacao": "validado", "natureza": "nao_aplicavel", "situacao": "aberto"},
        },
        intervencoes={"T1": {"objetivo_id": "O1", "achado_id": "A9", "status": "em_execucao"},
                      "T2": {"objetivo_id": "O2", "achado_id": "A8", "status": "planejada"}},
        ativos={("prata", "fato_credito")}, produtos={"PR1"}, termos={"G1"}, dominios={"Crédito"},
        responsaveis={"ana.lima@meridian.com"},
    )


# ════════════════════════════════════════════════════════════════════
# Coerência entre entidades (C01–C07)
# ════════════════════════════════════════════════════════════════════
class TestCoerencia:
    def test_processo_valido(self, repo):
        assert R.validar_processo(repo, {"objetivo_id": "O1", "resp_processo": "ana.lima@meridian.com"}) == []

    @pytest.mark.parametrize("obj", ["NAO_EXISTE", "OX"])
    def test_processo_objetivo_inexistente_ou_cancelado(self, repo, obj):
        assert any("C01" in e for e in R.validar_processo(repo, {"objetivo_id": obj, "resp_processo": "ana.lima@meridian.com"}))

    def test_responsavel_desconhecido(self, repo):
        assert any("vd_v_responsaveis" in e for e in R.validar_processo(repo, {"objetivo_id": "O1", "resp_processo": "x@y.com"}))

    def test_indicador_com_processo_de_outro_objetivo(self, repo):
        e = R.validar_indicador(repo, {"objetivo_id": "O1", "processo_id": "P2", "sentido_melhora": "reduzir",
                                       "responsavel": "ana.lima@meridian.com"})
        assert any("C02" in x and "outro objetivo" in x for x in e)

    def test_vinculo_ativo_valido(self, repo):
        assert R.validar_vinculo(repo, {"objetivo_id": "O1", "origem_tipo": "processo", "origem_id": "P1", "ref_tipo": "ativo",
                                        "ref_schema": "prata", "ref_nome": "fato_credito", "papel_no_processo": "saida",
                                        "origem": "manual"}) == []

    def test_vinculo_processo_de_outro_objetivo(self, repo):
        e = R.validar_vinculo(repo, {"objetivo_id": "O1", "origem_tipo": "processo", "origem_id": "P2", "ref_tipo": "produto",
                                     "ref_id": "PR1", "origem": "manual"})
        assert any("C03" in x for x in e)

    @pytest.mark.parametrize("vin,esperado", [
        ({"ref_tipo": "ativo", "ref_schema": "prata", "ref_nome": "nao_existe", "papel_no_processo": "fonte"}, "ativo não existe"),
        ({"ref_tipo": "ativo", "ref_schema": "prata", "ref_nome": "fato_credito"}, "Papel do ativo"),
        ({"ref_tipo": "produto", "ref_id": "PRX"}, "produto inexistente"),
        ({"ref_tipo": "termo_glossario", "ref_id": "GX"}, "termo"),
        ({"ref_tipo": "dominio", "ref_nome": "Inexistente"}, "domínio"),
        ({"ref_tipo": "responsavel", "ref_nome": "x@y.com"}, "responsável"),
        ({"ref_tipo": "indicador", "ref_id": "I2"}, "outro objetivo"),
        ({"ref_tipo": "regra_negocio", "ref_id": "R1"}, "não confirmada"),
        ({"ref_tipo": "produto", "ref_id": "PR1", "papel_no_processo": "saida"}, "só se aplica a ativos"),
    ])
    def test_referencias_invalidas(self, repo, vin, esperado):
        base = {"objetivo_id": "O1", "origem_tipo": "objetivo", "origem_id": "O1", "origem": "manual"}
        assert any(esperado in x for x in R.validar_vinculo(repo, {**base, **vin}))

    def test_regra_negocio_aceita_apos_confirmacao(self, repo):
        repo.chave_regra_confirmada, repo.regras = True, {"R1"}
        vin = {"objetivo_id": "O1", "origem_tipo": "objetivo", "origem_id": "O1", "ref_tipo": "regra_negocio",
               "ref_id": "R1", "origem": "manual"}
        assert R.validar_vinculo(repo, vin) == []

    def test_vinculo_por_metadado_exige_evidencia(self, repo):
        vin = {"objetivo_id": "O1", "origem_tipo": "objetivo", "origem_id": "O1", "ref_tipo": "produto", "ref_id": "PR1",
               "origem": "metadado"}
        assert any("comprova" in x for x in R.validar_vinculo(repo, vin))

    def test_intervencao_valida(self, repo):
        assert R.validar_intervencao_nova(repo, "A1", "O1") == []

    @pytest.mark.parametrize("achado,obj,esperado", [
        ("A1", "O2", "outro objetivo"),
        ("A2", "O1", "não validado"),
        ("A3", "O1", "não aplicável"),
        ("AX", "O1", "inexistente"),
    ])
    def test_intervencao_invalida(self, repo, achado, obj, esperado):
        assert any(esperado in x for x in R.validar_intervencao_nova(repo, achado, obj))

    def test_intervencao_duplicada_para_mesmo_achado(self, repo):
        repo.intervencoes["T3"] = {"objetivo_id": "O1", "achado_id": "A1", "status": "planejada"}
        assert any("não final" in x for x in R.validar_intervencao_nova(repo, "A1", "O1"))

    def test_medicao_objetivo_divergente(self, repo):
        assert any("C07" in x for x in R.validar_medicao(repo, {"indicador_id": "I1", "objetivo_id": "O2", "tipo": "linha_base"}))

    def test_medicao_intervencao_de_outro_objetivo(self, repo):
        e = R.validar_medicao(repo, {"indicador_id": "I1", "objetivo_id": "O1", "tipo": "acompanhamento", "intervencao_id": "T2"})
        assert any("intervenção" in x for x in e)


# ════════════════════════════════════════════════════════════════════
# Priorização P1
# ════════════════════════════════════════════════════════════════════
class TestPriorizacao:
    def test_exemplo_documentado(self):
        p = R.priorizar("alta", "saida", "nao_conforme", 7, "baixo")
        assert p.pontos == {"prioridade_objetivo": 3, "posicao_ativo": 3, "tipo_achado": 3, "abrangencia": 3, "esforco": 1}
        assert (p.total, p.prioridade) == (13, "critica")
        assert "= 13 → critica (modelo P1)" in p.explicacao()

    def test_desconhecidos_sao_neutros(self):
        p = R.priorizar("baixa", "fonte", "nao_identificado", None, None)
        assert p.entradas["abrangencia"] == "nao_determinada" and p.entradas["esforco"] == "nao_informado"
        assert p.pontos["abrangencia"] == 0 and p.pontos["esforco"] == 0

    @pytest.mark.parametrize("qtd,faixa", [(None, "nao_determinada"), (0, "0"), (1, "1-2"), (2, "1-2"),
                                           (3, "3-5"), (5, "3-5"), (6, "6+"), (40, "6+")])
    def test_faixas_de_abrangencia(self, qtd, faixa):
        assert R.faixa_abrangencia(qtd) == faixa

    def test_todas_as_combinacoes_tem_faixa_unica_e_limites(self):
        totais = set()
        for po, pa, ta, ab, es in product(["alta", "media", "baixa"], ["saida", "intermediario", "fonte"],
                                          ["nao_conforme", "nao_cadastrado", "nao_identificado"],
                                          [None, 0, 1, 4, 9], ["baixo", "medio", "alto", None]):
            p = R.priorizar(po, pa, ta, ab, es)
            totais.add(p.total)
            assert p.total == sum(p.pontos.values())
        assert min(totais) == 2 and max(totais) == 13

    def test_entrada_pendente_bloqueia_pontuacao(self):
        """Achado sobre produto (sem posição de ativo) depende de decisão não aprovada."""
        with pytest.raises(R.DecisaoPendente):
            R.priorizar("alta", None, "nao_cadastrado", None, "baixo")

    def test_nao_aplicavel_nao_gera_intervencao(self):
        with pytest.raises(ValueError):
            R.priorizar("alta", "saida", "nao_aplicavel", 1, "baixo")

    def test_entrada_invalida(self):
        with pytest.raises(ValueError):
            R.priorizar("urgente", "saida", "nao_conforme", 1, "baixo")

    def test_abrangencia_pela_linhagem(self):
        lin = [("bronze", "a", "prata", "b"), ("prata", "b", "ouro", "c"), ("prata", "b", "ouro", "d"), ("ouro", "c", "ouro", "b2")]
        assert R.abrangencia_jusante(("bronze", "a"), lin) == {("prata", "b"), ("ouro", "c"), ("ouro", "d"), ("ouro", "b2")}
        assert R.abrangencia_jusante(("ouro", "d"), lin) == set()
        assert R.abrangencia_jusante(("x", "sem_linhagem"), lin) is None

    def test_abrangencia_com_ciclo_termina(self):
        lin = [("s", "a", "s", "b"), ("s", "b", "s", "a")]
        assert R.abrangencia_jusante(("s", "a"), lin) == {("s", "b")}


# ════════════════════════════════════════════════════════════════════
# Benefícios F1
# ════════════════════════════════════════════════════════════════════
def _med(tipo, valor, dia, ind="I1", val="validado"):
    return {"indicador_id": ind, "tipo": tipo, "valor": valor, "data_referencia": date(2026, dia, 1), "status_validacao": val}


CONV = {"unidade_indicador": "horas", "unidade_custo": "hora", "fator": "1", "custo_unitario": "120.00", "moeda": "BRL",
        "fonte": "parâmetro informado pela organização", "status_validacao": "validado",
        "vigencia_inicio": date(2026, 1, 1), "vigencia_fim": None}


class TestBeneficio:
    def test_reduzir(self):
        c = R.calcular_beneficio("reduzir", "tempo", "horas", _med("linha_base", 16, 9), _med("acompanhamento", 9, 11), CONV)
        assert c.melhoria == Decimal("7.0000") and c.melhoria_pct == Decimal("43.7500")
        assert c.valor_financeiro == Decimal("840.00") and c.moeda == "BRL" and c.pode_validar

    def test_aumentar(self):
        c = R.calcular_beneficio("aumentar", "quantidade", "itens", _med("linha_base", 50, 9), _med("acompanhamento", 80, 10))
        assert c.melhoria == Decimal("30.0000") and c.valor_financeiro is None

    def test_piora_nao_pode_ser_validada(self):
        c = R.calcular_beneficio("reduzir", "tempo", "horas", _med("linha_base", 9, 9), _med("acompanhamento", 12, 10))
        assert c.melhoria == Decimal("-3.0000") and not c.pode_validar

    def test_linha_base_zero_sem_percentual(self):
        c = R.calcular_beneficio("aumentar", "quantidade", "itens", _med("linha_base", 0, 9), _med("acompanhamento", 5, 10))
        assert c.melhoria_pct is None

    @pytest.mark.parametrize("antes,depois,esperado", [
        (_med("linha_base", 16, 9), _med("acompanhamento", 9, 11, ind="I2"), "indicadores diferentes"),
        (_med("acompanhamento", 16, 9), _med("acompanhamento", 9, 11), "linha de base"),
        (_med("linha_base", 16, 11), _med("acompanhamento", 9, 9), "data de referência"),
        (_med("linha_base", 16, 9, val="pendente"), _med("acompanhamento", 9, 11), "validadas"),
    ])
    def test_medicoes_incompativeis(self, antes, depois, esperado):
        with pytest.raises(R.ErroIntegridade, match=esperado):
            R.calcular_beneficio("reduzir", "tempo", "horas", antes, depois)

    @pytest.mark.parametrize("ajuste,tipo_unidade,esperado", [
        ({}, "percentual", "percentual"),
        ({"unidade_indicador": "dias"}, "tempo", "unidade diferente"),
        ({"status_validacao": "pendente"}, "tempo", "não validada"),
        ({"vigencia_inicio": date(2026, 12, 1)}, "tempo", "vigência"),
    ])
    def test_conversao_invalida(self, ajuste, tipo_unidade, esperado):
        with pytest.raises(R.ErroIntegridade, match=esperado):
            R.calcular_beneficio("reduzir", tipo_unidade, "horas", _med("linha_base", 16, 9), _med("acompanhamento", 9, 11),
                                 {**CONV, **ajuste})


# ════════════════════════════════════════════════════════════════════
# Máquina de estados
# ════════════════════════════════════════════════════════════════════
INTERV = {"status": "em_execucao", "responsavel": "joao@meridian.com", "recomendacao": "x", "criterio_conclusao": "y",
          "prazo": date(2026, 12, 1)}


class TestTransicoes:
    def test_responsavel_envia_para_validacao_com_evidencia(self):
        assert R.validar_transicao(INTERV, "em_validacao", "consultante", "joao@meridian.com", tem_evidencia=True) == []

    def test_sem_evidencia(self):
        assert any("evidência" in e for e in R.validar_transicao(INTERV, "em_validacao", "consultante", "joao@meridian.com"))

    def test_outro_usuario_nao_e_responsavel(self):
        assert any("não pode" in e for e in R.validar_transicao(INTERV, "em_validacao", "consultante", "outro@meridian.com", tem_evidencia=True))

    def test_pular_etapa(self):
        assert any("não permitida" in e for e in R.validar_transicao({**INTERV, "status": "identificada"}, "concluida", "aprovador", "a"))

    def test_estado_final_nao_reabre(self):
        for final in R.FINAIS:
            for destino in R.STATUS_INTERVENCAO:
                assert R.validar_transicao({**INTERV, "status": final}, destino, "aprovador", "a")

    def test_so_aprovador_conclui(self):
        em_val = {**INTERV, "status": "em_validacao"}
        assert R.validar_transicao(em_val, "concluida", "aprovador", "a") == []
        assert R.validar_transicao(em_val, "concluida", "curador", "a")

    def test_devolucao_exige_comentario(self):
        assert any("Comentário" in e for e in R.validar_transicao({**INTERV, "status": "em_analise"}, "identificada", "curador", "a"))

    def test_cancelamento_exige_justificativa(self):
        assert any("justificativa" in e for e in R.validar_transicao(INTERV, "cancelada", "curador", "a"))

    def test_planejamento_exige_prazo(self):
        assert any("prazo" in e for e in R.validar_transicao({**INTERV, "status": "aprovada", "prazo": None}, "planejada", "curador", "a"))


# ════════════════════════════════════════════════════════════════════
# Diagnóstico: separação das naturezas e reconciliação entre execuções
# ════════════════════════════════════════════════════════════════════
META = {"data_owner": "ana@x", "data_steward": "", "classificacao": None}
KW = dict(papel="intermediario", limite_qualidade=80.0, qualidade=72.0, tem_qualidade=True, tem_linhagem_destino=True,
          termos_vinculados=1, colunas_opcionais={"tabelas_metadata.classificacao"})


class TestDiagnostico:
    def test_ausencia_e_nao_cadastrado(self):
        assert R.avaliar_ativo("DG-02", META, **KW)[:2] == ("disparou", "nao_cadastrado")

    def test_sem_fonte_e_nao_identificado(self):
        assert R.avaliar_ativo("DG-05", META, **{**KW, "tem_qualidade": False})[:2] == ("disparou", "nao_identificado")

    def test_so_criterio_violado_e_nao_conforme(self):
        assert R.avaliar_ativo("DG-06", META, **KW)[:2] == ("disparou", "nao_conforme")

    def test_sem_limite_nao_avalia_dg06(self):
        assert R.avaliar_ativo("DG-06", META, **{**KW, "limite_qualidade": None})[0].startswith("nao_avaliada")

    def test_sem_avaliacao_de_qualidade_nao_vira_nao_conforme(self):
        r = R.avaliar_ativo("DG-06", META, **{**KW, "tem_qualidade": False, "qualidade": None})
        assert r[0].startswith("nao_avaliada") and r[1] is None

    def test_coluna_opcional_ausente_desabilita_dg04(self):
        assert R.avaliar_ativo("DG-04", META, **{**KW, "colunas_opcionais": set()})[0].startswith("nao_avaliada")

    def test_fonte_nao_avalia_linhagem(self):
        assert R.avaliar_ativo("DG-07", META, **{**KW, "papel": "fonte", "tem_linhagem_destino": False})[0].startswith("nao_avaliada")

    def test_vinculo_ambiguo_e_nao_identificado(self):
        assert R.avaliar_ativo("DG-03", META, **{**KW, "termos_vinculados": None})[1] == "nao_identificado"

    def test_nenhuma_regra_produz_nao_conforme_por_ausencia(self):
        vazio = {"data_owner": None, "data_steward": None, "classificacao": None}
        for regra in ("DG-01", "DG-02", "DG-03", "DG-04", "DG-05", "DG-07"):
            r = R.avaliar_ativo(regra, vazio, papel="saida", limite_qualidade=None, qualidade=None, tem_qualidade=False,
                                tem_linhagem_destino=False, termos_vinculados=0,
                                colunas_opcionais={"tabelas_metadata.classificacao"})
            assert r[1] != "nao_conforme"

    def test_reconciliacao_sem_duplicar(self):
        existentes = {"k1": {"situacao": "aberto"}, "k2": {"situacao": "aberto"}, "k3": {"situacao": "resolvido"},
                      "k4": {"situacao": "aberto"}}
        disparados = {"k1": ("nao_cadastrado", "v"), "k3": ("nao_cadastrado", "v"), "k5": ("nao_identificado", "v")}
        acoes = {a.chave_natural: a.tipo for a in R.reconciliar(existentes, disparados, avaliados={"k1", "k2", "k3", "k5"})}
        assert acoes == {"k1": "reincidente", "k3": "reaberto", "k5": "novo", "k2": "resolvido"}
        # k4 não foi avaliado nesta execução: falta de avaliação não resolve o achado
        assert "k4" not in acoes

    def test_reexecucao_identica_nao_cria_novos(self):
        existentes = {"k1": {"situacao": "aberto"}}
        acoes = R.reconciliar(existentes, {"k1": ("nao_cadastrado", "v")}, {"k1"})
        assert [a.tipo for a in acoes] == ["reincidente"]

    def test_chave_natural_estavel(self):
        assert R.chave("Objetivo", " Reduzir  Retrabalho ", "Finanças") == R.chave("objetivo", "reduzir retrabalho", "financas")


# ════════════════════════════════════════════════════════════════════
# Consistência entre o código e o SQL publicado
# ════════════════════════════════════════════════════════════════════
def _values(view: str):
    txt = (SQL / "02_dados_de_referencia.sql").read_text(encoding="utf-8")
    bloco = re.search(rf"VIEW {view} AS\s*SELECT \* FROM VALUES(.*?)AS t\(", txt, re.S).group(1)
    return [tuple(x.strip().strip("'") for x in re.split(r",(?=(?:[^']*'[^']*')*[^']*$)", t))
            for t in re.findall(r"\(([^()]*(?:\([^()]*\)[^()]*)*)\)", bloco)]


def _colunas_tabela(tabela: str) -> list[str]:
    txt = (SQL / "01_estruturas.sql").read_text(encoding="utf-8")
    corpo = re.search(rf"CREATE TABLE IF NOT EXISTS {tabela} \((.*?)\n\)", txt, re.S).group(1)
    return [l.split()[0] for l in corpo.splitlines() if l.strip() and not l.strip().startswith(("CONSTRAINT", "--"))]


class TestCodigoIgualAoSQL:
    def test_modelo_p1(self):
        linhas = _values("vd_ref_modelo_p1")
        sql = {(c, e): int(p) for _, c, e, p, peso, _, _ in linhas}
        py = {(c, e): p for c, es in R.MODELO_P1.items() for e, p in es.items()}
        assert sql == py
        assert {(c, e) for _, c, e, _, _, _, sit in linhas if sit == "pendente"} == R.PENDENTES_P1

    def test_regras_r1_aplicacao(self):
        assert {r[0]: r[7] for r in _values("vd_ref_regras_r1")} == R.REGRAS_R1

    def test_intervencao_so_usa_entradas_aprovadas(self):
        assert R.SQL_INSERIR_INTERVENCAO.count(".situacao = 'aprovado'") == 5

    def test_transicao_no_banco_confere_precondicoes(self):
        for trecho in ("em_validacao", "'aprovada'", "'planejada'", "'cancelada'", ":comentario", "i.versao = :versao_lida",
                       "array_contains(split(tr.perfis"):
            assert trecho in R.SQL_TRANSICIONAR

    def test_faixas_p1(self):
        assert {(p, int(lo), int(hi)) for _, p, lo, hi in _values("vd_ref_faixas_p1")} == set(R.FAIXAS_P1)

    def test_transicoes(self):
        sql = {(d, p): tuple(perfis.split(",")) for d, p, perfis, _ in _values("vd_ref_transicoes")}
        assert sql == R.TRANSICOES

    @pytest.mark.parametrize("sql_const,tabela", [
        ("SQL_INSERIR_INTERVENCAO", "vd_intervencoes"),
        ("SQL_INSERIR_BENEFICIO_MEDIDO", "vd_beneficios"),
    ])
    def test_merge_traz_todas_as_colunas_na_ordem(self, sql_const, tabela):
        """INSERT * exige que a origem tenha exatamente as colunas da tabela."""
        texto = getattr(R, sql_const)
        arvore = sqlglot.parse_one(re.sub(r":(\w+)", r"'\1'", texto), read="databricks")
        origem = arvore.find(exp.Subquery).this
        assert [e.alias_or_name for e in origem.expressions] == _colunas_tabela(tabela)

    @pytest.mark.parametrize("sql_const,tabela", [("SQL_INSERIR_HISTORICO", "vd_historico"),
                                                  ("SQL_INSERIR_EVIDENCIA", "vd_evidencias")])
    def test_insert_posicional_tem_aridade_da_tabela(self, sql_const, tabela):
        texto = re.sub(r":(\w+)", r"'\1'", getattr(R, sql_const))
        sel = sqlglot.parse_one(texto, read="databricks").expression
        assert len(sel.expressions) == len(_colunas_tabela(tabela))

    def test_todos_os_sql_da_aplicacao_sao_validos(self):
        for nome in ("SQL_INSERIR_INTERVENCAO", "SQL_TRANSICIONAR", "SQL_INSERIR_BENEFICIO_MEDIDO",
                     "SQL_INSERIR_HISTORICO", "SQL_INSERIR_EVIDENCIA"):
            sqlglot.parse_one(re.sub(r":(\w+)", r"'\1'", getattr(R, nome)), read="databricks")

    def test_comandos_de_gravacao_novos_sao_validos(self):
        for nome in ("SQL_INSERIR_OCORRENCIA", "SQL_CONCLUIR_EXECUCAO"):
            sqlglot.parse_one(re.sub(r":(\w+)", r"'\1'", getattr(R, nome)), read="databricks")
        texto = re.sub(r":(\w+)", r"'\1'", R.SQL_INSERIR_OCORRENCIA)
        sel = sqlglot.parse_one(texto, read="databricks").expression
        assert len(sel.expressions) == len(_colunas_tabela("vd_achados_ocorrencias"))

    def test_verificacoes_sao_somente_leitura(self):
        for sql in R.VERIFICACOES.values():
            assert sqlglot.parse_one(re.sub(r":(\w+)", r"'\1'", sql), read="databricks").key == "select"

    def test_fonte_unica_de_responsaveis(self):
        sql03 = (SQL / "03_validacoes_integridade.sql").read_text(encoding="utf-8")
        assert "vd_v_responsaveis" in R.SQL_RESPONSAVEIS
        assert "CREATE OR REPLACE VIEW vd_v_responsaveis" in sql03
        assert sql03.count("LEFT ANTI JOIN vd_v_responsaveis") == 2      # C04 e C11
        assert "m.data_owner = v.ref_nome" not in sql03                 # regra antiga, divergente, removida


# ════════════════════════════════════════════════════════════════════
# Cobertura do diagnóstico (I04)
# ════════════════════════════════════════════════════════════════════
HAB = {c: (True, "ok") for c in R.REGRAS_R1}


class TestCobertura:
    def test_regras_por_tipo(self):
        assert R.regras_aplicaveis("ativo") == ["DG-01", "DG-02", "DG-03", "DG-04", "DG-05", "DG-06", "DG-07", "DG-09"]
        assert R.regras_aplicaveis("produto") == ["DG-08", "DG-09"]
        assert R.regras_aplicaveis("dominio") == ["DG-09"]

    def _res(self, vid, regras, resultado=("nao_disparou", None, None)):
        return {(vid, r): resultado for r in regras}

    def test_toda_regra_gera_ocorrencia_inclusive_sem_achado(self):
        res = self._res("V1", R.regras_aplicaveis("ativo")) | self._res("V2", ["DG-08", "DG-09"])
        oc = R.montar_ocorrencias({"V1": "ativo", "V2": "produto"}, HAB, res)
        assert len(oc) == 10 and {o.resultado for o in oc} == {"nao_disparou"}

    def test_regra_desabilitada_vira_nao_avaliada_com_motivo(self):
        hab = {**HAB, "DG-04": (False, "classificacao ausente")}
        res = self._res("V1", [r for r in R.regras_aplicaveis("ativo") if r != "DG-04"])
        oc = {o.regra_codigo: o for o in R.montar_ocorrencias({"V1": "ativo"}, hab, res)}
        assert oc["DG-04"].resultado == "nao_avaliada" and oc["DG-04"].motivo_nao_avaliada == "classificacao ausente"

    def test_resultado_para_regra_desabilitada_e_recusado(self):
        hab = {**HAB, "DG-04": (False, "x")}
        with pytest.raises(R.ErroIntegridade, match="desabilitada"):
            R.montar_ocorrencias({"V1": "ativo"}, hab, self._res("V1", R.regras_aplicaveis("ativo")))

    def test_execucao_incompleta_nao_conclui(self):
        res = self._res("V1", ["DG-01", "DG-02"])
        with pytest.raises(R.ErroIntegridade, match="incompleta"):
            R.montar_ocorrencias({"V1": "ativo"}, HAB, res)

    def test_resultado_e_natureza_coerentes(self):
        res = self._res("V1", ["DG-08", "DG-09"]) | {("V1", "DG-08"): ("disparou", None, "x")}
        with pytest.raises(R.ErroIntegridade, match="natureza"):
            R.montar_ocorrencias({"V1": "produto"}, HAB, res)


# ════════════════════════════════════════════════════════════════════
# Confirmação de gravações e atomicidade
# ════════════════════════════════════════════════════════════════════
class CursorFalso:
    """Cursor roteirizado. SELECT consome um valor devolvido por fetchone();
    INSERT/MERGE/UPDATE consome um valor de rowcount (-1 = conector não informa).
    Chamar fetchone() depois de uma gravação FALHA o teste: prova que o código não
    presume que INSERT/MERGE devolva linha com contagem."""

    def __init__(self, roteiro, fetchall=None):
        self.roteiro, self.executados, self._valor, self._ultimo_select = list(roteiro), [], None, False
        self.rowcount, self._fetchall = -1, fetchall or []

    def execute(self, sql, params=None):
        self.executados.append(sql.strip().split()[0].upper())
        r = self.roteiro.pop(0)
        if isinstance(r, Exception):
            raise r
        self._ultimo_select = sql.lstrip().upper().startswith("SELECT")
        if self._ultimo_select:
            self._valor, self.rowcount = r, -1
        else:
            self._valor, self.rowcount = None, r

    def fetchone(self):
        assert self._ultimo_select, "fetchone() chamado após INSERT/MERGE"
        return (self._valor,)

    def fetchall(self):
        return self._fetchall


INT = {"intervencao_id": "T1", "status": "em_analise", "versao": 2, "responsavel": "joao@x", "recomendacao": "r",
       "criterio_conclusao": "c", "prazo": None}
OK_TRANS = lambda rc=-1, rc_h=-1: [0, rc, 1, rc_h, 1]   # pendência, MERGE, leitura, histórico, leitura


class TestConfirmacao:
    @pytest.mark.parametrize("rc", [-1, 1], ids=["conector_sem_contagem", "conector_com_contagem"])
    def test_confirma_por_leitura_com_ou_sem_contagem_do_conector(self, rc):
        cur = CursorFalso(OK_TRANS(rc, rc))
        r = R.transicionar(cur, INT, "aprovada", "aprovador", "ana@x", historico_id="H1")
        assert r.confirmada and r.versao_nova == 3
        assert cur.executados == ["SELECT", "MERGE", "SELECT", "INSERT", "SELECT"]

    def test_leitura_sem_estado_esperado_recusa(self):
        with pytest.raises(R.ErroIntegridade, match="estado esperado não encontrado"):
            R.transicionar(CursorFalso([0, -1, 0]), INT, "aprovada", "aprovador", "ana@x", historico_id="H1")

    def test_contagem_do_conector_divergente_recusa(self):
        with pytest.raises(R.ErroIntegridade, match="divergência"):
            R.transicionar(CursorFalso([0, 2, 1]), INT, "aprovada", "aprovador", "ana@x", historico_id="H1")

    def test_repeticao_idempotente_do_historico_e_aceita(self):
        r = R.transicionar(CursorFalso([0, 1, 1, 0, 1]), INT, "aprovada", "aprovador", "ana@x", historico_id="H1")
        assert r.confirmada

    def test_falha_no_historico_nao_confirma(self):
        with pytest.raises(R.ErroAuditoria, match="NÃO confirmada"):
            R.transicionar(CursorFalso([0, 1, 1, -1, 0]), INT, "aprovada", "aprovador", "ana@x", historico_id="H1")

    def test_excecao_no_historico_nao_confirma(self):
        with pytest.raises(R.ErroAuditoria, match="NÃO confirmada"):
            R.transicionar(CursorFalso([0, 1, 1, RuntimeError("timeout")]), INT, "aprovada", "aprovador", "ana@x",
                           historico_id="H1")

    def test_entidade_com_pendencia_fica_bloqueada(self):
        cur = CursorFalso([1])
        with pytest.raises(R.ErroAuditoria, match="reconciliar"):
            R.transicionar(cur, INT, "aprovada", "aprovador", "ana@x", historico_id="H1")
        assert cur.executados == ["SELECT"], "nada é gravado"

    def test_recusa_no_banco_nao_grava_historico(self):
        cur = CursorFalso([0, 0, 0])
        with pytest.raises(R.ErroIntegridade, match="recusada"):
            R.transicionar(cur, INT, "aprovada", "aprovador", "ana@x", historico_id="H1")
        assert "INSERT" not in cur.executados

    def test_validacao_previa_impede_ir_ao_banco(self):
        cur = CursorFalso([])
        with pytest.raises(R.ErroIntegridade, match="Perfil"):
            R.transicionar(cur, INT, "aprovada", "curador", "ana@x", historico_id="H1")
        assert cur.executados == []

    def test_devolucao_sem_comentario_nao_vai_ao_banco(self):
        cur = CursorFalso([])
        with pytest.raises(R.ErroIntegridade, match="Comentário"):
            R.transicionar(cur, INT, "identificada", "curador", "ana@x", historico_id="H1")
        assert cur.executados == []

    def test_consulta_de_contagem_so_aceita_select(self):
        with pytest.raises(ValueError):
            R._consultar_contagem(CursorFalso([1]), "INSERT INTO x VALUES (1)", {})


class TestPersistenciaOcorrencias:
    def _ocorrencias(self):
        hab = {**{c: (True, "ok") for c in R.REGRAS_R1}, "DG-04": (False, "classificacao ausente")}
        res = {("V1", r): ("nao_disparou", None, None) for r in R.regras_aplicaveis("ativo") if r != "DG-04"}
        res[("V1", "DG-02")] = ("disparou", "nao_cadastrado", "vazio")
        return R.montar_ocorrencias({"V1": "ativo"}, hab, res)

    def test_grava_as_tres_situacoes_e_conclui(self):
        oc = self._ocorrencias()
        assert {o.resultado for o in oc} == {"disparou", "nao_disparou", "nao_avaliada"} and len(oc) == 8
        roteiro = [x for _ in oc for x in (1, 1)] + [len(oc), 1, 1]   # 8×(INSERT, leitura), contagem, MERGE, leitura
        cur = CursorFalso(roteiro)
        ids = iter(range(100))
        n = R.gravar_ocorrencias_e_concluir(cur, "E1", oc, {("V1", "DG-02"): "A1"}, lambda: f"id{next(ids)}",
                                            {"achados_novos": 1, "achados_reincidentes": 0, "achados_resolvidos": 0})
        assert n == 8 and cur.executados.count("INSERT") == 8 and cur.executados[-2:] == ["MERGE", "SELECT"]

    def test_nao_conclui_se_o_banco_tiver_menos_ocorrencias(self):
        oc = self._ocorrencias()
        roteiro = [x for _ in oc for x in (1, 1)] + [7]
        cur = CursorFalso(roteiro)
        with pytest.raises(R.ErroIntegridade, match="7 ocorrências no banco, 8 esperadas"):
            R.gravar_ocorrencias_e_concluir(cur, "E1", oc, {}, lambda: "x",
                                            {"achados_novos": 0, "achados_reincidentes": 0, "achados_resolvidos": 0})
        assert "MERGE" not in cur.executados

    def test_ocorrencia_nao_gravada_interrompe(self):
        oc = self._ocorrencias()
        with pytest.raises(R.ErroIntegridade, match="estado esperado"):
            R.gravar_ocorrencias_e_concluir(CursorFalso([1, 0]), "E1", oc, {}, lambda: "x", {})


class TestResponsaveis:
    def test_carrega_da_fonte_unica(self):
        cur = CursorFalso([None], fetchall=[("ana@x",), ("joao@x",)])
        assert R.carregar_responsaveis(cur) == {"ana@x", "joao@x"}
