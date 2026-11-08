-- ════════════════════════════════════════════════════════════════════
-- GOVERNANTES · Módulo Valor dos Dados · Piloto (cenário Banco Meridian)
-- Script de estruturas — versão 2 (para aprovação)
--
-- Mudanças da v2
--   • Bloco padrão de rastreabilidade em todas as tabelas: origem,
--     responsável pelo registro, criação/atualização, versão, situação de
--     validação e chave natural.
--   • Idempotência: tabelas com IF NOT EXISTS; restrições recriadas com
--     DROP CONSTRAINT IF EXISTS + ADD; nenhuma carga de dados neste script.
--     A aplicação grava sempre com MERGE pela chave natural (seção 4).
--   • Histórico e evidências imutáveis (delta.appendOnly) e Change Data
--     Feed ligado em todas as tabelas como segunda trilha de alterações.
--   • Integridade referencial: chaves informativas + exclusão física
--     proibida (registros são cancelados, nunca apagados) + consultas de
--     órfãos e duplicidades (seção 5).
--   • Permissões no Unity Catalog (seção 6).
--
-- Princípios mantidos
--   • Nenhuma tabela existente é alterada. Só são criadas tabelas vd_*.
--   • Objetos existentes são referenciados por suas chaves; nenhum
--     metadado é copiado.
--   • IDs são UUID (STRING) gerados pela aplicação; usuários são e-mails.
--
-- Execução: rode as seções em ordem. Rodar o script inteiro de novo não
-- duplica estruturas nem dados.
-- ════════════════════════════════════════════════════════════════════

USE CATALOG workspace;
USE SCHEMA meridian_governanca;

-- ────────────────────────────────────────────────────────────────────
-- 0. VERIFICAÇÃO PRÉVIA (somente leitura)
-- ────────────────────────────────────────────────────────────────────
DESCRIBE TABLE tabelas_metadata;
DESCRIBE TABLE glossary_asset_link;   -- confirmar se possui schema_name
DESCRIBE TABLE business_glossary;
DESCRIBE TABLE business_rules;        -- confirmar a chave da regra
DESCRIBE TABLE produtos_dados;
DESCRIBE TABLE produto_ativos;        -- confirmar se possui schema_name
DESCRIBE TABLE gd_quality_dimensions;
DESCRIBE TABLE linhagem_ativos;

-- A chave de ativo (schema + tabela) precisa ser única: deve retornar zero linhas
SELECT schema_name, table_name, COUNT(*) AS ocorrencias
FROM tabelas_metadata GROUP BY schema_name, table_name HAVING COUNT(*) > 1;

-- Privilégios atuais no schema (para planejar a seção 6)
SHOW GRANTS ON SCHEMA meridian_governanca;


-- ════════════════════════════════════════════════════════════════════
-- 1. TABELAS
--
-- Bloco padrão de rastreabilidade (presente em todas as entidades):
--   origem            manual | metadado | calculado | importacao | sugestao_ia
--   chave_natural     identidade de negócio; base do MERGE que impede duplicação
--   status_validacao  pendente | validado | rejeitado
--   validado_por / validado_em / justificativa_validacao
--   criado_por / criado_em / atualizado_por / atualizado_em
--   versao            incrementada a cada atualização (controle de concorrência)
-- Evidências: vd_evidencias. Histórico: vd_historico (+ Change Data Feed).
-- ════════════════════════════════════════════════════════════════════

