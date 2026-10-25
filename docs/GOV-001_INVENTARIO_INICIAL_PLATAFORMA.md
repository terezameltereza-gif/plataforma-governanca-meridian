# GOV-001 — Inventário inicial da plataforma

**Base analisada:** `app.py` na branch `fix/home-navigation-native-controls` (revisão estática do código-fonte).  
**Data:** 2026-10-25  
**Status:** inventário inicial; precisa ser complementado com execução da aplicação e confirmação de tabelas/colunas no Databricks.

## 1. Arquitetura observada no código

- Aplicação monolítica em Streamlit, concentrada em `app.py`.
- Acesso a dados via conector SQL do Databricks (`databricks.sql`).
- Catálogo/schema configurado na conexão: `workspace` / `meridian_governanca`; as consultas usam nomes qualificados `meridian_governanca.<tabela>`.
- Cache de conexão com `st.cache_resource`; cache de consultas e loaders com TTL de 300 segundos.
- Navegação por `st.session_state["pagina"]`, com menu lateral e páginas condicionais.
- Identidade/perfil implementados atualmente por dicionário fixo `USUARIOS` e seletor de usuário na interface. Isso caracteriza simulação de login; não demonstra autenticação corporativa. A interface agora identifica explicitamente o acesso como demonstrativo, mas a autenticação real segue pendente.
- A função `qry` retorna DataFrame e erro. Os 15 loaders principais agora passam por `_load_df`, que exibe erro de leitura no contexto da página em vez de descartar silenciosamente a falha. A execução contra o Databricks ainda não foi validada.
- A função `exe` retorna sucesso/erro, mas a revisão anterior identificou fluxos que precisam verificar cada gravação individualmente.

## 2. Páginas e jornadas identificadas

Os rótulos abaixo são os nomes observados no menu e/ou nas condições de roteamento. A existência do código de página não prova que todos os fluxos funcionem contra o ambiente real.

| Página/área | Jornada principal | Dependências / pontos de atenção |
|---|---|---|
| Início | Visão geral e atalhos para descoberta | KPIs agregados de metadados, glossário, vínculos e regras; havia botões ocultos acionados por JavaScript; havia exemplo de linhagem ilustrativo sem identificação explícita como exemplo |
| Glossário | Pesquisar conceitos, regras, relacionamentos e histórico; curadoria de conceitos | `business_glossary`, `business_rules`, `glossary_asset_link`, sugestões e histórico; revisar estados vazios e erro de leitura |
| Catálogo | Localizar ativos de dados e consultar metadados | `tabelas_metadata`; verificar completude, responsável, classificação, atualização e origem |
| Domínios | Explorar domínios de negócio e seus ativos/responsáveis | Depende de metadados e relações; validar definição de domínio e ownership |
| Indicadores | Consultar indicadores gerenciais/snapshots | `gd_indicators_snapshot` e outras fontes; fórmulas, filtros, período e atualização precisam ser documentados |
| Scorecard | Acompanhar completude/avaliação indicativa | Distinguir completude de metadados de qualidade real e maturidade |
| Qualidade | Consultar dimensões e solicitações de qualidade | `gd_quality_dimensions`, `solicitacoes_qualidade`; verificar evidência de execução e período |
| Certificação | Consultar e operar certificação de ativos | `gd_certification`; validar critérios, aprovação, consistência de gravações e auditoria |
| Curadoria | Manter metadados e tratar sugestões/alterações | Escritas SQL e eventos de auditoria; verificar erros parciais e permissões no backend |
| Auditoria | Consultar registros de alterações | `metadata_audit` e eventos registrados em outros fluxos; cobertura ainda não demonstrada como uniforme |
| Meu Espaço | Jornada pessoal de solicitações e pendências | Verificar vínculo entre solicitante, status, fila e histórico |
| Linhagem | Explorar relações de origem/derivação | `linhagem_ativos`; distinguir linhagem integrada/verificada de relacionamento cadastrado manualmente |
| Produtos | Consultar produtos de dados e ativos vinculados | `produtos_dados`, `produto_ativos`; validar responsáveis, status e vínculos |

## 3. Tabelas acessadas por loaders identificados

