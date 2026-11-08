-- ════════════════════════════════════════════════════════════════════
-- GOVERNANTES · Valor dos Dados · v3
-- 01 — Estruturas (cria apenas tabelas vd_*; não altera nem lê dados de negócio)
--
-- Pré-requisito: 00_parametros_e_preverificacao.sql executado sem ABORTAR.
-- Idempotência:
--   • CREATE TABLE IF NOT EXISTS;
--   • restrições CHECK com DROP CONSTRAINT IF EXISTS + ADD CONSTRAINT
--     (reexecução recria a mesma regra; se houver dado que a viole, o ADD
--     falha e a reexecução para — nenhum dado é alterado);
--   • nenhuma carga de dados neste arquivo (dados de referência em 02).
-- Integridade: PK/FK do Unity Catalog são INFORMATIVAS. A garantia está em
--   (1) CHECK/NOT NULL impostos aqui, (2) gravações condicionadas da
--   aplicação (vd_regras.py), (3) validações de 03, (4) proibição de
--   exclusão física: registros são cancelados, nunca apagados.
-- ════════════════════════════════════════════════════════════════════

DECLARE OR REPLACE VARIABLE vd_catalogo STRING DEFAULT 'workspace';
DECLARE OR REPLACE VARIABLE vd_schema   STRING DEFAULT 'meridian_governanca';
USE CATALOG IDENTIFIER(vd_catalogo);
USE SCHEMA  IDENTIFIER(vd_schema);

-- ── 0. Controle de versão do esquema ─────────────────────────────────
CREATE TABLE IF NOT EXISTS vd_controle_versao (
  versao        STRING    NOT NULL,
  descricao     STRING    NOT NULL,
  aplicado_por  STRING    NOT NULL,
  aplicado_em   TIMESTAMP NOT NULL,
  CONSTRAINT vd_controle_versao_pk PRIMARY KEY (versao)
) COMMENT 'Valor dos Dados — versões do esquema aplicadas'
TBLPROPERTIES ('delta.appendOnly' = 'true');

-- Recusa instalar sobre versão diferente (exigiria migração explícita)
SELECT CASE WHEN COUNT(*) = 0 OR COUNT_IF(versao = 'v3') = COUNT(*) THEN 'OK: versão compatível'
            ELSE raise_error(concat('ABORTAR: versão instalada diferente de v3: ', array_join(collect_list(versao), ', ')))
       END AS verificacao_versao
FROM vd_controle_versao;


-- ════════════════════════════════════════════════════════════════════
-- 1. TABELAS DE REFERÊNCIA (conteúdo carregado em 02, versionado)
-- ════════════════════════════════════════════════════════════════════

-- 1.1 Catálogo de regras do diagnóstico
CREATE TABLE IF NOT EXISTS vd_regras_diagnostico (
  regra_codigo      STRING  NOT NULL COMMENT 'DG-01 … DG-09',
  versao_regras     STRING  NOT NULL COMMENT 'Versão do conjunto de regras (ex.: R1)',
  nome              STRING  NOT NULL,
  descricao         STRING  NOT NULL,
  natureza_padrao   STRING  NOT NULL COMMENT 'Natureza atribuída quando a regra dispara',
  fonte             STRING  NOT NULL COMMENT 'Tabela.coluna consultada',
  criterio          STRING  NOT NULL,
  aplica_a          STRING  NOT NULL COMMENT 'ativo | produto | vinculo',
  dependencia       STRING  COMMENT 'Coluna opcional exigida; regra desabilitada se ausente (ver 00, passo 3)',
  vigente           BOOLEAN NOT NULL,
  CONSTRAINT vd_regras_diagnostico_pk PRIMARY KEY (regra_codigo, versao_regras)
) COMMENT 'Valor dos Dados — catálogo versionado de regras do diagnóstico';

-- 1.1b Habilitação das regras no ambiente (decisão, não informação)
--   Recalculada por 02 a partir do catálogo. Regra desabilitada gera
--   ocorrência 'nao_avaliada' com o motivo; nunca é ignorada em silêncio.
CREATE TABLE IF NOT EXISTS vd_regras_habilitacao (
  regra_codigo      STRING    NOT NULL,
  versao_regras     STRING    NOT NULL,
  habilitada        BOOLEAN   NOT NULL,
  motivo            STRING    NOT NULL COMMENT 'Dependência confirmada ou ausente no catálogo',
  verificado_por    STRING    NOT NULL,
  verificado_em     TIMESTAMP NOT NULL,
  CONSTRAINT vd_regras_habilitacao_pk PRIMARY KEY (regra_codigo, versao_regras)
) COMMENT 'Valor dos Dados — regras habilitadas conforme a estrutura confirmada do catálogo'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- 1.2 Modelo de priorização: pontos por critério e entrada
CREATE TABLE IF NOT EXISTS vd_modelo_priorizacao (
  versao_modelo     STRING  NOT NULL COMMENT 'Ex.: P1',
  criterio          STRING  NOT NULL COMMENT 'prioridade_objetivo | posicao_ativo | tipo_achado | abrangencia | esforco',
  entrada           STRING  NOT NULL COMMENT 'Valor de entrada (ex.: alta, saida, 3-5, nao_informado)',
  pontos            INT     NOT NULL,
  peso              INT     NOT NULL COMMENT 'Multiplicador do critério (P1: todos = 1)',
  descricao         STRING  NOT NULL,
  situacao          STRING  NOT NULL COMMENT 'aprovado | pendente — entrada pendente não pode pontuar intervenções',
  CONSTRAINT vd_modelo_priorizacao_pk PRIMARY KEY (versao_modelo, criterio, entrada)
) COMMENT 'Valor dos Dados — escala de pontos por critério (versionada)';

