# Projeto de Evolução da Plataforma de Governança de Dados

**Produto:** Plataforma de Governança de Dados — Meridian / Governantes  
**Repositório:** `terezameltereza-gif/plataforma-governanca-meridian`  
**Branch de trabalho inicial:** `project/plataforma-evolucao-governanca`  
**Status:** Plano de execução — diagnóstico de código existente; validação funcional e de dados ainda necessária.

## 1. Objetivo

Evoluir a plataforma existente para que seja útil no trabalho real de governança, sem reconstruí-la do zero nem remover capacidades que já funcionam. A evolução deve permitir que uma pessoa:

1. **Encontre um dado** e compreenda seu significado, localização, responsável, contexto e limitações.
2. **Aja sobre o dado** — solicitar acesso, propor/corrigir definição, reportar problema de qualidade ou pedir melhoria.
3. **Acompanhe a ação** — saber quem é responsável, qual é o status, o que falta e qual foi o resultado.
4. **Avalie a confiança** com evidências verificáveis sobre significado, origem/linhagem, qualidade, atualização, responsabilidade e restrições de uso.
5. **Tome decisões de gestão** a partir de indicadores com fórmula, fonte, período, filtros e limitações documentados.

A regra de produto é: **Descobrir o dado → agir sobre o dado → demonstrar a confiança no dado.**

## 2. Princípios que não podem ser quebrados

- Preservar funcionalidades úteis e o backend atual; não reescrever a plataforma por preferência estética.
- Não criar ferramentas paralelas nem duplicar cadastros sem necessidade demonstrada.
- Não apresentar dado fictício, exemplo ilustrativo ou horário do servidor como se fosse evidência de atualização real.
- Não confundir completude de metadados, qualidade medida, conformidade, maturidade e certificação.
- Não exibir selo ou status de confiança sem critérios explícitos, evidências e trilha de auditoria.
- Falha de consulta não pode ser apresentada como catálogo vazio ou como sucesso.
- A interface deve usar controles acessíveis e previsíveis; evitar cartões HTML que simulam cliques em botões ocultos.
- A autorização real deve ser aplicada no servidor/dados, não apenas escondendo páginas ou oferecendo seletor de usuário.
- Toda mudança deve ter critério de aceite, teste e evidência do que foi validado.
- Manter a identidade visual escura/dourada da marca, desde que não prejudique contraste, leitura ou acessibilidade.

## 3. Escopo por frentes de trabalho

### Frente A — Diagnóstico e linha de base

**Objetivo:** entender o que existe antes de alterar.

Atividades:
- Inventariar páginas, fluxos, fontes de dados, tabelas e funções de leitura/escrita.
- Mapear os fluxos de ponta a ponta: descoberta de conceito, detalhe de ativo, solicitação, curadoria, aprovação, certificação, qualidade, linhagem e auditoria.
- Identificar funcionalidades existentes, incompletas, redundantes, quebradas ou sem evidência de uso.
- Separar achados confirmados por leitura do código daqueles que dependem de execução com dados reais.
- Registrar riscos, dependências e comportamento atual antes de mudanças.

Entregáveis:
- Matriz de funcionalidades e fluxos.
- Inventário de dependências e pontos de integração.
- Registro de riscos e linha de base para regressão.

### Frente B — UX e navegação

**Objetivo:** reduzir esforço para encontrar e concluir tarefas.

Prioridades:
- Corrigir a navegação da página inicial: eliminar o padrão de cartão visual com botão oculto acionado por JavaScript.
- Tornar os cartões e chamadas de ação coerentes, acessíveis e com destino correto.
- Evitar rotas diferentes que levam à mesma página sem explicar a diferença; revisar “Regras de Negócio”, “Relacionamentos” e “Qualidade dos Dados”.
- Diferenciar claramente navegação, filtro, seleção de registro e execução de ação.
- Padronizar nomes, descrições, status e mensagens de sucesso/erro.
- Reduzir repetição de cartões, botões, indicadores e listas que mostram a mesma informação.
- Exibir estados vazios, carregamento, erro e ausência de permissão de maneira explícita.
- Validar contraste, foco por teclado, legibilidade e comportamento em diferentes larguras de tela.

Entregáveis:
- Mapa de navegação revisado.
- Padrões de componentes e mensagens.
- Fluxos de tarefa testados com critérios de aceite.

