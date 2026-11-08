-- ════════════════════════════════════════════════════════════════════
-- GOVERNANTES · Valor dos Dados · v3
-- 00 — Parâmetros de ambiente e pré-verificação (SOMENTE LEITURA)
--
-- Rode este arquivo antes de 01. Ele não cria nem altera nada.
-- Cada verificação usa raise_error(): se uma suposição falhar, a execução
-- para naquele ponto, com a mensagem do problema.
--
-- Requisitos do ambiente (confirmar): Unity Catalog; SQL Warehouse ou
-- cluster com suporte a variáveis de sessão (DECLARE VARIABLE) e à
-- cláusula IDENTIFIER() — Databricks SQL / DBR 14.1 ou superior.
-- ════════════════════════════════════════════════════════════════════

-- ── Parâmetros de ambiente ────────────────────────────────────────────
-- Produção do piloto:  vd_catalogo = 'workspace', vd_schema = 'meridian_governanca'
-- Testes:              vd_schema   = 'meridian_governanca_teste' (ver tests/README)
DECLARE OR REPLACE VARIABLE vd_catalogo STRING DEFAULT 'workspace';
DECLARE OR REPLACE VARIABLE vd_schema   STRING DEFAULT 'meridian_governanca';

USE CATALOG IDENTIFIER(vd_catalogo);
USE SCHEMA  IDENTIFIER(vd_schema);

-- Confirmação visual do destino
SELECT current_catalog() AS catalogo, current_schema() AS schema, current_user() AS executado_por;


-- ── 1. Tabelas existentes das quais o piloto depende ─────────────────
SELECT CASE WHEN COUNT(*) = 8 THEN 'OK: 8 tabelas encontradas'
            ELSE raise_error(concat('ABORTAR: tabelas ausentes no schema: ',
                 array_join(array_except(
                   array('tabelas_metadata','business_glossary','glossary_asset_link','business_rules',
                         'produtos_dados','produto_ativos','gd_quality_dimensions','linhagem_ativos'),
                   collect_list(table_name)), ', '))) END AS verificacao_tabelas
FROM information_schema.tables
WHERE table_catalog = current_catalog() AND table_schema = current_schema()
  AND table_name IN ('tabelas_metadata','business_glossary','glossary_asset_link','business_rules',
                     'produtos_dados','produto_ativos','gd_quality_dimensions','linhagem_ativos');


-- ── 2. Colunas OBRIGATÓRIAS (o piloto não funciona sem elas) ─────────
--    Origem da suposição: comandos de gravação e leitura em app.py.
WITH esperadas AS (
  SELECT * FROM VALUES
    ('tabelas_metadata','schema_name'),   ('tabelas_metadata','table_name'),     -- UPDATE ... WHERE (app.py)
    ('tabelas_metadata','data_owner'),    ('tabelas_metadata','data_steward'),   -- UPDATE SET (app.py)
    ('tabelas_metadata','descricao'),     ('tabelas_metadata','dominio'),        -- UPDATE SET (app.py)
    ('business_glossary','glossary_id'),  ('business_glossary','status'),       -- UPDATE ... WHERE (app.py)
    ('business_rules','glossary_id'),                                            -- JOIN (app.py)
    ('produtos_dados','produto_id'),                                             -- leitura (app.py)
    ('produto_ativos','produto_id'),      ('produto_ativos','table_name'),      -- leitura (app.py)
    ('gd_quality_dimensions','schema_name'), ('gd_quality_dimensions','table_name'), ('gd_quality_dimensions','score_final'),
    ('linhagem_ativos','origem_schema'),  ('linhagem_ativos','origem_tabela'),
    ('linhagem_ativos','destino_schema'), ('linhagem_ativos','destino_tabela')
    AS t(tabela, coluna)
),
faltando AS (
  SELECT e.tabela, e.coluna FROM esperadas e
  LEFT ANTI JOIN information_schema.columns c
    ON c.table_catalog = current_catalog() AND c.table_schema = current_schema()
   AND c.table_name = e.tabela AND c.column_name = e.coluna
)
SELECT CASE WHEN COUNT(*) = 0 THEN 'OK: colunas obrigatórias confirmadas'
            ELSE raise_error(concat('ABORTAR: colunas ausentes: ',
                 array_join(collect_list(concat(tabela,'.',coluna)), ', '))) END AS verificacao_colunas
FROM faltando;


-- ── 3. Colunas que o código lê de forma opcional (não interrompem) ───
--    Definem quais regras ficam habilitadas: 02 grava a decisão em
--    vd_regras_habilitacao e o diagnóstico registra 'nao_avaliada' para
--    toda regra desabilitada (com o motivo).
--    DG-04 depende de tabelas_metadata.classificacao (lida com .get()).
--    Vínculo por schema depende de glossary_asset_link.schema_name e
--    produto_ativos.schema_name (o código lê apenas table_name).
SELECT e.tabela, e.coluna, e.uso,
       CASE WHEN c.column_name IS NULL THEN 'AUSENTE' ELSE c.full_data_type END AS situacao