-- 1.3 Faixas de prioridade
CREATE TABLE IF NOT EXISTS vd_faixas_prioridade (
  versao_modelo     STRING  NOT NULL,
  prioridade        STRING  NOT NULL COMMENT 'critica | alta | media | baixa',
  pontuacao_min     INT     NOT NULL,
  pontuacao_max     INT     NOT NULL,
  CONSTRAINT vd_faixas_prioridade_pk PRIMARY KEY (versao_modelo, prioridade)
) COMMENT 'Valor dos Dados — conversão de pontuação total em prioridade';

-- 1.4 Transições permitidas das intervenções
CREATE TABLE IF NOT EXISTS vd_transicoes_intervencao (
  status_de         STRING  NOT NULL,
  status_para       STRING  NOT NULL,
  perfis            STRING  NOT NULL COMMENT 'Lista separada por vírgula: curador,aprovador,responsavel',
  exige             STRING  NOT NULL COMMENT 'Pré-condições verificadas pela aplicação e pela gravação condicionada',
  CONSTRAINT vd_transicoes_intervencao_pk PRIMARY KEY (status_de, status_para)
) COMMENT 'Valor dos Dados — máquina de estados das intervenções';

-- 1.5 Conversões financeiras (fornecidas pela organização; nasce vazia)
CREATE TABLE IF NOT EXISTS vd_conversoes_financeiras (
  conversao_id        STRING        NOT NULL,
  chave_natural       STRING        NOT NULL COMMENT 'unidade_indicador|unidade_custo|moeda|vigencia_inicio',
  unidade_indicador   STRING        NOT NULL COMMENT 'Unidade do indicador (ex.: horas)',
  unidade_custo       STRING        NOT NULL COMMENT 'Unidade do custo (ex.: hora)',
  fator               DECIMAL(18,6) NOT NULL COMMENT 'Quantidade de unidade_custo por unidade_indicador',
  custo_unitario      DECIMAL(18,2) NOT NULL,
  moeda               STRING        NOT NULL COMMENT 'ISO 4217 (ex.: BRL)',
  fonte               STRING        NOT NULL COMMENT 'Origem do parâmetro (ex.: tabela salarial RH 2026)',
  vigencia_inicio     DATE          NOT NULL,
  vigencia_fim        DATE,
  origem              STRING        NOT NULL,
  status_validacao    STRING        NOT NULL,
  validado_por        STRING,
  validado_em         TIMESTAMP,
  justificativa_validacao STRING,
  criado_por          STRING        NOT NULL,
  criado_em           TIMESTAMP     NOT NULL,
  atualizado_por      STRING,
  atualizado_em       TIMESTAMP,
  versao              INT           NOT NULL,
  CONSTRAINT vd_conversoes_financeiras_pk PRIMARY KEY (conversao_id)
) COMMENT 'Valor dos Dados — parâmetros para conversão de resultado operacional em valor financeiro'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');


-- ════════════════════════════════════════════════════════════════════
-- 2. ENTIDADES DO CICLO
-- Bloco padrão de rastreabilidade: origem, chave_natural, status_validacao,
-- validado_por/em, justificativa_validacao, criado_por/em,
-- atualizado_por/em, versao. Evidências em vd_evidencias; histórico em
-- vd_historico (+ Change Data Feed).
-- ════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS vd_objetivos (
  objetivo_id             STRING       NOT NULL,
  chave_natural           STRING       NOT NULL COMMENT 'tipo|nome|area_negocio normalizados',
  tipo                    STRING       NOT NULL,
  nome                    STRING       NOT NULL,
  descricao               STRING,
  area_negocio            STRING       NOT NULL,
  objetivo_estrategico    STRING,
  resp_negocio            STRING       NOT NULL,
  resp_acompanhamento     STRING       NOT NULL,
  prioridade              STRING       NOT NULL,
  data_inicio             DATE,
  data_prevista           DATE,
  status                  STRING       NOT NULL,
  limite_qualidade_pct    DECIMAL(5,2) COMMENT 'Sem valor = DG-06 não se aplica',
  criterio_sucesso        STRING       NOT NULL,
  origem                  STRING       NOT NULL,
  status_validacao        STRING       NOT NULL,
  validado_por            STRING,
  validado_em             TIMESTAMP,
  justificativa_validacao STRING,
  criado_por              STRING       NOT NULL,
  criado_em               TIMESTAMP    NOT NULL,
  atualizado_por          STRING,
  atualizado_em           TIMESTAMP,
  versao                  INT          NOT NULL,
  CONSTRAINT vd_objetivos_pk PRIMARY KEY (objetivo_id)
) COMMENT 'Valor dos Dados — objetivos e desafios'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

CREATE TABLE IF NOT EXISTS vd_processos (
  processo_id             STRING    NOT NULL,
  chave_natural           STRING    NOT NULL COMMENT 'objetivo_id|nome',
  objetivo_id             STRING    NOT NULL,
  nome                    STRING    NOT NULL,
  descricao               STRING,
  area_negocio            STRING    NOT NULL,
  resp_processo           STRING    NOT NULL,
  periodicidade           STRING,
  criticidade             STRING    NOT NULL,
  status                  STRING    NOT NULL,
  origem                  STRING    NOT NULL,
  status_validacao        STRING    NOT NULL,
  validado_por            STRING,
  validado_em             TIMESTAMP,
  justificativa_validacao STRING,
  criado_por              STRING    NOT NULL,
  criado_em               TIMESTAMP NOT NULL,
  atualizado_por          STRING,
  atualizado_em           TIMESTAMP,
  versao                  INT       NOT NULL,
  CONSTRAINT vd_processos_pk PRIMARY KEY (processo_id),
  CONSTRAINT vd_processos_obj_fk FOREIGN KEY (objetivo_id) REFERENCES vd_objetivos (objetivo_id)
) COMMENT 'Valor dos Dados — processos'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

