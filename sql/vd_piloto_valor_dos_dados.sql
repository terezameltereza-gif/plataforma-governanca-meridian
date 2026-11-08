-- ════════════════════════════════════════════════════════════════════
-- GOVERNANTES · Módulo Valor dos Dados · Piloto (cenário Banco Meridian)
-- Script de criação das estruturas novas — versão 1 (para aprovação)
--
-- Princípios
--   • Nenhuma tabela existente é alterada. Este script só cria tabelas vd_*.
--   • Ativos, glossário, regras, produtos, qualidade e linhagem são
--     REFERENCIADOS pelas chaves que já existem; nenhum metadado é copiado.
--   • Identificadores: UUID (STRING) gerado pela aplicação, como no restante
--     da plataforma (uuid.uuid4()).
--   • Usuários: e-mail, a mesma chave usada em data_owner / data_steward.
--   • Chaves primárias e estrangeiras no Unity Catalog são INFORMATIVAS (não
--     impostas). A integridade é garantida pela aplicação e verificada pela
--     consulta de órfãos no fim deste arquivo. CHECK e NOT NULL são impostos.
--
-- Ordem de execução
--   0. Bloco de verificação (somente leitura) — confirmar as chaves existentes
--   1. Criação das tabelas (idempotente: IF NOT EXISTS)
--   2. Restrições CHECK
--   3. Consultas de integridade (somente leitura)
--   Reversão: bloco comentado no final.
-- ════════════════════════════════════════════════════════════════════

USE CATALOG workspace;
USE SCHEMA meridian_governanca;

-- ────────────────────────────────────────────────────────────────────
-- 0. VERIFICAÇÃO PRÉVIA (somente leitura)
--    Confirma as colunas-chave das tabelas que serão referenciadas.
--    Atenção especial: glossary_asset_link e produto_ativos — o código
--    atual lê apenas table_name; verificar se existe schema_name.
-- ────────────────────────────────────────────────────────────────────
DESCRIBE TABLE tabelas_metadata;
DESCRIBE TABLE glossary_asset_link;
DESCRIBE TABLE business_glossary;
DESCRIBE TABLE business_rules;
DESCRIBE TABLE produtos_dados;
DESCRIBE TABLE produto_ativos;
DESCRIBE TABLE gd_quality_dimensions;
DESCRIBE TABLE linhagem_ativos;

-- Unicidade da chave de ativo (deve retornar zero linhas)
SELECT schema_name, table_name, COUNT(*) AS ocorrencias
FROM tabelas_metadata GROUP BY schema_name, table_name HAVING COUNT(*) > 1;


-- ────────────────────────────────────────────────────────────────────
-- 1. TABELAS
-- ────────────────────────────────────────────────────────────────────

-- 1.1 Objetivos e desafios de negócio ---------------------------------
CREATE TABLE IF NOT EXISTS vd_objetivos (
  objetivo_id               STRING    NOT NULL COMMENT 'UUID',
  tipo                      STRING    NOT NULL COMMENT 'objetivo | desafio',
  nome                      STRING    NOT NULL,
  descricao                 STRING,
  area_negocio              STRING    NOT NULL,
  objetivo_estrategico      STRING    COMMENT 'Objetivo estratégico ao qual se subordina',
  resp_negocio              STRING    NOT NULL COMMENT 'E-mail do responsável pelo negócio',
  resp_acompanhamento       STRING    NOT NULL COMMENT 'E-mail do responsável pelo acompanhamento',
  prioridade                STRING    NOT NULL COMMENT 'alta | media | baixa',
  data_inicio               DATE,
  data_prevista             DATE,
  status                    STRING    NOT NULL COMMENT 'rascunho | ativo | atingido | nao_atingido | cancelado',
  limite_qualidade_pct      DECIMAL(5,2) COMMENT 'Score mínimo de qualidade exigido dos ativos vinculados; sem valor = regra de qualidade não aplicada',
  criterio_sucesso          STRING    NOT NULL,
  -- Linha de base e meta ficam em vd_indicadores / vd_medicoes (fonte única)
  criado_por                STRING    NOT NULL,
  criado_em                 TIMESTAMP NOT NULL,
  atualizado_por            STRING,
  atualizado_em             TIMESTAMP,
  CONSTRAINT vd_objetivos_pk PRIMARY KEY (objetivo_id)
) COMMENT 'Valor dos Dados — objetivos e desafios de negócio';

