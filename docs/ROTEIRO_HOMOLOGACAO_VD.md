# Roteiro de homologação — Valor dos Dados v3.2 (revisão 2)

Objetivo: comprovar no Databricks real o que os testes offline não comprovam, sem que nenhuma etapa consiga alterar produção (`workspace.meridian_governanca`).

Revisão 2: explicita a sequência de schemas, separa as sessões de execução, amplia a trava de privilégios para grupos e herança e anexa as evidências offline de isolamento.

## 1. Princípio de segurança

Produção fica protegida por duas barreiras independentes. Para alterar produção, as duas teriam de falhar ao mesmo tempo.

| Barreira | Natureza | Como é comprovada |
|---|---|---|
| **A. Permissão** | A credencial de homologação não tem privilégio de gravação em produção, nem direto, nem herdado de grupo ou do catálogo, e não é dona de nenhum objeto de produção. O Unity Catalog recusa qualquer gravação, independentemente do código. | Consulta de privilégios efetivos (passo 3.4), repetida automaticamente pela trava 3 |
| **B. Código** | Nenhum comando executado na homologação tem produção como destino de gravação. Os comandos de gravação usam nomes sem qualificação, resolvidos no schema corrente, e o schema corrente é conferido antes de qualquer gravação e depois de cada `USE`. | 28 testes offline em `tests/test_isolamento_producao.py` (seção 7), já executados |

A barreira A é a principal. A barreira B garante que, mesmo com uma permissão configurada errado, o código não envia gravação para produção.

**Por que não há "tentativa de gravação" como contraprova.** Testar a permissão tentando gravar em produção e esperando a recusa seria, em caso de erro de configuração, uma gravação real. A permissão é comprovada por leitura dos privilégios efetivos, e não por tentativa.

## 2. Sequência de schemas

São quatro sessões separadas. Nenhuma herda contexto da anterior.

| Etapa | Quem executa | Credencial | Schema de destino | Comandos | Por que não altera produção |
|---|---|---|---|---|---|
| 3. Preparação | Administrador | Administrador | `meridian_governanca_teste` | `CREATE SCHEMA` do teste, 8 `CREATE VIEW` no teste, GRANT ao principal de teste | O script só cria objetos no schema de teste. Produção aparece apenas como origem de leitura das visões (teste `test_setup_so_cria_objetos_no_schema_de_teste`). |
| 4. Pré-verificação | Executor | Principal de teste | `meridian_governanca` (**somente leitura**) | Apenas `DECLARE VARIABLE`, `USE`, `SELECT`, `SHOW` | **A:** sem privilégio de gravação. **B:** o arquivo 00 não contém nenhum comando de gravação (testes `test_00_*`). |
| 5. Testes de integração | Executor | Principal de teste | `meridian_governanca_teste` | Instalação de 00–03 e ciclo do piloto | **A:** sem privilégio de gravação. **B:** travas 1 a 3 antes de qualquer comando, scripts redirecionados e conferidos, schema verificado após cada `USE`. |
| 8. Encerramento | Administrador | Administrador | `meridian_governanca_teste` | `DROP SCHEMA ... CASCADE` do teste | O comando nomeia exclusivamente o schema de teste. |

### Por que o arquivo 00 roda duas vezes, em schemas diferentes

- **Etapa 4, em produção:** confirma a estrutura real das 8 tabelas, as chaves, a unicidade, a ausência de tabelas `vd_*` e os grants do schema. É a verificação exigida antes de qualquer instalação. Roda manualmente no editor SQL, em uma sessão própria.
- **Etapa 5, no teste:** faz parte da instalação de teste e confirma que as 8 visões do schema de teste expõem as mesmas colunas.

A troca de contexto não acontece dentro de uma mesma sessão. Na etapa 5, o pytest abre uma conexão nova. A primeira ação é a trava 2, que fixa e lê de volta o schema de teste. Só depois disso algum script é lido. Cada arquivo 00–03 passa por `preparar_sql`, que:

1. substitui o parâmetro `'meridian_governanca'` por `'meridian_governanca_teste'`;
2. recusa o arquivo se restar qualquer menção ao schema de produção;
3. é seguido, a cada `USE`, da leitura de `current_schema()`, e a execução é interrompida se o resultado não for o schema de teste.

## 3. Preparação (administrador, uma única vez)

```sql
-- 3.1 Principal dedicado à homologação (service principal ou usuário exclusivo).
--     Não usar a conta pessoal de administração: ela é dona do catálogo e será recusada pela trava 3.

-- 3.2 Schema de teste com visões somente leitura sobre as 8 tabelas existentes
--     (arquivo tests/setup_schema_teste.sql)

-- 3.3 Permissões
GRANT USE CATALOG ON CATALOG workspace TO `<principal_teste>`;
GRANT USE SCHEMA, SELECT ON SCHEMA workspace.meridian_governanca TO `<principal_teste>`;    -- só leitura
GRANT ALL PRIVILEGES ON SCHEMA workspace.meridian_governanca_teste TO `<principal_teste>`;
```

### 3.4 Conferência de isolamento (executada **com o principal de teste**)

São as mesmas consultas da trava 3. O resultado deve ser guardado como evidência antes da etapa 4.

```sql
-- Privilégios efetivos em produção: diretos, de grupos e herdados do catálogo
SELECT 'catalogo' AS nivel, catalog_name AS objeto, grantee, privilege_type
FROM workspace.information_schema.catalog_privileges
WHERE catalog_name = 'workspace' AND (grantee = current_user() OR is_account_group_member(grantee))
UNION ALL
SELECT 'schema', schema_name, grantee, privilege_type
FROM workspace.information_schema.schema_privileges
WHERE schema_name = 'meridian_governanca' AND (grantee = current_user() OR is_account_group_member(grantee))
UNION ALL
SELECT 'tabela', table_name, grantee, privilege_type
FROM workspace.information_schema.table_privileges
WHERE table_schema = 'meridian_governanca' AND (grantee = current_user() OR is_account_group_member(grantee));
-- Esperado: somente USE CATALOG, USE SCHEMA e SELECT.
-- Qualquer MODIFY, ALL PRIVILEGES, MANAGE ou CREATE *: PARAR.

-- Propriedade de objetos de produção (o dono tem todos os direitos sem GRANT)
SELECT 'catalogo', catalog_name, catalog_owner FROM workspace.information_schema.catalogs
WHERE catalog_name = 'workspace' AND (catalog_owner = current_user() OR is_account_group_member(catalog_owner))
UNION ALL
SELECT 'schema', schema_name, schema_owner FROM workspace.information_schema.schemata
WHERE schema_name = 'meridian_governanca' AND (schema_owner = current_user() OR is_account_group_member(schema_owner))
UNION ALL
SELECT 'tabela', table_name, table_owner FROM workspace.information_schema.tables
WHERE table_schema = 'meridian_governanca' AND (table_owner = current_user() OR is_account_group_member(table_owner));
-- Esperado: nenhuma linha. Qualquer linha: PARAR.
```

`SHOW GRANTS` não é suficiente para essa conferência, porque não mostra privilégios recebidos por meio de grupos.

## 4. Pré-verificação do catálogo (principal de teste, somente leitura)

No editor SQL, em uma sessão nova, executar `sql/valor_dos_dados/00_parametros_e_preverificacao.sql` sem alteração. O arquivo aponta para `meridian_governanca` e contém apenas leitura. Guardar a saída completa.

Critério para continuar: nenhuma asserção `raise_error` disparada. Itens marcados como ATENÇÃO devem ser registrados e avaliados antes da etapa 5.

## 5. Testes de integração (principal de teste, schema de teste)

```bash
pip install -r requirements.txt pytest
export DATABRICKS_HOST=...  DATABRICKS_HTTP_PATH=...  DATABRICKS_TOKEN=<token do principal de teste>
export VD_SCHEMA_TESTE=meridian_governanca_teste  VD_SCHEMA_PRODUCAO=meridian_governanca

# 5.1 Evidência offline, no mesmo código que será executado
PYTHONPATH=. pytest tests/test_isolamento_producao.py tests/test_vd_regras.py -q --junitxml=offline.xml

# 5.2 Integração
PYTHONPATH=. pytest tests/test_vd_banco.py -v -p no:randomly --junitxml=homologacao.xml
```