-- 1.1 Objetivos e desafios ----------------------------------------------------
CREATE TABLE IF NOT EXISTS vd_objetivos (
  objetivo_id               STRING        NOT NULL COMMENT 'UUID',
  chave_natural             STRING        NOT NULL COMMENT 'tipo|nome|area_negocio (normalizados)',
  tipo                      STRING        NOT NULL COMMENT 'objetivo | desafio',
  nome                      STRING        NOT NULL,
  descricao                 STRING,
  area_negocio              STRING        NOT NULL,
  objetivo_estrategico      STRING,
  resp_negocio              STRING        NOT NULL COMMENT 'E-mail',
  resp_acompanhamento       STRING        NOT NULL COMMENT 'E-mail',
  prioridade                STRING        NOT NULL COMMENT 'alta | media | baixa',
  data_inicio               DATE,
  data_prevista             DATE,
  status                    STRING        NOT NULL COMMENT 'rascunho | ativo | atingido | nao_atingido | cancelado',
  limite_qualidade_pct      DECIMAL(5,2)  COMMENT 'Sem valor = regra DG-06 não se aplica',
  criterio_sucesso          STRING        NOT NULL,
  origem                    STRING        NOT NULL,
  status_validacao          STRING        NOT NULL COMMENT 'Validação pelo responsável de negócio',
  validado_por              STRING,
  validado_em               TIMESTAMP,
  justificativa_validacao   STRING,
  criado_por                STRING        NOT NULL,
  criado_em                 TIMESTAMP     NOT NULL,
  atualizado_por            STRING,
  atualizado_em             TIMESTAMP,
  versao                    INT           NOT NULL,
  CONSTRAINT vd_objetivos_pk PRIMARY KEY (objetivo_id)
) COMMENT 'Valor dos Dados — objetivos e desafios de negócio'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- 1.2 Processos ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vd_processos (
  processo_id               STRING        NOT NULL,
  chave_natural             STRING        NOT NULL COMMENT 'objetivo_id|nome',
  objetivo_id               STRING        NOT NULL,
  nome                      STRING        NOT NULL,
  descricao                 STRING,
  area_negocio              STRING        NOT NULL,
  resp_processo             STRING        NOT NULL COMMENT 'E-mail',
  periodicidade             STRING,
  criticidade               STRING        NOT NULL COMMENT 'alta | media | baixa',
  status                    STRING        NOT NULL COMMENT 'ativo | cancelado',
  origem                    STRING        NOT NULL,
  status_validacao          STRING        NOT NULL,
  validado_por              STRING,
  validado_em               TIMESTAMP,
  justificativa_validacao   STRING,
  criado_por                STRING        NOT NULL,
  criado_em                 TIMESTAMP     NOT NULL,
  atualizado_por            STRING,
  atualizado_em             TIMESTAMP,
  versao                    INT           NOT NULL,
  CONSTRAINT vd_processos_pk PRIMARY KEY (processo_id),
  CONSTRAINT vd_processos_obj_fk FOREIGN KEY (objetivo_id) REFERENCES vd_objetivos (objetivo_id)
) COMMENT 'Valor dos Dados — processos de negócio'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- 1.3 Indicadores de resultado ---------------------------------------------------
CREATE TABLE IF NOT EXISTS vd_indicadores (
  indicador_id              STRING        NOT NULL,
  chave_natural             STRING        NOT NULL COMMENT 'objetivo_id|nome',
  objetivo_id               STRING        NOT NULL,
  processo_id               STRING,
  papel                     STRING        NOT NULL COMMENT 'principal | complementar',
  nome                      STRING        NOT NULL,
  descricao                 STRING,
  unidade                   STRING        NOT NULL,
  sentido_melhora           STRING        NOT NULL COMMENT 'reduzir | aumentar',
  formula                   STRING        NOT NULL,
  fonte                     STRING        NOT NULL,
  periodicidade             STRING        NOT NULL,
  responsavel               STRING        NOT NULL COMMENT 'E-mail',
  meta                      DECIMAL(18,4),
  status                    STRING        NOT NULL COMMENT 'ativo | cancelado',
  origem                    STRING        NOT NULL,
  status_validacao          STRING        NOT NULL,
  validado_por              STRING,
  validado_em               TIMESTAMP,
  justificativa_validacao   STRING,
  criado_por                STRING        NOT NULL,
  criado_em                 TIMESTAMP     NOT NULL,
  atualizado_por            STRING,
  atualizado_em             TIMESTAMP,
  versao                    INT           NOT NULL,
  CONSTRAINT vd_indicadores_pk PRIMARY KEY (indicador_id),
  CONSTRAINT vd_indicadores_obj_fk FOREIGN KEY (objetivo_id) REFERENCES vd_objetivos (objetivo_id),
  CONSTRAINT vd_indicadores_proc_fk FOREIGN KEY (processo_id) REFERENCES vd_processos (processo_id)
) COMMENT 'Valor dos Dados — indicadores (piloto: horas de retrabalho = principal · divergências = complementar)'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- 1.4 Vínculos negócio → objetos existentes --------------------------------------
--   ativo           → ref_schema + ref_nome   (tabelas_metadata)
--   produto         → ref_id                  (produtos_dados.produto_id)
--   termo_glossario → ref_id                  (business_glossary.glossary_id)
--   regra_negocio   → ref_id                  (business_rules; chave confirmada na seção 0)
--   dominio         → ref_nome                (atributo de tabelas_metadata)
--   indicador       → ref_id                  (vd_indicadores.indicador_id)
--   responsavel     → ref_nome                (e-mail)
CREATE TABLE IF NOT EXISTS vd_vinculos (
  vinculo_id                STRING        NOT NULL,
  chave_natural             STRING        NOT NULL COMMENT 'origem_tipo|origem_id|ref_tipo|ref_id|ref_schema|ref_nome',
  origem_tipo               STRING        NOT NULL COMMENT 'objetivo | processo',
  origem_id                 STRING        NOT NULL,
  ref_tipo                  STRING        NOT NULL,
  ref_id                    STRING,
  ref_schema                STRING,
  ref_nome                  STRING,
  papel_no_processo         STRING        COMMENT 'fonte | intermediario | saida (obrigatório para ativo · informado, nunca inferido)',
  evidencia_base            STRING        COMMENT 'Registro que comprova a relação, quando origem = metadado',
  status                    STRING        NOT NULL COMMENT 'ativo | cancelado',
  origem                    STRING        NOT NULL,
  status_validacao          STRING        NOT NULL,
  validado_por              STRING,
  validado_em               TIMESTAMP,
  justificativa_validacao   STRING,
  criado_por                STRING        NOT NULL,
  criado_em                 TIMESTAMP     NOT NULL,
  atualizado_por            STRING,
  atualizado_em             TIMESTAMP,
  versao                    INT           NOT NULL,
  CONSTRAINT vd_vinculos_pk PRIMARY KEY (vinculo_id)
) COMMENT 'Valor dos Dados — relações negócio-dados por referência às chaves existentes'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- 1.5 Achados do diagnóstico ---------------------------------------------------
--   natureza: nao_cadastrado (campo vazio) | nao_identificado (sem fonte para verificar)
--             | nao_conforme (viola critério, com evidência) | nao_aplicavel (só por pessoa)
--   Um achado por (objetivo, vínculo, regra): reexecutar o diagnóstico atualiza
--   o mesmo registro via MERGE; não cria outro.
CREATE TABLE IF NOT EXISTS vd_achados (
  achado_id                 STRING        NOT NULL,
  chave_natural             STRING        NOT NULL COMMENT 'objetivo_id|vinculo_id|regra_codigo',
  objetivo_id               STRING        NOT NULL,
  processo_id               STRING,
  vinculo_id                STRING        NOT NULL,
  regra_codigo              STRING        NOT NULL COMMENT 'DG-01 … DG-09',
  natureza                  STRING        NOT NULL,
  evidencia_fato            STRING        NOT NULL COMMENT 'Tabela, campo e valor consultados',
  valor_observado           STRING,
  criterio                  STRING        COMMENT 'Obrigatório quando natureza = nao_conforme',
  situacao                  STRING        NOT NULL COMMENT 'aberto | resolvido (regra deixou de disparar) | cancelado',
  primeira_execucao_id      STRING        NOT NULL,
  ultima_execucao_id        STRING        NOT NULL,
  primeira_deteccao_em      TIMESTAMP     NOT NULL,
  ultima_deteccao_em        TIMESTAMP     NOT NULL,
  origem                    STRING        NOT NULL COMMENT 'calculado (regra) | manual',
  status_validacao          STRING        NOT NULL,
  validado_por              STRING,
  validado_em               TIMESTAMP,
  justificativa_validacao   STRING,
  criado_por                STRING        NOT NULL,
  criado_em                 TIMESTAMP     NOT NULL,
  atualizado_por            STRING,
  atualizado_em             TIMESTAMP,
  versao                    INT           NOT NULL,
  CONSTRAINT vd_achados_pk PRIMARY KEY (achado_id),
  CONSTRAINT vd_achados_obj_fk FOREIGN KEY (objetivo_id) REFERENCES vd_objetivos (objetivo_id),
  CONSTRAINT vd_achados_vinc_fk FOREIGN KEY (vinculo_id) REFERENCES vd_vinculos (vinculo_id)
) COMMENT 'Valor dos Dados — achados do diagnóstico por regras documentadas'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- 1.6 Intervenções -------------------------------------------------------------
--   Situação de validação = o próprio ciclo (aprovada / em_validacao / concluida),
--   com aprovador registrado em aprovado_por e concluido_por.
CREATE TABLE IF NOT EXISTS vd_intervencoes (
  intervencao_id            STRING        NOT NULL,
  chave_natural             STRING        NOT NULL COMMENT 'achado_id|sequencia (reabertura gera nova sequência)',
  codigo                    STRING        NOT NULL COMMENT 'INT-0001',
  achado_id                 STRING        NOT NULL,
  intervencao_anterior_id   STRING        COMMENT 'Preenchido em reaberturas',
  objetivo_id               STRING        NOT NULL,
  titulo                    STRING        NOT NULL,
  recomendacao              STRING        NOT NULL,
  tipo_afirmacao            STRING        NOT NULL COMMENT 'fato | hipotese',
  causa_provavel            STRING,
  responsavel               STRING        NOT NULL COMMENT 'E-mail',
  area                      STRING        NOT NULL,
  pts_prioridade_objetivo   INT           NOT NULL,
  pts_posicao_ativo         INT           NOT NULL,
  pts_tipo_achado           INT           NOT NULL,
  pts_abrangencia           INT           NOT NULL,
  abrangencia_ativos        INT           COMMENT 'Nulo = não determinada (vale 0 ponto)',
  pts_esforco               INT           NOT NULL,
  esforco                   STRING        NOT NULL COMMENT 'baixo | medio | alto | nao_informado',
  pontuacao_total           INT           NOT NULL,
  prioridade                STRING        NOT NULL COMMENT 'critica | alta | media | baixa',
  criterio_conclusao        STRING        NOT NULL,
  status                    STRING        NOT NULL,
  aberta_em                 TIMESTAMP     NOT NULL,
  prazo                     DATE,
  aprovado_por              STRING,
  aprovado_em               TIMESTAMP,
  concluido_por             STRING,
  concluida_em              TIMESTAMP,
  justificativa_cancelamento STRING,
  origem                    STRING        NOT NULL,
  criado_por                STRING        NOT NULL,
  criado_em                 TIMESTAMP     NOT NULL,
  atualizado_por            STRING,
  atualizado_em             TIMESTAMP,
  versao                    INT           NOT NULL,
  CONSTRAINT vd_intervencoes_pk PRIMARY KEY (intervencao_id),
  CONSTRAINT vd_intervencoes_achado_fk FOREIGN KEY (achado_id) REFERENCES vd_achados (achado_id),
  CONSTRAINT vd_intervencoes_obj_fk FOREIGN KEY (objetivo_id) REFERENCES vd_objetivos (objetivo_id)
) COMMENT 'Valor dos Dados — intervenções rastreáveis, executadas pelo Meu Espaço'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- 1.7 Medições -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vd_medicoes (
  medicao_id                STRING        NOT NULL,
  chave_natural             STRING        NOT NULL COMMENT 'indicador_id|tipo|data_referencia',
  indicador_id              STRING        NOT NULL,
  tipo                      STRING        NOT NULL COMMENT 'linha_base | acompanhamento',
  data_referencia           DATE          NOT NULL,
  valor                     DECIMAL(18,4) NOT NULL,
  metodo                    STRING        NOT NULL,
  intervencao_id            STRING,
  status                    STRING        NOT NULL COMMENT 'ativo | cancelado (correção = nova versão do mesmo registro)',
  origem                    STRING        NOT NULL COMMENT 'manual | importacao',
  status_validacao          STRING        NOT NULL COMMENT 'Validação pelo responsável do indicador',
  validado_por              STRING,
  validado_em               TIMESTAMP,
  justificativa_validacao   STRING,
  criado_por                STRING        NOT NULL,
  criado_em                 TIMESTAMP     NOT NULL,
  atualizado_por            STRING,
  atualizado_em             TIMESTAMP,
  versao                    INT           NOT NULL,
  CONSTRAINT vd_medicoes_pk PRIMARY KEY (medicao_id),
  CONSTRAINT vd_medicoes_ind_fk FOREIGN KEY (indicador_id) REFERENCES vd_indicadores (indicador_id),
  CONSTRAINT vd_medicoes_int_fk FOREIGN KEY (intervencao_id) REFERENCES vd_intervencoes (intervencao_id)
) COMMENT 'Valor dos Dados — medições informadas pela organização'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- 1.8 Benefícios -----------------------------------------------------------------
--   Situação de validação = estagio (estimado → em_validacao → validado | recusado).
CREATE TABLE IF NOT EXISTS vd_beneficios (
  beneficio_id              STRING        NOT NULL,
  chave_natural             STRING        NOT NULL COMMENT 'indicador_id|intervencao_id',
  indicador_id              STRING        NOT NULL,
  intervencao_id            STRING        NOT NULL,
  medicao_antes_id          STRING,
  medicao_depois_id         STRING,
  estagio                   STRING        NOT NULL,
  premissas                 STRING        NOT NULL,
  valor_estimado            DECIMAL(18,4),
  diferenca_medida          DECIMAL(18,4),
  custo_unitario            DECIMAL(18,2),
  fonte_custo_unitario      STRING,
  valor_financeiro          DECIMAL(18,2),
  ressalva_causalidade      STRING        NOT NULL,
  validado_por              STRING        COMMENT 'Responsável de negócio',
  validado_em               TIMESTAMP,
  justificativa_validacao   STRING,
  origem                    STRING        NOT NULL COMMENT 'calculado | manual',
  criado_por                STRING        NOT NULL,
  criado_em                 TIMESTAMP     NOT NULL,
  atualizado_por            STRING,
  atualizado_em             TIMESTAMP,
  versao                    INT           NOT NULL,
  CONSTRAINT vd_beneficios_pk PRIMARY KEY (beneficio_id),
  CONSTRAINT vd_beneficios_ind_fk FOREIGN KEY (indicador_id) REFERENCES vd_indicadores (indicador_id),
  CONSTRAINT vd_beneficios_int_fk FOREIGN KEY (intervencao_id) REFERENCES vd_intervencoes (intervencao_id),
  CONSTRAINT vd_beneficios_antes_fk FOREIGN KEY (medicao_antes_id) REFERENCES vd_medicoes (medicao_id),
  CONSTRAINT vd_beneficios_depois_fk FOREIGN KEY (medicao_depois_id) REFERENCES vd_medicoes (medicao_id)
) COMMENT 'Valor dos Dados — benefícios'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- 1.9 Evidências — imutáveis ---------------------------------------------------
CREATE TABLE IF NOT EXISTS vd_evidencias (
  evidencia_id              STRING        NOT NULL,
  chave_natural             STRING        NOT NULL COMMENT 'entidade_tipo|entidade_id|sha2(conteudo)',
  entidade_tipo             STRING        NOT NULL,
  entidade_id               STRING        NOT NULL,
  tipo                      STRING        NOT NULL COMMENT 'link | consulta_sql | texto',
  descricao                 STRING        NOT NULL,
  conteudo                  STRING        NOT NULL,
  origem                    STRING        NOT NULL,
  registrado_por            STRING        NOT NULL,
  registrado_em             TIMESTAMP     NOT NULL,
  CONSTRAINT vd_evidencias_pk PRIMARY KEY (evidencia_id)
) COMMENT 'Valor dos Dados — evidências (somente inclusão)'
TBLPROPERTIES ('delta.appendOnly' = 'true', 'delta.enableChangeDataFeed' = 'true');

