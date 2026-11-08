"""Testes de integração do Valor dos Dados — HOMOLOGAÇÃO (schema de teste).

Travas contra gravação em produção (todas obrigatórias, verificadas antes de
qualquer comando de gravação):
  1. VD_SCHEMA_TESTE precisa terminar em '_teste' e ser diferente de VD_SCHEMA_PRODUCAO;
  2. depois do USE, o schema corrente é lido de volta e conferido;
  3. a credencial NÃO pode ter privilégio de gravação efetivo em produção — direto,
     herdado do catálogo ou herdado de grupo — nem ser dona (ela ou um grupo dela)
     do catálogo, do schema ou de tabelas de produção.
Em caso de falha, pytest.exit encerra a sessão antes de qualquer gravação.
Os registros criados são insumos de teste (prefixo TESTE-), não evidência sobre
dados de negócio, e são descartados com o DROP do schema de teste.

Variáveis: DATABRICKS_HOST, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN,
VD_SCHEMA_TESTE (padrão meridian_governanca_teste), VD_SCHEMA_PRODUCAO (padrão meridian_governanca).
Execução: PYTHONPATH=. pytest tests/test_vd_banco.py -v -p no:randomly --junitxml=homologacao.xml
Os testes são sequenciais (o ciclo avança de etapa em etapa).
"""
import json
import os
import re
import uuid
from pathlib import Path

import pytest

import vd_regras as R

SQL = Path(__file__).resolve().parents[1] / "sql" / "valor_dos_dados"
CATALOGO = "workspace"
TESTE = os.environ.get("VD_SCHEMA_TESTE", "meridian_governanca_teste")
PRODUCAO = os.environ.get("VD_SCHEMA_PRODUCAO", "meridian_governanca")
EVIDENCIAS = Path(os.environ.get("VD_EVIDENCIAS", "evidencias_homologacao.json"))

pytestmark = pytest.mark.skipif(not os.environ.get("DATABRICKS_TOKEN"), reason="sem credenciais do Databricks")
registro: dict = {}


def tid():
    return f"TESTE-{uuid.uuid4().hex[:12]}"


# ════════════════════════════════════════════════════════════════════
# Travas de segurança (funções puras, também exercitadas offline em
# tests/test_isolamento_producao.py)
# ════════════════════════════════════════════════════════════════════
# Privilégios que permitiriam gravar ou criar objetos em produção. No catálogo
# eles são herdados por todos os schemas, por isso também são verificados lá.
PRIVILEGIOS_DE_GRAVACAO = {"MODIFY", "ALL PRIVILEGES", "MANAGE", "CREATE TABLE", "CREATE MATERIALIZED VIEW",
                           "CREATE FUNCTION", "CREATE VOLUME", "CREATE MODEL"}

# Privilégios efetivos: concedidos ao próprio principal OU a qualquer grupo do qual
# ele faça parte (SHOW GRANTS `principal` não mostra os herdados de grupos).
SQL_PRIVILEGIOS_PRODUCAO = """
SELECT 'catalogo' AS nivel, catalog_name AS objeto, grantee, privilege_type
FROM {cat}.information_schema.catalog_privileges
WHERE catalog_name = :cat AND (grantee = current_user() OR is_account_group_member(grantee))
UNION ALL
SELECT 'schema', schema_name, grantee, privilege_type
FROM {cat}.information_schema.schema_privileges
WHERE schema_name = :prod AND (grantee = current_user() OR is_account_group_member(grantee))
UNION ALL
SELECT 'tabela', table_name, grantee, privilege_type
FROM {cat}.information_schema.table_privileges
WHERE table_schema = :prod AND (grantee = current_user() OR is_account_group_member(grantee))
"""