FROM (SELECT * FROM VALUES
        ('tabelas_metadata','classificacao','Regra DG-04 (sem classificação)'),
        ('glossary_asset_link','schema_name','Chave completa do ativo no vínculo com o glossário (DG-03)'),
        ('produto_ativos','schema_name','Chave completa do ativo no vínculo com o produto'),
        ('produtos_dados','descricao','Regra DG-08 (produto sem documentação)'),
        ('produtos_dados','finalidade','Regra DG-08 (alternativa a descricao)'),
        ('produtos_dados','owner','Regra DG-08 (produto sem responsável)'),
        ('produtos_dados','data_owner','Regra DG-08 (alternativa a owner)')
      AS t(tabela, coluna, uso)) e
LEFT JOIN information_schema.columns c
  ON c.table_catalog = current_catalog() AND c.table_schema = current_schema()
 AND c.table_name = e.tabela AND c.column_name = e.coluna
ORDER BY e.tabela, e.coluna;


-- ── 4. Estrutura completa das tabelas de referência ──────────────────
--    Para confirmar a chave de business_rules (vínculo regra_negocio).
--    Enquanto não confirmada, a aplicação recusa vínculos desse tipo.
SELECT table_name, ordinal_position, column_name, full_data_type, is_nullable
FROM information_schema.columns
WHERE table_catalog = current_catalog() AND table_schema = current_schema()
  AND table_name IN ('business_rules','glossary_asset_link','produto_ativos','produtos_dados')
ORDER BY table_name, ordinal_position;


-- ── 5. Unicidade das chaves usadas como referência ───────────────────
SELECT CASE WHEN COUNT(*) = 0 THEN 'OK: schema_name + table_name é única em tabelas_metadata'
            ELSE raise_error(concat('ABORTAR: ', COUNT(*), ' chaves de ativo duplicadas em tabelas_metadata')) END AS unicidade_ativo
FROM (SELECT schema_name, table_name FROM tabelas_metadata GROUP BY ALL HAVING COUNT(*) > 1);

SELECT CASE WHEN COUNT(*) = 0 THEN 'OK: glossary_id é única'
            ELSE raise_error(concat('ABORTAR: ', COUNT(*), ' glossary_id duplicados')) END AS unicidade_glossario
FROM (SELECT glossary_id FROM business_glossary GROUP BY ALL HAVING COUNT(*) > 1);

SELECT CASE WHEN COUNT(*) = 0 THEN 'OK: produto_id é única'
            ELSE raise_error(concat('ABORTAR: ', COUNT(*), ' produto_id duplicados')) END AS unicidade_produto
FROM (SELECT produto_id FROM produtos_dados GROUP BY ALL HAVING COUNT(*) > 1);

-- Avaliações de qualidade por ativo: se houver mais de uma, a regra DG-06
-- fica DESABILITADA em 02 (não há critério confirmado para escolher qual vale).
SELECT CASE WHEN COUNT(*) = 0 THEN 'OK: uma avaliação por ativo em gd_quality_dimensions — DG-06 habilitável'
            ELSE concat('ATENÇÃO: ', COUNT(*), ' ativos com mais de uma avaliação — DG-06 será desabilitada') END AS unicidade_qualidade
FROM (SELECT schema_name, table_name FROM gd_quality_dimensions GROUP BY ALL HAVING COUNT(*) > 1);

-- Ativos com o mesmo table_name em schemas diferentes: se houver, vínculos
-- lidos só por table_name (glossário/produto) ficam ambíguos e a aplicação
-- marca esses casos como 'nao_identificado' em vez de supor o schema.
SELECT table_name, COUNT(DISTINCT schema_name) AS schemas
FROM tabelas_metadata GROUP BY table_name HAVING COUNT(DISTINCT schema_name) > 1;


-- ── 6. Estado anterior do módulo ─────────────────────────────────────
--    Se existirem tabelas vd_* criadas por versão anterior (v1/v2), o
--    CREATE IF NOT EXISTS de 01 não as atualizaria. Este passo aborta.
SELECT CASE WHEN COUNT(*) = 0 THEN 'OK: nenhuma tabela vd_* pré-existente'
            WHEN SUM(CASE WHEN table_name = 'vd_controle_versao' THEN 1 ELSE 0 END) = 1
                 THEN 'OK: módulo já instalado — 01 confirmará a versão registrada'
            ELSE raise_error('ABORTAR: existem tabelas vd_* sem controle de versão (instalação anterior incompleta)') END AS estado_modulo
FROM information_schema.tables
WHERE table_catalog = current_catalog() AND table_schema = current_schema() AND table_name LIKE 'vd\_%';


-- ── 7. Privilégios atuais (insumo para a seção de permissões de 01) ──
SHOW GRANTS ON SCHEMA IDENTIFIER(vd_schema);
