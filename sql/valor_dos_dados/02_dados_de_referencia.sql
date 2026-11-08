-- ════════════════════════════════════════════════════════════════════
-- GOVERNANTES · Valor dos Dados · v3
-- 02 — Dados de referência (configuração versionada, não são dados de negócio)
--
-- Conteúdo: catálogo de regras R1, modelo de priorização P1, faixas P1 e
-- máquina de estados das intervenções.
-- Idempotência: MERGE apenas com INSERT para linhas ausentes. Uma versão
-- publicada nunca é sobrescrita: se o conteúdo gravado divergir do
-- esperado, a verificação ao final ABORTA (mudança exige nova versão).
-- ════════════════════════════════════════════════════════════════════

DECLARE OR REPLACE VARIABLE vd_catalogo STRING DEFAULT 'workspace';
DECLARE OR REPLACE VARIABLE vd_schema   STRING DEFAULT 'meridian_governanca';
USE CATALOG IDENTIFIER(vd_catalogo);
USE SCHEMA  IDENTIFIER(vd_schema);

-- ── 1. Regras do diagnóstico — versão R1 ─────────────────────────────
CREATE OR REPLACE TEMPORARY VIEW vd_ref_regras_r1 AS
SELECT * FROM VALUES
 ('DG-01','R1','Ativo sem Owner','O ativo não tem Data Owner cadastrado.','nao_cadastrado','tabelas_metadata.data_owner','Valor nulo ou vazio','ativo',CAST(NULL AS STRING),true),
 ('DG-02','R1','Ativo sem Steward','O ativo não tem Data Steward cadastrado.','nao_cadastrado','tabelas_metadata.data_steward','Valor nulo ou vazio','ativo',NULL,true),
 ('DG-03','R1','Ativo sem definição de negócio','Nenhum termo do glossário vinculado ao ativo.','nao_cadastrado','glossary_asset_link','Nenhuma linha para o ativo; se o vínculo só tiver table_name e o nome existir em mais de um schema, resultado = nao_identificado','ativo',NULL,true),
 ('DG-04','R1','Ativo sem classificação','O ativo não tem classificação de informação.','nao_cadastrado','tabelas_metadata.classificacao','Valor nulo ou vazio','ativo','tabelas_metadata.classificacao',true),
 ('DG-05','R1','Ativo sem avaliação de qualidade','Não há registro de avaliação de qualidade para o ativo na plataforma.','nao_identificado','gd_quality_dimensions','Nenhuma linha para schema_name + table_name','ativo',NULL,true),
 ('DG-06','R1','Qualidade abaixo do limite do objetivo','O score final de qualidade está abaixo do limite definido no objetivo.','nao_conforme','gd_quality_dimensions.score_final','score_final < vd_objetivos.limite_qualidade_pct (só avaliada se o limite estiver definido)','ativo',NULL,true),
 ('DG-07','R1','Linhagem não registrada','O ativo não aparece como destino em nenhuma relação de linhagem.','nao_identificado','linhagem_ativos.destino_schema/destino_tabela','Nenhuma linha como destino; não avaliada para ativos com papel fonte','ativo',NULL,true),
 ('DG-08','R1','Produto sem documentação','Produto de dados sem descrição/finalidade ou sem responsável.','nao_cadastrado','produtos_dados','Colunas confirmadas em 00, passo 3; desabilitada se nenhuma existir','produto','produtos_dados.(descricao|finalidade) e (owner|data_owner)',true),
 ('DG-09','R1','Vínculo para objeto inexistente','O vínculo aponta para um objeto que não existe no catálogo atual.','nao_identificado','vd_vinculos x tabelas de origem','Referência não encontrada pela chave do tipo','vinculo',NULL,true)
AS t(regra_codigo, versao_regras, nome, descricao, natureza_padrao, fonte, criterio, aplica_a, dependencia, vigente);

MERGE INTO vd_regras_diagnostico t USING vd_ref_regras_r1 s
ON t.regra_codigo = s.regra_codigo AND t.versao_regras = s.versao_regras
WHEN NOT MATCHED THEN INSERT *;

