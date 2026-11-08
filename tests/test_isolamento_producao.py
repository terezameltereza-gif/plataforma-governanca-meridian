"""Evidências offline de que a homologação não consegue alterar produção.

Não conecta ao Databricks. Examina o texto de TODOS os comandos que a
homologação executa (scripts 00–03, setup do schema de teste, SQL da aplicação e
testes de integração) e exercita as travas com um cursor simulado.
O que só o ambiente real comprova (permissões efetivas) está no roteiro.
"""
import ast
import re
from pathlib import Path

import pytest

import vd_regras as R
from tests import test_vd_banco as B

RAIZ = Path(__file__).resolve().parents[1]
SQL = RAIZ / "sql" / "valor_dos_dados"
PROD, TESTE, CAT = "meridian_governanca", "meridian_governanca_teste", "workspace"
BASE = {"tabelas_metadata", "business_glossary", "glossary_asset_link", "business_rules", "produtos_dados",
        "produto_ativos", "gd_quality_dimensions", "linhagem_ativos"}

# Comando de gravação → alvo. Alvo sem qualificação = schema corrente (o de teste).
ALVO = re.compile(r"""^\s*(?:
      CREATE\s+(?:OR\s+REPLACE\s+)?(?:TEMPORARY\s+)?(?:TABLE|VIEW)\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<a>[\w.`]+)
    | INSERT\s+(?:INTO|OVERWRITE)\s+(?:TABLE\s+)?(?P<b>[\w.`]+)
    | MERGE\s+INTO\s+(?P<c>[\w.`]+)
    | UPDATE\s+(?P<d>[\w.`]+)
    | DELETE\s+FROM\s+(?P<e>[\w.`]+)
    | ALTER\s+(?:TABLE|VIEW)\s+(?P<f>[\w.`]+)
    | DROP\s+(?:TABLE|VIEW)\s+(?:IF\s+EXISTS\s+)?(?P<g>[\w.`]+)
    | TRUNCATE\s+TABLE\s+(?P<h>[\w.`]+)
    | CREATE\s+SCHEMA\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<i>[\w.`]+)
    | (?P<j>GRANT|REVOKE|OPTIMIZE|VACUUM|COMMENT\s+ON|SET\s+TAG|ALTER\s+SCHEMA|ALTER\s+CATALOG|DROP\s+SCHEMA)
)""", re.I | re.X)
LEITURA = re.compile(r"^\s*(SELECT|WITH|SHOW|DESCRIBE|DECLARE\s+OR\s+REPLACE\s+VARIABLE|USE)\b", re.I)


def alvo(stmt):
    m = ALVO.match(stmt)
    if not m:
        return None
    nome = next(v for v in m.groupdict().values() if v)
    return nome.strip("`")


def gravacoes(stmts):
    return [(alvo(s), s.split("\n")[0][:70]) for s in stmts if alvo(s)]


# ════════════════════════════════════════════════════════════════════
# 1. Scripts 00–03, exatamente como a homologação os executa
# ════════════════════════════════════════════════════════════════════
def test_00_e_somente_leitura():
    stmts = B.preparar_sql("00_parametros_e_preverificacao.sql", teste=TESTE, producao=PROD)
    assert stmts and all(LEITURA.match(s) for s in stmts), [s[:60] for s in stmts if not LEITURA.match(s)]
    assert gravacoes(stmts) == []


def test_00_original_aponta_para_producao_e_continua_somente_leitura():
    """Passo 4 do roteiro: 00 SEM substituição (aponta para produção). Nenhum comando grava."""
    txt = (SQL / "00_parametros_e_preverificacao.sql").read_text(encoding="utf-8")
    sem = "\n".join(l for l in txt.splitlines() if not l.strip().startswith("--"))
    stmts = [s.strip() for s in re.split(r";\s*\n", sem) if s.strip()]
    assert all(LEITURA.match(s) for s in stmts)
    assert f"DEFAULT '{PROD}'" in sem


@pytest.mark.parametrize("arquivo", ["00_parametros_e_preverificacao.sql", "01_estruturas.sql",
                                     "02_dados_de_referencia.sql", "03_validacoes_integridade.sql"])
def test_scripts_so_gravam_no_schema_corrente(arquivo):
    stmts = B.preparar_sql(arquivo, teste=TESTE, producao=PROD)
    texto = "\n".join(stmts)
    assert re.search(rf"\b{PROD}\b(?!_)", texto) is None
    assert f"DECLARE OR REPLACE VARIABLE vd_schema   STRING DEFAULT '{TESTE}'" in texto
    usos = [s for s in stmts if s.upper().startswith("USE ")]
    assert usos == ["USE CATALOG IDENTIFIER(vd_catalogo)", "USE SCHEMA  IDENTIFIER(vd_schema)"]
    for nome, inicio in gravacoes(stmts):
        assert nome and "." not in nome, f"{arquivo}: gravação qualificada fora do schema corrente: {inicio}"
        assert nome.lower() not in BASE, f"{arquivo}: gravação em tabela existente do catálogo: {inicio}"
        assert nome.lower().startswith("vd_"), f"{arquivo}: alvo fora do módulo: {inicio}"