-- 1.10 Histórico — imutável ----------------------------------------------------
CREATE TABLE IF NOT EXISTS vd_historico (
  historico_id              STRING        NOT NULL,
  entidade_tipo             STRING        NOT NULL,
  entidade_id               STRING        NOT NULL,
  acao                      STRING        NOT NULL COMMENT 'criacao | edicao | transicao | validacao | evidencia | cancelamento',
  versao_entidade           INT           COMMENT 'Versão do registro após a ação',
  status_anterior           STRING,
  status_novo               STRING,
  campos_alterados          STRING        COMMENT 'JSON {campo: [antes, depois]}',
  comentario                STRING,
  evidencia_id              STRING,
  executado_por             STRING        NOT NULL,
  perfil                    STRING        NOT NULL,
  executado_em              TIMESTAMP     NOT NULL,
  CONSTRAINT vd_historico_pk PRIMARY KEY (historico_id)
) COMMENT 'Valor dos Dados — trilha de auditoria (somente inclusão)'
TBLPROPERTIES ('delta.appendOnly' = 'true', 'delta.enableChangeDataFeed' = 'true');


-- ════════════════════════════════════════════════════════════════════
-- 2. RESTRIÇÕES CHECK — recriáveis (DROP IF EXISTS + ADD)
-- ════════════════════════════════════════════════════════════════════

