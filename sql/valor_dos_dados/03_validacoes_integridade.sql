-- ════════════════════════════════════════════════════════════════════
-- GOVERNANTES · Valor dos Dados · v3
-- 03 — Validações de integridade e consistência
--
-- Cria a visão vd_v_integridade (somente leitura) com uma linha por
-- violação encontrada, e termina com uma asserção que ABORTA se houver
-- qualquer violação. A aplicação consulta a mesma visão antes de cada
-- diagnóstico e na tela de auditoria do módulo.
--
-- Estas verificações são a 3ª camada. As duas primeiras impedem a
-- gravação incorreta: validação prévia na aplicação e gravação
-- condicionada (vd_regras.py). Esta camada detecta qualquer desvio que
-- tenha escapado — inclusive gravações feitas fora da aplicação.
-- ════════════════════════════════════════════════════════════════════

DECLARE OR REPLACE VARIABLE vd_catalogo STRING DEFAULT 'workspace';
DECLARE OR REPLACE VARIABLE vd_schema   STRING DEFAULT 'meridian_governanca';
USE CATALOG IDENTIFIER(vd_catalogo);
USE SCHEMA  IDENTIFIER(vd_schema);

CREATE OR REPLACE VIEW vd_v_integridade
COMMENT 'Valor dos Dados — violações de integridade (deve estar vazia)' AS

-- ── I01 Duplicidade de chave natural ─────────────────────────────────
SELECT 'I01' AS codigo, 'Chave natural duplicada' AS regra, tabela AS entidade, chave AS registro, CAST(n AS STRING) AS detalhe
FROM (
          SELECT 'vd_objetivos' tabela, chave_natural chave, COUNT(*) n FROM vd_objetivos GROUP BY ALL HAVING COUNT(*) > 1
UNION ALL SELECT 'vd_processos', chave_natural, COUNT(*) FROM vd_processos GROUP BY ALL HAVING COUNT(*) > 1
UNION ALL SELECT 'vd_indicadores', chave_natural, COUNT(*) FROM vd_indicadores GROUP BY ALL HAVING COUNT(*) > 1
UNION ALL SELECT 'vd_vinculos', chave_natural, COUNT(*) FROM vd_vinculos GROUP BY ALL HAVING COUNT(*) > 1
UNION ALL SELECT 'vd_achados', chave_natural, COUNT(*) FROM vd_achados GROUP BY ALL HAVING COUNT(*) > 1
UNION ALL SELECT 'vd_achados_ocorrencias', chave_natural, COUNT(*) FROM vd_achados_ocorrencias GROUP BY ALL HAVING COUNT(*) > 1
UNION ALL SELECT 'vd_intervencoes', chave_natural, COUNT(*) FROM vd_intervencoes GROUP BY ALL HAVING COUNT(*) > 1
UNION ALL SELECT 'vd_intervencoes.codigo', codigo, COUNT(*) FROM vd_intervencoes GROUP BY ALL HAVING COUNT(*) > 1
UNION ALL SELECT 'vd_medicoes', chave_natural, COUNT(*) FROM vd_medicoes GROUP BY ALL HAVING COUNT(*) > 1
UNION ALL SELECT 'vd_beneficios', chave_natural, COUNT(*) FROM vd_beneficios GROUP BY ALL HAVING COUNT(*) > 1
UNION ALL SELECT 'vd_conversoes_financeiras', chave_natural, COUNT(*) FROM vd_conversoes_financeiras GROUP BY ALL HAVING COUNT(*) > 1
UNION ALL SELECT 'vd_evidencias', chave_natural, COUNT(*) FROM vd_evidencias GROUP BY ALL HAVING COUNT(*) > 1
UNION ALL SELECT 'vd_historico', chave_natural, COUNT(*) FROM vd_historico GROUP BY ALL HAVING COUNT(*) > 1
)

