# Auditoria técnica — Plataforma de Governança Banco Meridian

Data: 2026-10-24  
Versão analisada: app.py v5.0  
Branch de trabalho: fix/scorecard-definicoes-auditoria

## Resumo executivo

A aplicação contém fluxos funcionais de catálogo, glossário, curadoria, indicadores, qualidade e certificação. Antes de ser tratada como aplicação corporativa, há riscos que precisam ser endereçados e validados no ambiente real. Este documento registra evidências no código e separa correções seguras de decisões que dependem da infraestrutura.

## Achados priorizados

### P0 — Autenticação e autorização reais não demonstradas
Evidência: `USUARIOS` contém perfis fixos no código e a interface permite selecionar o usuário em um `selectbox`; o perfil é copiado para `st.session_state`. Isso é simulação de login, não autenticação. A autorização baseada nesses perfis não deve ser considerada uma barreira de segurança para dados reais.

**Ação requerida:** integrar o provedor de identidade corporativo suportado pelo ambiente de hospedagem (por exemplo, SSO/OIDC ou mecanismo aprovado pela organização), obter a identidade verificada do servidor e mapear grupos para perfis. Não remover o login de demonstração sem confirmar o provedor e a configuração de deploy, pois isso pode bloquear todos os usuários.

### P1 — SQL dinâmico e validação de parâmetros
Evidência: há chamadas `exe(f"UPDATE ...")` e `exe(f"INSERT ...")` em múltiplas telas. A função `esc` duplica aspas simples, mas não substitui consultas parametrizadas nem validação por allowlist de identificadores SQL.

**Ação requerida:** inventariar todas as gravações; usar parâmetros vinculados quando suportados pelo conector e validar identificadores de schema/tabela por allowlist. Testar caracteres especiais e entradas inesperadas. Não fazer substituição em massa sem testes de regressão.

### P1 — Resultado das operações e consistência transacional
Evidência: `exe` retorna `(True, None)` ou `(False, erro)`, mas alguns fluxos de certificação executam duas atualizações sequenciais e exibem sucesso sem verificar os dois resultados individualmente.

**Ação requerida:** centralizar a execução de comandos de escrita, verificar cada resultado e exibir sucesso somente após todas as operações necessárias concluírem. Definir estratégia de compensação/idempotência para falha parcial e registrar o resultado da operação.

### P1 — Auditoria de alterações incompleta ou inconsistente
Evidência: há inserções em `metadata_audit` em alguns fluxos de curadoria e uma tela de leitura da tabela; os fluxos de aprovação/certificação também alteram estado. A cobertura uniforme de todas as alterações não está demonstrada.

**Ação requerida:** criar uma matriz ação × evento auditado; incluir ator verificado, timestamp, objeto, ação, valores anterior/novo e resultado. Não registrar tokens, segredos ou dados pessoais desnecessários.

### P1 — Conceitos e critérios de indicadores
Evidência: o Scorecard calcula um pilar de preenchimento de metadados, enquanto a aplicação tem uma área separada de qualidade multidimensional e outra de certificação. Esses conceitos devem permanecer distintos. A primeira correção já foi preparada na branch para explicitar isso no Scorecard.

**Ação requerida:** definir um dicionário de indicadores com nome, propósito, fórmula, numerador, denominador, filtros, origem, periodicidade, tratamento de nulos e responsável; validar as fórmulas com os donos de negócio.

### P2 — Tratamento de falhas de consulta
Evidência: `qry` captura exceções e retorna DataFrame vazio mais texto de erro; as funções `load_*` geralmente descartam o erro ao usar `df, _ = qry(...)`. Uma falha de conexão pode parecer ausência legítima de dados.

**Ação requerida:** diferenciar explicitamente erro de consulta e conjunto vazio; mostrar estado de erro ao usuário, registrar detalhes técnicos sem segredos e impedir ações de gravação quando a leitura necessária falhou.

### P2 — Testes automatizados e implantação
Evidência: a revisão estática não prova que a aplicação executa corretamente contra o workspace, as tabelas e as permissões atuais do Databricks.

**Ação requerida:** adicionar testes de sintaxe, testes unitários para regras puras e testes de integração em workspace de homologação; manter publicação separada do merge e validar rollback.

## Mudança já preparada

- Renomeia o pilar “Qualidade” do Scorecard para “Completude de Metadados”.
- Esclarece que preenchimento de metadados não equivale à qualidade efetiva dos dados.
- Esclarece que certificação depende de status formal e fluxo de certificação, não de preenchimento automático.

## Plano de validação antes de publicar

- [ ] Revisar o diff do pull request.
- [ ] Executar compilação/sintaxe Python e testes automatizados.
- [ ] Confirmar esquema e permissões das tabelas no Databricks de homologação.
- [ ] Testar perfis consultante, curador e aprovador com identidades reais.
- [ ] Testar falha de conexão, falha parcial de escrita e cache após atualização.
- [ ] Validar indicadores com exemplos calculados manualmente e aprovação do responsável de negócio.
- [ ] Aprovar o pull request antes de merge.
- [ ] Publicar em homologação e validar antes de qualquer produção.

## Limites desta auditoria

Esta revisão foi feita sobre o código-fonte no GitHub. Não foram executadas consultas no Databricks nem testes de ponta a ponta. Os achados indicam o que o código demonstra ou não demonstra; não substituem validação do ambiente, configuração de identidade, permissões e regras de negócio.