-- ── 2. Modelo de priorização — versão P1 ─────────────────────────────
--    pontuacao_total = Σ (pontos × peso). Em P1 todos os pesos = 1.
--    Mínimo possível = 2; máximo = 13.
CREATE OR REPLACE TEMPORARY VIEW vd_ref_modelo_p1 AS
SELECT * FROM VALUES
 ('P1','prioridade_objetivo','alta',3,1,'Prioridade do objetivo de negócio'),
 ('P1','prioridade_objetivo','media',2,1,'Prioridade do objetivo de negócio'),
 ('P1','prioridade_objetivo','baixa',1,1,'Prioridade do objetivo de negócio'),
 ('P1','posicao_ativo','saida',3,1,'Ativo entrega o resultado do processo'),
 ('P1','posicao_ativo','intermediario',2,1,'Ativo de transformação'),
 ('P1','posicao_ativo','fonte',1,1,'Ativo de origem'),
 ('P1','posicao_ativo','nao_aplicavel',2,1,'Achado sobre produto de dados (sem posição de ativo); valor neutro — DECISÃO PENDENTE'),
 ('P1','tipo_achado','nao_conforme',3,1,'Informação existe e viola critério'),
 ('P1','tipo_achado','nao_cadastrado',2,1,'Informação ausente na plataforma'),
 ('P1','tipo_achado','nao_identificado',1,1,'Plataforma não consegue verificar'),
 ('P1','abrangencia','0',0,1,'Nenhum ativo a jusante na linhagem'),
 ('P1','abrangencia','1-2',1,1,'1 a 2 ativos a jusante'),
 ('P1','abrangencia','3-5',2,1,'3 a 5 ativos a jusante'),
 ('P1','abrangencia','6+',3,1,'6 ou mais ativos a jusante'),
 ('P1','abrangencia','nao_determinada',0,1,'Sem linhagem: neutro, exibido como não determinada'),
 ('P1','esforco','baixo',1,1,'Esforço informado pelo gestor'),
 ('P1','esforco','medio',0,1,'Esforço informado pelo gestor'),
 ('P1','esforco','alto',-1,1,'Esforço informado pelo gestor'),
 ('P1','esforco','nao_informado',0,1,'Neutro, exibido como não informado')
AS t(versao_modelo, criterio, entrada, pontos, peso, descricao);

MERGE INTO vd_modelo_priorizacao t USING vd_ref_modelo_p1 s
ON t.versao_modelo = s.versao_modelo AND t.criterio = s.criterio AND t.entrada = s.entrada
WHEN NOT MATCHED THEN INSERT *;

CREATE OR REPLACE TEMPORARY VIEW vd_ref_faixas_p1 AS
SELECT * FROM VALUES
 ('P1','critica',10,99), ('P1','alta',7,9), ('P1','media',4,6), ('P1','baixa',-99,3)
AS t(versao_modelo, prioridade, pontuacao_min, pontuacao_max);

MERGE INTO vd_faixas_prioridade t USING vd_ref_faixas_p1 s
ON t.versao_modelo = s.versao_modelo AND t.prioridade = s.prioridade
WHEN NOT MATCHED THEN INSERT *;