# Dono de catálogo, schema ou tabela tem todos os direitos, sem precisar de GRANT.
SQL_PROPRIEDADE_PRODUCAO = """
SELECT 'catalogo' AS nivel, catalog_name AS objeto, catalog_owner AS dono FROM {cat}.information_schema.catalogs
WHERE catalog_name = :cat AND (catalog_owner = current_user() OR is_account_group_member(catalog_owner))
UNION ALL
SELECT 'schema', schema_name, schema_owner FROM {cat}.information_schema.schemata
WHERE schema_name = :prod AND (schema_owner = current_user() OR is_account_group_member(schema_owner))
UNION ALL
SELECT 'tabela', table_name, table_owner FROM {cat}.information_schema.tables
WHERE table_schema = :prod AND (table_owner = current_user() OR is_account_group_member(table_owner))
"""


class TravaAcionada(AssertionError):
    pass


def verificar_travas(c, catalogo=CATALOGO, teste=TESTE, producao=PRODUCAO) -> dict:
    """Executada antes de qualquer gravação. Só emite SELECT, USE e consultas ao
    information_schema. Qualquer falha interrompe toda a sessão de testes."""
    if not (teste.endswith("_teste") and teste != producao):
        raise TravaAcionada(f"trava 1: schema de teste inválido ({teste})")
    c.execute(f"USE CATALOG {catalogo}")
    c.execute(f"USE SCHEMA {teste}")
    c.execute("SELECT current_catalog(), current_schema(), current_user()")
    cat, sch, usuario = c.fetchone()
    if (cat, sch) != (catalogo, teste):
        raise TravaAcionada(f"trava 2: schema corrente é {cat}.{sch}, esperado {catalogo}.{teste}")
    params = {"cat": catalogo, "prod": producao}
    c.execute(SQL_PRIVILEGIOS_PRODUCAO.format(cat=catalogo), params)
    privilegios = [tuple(r) for r in c.fetchall()]
    indevidos = [p for p in privilegios if str(p[3]).upper() in PRIVILEGIOS_DE_GRAVACAO]
    if indevidos:
        raise TravaAcionada(f"trava 3: a credencial pode gravar em produção: {indevidos}")
    c.execute(SQL_PROPRIEDADE_PRODUCAO.format(cat=catalogo), params)
    propriedades = [tuple(r) for r in c.fetchall()]
    if propriedades:
        raise TravaAcionada(f"trava 3: a credencial (ou um grupo dela) é dona de objetos de produção: {propriedades}")
    return {"catalogo": cat, "schema_teste": sch, "usuario": usuario,
            "privilegios_efetivos_producao": privilegios, "propriedade_producao": propriedades}


def preparar_sql(nome, teste=TESTE, producao=PRODUCAO) -> list:
    """Lê um arquivo 00–03, aponta o parâmetro de schema para o teste e recusa o
    arquivo se restar qualquer referência ao schema de produção."""
    txt = (SQL / nome).read_text(encoding="utf-8")
    sem_comentarios = "\n".join(l for l in txt.splitlines() if not l.strip().startswith("--"))
    ajustado = sem_comentarios.replace(f"'{producao}'", f"'{teste}'")
    restos = re.findall(rf"\b{re.escape(producao)}\b(?!_)", ajustado.replace(teste, ""))
    if restos:
        raise TravaAcionada(f"{nome}: referência ao schema de produção remanescente")
    return [s.strip() for s in re.split(r";\s*\n", ajustado) if s.strip()]


def rodar_arquivo(c, nome, teste=TESTE):
    for stmt in preparar_sql(nome, teste=teste):
        c.execute(stmt)
        if stmt.upper().startswith("USE "):                     # cada troca de contexto é conferida
            c.execute("SELECT current_schema()")
            atual = c.fetchone()[0]
            if atual != teste:
                raise TravaAcionada(f"{nome}: o schema corrente passou a ser {atual}")
    c.execute("SELECT current_schema()")
    if c.fetchone()[0] != teste:
        raise TravaAcionada(f"{nome} alterou o schema corrente")