-- Bloco padrão (origem e validação) em todas as entidades com status_validacao
ALTER TABLE vd_objetivos   DROP CONSTRAINT IF EXISTS ck_obj_padrao;
ALTER TABLE vd_objetivos   ADD  CONSTRAINT ck_obj_padrao CHECK (
  origem IN ('manual','importacao') AND status_validacao IN ('pendente','validado','rejeitado')
  AND (status_validacao = 'pendente' OR (validado_por IS NOT NULL AND validado_em IS NOT NULL))
  AND (status_validacao <> 'rejeitado' OR justificativa_validacao IS NOT NULL) AND versao >= 1);
ALTER TABLE vd_processos   DROP CONSTRAINT IF EXISTS ck_proc_padrao;
ALTER TABLE vd_processos   ADD  CONSTRAINT ck_proc_padrao CHECK (
  origem IN ('manual','importacao') AND status_validacao IN ('pendente','validado','rejeitado')
  AND (status_validacao = 'pendente' OR (validado_por IS NOT NULL AND validado_em IS NOT NULL))
  AND (status_validacao <> 'rejeitado' OR justificativa_validacao IS NOT NULL) AND versao >= 1);
ALTER TABLE vd_indicadores DROP CONSTRAINT IF EXISTS ck_ind_padrao;
ALTER TABLE vd_indicadores ADD  CONSTRAINT ck_ind_padrao CHECK (
  origem IN ('manual','importacao') AND status_validacao IN ('pendente','validado','rejeitado')
  AND (status_validacao = 'pendente' OR (validado_por IS NOT NULL AND validado_em IS NOT NULL))
  AND (status_validacao <> 'rejeitado' OR justificativa_validacao IS NOT NULL) AND versao >= 1);