| Tabela | Loader / uso identificado | Validação pendente |
|---|---|---|
| `meridian_governanca.tabelas_metadata` | `load_meta()`; catálogo, indicadores de ativos e detalhes | Colunas obrigatórias, responsáveis, atualização, classificação |
| `meridian_governanca.business_glossary` | `load_glossario()`; conceitos de negócio | Vocabulário de status, owner/steward, aprovação e histórico |
| `meridian_governanca.glossary_asset_link` | `load_links()`; vínculo conceito–ativo | Chaves, duplicidades, cobertura e integridade dos vínculos |
| `meridian_governanca.business_rules` | `load_rules()`; regras de negócio | Relação com conceitos/ativos e critério de validação |
| `meridian_governanca.sugestoes_conceitos` | `load_sugestoes_conceitos()` | Fluxo de aprovação, autor, status e auditoria |
| `meridian_governanca.sugestoes_regras` | `load_sugestoes_regras()` | Fluxo de aprovação, autor, status e auditoria |
| `meridian_governanca.gd_solicitacoes_timeline` | `load_timeline()` | Relação com solicitações e consistência temporal |
| `meridian_governanca.gd_sla_atendimento_snapshot` | `load_sla_snap()` | Definição do SLA, periodicidade e cálculo |
| `meridian_governanca.solicitacoes_acesso` | `load_solicitacoes_acesso()` | Estados, autorização real, decisão e trilha de auditoria |
| `meridian_governanca.gd_quality_dimensions` | `load_quality_dimensions()` | Fórmulas, fonte de cada dimensão, execução e cobertura |
| `meridian_governanca.gd_certification` | `load_cert()` | Critérios formais, aprovador e transições de status |
| `meridian_governanca.gd_indicators_snapshot` | `load_snap()` | Definições, período, origem e atualização |
| `meridian_governanca.produtos_dados` | `load_produtos()` | Owner, steward, status e finalidade |
| `meridian_governanca.produto_ativos` | `load_produto_ativos()` | Integridade e cardinalidade dos vínculos |
| `meridian_governanca.linhagem_ativos` | `load_linhagem()` | Origem, destino, tipo de relação e proveniência |
| `meridian_governanca.solicitacoes_qualidade` | `load_solicitacoes_qualidade()` | Fluxo, responsável, prioridade, prazo e evidências |
| `meridian_governanca.metadata_audit` | Referenciada nos fluxos de auditoria | Cobertura de eventos e estrutura real precisam ser confirmadas |

**Importante:** esta lista foi extraída de nomes de tabelas no código. Não é confirmação de que todas as tabelas existem, estão acessíveis, têm os esquemas esperados ou contêm dados atuais no workspace.

## 4. Achados confirmados por leitura estática

1. **Login demonstrativo:** usuários e perfis são definidos no código e selecionados por um `selectbox`; não é autenticação corporativa.
2. **Erro de consulta pode ser descartado:** `qry` retorna erro separado, mas vários loaders usam `df, _`.
3. **SQL montado dinamicamente:** `exe` é chamado em diversos fluxos; a função `esc` não equivale a parâmetros SQL.
4. **Consistência de gravações:** cada retorno de `exe` precisa ser verificado em todos os fluxos; operações múltiplas podem falhar parcialmente.
5. **Indicadores de confiança:** fórmulas e fontes precisam ser documentadas para não confundir completude, qualidade, conformidade, maturidade e certificação.
6. **Home com interação frágil:** os cartões usavam HTML com `onclick` para acionar botões Streamlit ocultos.
7. **Exemplo visual na Home:** a sequência “Inadimplência → Janela 90 dias → fato_inadimplencia → Taxa NPL → Gestão de Risco” é escrita diretamente no HTML; não é comprovadamente uma linhagem derivada dos dados carregados.
8. **Atualização exibida na Home:** o horário vinha de `datetime.now()`, ou seja, horário de renderização, não necessariamente a última atualização das fontes.

## 5. Correção inicial preparada em branch separada

Na branch `fix/home-navigation-native-controls`:
- Removido o padrão de cartões que dependia de botão oculto e JavaScript para navegação.
- Cada cartão agora apresenta um botão nativo do Streamlit, com rótulo explícito.
- O cartão “Qualidade dos Dados” foi direcionado à página “🏆 Qualidade”, em vez de “🛡️ Scorecard”, para alinhar rótulo e destino.

Esta alteração ainda requer revisão do diff, teste de sintaxe, teste de navegação e validação no app publicado antes de ser considerada concluída.

## 6. Validações e correções adicionais na branch\n\n- Os carregadores principais usam `_load_df` para diferenciar falha de leitura de resultado vazio e exibir uma mensagem contextual. O cache de consultas continua em `qry` com TTL de 300 segundos; os wrappers de carregamento não mantêm cache independente.\n- O login apresenta aviso de ambiente demonstrativo e informa que selecionar um nome não autentica a identidade. Isso reduz o risco de interpretação equivocada, mas **não substitui SSO, autenticação corporativa, autorização server-side ou gestão de segredos**.\n- Foi adicionado GitHub Actions para executar `python -m py_compile app.py`; a execução para o commit `3e283356d07d6780202ee08d2297661d19d803fd` concluiu com sucesso. A verificação não executa o app, não valida bibliotecas em runtime e não consulta o Databricks.\n- As operações de gravação ainda exigem revisão individual: o código monta SQL dinamicamente e a sanitização por `esc` não equivale a query parametrizada. A interface não deve ser considerada pronta para dados reais antes de autenticação/autorização adequadas e teste de consistência/auditoria.\n\n## 7. Próximas verificações para concluir GOV-001

- [ ] Confirmar a lista de páginas e os caminhos de navegação no ambiente publicado.
- [ ] Executar cada fluxo com perfis de demonstração, sem tratar esses perfis como segurança real.
- [ ] Confirmar existência, esquema e permissões das tabelas com acesso autorizado ao workspace Databricks.
- [ ] Mapear todas as instruções `INSERT`, `UPDATE`, `DELETE` e respectivos tratamentos de erro.
- [ ] Mapear fórmulas e filtros de cada KPI.
- [ ] Identificar páginas que dependem de fontes não disponíveis ou de tabelas sem dados.
- [ ] Registrar evidência de execução e separar “não testado” de “falhou”.
