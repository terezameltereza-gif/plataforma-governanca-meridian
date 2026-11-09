"""Testes offline das telas do Valor dos Dados (etapa 1: consulta)."""
import re
from pathlib import Path

import pandas as pd
import pytest

import vd_telas as T

FONTE = (Path(__file__).resolve().parents[1] / "vd_telas.py").read_text(encoding="utf-8")


def test_texto_do_banco_e_escapado():
    assert T.e('<script>alert("x")</script>') == "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;"
    assert T.e(None) == "" and T.e(float("nan")) == ""


@pytest.mark.parametrize("v,esperado", [(16.0, "16 h"), (9.5, "9,5 h"), (43.75, "43,75 h"), (1234.5, "1.234,5 h"),
                                        (None, "—")])
def test_formato_numerico_brasileiro(v, esperado):
    assert T._fmt_num(v, "h") == esperado


@pytest.mark.parametrize("v", ["x' OR '1'='1", "a\\b"])
def test_identificador_com_aspas_e_recusado(v):
    with pytest.raises(ValueError):
        T._lit(v)


def test_modulo_desligado_nao_consulta_o_banco():
    chamadas = []
    assert T.estado_instalacao(lambda sql: chamadas.append(sql), False) == (False, "desabilitado")
    assert chamadas == []


@pytest.mark.parametrize("resposta,disp", [((pd.DataFrame({"versao": ["v3"]}), None), True),
                                           ((pd.DataFrame(), None), False),
                                           ((pd.DataFrame(), "TABLE_OR_VIEW_NOT_FOUND"), False)])
def test_disponibilidade_depende_da_estrutura_instalada(resposta, disp):
    assert T.estado_instalacao(lambda sql: resposta, True)[0] is disp


def test_telas_so_leem_o_banco():
    consultas = re.findall(r'f?"(?:SELECT|INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP)[^"]*', FONTE)
    assert consultas and all(c.lstrip('f"').startswith("SELECT") for c in consultas)
    assert not re.search(r"\b(INSERT|UPDATE|DELETE|MERGE)\s+(INTO|FROM)?\s*\{?SCHEMA", FONTE)


def test_html_dinamico_usa_escape():
    """Toda célula vinda de linha do banco (r[...], o[...], a[...], i[...], b[...], x[...], v[...]) aparece dentro de e(),
    pessoa(), _data(), _fmt_num(), int() ou serve só de chave de dicionário."""
    suspeitos = re.findall(r"\{(?:r|o|a|i|b|x|v|p|c)\[\"\w+\"\]\}", FONTE)
    # Rótulos de widgets do Streamlit (expander e selectbox) não interpretam HTML.
    rotulos_de_widget = {'{o["nome"]}', '{r["codigo"]}', '{r["titulo"]}'}
    assert set(suspeitos) <= rotulos_de_widget, suspeitos