ALTER TABLE vd_vinculos    DROP CONSTRAINT IF EXISTS ck_vin_padrao;
ALTER TABLE vd_vinculos    ADD  CONSTRAINT ck_vin_padrao CHECK (
  origem IN ('manual','metadado','sugestao_ia') AND status_validacao IN ('pendente','validado','rejeitado')
  AND (status_validacao = 'pendente' OR (validado_por IS NOT NULL AND validado_em IS NOT NULL))
  AND (status_validacao <> 'rejeitado' OR justificativa_validacao IS NOT NULL) AND versao >= 1);
ALTER TABLE vd_achados     DROP CONSTRAINT IF EXISTS ck_ach_padrao;
ALTER TABLE vd_achados     ADD  CONSTRAINT ck_ach_padrao CHECK (
  origem IN ('calculado','manual') AND status_validacao IN ('pendente','validado','rejeitado')
  AND (status_validacao = 'pendente' OR (validado_por IS NOT NULL AND validado_em IS NOT NULL))
  AND (status_validacao <> 'rejeitado' OR justificativa_validacao IS NOT NULL) AND versao >= 1);
ALTER TABLE vd_medicoes    DROP CONSTRAINT IF EXISTS ck_med_padrao;
ALTER TABLE vd_medicoes    ADD  CONSTRAINT ck_med_padrao CHECK (
  origem IN ('manual','importacao') AND status_validacao IN ('pendente','validado','rejeitado')
  AND (status_validacao = 'pendente' OR (validado_por IS NOT NULL AND validado_em IS NOT NULL))
  AND (status_validacao <> 'rejeitado' OR justificativa_validacao IS NOT NULL) AND versao >= 1);

-- Objetivos, processos, indicadores
ALTER TABLE vd_objetivos   DROP CONSTRAINT IF EXISTS ck_obj_dominio;
ALTER TABLE vd_objetivos   ADD  CONSTRAINT ck_obj_dominio CHECK (
  tipo IN ('objetivo','desafio') AND prioridade IN ('alta','media','baixa')
  AND status IN ('rascunho','ativo','atingido','nao_atingido','cancelado')
  AND (limite_qualidade_pct IS NULL OR limite_qualidade_pct BETWEEN 0 AND 100)
  AND (data_prevista IS NULL OR data_inicio IS NULL OR data_prevista >= data_inicio));
ALTER TABLE vd_processos   DROP CONSTRAINT IF EXISTS ck_proc_dominio;
ALTER TABLE vd_processos   ADD  CONSTRAINT ck_proc_dominio CHECK (criticidade IN ('alta','media','baixa') AND status IN ('ativo','cancelado'));
ALTER TABLE vd_indicadores DROP CONSTRAINT IF EXISTS ck_ind_dominio;
ALTER TABLE vd_indicadores ADD  CONSTRAINT ck_ind_dominio CHECK (
  papel IN ('principal','complementar') AND sentido_melhora IN ('reduzir','aumentar') AND status IN ('ativo','cancelado'));