-- ── C01 Processo → objetivo existente ────────────────────────────────
UNION ALL SELECT 'C01','Processo sem objetivo existente','vd_processos', p.processo_id, p.objetivo_id
FROM vd_processos p LEFT ANTI JOIN vd_objetivos o ON o.objetivo_id = p.objetivo_id

-- ── C02 Indicador: objetivo existente e processo do mesmo objetivo ──
UNION ALL SELECT 'C02','Indicador sem objetivo existente','vd_indicadores', i.indicador_id, i.objetivo_id
FROM vd_indicadores i LEFT ANTI JOIN vd_objetivos o ON o.objetivo_id = i.objetivo_id
UNION ALL SELECT 'C02','Indicador ligado a processo de outro objetivo ou inexistente','vd_indicadores', i.indicador_id, i.processo_id
FROM vd_indicadores i LEFT JOIN vd_processos p ON p.processo_id = i.processo_id
WHERE i.processo_id IS NOT NULL AND (p.processo_id IS NULL OR p.objetivo_id <> i.objetivo_id)

-- ── C03 Vínculo: origem existente e do mesmo objetivo ────────────────
UNION ALL SELECT 'C03','Vínculo com objetivo inexistente','vd_vinculos', v.vinculo_id, v.objetivo_id
FROM vd_vinculos v LEFT ANTI JOIN vd_objetivos o ON o.objetivo_id = v.objetivo_id
UNION ALL SELECT 'C03','Vínculo de processo inexistente ou de outro objetivo','vd_vinculos', v.vinculo_id, v.origem_id
FROM vd_vinculos v LEFT JOIN vd_processos p ON p.processo_id = v.origem_id
WHERE v.origem_tipo = 'processo' AND (p.processo_id IS NULL OR p.objetivo_id <> v.objetivo_id)

-- ── C04 Referências dos vínculos ativos ao catálogo existente ────────
UNION ALL SELECT 'C04','Ativo referenciado não existe em tabelas_metadata','vd_vinculos', v.vinculo_id, concat(v.ref_schema,'.',v.ref_nome)
FROM vd_vinculos v LEFT JOIN tabelas_metadata m ON m.schema_name = v.ref_schema AND m.table_name = v.ref_nome
WHERE v.status = 'ativo' AND v.ref_tipo = 'ativo' AND m.table_name IS NULL
UNION ALL SELECT 'C04','Produto referenciado não existe','vd_vinculos', v.vinculo_id, v.ref_id
FROM vd_vinculos v LEFT JOIN produtos_dados p ON p.produto_id = v.ref_id
WHERE v.status = 'ativo' AND v.ref_tipo = 'produto' AND p.produto_id IS NULL
UNION ALL SELECT 'C04','Termo do glossário referenciado não existe','vd_vinculos', v.vinculo_id, v.ref_id
FROM vd_vinculos v LEFT JOIN business_glossary g ON g.glossary_id = v.ref_id
WHERE v.status = 'ativo' AND v.ref_tipo = 'termo_glossario' AND g.glossary_id IS NULL
UNION ALL SELECT 'C04','Indicador referenciado inexistente ou de outro objetivo','vd_vinculos', v.vinculo_id, v.ref_id
FROM vd_vinculos v LEFT JOIN vd_indicadores i ON i.indicador_id = v.ref_id
WHERE v.status = 'ativo' AND v.ref_tipo = 'indicador' AND (i.indicador_id IS NULL OR i.objetivo_id <> v.objetivo_id)
UNION ALL SELECT 'C04','Domínio referenciado não existe em tabelas_metadata.dominio','vd_vinculos', v.vinculo_id, v.ref_nome
FROM vd_vinculos v
WHERE v.status = 'ativo' AND v.ref_tipo = 'dominio'
  AND NOT EXISTS (SELECT 1 FROM tabelas_metadata m WHERE m.dominio = v.ref_nome)