### Frente C — Descoberta e compreensão dos dados

**Objetivo:** ajudar o usuário a localizar o dado certo e entender se pode usá-lo.

Para cada ativo/conceito, quando a informação existir, apresentar:
- Nome e definição de negócio.
- Domínio, sistema/fonte e localização técnica (tabela/objeto/campo).
- Owner e Steward responsáveis.
- Regras de negócio e regras de qualidade relacionadas.
- Linhagem e transformações conhecidas.
- Última atualização real e periodicidade esperada.
- Classificação, restrições e instruções de solicitação de acesso.
- Evidências de qualidade, limitações conhecidas e data da última validação.
- Status do metadado e significado objetivo desse status.

Regras:
- Não inventar valores ausentes. Mostrar “não informado”, “não integrado” ou “não validado”, conforme o caso.
- Distinguir linhagem efetivamente integrada de relacionamento cadastrado manualmente.
- A descoberta do ativo não implica autorização para acessar seu conteúdo.
- A busca deve permitir procurar por termo de negócio, sinônimo, domínio e nome técnico quando suportado pela fonte.

### Frente D — Operação de Owners e Stewards

**Objetivo:** transformar governança em trabalho atribuível e acompanhável.

Capacidades-alvo:
- Fila única de pendências atribuídas, com prioridade, prazo, responsável e próximo passo.
- Solicitação de novo termo, alteração de definição, correção de metadado, melhoria de ativo, reporte de problema e solicitação de acesso.
- Encaminhamento para o papel correto e estados de fluxo documentados.
- Registro de decisão, justificativa, evidência e histórico de alterações.
- Visão de “Minhas solicitações” para solicitantes e “Minha fila” para responsáveis.
- Mensagens que indiquem claramente se a operação foi concluída, parcialmente concluída ou falhou.

Antes de implementar novos formulários, verificar se “Meu Espaço”, Curadoria e fluxos existentes já cobrem a necessidade. Reutilizar e conectar o que funciona.

### Frente E — Confiança, qualidade, linhagem e certificação

**Objetivo:** tornar a confiança explicável, auditável e proporcional à evidência.

Manter conceitos separados:
- **Completude de metadados:** proporção de campos de metadados obrigatórios preenchidos.
- **Qualidade medida:** resultado das regras de qualidade executadas, com período, cobertura e fonte.
- **Conformidade:** atendimento a requisitos específicos aplicáveis.
- **Maturidade:** nível de capacidade/processo, conforme modelo definido.
- **Certificação:** decisão formal baseada em critérios e evidências aprovados.

Para cada indicador ou selo, documentar:
- Nome, finalidade e definição.
- Fórmula e denominador.
- Fonte, filtros, periodicidade e horário da última execução.
- Tratamento de nulos, falhas e ausência de dados.
- Responsável pela regra e pela validação.
- Critério de aprovação e evidências associadas.
- Limitações conhecidas.

Não apresentar um índice composto como “qualidade real dos dados” sem metodologia validada. Se um índice indicativo for mantido, explicitar o que mede e o que não mede.

### Frente F — Indicadores e decisão executiva

**Objetivo:** permitir priorizar ações, não apenas visualizar números.

Cada indicador deve responder:
- Qual pergunta de gestão ele responde?
- Qual decisão pode ser tomada a partir dele?
- Qual é a definição e a fórmula?
- Qual é a fonte e o período?
- Quais filtros realmente alteram o resultado?
- Quem é o responsável?
- Quais são as limitações e a qualidade da própria métrica?

Indicadores candidatos, sujeitos à disponibilidade e validação das fontes:
- Ativos com Owner/Steward definidos.
- Metadados obrigatórios completos.
- Regras de qualidade aprovadas, reprovadas e não executadas.
- Solicitações abertas, vencidas, concluídas e tempo de resolução.
- Pendências por domínio, responsável, criticidade e antiguidade.
- Ativos certificados e certificações próximas da revisão.
- Cobertura de linhagem e de regras associadas.
- Problemas recorrentes e riscos por domínio.

Não publicar um KPI até que sua fórmula, fonte e interpretação estejam confirmadas. Os filtros visíveis devem afetar o resultado ou ser removidos.

### Frente G — Segurança, integridade e auditoria

**Objetivo:** evitar que a interface prometa controles que não existem.