Se qualquer trava for acionada, `pytest.exit` encerra a sessão inteira com código 3, antes de qualquer gravação.

Ordem dos testes de integração:

1. Travas 1 a 3. Nesta fase só são enviados `USE`, `SELECT` e consultas ao `information_schema`.
2. Instalação de 00–03 no schema de teste, duas vezes, como prova de idempotência.
3. Contagem das tabelas de referência e bloqueio da entrada pendente do modelo P1.
4. Propriedade `delta.appendOnly` nas tabelas de auditoria.
5. Ciclo pelo código da aplicação: objetivo, processo, indicador, vínculo com ativo real cujo Owner consta em `vd_v_responsaveis`, execução e achado.
6. Gravação de todas as ocorrências (disparou, nao_disparou e nao_avaliada), com habilitação lida do banco e sem violação I04.
7. Comportamento real do conector: `rowcount` após INSERT comparado com a leitura posterior.
8. Intervenção: recusa por objetivo divergente, inclusão confirmada, recusa de duplicidade e pontuação igual à do Python.
9. Recusa de transições inválidas pelo próprio banco e ciclo completo de estados, com exigência de evidência.
10. Medições e benefício: recusas, cálculo pelo banco e CHECK contra adulteração.
11. Imutabilidade de histórico e evidências.
12. Ciclo válido sem violações e detecção de desvios gravados fora da aplicação (C01, C11, I03, C09).

## 6. Evidências a anexar

| Evidência | Origem | Comprova |
|---|---|---|
| Saída da conferência 3.4 | Editor SQL, principal de teste | Barreira A |
| Saída completa do arquivo 00 | Editor SQL, principal de teste | Estrutura real do catálogo |
| `offline.xml` | pytest 5.1 | Barreira B e regras de negócio, no código efetivamente executado |
| `homologacao.xml` | pytest 5.2 | Resultado de cada teste de integração |
| `evidencias_homologacao.json` | Gerado pelos testes | Usuário, privilégios efetivos e propriedade em produção (registrados pela trava 3), habilitação das regras, ocorrências por resultado, versão do conector, `rowcount` observado e violações do ciclo válido |
| Versão do Databricks Runtime / SQL warehouse | Configuração do warehouse | Compatibilidade do SQL |
| Histórico de produção depois da homologação | `DESCRIBE HISTORY` das 8 tabelas, pelo administrador | Ausência de qualquer versão nova durante a janela da homologação |

O último item é a prova final: as 8 tabelas de produção não podem ter nenhuma versão Delta com data dentro da janela da homologação.

Os registros criados nos testes são insumos técnicos (prefixo `TESTE-`). Não são evidência sobre dados de negócio e não substituem o piloto com o processo real.

## 7. Evidências offline de isolamento (já executadas)

Arquivo `tests/test_isolamento_producao.py`, com 28 testes aprovados. Eles examinam o texto de todos os comandos que a homologação executa e exercitam as travas com um cursor simulado.