-- 1.2 Processos de negócio -----------------------------------------------
CREATE TABLE IF NOT EXISTS vd_processos (
  processo_id               STRING    NOT NULL,
  objetivo_id               STRING    NOT NULL,
  nome                      STRING    NOT NULL,
  descricao                 STRING,
  area_negocio              STRING    NOT NULL,
  resp_processo             STRING    NOT NULL COMMENT 'E-mail',
  periodicidade             STRING    COMMENT 'Ex.: mensal',
  criticidade               STRING    NOT NULL COMMENT 'alta | media | baixa',
  criado_por                STRING    NOT NULL,
  criado_em                 TIMESTAMP NOT NULL,
  atualizado_por            STRING,
  atualizado_em             TIMESTAMP,
  CONSTRAINT vd_processos_pk PRIMARY KEY (processo_id),
  CONSTRAINT vd_processos_obj_fk FOREIGN KEY (objetivo_id) REFERENCES vd_objetivos (objetivo_id)
) COMMENT 'Valor dos Dados — processos de negócio ligados a objetivos';

-- 1.3 Indicadores de resultado ------------------------------------------
CREATE TABLE IF NOT EXISTS vd_indicadores (
  indicador_id              STRING    NOT NULL,
  objetivo_id               STRING    NOT NULL,
  processo_id               STRING,
  papel                     STRING    NOT NULL COMMENT 'principal | complementar',
  nome                      STRING    NOT NULL,
  descricao                 STRING,
  unidade                   STRING    NOT NULL COMMENT 'Ex.: horas, quantidade, %',
  sentido_melhora           STRING    NOT NULL COMMENT 'reduzir | aumentar',
  formula                   STRING    NOT NULL,
  fonte                     STRING    NOT NULL COMMENT 'Origem do dado medido',
  periodicidade             STRING    NOT NULL,
  responsavel               STRING    NOT NULL COMMENT 'E-mail',
  meta                      DECIMAL(18,4),
  criado_por                STRING    NOT NULL,
  criado_em                 TIMESTAMP NOT NULL,
  CONSTRAINT vd_indicadores_pk PRIMARY KEY (indicador_id),
  CONSTRAINT vd_indicadores_obj_fk FOREIGN KEY (objetivo_id) REFERENCES vd_objetivos (objetivo_id),
  CONSTRAINT vd_indicadores_proc_fk FOREIGN KEY (processo_id) REFERENCES vd_processos (processo_id)
) COMMENT 'Valor dos Dados — indicadores de resultado (piloto: horas de retrabalho = principal; divergências = complementar)';

-- 1.4 Vínculos negócio → objetos já existentes --------------------------
--   ref_tipo e chave de referência (nenhum metadado é copiado):
--     ativo           → ref_schema + ref_nome            (tabelas_metadata.schema_name, table_name)
--     produto         → ref_id                           (produtos_dados.produto_id)
--     termo_glossario → ref_id                           (business_glossary.glossary_id)
--     regra_negocio   → ref_id                           (business_rules: chave a confirmar no passo 0)
--     dominio         → ref_nome                         (valor de tabelas_metadata.dominio; não há tabela de domínios)
--     indicador       → ref_id                           (vd_indicadores.indicador_id)
--     responsavel     → ref_nome                         (e-mail)
--   Campos e sistemas: fora do piloto — a plataforma ainda não possui
--   metadados de coluna nem cadastro de sistemas.
CREATE TABLE IF NOT EXISTS vd_vinculos (
  vinculo_id                STRING    NOT NULL,
  origem_tipo               STRING    NOT NULL COMMENT 'objetivo | processo',
  origem_id                 STRING    NOT NULL,
  ref_tipo                  STRING    NOT NULL,
  ref_id                    STRING,
  ref_schema                STRING,
  ref_nome                  STRING,
  papel_no_processo         STRING    COMMENT 'fonte | intermediario | saida — obrigatório para ativos; informado pelo curador, nunca inferido',
  base_do_vinculo           STRING    NOT NULL COMMENT 'manual | metadado | sugestao_ia',
  evidencia_base            STRING    COMMENT 'Ex.: registro de linhagem ou produto que comprova a relação',
  status_validacao          STRING    NOT NULL COMMENT 'pendente | validado | rejeitado',
  validado_por              STRING,
  validado_em               TIMESTAMP,
  criado_por                STRING    NOT NULL,
  criado_em                 TIMESTAMP NOT NULL,
  CONSTRAINT vd_vinculos_pk PRIMARY KEY (vinculo_id)
) COMMENT 'Valor dos Dados — relações entre negócio e dados, por referência às chaves existentes';