# ════════════════════════════════════════════════════════════════════
# Conexão
# ════════════════════════════════════════════════════════════════════
@pytest.fixture(scope="session")
def cur():
    from databricks import sql
    con = sql.connect(server_hostname=os.environ["DATABRICKS_HOST"], http_path=os.environ["DATABRICKS_HTTP_PATH"],
                      access_token=os.environ["DATABRICKS_TOKEN"])
    c = con.cursor()
    try:
        registro["ambiente"] = verificar_travas(c)
    except TravaAcionada as exc:
        c.close()
        con.close()
        pytest.exit(str(exc), returncode=3)                    # encerra a sessão inteira, sem nenhuma gravação
    yield c
    c.close()
    con.close()
    EVIDENCIAS.write_text(json.dumps(registro, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def contar(c, sql, params=None) -> int:
    c.execute(sql, params or {})
    return int(c.fetchone()[0])


def hist(c, tipo, ent_id, versao=1, acao="criacao", de=None, para=None, perfil="curador", usuario="teste@governantes"):
    p = dict(historico_id=tid(), chave_natural=R.chave(tipo, ent_id, str(versao), acao), entidade_tipo=tipo,
             entidade_id=ent_id, acao=acao, versao_entidade=versao, status_anterior=de, status_novo=para,
             campos_alterados=None, comentario=None, evidencia_id=None, usuario=usuario, perfil=perfil)
    R.executar_gravacao(c, f"histórico {tipo}", R.SQL_INSERIR_HISTORICO, p, "historico",
                        {"chave_natural": p["chave_natural"]}, aceita_ja_existente=True)


def inserir(c, sql, params, tabela, coluna_id, valor_id):
    """Inclusão de insumo de teste confirmada por leitura (não por fetchone)."""
    c.execute(sql, params)
    assert contar(c, f"SELECT COUNT(*) FROM {tabela} WHERE {coluna_id} = :i", {"i": valor_id}) == 1


# ════════════════════════════════════════════════════════════════════
# Instalação (duas vezes = prova de idempotência)
# ════════════════════════════════════════════════════════════════════
@pytest.fixture(scope="session")
def ambiente(cur):
    for rodada in (1, 2):
        for arq in ("00_parametros_e_preverificacao.sql", "01_estruturas.sql", "02_dados_de_referencia.sql",
                    "03_validacoes_integridade.sql"):
            rodar_arquivo(cur, arq)
    cur.execute("SELECT regra_codigo, habilitada, motivo FROM vd_regras_habilitacao WHERE versao_regras = 'R1'")
    registro["habilitacao"] = {r[0]: {"habilitada": r[1], "motivo": r[2]} for r in cur.fetchall()}
    return cur


def test_reinstalacao_nao_duplica(ambiente):
    for tabela, esperado in (("vd_regras_diagnostico", 9), ("vd_modelo_priorizacao", 19), ("vd_faixas_prioridade", 4),
                             ("vd_transicoes_intervencao", 15), ("vd_controle_versao", 1), ("vd_regras_habilitacao", 9)):
        assert contar(ambiente, f"SELECT COUNT(*) FROM {tabela}") == esperado, tabela


def test_entrada_pendente_do_modelo_continua_bloqueada(ambiente):
    ambiente.execute("SELECT criterio, entrada FROM vd_modelo_priorizacao WHERE situacao = 'pendente'")
    assert {tuple(r) for r in ambiente.fetchall()} == R.PENDENTES_P1


@pytest.mark.parametrize("tabela", ["vd_historico", "vd_evidencias", "vd_achados_ocorrencias"])
def test_auditoria_append_only(ambiente, tabela):
    ambiente.execute(f"SHOW TBLPROPERTIES {tabela} ('delta.appendOnly')")
    assert ambiente.fetchone()[1] == "true"


# ════════════════════════════════════════════════════════════════════
# Ciclo do piloto, pelas funções da aplicação
# ════════════════════════════════════════════════════════════════════
@pytest.fixture(scope="session")
def ciclo(ambiente):
    c = ambiente
    responsaveis = R.carregar_responsaveis(c)
    assert responsaveis, "vd_v_responsaveis vazia: o catálogo não tem Owners/Stewards"
    c.execute("""SELECT m.schema_name, m.table_name FROM tabelas_metadata m
                 JOIN vd_v_responsaveis r ON r.email = m.data_owner LIMIT 1""")
    schema, tabela = c.fetchone()
    dono = sorted(responsaveis)[0]
    ids = {k: tid() for k in ("obj", "obj2", "proc", "ind", "vin", "exe", "ach")}
    for k, nome in (("obj", "Objetivo de teste A"), ("obj2", "Objetivo de teste B")):
        inserir(c, """INSERT INTO vd_objetivos (objetivo_id, chave_natural, tipo, nome, area_negocio, resp_negocio,
                      resp_acompanhamento, prioridade, status, criterio_sucesso, origem, status_validacao, criado_por, criado_em, versao)
                      VALUES (:i, :k, 'objetivo', :n, 'Teste', :o, :o, 'alta', 'ativo', 'teste', 'manual', 'pendente',
                      'teste@governantes', current_timestamp(), 1)""",
                dict(i=ids[k], k=R.chave("objetivo", nome, "Teste"), n=nome, o=dono), "vd_objetivos", "objetivo_id", ids[k])
        hist(c, "objetivo", ids[k])
    inserir(c, """INSERT INTO vd_processos (processo_id, chave_natural, objetivo_id, nome, area_negocio, resp_processo, criticidade,
                  status, origem, status_validacao, criado_por, criado_em, versao)
                  VALUES (:p, :k, :o, 'Processo de teste', 'Teste', :r, 'alta', 'ativo', 'manual', 'pendente', 'teste@governantes',
                  current_timestamp(), 1)""", dict(p=ids["proc"], k=R.chave(ids["obj"], "processo"), o=ids["obj"], r=dono),
            "vd_processos", "processo_id", ids["proc"])
    hist(c, "processo", ids["proc"])
    inserir(c, """INSERT INTO vd_indicadores (indicador_id, chave_natural, objetivo_id, processo_id, papel, nome, unidade, tipo_unidade,
                  sentido_melhora, formula, fonte, periodicidade, responsavel, status, origem, status_validacao, criado_por, criado_em, versao)
                  VALUES (:i, :k, :o, :p, 'principal', 'Horas de retrabalho', 'horas', 'tempo', 'reduzir', 'soma', 'teste',
                  'mensal', :r, 'ativo', 'manual', 'pendente', 'teste@governantes', current_timestamp(), 1)""",
            dict(i=ids["ind"], k=R.chave(ids["obj"], "horas"), o=ids["obj"], p=ids["proc"], r=dono),
            "vd_indicadores", "indicador_id", ids["ind"])
    hist(c, "indicador", ids["ind"])
    inserir(c, """INSERT INTO vd_vinculos (vinculo_id, chave_natural, objetivo_id, origem_tipo, origem_id, ref_tipo, ref_schema, ref_nome,
                  papel_no_processo, status, origem, status_validacao, criado_por, criado_em, versao)
                  VALUES (:v, :k, :o, 'processo', :p, 'ativo', :s, :t, 'saida', 'ativo', 'manual', 'pendente', 'teste@governantes',
                  current_timestamp(), 1)""",
            dict(v=ids["vin"], k=R.chave("processo", ids["proc"], "ativo", None, schema, tabela), o=ids["obj"], p=ids["proc"],
                 s=schema, t=tabela), "vd_vinculos", "vinculo_id", ids["vin"])
    hist(c, "vinculo", ids["vin"])
    inserir(c, """INSERT INTO vd_execucoes_diagnostico (execucao_id, objetivo_id, processo_id, versao_regras, versao_diagnostico,
                  executado_por, perfil, iniciado_em, status, regras_desabilitadas, motivos_desabilitacao)
                  VALUES (:e, :o, :p, 'R1', :vd, 'teste@governantes', 'curador', current_timestamp(), 'em_execucao', :des, :mot)""",
            dict(e=ids["exe"], o=ids["obj"], p=ids["proc"], vd=R.VERSAO_DIAGNOSTICO,
                 des=",".join(k for k, v in registro["habilitacao"].items() if not v["habilitada"]),
                 mot=json.dumps({k: v["motivo"] for k, v in registro["habilitacao"].items() if not v["habilitada"]},
                                ensure_ascii=False)),
            "vd_execucoes_diagnostico", "execucao_id", ids["exe"])
    inserir(c, """INSERT INTO vd_achados (achado_id, chave_natural, objetivo_id, processo_id, vinculo_id, regra_codigo, versao_regras,
                  natureza, evidencia_fato, valor_observado, situacao, primeira_execucao_id, ultima_execucao_id, primeira_deteccao_em,
                  ultima_deteccao_em, origem, status_validacao, validado_por, validado_em, criado_por, criado_em, versao)
                  VALUES (:a, :k, :o, :p, :v, 'DG-02', 'R1', 'nao_cadastrado', 'tabelas_metadata.data_steward', 'vazio', 'aberto',
                  :e, :e, current_timestamp(), current_timestamp(), 'calculado', 'validado', 'teste@governantes', current_timestamp(),
                  'teste@governantes', current_timestamp(), 1)""",
            dict(a=ids["ach"], k=R.chave(ids["obj"], ids["vin"], "DG-02"), o=ids["obj"], p=ids["proc"], v=ids["vin"], e=ids["exe"]),
            "vd_achados", "achado_id", ids["ach"])
    hist(c, "achado", ids["ach"])
    ids.update(dono=dono)
    return ids


def test_ocorrencias_das_tres_situacoes_sao_gravadas(ciclo, cur):
    """Item 3: todas as ocorrências — disparou, nao_disparou e nao_avaliada — chegam ao banco."""
    hab = {k: (v["habilitada"], v["motivo"]) for k, v in registro["habilitacao"].items()}
    habilitadas = [r for r in R.regras_aplicaveis("ativo") if hab[r][0]]
    assert "DG-02" in habilitadas and len(habilitadas) >= 3, f"pré-condição: regras habilitadas {habilitadas}"
    resultados = {(ciclo["vin"], r): ("nao_disparou", None, None) for r in habilitadas}
    resultados[(ciclo["vin"], "DG-02")] = ("disparou", "nao_cadastrado", "vazio")
    sem_avaliacao = next(r for r in habilitadas if r != "DG-02")
    resultados[(ciclo["vin"], sem_avaliacao)] = ("nao_avaliada:insumo indisponível no teste", None, None)
    oc = R.montar_ocorrencias({ciclo["vin"]: "ativo"}, hab, resultados)
    R.gravar_ocorrencias_e_concluir(cur, ciclo["exe"], oc, {(ciclo["vin"], "DG-02"): ciclo["ach"]}, tid,
                                    {"achados_novos": 1, "achados_reincidentes": 0, "achados_resolvidos": 0})
    cur.execute("SELECT resultado, COUNT(*) FROM vd_achados_ocorrencias WHERE execucao_id = :e GROUP BY resultado",
                {"e": ciclo["exe"]})
    por_resultado = dict(cur.fetchall())
    registro["ocorrencias"] = por_resultado
    assert set(por_resultado) == {"disparou", "nao_disparou", "nao_avaliada"}
    assert sum(por_resultado.values()) == len(R.regras_aplicaveis("ativo"))
    assert contar(cur, """SELECT COUNT(*) FROM vd_v_integridade WHERE codigo = 'I04' AND (registro LIKE :p
                  OR registro IN (SELECT ocorrencia_id FROM vd_achados_ocorrencias WHERE execucao_id = :e))""",
                  {"p": f"{ciclo['exe']}%", "e": ciclo["exe"]}) == 0
    # reexecutar a gravação não duplica ocorrências
    for o in oc:
        cur.execute(R.SQL_INSERIR_OCORRENCIA, {"ocorrencia_id": tid(), "chave_natural": R.chave(ciclo["exe"], o.vinculo_id, o.regra_codigo),
                                               "execucao_id": ciclo["exe"], "vinculo_id": o.vinculo_id, "regra_codigo": o.regra_codigo,
                                               "achado_id": None, "resultado": o.resultado, "natureza": o.natureza,
                                               "valor_observado": o.valor_observado, "motivo_nao_avaliada": o.motivo_nao_avaliada})
    assert contar(cur, R.VERIFICACOES["ocorrencias"], {"execucao_id": ciclo["exe"]}) == len(oc)


def test_comportamento_do_conector_registrado(ciclo, cur):
    """Item 1: registra o que o conector real informa após uma inclusão e confirma pela leitura."""
    conteudo = f"teste-conector-{tid()}"
    p = dict(evidencia_id=tid(), chave_natural=R.chave_evidencia("achado", ciclo["ach"], conteudo), entidade_tipo="achado",
             entidade_id=ciclo["ach"], tipo="texto", descricao="teste do conector", conteudo=conteudo, origem="manual",
             usuario="teste@governantes", perfil="curador")
    cur.execute(R.SQL_INSERIR_EVIDENCIA, p)
    informado = cur.rowcount
    lido = contar(cur, R.VERIFICACOES["evidencia"], {"chave_natural": p["chave_natural"]})
    from importlib.metadata import version
    registro["conector"] = {"versao": version("databricks-sql-connector"),
                            "rowcount_apos_insert": informado, "leitura_posterior": lido}
    assert lido == 1
    assert informado in (-1, 1), f"rowcount inesperado: {informado}"
    cur.execute(R.SQL_INSERIR_EVIDENCIA, {**p, "evidencia_id": tid()})
    registro["conector"]["rowcount_apos_insert_repetido"] = cur.rowcount
    assert contar(cur, R.VERIFICACOES["evidencia"], {"chave_natural": p["chave_natural"]}) == 1


def _p_intervencao(ids, objetivo=None):
    return dict(intervencao_id=tid(), codigo=f"INT-{uuid.uuid4().hex[:6]}", titulo="Cadastrar steward", recomendacao="Designar steward",
                tipo_afirmacao="fato", causa_provavel=None, responsavel=ids["dono"], area="Teste", abrangencia_ativos=None,
                abrangencia_base=None, entrada_abrangencia="nao_determinada", esforco="baixo", criterio_conclusao="Steward cadastrado",
                usuario="teste@governantes", versao_modelo="P1", achado_id=ids["ach"], objetivo_id=objetivo or ids["obj"])


def test_intervencao_de_outro_objetivo_e_recusada(ciclo, cur):
    p = _p_intervencao(ciclo, objetivo=ciclo["obj2"])
    with pytest.raises(R.ErroIntegridade, match="estado esperado"):
        R.executar_gravacao(cur, "intervenção", R.SQL_INSERIR_INTERVENCAO, p, "intervencao_inserida",
                            {"intervencao_id": p["intervencao_id"]})


def test_intervencao_valida_sem_duplicar(ciclo, cur):
    p = _p_intervencao(ciclo)
    h = dict(historico_id=tid(), chave_natural=R.chave("intervencao", p["intervencao_id"], "1", "criacao"),
             entidade_tipo="intervencao", entidade_id=p["intervencao_id"], acao="criacao", versao_entidade=1,
             status_anterior=None, status_novo="identificada", campos_alterados=None, comentario=None, evidencia_id=None,
             usuario="teste@governantes", perfil="curador")
    r = R.executar_com_historico(cur, "Abrir intervenção", R.SQL_INSERIR_INTERVENCAO, p, "intervencao_inserida",
                                 {"intervencao_id": p["intervencao_id"]}, h, "intervencao", p["intervencao_id"])
    assert r.confirmada
    p2 = {**p, "intervencao_id": tid(), "codigo": "INT-DUP"}
    with pytest.raises(R.ErroIntegridade):
        R.executar_gravacao(cur, "duplicada", R.SQL_INSERIR_INTERVENCAO, p2, "intervencao_inserida",
                            {"intervencao_id": p2["intervencao_id"]})
    cur.execute("SELECT pontuacao_total, prioridade FROM vd_intervencoes WHERE intervencao_id = :i", {"i": p["intervencao_id"]})
    esperado = R.priorizar("alta", "saida", "nao_cadastrado", None, "baixo")
    assert tuple(cur.fetchone()) == (esperado.total, esperado.prioridade)
    ciclo["int"] = p["intervencao_id"]


def _interv(cur, iid):
    cur.execute("SELECT intervencao_id, status, versao, responsavel, recomendacao, criterio_conclusao, prazo "
                "FROM vd_intervencoes WHERE intervencao_id = :i", {"i": iid})
    return dict(zip(("intervencao_id", "status", "versao", "responsavel", "recomendacao", "criterio_conclusao", "prazo"),
                    cur.fetchone()))


def test_guarda_do_banco_recusa_transicao_invalida(ciclo, cur):
    """Chamada direta ao SQL, sem a validação prévia: o próprio banco recusa."""
    it = _interv(cur, ciclo["int"])
    base = dict(intervencao_id=it["intervencao_id"], prazo=None, justificativa=None, comentario=None, usuario="teste@governantes",
                versao_lida=it["versao"])
    for de, para, perfil in (("identificada", "concluida", "aprovador"), ("identificada", "em_analise", "consultante")):
        with pytest.raises(R.ErroIntegridade):
            R.executar_gravacao(cur, "inválida", R.SQL_TRANSICIONAR, {**base, "status_de": de, "status_para": para, "perfil": perfil},
                                "transicao", {"intervencao_id": it["intervencao_id"], "status_para": para,
                                              "versao_nova": it["versao"] + 1, "usuario": "teste@governantes"})


def test_ciclo_de_estados_completo(ciclo, cur):
    from datetime import date
    passos = [("em_analise", "curador", "teste@governantes", {}),
              ("aprovada", "aprovador", "teste@governantes", {}),
              ("planejada", "curador", "teste@governantes", {"prazo": date(2026, 12, 31)}),
              ("em_execucao", "consultante", ciclo["dono"], {})]
    for para, perfil, usuario, extra in passos:
        r = R.transicionar(cur, _interv(cur, ciclo["int"]), para, perfil, usuario, historico_id=tid(), **extra)
        assert r.confirmada
    it = _interv(cur, ciclo["int"])
    with pytest.raises(R.ErroIntegridade):
        R.executar_gravacao(cur, "sem evidência", R.SQL_TRANSICIONAR,
                            dict(intervencao_id=it["intervencao_id"], status_de="em_execucao", status_para="em_validacao",
                                 perfil="consultante", usuario=ciclo["dono"], versao_lida=it["versao"], prazo=None,
                                 justificativa=None, comentario=None),
                            "transicao", {"intervencao_id": it["intervencao_id"], "status_para": "em_validacao",
                                          "versao_nova": it["versao"] + 1, "usuario": ciclo["dono"]})
    conteudo = "https://exemplo.interno/ticket/TESTE"
    ev = dict(evidencia_id=tid(), chave_natural=R.chave_evidencia("intervencao", it["intervencao_id"], conteudo),
              entidade_tipo="intervencao", entidade_id=it["intervencao_id"], tipo="link", descricao="teste",
              conteudo=conteudo, origem="manual", usuario=ciclo["dono"], perfil="consultante")
    R.executar_gravacao(cur, "evidência", R.SQL_INSERIR_EVIDENCIA, ev, "evidencia", {"chave_natural": ev["chave_natural"]},
                        aceita_ja_existente=True)
    assert R.transicionar(cur, _interv(cur, ciclo["int"]), "em_validacao", "consultante", ciclo["dono"],
                          historico_id=tid(), tem_evidencia=True).confirmada
    assert R.transicionar(cur, _interv(cur, ciclo["int"]), "concluida", "aprovador", "teste@governantes",
                          historico_id=tid()).confirmada


def test_beneficio_calculado_no_banco(ciclo, cur):
    med = {}
    for tipo, valor, data in (("linha_base", 16, "2026-09-01"), ("acompanhamento", 9, "2026-11-01")):
        med[tipo] = tid()
        inserir(cur, """INSERT INTO vd_medicoes (medicao_id, chave_natural, indicador_id, objetivo_id, tipo, data_referencia, valor, metodo,
                        status, origem, status_validacao, validado_por, validado_em, criado_por, criado_em, versao)
                        VALUES (:m, :k, :i, :o, :t, :d, :v, 'teste', 'ativo', 'manual', 'validado', 'teste@governantes',
                        current_timestamp(), 'teste@governantes', current_timestamp(), 1)""",
                dict(m=med[tipo], k=R.chave(ciclo["ind"], tipo, data), i=ciclo["ind"], o=ciclo["obj"], t=tipo, d=data, v=valor),
                "vd_medicoes", "medicao_id", med[tipo])
        hist(cur, "medicao", med[tipo])
    base = dict(premissas="teste", valor_estimado=None, metodo_calculo="F1", usuario="teste@governantes", indicador_id=ciclo["ind"],
                intervencao_id=ciclo["int"], medicao_antes_id=med["linha_base"], medicao_depois_id=med["acompanhamento"],
                conversao_id=None)
    for ajuste in ({"medicao_antes_id": med["acompanhamento"], "medicao_depois_id": med["linha_base"]},
                   {"conversao_id": "NAO-EXISTE"}):
        p = {**base, **ajuste, "beneficio_id": tid()}
        with pytest.raises(R.ErroIntegridade):
            R.executar_gravacao(cur, "benefício inválido", R.SQL_INSERIR_BENEFICIO_MEDIDO, p, "beneficio_inserido",
                                {"beneficio_id": p["beneficio_id"]})
    p = {**base, "beneficio_id": tid()}
    R.executar_gravacao(cur, "benefício", R.SQL_INSERIR_BENEFICIO_MEDIDO, p, "beneficio_inserido", {"beneficio_id": p["beneficio_id"]})
    cur.execute("SELECT melhoria, melhoria_pct, valor_financeiro FROM vd_beneficios WHERE beneficio_id = :b", {"b": p["beneficio_id"]})
    melhoria, pct, fin = cur.fetchone()
    assert (float(melhoria), float(pct), fin) == (7.0, 43.75, None)
    with pytest.raises(Exception, match="(?i)check|constraint"):
        cur.execute("UPDATE vd_beneficios SET melhoria = 8 WHERE beneficio_id = :b", {"b": p["beneficio_id"]})


# ════════════════════════════════════════════════════════════════════
# Auditoria imutável e detecção posterior
# ════════════════════════════════════════════════════════════════════
def test_historico_nao_pode_ser_alterado(ciclo, cur):
    with pytest.raises(Exception, match="(?i)append|DELTA_CANNOT"):
        cur.execute("UPDATE vd_historico SET comentario = 'x' WHERE entidade_id = :a", {"a": ciclo["ach"]})


def test_evidencia_nao_pode_ser_excluida(ciclo, cur):
    with pytest.raises(Exception, match="(?i)append|DELTA_CANNOT"):
        cur.execute("DELETE FROM vd_evidencias WHERE entidade_id = :a", {"a": ciclo["ach"]})


def test_ciclo_valido_sem_violacoes(ciclo, cur):
    ids = [v for k, v in ciclo.items() if k != "dono"]
    cur.execute("SELECT codigo, regra, registro FROM vd_v_integridade")
    proprias = [r for r in cur.fetchall() if any(i in str(r[2]) for i in ids)]
    registro["violacoes_ciclo_valido"] = proprias
    assert proprias == []


def test_visao_detecta_desvios_gravados_fora_da_aplicacao(ciclo, cur):
    orfao = tid()
    cur.execute("""INSERT INTO vd_processos (processo_id, chave_natural, objetivo_id, nome, area_negocio, resp_processo, criticidade,
                   status, origem, status_validacao, criado_por, criado_em, versao)
                   VALUES (:p, :p, 'NAO-EXISTE', 'x', 'x', 'nao-cadastrado@x', 'baixa', 'ativo', 'manual', 'pendente', 't',
                   current_timestamp(), 1)""", {"p": orfao})
    cur.execute("SELECT DISTINCT codigo FROM vd_v_integridade WHERE registro = :p", {"p": orfao})
    assert {r[0] for r in cur.fetchall()} >= {"C01", "C11", "I03"}
    cur.execute("UPDATE vd_intervencoes SET prioridade = 'baixa' WHERE intervencao_id = :i", {"i": ciclo["int"]})
    assert contar(cur, "SELECT COUNT(*) FROM vd_v_integridade WHERE registro = :i AND codigo = 'C09'", {"i": ciclo["int"]}) >= 1
