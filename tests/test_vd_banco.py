"""Testes de integração do Valor dos Dados no Databricks (schema de TESTE).

Executam contra workspace.meridian_governanca_teste (ver setup_schema_teste.sql).
Nunca contra produção: o teste aborta se o schema não terminar em '_teste'.
Os registros criados aqui são insumos de teste (prefixo TESTE-), não
evidência sobre dados de negócio, e somem com o DROP do schema de teste.

Variáveis de ambiente: DATABRICKS_HOST, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN,
VD_SCHEMA_TESTE (padrão meridian_governanca_teste).
Execução: PYTHONPATH=. pytest tests/test_vd_banco.py -v
"""
import os
import re
import uuid
from pathlib import Path

import pytest

import vd_regras as R

SQL = Path(__file__).resolve().parents[1] / "sql" / "valor_dos_dados"
SCHEMA = os.environ.get("VD_SCHEMA_TESTE", "meridian_governanca_teste")

pytestmark = pytest.mark.skipif(not os.environ.get("DATABRICKS_TOKEN"), reason="sem credenciais do Databricks")


# ── Infraestrutura ───────────────────────────────────────────────────
@pytest.fixture(scope="session")
def cur():
    assert SCHEMA.endswith("_teste"), "Os testes só rodam em schema de teste"
    from databricks import sql
    con = sql.connect(server_hostname=os.environ["DATABRICKS_HOST"], http_path=os.environ["DATABRICKS_HTTP_PATH"],
                      access_token=os.environ["DATABRICKS_TOKEN"])
    c = con.cursor()
    c.execute("USE CATALOG workspace")
    c.execute(f"USE SCHEMA {SCHEMA}")
    yield c
    c.close()
    con.close()


def rodar_arquivo(c, nome):
    txt = (SQL / nome).read_text(encoding="utf-8").replace("'meridian_governanca'", f"'{SCHEMA}'")
    sem_comentarios = "\n".join(l for l in txt.splitlines() if not l.strip().startswith("--"))
    for stmt in [s.strip() for s in re.split(r";\s*\n", sem_comentarios) if s.strip()]:
        c.execute(stmt)


def afetadas(c) -> int:
    row = c.fetchone()
    return int(row[0]) if row else 0


def tid():
    return f"TESTE-{uuid.uuid4().hex[:12]}"


def hist(c, tipo, ent_id, versao=1, acao="criacao", de=None, para=None, perfil="curador", usuario="teste@governantes"):
    c.execute(R.SQL_INSERIR_HISTORICO, dict(
        historico_id=tid(), chave_natural=R.chave(tipo, ent_id, str(versao), acao, de, para), entidade_tipo=tipo,
        entidade_id=ent_id, acao=acao, versao_entidade=versao, status_anterior=de, status_novo=para,
        campos_alterados=None, comentario=None, evidencia_id=None, usuario=usuario, perfil=perfil))


@pytest.fixture(scope="session")
def ambiente(cur):
    """Instala a v3 no schema de teste duas vezes (prova de idempotência)."""
    for _ in range(2):
        for arq in ("00_parametros_e_preverificacao.sql", "01_estruturas.sql", "02_dados_de_referencia.sql",
                    "03_validacoes_integridade.sql"):
            rodar_arquivo(cur, arq)
    return cur