-- 1.5 Achados do diagnóstico ---------------------------------------------
--   natureza (o que se sabe) é separada de status_validacao (quem confirmou):
--     nao_cadastrado   → o campo existe na plataforma e está vazio (ausência de informação)
--     nao_identificado → a plataforma não tem como verificar (falta a fonte da informação)
--     nao_conforme     → a informação existe e viola um critério definido, com evidência
--     nao_aplicavel    → atribuído só por pessoa, com justificativa
CREATE TABLE IF NOT EXISTS vd_achados (
  achado_id                 STRING    NOT NULL,
  execucao_id               STRING    NOT NULL COMMENT 'Agrupa os achados de uma mesma execução do diagnóstico',
  objetivo_id               STRING    NOT NULL,
  processo_id               STRING,
  vinculo_id                STRING    NOT NULL COMMENT 'Vínculo (ativo/produto) avaliado',
  regra_codigo              STRING    NOT NULL COMMENT 'Ex.: DG-01 sem owner (catálogo de regras na especificação)',
  natureza                  STRING    NOT NULL,
  evidencia                 STRING    NOT NULL COMMENT 'Fato verificado: tabela, campo e valor consultado',
  valor_observado           STRING,
  criterio                  STRING    COMMENT 'Critério aplicado (ex.: limite de qualidade do objetivo)',
  status_validacao          STRING    NOT NULL COMMENT 'pendente | validado | descartado',
  justificativa_validacao   STRING,
  validado_por              STRING,
  validado_em               TIMESTAMP,
  detectado_em              TIMESTAMP NOT NULL,
  CONSTRAINT vd_achados_pk PRIMARY KEY (achado_id),
  CONSTRAINT vd_achados_obj_fk FOREIGN KEY (objetivo_id) REFERENCES vd_objetivos (objetivo_id),
  CONSTRAINT vd_achados_vinc_fk FOREIGN KEY (vinculo_id) REFERENCES vd_vinculos (vinculo_id)
) COMMENT 'Valor dos Dados — achados do diagnóstico por regras documentadas';

-- 1.6 Intervenções -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS vd_intervencoes (
  intervencao_id            STRING    NOT NULL,
  codigo                    STRING    NOT NULL COMMENT 'Identificador legível, ex.: INT-0001',
  achado_id                 STRING    NOT NULL COMMENT 'Problema de origem (achado validado)',
  objetivo_id               STRING    NOT NULL,
  titulo                    STRING    NOT NULL,
  recomendacao              STRING    NOT NULL,
  tipo_afirmacao            STRING    NOT NULL COMMENT 'Separa fato de hipótese: fato | hipotese',
  causa_provavel            STRING    COMMENT 'Só preenchida quando houver evidência',
  responsavel               STRING    NOT NULL COMMENT 'E-mail',
  area                      STRING    NOT NULL,
  -- Priorização: pontos gravados por critério para explicar a prioridade
  pts_prioridade_objetivo   INT,
  pts_posicao_ativo         INT,
  pts_tipo_achado           INT,
  pts_abrangencia           INT,
  abrangencia_ativos        INT       COMMENT 'Nº de ativos a jusante pela linhagem; nulo = não determinada',
  pts_esforco               INT,
  esforco                   STRING    COMMENT 'baixo | medio | alto | nao_informado',
  pontuacao_total           INT,
  prioridade                STRING    NOT NULL COMMENT 'critica | alta | media | baixa',
  criterio_conclusao        STRING    NOT NULL,
  status                    STRING    NOT NULL,
  aberta_em                 TIMESTAMP NOT NULL,
  prazo                     DATE,
  concluida_em              TIMESTAMP,
  criado_por                STRING    NOT NULL,
  atualizado_por            STRING,
  atualizado_em             TIMESTAMP,
  CONSTRAINT vd_intervencoes_pk PRIMARY KEY (intervencao_id),
  CONSTRAINT vd_intervencoes_achado_fk FOREIGN KEY (achado_id) REFERENCES vd_achados (achado_id),
  CONSTRAINT vd_intervencoes_obj_fk FOREIGN KEY (objetivo_id) REFERENCES vd_objetivos (objetivo_id)
) COMMENT 'Valor dos Dados — intervenções rastreáveis, executadas pelo Meu Espaço';