CREATE TABLE IF NOT EXISTS vd_indicadores (
  indicador_id            STRING        NOT NULL,
  chave_natural           STRING        NOT NULL COMMENT 'objetivo_id|nome',
  objetivo_id             STRING        NOT NULL,
  processo_id             STRING        COMMENT 'Se informado, pertence ao mesmo objetivo (regra C02)',
  papel                   STRING        NOT NULL,
  nome                    STRING        NOT NULL,
  descricao               STRING,
  unidade                 STRING        NOT NULL,
  tipo_unidade            STRING        NOT NULL COMMENT 'tempo | quantidade | percentual | monetario',
  sentido_melhora         STRING        NOT NULL COMMENT 'reduzir | aumentar — define a fórmula de melhoria',
  formula                 STRING        NOT NULL,
  fonte                   STRING        NOT NULL,
  periodicidade           STRING        NOT NULL,
  responsavel             STRING        NOT NULL,
  meta                    DECIMAL(18,4),
  status                  STRING        NOT NULL,
  origem                  STRING        NOT NULL,
  status_validacao        STRING        NOT NULL,
  validado_por            STRING,
  validado_em             TIMESTAMP,
  justificativa_validacao STRING,
  criado_por              STRING        NOT NULL,
  criado_em               TIMESTAMP     NOT NULL,
  atualizado_por          STRING,
  atualizado_em           TIMESTAMP,
  versao                  INT           NOT NULL,
  CONSTRAINT vd_indicadores_pk PRIMARY KEY (indicador_id),
  CONSTRAINT vd_indicadores_obj_fk FOREIGN KEY (objetivo_id) REFERENCES vd_objetivos (objetivo_id),
  CONSTRAINT vd_indicadores_proc_fk FOREIGN KEY (processo_id) REFERENCES vd_processos (processo_id)
) COMMENT 'Valor dos Dados — indicadores de resultado'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- objetivo_id é gravado também quando a origem é um processo (desnormalização
-- controlada): permite a verificação de "mesmo objetivo" sem junções e é
-- conferido contra vd_processos em toda gravação (regra C03).
CREATE TABLE IF NOT EXISTS vd_vinculos (
  vinculo_id              STRING    NOT NULL,
  chave_natural           STRING    NOT NULL COMMENT 'origem_tipo|origem_id|ref_tipo|ref_id|ref_schema|ref_nome',
  objetivo_id             STRING    NOT NULL,
  origem_tipo             STRING    NOT NULL,
  origem_id               STRING    NOT NULL,
  ref_tipo                STRING    NOT NULL,
  ref_id                  STRING,
  ref_schema              STRING,
  ref_nome                STRING,
  papel_no_processo       STRING,
  evidencia_base          STRING,
  status                  STRING    NOT NULL,
  origem                  STRING    NOT NULL,
  status_validacao        STRING    NOT NULL,
  validado_por            STRING,
  validado_em             TIMESTAMP,
  justificativa_validacao STRING,
  criado_por              STRING    NOT NULL,
  criado_em               TIMESTAMP NOT NULL,
  atualizado_por          STRING,
  atualizado_em           TIMESTAMP,
  versao                  INT       NOT NULL,
  CONSTRAINT vd_vinculos_pk PRIMARY KEY (vinculo_id),
  CONSTRAINT vd_vinculos_obj_fk FOREIGN KEY (objetivo_id) REFERENCES vd_objetivos (objetivo_id)
) COMMENT 'Valor dos Dados — vínculos por referência às chaves existentes'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- Execuções do diagnóstico
CREATE TABLE IF NOT EXISTS vd_execucoes_diagnostico (
  execucao_id             STRING    NOT NULL,
  objetivo_id             STRING    NOT NULL,
  processo_id             STRING,
  versao_regras           STRING    NOT NULL,
  versao_diagnostico      STRING    NOT NULL COMMENT 'Versão do código que executou (ex.: vd_regras 3.0.0)',
  executado_por           STRING    NOT NULL COMMENT 'E-mail do usuário ou identificação do processo',
  perfil                  STRING    NOT NULL,
  iniciado_em             TIMESTAMP NOT NULL,
  finalizado_em           TIMESTAMP,
  status                  STRING    NOT NULL COMMENT 'em_execucao | concluida | falhou',
  regras_aplicadas        STRING    COMMENT 'Lista de códigos efetivamente avaliados',
  regras_desabilitadas    STRING    COMMENT 'Códigos separados por vírgula (cópia de vd_regras_habilitacao no início da execução)',
  motivos_desabilitacao   STRING    COMMENT 'JSON {regra: motivo}',
  vinculos_analisados     INT,
  achados_novos           INT,
  achados_reincidentes    INT,
  achados_resolvidos      INT,
  mensagem_erro           STRING,
  CONSTRAINT vd_execucoes_diagnostico_pk PRIMARY KEY (execucao_id),
  CONSTRAINT vd_execucoes_obj_fk FOREIGN KEY (objetivo_id) REFERENCES vd_objetivos (objetivo_id)
) COMMENT 'Valor dos Dados — execuções do diagnóstico'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- Achados: UM registro por (objetivo, vínculo, regra). Reexecuções atualizam
-- este registro; cada execução grava uma linha em vd_achados_ocorrencias.
CREATE TABLE IF NOT EXISTS vd_achados (
  achado_id               STRING    NOT NULL,
  chave_natural           STRING    NOT NULL COMMENT 'objetivo_id|vinculo_id|regra_codigo',
  objetivo_id             STRING    NOT NULL,
  processo_id             STRING,
  vinculo_id              STRING    NOT NULL,
  regra_codigo            STRING    NOT NULL,
  versao_regras           STRING    NOT NULL,
  natureza                STRING    NOT NULL,
  evidencia_fato          STRING    NOT NULL,
  valor_observado         STRING,
  criterio                STRING,
  situacao                STRING    NOT NULL COMMENT 'aberto | resolvido | cancelado',
  primeira_execucao_id    STRING    NOT NULL,
  ultima_execucao_id      STRING    NOT NULL,
  primeira_deteccao_em    TIMESTAMP NOT NULL,
  ultima_deteccao_em      TIMESTAMP NOT NULL,
  resolvido_em            TIMESTAMP,
  origem                  STRING    NOT NULL,
  status_validacao        STRING    NOT NULL,
  validado_por            STRING,
  validado_em             TIMESTAMP,
  justificativa_validacao STRING,
  criado_por              STRING    NOT NULL,
  criado_em               TIMESTAMP NOT NULL,
  atualizado_por          STRING,
  atualizado_em           TIMESTAMP,
  versao                  INT       NOT NULL,
  CONSTRAINT vd_achados_pk PRIMARY KEY (achado_id),
  CONSTRAINT vd_achados_obj_fk FOREIGN KEY (objetivo_id) REFERENCES vd_objetivos (objetivo_id),
  CONSTRAINT vd_achados_vinc_fk FOREIGN KEY (vinculo_id) REFERENCES vd_vinculos (vinculo_id),
  CONSTRAINT vd_achados_exec_fk FOREIGN KEY (primeira_execucao_id) REFERENCES vd_execucoes_diagnostico (execucao_id)
) COMMENT 'Valor dos Dados — achados (estado atual por objetivo, vínculo e regra)'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- Resultado de cada regra em cada execução (preserva a série histórica)
CREATE TABLE IF NOT EXISTS vd_achados_ocorrencias (
  ocorrencia_id           STRING    NOT NULL,
  chave_natural           STRING    NOT NULL COMMENT 'execucao_id|vinculo_id|regra_codigo',
  execucao_id             STRING    NOT NULL,
  vinculo_id              STRING    NOT NULL,
  regra_codigo            STRING    NOT NULL,
  achado_id               STRING    COMMENT 'Nulo quando a regra não disparou e não havia achado',
  resultado               STRING    NOT NULL COMMENT 'disparou | nao_disparou | nao_avaliada',
  natureza                STRING,
  valor_observado         STRING,
  motivo_nao_avaliada     STRING,
  registrado_em           TIMESTAMP NOT NULL,
  CONSTRAINT vd_achados_ocorrencias_pk PRIMARY KEY (ocorrencia_id),
  CONSTRAINT vd_ocorr_exec_fk FOREIGN KEY (execucao_id) REFERENCES vd_execucoes_diagnostico (execucao_id)
) COMMENT 'Valor dos Dados — resultado de cada regra em cada execução (somente inclusão)'
TBLPROPERTIES ('delta.appendOnly' = 'true', 'delta.enableChangeDataFeed' = 'true');