UNION ALL SELECT 'C04','Responsável referenciado não é Owner/Steward cadastrado','vd_vinculos', v.vinculo_id, v.ref_nome
FROM vd_vinculos v
WHERE v.status = 'ativo' AND v.ref_tipo = 'responsavel'
  AND NOT EXISTS (SELECT 1 FROM tabelas_metadata m WHERE m.data_owner = v.ref_nome OR m.data_steward = v.ref_nome)
-- Chave de business_rules ainda não confirmada: enquanto não for, nenhum
-- vínculo desse tipo é aceito (a aplicação também recusa).
UNION ALL SELECT 'C04','Vínculo a regra de negócio antes da confirmação da chave','vd_vinculos', v.vinculo_id, v.ref_id
FROM vd_vinculos v WHERE v.status = 'ativo' AND v.ref_tipo = 'regra_negocio'

-- ── C05 Achado coerente com execução, vínculo, objetivo e processo ──
UNION ALL SELECT 'C05','Achado com vínculo inexistente ou de outro objetivo','vd_achados', a.achado_id, a.vinculo_id
FROM vd_achados a LEFT JOIN vd_vinculos v ON v.vinculo_id = a.vinculo_id
WHERE v.vinculo_id IS NULL OR v.objetivo_id <> a.objetivo_id
UNION ALL SELECT 'C05','Achado com processo incompatível com o vínculo','vd_achados', a.achado_id, a.processo_id
FROM vd_achados a JOIN vd_vinculos v ON v.vinculo_id = a.vinculo_id
WHERE (v.origem_tipo = 'processo' AND (a.processo_id IS NULL OR a.processo_id <> v.origem_id))
   OR (v.origem_tipo = 'objetivo' AND a.processo_id IS NOT NULL)
UNION ALL SELECT 'C05','Achado com execução inexistente ou de outro objetivo','vd_achados', a.achado_id, a.ultima_execucao_id
FROM vd_achados a LEFT JOIN vd_execucoes_diagnostico e ON e.execucao_id = a.ultima_execucao_id
WHERE e.execucao_id IS NULL OR e.objetivo_id <> a.objetivo_id
UNION ALL SELECT 'C05','Achado com regra fora do catálogo da versão','vd_achados', a.achado_id, concat(a.regra_codigo,'/',a.versao_regras)
FROM vd_achados a LEFT ANTI JOIN vd_regras_diagnostico r ON r.regra_codigo = a.regra_codigo AND r.versao_regras = a.versao_regras
UNION ALL SELECT 'C05','Ocorrência com execução, vínculo ou achado inconsistente','vd_achados_ocorrencias', oc.ocorrencia_id, oc.execucao_id
FROM vd_achados_ocorrencias oc
LEFT JOIN vd_execucoes_diagnostico e ON e.execucao_id = oc.execucao_id
LEFT JOIN vd_vinculos v ON v.vinculo_id = oc.vinculo_id
LEFT JOIN vd_achados a ON a.achado_id = oc.achado_id
WHERE e.execucao_id IS NULL OR v.vinculo_id IS NULL OR v.objetivo_id <> e.objetivo_id
   OR (oc.achado_id IS NOT NULL AND (a.achado_id IS NULL OR a.vinculo_id <> oc.vinculo_id OR a.regra_codigo <> oc.regra_codigo))