def test_04_permissoes_nao_e_executado_na_homologacao():
    fonte = (RAIZ / "tests" / "test_vd_banco.py").read_text(encoding="utf-8")
    assert "04_permissoes" not in fonte


def test_preparar_sql_recusa_referencia_remanescente(tmp_path, monkeypatch):
    (tmp_path / "x.sql").write_text(f"SELECT * FROM {CAT}.{PROD}.tabelas_metadata;\n", encoding="utf-8")
    monkeypatch.setattr(B, "SQL", tmp_path)
    with pytest.raises(B.TravaAcionada, match="remanescente"):
        B.preparar_sql("x.sql", teste=TESTE, producao=PROD)


# ════════════════════════════════════════════════════════════════════
# 2. Setup do schema de teste (executado pelo administrador)
# ════════════════════════════════════════════════════════════════════
def test_setup_so_cria_objetos_no_schema_de_teste():
    txt = (RAIZ / "tests" / "setup_schema_teste.sql").read_text(encoding="utf-8")
    stmts = [s.strip() for s in re.split(r";\s*\n", "\n".join(l for l in txt.splitlines()
             if not l.strip().startswith("--"))) if s.strip()]
    assert stmts[:3] == [f"USE CATALOG {CAT}",
                         f"CREATE SCHEMA IF NOT EXISTS {TESTE} COMMENT 'Testes do Valor dos Dados — descartável'",
                         f"USE SCHEMA {TESTE}"]
    for s in stmts[3:]:
        s = s.rstrip(";").strip()
        m = re.fullmatch(rf"CREATE OR REPLACE VIEW (\w+)\s+AS SELECT \* FROM {CAT}\.{PROD}\.(\w+)", s)
        assert m and m.group(1) == m.group(2) and m.group(1) in BASE, s
    # produção aparece somente como ORIGEM de leitura das visões
    assert len(re.findall(rf"\b{PROD}\b(?!_)", "\n".join(stmts))) == len(BASE)


# ════════════════════════════════════════════════════════════════════
# 3. SQL da aplicação usado nos testes
# ════════════════════════════════════════════════════════════════════
def test_sql_da_aplicacao_grava_somente_tabelas_do_modulo():
    consts = {k: v for k, v in vars(R).items() if k.startswith("SQL_") and isinstance(v, str)}
    consts.update({f"VERIFICACOES.{k}": v for k, v in R.VERIFICACOES.items()})
    for nome, sql in consts.items():
        a = alvo(sql)
        if a is None:
            assert LEITURA.match(sql), nome
            continue
        assert "." not in a and a.startswith("vd_") and a not in BASE, f"{nome} grava em {a}"
        assert PROD not in sql, nome


# ════════════════════════════════════════════════════════════════════
# 4. Testes de integração
# ════════════════════════════════════════════════════════════════════
def _literais_sql(fonte):
    arvore = ast.parse(fonte)
    em_fstring = {id(v) for n in ast.walk(arvore) if isinstance(n, ast.JoinedStr) for v in n.values}
    for n in ast.walk(arvore):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in em_fstring:
            yield n.value, False
        elif isinstance(n, ast.JoinedStr):
            yield "".join(v.value if isinstance(v, ast.Constant) else "{" + ast.unparse(v.value) + "}"
                          for v in n.values), True


def test_testes_de_integracao_so_gravam_no_schema_corrente():
    fonte = (RAIZ / "tests" / "test_vd_banco.py").read_text(encoding="utf-8")
    encontrados = 0
    for texto, interpolado in _literais_sql(fonte):
        a = alvo(texto)
        if a is None:
            continue
        encontrados += 1
        assert "." not in a and "{" not in a, f"gravação com alvo qualificado ou variável: {texto[:70]}"
        assert a.startswith("vd_") and a not in BASE, f"gravação fora do módulo: {texto[:70]}"
        assert not interpolado or "PRODUCAO" not in texto
    assert encontrados >= 8          # objetivos, processos, indicadores, vínculos, execução, achados, medições, UPDATEs negativos