-- ── 3. Máquina de estados das intervenções ──────────────────────────
CREATE OR REPLACE TEMPORARY VIEW vd_ref_transicoes AS
SELECT * FROM VALUES
 ('identificada','em_analise','curador,aprovador','—'),
 ('em_analise','aprovada','aprovador','recomendacao e criterio_conclusao preenchidos; grava aprovado_por/em'),
 ('em_analise','identificada','curador,aprovador','comentario obrigatório (devolução)'),
 ('aprovada','planejada','curador,aprovador,responsavel','responsavel e prazo preenchidos'),
 ('planejada','em_execucao','responsavel','—'),
 ('em_execucao','planejada','responsavel','comentario obrigatório (replanejamento)'),
 ('em_execucao','em_validacao','responsavel','ao menos uma evidência registrada para a intervenção'),
 ('em_validacao','concluida','aprovador','confirmação do criterio_conclusao; grava concluido_por/em'),
 ('em_validacao','em_execucao','aprovador','comentario obrigatório (validação recusada)'),
 ('identificada','cancelada','curador,aprovador','justificativa_cancelamento'),
 ('em_analise','cancelada','curador,aprovador','justificativa_cancelamento'),
 ('aprovada','cancelada','curador,aprovador','justificativa_cancelamento'),
 ('planejada','cancelada','curador,aprovador','justificativa_cancelamento'),
 ('em_execucao','cancelada','curador,aprovador','justificativa_cancelamento'),
 ('em_validacao','cancelada','curador,aprovador','justificativa_cancelamento')
AS t(status_de, status_para, perfis, exige);

MERGE INTO vd_transicoes_intervencao t USING vd_ref_transicoes s
ON t.status_de = s.status_de AND t.status_para = s.status_para
WHEN NOT MATCHED THEN INSERT *;

-- ── 4. Verificação: o conteúdo gravado é exatamente o publicado ─────
SELECT CASE WHEN COUNT(*) = 0 THEN 'OK: regras R1 íntegras'
            ELSE raise_error('ABORTAR: catálogo de regras R1 divergente do publicado (criar nova versão)') END AS r1
FROM ((SELECT * FROM vd_ref_regras_r1 EXCEPT SELECT * FROM vd_regras_diagnostico WHERE versao_regras = 'R1')
      UNION ALL (SELECT * FROM vd_regras_diagnostico WHERE versao_regras = 'R1' EXCEPT SELECT * FROM vd_ref_regras_r1));

SELECT CASE WHEN COUNT(*) = 0 THEN 'OK: modelo P1 íntegro'
            ELSE raise_error('ABORTAR: modelo de priorização P1 divergente do publicado') END AS p1
FROM ((SELECT * FROM vd_ref_modelo_p1 EXCEPT SELECT * FROM vd_modelo_priorizacao WHERE versao_modelo = 'P1')
      UNION ALL (SELECT * FROM vd_modelo_priorizacao WHERE versao_modelo = 'P1' EXCEPT SELECT * FROM vd_ref_modelo_p1));

SELECT CASE WHEN COUNT(*) = 0 THEN 'OK: faixas P1 íntegras'
            ELSE raise_error('ABORTAR: faixas P1 divergentes do publicado') END AS faixas
FROM ((SELECT * FROM vd_ref_faixas_p1 EXCEPT SELECT * FROM vd_faixas_prioridade WHERE versao_modelo = 'P1')
      UNION ALL (SELECT * FROM vd_faixas_prioridade WHERE versao_modelo = 'P1' EXCEPT SELECT * FROM vd_ref_faixas_p1));

-- Faixas sem lacuna nem sobreposição no intervalo possível (2 a 13)
SELECT CASE WHEN COUNT_IF(n <> 1) = 0 THEN 'OK: cada pontuação de 2 a 13 cai em exatamente uma faixa'
            ELSE raise_error('ABORTAR: faixas P1 com lacuna ou sobreposição') END AS cobertura
FROM (SELECT p.pontos, COUNT(f.prioridade) AS n
      FROM (SELECT explode(sequence(2, 13)) AS pontos) p
      LEFT JOIN vd_faixas_prioridade f ON f.versao_modelo = 'P1' AND p.pontos BETWEEN f.pontuacao_min AND f.pontuacao_max
      GROUP BY p.pontos);

SELECT CASE WHEN COUNT(*) = 0 THEN 'OK: transições íntegras'
            ELSE raise_error('ABORTAR: máquina de estados divergente do publicado') END AS transicoes
FROM ((SELECT * FROM vd_ref_transicoes EXCEPT SELECT * FROM vd_transicoes_intervencao)
      UNION ALL (SELECT * FROM vd_transicoes_intervencao EXCEPT SELECT * FROM vd_ref_transicoes));