-- ── C06 Intervenção coerente com o achado de origem ──────────────────
UNION ALL SELECT 'C06','Intervenção com achado inexistente ou de outro objetivo','vd_intervencoes', i.intervencao_id, i.achado_id
FROM vd_intervencoes i LEFT JOIN vd_achados a ON a.achado_id = i.achado_id
WHERE a.achado_id IS NULL OR a.objetivo_id <> i.objetivo_id
UNION ALL SELECT 'C06','Intervenção originada de achado não validado ou não aplicável','vd_intervencoes', i.intervencao_id, a.status_validacao
FROM vd_intervencoes i JOIN vd_achados a ON a.achado_id = i.achado_id
WHERE a.status_validacao <> 'validado' OR a.natureza = 'nao_aplicavel'
UNION ALL SELECT 'C06','Mais de uma intervenção não final para o mesmo achado','vd_intervencoes', achado_id, CAST(COUNT(*) AS STRING)
FROM vd_intervencoes WHERE status NOT IN ('concluida','cancelada') GROUP BY achado_id HAVING COUNT(*) > 1
UNION ALL SELECT 'C06','Reabertura sem intervenção anterior final do mesmo achado','vd_intervencoes', i.intervencao_id, i.intervencao_anterior_id
FROM vd_intervencoes i LEFT JOIN vd_intervencoes ant ON ant.intervencao_id = i.intervencao_anterior_id
WHERE i.sequencia > 1 AND (ant.intervencao_id IS NULL OR ant.achado_id <> i.achado_id
      OR ant.sequencia <> i.sequencia - 1 OR ant.status NOT IN ('concluida','cancelada'))
UNION ALL SELECT 'C06','Intervenção em validação ou concluída sem evidência','vd_intervencoes', i.intervencao_id, i.status
FROM vd_intervencoes i
WHERE i.status IN ('em_validacao','concluida')
  AND NOT EXISTS (SELECT 1 FROM vd_evidencias e WHERE e.entidade_tipo = 'intervencao' AND e.entidade_id = i.intervencao_id)

-- ── C07 Medição coerente com indicador e intervenção ─────────────────
UNION ALL SELECT 'C07','Medição com indicador inexistente ou de outro objetivo','vd_medicoes', m.medicao_id, m.indicador_id
FROM vd_medicoes m LEFT JOIN vd_indicadores i ON i.indicador_id = m.indicador_id
WHERE i.indicador_id IS NULL OR i.objetivo_id <> m.objetivo_id
UNION ALL SELECT 'C07','Medição associada a intervenção de outro objetivo','vd_medicoes', m.medicao_id, m.intervencao_id
FROM vd_medicoes m LEFT JOIN vd_intervencoes i ON i.intervencao_id = m.intervencao_id
WHERE m.intervencao_id IS NOT NULL AND (i.intervencao_id IS NULL OR i.objetivo_id <> m.objetivo_id)

-- ── C08 Benefício coerente e cálculo reproduzível (fórmula F1) ───────
UNION ALL SELECT 'C08','Benefício com indicador ou intervenção de outro objetivo','vd_beneficios', b.beneficio_id, b.objetivo_id
FROM vd_beneficios b
LEFT JOIN vd_indicadores i ON i.indicador_id = b.indicador_id
LEFT JOIN vd_intervencoes v ON v.intervencao_id = b.intervencao_id
WHERE i.indicador_id IS NULL OR v.intervencao_id IS NULL OR i.objetivo_id <> b.objetivo_id OR v.objetivo_id <> b.objetivo_id
UNION ALL SELECT 'C08','Medições do benefício incompatíveis (indicador, tipo, ordem, validação ou valores)','vd_beneficios', b.beneficio_id, concat_ws('/', b.medicao_antes_id, b.medicao_depois_id)
FROM vd_beneficios b
JOIN vd_indicadores i ON i.indicador_id = b.indicador_id
LEFT JOIN vd_medicoes a ON a.medicao_id = b.medicao_antes_id
LEFT JOIN vd_medicoes d ON d.medicao_id = b.medicao_depois_id
WHERE b.estagio IN ('em_validacao','validado') AND (
      a.medicao_id IS NULL OR d.medicao_id IS NULL
   OR a.indicador_id <> b.indicador_id OR d.indicador_id <> b.indicador_id
   OR a.tipo <> 'linha_base' OR d.tipo <> 'acompanhamento'
   OR d.data_referencia <= a.data_referencia
   OR a.status <> 'ativo' OR d.status <> 'ativo'
   OR a.status_validacao <> 'validado' OR d.status_validacao <> 'validado'
   OR a.valor <> b.valor_antes OR d.valor <> b.valor_depois
   OR i.sentido_melhora <> b.sentido_melhora)