-- 1.7 Medições dos indicadores ------------------------------------------
CREATE TABLE IF NOT EXISTS vd_medicoes (
  medicao_id                STRING    NOT NULL,
  indicador_id              STRING    NOT NULL,
  tipo                      STRING    NOT NULL COMMENT 'linha_base | acompanhamento',
  data_referencia           DATE      NOT NULL COMMENT 'Ex.: fechamento de out/2026',
  valor                     DECIMAL(18,4) NOT NULL,
  metodo                    STRING    NOT NULL COMMENT 'Como o valor foi obtido',
  intervencao_id            STRING    COMMENT 'Intervenção executada antes desta medição, se houver',
  registrado_por            STRING    NOT NULL,
  registrado_em             TIMESTAMP NOT NULL,
  CONSTRAINT vd_medicoes_pk PRIMARY KEY (medicao_id),
  CONSTRAINT vd_medicoes_ind_fk FOREIGN KEY (indicador_id) REFERENCES vd_indicadores (indicador_id)
) COMMENT 'Valor dos Dados — medições informadas pela organização (nenhum valor é gerado pela plataforma)';

-- 1.8 Benefícios -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vd_beneficios (
  beneficio_id              STRING    NOT NULL,
  indicador_id              STRING    NOT NULL,
  intervencao_id            STRING    NOT NULL,
  medicao_antes_id          STRING    COMMENT 'Obrigatória a partir de em_validacao',
  medicao_depois_id         STRING    COMMENT 'Obrigatória a partir de em_validacao',
  estagio                   STRING    NOT NULL COMMENT 'estimado | em_validacao | validado | recusado',
  premissas                 STRING    NOT NULL COMMENT 'Premissas documentadas do cálculo',
  valor_estimado            DECIMAL(18,4) COMMENT 'Na unidade do indicador',
  diferenca_medida          DECIMAL(18,4) COMMENT 'Calculada das medições; gravada para auditoria',
  custo_unitario            DECIMAL(18,2) COMMENT 'Parâmetro financeiro fornecido pela organização (ex.: R$/hora)',
  fonte_custo_unitario      STRING,
  valor_financeiro          DECIMAL(18,2) COMMENT 'diferenca_medida (ou valor_estimado) × custo_unitario',
  ressalva_causalidade      STRING    NOT NULL COMMENT 'Resultado associado à intervenção, sem atribuição causal exclusiva',
  validado_por              STRING    COMMENT 'Responsável de negócio',
  validado_em               TIMESTAMP,
  criado_por                STRING    NOT NULL,
  criado_em                 TIMESTAMP NOT NULL,
  CONSTRAINT vd_beneficios_pk PRIMARY KEY (beneficio_id),
  CONSTRAINT vd_beneficios_ind_fk FOREIGN KEY (indicador_id) REFERENCES vd_indicadores (indicador_id),
  CONSTRAINT vd_beneficios_int_fk FOREIGN KEY (intervencao_id) REFERENCES vd_intervencoes (intervencao_id)
) COMMENT 'Valor dos Dados — benefícios: estimado → em validação → validado';

-- 1.9 Evidências (genérica, para achados, intervenções, medições e benefícios)
--   O app não armazena arquivos: a evidência é um link (documento, Volume
--   do Unity Catalog, ticket), uma consulta SQL com o resultado registrado,
--   ou um texto descritivo.
CREATE TABLE IF NOT EXISTS vd_evidencias (
  evidencia_id              STRING    NOT NULL,
  entidade_tipo             STRING    NOT NULL COMMENT 'achado | intervencao | medicao | beneficio',
  entidade_id               STRING    NOT NULL,
  tipo                      STRING    NOT NULL COMMENT 'link | consulta_sql | texto',
  descricao                 STRING    NOT NULL,
  conteudo                  STRING    NOT NULL COMMENT 'URL, SQL + resultado registrado, ou texto',
  registrado_por            STRING    NOT NULL,
  registrado_em             TIMESTAMP NOT NULL,
  CONSTRAINT vd_evidencias_pk PRIMARY KEY (evidencia_id)
) COMMENT 'Valor dos Dados — evidências (somente inclusão; nunca editadas ou apagadas)';