@pytest.fixture(scope="session")
def ciclo(ambiente):
    """Cadeia completa válida: objetivo → processo → indicador → vínculo → execução → achado validado."""
    c = ambiente
    c.execute("SELECT schema_name, table_name, data_owner FROM tabelas_metadata WHERE data_owner IS NOT NULL AND data_owner <> '' LIMIT 1")
    schema, tabela, owner = c.fetchone()
    ids = {k: tid() for k in ("obj", "obj2", "proc", "ind", "vin", "exe", "ach")}
    for k, nome in (("obj", "Objetivo de teste A"), ("obj2", "Objetivo de teste B")):
        c.execute("""INSERT INTO vd_objetivos (objetivo_id, chave_natural, tipo, nome, area_negocio, resp_negocio,
                     resp_acompanhamento, prioridade, status, criterio_sucesso, origem, status_validacao, criado_por, criado_em, versao)
                     VALUES (:i, :k, 'objetivo', :n, 'Teste', :o, :o, 'alta', 'ativo', 'teste', 'manual', 'pendente',
                     'teste@governantes', current_timestamp(), 1)""", dict(i=ids[k], k=R.chave("objetivo", nome, "Teste"), n=nome, o=owner))
        hist(c, "objetivo", ids[k])
    c.execute("""INSERT INTO vd_processos (processo_id, chave_natural, objetivo_id, nome, area_negocio, resp_processo, criticidade,
                 status, origem, status_validacao, criado_por, criado_em, versao)
                 VALUES (:p, :k, :o, 'Processo de teste', 'Teste', :r, 'alta', 'ativo', 'manual', 'pendente', 'teste@governantes',
                 current_timestamp(), 1)""", dict(p=ids["proc"], k=R.chave(ids["obj"], "processo de teste"), o=ids["obj"], r=owner))
    hist(c, "processo", ids["proc"])
    c.execute("""INSERT INTO vd_indicadores (indicador_id, chave_natural, objetivo_id, processo_id, papel, nome, unidade, tipo_unidade,
                 sentido_melhora, formula, fonte, periodicidade, responsavel, status, origem, status_validacao, criado_por, criado_em, versao)
                 VALUES (:i, :k, :o, :p, 'principal', 'Horas de retrabalho', 'horas', 'tempo', 'reduzir', 'soma de horas', 'teste',
                 'mensal', :r, 'ativo', 'manual', 'pendente', 'teste@governantes', current_timestamp(), 1)""",
              dict(i=ids["ind"], k=R.chave(ids["obj"], "horas de retrabalho"), o=ids["obj"], p=ids["proc"], r=owner))
    hist(c, "indicador", ids["ind"])
    c.execute("""INSERT INTO vd_vinculos (vinculo_id, chave_natural, objetivo_id, origem_tipo, origem_id, ref_tipo, ref_schema, ref_nome,
                 papel_no_processo, status, origem, status_validacao, criado_por, criado_em, versao)
                 VALUES (:v, :k, :o, 'processo', :p, 'ativo', :s, :t, 'saida', 'ativo', 'manual', 'pendente', 'teste@governantes',
                 current_timestamp(), 1)""",
              dict(v=ids["vin"], k=R.chave("processo", ids["proc"], "ativo", None, schema, tabela), o=ids["obj"], p=ids["proc"],
                   s=schema, t=tabela))
    hist(c, "vinculo", ids["vin"])
    c.execute("""INSERT INTO vd_execucoes_diagnostico (execucao_id, objetivo_id, processo_id, versao_regras, versao_diagnostico,
                 executado_por, perfil, iniciado_em, finalizado_em, status, vinculos_analisados, achados_novos, achados_reincidentes,
                 achados_resolvidos) VALUES (:e, :o, :p, 'R1', :vd, 'teste@governantes', 'curador', current_timestamp(),
                 current_timestamp(), 'concluida', 1, 1, 0, 0)""", dict(e=ids["exe"], o=ids["obj"], p=ids["proc"], vd=R.VERSAO_DIAGNOSTICO))
    c.execute("""INSERT INTO vd_achados (achado_id, chave_natural, objetivo_id, processo_id, vinculo_id, regra_codigo, versao_regras,
                 natureza, evidencia_fato, valor_observado, situacao, primeira_execucao_id, ultima_execucao_id, primeira_deteccao_em,
                 ultima_deteccao_em, origem, status_validacao, validado_por, validado_em, criado_por, criado_em, versao)
                 VALUES (:a, :k, :o, :p, :v, 'DG-02', 'R1', 'nao_cadastrado', 'tabelas_metadata.data_steward', 'vazio', 'aberto',
                 :e, :e, current_timestamp(), current_timestamp(), 'calculado', 'validado', 'teste@governantes', current_timestamp(),
                 'teste@governantes', current_timestamp(), 1)""",
              dict(a=ids["ach"], k=R.chave(ids["obj"], ids["vin"], "DG-02"), o=ids["obj"], p=ids["proc"], v=ids["vin"], e=ids["exe"]))
    c.execute("""INSERT INTO vd_achados_ocorrencias VALUES (:oc, :k, :e, :v, 'DG-02', :a, 'disparou', 'nao_cadastrado', 'vazio',
                 NULL, current_timestamp())""", dict(oc=tid(), k=R.chave(ids["exe"], ids["vin"], "DG-02"), e=ids["exe"], v=ids["vin"], a=ids["ach"]))
    hist(c, "achado", ids["ach"])
    ids["owner"] = owner
    return ids


