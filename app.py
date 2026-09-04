-- ═══════════════════════════════════════════════════════
-- PLATAFORMA GOVERNANTES — SLA e Workflow de Atendimento
-- Execute no SQL Editor do Databricks
-- ═══════════════════════════════════════════════════════

-- 1. SLA por tipo de solicitação e etapa
CREATE TABLE IF NOT EXISTS meridian_governanca.gd_solicitacoes_sla (
  sla_id        STRING,
  tipo_sol      STRING,
  etapa         STRING,
  sla_horas     INT,
  responsavel   STRING,
  descricao     STRING
);

-- 2. Timeline de cada etapa de cada solicitação
CREATE TABLE IF NOT EXISTS meridian_governanca.gd_solicitacoes_timeline (
  timeline_id     STRING,
  solicitacao_id  STRING,
  tipo_sol        STRING,
  titulo          STRING,
  dominio         STRING,
  etapa           STRING,
  status_etapa    STRING,
  responsavel     STRING,
  iniciado_em     TIMESTAMP,
  concluido_em    TIMESTAMP,
  sla_horas       INT,
  horas_gastas    DOUBLE,
  dentro_sla      BOOLEAN,
  observacao      STRING
);

-- 3. Snapshot diário para indicadores de SLA
CREATE TABLE IF NOT EXISTS meridian_governanca.gd_sla_atendimento_snapshot (
  snapshot_id       STRING,
  data_snapshot     DATE,
  dominio           STRING,
  tipo_sol          STRING,
  total_abertas     INT,
  total_andamento   INT,
  total_resolvidas  INT,
  total_atrasadas   INT,
  tempo_medio_hrs   DOUBLE,
  taxa_sla_pct      DOUBLE,
  gargalo_etapa     STRING,
  gargalo_resp      STRING
);

-- ────────────────────────────────────────────────────────
-- POPULAR gd_solicitacoes_sla
-- ────────────────────────────────────────────────────────
INSERT INTO meridian_governanca.gd_solicitacoes_sla VALUES
('sla-01','acesso',    'owner',      48,  'Data Owner',     'Owner responde a solicitação de acesso em até 48h'),
('sla-02','acesso',    'governanca', 24,  'Governança',     'Governança valida e libera o acesso em até 24h'),
('sla-03','qualidade', 'owner',      72,  'Data Owner',     'Owner analisa problema de qualidade em até 72h'),
('sla-04','qualidade', 'governanca', 48,  'Governança',     'Governança classifica e encaminha a resolução em até 48h'),
('sla-05','qualidade', 'resolucao',  120, 'Equipe Técnica', 'Resolução técnica do problema em até 120h'),
('sla-06','conceito',  'owner',      120, 'Data Owner',     'Owner analisa sugestão de novo conceito em até 120h'),
('sla-07','conceito',  'aprovacao',  72,  'Aprovador',      'Aprovador homologa ou rejeita conceito em até 72h'),
('sla-08','regra',     'owner',      120, 'Data Owner',     'Owner analisa sugestão de nova regra em até 120h'),
('sla-09','regra',     'aprovacao',  72,  'Aprovador',      'Aprovador homologa ou rejeita regra em até 72h');

-- ────────────────────────────────────────────────────────
-- POPULAR gd_solicitacoes_timeline
-- ────────────────────────────────────────────────────────
INSERT INTO meridian_governanca.gd_solicitacoes_timeline VALUES
-- Solicitação 1: Acesso a fato_pix (RESOLVIDA no prazo)
('tl-001','sol-acc-001','acesso','Acesso a fato_pix','Pagamentos','abertura','concluido','consultante@meridian.com',
  timestamp('2026-06-01 09:00:00'),timestamp('2026-06-01 09:05:00'),0,0.08,true,'Solicitação registrada'),
('tl-002','sol-acc-001','acesso','Acesso a fato_pix','Pagamentos','owner','concluido','curador@meridian.com',
  timestamp('2026-06-01 09:05:00'),timestamp('2026-06-01 18:30:00'),48,9.4,true,'Owner aprovou o acesso'),
('tl-003','sol-acc-001','acesso','Acesso a fato_pix','Pagamentos','governanca','concluido','governanca@meridian.com',
  timestamp('2026-06-01 18:30:00'),timestamp('2026-06-02 10:00:00'),24,15.5,true,'Acesso liberado com permissão de leitura'),

-- Solicitação 2: Qualidade de dim_clientes (EM ANDAMENTO - atrasada)
('tl-004','sol-qua-001','qualidade','Problema de qualidade em dim_clientes','Clientes','abertura','concluido','consultante@meridian.com',
  timestamp('2026-06-10 14:00:00'),timestamp('2026-06-10 14:02:00'),0,0.03,true,'Problema reportado: campos nulos em email'),
('tl-005','sol-qua-001','qualidade','Problema de qualidade em dim_clientes','Clientes','owner','atrasado','curador@meridian.com',
  timestamp('2026-06-10 14:02:00'),null,72,110.0,false,'Aguardando análise do owner — prazo expirado'),
('tl-006','sol-qua-001','qualidade','Problema de qualidade em dim_clientes','Clientes','governanca','pendente','governanca@meridian.com',
  null,null,48,null,null,'Aguardando etapa anterior'),

