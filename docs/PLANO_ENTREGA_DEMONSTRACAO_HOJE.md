# Plano de entrega para demonstração — 25/10/2026

## Objetivo
Preparar a plataforma Meridian para uma apresentação executiva usando exclusivamente dados fictícios. Este plano não caracteriza homologação para produção nem validação de controles corporativos.

## Corte de escopo para hoje
1. **Navegação e apresentação:** validar página inicial, menus, atalhos, títulos, estados vazios e indicação explícita de exemplos ilustrativos.
2. **Cenário de demonstração:** escolher uma jornada curta e coerente: localizar ativo → compreender conceito e regra → consultar qualidade/linhagem → abrir solicitação ou registrar problema → acompanhar o estado.
3. **Consistência dos dados:** confirmar que contagens e indicadores exibidos correspondem aos dados fictícios carregados; não mostrar métricas como se fossem reais ou atualizadas quando isso não foi verificado.
4. **Ações críticas:** testar gravação, aprovação/rejeição, curadoria individual e em lote; verificar mensagens de erro e trilha de auditoria. Não afirmar sucesso quando uma gravação falhar.
5. **Indicadores:** distinguir completude de metadados, qualidade, conformidade, maturidade e certificação; exibir fórmula/critério quando disponível e identificar indicadores ilustrativos.
6. **Revisão visual:** verificar hierarquia, consistência de componentes, legibilidade, responsividade e ausência de erros visuais impeditivos.
7. **Validação final:** executar o roteiro de apresentação na versão publicada e registrar limitações remanescentes.

## Roteiro mínimo de demonstração
1. Início: apresentar panorama e pendências.
2. Catálogo: pesquisar e abrir um ativo fictício.
3. Glossário: mostrar conceito e regra de negócio relacionada.
4. Detalhe do ativo: explicar responsável, classificação, atualização e linhagem disponível.
5. Qualidade: demonstrar dimensão, problema e evidência — ou identificar claramente o exemplo como simulado.
6. Solicitação: registrar uma solicitação e mostrar o estado do fluxo.
7. Gestão: explicar os indicadores, suas fórmulas e limitações.

## Critérios de aceite para a apresentação
- Nenhum atalho principal leva à página errada.
- Nenhum dado demonstrativo é apresentado como dado corporativo real.
- Os principais fluxos do roteiro podem ser concluídos sem intervenção manual no banco durante a reunião.
- Falhas de leitura/gravação são comunicadas sem falsa confirmação.
- As contagens e indicadores do roteiro são coerentes com os dados de demonstração.
- Limitações conhecidas estão registradas e não são mascaradas.

## Fora do corte de hoje
- SSO e autenticação corporativa.
- Uso de dados reais da empresa.
- Garantia de prontidão para produção.
- Refatoração integral da aplicação monolítica.
- Funcionalidades novas que não sejam necessárias para o roteiro principal.

## Regra de comunicação
O código compilar não significa que o fluxo foi validado. Cada item deve ser marcado como concluído somente após teste na aplicação; acesso ao Databricks e execução da versão publicada precisam ser confirmados separadamente.