def params_intervencao(ids, objetivo=None, achado=None):
    return dict(intervencao_id=tid(), codigo=f"INT-{uuid.uuid4().hex[:6]}", titulo="Cadastrar steward", recomendacao="Designar steward",
                tipo_afirmacao="fato", causa_provavel=None, responsavel=ids["owner"], area="Teste", abrangencia_ativos=None,
                abrangencia_base=None, entrada_abrangencia="nao_determinada", esforco="baixo", criterio_conclusao="Steward cadastrado",
                usuario="teste@governantes", versao_modelo="P1", achado_id=achado or ids["ach"], objetivo_id=objetivo or ids["obj"])


# ════════════════════════════════════════════════════════════════════
# Idempotência e estrutura
# ════════════════════════════════════════════════════════════════════
def test_entrada_pendente_registrada_no_banco(ambiente):
    ambiente.execute("SELECT criterio, entrada FROM vd_modelo_priorizacao WHERE situacao = 'pendente'")
    assert {tuple(r) for r in ambiente.fetchall()} == R.PENDENTES_P1


def test_habilitacao_calculada_para_todas_as_regras(ambiente):
    ambiente.execute("SELECT COUNT(*) FROM vd_regras_habilitacao WHERE versao_regras = 'R1'")
    assert ambiente.fetchone()[0] == len(R.REGRAS_R1)


def test_reexecucao_nao_duplica_referencias(ambiente):
    c = ambiente
    for tabela, esperado in (("vd_regras_diagnostico", 9), ("vd_modelo_priorizacao", 19), ("vd_faixas_prioridade", 4),
                             ("vd_transicoes_intervencao", 15), ("vd_controle_versao", 1)):
        c.execute(f"SELECT COUNT(*) FROM {tabela}")
        assert c.fetchone()[0] == esperado, tabela


@pytest.mark.parametrize("tabela", ["vd_historico", "vd_evidencias", "vd_achados_ocorrencias"])
def test_tabelas_de_auditoria_sao_append_only(ambiente, tabela):
    ambiente.execute(f"SHOW TBLPROPERTIES {tabela} ('delta.appendOnly')")
    assert ambiente.fetchone()[1] == "true"


# ════════════════════════════════════════════════════════════════════
# Restrições impostas (cenários negativos)
# ════════════════════════════════════════════════════════════════════
def test_check_recusa_status_invalido(ciclo, cur):
    with pytest.raises(Exception, match="(?i)check|constraint"):
        cur.execute("UPDATE vd_vinculos SET status = 'apagado' WHERE vinculo_id = :v", dict(v=ciclo["vin"]))


def test_check_recusa_ativo_sem_papel(ciclo, cur):
    with pytest.raises(Exception, match="(?i)check|constraint"):
        cur.execute("""INSERT INTO vd_vinculos (vinculo_id, chave_natural, objetivo_id, origem_tipo, origem_id, ref_tipo, ref_schema,
                       ref_nome, status, origem, status_validacao, criado_por, criado_em, versao)
                       VALUES (:v, :v, :o, 'objetivo', :o, 'ativo', 'x', 'y', 'ativo', 'manual', 'pendente', 't', current_timestamp(), 1)""",
                    dict(v=tid(), o=ciclo["obj"]))


def test_check_recusa_nao_conforme_sem_criterio(ciclo, cur):
    with pytest.raises(Exception, match="(?i)check|constraint"):
        cur.execute("UPDATE vd_achados SET natureza = 'nao_conforme' WHERE achado_id = :a", dict(a=ciclo["ach"]))


def test_historico_nao_pode_ser_alterado(ciclo, cur):
    with pytest.raises(Exception, match="(?i)append|DELTA_CANNOT"):
        cur.execute("UPDATE vd_historico SET comentario = 'x' WHERE entidade_id = :a", dict(a=ciclo["ach"]))