| Afirmação | Teste |
|---|---|
| O arquivo 00 só contém leitura, tanto na versão que aponta para produção quanto na redirecionada | `test_00_e_somente_leitura`, `test_00_original_aponta_para_producao_e_continua_somente_leitura` |
| 00–03 redirecionados não mencionam produção, só usam `USE IDENTIFIER(vd_schema)` e só gravam em tabelas `vd_*` sem qualificação | `test_scripts_so_gravam_no_schema_corrente` (4 arquivos) |
| Um arquivo com menção remanescente a produção é recusado | `test_preparar_sql_recusa_referencia_remanescente` |
| O arquivo 04 (permissões) não é executado pela homologação | `test_04_permissoes_nao_e_executado_na_homologacao` |
| O setup só cria objetos no schema de teste | `test_setup_so_cria_objetos_no_schema_de_teste` |
| O SQL da aplicação só grava em tabelas `vd_*` | `test_sql_da_aplicacao_grava_somente_tabelas_do_modulo` |
| Os testes de integração só gravam em `vd_*` sem qualificação; a variável de produção só é usada pelas travas | `test_testes_de_integracao_so_gravam_no_schema_corrente`, `test_variavel_de_producao_so_e_usada_pelas_travas` |
| As travas só fazem leitura e consideram grupos | `test_travas_consultam_apenas_leitura` |
| A trava 1 recusa nome inválido sem enviar nada ao banco | `test_trava1_nome_do_schema` (3 casos) |
| A trava 2 recusa schema corrente divergente | `test_trava2_schema_corrente_divergente` |
| A trava 3 recusa MODIFY direto, MODIFY de grupo, CREATE TABLE e ALL PRIVILEGES herdados do catálogo, MANAGE e propriedade de catálogo, schema ou tabela | `test_trava3_privilegio_de_gravacao` (5 casos), `test_trava3_propriedade` (3 casos) |
| Um `USE` que leve a produção interrompe a instalação antes de qualquer gravação | `test_rodar_arquivo_interrompe_se_use_mudar_para_producao` |
| A sessão é encerrada quando uma trava é acionada | `test_fixture_encerra_sessao_quando_trava_aciona` |

Prova de sensibilidade, executada e depois revertida: ao inserir em uma cópia de `01_estruturas.sql` um `INSERT INTO workspace.meridian_governanca.tabelas_metadata ...`, os testes falharam. O mesmo aconteceu com um `INSERT INTO meridian_governanca_teste.tabelas_metadata ...` (gravação em tabela existente do catálogo). O arquivo original foi restaurado sem diferenças.

Limite destas evidências: elas comprovam o que o código envia, não o que o Unity Catalog permite. A permissão só é comprovada no ambiente (3.4, trava 3 e histórico de produção).

## 8. Critérios de parada

Interromper e não repetir até análise se ocorrer qualquer um destes casos:

- conferência 3.4 com privilégio de gravação ou propriedade;
- trava acionada (código de saída 3);
- falha em `offline.xml`;
- `raise_error` no arquivo 00 ou 03;
- recusa por recurso SQL não suportado na versão do warehouse;
- `rowcount` diferente de −1 e de 1 após uma inclusão;
- qualquer violação em `vd_v_integridade` no ciclo válido;
- qualquer versão nova nas tabelas de produção durante a janela da homologação.

## 9. Encerramento

```sql
DROP SCHEMA workspace.meridian_governanca_teste CASCADE;
SHOW TABLES IN workspace.meridian_governanca LIKE 'vd_*';     -- esperado: nenhuma
-- DESCRIBE HISTORY de cada uma das 8 tabelas de produção (evidência da seção 6)
REVOKE SELECT, USE SCHEMA ON SCHEMA workspace.meridian_governanca FROM `<principal_teste>`;
```

## 10. Dependências do ambiente que podem impedir a homologação

- **Principal dedicado.** É preciso um principal separado da conta de administração. Se o plano do workspace (por exemplo, a Free Edition) não permitir criar service principal ou um segundo usuário sem privilégios, a barreira A não pode ser estabelecida, e a homologação **não deve ser executada**.
- **Administradores do metastore ou do workspace.** Podem conceder privilégios a si mesmos. O principal de teste não pode ter esse papel. Isso não aparece no `information_schema` e deve ser confirmado pelo administrador no console de contas.
- **Funções do warehouse.** `is_account_group_member` e o `information_schema` com as tabelas `*_privileges` precisam estar disponíveis na versão do warehouse. Sem isso, a trava 3 falha e a sessão é encerrada sem gravar.

## 11. Fora do escopo desta homologação

- Instalação em produção e execução do arquivo 04 com principais reais: exige aprovação específica após a homologação.
- Pontuação de achados de produtos (`posicao_ativo = nao_aplicavel`): decisão de negócio pendente. Permanece bloqueada no código, no SQL e na verificação C09.
- Integração do módulo à interface da plataforma: depende da aprovação da prévia das telas.