CREATE TABLE IF NOT EXISTS vd_intervencoes (
  intervencao_id            STRING    NOT NULL,
  chave_natural             STRING    NOT NULL COMMENT 'achado_id|sequencia',
  codigo                    STRING    NOT NULL,
  achado_id                 STRING    NOT NULL,
  sequencia                 INT       NOT NULL COMMENT '1 na abertura; reabertura cria sequência + 1',
  intervencao_anterior_id   STRING,
  objetivo_id               STRING    NOT NULL COMMENT 'Igual ao objetivo do achado (regra C06)',
  titulo                    STRING    NOT NULL,
  recomendacao              STRING    NOT NULL,
  tipo_afirmacao            STRING    NOT NULL,
  causa_provavel            STRING,
  responsavel               STRING    NOT NULL,
  area                      STRING    NOT NULL,
  -- Entradas da priorização (gravadas para reprodutibilidade)
  versao_modelo             STRING    NOT NULL,
  entrada_prioridade_obj    STRING    NOT NULL COMMENT 'alta | media | baixa (do objetivo)',
  entrada_posicao_ativo     STRING    NOT NULL COMMENT 'fonte | intermediario | saida | nao_aplicavel (do vínculo)',
  entrada_tipo_achado       STRING    NOT NULL COMMENT 'Natureza do achado',
  abrangencia_ativos        INT       COMMENT 'Nulo = não determinada',
  abrangencia_base          STRING    COMMENT 'JSON com os ativos a jusante e a data da linhagem consultada',
  entrada_abrangencia       STRING    NOT NULL COMMENT '0 | 1-2 | 3-5 | 6+ | nao_determinada',
  esforco                   STRING    NOT NULL,
  -- Pontos (derivados do modelo; recalculáveis por 03)
  pts_prioridade_objetivo   INT       NOT NULL,
  pts_posicao_ativo         INT       NOT NULL,
  pts_tipo_achado           INT       NOT NULL,
  pts_abrangencia           INT       NOT NULL,
  pts_esforco               INT       NOT NULL,
  pontuacao_total           INT       NOT NULL,
  prioridade                STRING    NOT NULL,
  criterio_conclusao        STRING    NOT NULL,
  status                    STRING    NOT NULL,
  aberta_em                 TIMESTAMP NOT NULL,
  prazo                     DATE,
  aprovado_por              STRING,
  aprovado_em               TIMESTAMP,
  concluido_por             STRING,
  concluida_em              TIMESTAMP,
  justificativa_cancelamento STRING,
  origem                    STRING    NOT NULL,
  criado_por                STRING    NOT NULL,
  criado_em                 TIMESTAMP NOT NULL,
  atualizado_por            STRING,
  atualizado_em             TIMESTAMP,
  versao                    INT       NOT NULL,
  CONSTRAINT vd_intervencoes_pk PRIMARY KEY (intervencao_id),
  CONSTRAINT vd_intervencoes_achado_fk FOREIGN KEY (achado_id) REFERENCES vd_achados (achado_id),
  CONSTRAINT vd_intervencoes_obj_fk FOREIGN KEY (objetivo_id) REFERENCES vd_objetivos (objetivo_id)
) COMMENT 'Valor dos Dados — intervenções'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