UNION ALL SELECT 'C08','Valor financeiro sem conversão compatível, validada e vigente','vd_beneficios', b.beneficio_id, b.conversao_id
FROM vd_beneficios b
JOIN vd_indicadores i ON i.indicador_id = b.indicador_id
LEFT JOIN vd_conversoes_financeiras c ON c.conversao_id = b.conversao_id
LEFT JOIN vd_medicoes d ON d.medicao_id = b.medicao_depois_id
WHERE b.valor_financeiro IS NOT NULL AND (
      c.conversao_id IS NULL OR c.status_validacao <> 'validado'
   OR i.tipo_unidade = 'percentual' OR c.unidade_indicador <> i.unidade OR c.moeda <> b.moeda
   OR d.data_referencia < c.vigencia_inicio OR (c.vigencia_fim IS NOT NULL AND d.data_referencia > c.vigencia_fim)
   OR abs(b.valor_financeiro - round(b.melhoria * c.fator * c.custo_unitario, 2)) > 0.01)

-- ── C09 Priorização reproduzível pelo modelo da versão gravada ───────
UNION ALL SELECT 'C09','Pontos ou prioridade diferentes do modelo','vd_intervencoes', i.intervencao_id,
       concat('gravado=', i.pontuacao_total, '/', i.prioridade, ' recalculado=', r.total, '/', f.prioridade)
FROM vd_intervencoes i
JOIN (SELECT i2.intervencao_id,
             SUM(mp.pontos * mp.peso) AS total,
             MAX(CASE WHEN mp.criterio = 'prioridade_objetivo' THEN mp.pontos * mp.peso END) AS p1,
             MAX(CASE WHEN mp.criterio = 'posicao_ativo'       THEN mp.pontos * mp.peso END) AS p2,
             MAX(CASE WHEN mp.criterio = 'tipo_achado'         THEN mp.pontos * mp.peso END) AS p3,
             MAX(CASE WHEN mp.criterio = 'abrangencia'         THEN mp.pontos * mp.peso END) AS p4,
             MAX(CASE WHEN mp.criterio = 'esforco'             THEN mp.pontos * mp.peso END) AS p5,
             COUNT(*) AS criterios
      FROM vd_intervencoes i2
      JOIN vd_modelo_priorizacao mp ON mp.versao_modelo = i2.versao_modelo AND (
            (mp.criterio = 'prioridade_objetivo' AND mp.entrada = i2.entrada_prioridade_obj)
         OR (mp.criterio = 'posicao_ativo'       AND mp.entrada = i2.entrada_posicao_ativo)
         OR (mp.criterio = 'tipo_achado'         AND mp.entrada = i2.entrada_tipo_achado)
         OR (mp.criterio = 'abrangencia'         AND mp.entrada = i2.entrada_abrangencia)
         OR (mp.criterio = 'esforco'             AND mp.entrada = i2.esforco))
      GROUP BY i2.intervencao_id) r ON r.intervencao_id = i.intervencao_id
LEFT JOIN vd_faixas_prioridade f ON f.versao_modelo = i.versao_modelo AND r.total BETWEEN f.pontuacao_min AND f.pontuacao_max
WHERE r.criterios <> 5 OR r.total <> i.pontuacao_total OR f.prioridade IS NULL OR f.prioridade <> i.prioridade
   OR r.p1 <> i.pts_prioridade_objetivo OR r.p2 <> i.pts_posicao_ativo OR r.p3 <> i.pts_tipo_achado
   OR r.p4 <> i.pts_abrangencia OR r.p5 <> i.pts_esforco