def test_evidencia_nao_pode_ser_excluida(ciclo, cur):
    with pytest.raises(Exception, match="(?i)append|DELTA_CANNOT"):
        cur.execute("DELETE FROM vd_evidencias WHERE entidade_id = :a", dict(a=ciclo["ach"]))


# ════════════════════════════════════════════════════════════════════
# Gravações condicionadas (positivos e negativos)
# ════════════════════════════════════════════════════════════════════
def test_intervencao_de_outro_objetivo_e_recusada(ciclo, cur):
    cur.execute(R.SQL_INSERIR_INTERVENCAO, params_intervencao(ciclo, objetivo=ciclo["obj2"]))
    assert afetadas(cur) == 0


def test_intervencao_valida_e_dedupe(ciclo, cur):
    p = params_intervencao(ciclo)
    cur.execute(R.SQL_INSERIR_INTERVENCAO, p)
    assert afetadas(cur) == 1
    cur.execute(R.SQL_INSERIR_INTERVENCAO, {**p, "intervencao_id": tid(), "codigo": "INT-DUP"})
    assert afetadas(cur) == 0, "reexecução não pode duplicar"
    cur.execute("SELECT intervencao_id, pontuacao_total, prioridade FROM vd_intervencoes WHERE achado_id = :a", dict(a=ciclo["ach"]))
    iid, total, prio = cur.fetchone()
    esperado = R.priorizar("alta", "saida", "nao_cadastrado", None, "baixo")
    assert (total, prio) == (esperado.total, esperado.prioridade)
    hist(cur, "intervencao", iid)
    ciclo["int"] = iid


def test_transicoes(ciclo, cur):
    iid = ciclo["int"]
    base = dict(intervencao_id=iid, prazo="2026-12-31", justificativa=None, comentario=None, usuario="teste@governantes")
    cur.execute(R.SQL_TRANSICIONAR, {**base, "status_de": "identificada", "status_para": "concluida", "perfil": "aprovador", "versao_lida": 1})
    assert afetadas(cur) == 0, "pular etapas é recusado"
    cur.execute(R.SQL_TRANSICIONAR, {**base, "status_de": "identificada", "status_para": "em_analise", "perfil": "consultante", "versao_lida": 1})
    assert afetadas(cur) == 0, "perfil sem permissão é recusado"
    passos = [("identificada", "em_analise", "curador"), ("em_analise", "aprovada", "aprovador"),
              ("aprovada", "planejada", "curador"), ("planejada", "em_execucao", None)]
    versao = 1
    for de, para, perfil in passos:
        usuario = ciclo["owner"] if perfil is None else "teste@governantes"
        cur.execute(R.SQL_TRANSICIONAR, {**base, "usuario": usuario, "status_de": de, "status_para": para,
                                         "perfil": perfil or "consultante", "versao_lida": versao})
        assert afetadas(cur) == 1, f"{de} → {para}"
        versao += 1
        hist(cur, "intervencao", iid, versao, "transicao", de, para, perfil or "consultante", usuario)
    cur.execute(R.SQL_TRANSICIONAR, {**base, "usuario": ciclo["owner"], "status_de": "em_execucao", "status_para": "em_validacao",
                                     "perfil": "consultante", "versao_lida": versao})
    assert afetadas(cur) == 0, "sem evidência não vai para validação"
    cur.execute(R.SQL_TRANSICIONAR, {**base, "status_de": "em_execucao", "status_para": "planejada", "perfil": "curador",
                                     "versao_lida": versao - 1})
    assert afetadas(cur) == 0, "versão desatualizada é recusada"
    ciclo["versao_int"] = versao


