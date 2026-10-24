# Auditoria de experiência do usuário — Plataforma de Governança

Data: 2026-10-24
Escopo: revisão estática do app.py v5.0, sem execução contra Databricks.

## Objetivo
Reduzir redundâncias, tornar os elementos interativos previsíveis e orientar a plataforma por tarefas do usuário, sem remover funcionalidades de governança necessárias.

## Evidência observada e ações

### P0 — Elemento visual duplicado na lista do Glossário
**Observação:** cada conceito era renderizado como um cartão informativo e, logo abaixo, um botão dourado com o mesmo nome. O botão repetia a informação e ocupava espaço, enquanto o cartão em si não era clicável.
**Ação preparada:** substituído por um único botão por conceito que contém nome, domínio e status. O conceito selecionado usa estilo primário; os demais, secundário. Isso elimina a duplicação e torna a área inteira do item clicável.
**Validação pendente:** conferir visualmente em diferentes larguras e temas do Streamlit.

### P1 — Indicadores no topo e detalhes da mesma informação
**Observação:** o Glossário mostra KPIs de total de conceitos e estados e, abaixo, filtros por status. Isso pode ser útil para visão gerencial, mas é redundante em tarefas de busca quando ocupa muito espaço.
**Recomendação:** manter os KPIs como resumo gerencial, mas considerar recolhê-los ou reduzi-los em telas focadas em localizar/editar um conceito. Não remover sem confirmar os perfis que usam a visão de gestão.

### P1 — Navegação por abas com funções diferentes
**Observação:** o Glossário reúne conceitos, regras, relacionamentos, histórico e workflow em abas. É uma organização coerente, mas a relação entre conceito e regras fica também apresentada dentro da tela de detalhe.
**Recomendação:** manter as regras vinculadas como resumo no detalhe do conceito; usar a aba “Regras de Negócio” para pesquisa, manutenção e visão transversal. Evitar repetir listas completas de regras em outros painéis.

### P1 — Estados e status precisam de vocabulário consistente
**Observação:** o código usa estados como `homologado`, `em_revisao`, `rascunho`, `pendente`, `em_analise` e `certificado` em contextos diferentes.
**Recomendação:** manter nomes internos no banco, mas mostrar rótulos amigáveis e padronizados por entidade e etapa. Não usar “certificado” para significar apenas “metadados completos”.

### P1 — Confirmação e retorno de ações
**Observação:** há operações de gravação com mensagens de sucesso e falha distintas; a revisão já melhorou a confirmação da certificação, edição em lote e gravação da auditoria nos fluxos tocados.
**Recomendação:** padronizar feedback com três estados: concluído, concluído parcialmente e não concluído. Mostrar qual registro falhou e próximo passo, sem expor detalhes técnicos sensíveis ao usuário final.

### P2 — Linguagem e densidade
**Observação:** a interface combina emojis, termos técnicos e cartões com informações repetidas.
**Recomendação:** manter ícones como apoio, mas priorizar rótulos consistentes, descrições curtas e hierarquia visual. Mostrar primeiro a decisão ou tarefa principal; deixar explicações longas em ajuda contextual/expansores.

### P2 — Responsividade e acessibilidade
**Observação:** uso extensivo de HTML/CSS embutido e cartões customizados pode gerar diferenças entre larguras de tela e temas.
**Recomendação:** validar contraste, foco por teclado, rótulos de controles, truncamento de nomes longos e layout em desktop/tablet. Preferir componentes nativos onde atendam à necessidade, reduzindo HTML customizado desnecessário.

## Princípios de UX a aplicar globalmente
1. Uma informação, um lugar principal; repetições só quando ajudarem uma tarefa diferente.
2. Um item que parece clicável deve ser clicável; um controle clicável deve ter estado selecionado claro.
3. Ação destrutiva ou de aprovação deve explicar impacto e exigir confirmação quando apropriado.
4. Todo salvamento deve informar resultado e próximo passo.
5. Filtros devem afetar claramente a lista e manter a seleção válida após mudanças.
6. Indicadores devem mostrar definição curta, período/filtro aplicável e origem quando necessário.
7. Separar estado operacional, completude documental, qualidade de dados e certificação.
8. Não alterar a semântica de regras ou estados sem validação com o responsável de negócio.

## Plano de trabalho
- [x] Remover duplicação cartão + botão na lista de conceitos do Glossário.
- [x] Tornar cada item da lista um único controle clicável com seleção visível.
- [ ] Revisar todos os módulos (Início, Catálogo, Glossário, Domínios, Scorecard, Curadoria, Auditoria e Meu Espaço) com matriz: tarefa, informação exibida, duplicação, ação principal e feedback.
- [ ] Unificar vocabulário visual dos estados.
- [ ] Validar responsividade e acessibilidade.
- [ ] Executar testes funcionais e visuais em ambiente de homologação.
- [ ] Confirmar com usuários de negócio quais KPIs são necessários por perfil antes de remover conteúdo.

## Limites
É uma auditoria estática do código, não teste de usabilidade com usuários nem validação visual executada. Não houve acesso de leitura/escrita às tabelas Databricks para confirmar dados reais. As recomendações que possam alterar significado, permissão ou regras precisam de validação de negócio.