UNION ALL SELECT 'C09','Entradas da priorização divergentes da origem','vd_intervencoes', i.intervencao_id, 'objetivo/vínculo/achado'
FROM vd_intervencoes i
JOIN vd_achados a ON a.achado_id = i.achado_id
JOIN vd_objetivos o ON o.objetivo_id = i.objetivo_id
JOIN vd_vinculos v ON v.vinculo_id = a.vinculo_id
WHERE i.entrada_tipo_achado <> a.natureza
   OR i.entrada_posicao_ativo <> coalesce(v.papel_no_processo, 'nao_aplicavel')
-- a prioridade do objetivo pode mudar depois; vale a do momento da gravação,
-- conferida no histórico de criação da intervenção (I03)
UNION ALL SELECT 'C09','Faixa de abrangência incompatível com a quantidade','vd_intervencoes', i.intervencao_id, i.entrada_abrangencia
FROM vd_intervencoes i
WHERE i.entrada_abrangencia <> CASE WHEN i.abrangencia_ativos IS NULL THEN 'nao_determinada'
                                    WHEN i.abrangencia_ativos = 0 THEN '0'
                                    WHEN i.abrangencia_ativos <= 2 THEN '1-2'
                                    WHEN i.abrangencia_ativos <= 5 THEN '3-5' ELSE '6+' END

UNION ALL SELECT 'C09','Intervenção pontuada com entrada do modelo ainda não aprovada','vd_intervencoes', i.intervencao_id,
       concat(mp.criterio, '=', mp.entrada)
FROM vd_intervencoes i
JOIN vd_modelo_priorizacao mp ON mp.versao_modelo = i.versao_modelo AND mp.situacao <> 'aprovado' AND (
      (mp.criterio = 'prioridade_objetivo' AND mp.entrada = i.entrada_prioridade_obj)
   OR (mp.criterio = 'posicao_ativo'       AND mp.entrada = i.entrada_posicao_ativo)
   OR (mp.criterio = 'tipo_achado'         AND mp.entrada = i.entrada_tipo_achado)
   OR (mp.criterio = 'abrangencia'         AND mp.entrada = i.entrada_abrangencia)
   OR (mp.criterio = 'esforco'             AND mp.entrada = i.esforco))

-- ── C10 Transições registradas no histórico seguem a máquina de estados
UNION ALL SELECT 'C10','Transição não permitida registrada','vd_historico', h.entidade_id, concat(h.status_anterior,' → ',h.status_novo)
FROM vd_historico h LEFT JOIN vd_transicoes_intervencao t ON t.status_de = h.status_anterior AND t.status_para = h.status_novo
WHERE h.entidade_tipo = 'intervencao' AND h.acao = 'transicao' AND t.status_de IS NULL
UNION ALL SELECT 'C10','Transição executada por perfil não autorizado','vd_historico', h.entidade_id, concat(h.perfil,': ',h.status_anterior,' → ',h.status_novo)
FROM vd_historico h
JOIN vd_transicoes_intervencao t ON t.status_de = h.status_anterior AND t.status_para = h.status_novo
JOIN vd_intervencoes i ON i.intervencao_id = h.entidade_id
WHERE h.entidade_tipo = 'intervencao' AND h.acao = 'transicao'
  AND NOT (array_contains(split(t.perfis, ','), h.perfil)
           OR (array_contains(split(t.perfis, ','), 'responsavel') AND h.executado_por = i.responsavel))

