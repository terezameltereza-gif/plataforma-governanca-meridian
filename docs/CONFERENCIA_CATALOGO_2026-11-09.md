# Conferência do catálogo — 09/11/2026

Conferência visual no Catalog Explorer do workspace Free Edition `dbc-af718492-0a17`, catálogo `workspace`, schema `meridian_governanca`. Nenhum SQL foi executado e nada foi alterado.

## Estado do schema

- 20 tabelas, todas com dono `terezameltereza@gmail.com`.
- Nenhuma tabela `vd_*`: o módulo Valor dos Dados não está instalado.
- Aba de permissões do schema: nenhum privilégio concedido a outro principal.

## Colunas que o pacote tratava como não confirmadas

| Tabela | Coluna | Situação |
|---|---|---|
| tabelas_metadata | classificacao | Existe |
| tabelas_metadata | data_steward | Existe |
| glossary_asset_link | schema_name | Existe |
| produto_ativos | schema_name | Existe |
| produtos_dados | descricao, finalidade | Existem |
| produtos_dados | owner, data_owner | **Não existem.** A coluna de responsável é `responsavel`. |
| business_rules | regra_id | Existe (candidata a chave; unicidade ainda depende do arquivo 00) |
| gd_quality_dimensions | dim_id, schema_name, table_name | Existem (uma linha por ativo ainda depende do arquivo 00) |

## Ajuste decorrente

A regra DG-08 (produto sem responsável) seria desabilitada, porque procurava apenas `owner` ou `data_owner`. Os arquivos 00 e 02 passam a aceitar também `responsavel`.

## Impacto na homologação

O workspace tem um único principal, que é dono do catálogo, do schema e das tabelas. A trava 3 do roteiro recusa esse principal, como previsto. É preciso confirmar se a Free Edition permite criar um segundo usuário ou service principal sem privilégios de gravação. Se não permitir, a homologação não pode ser executada neste workspace nas condições aprovadas.

## Identidades do workspace (conferência visual, sem alterações)

- Service principals: nenhum cadastrado. O botão "Add service principal" está disponível na Free Edition.
- Grupos: `admins`, `users` e um clone de `users` criado pela Databricks, cada um com 1 membro.
- Permissões do catálogo `workspace`: o grupo de usuários do workspace tem apenas `USE CATALOG`. Um principal novo herdaria somente esse privilégio, sem nenhum direito de gravação em `meridian_governanca`.
- Ainda não verificado: se a Free Edition permite gerar credencial (segredo OAuth ou token) para o service principal, que é necessária para executar os testes.