CREATE TABLE IF NOT EXISTS vd_medicoes (
  medicao_id              STRING        NOT NULL,
  chave_natural           STRING        NOT NULL COMMENT 'indicador_id|tipo|data_referencia',
  indicador_id            STRING        NOT NULL,
  objetivo_id             STRING        NOT NULL COMMENT 'Igual ao do indicador (regra C07)',
  tipo                    STRING        NOT NULL,
  data_referencia         DATE          NOT NULL,
  valor                   DECIMAL(18,4) NOT NULL,
  metodo                  STRING        NOT NULL,
  intervencao_id          STRING        COMMENT 'Se informada, do mesmo objetivo (regra C07)',
  status                  STRING        NOT NULL,
  origem                  STRING        NOT NULL,
  status_validacao        STRING        NOT NULL,
  validado_por            STRING,
  validado_em             TIMESTAMP,
  justificativa_validacao STRING,
  criado_por              STRING        NOT NULL,
  criado_em               TIMESTAMP     NOT NULL,
  atualizado_por          STRING,
  atualizado_em           TIMESTAMP,
  versao                  INT           NOT NULL,
  CONSTRAINT vd_medicoes_pk PRIMARY KEY (medicao_id),
  CONSTRAINT vd_medicoes_ind_fk FOREIGN KEY (indicador_id) REFERENCES vd_indicadores (indicador_id),
  CONSTRAINT vd_medicoes_obj_fk FOREIGN KEY (objetivo_id) REFERENCES vd_objetivos (objetivo_id),
  CONSTRAINT vd_medicoes_int_fk FOREIGN KEY (intervencao_id) REFERENCES vd_intervencoes (intervencao_id)
) COMMENT 'Valor dos Dados — medições informadas pela organização'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- Fórmulas (versão F1), aplicadas na gravação condicionada e recalculadas em 03:
--   melhoria      = valor_antes - valor_depois   se sentido_melhora = 'reduzir'
--                 = valor_depois - valor_antes   se sentido_melhora = 'aumentar'
--   melhoria_pct  = melhoria / ABS(valor_antes) * 100   (nula se valor_antes = 0)
--   valor_financeiro = melhoria * fator * custo_unitario
--       somente se existir conversão validada e vigente para a unidade do
--       indicador; indicadores com tipo_unidade = 'percentual' não são
--       convertidos (não há regra de conversão possível sem base absoluta).
--   Benefício só pode ser 'validado' com melhoria > 0.
CREATE TABLE IF NOT EXISTS vd_beneficios (
  beneficio_id            STRING        NOT NULL,
  chave_natural           STRING        NOT NULL COMMENT 'indicador_id|intervencao_id',
  objetivo_id             STRING        NOT NULL COMMENT 'Igual ao do indicador e da intervenção (regra C08)',
  indicador_id            STRING        NOT NULL,
  intervencao_id          STRING        NOT NULL,
  formula_versao          STRING        NOT NULL COMMENT 'F1',
  sentido_melhora         STRING        NOT NULL COMMENT 'Copiado do indicador no momento do cálculo',
  premissas               STRING        NOT NULL,
  valor_estimado          DECIMAL(18,4) COMMENT 'Melhoria esperada, na unidade do indicador (estágio estimado)',
  medicao_antes_id        STRING,
  medicao_depois_id       STRING,
  valor_antes             DECIMAL(18,4),
  valor_depois            DECIMAL(18,4),
  melhoria                DECIMAL(18,4),
  melhoria_pct            DECIMAL(9,4),
  conversao_id            STRING,
  moeda                   STRING,
  valor_financeiro        DECIMAL(18,2),
  metodo_calculo          STRING        NOT NULL COMMENT 'Descrição legível do cálculo aplicado',
  estagio                 STRING        NOT NULL,
  ressalva_causalidade    STRING        NOT NULL,
  validado_por            STRING,
  validado_em             TIMESTAMP,
  justificativa_validacao STRING,
  origem                  STRING        NOT NULL,
  criado_por              STRING        NOT NULL,
  criado_em               TIMESTAMP     NOT NULL,
  atualizado_por          STRING,
  atualizado_em           TIMESTAMP,
  versao                  INT           NOT NULL,
  CONSTRAINT vd_beneficios_pk PRIMARY KEY (beneficio_id),
  CONSTRAINT vd_beneficios_obj_fk FOREIGN KEY (objetivo_id) REFERENCES vd_objetivos (objetivo_id),
  CONSTRAINT vd_beneficios_ind_fk FOREIGN KEY (indicador_id) REFERENCES vd_indicadores (indicador_id),
  CONSTRAINT vd_beneficios_int_fk FOREIGN KEY (intervencao_id) REFERENCES vd_intervencoes (intervencao_id),
  CONSTRAINT vd_beneficios_antes_fk FOREIGN KEY (medicao_antes_id) REFERENCES vd_medicoes (medicao_id),
  CONSTRAINT vd_beneficios_depois_fk FOREIGN KEY (medicao_depois_id) REFERENCES vd_medicoes (medicao_id),
  CONSTRAINT vd_beneficios_conv_fk FOREIGN KEY (conversao_id) REFERENCES vd_conversoes_financeiras (conversao_id)
) COMMENT 'Valor dos Dados — benefícios'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- Evidências e histórico: imutáveis (delta.appendOnly bloqueia UPDATE e
-- DELETE para qualquer usuário; só o dono da tabela poderia remover a
-- propriedade — ver permissões em 04).
CREATE TABLE IF NOT EXISTS vd_evidencias (
  evidencia_id    STRING    NOT NULL,
  chave_natural   STRING    NOT NULL COMMENT 'entidade_tipo|entidade_id|sha2(conteudo,256)',
  entidade_tipo   STRING    NOT NULL,
  entidade_id     STRING    NOT NULL,
  tipo            STRING    NOT NULL,
  descricao       STRING    NOT NULL,
  conteudo        STRING    NOT NULL,
  origem          STRING    NOT NULL,
  registrado_por  STRING    NOT NULL,
  perfil          STRING    NOT NULL,
  registrado_em   TIMESTAMP NOT NULL,
  CONSTRAINT vd_evidencias_pk PRIMARY KEY (evidencia_id)
) COMMENT 'Valor dos Dados — evidências (imutável)'
TBLPROPERTIES ('delta.appendOnly' = 'true', 'delta.enableChangeDataFeed' = 'true');