-- Vínculos: chave de referência coerente com o tipo
ALTER TABLE vd_vinculos    DROP CONSTRAINT IF EXISTS ck_vin_dominio;
ALTER TABLE vd_vinculos    ADD  CONSTRAINT ck_vin_dominio CHECK (
  origem_tipo IN ('objetivo','processo') AND status IN ('ativo','cancelado')
  AND ref_tipo IN ('ativo','produto','termo_glossario','regra_negocio','dominio','indicador','responsavel')
  AND (  (ref_tipo = 'ativo' AND ref_schema IS NOT NULL AND ref_nome IS NOT NULL AND ref_id IS NULL
          AND papel_no_processo IN ('fonte','intermediario','saida'))
      OR (ref_tipo IN ('produto','termo_glossario','regra_negocio','indicador') AND ref_id IS NOT NULL)
      OR (ref_tipo IN ('dominio','responsavel') AND ref_nome IS NOT NULL AND ref_id IS NULL))
  AND (origem <> 'metadado' OR evidencia_base IS NOT NULL));

-- Achados: separação rigorosa das naturezas
ALTER TABLE vd_achados     DROP CONSTRAINT IF EXISTS ck_ach_dominio;
ALTER TABLE vd_achados     ADD  CONSTRAINT ck_ach_dominio CHECK (
  natureza IN ('nao_cadastrado','nao_identificado','nao_conforme','nao_aplicavel')
  AND situacao IN ('aberto','resolvido','cancelado')
  AND (natureza <> 'nao_conforme' OR (criterio IS NOT NULL AND valor_observado IS NOT NULL))
  AND (natureza <> 'nao_aplicavel' OR (origem = 'manual' AND justificativa_validacao IS NOT NULL))
  AND ultima_deteccao_em >= primeira_deteccao_em);

-- Intervenções: estados e exigências por estado
ALTER TABLE vd_intervencoes DROP CONSTRAINT IF EXISTS ck_int_dominio;
ALTER TABLE vd_intervencoes ADD  CONSTRAINT ck_int_dominio CHECK (
  status IN ('identificada','em_analise','aprovada','planejada','em_execucao','em_validacao','concluida','cancelada')
  AND prioridade IN ('critica','alta','media','baixa') AND tipo_afirmacao IN ('fato','hipotese')
  AND esforco IN ('baixo','medio','alto','nao_informado') AND origem IN ('manual','calculado') AND versao >= 1
  AND pontuacao_total = pts_prioridade_objetivo + pts_posicao_ativo + pts_tipo_achado + pts_abrangencia + pts_esforco
  AND (abrangencia_ativos IS NOT NULL OR pts_abrangencia = 0)
  AND (esforco <> 'nao_informado' OR pts_esforco = 0));
ALTER TABLE vd_intervencoes DROP CONSTRAINT IF EXISTS ck_int_estado;
ALTER TABLE vd_intervencoes ADD  CONSTRAINT ck_int_estado CHECK (
      (status IN ('identificada','em_analise','cancelada') OR (aprovado_por IS NOT NULL AND aprovado_em IS NOT NULL))
  AND (status IN ('identificada','em_analise','aprovada','cancelada') OR prazo IS NOT NULL)
  AND (status <> 'concluida' OR (concluido_por IS NOT NULL AND concluida_em IS NOT NULL))
  AND (status <> 'cancelada' OR justificativa_cancelamento IS NOT NULL));

-- Medições
ALTER TABLE vd_medicoes    DROP CONSTRAINT IF EXISTS ck_med_dominio;
ALTER TABLE vd_medicoes    ADD  CONSTRAINT ck_med_dominio CHECK (tipo IN ('linha_base','acompanhamento') AND status IN ('ativo','cancelado'));

-- Benefícios
ALTER TABLE vd_beneficios  DROP CONSTRAINT IF EXISTS ck_ben_dominio;
ALTER TABLE vd_beneficios  ADD  CONSTRAINT ck_ben_dominio CHECK (
  estagio IN ('estimado','em_validacao','validado','recusado') AND origem IN ('calculado','manual') AND versao >= 1
  AND (estagio IN ('estimado','recusado') OR (medicao_antes_id IS NOT NULL AND medicao_depois_id IS NOT NULL AND diferenca_medida IS NOT NULL))
  AND (estagio <> 'validado' OR (validado_por IS NOT NULL AND validado_em IS NOT NULL))
  AND (estagio <> 'recusado' OR justificativa_validacao IS NOT NULL)
  AND (valor_financeiro IS NULL OR (custo_unitario IS NOT NULL AND fonte_custo_unitario IS NOT NULL)));

-- Evidências e histórico
ALTER TABLE vd_evidencias  DROP CONSTRAINT IF EXISTS ck_evi_dominio;
ALTER TABLE vd_evidencias  ADD  CONSTRAINT ck_evi_dominio CHECK (
  entidade_tipo IN ('objetivo','processo','indicador','vinculo','achado','intervencao','medicao','beneficio')
  AND tipo IN ('link','consulta_sql','texto') AND origem IN ('manual','calculado','importacao'));
ALTER TABLE vd_historico   DROP CONSTRAINT IF EXISTS ck_his_dominio;
ALTER TABLE vd_historico   ADD  CONSTRAINT ck_his_dominio CHECK (
  entidade_tipo IN ('objetivo','processo','indicador','vinculo','achado','intervencao','medicao','beneficio','evidencia')
  AND acao IN ('criacao','edicao','transicao','validacao','evidencia','cancelamento')
  AND perfil IN ('consultante','curador','aprovador'));