def test_beneficio_calculado_e_coerente(ciclo, cur):
    """Leva a intervenção até 'concluida' e grava o benefício medido (fórmula F1)."""
    iid, versao, dono = ciclo["int"], ciclo["versao_int"], ciclo["owner"]
    conteudo = "https://exemplo.interno/ticket/TESTE"
    cur.execute(R.SQL_INSERIR_EVIDENCIA, dict(evidencia_id=tid(), chave_natural=R.chave_evidencia("intervencao", iid, conteudo),
                entidade_tipo="intervencao", entidade_id=iid, tipo="link", descricao="teste", conteudo=conteudo,
                origem="manual", usuario=dono, perfil="consultante"))
    base = dict(intervencao_id=iid, prazo=None, justificativa=None, comentario=None)
    for de, para, perfil, usuario in (("em_execucao", "em_validacao", "consultante", dono),
                                      ("em_validacao", "concluida", "aprovador", "teste@governantes")):
        cur.execute(R.SQL_TRANSICIONAR, {**base, "usuario": usuario, "status_de": de, "status_para": para, "perfil": perfil,
                                         "versao_lida": versao})
        assert afetadas(cur) == 1, f"{de} → {para}"
        versao += 1
        hist(cur, "intervencao", iid, versao, "transicao", de, para, perfil, usuario)
    med = {}
    for tipo, valor, data in (("linha_base", 16, "2026-09-01"), ("acompanhamento", 9, "2026-11-01")):
        med[tipo] = tid()
        cur.execute("""INSERT INTO vd_medicoes (medicao_id, chave_natural, indicador_id, objetivo_id, tipo, data_referencia, valor, metodo,
                       status, origem, status_validacao, validado_por, validado_em, criado_por, criado_em, versao)
                       VALUES (:m, :k, :i, :o, :t, :d, :v, 'teste', 'ativo', 'manual', 'validado', 'teste@governantes',
                       current_timestamp(), 'teste@governantes', current_timestamp(), 1)""",
                    dict(m=med[tipo], k=R.chave(ciclo["ind"], tipo, data), i=ciclo["ind"], o=ciclo["obj"], t=tipo, d=data, v=valor))
        hist(cur, "medicao", med[tipo])
    p = dict(beneficio_id=tid(), premissas="teste", valor_estimado=None, metodo_calculo="F1", usuario="teste@governantes",
             indicador_id=ciclo["ind"], intervencao_id=iid, medicao_antes_id=med["linha_base"],
             medicao_depois_id=med["acompanhamento"], conversao_id=None)
    cur.execute(R.SQL_INSERIR_BENEFICIO_MEDIDO, {**p, "medicao_antes_id": med["acompanhamento"], "medicao_depois_id": med["linha_base"]})
    assert afetadas(cur) == 0, "ordem invertida das medições é recusada"
    cur.execute(R.SQL_INSERIR_BENEFICIO_MEDIDO, {**p, "conversao_id": "NAO-EXISTE"})
    assert afetadas(cur) == 0, "conversão inexistente é recusada"
    cur.execute(R.SQL_INSERIR_BENEFICIO_MEDIDO, p)
    assert afetadas(cur) == 1
    cur.execute("SELECT melhoria, melhoria_pct, valor_financeiro FROM vd_beneficios WHERE intervencao_id = :i", dict(i=iid))
    melhoria, pct, fin = cur.fetchone()
    assert (float(melhoria), float(pct), fin) == (7.0, 43.75, None)
    with pytest.raises(Exception, match="(?i)check|constraint"):
        cur.execute("UPDATE vd_beneficios SET melhoria = 8 WHERE intervencao_id = :i", dict(i=iid))


# ════════════════════════════════════════════════════════════════════
# Validação posterior: a visão detecta desvio gravado fora da aplicação
# ════════════════════════════════════════════════════════════════════
def test_visao_detecta_processo_orfao(ciclo, cur):
    orfao = tid()
    cur.execute("""INSERT INTO vd_processos (processo_id, chave_natural, objetivo_id, nome, area_negocio, resp_processo, criticidade,
                   status, origem, status_validacao, criado_por, criado_em, versao)
                   VALUES (:p, :p, 'NAO-EXISTE', 'x', 'x', 'x', 'baixa', 'ativo', 'manual', 'pendente', 't', current_timestamp(), 1)""",
                dict(p=orfao))
    cur.execute("SELECT codigo FROM vd_v_integridade WHERE registro = :p", dict(p=orfao))
    assert {r[0] for r in cur.fetchall()} >= {"C01", "I03"}


def test_visao_detecta_prioridade_adulterada(ciclo, cur):
    cur.execute("UPDATE vd_intervencoes SET prioridade = 'baixa' WHERE intervencao_id = :i", dict(i=ciclo["int"]))
    cur.execute("SELECT codigo FROM vd_v_integridade WHERE registro = :i AND codigo = 'C09'", dict(i=ciclo["int"]))
    assert cur.fetchall(), "prioridade incoerente com o modelo deve ser apontada"
