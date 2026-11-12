# Login com conta Google

A plataforma usa o login nativo do Streamlit (`st.login`) com o Google como provedor OpenID Connect. A página pública continua aberta; o restante exige login, e só entram os e-mails autorizados.

Enquanto a seção `[auth]` não existir nos secrets do app, a plataforma continua com os usuários de demonstração. Basta salvar os secrets abaixo para o login real entrar em vigor; não há nova publicação de código.

## 1. Credencial no Google Cloud (uma vez)

1. Em console.cloud.google.com, crie ou escolha um projeto (sugestão: `governantes-plataforma`).
2. **APIs e serviços › Tela de consentimento OAuth** (Google Auth Platform › Branding):
   - Tipo de usuário: **Externo**.
   - Nome do app: `Plataforma Governantes`; e-mail de suporte: o seu.
   - Escopos: apenas `openid`, `email` e `profile`, que não exigem verificação do Google.
   - Enquanto o app estiver em modo de teste, cadastre em **Usuários de teste** os mesmos e-mails que terão acesso (limite de 100). Para não depender dessa lista, publique o app em produção; com esses escopos básicos, a publicação não passa por revisão.
3. **Credenciais › Criar credenciais › ID do cliente OAuth**:
   - Tipo: **Aplicativo da Web**.
   - URI de redirecionamento autorizado: `https://banco-meridian-governanca.streamlit.app/oauth2callback`
   - Para testes locais, acrescente também `http://localhost:8501/oauth2callback`.
4. Guarde o **ID do cliente** e a **chave secreta do cliente**.

## 2. Secrets do app no Streamlit Cloud

Em share.streamlit.io › app › Settings › Secrets, acrescente ao conteúdo que já existe (sem apagar as credenciais do Databricks):

```toml
[auth]
redirect_uri = "https://banco-meridian-governanca.streamlit.app/oauth2callback"
cookie_secret = "<texto aleatório longo, gerado uma vez>"
client_id = "<ID do cliente>"
client_secret = "<chave secreta do cliente>"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[acesso.usuarios."seu.email@gmail.com"]
nome = "Seu Nome"
perfil = "curador"

[acesso.usuarios."outra.pessoa@empresa.com"]
nome = "Outra Pessoa"
perfil = "consultante"
```

- `perfil` aceita `consultante`, `curador` ou `aprovador`. Um e-mail com perfil fora dessa lista é ignorado.
- `cookie_secret` pode ser gerado com `python -c "import secrets; print(secrets.token_hex(32))"`.
- Para incluir, remover ou mudar o perfil de alguém, edite só a lista `[acesso.usuarios]`. Remover o e-mail bloqueia o acesso na próxima vez que a pessoa abrir a plataforma.

## 3. Comportamento

| Situação | O que acontece |
|---|---|
| Visitante sem login | Vê a página pública. "Entrar na plataforma" leva ao login do Google. |
| Conta Google autorizada | Entra com o nome e o perfil definidos na lista. Não há troca de perfil. |
| Conta Google não autorizada | Vê "Acesso não autorizado" e a opção de sair e usar outra conta. Nenhum dado é exibido. |
| Sair | O menu do perfil, no topo, encerra a sessão. |

O e-mail autenticado pelo Google passa a ser o autor de cada registro, o que atende à rastreabilidade exigida pelo módulo Valor dos Dados.