def test_variavel_de_producao_so_e_usada_pelas_travas():
    arvore = ast.parse((RAIZ / "tests" / "test_vd_banco.py").read_text(encoding="utf-8"))
    permitidos = {"verificar_travas", "preparar_sql"}
    for func in [n for n in ast.walk(arvore) if isinstance(n, ast.FunctionDef)]:
        usa = any(isinstance(x, ast.Name) and x.id == "PRODUCAO" for x in ast.walk(func))
        assert not usa or func.name in permitidos, f"{func.name} usa PRODUCAO"


def test_travas_consultam_apenas_leitura():
    for sql in (B.SQL_PRIVILEGIOS_PRODUCAO, B.SQL_PROPRIEDADE_PRODUCAO):
        assert LEITURA.match(sql) and alvo(sql) is None
        assert "is_account_group_member" in sql          # cobre privilégios herdados de grupos


# ════════════════════════════════════════════════════════════════════
# 5. Comportamento das travas (cursor simulado)
# ════════════════════════════════════════════════════════════════════
class CursorTravas:
    def __init__(self, schema=TESTE, privilegios=(), propriedades=(), schema_apos_use=None):
        self.schema, self.privilegios, self.propriedades = schema, list(privilegios), list(propriedades)
        self.schema_apos_use, self.comandos, self._r = schema_apos_use, [], []

    def execute(self, sql, params=None):
        self.comandos.append(sql)
        s = sql.strip()
        if "catalog_privileges" in s:
            self._r = self.privilegios
        elif "catalog_owner" in s:
            self._r = self.propriedades
        elif s.startswith("SELECT current_catalog()"):
            self._r = [(CAT, self.schema, "homologacao@governantes")]
        elif s.startswith("SELECT current_schema()"):
            self._r = [(self.schema_apos_use or self.schema,)]
        else:
            self._r = []

    def fetchone(self):
        return self._r[0]

    def fetchall(self):
        return self._r


def test_travas_aprovam_credencial_somente_leitura():
    c = CursorTravas(privilegios=[("schema", PROD, "homologacao@governantes", "SELECT"),
                                  ("schema", PROD, "homologacao@governantes", "USE SCHEMA")])
    r = B.verificar_travas(c, CAT, TESTE, PROD)
    assert r["propriedade_producao"] == []
    assert all(LEITURA.match(x) for x in c.comandos)


@pytest.mark.parametrize("teste", [PROD, "meridian_governanca_hml", ""])
def test_trava1_nome_do_schema(teste):
    c = CursorTravas()
    with pytest.raises(B.TravaAcionada, match="trava 1"):
        B.verificar_travas(c, CAT, teste, PROD)
    assert c.comandos == []                                  # nada foi enviado ao banco


def test_trava2_schema_corrente_divergente():
    with pytest.raises(B.TravaAcionada, match="trava 2"):
        B.verificar_travas(CursorTravas(schema=PROD), CAT, TESTE, PROD)


@pytest.mark.parametrize("linha", [
    ("schema", PROD, "homologacao@governantes", "MODIFY"),
    ("tabela", "tabelas_metadata", "grupo_engenharia", "MODIFY"),          # herdado de grupo
    ("catalogo", CAT, "account users", "CREATE TABLE"),                    # herdado do catálogo
    ("catalogo", CAT, "admins", "ALL PRIVILEGES"),
    ("schema", PROD, "homologacao@governantes", "MANAGE"),
])
def test_trava3_privilegio_de_gravacao(linha):
    with pytest.raises(B.TravaAcionada, match="trava 3"):
        B.verificar_travas(CursorTravas(privilegios=[linha]), CAT, TESTE, PROD)


@pytest.mark.parametrize("linha", [("catalogo", CAT, "homologacao@governantes"),
                                   ("schema", PROD, "admins"), ("tabela", "produtos_dados", "homologacao@governantes")])
def test_trava3_propriedade(linha):
    with pytest.raises(B.TravaAcionada, match="trava 3"):
        B.verificar_travas(CursorTravas(propriedades=[linha]), CAT, TESTE, PROD)


def test_rodar_arquivo_interrompe_se_use_mudar_para_producao(monkeypatch):
    c = CursorTravas(schema_apos_use=PROD)
    with pytest.raises(B.TravaAcionada, match="schema corrente"):
        B.rodar_arquivo(c, "01_estruturas.sql", teste=TESTE)
    assert not any(alvo(x) for x in c.comandos), "nenhuma gravação pode ter sido enviada"


def test_fixture_encerra_sessao_quando_trava_aciona():
    fonte = (RAIZ / "tests" / "test_vd_banco.py").read_text(encoding="utf-8")
    corpo = fonte[fonte.index("def cur():"):fonte.index("yield c")]
    assert "verificar_travas(c)" in corpo and "pytest.exit" in corpo
    assert corpo.index("verificar_travas(c)") < corpo.index("pytest.exit")
