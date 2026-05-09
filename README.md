# Raízes do Nordeste — API

API back-end para a rede de lanchonetes "Raízes do Nordeste". Trabalho feito para o projeto multidisciplinar da UNINTER (2026), trilha back-end, sob orientação da Prof. Luciane Yanase Kanashiro.

A API cobre cadastro/autenticação, cardápio, controle de estoque por unidade, pedidos com canais diferentes (app, totem, balcão, pickup, web), pagamento simulado e programa de fidelidade.

## Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2 + Alembic
- PostgreSQL
- JWT (python-jose) e bcrypt (passlib)
- Pytest

## Pré-requisitos

- Python 3.11 ou superior
- PostgreSQL rodando em algum lugar (local, container, etc.)
- Git

## Como rodar

Clone o repositório e entre na pasta:

```bash
git clone <url-do-repo>
cd projeto_raizes_do_nordeste
```

Crie e ative o ambiente virtual:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / Mac
source venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Copie o `.env.example` para `.env` e preencha com seus dados:

```bash
cp .env.example .env
```

O `.env` espera:

```
DATABASE_URL=postgresql://usuario:senha@localhost:5432/raizes_nordeste
SECRET_KEY=alguma-chave-secreta
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Crie o banco no Postgres (`raizes_nordeste`, ou o nome que você escolher na URL) e rode as migrations:

```bash
alembic upgrade head
```

Suba a API:

```bash
uvicorn main:app --reload
```

A API fica em `http://localhost:8000`. A documentação interativa do Swagger fica em `http://localhost:8000/docs` e o Redoc em `http://localhost:8000/redoc`.

Pra checar se subiu certo, tem um endpoint de health em `GET /health`.

## Testes

Os testes usam SQLite em memória, então não precisa de Postgres rodando pra testar.

```bash
pytest
```

## Estrutura

```
app/
  api/             rotas e schemas Pydantic
  application/     casos de uso (services)
  domain/          modelos do banco e enums
  infrastructure/  config, conexão com banco, segurança/JWT
alembic/           migrations
tests/             testes automatizados
main.py            ponto de entrada da API
```

A separação em camadas segue o que foi pedido no roteiro: domain isolado das dependências externas, application com a lógica de negócio, infrastructure com o que conversa com banco/config, e api com os controllers.

## Endpoints principais

Estão todos documentados no Swagger, mas em resumo:

- `/auth` — cadastro, login (JWT) e perfil do usuário logado
- `/unidades` — CRUD das unidades da rede
- `/produtos` — cardápio
- `/estoque` — consulta e movimentação de estoque por unidade
- `/pedidos` — criar, listar, consultar e atualizar status de pedidos
- `/pagamentos` — solicitar pagamento (mock) e consultar
- `/fidelidade` — saldo de pontos, ganhar, resgatar e histórico

## Perfis de acesso

- `CLIENTE` — cria pedidos, consulta os próprios pedidos e usa fidelidade
- `ATENDENTE` — atende pedidos no balcão, mexe em estoque
- `COZINHA` — atualiza status dos pedidos (em preparo, pronto)
- `GERENTE` — tudo de operação + cadastro de produtos/unidades
- `ADMIN` — acesso total

## LGPD

O cadastro só é aceito com `consentimento_lgpd: true`. Sem isso retorna 400.

## Observações

O pagamento é um mock — simula um gateway externo aprovando ~90% das requisições e recusando valores abaixo de R$1.