-- ════════════════════════════════════════════════════════════════════
-- 3. TABELA DE CONTROLE DE VERSÃO DO ESQUEMA (idempotente)
-- ════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS vd_controle_versao (
  versao                    STRING        NOT NULL,
  descricao                 STRING        NOT NULL,
  aplicado_por              STRING        NOT NULL,
  aplicado_em               TIMESTAMP     NOT NULL,
  CONSTRAINT vd_controle_versao_pk PRIMARY KEY (versao)
) COMMENT 'Valor dos Dados — versões do esquema aplicadas'
TBLPROPERTIES ('delta.appendOnly' = 'true');

MERGE INTO vd_controle_versao t
USING (SELECT 'v2' AS versao, 'Estruturas do piloto Valor dos Dados' AS descricao,
              current_user() AS aplicado_por, current_timestamp() AS aplicado_em) s
ON t.versao = s.versao
WHEN NOT MATCHED THEN INSERT *;


-- ════════════════════════════════════════════════════════════════════
-- 4. PADRÃO DE GRAVAÇÃO DA APLICAÇÃO (referência — não executar)
--    Toda inclusão é MERGE pela chave natural, então repetir a operação não
--    duplica. Toda atualização confere a versão lida (concorrência otimista)
--    e grava uma linha em vd_historico.
-- ════════════════════════════════════════════════════════════════════
-- MERGE INTO vd_vinculos t
-- USING (SELECT :vinculo_id AS vinculo_id, :chave_natural AS chave_natural, ... ) s
-- ON t.chave_natural = s.chave_natural
-- WHEN NOT MATCHED THEN INSERT *;
--
-- UPDATE vd_intervencoes
--    SET status = :novo_status, versao = versao + 1, atualizado_por = :usuario, atualizado_em = current_timestamp()
--  WHERE intervencao_id = :id AND versao = :versao_lida AND status = :status_esperado;
--  -- 0 linhas afetadas = conflito ou transição inválida → nada é gravado no histórico


-- ════════════════════════════════════════════════════════════════════
-- 5. INTEGRIDADE (somente leitura) — devem retornar zero linhas
--    Rodadas pela aplicação antes de cada diagnóstico e disponíveis na
--    tela de auditoria do módulo.
-- ════════════════════════════════════════════════════════════════════

-- 5.1 Duplicidade de chave natural
SELECT 'vd_objetivos' AS tabela, chave_natural, COUNT(*) AS n FROM vd_objetivos   GROUP BY chave_natural HAVING COUNT(*) > 1
UNION ALL SELECT 'vd_processos',    chave_natural, COUNT(*) FROM vd_processos    GROUP BY chave_natural HAVING COUNT(*) > 1
UNION ALL SELECT 'vd_indicadores',  chave_natural, COUNT(*) FROM vd_indicadores  GROUP BY chave_natural HAVING COUNT(*) > 1
UNION ALL SELECT 'vd_vinculos',     chave_natural, COUNT(*) FROM vd_vinculos     GROUP BY chave_natural HAVING COUNT(*) > 1
UNION ALL SELECT 'vd_achados',      chave_natural, COUNT(*) FROM vd_achados      GROUP BY chave_natural HAVING COUNT(*) > 1
UNION ALL SELECT 'vd_intervencoes', chave_natural, COUNT(*) FROM vd_intervencoes GROUP BY chave_natural HAVING COUNT(*) > 1
UNION ALL SELECT 'vd_medicoes',     chave_natural, COUNT(*) FROM vd_medicoes     GROUP BY chave_natural HAVING COUNT(*) > 1
UNION ALL SELECT 'vd_beneficios',   chave_natural, COUNT(*) FROM vd_beneficios   GROUP BY chave_natural HAVING COUNT(*) > 1
UNION ALL SELECT 'vd_evidencias',   chave_natural, COUNT(*) FROM vd_evidencias   GROUP BY chave_natural HAVING COUNT(*) > 1
UNION ALL SELECT 'vd_intervencoes:codigo', codigo, COUNT(*) FROM vd_intervencoes GROUP BY codigo HAVING COUNT(*) > 1;

-- 5.2 Órfãos entre tabelas novas
SELECT 'processo sem objetivo' AS problema, p.processo_id AS id FROM vd_processos p LEFT ANTI JOIN vd_objetivos o ON p.objetivo_id = o.objetivo_id
UNION ALL SELECT 'indicador sem objetivo', i.indicador_id FROM vd_indicadores i LEFT ANTI JOIN vd_objetivos o ON i.objetivo_id = o.objetivo_id
UNION ALL SELECT 'vinculo sem origem', v.vinculo_id FROM vd_vinculos v
          WHERE (v.origem_tipo = 'objetivo' AND NOT EXISTS (SELECT 1 FROM vd_objetivos o WHERE o.objetivo_id = v.origem_id))
             OR (v.origem_tipo = 'processo' AND NOT EXISTS (SELECT 1 FROM vd_processos p WHERE p.processo_id = v.origem_id))
