-- ════════════════════════════════════════════════════════════════════
-- GOVERNANTES · Valor dos Dados · v3
-- 04 — Permissões (Unity Catalog)
--
-- Substitua os marcadores <...> pelos principais reais e confirme com
-- SHOW GRANTS (00, passo 7). Comandos de GRANT/REVOKE são idempotentes.
--
-- Modelo de proteção da auditoria:
--   • vd_historico, vd_evidencias, vd_achados_ocorrencias e
--     vd_controle_versao têm delta.appendOnly = true: UPDATE e DELETE são
--     rejeitados pelo Delta para QUALQUER usuário, inclusive o app.
--   • Só o DONO da tabela pode remover essa propriedade. O dono é um grupo
--     de administração — nunca a credencial do app nem usuários comuns.
--   • Usuários comuns não acessam o banco: entram pela aplicação, que não
--     oferece edição nem exclusão de histórico e evidências.
--   • A credencial do app recebe SELECT + MODIFY (MODIFY é necessário para
--     inserir); sem ALTER, sem propriedade, sem DROP.
--   • Tabelas de referência (regras, modelo, faixas, transições, versão):
--     o app só lê; alterações passam por nova versão publicada em 02.
-- ════════════════════════════════════════════════════════════════════

DECLARE OR REPLACE VARIABLE vd_catalogo STRING DEFAULT 'workspace';
DECLARE OR REPLACE VARIABLE vd_schema   STRING DEFAULT 'meridian_governanca';
USE CATALOG IDENTIFIER(vd_catalogo);
USE SCHEMA  IDENTIFIER(vd_schema);

-- ── Dono das tabelas: grupo de administração da governança ───────────
ALTER TABLE vd_controle_versao        OWNER TO `<grupo_admin_governanca>`;
ALTER TABLE vd_regras_diagnostico     OWNER TO `<grupo_admin_governanca>`;
ALTER TABLE vd_modelo_priorizacao     OWNER TO `<grupo_admin_governanca>`;
ALTER TABLE vd_faixas_prioridade      OWNER TO `<grupo_admin_governanca>`;
ALTER TABLE vd_transicoes_intervencao OWNER TO `<grupo_admin_governanca>`;
ALTER TABLE vd_conversoes_financeiras OWNER TO `<grupo_admin_governanca>`;
ALTER TABLE vd_objetivos              OWNER TO `<grupo_admin_governanca>`;
ALTER TABLE vd_processos              OWNER TO `<grupo_admin_governanca>`;
ALTER TABLE vd_indicadores            OWNER TO `<grupo_admin_governanca>`;
ALTER TABLE vd_vinculos               OWNER TO `<grupo_admin_governanca>`;
ALTER TABLE vd_execucoes_diagnostico  OWNER TO `<grupo_admin_governanca>`;
ALTER TABLE vd_achados                OWNER TO `<grupo_admin_governanca>`;
ALTER TABLE vd_achados_ocorrencias    OWNER TO `<grupo_admin_governanca>`;
ALTER TABLE vd_intervencoes           OWNER TO `<grupo_admin_governanca>`;
ALTER TABLE vd_medicoes               OWNER TO `<grupo_admin_governanca>`;
ALTER TABLE vd_beneficios             OWNER TO `<grupo_admin_governanca>`;
ALTER TABLE vd_evidencias             OWNER TO `<grupo_admin_governanca>`;
ALTER TABLE vd_historico              OWNER TO `<grupo_admin_governanca>`;
ALTER VIEW  vd_v_integridade          OWNER TO `<grupo_admin_governanca>`;

-- ── Credencial do app ────────────────────────────────────────────────
GRANT USE CATALOG ON CATALOG IDENTIFIER(vd_catalogo) TO `<principal_do_app>`;
GRANT USE SCHEMA  ON SCHEMA  IDENTIFIER(vd_schema)   TO `<principal_do_app>`;

-- Leitura apenas
GRANT SELECT ON TABLE vd_controle_versao        TO `<principal_do_app>`;
GRANT SELECT ON TABLE vd_regras_diagnostico     TO `<principal_do_app>`;
GRANT SELECT ON TABLE vd_modelo_priorizacao     TO `<principal_do_app>`;
GRANT SELECT ON TABLE vd_faixas_prioridade      TO `<principal_do_app>`;
GRANT SELECT ON TABLE vd_transicoes_intervencao TO `<principal_do_app>`;
GRANT SELECT ON TABLE vd_v_integridade          TO `<principal_do_app>`;

-- Leitura e gravação
GRANT SELECT, MODIFY ON TABLE vd_conversoes_financeiras TO `<principal_do_app>`;
GRANT SELECT, MODIFY ON TABLE vd_objetivos              TO `<principal_do_app>`;
GRANT SELECT, MODIFY ON TABLE vd_processos              TO `<principal_do_app>`;
GRANT SELECT, MODIFY ON TABLE vd_indicadores            TO `<principal_do_app>`;
GRANT SELECT, MODIFY ON TABLE vd_vinculos               TO `<principal_do_app>`;
GRANT SELECT, MODIFY ON TABLE vd_execucoes_diagnostico  TO `<principal_do_app>`;
GRANT SELECT, MODIFY ON TABLE vd_achados                TO `<principal_do_app>`;
GRANT SELECT, MODIFY ON TABLE vd_intervencoes           TO `<principal_do_app>`;
GRANT SELECT, MODIFY ON TABLE vd_medicoes               TO `<principal_do_app>`;
GRANT SELECT, MODIFY ON TABLE vd_beneficios             TO `<principal_do_app>`;
-- Somente inclusão garantida pelo appendOnly
GRANT SELECT, MODIFY ON TABLE vd_achados_ocorrencias    TO `<principal_do_app>`;
GRANT SELECT, MODIFY ON TABLE vd_evidencias             TO `<principal_do_app>`;
GRANT SELECT, MODIFY ON TABLE vd_historico              TO `<principal_do_app>`;

-- ── Conferência ──────────────────────────────────────────────────────
SHOW GRANTS `<principal_do_app>` ON SCHEMA IDENTIFIER(vd_schema);
SHOW TBLPROPERTIES vd_historico  ('delta.appendOnly');
SHOW TBLPROPERTIES vd_evidencias ('delta.appendOnly');