CREATE TABLE IF NOT EXISTS vd_historico (
  historico_id      STRING    NOT NULL,
  chave_natural     STRING    NOT NULL COMMENT 'entidade_tipo|entidade_id|versao_entidade|acao',
  entidade_tipo     STRING    NOT NULL,
  entidade_id       STRING    NOT NULL,
  acao              STRING    NOT NULL,
  versao_entidade   INT       NOT NULL,
  status_anterior   STRING,
  status_novo       STRING,
  campos_alterados  STRING,
  comentario        STRING,
  evidencia_id      STRING,
  executado_por     STRING    NOT NULL,
  perfil            STRING    NOT NULL,
  executado_em      TIMESTAMP NOT NULL,
  CONSTRAINT vd_historico_pk PRIMARY KEY (historico_id)
) COMMENT 'Valor dos Dados — trilha de auditoria (imutável)'
TBLPROPERTIES ('delta.appendOnly' = 'true', 'delta.enableChangeDataFeed' = 'true');


-- ════════════════════════════════════════════════════════════════════
-- 3. RESTRIÇÕES CHECK (impostas) — idempotentes
-- ════════════════════════════════════════════════════════════════════
-- Bloco padrão
ALTER TABLE vd_objetivos   DROP CONSTRAINT IF EXISTS ck_padrao;
ALTER TABLE vd_objetivos   ADD  CONSTRAINT ck_padrao CHECK (origem IN ('manual','importacao') AND status_validacao IN ('pendente','validado','rejeitado') AND (status_validacao = 'pendente' OR (validado_por IS NOT NULL AND validado_em IS NOT NULL)) AND (status_validacao <> 'rejeitado' OR justificativa_validacao IS NOT NULL) AND versao >= 1 AND (atualizado_em IS NULL OR atualizado_em >= criado_em));
ALTER TABLE vd_processos   DROP CONSTRAINT IF EXISTS ck_padrao;
ALTER TABLE vd_processos   ADD  CONSTRAINT ck_padrao CHECK (origem IN ('manual','importacao') AND status_validacao IN ('pendente','validado','rejeitado') AND (status_validacao = 'pendente' OR (validado_por IS NOT NULL AND validado_em IS NOT NULL)) AND (status_validacao <> 'rejeitado' OR justificativa_validacao IS NOT NULL) AND versao >= 1 AND (atualizado_em IS NULL OR atualizado_em >= criado_em));
ALTER TABLE vd_indicadores DROP CONSTRAINT IF EXISTS ck_padrao;
ALTER TABLE vd_indicadores ADD  CONSTRAINT ck_padrao CHECK (origem IN ('manual','importacao') AND status_validacao IN ('pendente','validado','rejeitado') AND (status_validacao = 'pendente' OR (validado_por IS NOT NULL AND validado_em IS NOT NULL)) AND (status_validacao <> 'rejeitado' OR justificativa_validacao IS NOT NULL) AND versao >= 1 AND (atualizado_em IS NULL OR atualizado_em >= criado_em));
ALTER TABLE vd_vinculos    DROP CONSTRAINT IF EXISTS ck_padrao;
ALTER TABLE vd_vinculos    ADD  CONSTRAINT ck_padrao CHECK (origem IN ('manual','metadado','sugestao_ia') AND status_validacao IN ('pendente','validado','rejeitado') AND (status_validacao = 'pendente' OR (validado_por IS NOT NULL AND validado_em IS NOT NULL)) AND (status_validacao <> 'rejeitado' OR justificativa_validacao IS NOT NULL) AND versao >= 1 AND (atualizado_em IS NULL OR atualizado_em >= criado_em));
ALTER TABLE vd_achados     DROP CONSTRAINT IF EXISTS ck_padrao;
ALTER TABLE vd_achados     ADD  CONSTRAINT ck_padrao CHECK (origem IN ('calculado','manual') AND status_validacao IN ('pendente','validado','rejeitado') AND (status_validacao = 'pendente' OR (validado_por IS NOT NULL AND validado_em IS NOT NULL)) AND (status_validacao <> 'rejeitado' OR justificativa_validacao IS NOT NULL) AND versao >= 1 AND (atualizado_em IS NULL OR atualizado_em >= criado_em));
ALTER TABLE vd_medicoes    DROP CONSTRAINT IF EXISTS ck_padrao;
ALTER TABLE vd_medicoes    ADD  CONSTRAINT ck_padrao CHECK (origem IN ('manual','importacao') AND status_validacao IN ('pendente','validado','rejeitado') AND (status_validacao = 'pendente' OR (validado_por IS NOT NULL AND validado_em IS NOT NULL)) AND (status_validacao <> 'rejeitado' OR justificativa_validacao IS NOT NULL) AND versao >= 1 AND (atualizado_em IS NULL OR atualizado_em >= criado_em));
ALTER TABLE vd_conversoes_financeiras DROP CONSTRAINT IF EXISTS ck_padrao;
ALTER TABLE vd_conversoes_financeiras ADD  CONSTRAINT ck_padrao CHECK (origem IN ('manual','importacao') AND status_validacao IN ('pendente','validado','rejeitado') AND (status_validacao = 'pendente' OR (validado_por IS NOT NULL AND validado_em IS NOT NULL)) AND (status_validacao <> 'rejeitado' OR justificativa_validacao IS NOT NULL) AND versao >= 1 AND fator > 0 AND custo_unitario >= 0 AND length(moeda) = 3 AND (vigencia_fim IS NULL OR vigencia_fim >= vigencia_inicio));