UNION ALL SELECT 'achado sem vinculo', a.achado_id FROM vd_achados a LEFT ANTI JOIN vd_vinculos v ON a.vinculo_id = v.vinculo_id
UNION ALL SELECT 'intervencao sem achado', i.intervencao_id FROM vd_intervencoes i LEFT ANTI JOIN vd_achados a ON i.achado_id = a.achado_id
UNION ALL SELECT 'medicao sem indicador', m.medicao_id FROM vd_medicoes m LEFT ANTI JOIN vd_indicadores i ON m.indicador_id = i.indicador_id
UNION ALL SELECT 'beneficio sem intervencao', b.beneficio_id FROM vd_beneficios b LEFT ANTI JOIN vd_intervencoes i ON b.intervencao_id = i.intervencao_id
UNION ALL SELECT 'historico sem entidade conhecida', h.historico_id FROM vd_historico h
          WHERE h.entidade_tipo = 'intervencao' AND NOT EXISTS (SELECT 1 FROM vd_intervencoes i WHERE i.intervencao_id = h.entidade_id);

-- 5.3 Vínculos apontando para objetos inexistentes no catálogo atual
--     (na aplicação, viram achado nao_identificado — regra DG-09)
SELECT v.vinculo_id, v.ref_tipo, v.ref_schema, v.ref_nome, v.ref_id
FROM vd_vinculos v
WHERE v.status = 'ativo' AND (
     (v.ref_tipo = 'ativo' AND NOT EXISTS (SELECT 1 FROM tabelas_metadata m WHERE m.schema_name = v.ref_schema AND m.table_name = v.ref_nome))
  OR (v.ref_tipo = 'produto' AND NOT EXISTS (SELECT 1 FROM produtos_dados p WHERE p.produto_id = v.ref_id))
  OR (v.ref_tipo = 'termo_glossario' AND NOT EXISTS (SELECT 1 FROM business_glossary g WHERE g.glossary_id = v.ref_id))
  OR (v.ref_tipo = 'indicador' AND NOT EXISTS (SELECT 1 FROM vd_indicadores i WHERE i.indicador_id = v.ref_id)));

-- 5.4 Entidades alteradas sem registro no histórico
SELECT 'intervencao' AS entidade, i.intervencao_id, i.versao
FROM vd_intervencoes i
WHERE NOT EXISTS (SELECT 1 FROM vd_historico h WHERE h.entidade_tipo = 'intervencao'
                  AND h.entidade_id = i.intervencao_id AND h.versao_entidade = i.versao);


-- ════════════════════════════════════════════════════════════════════
-- 6. PERMISSÕES (Unity Catalog)
--    Substitua os marcadores <...> pelos principais reais antes de rodar.
--    • O app usa uma única credencial: no banco ele pode ler e gravar,
--      mas não alterar estrutura nem apagar tabelas.
--    • A distinção entre consultante, curador e aprovador é aplicada pela
--      aplicação (matriz na especificação), porque todos os usuários
--      acessam o banco pela credencial do app.
--    • Histórico e evidências são imutáveis por propriedade da tabela
--      (appendOnly), independentemente de permissão.
-- ════════════════════════════════════════════════════════════════════
-- ALTER TABLE vd_objetivos    OWNER TO `<grupo_administradores_governanca>`;
-- (repetir OWNER TO para todas as tabelas vd_*)
--
-- GRANT USE CATALOG ON CATALOG workspace            TO `<principal_do_app>`;
-- GRANT USE SCHEMA  ON SCHEMA  meridian_governanca  TO `<principal_do_app>`;
-- GRANT SELECT, MODIFY ON TABLE vd_objetivos        TO `<principal_do_app>`;
-- GRANT SELECT, MODIFY ON TABLE vd_processos        TO `<principal_do_app>`;
-- GRANT SELECT, MODIFY ON TABLE vd_indicadores      TO `<principal_do_app>`;
-- GRANT SELECT, MODIFY ON TABLE vd_vinculos         TO `<principal_do_app>`;
-- GRANT SELECT, MODIFY ON TABLE vd_achados          TO `<principal_do_app>`;
-- GRANT SELECT, MODIFY ON TABLE vd_intervencoes     TO `<principal_do_app>`;
-- GRANT SELECT, MODIFY ON TABLE vd_medicoes         TO `<principal_do_app>`;
-- GRANT SELECT, MODIFY ON TABLE vd_beneficios       TO `<principal_do_app>`;
-- GRANT SELECT, MODIFY ON TABLE vd_evidencias       TO `<principal_do_app>`;
-- GRANT SELECT, MODIFY ON TABLE vd_historico        TO `<principal_do_app>`;
-- GRANT SELECT         ON TABLE vd_controle_versao  TO `<principal_do_app>`;
--
-- Leitura analítica (opcional, ex.: painéis externos)
-- GRANT SELECT ON SCHEMA meridian_governanca TO `<grupo_leitura>`;


-- ════════════════════════════════════════════════════════════════════
-- REVERSÃO (não executar sem decisão explícita) — remove apenas vd_*
-- ════════════════════════════════════════════════════════════════════
-- DROP TABLE IF EXISTS vd_historico;
-- DROP TABLE IF EXISTS vd_evidencias;
-- DROP TABLE IF EXISTS vd_beneficios;
-- DROP TABLE IF EXISTS vd_medicoes;
-- DROP TABLE IF EXISTS vd_intervencoes;
-- DROP TABLE IF EXISTS vd_achados;
-- DROP TABLE IF EXISTS vd_vinculos;
-- DROP TABLE IF EXISTS vd_indicadores;
-- DROP TABLE IF EXISTS vd_processos;
-- DROP TABLE IF EXISTS vd_objetivos;
-- DROP TABLE IF EXISTS vd_controle_versao;
