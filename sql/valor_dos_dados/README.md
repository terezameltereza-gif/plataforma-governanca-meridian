# Valor dos Dados — estruturas v3

Substitui `sql/vd_piloto_valor_dos_dados.sql` (v1/v2), que nunca foi executado.

## Ordem de execução

| Passo | Arquivo | Natureza |
|---|---|---|
| 0 | `00_parametros_e_preverificacao.sql` | Somente leitura. Para (`ABORTAR`) se tabela, coluna ou unicidade esperada não existir |
| 1 | `01_estruturas.sql` | Cria apenas tabelas `vd_*` e restrições. Idempotente |
| 2 | `02_dados_de_referencia.sql` | Regras R1, modelo P1, faixas, transições. Idempotente; aborta se uma versão publicada divergir |
| 3 | `03_validacoes_integridade.sql` | Cria a visão `vd_v_integridade` e aborta se houver violação |
| 4 | `04_permissoes.sql` | Dono, GRANTs (substituir os marcadores `<...>`) |

Produção só depois de os testes de integração passarem no schema de teste.

## Testes

1. `tests/setup_schema_teste.sql` — cria `meridian_governanca_teste` com visões somente leitura das 8 tabelas existentes.
2. `PYTHONPATH=. pytest tests/test_vd_regras.py` — regras, fórmulas e consistência código × SQL (sem banco).
3. `PYTHONPATH=. pytest tests/test_vd_banco.py` — integração no schema de teste (exige `DATABRICKS_HOST`, `DATABRICKS_HTTP_PATH`, `DATABRICKS_TOKEN`).
4. `DROP SCHEMA workspace.meridian_governanca_teste CASCADE` ao final.

## Camadas de integridade

1. Restrições impostas pelo Delta (`CHECK`, `NOT NULL`, `delta.appendOnly`).
2. Validação prévia na aplicação (`vd_regras.validar_*`).
3. Gravação condicionada: o comando SQL só grava se as relações forem coerentes (`vd_regras.SQL_*`); 0 linhas = recusa.
4. Detecção posterior: `vd_v_integridade`.

PK e FK do Unity Catalog são apenas informativas e não são tratadas como garantia.