Prioridade alta:
- Substituir a seleção de usuário de demonstração por autenticação real compatível com o ambiente de implantação, ou rotular claramente o modo como demonstração e bloquear uso produtivo.
- Definir matriz de permissões por perfil e aplicar a autorização também no backend.
- Revisar consultas construídas por interpolação de strings; usar parâmetros suportados pelo driver e validação estrita para identificadores.
- Verificar retorno de todas as operações de escrita e tratar falhas parciais.
- Garantir trilha de auditoria consistente: ator, data/hora, ação, entidade, valores relevantes, resultado e justificativa quando aplicável.
- Evitar registrar segredos, credenciais ou dados sensíveis em logs.
- Definir comportamento seguro para falta de conexão, erro de consulta e ausência de permissão.

**Bloqueio de produção:** não declarar a plataforma pronta para uso produtivo com dados sensíveis enquanto autenticação, autorização e tratamento de falhas não forem verificados no ambiente real.

### Frente H — Testes, implantação e observabilidade

**Objetivo:** reduzir regressões e comprovar o comportamento real.

Testes mínimos:
- Testes unitários de cálculos, normalização de status e validações.
- Testes de integração para leitura/escrita, com dados de teste não sensíveis.
- Testes de fluxos críticos: criar solicitação, encaminhar, aprovar/rejeitar, corrigir metadado, certificar, auditar.
- Testes de erro: conexão indisponível, consulta com erro, escrita parcial, registro inexistente, permissão negada.
- Testes de regressão das páginas existentes.
- Smoke test após publicação no Streamlit Community Cloud.
- Verificação de logs e de secrets/configuração sem expor credenciais.

Entregáveis:
- Checklist de testes com resultado e evidência.
- Registro de defeitos conhecidos.
- Plano de rollback para mudanças de risco.
- Registro do commit/versão validada e data da validação.

## 4. Priorização

### P0 — Segurança e veracidade

1. Confirmar ambiente, fontes de dados e comportamento quando a consulta falha.
2. Identificar modo de autenticação e impedir que um seletor de usuário seja confundido com controle de acesso real.
3. Corrigir qualquer KPI, status, selo ou timestamp que possa transmitir confiança sem evidência.
4. Corrigir navegação quebrada e interações frágeis na página inicial.
5. Proteger operações de escrita e registrar falhas parciais.

### P1 — Fluxos operacionais essenciais

1. Mapear e testar a jornada completa do usuário que encontra um dado.
2. Mapear e testar a jornada de solicitação e acompanhamento.
3. Consolidar a fila de Owner/Steward sem duplicar cadastros.
4. Mostrar evidências de significado, responsabilidade, qualidade e linhagem no detalhe do ativo.
5. Padronizar status, mensagens e estados vazios/erro.

### P2 — Gestão e experiência

1. Validar fórmulas e filtros dos indicadores.
2. Criar visões de gestão por domínio e responsável com ações associadas.
3. Melhorar acessibilidade, responsividade e consistência visual.
4. Reduzir redundâncias restantes com base em uso e teste, não apenas preferência estética.

### P3 — Evoluções posteriores

1. Busca avançada e sinônimos, conforme suporte da fonte.
2. Alertas e monitoramento de prazos e regras.
3. Recomendações de priorização e apoio de IA, apenas com fontes e limites explícitos.
4. Medição de adoção e efetividade da plataforma.

## 5. Critérios de aceite transversais

Uma alteração só será considerada concluída quando:
- O problema e o comportamento esperado estiverem descritos.
- A funcionalidade anterior relevante tiver sido preservada ou a mudança tiver justificativa explícita.
- O fluxo funcionar com dados reais ou com dados de teste claramente identificados.
- Erros e ausência de dados forem distinguidos de resultado vazio/zero.
- Permissões forem respeitadas.
- A mudança tiver sido testada, incluindo pelo menos um cenário negativo quando aplicável.
- Não houver regressão conhecida em páginas e fluxos relacionados.
- O resultado for documentado com evidência e limitação conhecida.

## 6. Forma de execução

Para cada item do backlog:
1. Registrar problema observado e evidência.
2. Definir impacto para usuário/negócio e risco.
3. Identificar páginas, funções, tabelas e integrações afetadas.
4. Definir comportamento esperado e critério de aceite.
5. Implementar em branch isolada e alteração pequena.
6. Executar testes estáticos e funcionais disponíveis.
7. Revisar diff e impactos em fluxos relacionados.
8. Abrir Pull Request com resumo, testes e riscos.
9. Validar no ambiente publicado após merge/deploy.
10. Atualizar este plano com status e evidências.

