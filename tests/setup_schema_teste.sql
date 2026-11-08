-- ════════════════════════════════════════════════════════════════════
-- Ambiente de TESTE do Valor dos Dados (isolado da produção)
--
-- Cria o schema meridian_governanca_teste com VISÕES somente leitura
-- sobre as 8 tabelas existentes. Nenhum dado de produção é copiado,
-- alterado ou excluído. As tabelas vd_* de teste são criadas neste schema
-- rodando 00 → 03 com vd_schema = 'meridian_governanca_teste'.
-- Ao final dos testes: DROP SCHEMA meridian_governanca_teste CASCADE.
-- ════════════════════════════════════════════════════════════════════
USE CATALOG workspace;
CREATE SCHEMA IF NOT EXISTS meridian_governanca_teste COMMENT 'Testes do Valor dos Dados — descartável';
USE SCHEMA meridian_governanca_teste;

CREATE OR REPLACE VIEW tabelas_metadata      AS SELECT * FROM workspace.meridian_governanca.tabelas_metadata;
CREATE OR REPLACE VIEW business_glossary     AS SELECT * FROM workspace.meridian_governanca.business_glossary;
CREATE OR REPLACE VIEW glossary_asset_link   AS SELECT * FROM workspace.meridian_governanca.glossary_asset_link;
CREATE OR REPLACE VIEW business_rules        AS SELECT * FROM workspace.meridian_governanca.business_rules;
CREATE OR REPLACE VIEW produtos_dados        AS SELECT * FROM workspace.meridian_governanca.produtos_dados;
CREATE OR REPLACE VIEW produto_ativos        AS SELECT * FROM workspace.meridian_governanca.produto_ativos;
CREATE OR REPLACE VIEW gd_quality_dimensions AS SELECT * FROM workspace.meridian_governanca.gd_quality_dimensions;
CREATE OR REPLACE VIEW linhagem_ativos       AS SELECT * FROM workspace.meridian_governanca.linhagem_ativos;
-- Observação: 00 consulta information_schema.tables; visões aparecem lá
-- como table_type = 'VIEW', então a pré-verificação funciona no teste.