-- Solicitação 3: Conceito "Taxa de Conversão" (RESOLVIDA no prazo)
('tl-007','sol-con-001','conceito','Sugestão: Taxa de Conversão','Vendas','abertura','concluido','consultante@meridian.com',
  timestamp('2026-06-05 10:00:00'),timestamp('2026-06-05 10:01:00'),0,0.02,true,'Sugestão registrada'),
('tl-008','sol-con-001','conceito','Sugestão: Taxa de Conversão','Vendas','owner','concluido','ana@meridian.com',
  timestamp('2026-06-05 10:01:00'),timestamp('2026-06-08 16:00:00'),120,77.9,true,'Owner aprovou — conceito válido para o domínio'),
('tl-009','sol-con-001','conceito','Sugestão: Taxa de Conversão','Vendas','aprovacao','concluido','ana@meridian.com',
  timestamp('2026-06-08 16:00:00'),timestamp('2026-06-09 11:00:00'),72,19.0,true,'Conceito homologado e publicado no glossário'),

-- Solicitação 4: Acesso a base_lgpd (ATRASADA em owner)
('tl-010','sol-acc-002','acesso','Acesso a base_lgpd','Compliance','abertura','concluido','consultante@meridian.com',
  timestamp('2026-06-12 08:00:00'),timestamp('2026-06-12 08:01:00'),0,0.02,true,'Solicitação registrada'),
('tl-011','sol-acc-002','acesso','Acesso a base_lgpd','Compliance','owner','atrasado','ana@meridian.com',
  timestamp('2026-06-12 08:01:00'),null,48,120.0,false,'Owner não respondeu — 120h sem retorno'),

-- Solicitação 5: Qualidade fato_pix (RESOLVIDA)
('tl-012','sol-qua-002','qualidade','Score baixo em fato_pix','Pagamentos','abertura','concluido','consultante@meridian.com',
  timestamp('2026-06-15 09:00:00'),timestamp('2026-06-15 09:02:00'),0,0.03,true,'Score de unicidade abaixo do esperado'),
('tl-013','sol-qua-002','qualidade','Score baixo em fato_pix','Pagamentos','owner','concluido','curador@meridian.com',
  timestamp('2026-06-15 09:02:00'),timestamp('2026-06-16 15:00:00'),72,29.9,true,'Owner identificou chave duplicada'),
('tl-014','sol-qua-002','qualidade','Score baixo em fato_pix','Pagamentos','governanca','concluido','governanca@meridian.com',
  timestamp('2026-06-16 15:00:00'),timestamp('2026-06-17 10:00:00'),48,19.0,true,'Pipeline corrigido e retestado'),
('tl-015','sol-qua-002','qualidade','Score baixo em fato_pix','Pagamentos','resolucao','concluido','curador@meridian.com',
  timestamp('2026-06-17 10:00:00'),timestamp('2026-06-18 14:00:00'),120,28.0,true,'Score normalizado para 96.3%');

-- ────────────────────────────────────────────────────────
-- POPULAR gd_sla_atendimento_snapshot
-- ────────────────────────────────────────────────────────
INSERT INTO meridian_governanca.gd_sla_atendimento_snapshot VALUES
-- Histórico geral últimos 6 meses
('sas-001',date_add(current_date(),-150),'Todos','Todos',12,8,3,4,72.5,66.7,'owner','ana@meridian.com'),
('sas-002',date_add(current_date(),-120),'Todos','Todos',18,10,6,5,65.2,72.2,'owner','curador@meridian.com'),
('sas-003',date_add(current_date(),-90), 'Todos','Todos',22,12,8,4,58.4,81.8,'governanca','governanca@meridian.com'),
('sas-004',date_add(current_date(),-60), 'Todos','Todos',25,14,10,3,48.7,88.0,'owner','ana@meridian.com'),
('sas-005',date_add(current_date(),-30), 'Todos','Todos',28,15,12,2,42.3,92.9,'owner','curador@meridian.com'),
('sas-006',current_date(),               'Todos','Todos',30,16,13,2,38.9,93.3,'owner','curador@meridian.com'),
-- Por domínio - hoje
('sas-007',current_date(),'Clientes','qualidade',  8,4,3,1,45.2,87.5,'owner','curador@meridian.com'),
('sas-008',current_date(),'Pagamentos','acesso',    6,3,3,0,32.1,100.0,'governanca','governanca@meridian.com'),
('sas-009',current_date(),'Credito','qualidade',    5,2,2,1,52.8,80.0,'owner','ana@meridian.com'),
('sas-010',current_date(),'Compliance','acesso',    4,3,1,2,88.4,50.0,'owner','ana@meridian.com'),
('sas-011',current_date(),'Clientes','conceito',    4,2,2,0,38.5,100.0,'aprovacao','ana@meridian.com'),
('sas-012',current_date(),'Credito','acesso',       3,2,1,0,28.7,100.0,'governanca','governanca@meridian.com');

-- ────────────────────────────────────────────────────────
-- VERIFICAÇÃO
-- ────────────────────────────────────────────────────────
SELECT 'gd_solicitacoes_sla'            AS tabela, COUNT(*) AS registros FROM meridian_governanca.gd_solicitacoes_sla
UNION ALL
SELECT 'gd_solicitacoes_timeline',       COUNT(*) FROM meridian_governanca.gd_solicitacoes_timeline
UNION ALL
SELECT 'gd_sla_atendimento_snapshot',    COUNT(*) FROM meridian_governanca.gd_sla_atendimento_snapshot;