-- ── I02 Evidência e histórico apontam para entidades existentes ──────
UNION ALL SELECT 'I02','Evidência de entidade inexistente','vd_evidencias', e.evidencia_id, concat(e.entidade_tipo,':',e.entidade_id)
FROM vd_evidencias e
WHERE NOT ( (e.entidade_tipo = 'objetivo'    AND EXISTS (SELECT 1 FROM vd_objetivos x WHERE x.objetivo_id = e.entidade_id))
         OR (e.entidade_tipo = 'processo'    AND EXISTS (SELECT 1 FROM vd_processos x WHERE x.processo_id = e.entidade_id))
         OR (e.entidade_tipo = 'indicador'   AND EXISTS (SELECT 1 FROM vd_indicadores x WHERE x.indicador_id = e.entidade_id))
         OR (e.entidade_tipo = 'vinculo'     AND EXISTS (SELECT 1 FROM vd_vinculos x WHERE x.vinculo_id = e.entidade_id))
         OR (e.entidade_tipo = 'achado'      AND EXISTS (SELECT 1 FROM vd_achados x WHERE x.achado_id = e.entidade_id))
         OR (e.entidade_tipo = 'intervencao' AND EXISTS (SELECT 1 FROM vd_intervencoes x WHERE x.intervencao_id = e.entidade_id))
         OR (e.entidade_tipo = 'medicao'     AND EXISTS (SELECT 1 FROM vd_medicoes x WHERE x.medicao_id = e.entidade_id))
         OR (e.entidade_tipo = 'beneficio'   AND EXISTS (SELECT 1 FROM vd_beneficios x WHERE x.beneficio_id = e.entidade_id))
         OR (e.entidade_tipo = 'conversao'   AND EXISTS (SELECT 1 FROM vd_conversoes_financeiras x WHERE x.conversao_id = e.entidade_id)))

-- ── I03 Toda versão de cada entidade tem registro no histórico ───────
UNION ALL SELECT 'I03','Versão sem registro no histórico', x.entidade_tipo, x.entidade_id, CAST(x.versao AS STRING)
FROM (          SELECT 'objetivo' entidade_tipo, objetivo_id entidade_id, versao FROM vd_objetivos
      UNION ALL SELECT 'processo', processo_id, versao FROM vd_processos
      UNION ALL SELECT 'indicador', indicador_id, versao FROM vd_indicadores
      UNION ALL SELECT 'vinculo', vinculo_id, versao FROM vd_vinculos
      UNION ALL SELECT 'achado', achado_id, versao FROM vd_achados
      UNION ALL SELECT 'intervencao', intervencao_id, versao FROM vd_intervencoes
      UNION ALL SELECT 'medicao', medicao_id, versao FROM vd_medicoes
      UNION ALL SELECT 'beneficio', beneficio_id, versao FROM vd_beneficios
      UNION ALL SELECT 'conversao', conversao_id, versao FROM vd_conversoes_financeiras) x
LEFT ANTI JOIN vd_historico h ON h.entidade_tipo = x.entidade_tipo AND h.entidade_id = x.entidade_id AND h.versao_entidade = x.versao

-- ── I04 Cobertura completa de cada execução concluída ────────────────
--    Cada vínculo analisado deve ter UMA ocorrência para CADA regra
--    aplicável da versão — inclusive nao_disparou e nao_avaliada.
--    Regras aplicáveis: tipo do vínculo 'ativo' → regras de ativo + DG-09;
--    'produto' → regras de produto + DG-09; demais tipos → DG-09.
UNION ALL SELECT 'I04','Resumo da execução diferente das ocorrências gravadas','vd_execucoes_diagnostico', e.execucao_id,
       concat('vinculos=', e.vinculos_analisados, ' x ', COALESCE(o.vinculos, 0))
FROM vd_execucoes_diagnostico e
LEFT JOIN (SELECT execucao_id, COUNT(DISTINCT vinculo_id) AS vinculos FROM vd_achados_ocorrencias GROUP BY execucao_id) o
       ON o.execucao_id = e.execucao_id