-- 1.10 Histórico (somente inclusão) ------------------------------------------
CREATE TABLE IF NOT EXISTS vd_historico (
  historico_id              STRING    NOT NULL,
  entidade_tipo             STRING    NOT NULL COMMENT 'objetivo | vinculo | achado | intervencao | medicao | beneficio',
  entidade_id               STRING    NOT NULL,
  acao                      STRING    NOT NULL COMMENT 'criacao | transicao | edicao | validacao | evidencia',
  status_anterior           STRING,
  status_novo               STRING,
  campos_alterados          STRING    COMMENT 'JSON {campo: [antes, depois]} para edições',
  comentario                STRING,
  evidencia_id              STRING,
  executado_por             STRING    NOT NULL,
  perfil                    STRING    NOT NULL COMMENT 'Perfil do usuário no momento da ação',
  executado_em              TIMESTAMP NOT NULL,
  CONSTRAINT vd_historico_pk PRIMARY KEY (historico_id)
) COMMENT 'Valor dos Dados — trilha de auditoria de todas as mudanças relevantes';


-- ────────────────────────────────────────────────────────────────────
-- 2. RESTRIÇÕES CHECK (impostas pelo Delta)
-- ────────────────────────────────────────────────────────────────────
ALTER TABLE vd_objetivos ADD CONSTRAINT ck_obj_tipo       CHECK (tipo IN ('objetivo','desafio'));
ALTER TABLE vd_objetivos ADD CONSTRAINT ck_obj_prioridade CHECK (prioridade IN ('alta','media','baixa'));
ALTER TABLE vd_objetivos ADD CONSTRAINT ck_obj_status     CHECK (status IN ('rascunho','ativo','atingido','nao_atingido','cancelado'));
ALTER TABLE vd_objetivos ADD CONSTRAINT ck_obj_limite     CHECK (limite_qualidade_pct IS NULL OR limite_qualidade_pct BETWEEN 0 AND 100);

ALTER TABLE vd_processos ADD CONSTRAINT ck_proc_crit      CHECK (criticidade IN ('alta','media','baixa'));

ALTER TABLE vd_indicadores ADD CONSTRAINT ck_ind_papel    CHECK (papel IN ('principal','complementar'));
ALTER TABLE vd_indicadores ADD CONSTRAINT ck_ind_sentido  CHECK (sentido_melhora IN ('reduzir','aumentar'));

ALTER TABLE vd_vinculos ADD CONSTRAINT ck_vin_origem      CHECK (origem_tipo IN ('objetivo','processo'));
ALTER TABLE vd_vinculos ADD CONSTRAINT ck_vin_ref_tipo    CHECK (ref_tipo IN ('ativo','produto','termo_glossario','regra_negocio','dominio','indicador','responsavel'));
ALTER TABLE vd_vinculos ADD CONSTRAINT ck_vin_chave       CHECK (
      (ref_tipo = 'ativo'       AND ref_schema IS NOT NULL AND ref_nome IS NOT NULL)
   OR (ref_tipo IN ('produto','termo_glossario','regra_negocio','indicador') AND ref_id IS NOT NULL)
   OR (ref_tipo IN ('dominio','responsavel') AND ref_nome IS NOT NULL));
ALTER TABLE vd_vinculos ADD CONSTRAINT ck_vin_papel       CHECK (ref_tipo <> 'ativo' OR papel_no_processo IN ('fonte','intermediario','saida'));
ALTER TABLE vd_vinculos ADD CONSTRAINT ck_vin_base        CHECK (base_do_vinculo IN ('manual','metadado','sugestao_ia'));
ALTER TABLE vd_vinculos ADD CONSTRAINT ck_vin_status      CHECK (status_validacao IN ('pendente','validado','rejeitado'));
ALTER TABLE vd_vinculos ADD CONSTRAINT ck_vin_ia          CHECK (base_do_vinculo <> 'sugestao_ia' OR status_validacao <> 'validado' OR validado_por IS NOT NULL);

ALTER TABLE vd_achados ADD CONSTRAINT ck_ach_natureza     CHECK (natureza IN ('nao_cadastrado','nao_identificado','nao_conforme','nao_aplicavel'));
ALTER TABLE vd_achados ADD CONSTRAINT ck_ach_status       CHECK (status_validacao IN ('pendente','validado','descartado'));
ALTER TABLE vd_achados ADD CONSTRAINT ck_ach_na_justif    CHECK (natureza <> 'nao_aplicavel' OR justificativa_validacao IS NOT NULL);
ALTER TABLE vd_achados ADD CONSTRAINT ck_ach_nc_criterio  CHECK (natureza <> 'nao_conforme' OR criterio IS NOT NULL);
ALTER TABLE vd_achados ADD CONSTRAINT ck_ach_validacao    CHECK (status_validacao = 'pendente' OR (validado_por IS NOT NULL AND validado_em IS NOT NULL));

