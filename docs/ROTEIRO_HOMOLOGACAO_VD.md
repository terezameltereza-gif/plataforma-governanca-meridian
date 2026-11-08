# Roteiro de homologação — Valor dos Dados v3.2

Objetivo: comprovar no Databricks real o que os testes offline não comprovam, sem nenhuma possibilidade de gravação em produção (`workspace.meridian_governanca`).

## 1. Princípio de segurança

A proteção não depende de disciplina de quem executa: depende de **permissão**. A homologação usa uma credencial que, pelo Unity Catalog, não consegue gravar em produção. As travas do código (`tests/test_vd_banco.py`) são uma segunda barreira e interrompem a execução se a credencial tiver privilégio indevido.

| Barreira | Onde | O que impede |
|---|---|---|
| Credencial dedicada sem MODIFY em produção | Unity Catalog | Qualquer INSERT/UPDATE/DELETE em `meridian_governanca` |
| Trava 1 — nome do schema | fixture `cur` | Rodar com schema que não termine em `_teste` ou igual ao de produção |
| Trava 2 — schema corrente lido de volta | fixture `cur` e `rodar_arquivo` | Script que troque o schema durante a execução |
| Trava 3 — privilégios e propriedade | fixture `cur` | Credencial com MODIFY, ALL PRIVILEGES, CREATE TABLE ou MANAGE no schema de produção ou no catálogo, ou dona do schema |
| Substituição verificada | `rodar_arquivo` | Script 00–03 executado com `'meridian_governanca'` remanescente |

## 2. Papéis

| Papel | Quem | Ações |
|---|---|---|
| Administrador do workspace | Responsável pela plataforma | Cria o principal de teste, o schema de teste e os grants (passo 3). Não executa os testes. |
| Executor da homologação | Principal de teste (service principal ou usuário dedicado) | Executa os testes (passo 5). |
| Aprovador | Governantes | Avalia as evidências (passo 6) e decide pela liberação. |

## 3. Preparação (administrador, uma única vez)

```sql
-- 3.1 Schema de teste com visões somente leitura sobre as 8 tabelas existentes
--     (arquivo tests/setup_schema_teste.sql)

-- 3.2 Permissões do principal de teste
GRANT USE CATALOG ON CATALOG workspace TO `<principal_teste>`;
GRANT USE SCHEMA, SELECT ON SCHEMA workspace.meridian_governanca TO `<principal_teste>`;   -- só leitura
GRANT ALL PRIVILEGES ON SCHEMA workspace.meridian_governanca_teste TO `<principal_teste>`;

-- 3.3 Conferência obrigatória antes de prosseguir
SHOW GRANTS `<principal_teste>` ON SCHEMA workspace.meridian_governanca;
-- Esperado: apenas USE SCHEMA e SELECT. Qualquer outro privilégio: parar.
```

Observação: as visões do schema de teste leem produção com a permissão de quem consulta; por isso o principal de teste precisa de SELECT em produção, e apenas isso.

## 4. Pré-verificação do catálogo (somente leitura)

Executar `sql/valor_dos_dados/00_parametros_e_preverificacao.sql` com `vd_schema = 'meridian_governanca'`, usando o principal de teste. O arquivo não grava nada e, com essa credencial, não conseguiria gravar. Guardar a saída completa: ela confirma colunas, chaves e unicidade que o restante do pacote presume.

Critério para continuar: nenhuma asserção `raise_error` disparada. Itens marcados como ATENÇÃO devem ser registrados e avaliados antes do passo 5.

## 5. Execução dos testes de integração

```bash
pip install -r requirements.txt pytest
export DATABRICKS_HOST=...  DATABRICKS_HTTP_PATH=...  DATABRICKS_TOKEN=<token do principal de teste>
export VD_SCHEMA_TESTE=meridian_governanca_teste  VD_SCHEMA_PRODUCAO=meridian_governanca
PYTHONPATH=. pytest tests/test_vd_banco.py -v -p no:randomly --junitxml=homologacao.xml
```

Os testes são sequenciais e executam, nesta ordem:

1. Travas de segurança (antes de qualquer gravação).
2. Instalação de 00–03 no schema de teste, duas vezes (prova de idempotência).
3. Contagem das tabelas de referência e bloqueio da entrada pendente do modelo P1.
4. Propriedade `delta.appendOnly` nas tabelas de auditoria.
5. Ciclo pelo código da aplicação: objetivo, processo, indicador, vínculo com ativo real do catálogo cujo Owner consta em `vd_v_responsaveis`, execução e achado.
6. Gravação de todas as ocorrências (disparou, nao_disparou, nao_avaliada) por `gravar_ocorrencias_e_concluir`, com habilitação lida do banco, e ausência de violação I04.
7. Registro do comportamento real do conector (`rowcount` após INSERT) contra a leitura posterior.
8. Intervenção: recusa por objetivo divergente, inclusão confirmada, recusa de duplicidade, pontuação igual à do Python.
9. Recusa de transições inválidas pelo próprio banco e ciclo completo de estados, inclusive exigência de evidência.
10. Benefício: recusas (ordem das medições, conversão inexistente), cálculo pelo banco e CHECK contra adulteração.
11. Imutabilidade de histórico e evidências.
12. Ciclo válido sem violações; detecção de desvios gravados fora da aplicação (C01, C11, I03, C09).

## 6. Evidências a anexar

| Evidência | Origem |
|---|---|
| Saída do passo 3.3 (SHOW GRANTS) | Console SQL |
| Saída completa do arquivo 00 | Console SQL |
| `homologacao.xml` | pytest (resultado por teste) |
| `evidencias_homologacao.json` | Gerado pelos testes: ambiente, usuário, privilégios em produção, habilitação das regras, ocorrências por resultado, versão do conector e `rowcount` observado, violações do ciclo válido |
| Versão do Databricks Runtime / SQL warehouse | Configuração do warehouse |

Os registros criados nos testes são insumos técnicos (prefixo `TESTE-`). Não são evidência sobre dados de negócio e não substituem o piloto com o processo real.

## 7. Critérios de parada

Interromper e não repetir até análise se ocorrer qualquer um:

- trava de segurança acionada;
- `raise_error` no arquivo 00 ou 03;
- comando recusado por recurso SQL não suportado na versão do warehouse;
- `rowcount` diferente de −1 e de 1 após uma inclusão;
- qualquer violação em `vd_v_integridade` no teste do ciclo válido.

## 8. Encerramento

```sql
DROP SCHEMA workspace.meridian_governanca_teste CASCADE;
REVOKE ALL PRIVILEGES ON SCHEMA workspace.meridian_governanca_teste FROM `<principal_teste>`;  -- se o schema for recriado
```

Conferir que `workspace.meridian_governanca` não contém nenhuma tabela `vd_*` (`SHOW TABLES IN workspace.meridian_governanca LIKE 'vd_*'`), exceto se a instalação em produção já tiver sido aprovada.

## 9. Fora do escopo desta homologação

- Instalação em produção e execução do arquivo 04 com principais reais: exige aprovação específica após a homologação.
- Pontuação de achados de produtos (`posicao_ativo = nao_aplicavel`): decisão de negócio pendente; permanece bloqueada no código, no SQL e na verificação C09.
- Integração do módulo à interface da plataforma: depende da aprovação da prévia das telas.