WHERE e.status = 'concluida' AND e.vinculos_analisados <> COALESCE(o.vinculos, 0)
UNION ALL SELECT 'I04','Regra aplicável sem ocorrência na execução','vd_achados_ocorrencias', concat(esp.execucao_id,'/',esp.vinculo_id), esp.regra_codigo
FROM (SELECT DISTINCT oc.execucao_id, oc.vinculo_id, r.regra_codigo
      FROM vd_achados_ocorrencias oc
      JOIN vd_execucoes_diagnostico e ON e.execucao_id = oc.execucao_id AND e.status = 'concluida'
      JOIN vd_vinculos v ON v.vinculo_id = oc.vinculo_id
      JOIN vd_regras_diagnostico r ON r.versao_regras = e.versao_regras
       AND (r.aplica_a = 'vinculo' OR (r.aplica_a = 'ativo' AND v.ref_tipo = 'ativo') OR (r.aplica_a = 'produto' AND v.ref_tipo = 'produto'))) esp
LEFT ANTI JOIN vd_achados_ocorrencias oc2
  ON oc2.execucao_id = esp.execucao_id AND oc2.vinculo_id = esp.vinculo_id AND oc2.regra_codigo = esp.regra_codigo
UNION ALL SELECT 'I04','Ocorrência de regra que não se aplica ao tipo do vínculo','vd_achados_ocorrencias', oc.ocorrencia_id, oc.regra_codigo
FROM vd_achados_ocorrencias oc
JOIN vd_execucoes_diagnostico e ON e.execucao_id = oc.execucao_id
JOIN vd_vinculos v ON v.vinculo_id = oc.vinculo_id
LEFT JOIN vd_regras_diagnostico r ON r.regra_codigo = oc.regra_codigo AND r.versao_regras = e.versao_regras
WHERE r.regra_codigo IS NULL
   OR NOT (r.aplica_a = 'vinculo' OR (r.aplica_a = 'ativo' AND v.ref_tipo = 'ativo') OR (r.aplica_a = 'produto' AND v.ref_tipo = 'produto'))
UNION ALL SELECT 'I04','Regra desabilitada na execução com resultado diferente de nao_avaliada','vd_achados_ocorrencias', oc.ocorrencia_id, oc.regra_codigo
FROM vd_achados_ocorrencias oc
JOIN vd_execucoes_diagnostico e ON e.execucao_id = oc.execucao_id
WHERE array_contains(split(coalesce(e.regras_desabilitadas, ''), ','), oc.regra_codigo) AND oc.resultado <> 'nao_avaliada'

-- ── I05 Estrutura: colunas obrigatórias da v3 presentes ──────────────
UNION ALL SELECT 'I05','Coluna da v3 ausente (tabela de versão anterior)', esperado.tabela, esperado.coluna, 'ausente'
FROM (SELECT * FROM VALUES
        ('vd_vinculos','objetivo_id'), ('vd_achados','versao_regras'), ('vd_achados','situacao'),
        ('vd_intervencoes','versao_modelo'), ('vd_intervencoes','entrada_abrangencia'), ('vd_intervencoes','sequencia'),
        ('vd_medicoes','objetivo_id'), ('vd_beneficios','melhoria'), ('vd_beneficios','formula_versao'),
        ('vd_indicadores','tipo_unidade'), ('vd_historico','chave_natural'), ('vd_evidencias','perfil'),
        ('vd_modelo_priorizacao','situacao'), ('vd_execucoes_diagnostico','motivos_desabilitacao')
      AS t(tabela, coluna)) esperado
LEFT ANTI JOIN information_schema.columns c
  ON c.table_catalog = current_catalog() AND c.table_schema = current_schema()
 AND c.table_name = esperado.tabela AND c.column_name = esperado.coluna;


-- ── Resultado detalhado e asserção ───────────────────────────────────
SELECT codigo, regra, COUNT(*) AS violacoes FROM vd_v_integridade GROUP BY codigo, regra ORDER BY codigo;

SELECT CASE WHEN COUNT(*) = 0 THEN 'OK: nenhuma violação de integridade'
            ELSE raise_error(concat('FALHA: ', COUNT(*), ' violações — consulte vd_v_integridade')) END AS resultado
FROM vd_v_integridade;