ALTER TABLE vd_intervencoes ADD CONSTRAINT ck_int_status  CHECK (status IN ('identificada','em_analise','aprovada','planejada','em_execucao','em_validacao','concluida','cancelada'));
ALTER TABLE vd_intervencoes ADD CONSTRAINT ck_int_prior   CHECK (prioridade IN ('critica','alta','media','baixa'));
ALTER TABLE vd_intervencoes ADD CONSTRAINT ck_int_afirm   CHECK (tipo_afirmacao IN ('fato','hipotese'));
ALTER TABLE vd_intervencoes ADD CONSTRAINT ck_int_esforco CHECK (esforco IS NULL OR esforco IN ('baixo','medio','alto','nao_informado'));
ALTER TABLE vd_intervencoes ADD CONSTRAINT ck_int_planej  CHECK (status IN ('identificada','em_analise','aprovada','cancelada') OR prazo IS NOT NULL);
ALTER TABLE vd_intervencoes ADD CONSTRAINT ck_int_concl   CHECK (status <> 'concluida' OR concluida_em IS NOT NULL);

ALTER TABLE vd_medicoes ADD CONSTRAINT ck_med_tipo        CHECK (tipo IN ('linha_base','acompanhamento'));

ALTER TABLE vd_beneficios ADD CONSTRAINT ck_ben_estagio   CHECK (estagio IN ('estimado','em_validacao','validado','recusado'));
ALTER TABLE vd_beneficios ADD CONSTRAINT ck_ben_medicoes  CHECK (estagio IN ('estimado','recusado') OR (medicao_antes_id IS NOT NULL AND medicao_depois_id IS NOT NULL AND diferenca_medida IS NOT NULL));
ALTER TABLE vd_beneficios ADD CONSTRAINT ck_ben_validado  CHECK (estagio <> 'validado' OR (validado_por IS NOT NULL AND validado_em IS NOT NULL));
ALTER TABLE vd_beneficios ADD CONSTRAINT ck_ben_financ    CHECK (valor_financeiro IS NULL OR (custo_unitario IS NOT NULL AND fonte_custo_unitario IS NOT NULL));

ALTER TABLE vd_evidencias ADD CONSTRAINT ck_evi_entidade  CHECK (entidade_tipo IN ('achado','intervencao','medicao','beneficio'));
ALTER TABLE vd_evidencias ADD CONSTRAINT ck_evi_tipo      CHECK (tipo IN ('link','consulta_sql','texto'));

ALTER TABLE vd_historico ADD CONSTRAINT ck_his_entidade   CHECK (entidade_tipo IN ('objetivo','vinculo','achado','intervencao','medicao','beneficio'));
ALTER TABLE vd_historico ADD CONSTRAINT ck_his_acao       CHECK (acao IN ('criacao','transicao','edicao','validacao','evidencia'));


-- ────────────────────────────────────────────────────────────────────
-- 3. INTEGRIDADE (somente leitura) — vínculos que apontam para objetos
--    inexistentes. Rodada também pela aplicação antes de cada diagnóstico;
--    vínculo órfão vira achado "nao_identificado", nunca "nao_conforme".
-- ────────────────────────────────────────────────────────────────────
SELECT v.vinculo_id, v.ref_tipo, v.ref_schema, v.ref_nome, v.ref_id
FROM vd_vinculos v
LEFT JOIN tabelas_metadata m ON v.ref_tipo = 'ativo' AND m.schema_name = v.ref_schema AND m.table_name = v.ref_nome
LEFT JOIN produtos_dados   p ON v.ref_tipo = 'produto' AND p.produto_id = v.ref_id
LEFT JOIN business_glossary g ON v.ref_tipo = 'termo_glossario' AND g.glossary_id = v.ref_id
WHERE (v.ref_tipo = 'ativo' AND m.table_name IS NULL)
   OR (v.ref_tipo = 'produto' AND p.produto_id IS NULL)
   OR (v.ref_tipo = 'termo_glossario' AND g.glossary_id IS NULL);


-- ────────────────────────────────────────────────────────────────────
-- REVERSÃO (não executar sem decisão explícita) — remove apenas vd_*
-- ────────────────────────────────────────────────────────────────────
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