Não agrupar mudanças de segurança, lógica de negócio e redesenho visual num único pacote sem necessidade. Mudanças de alto risco devem ser isoladas para facilitar revisão e rollback.

## 7. Backlog inicial de execução

| ID | Item | Prioridade | Evidência / condição de conclusão |
|---|---|---|---|
| GOV-001 | Inventariar páginas e fluxos existentes | P0 | Matriz de fluxo, origem de dados e operações de escrita |
| GOV-002 | Auditar autenticação e autorização | P0 | Perfis, limites do modo atual e plano de bloqueio/implementação real |
| GOV-003 | Tratar erros de leitura sem mascará-los como lista vazia | P0 | Teste de consulta com falha e mensagem/telemetria explícita |
| GOV-004 | Corrigir navegação da página inicial | P0 | Cartões/ações acessíveis, destino correto, sem botão oculto acionado por JS |
| GOV-005 | Revisar indicadores, selos e timestamps de confiança | P0 | Definição, fonte, fórmula, data real e limitações documentadas |
| GOV-006 | Revisar consistência das operações de escrita e auditoria | P0 | Falhas parciais visíveis e auditadas |
| GOV-007 | Testar jornada de descoberta de dados | P1 | Usuário encontra ativo e entende significado, localização, responsável e restrições |
| GOV-008 | Testar solicitação e acompanhamento de ponta a ponta | P1 | Solicitante acompanha status; responsável recebe fila correta |
| GOV-009 | Consolidar experiência Owner/Steward | P1 | Fila acionável sem cadastro paralelo desnecessário |
| GOV-010 | Tornar confiança do ativo explicável | P1 | Evidências e lacunas visíveis; conceitos de score separados |
| GOV-011 | Validar filtros e fórmulas do painel gerencial | P1 | Casos de teste por KPI e filtro |
| GOV-012 | Padronizar status, mensagens e estados de erro/vazio | P1 | Vocabulário e comportamento documentados |
| GOV-013 | Testes de regressão e smoke test de publicação | P1 | Checklist preenchido com resultado real |
| GOV-014 | Revisão de acessibilidade e responsividade | P2 | Teclado, foco, contraste e telas menores verificados |
| GOV-015 | Medir resultados de uso e operação | P2 | Métricas de descoberta, resolução, prazos e cobertura definidas |

## 8. Indicadores de sucesso do projeto

Acompanhar, depois de estabelecer uma linha de base:
- Taxa de sucesso em tarefas de descoberta.
- Tempo para encontrar e compreender um ativo.
- Percentual de solicitações encaminhadas corretamente.
- Tempo de resolução e percentual de pendências vencidas.
- Percentual de ativos com responsáveis definidos.
- Cobertura de metadados obrigatórios e cobertura de regras de qualidade executadas.
- Percentual de ativos com linhagem verificada.
- Número de erros técnicos apresentados indevidamente como ausência de dados.
- Defeitos/regressões encontrados após publicação.

As metas numéricas devem ser definidas após medir a linha de base; não inventar metas sem dados.

## 9. Fora de escopo até existir justificativa

- Reescrever a plataforma inteira.
- Migrar para outra arquitetura ou banco apenas por preferência.
- Introduzir ferramentas proibidas pelo desenho atual sem decisão arquitetural explícita.
- Criar novos painéis sem pergunta de gestão e ação associada.
- Adotar IA para preencher lacunas de metadados sem validação humana, proveniência e controles.
- Declarar conformidade regulatória, qualidade ou segurança sem evidências.

## 10. Primeiro ciclo recomendado

Começar por GOV-001 a GOV-006. Eles reduzem os riscos de mexer na experiência sem entender os fluxos e de apresentar dados ou controles sem sustentação. Depois, seguir para GOV-007 a GOV-010, que materializam a jornada de descoberta, ação e confiança.

**Nota de validação:** este plano usa os achados já identificados na revisão estática do código e dos documentos do repositório. Ele não significa que todos os fluxos foram executados com dados reais, nem que a implantação publicada foi validada. Cada conclusão deve ser confirmada no ambiente correspondente antes de ser marcada como concluída.