-- Domínios de valores e regras internas de cada linha
ALTER TABLE vd_objetivos   DROP CONSTRAINT IF EXISTS ck_dominio;
ALTER TABLE vd_objetivos   ADD  CONSTRAINT ck_dominio CHECK (tipo IN ('objetivo','desafio') AND prioridade IN ('alta','media','baixa') AND status IN ('rascunho','ativo','atingido','nao_atingido','cancelado') AND (limite_qualidade_pct IS NULL OR limite_qualidade_pct BETWEEN 0 AND 100) AND (data_prevista IS NULL OR data_inicio IS NULL OR data_prevista >= data_inicio));
ALTER TABLE vd_processos   DROP CONSTRAINT IF EXISTS ck_dominio;
ALTER TABLE vd_processos   ADD  CONSTRAINT ck_dominio CHECK (criticidade IN ('alta','media','baixa') AND status IN ('ativo','cancelado'));
ALTER TABLE vd_indicadores DROP CONSTRAINT IF EXISTS ck_dominio;
ALTER TABLE vd_indicadores ADD  CONSTRAINT ck_dominio CHECK (papel IN ('principal','complementar') AND sentido_melhora IN ('reduzir','aumentar') AND tipo_unidade IN ('tempo','quantidade','percentual','monetario') AND status IN ('ativo','cancelado'));
ALTER TABLE vd_vinculos    DROP CONSTRAINT IF EXISTS ck_dominio;
ALTER TABLE vd_vinculos    ADD  CONSTRAINT ck_dominio CHECK (
  origem_tipo IN ('objetivo','processo') AND status IN ('ativo','cancelado')
  AND (origem_tipo <> 'objetivo' OR origem_id = objetivo_id)
  AND ref_tipo IN ('ativo','produto','termo_glossario','regra_negocio','dominio','indicador','responsavel')
  AND (  (ref_tipo = 'ativo' AND ref_schema IS NOT NULL AND ref_nome IS NOT NULL AND ref_id IS NULL AND papel_no_processo IN ('fonte','intermediario','saida'))
      OR (ref_tipo IN ('produto','termo_glossario','regra_negocio','indicador') AND ref_id IS NOT NULL AND ref_schema IS NULL)
      OR (ref_tipo IN ('dominio','responsavel') AND ref_nome IS NOT NULL AND ref_id IS NULL AND ref_schema IS NULL))
  AND (ref_tipo = 'ativo' OR papel_no_processo IS NULL)
  AND (origem <> 'metadado' OR evidencia_base IS NOT NULL)
  AND (origem <> 'sugestao_ia' OR status_validacao <> 'validado' OR validado_por IS NOT NULL));
ALTER TABLE vd_execucoes_diagnostico DROP CONSTRAINT IF EXISTS ck_dominio;
ALTER TABLE vd_execucoes_diagnostico ADD  CONSTRAINT ck_dominio CHECK (
  status IN ('em_execucao','concluida','falhou') AND perfil IN ('curador','aprovador','processo')
  AND (status = 'em_execucao' OR finalizado_em IS NOT NULL)
  AND (finalizado_em IS NULL OR finalizado_em >= iniciado_em)
  AND (status <> 'falhou' OR mensagem_erro IS NOT NULL)
  AND (status <> 'concluida' OR (vinculos_analisados IS NOT NULL AND achados_novos IS NOT NULL AND achados_reincidentes IS NOT NULL AND achados_resolvidos IS NOT NULL)));
ALTER TABLE vd_achados     DROP CONSTRAINT IF EXISTS ck_dominio;
ALTER TABLE vd_achados     ADD  CONSTRAINT ck_dominio CHECK (
  natureza IN ('nao_cadastrado','nao_identificado','nao_conforme','nao_aplicavel')
  AND situacao IN ('aberto','resolvido','cancelado')
  AND (natureza <> 'nao_conforme' OR (criterio IS NOT NULL AND valor_observado IS NOT NULL))
  AND (natureza <> 'nao_aplicavel' OR (origem = 'manual' AND justificativa_validacao IS NOT NULL))
  AND (situacao <> 'resolvido' OR resolvido_em IS NOT NULL)
  AND ultima_deteccao_em >= primeira_deteccao_em);
ALTER TABLE vd_achados_ocorrencias DROP CONSTRAINT IF EXISTS ck_dominio;
ALTER TABLE vd_achados_ocorrencias ADD  CONSTRAINT ck_dominio CHECK (
  resultado IN ('disparou','nao_disparou','nao_avaliada')
  AND (resultado <> 'disparou' OR (achado_id IS NOT NULL AND natureza IS NOT NULL))
  AND (resultado <> 'nao_avaliada' OR motivo_nao_avaliada IS NOT NULL));
ALTER TABLE vd_intervencoes DROP CONSTRAINT IF EXISTS ck_dominio;
ALTER TABLE vd_intervencoes ADD  CONSTRAINT ck_dominio CHECK (
  status IN ('identificada','em_analise','aprovada','planejada','em_execucao','em_validacao','concluida','cancelada')
  AND prioridade IN ('critica','alta','media','baixa') AND tipo_afirmacao IN ('fato','hipotese')
  AND origem IN ('manual','calculado') AND versao >= 1 AND sequencia >= 1
  AND (sequencia = 1 OR intervencao_anterior_id IS NOT NULL)
  AND entrada_prioridade_obj IN ('alta','media','baixa')
  AND entrada_posicao_ativo IN ('fonte','intermediario','saida','nao_aplicavel')
  AND entrada_tipo_achado IN ('nao_cadastrado','nao_identificado','nao_conforme')
  AND entrada_abrangencia IN ('0','1-2','3-5','6+','nao_determinada')
  AND (entrada_abrangencia = 'nao_determinada') = (abrangencia_ativos IS NULL)
  AND esforco IN ('baixo','medio','alto','nao_informado')
  AND pontuacao_total = pts_prioridade_objetivo + pts_posicao_ativo + pts_tipo_achado + pts_abrangencia + pts_esforco
  AND (tipo_afirmacao = 'hipotese' OR causa_provavel IS NULL OR length(causa_provavel) > 0));
ALTER TABLE vd_intervencoes DROP CONSTRAINT IF EXISTS ck_estado;
ALTER TABLE vd_intervencoes ADD  CONSTRAINT ck_estado CHECK (
      (status IN ('identificada','em_analise','cancelada') OR (aprovado_por IS NOT NULL AND aprovado_em IS NOT NULL))
  AND (status IN ('identificada','em_analise','aprovada','cancelada') OR prazo IS NOT NULL)
  AND (status <> 'concluida' OR (concluido_por IS NOT NULL AND concluida_em IS NOT NULL))
  AND (status = 'concluida' OR concluida_em IS NULL)
  AND (status <> 'cancelada' OR justificativa_cancelamento IS NOT NULL));
ALTER TABLE vd_medicoes    DROP CONSTRAINT IF EXISTS ck_dominio;
ALTER TABLE vd_medicoes    ADD  CONSTRAINT ck_dominio CHECK (tipo IN ('linha_base','acompanhamento') AND status IN ('ativo','cancelado'));
ALTER TABLE vd_beneficios  DROP CONSTRAINT IF EXISTS ck_dominio;
ALTER TABLE vd_beneficios  ADD  CONSTRAINT ck_dominio CHECK (
  estagio IN ('estimado','em_validacao','validado','recusado') AND origem IN ('calculado','manual') AND versao >= 1
  AND formula_versao = 'F1' AND sentido_melhora IN ('reduzir','aumentar')
  AND (estagio IN ('estimado','recusado') OR (medicao_antes_id IS NOT NULL AND medicao_depois_id IS NOT NULL
       AND valor_antes IS NOT NULL AND valor_depois IS NOT NULL AND melhoria IS NOT NULL))
  AND (melhoria IS NULL OR melhoria = CASE sentido_melhora WHEN 'reduzir' THEN valor_antes - valor_depois ELSE valor_depois - valor_antes END)
  AND (melhoria_pct IS NULL OR (valor_antes <> 0 AND abs(melhoria_pct - melhoria / abs(valor_antes) * 100) < 0.0001))
  AND (estagio <> 'validado' OR (melhoria > 0 AND validado_por IS NOT NULL AND validado_em IS NOT NULL))
  AND (estagio <> 'recusado' OR justificativa_validacao IS NOT NULL)
  AND ((valor_financeiro IS NULL) = (conversao_id IS NULL))
  AND (valor_financeiro IS NULL OR (moeda IS NOT NULL AND melhoria IS NOT NULL)));
ALTER TABLE vd_evidencias  DROP CONSTRAINT IF EXISTS ck_dominio;
ALTER TABLE vd_evidencias  ADD  CONSTRAINT ck_dominio CHECK (
  entidade_tipo IN ('objetivo','processo','indicador','vinculo','achado','intervencao','medicao','beneficio','conversao')
  AND tipo IN ('link','consulta_sql','texto') AND origem IN ('manual','calculado','importacao')
  AND perfil IN ('consultante','curador','aprovador','processo') AND length(trim(conteudo)) > 0);
ALTER TABLE vd_historico   DROP CONSTRAINT IF EXISTS ck_dominio;
ALTER TABLE vd_historico   ADD  CONSTRAINT ck_dominio CHECK (
  entidade_tipo IN ('objetivo','processo','indicador','vinculo','execucao','achado','intervencao','medicao','beneficio','conversao','evidencia')
  AND acao IN ('criacao','edicao','transicao','validacao','evidencia','cancelamento','reincidencia','resolucao')
  AND perfil IN ('consultante','curador','aprovador','processo') AND versao_entidade >= 1);
ALTER TABLE vd_modelo_priorizacao DROP CONSTRAINT IF EXISTS ck_dominio;
ALTER TABLE vd_modelo_priorizacao ADD  CONSTRAINT ck_dominio CHECK (criterio IN ('prioridade_objetivo','posicao_ativo','tipo_achado','abrangencia','esforco') AND peso >= 1 AND pontos BETWEEN -3 AND 3 AND situacao IN ('aprovado','pendente'));
ALTER TABLE vd_faixas_prioridade DROP CONSTRAINT IF EXISTS ck_dominio;
ALTER TABLE vd_faixas_prioridade ADD  CONSTRAINT ck_dominio CHECK (prioridade IN ('critica','alta','media','baixa') AND pontuacao_max >= pontuacao_min);
ALTER TABLE vd_regras_diagnostico DROP CONSTRAINT IF EXISTS ck_dominio;
ALTER TABLE vd_regras_diagnostico ADD  CONSTRAINT ck_dominio CHECK (natureza_padrao IN ('nao_cadastrado','nao_identificado','nao_conforme') AND aplica_a IN ('ativo','produto','vinculo'));


-- ════════════════════════════════════════════════════════════════════
-- 4. REGISTRO DA VERSÃO (idempotente)
-- ════════════════════════════════════════════════════════════════════
INSERT INTO vd_controle_versao
SELECT 'v3', 'Estruturas do piloto Valor dos Dados (auditoria técnica incorporada)', current_user(), current_timestamp()
FROM (SELECT 1) AS d
WHERE NOT EXISTS (SELECT 1 FROM vd_controle_versao WHERE versao = 'v3');
