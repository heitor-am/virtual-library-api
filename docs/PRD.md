---
tags:
  - api
  - fastapi
  - arquitetura
  - planning
  - documentation
---

# PRD — Virtual Library API

**Projeto:** Virtual Library API
**Status:** Planejamento

---

## 1. Contexto e Motivação

API REST de biblioteca virtual com busca semântica — projeto de engenharia backend com integração de IA. O objetivo é demonstrar, em um caso de uso realista, um conjunto de práticas modernas:

- FastAPI moderno (Pydantic v2, SQLAlchemy 2.0, async)
- Arquitetura em camadas com separação de responsabilidades
- Qualidade de código: lint, type check, cobertura de testes, contract testing
- Cultura DevOps: CI/CD, multi-stage Docker, deploy automatizado
- Integração de LLM em contexto CRUD real (resumo automático + busca semântica)

Faz parte de um trio de projetos que compartilham stack e convenções para demonstrar consistência arquitetural — ver seção 14.

---

## 2. Objetivo

Entregar uma **API REST de biblioteca virtual** que permite cadastrar, consultar, atualizar e remover livros, com busca por título e autor, documentação OpenAPI automática, cobertura de testes, pipeline CI e deploy público.

### 2.1 Critérios Core

- [x] Cadastro de livros com campos: `title`, `author`, `published_date`, `summary`
- [x] Consulta de livros por título ou autor
- [x] Banco SQLite
- [x] Testes unitários dos endpoints
- [x] Endpoints bem documentados

### 2.2 Critérios Adicionais

- [x] CRUD completo (POST, GET, GET por id, PUT, DELETE)
- [x] Paginação e ordenação nas listagens
- [x] Busca case-insensitive com correspondência parcial
- [x] Migrations versionadas (Alembic)
- [x] Cobertura de testes ≥ 90%
- [x] CI no GitHub Actions (lint + type check + testes + contract tests)
- [x] Deploy público com URL acessível
- [x] README com setup, exemplos e badges

### 2.3 Diferenciais (wow factor)

Recursos pensados para destacar o projeto como peça de portfólio acima da média:

**Documentação e DX:**
- [x] **Scalar** como UI de documentação (substitui Swagger default) — visual moderno
- [x] **Landing page** em `/` com pitch do projeto e links para docs
- [x] **Mermaid diagrams** no README (arquitetura + fluxo de request) renderizados pelo GitHub
- [x] **ADRs** (Architecture Decision Records) em `docs/adr/` documentando o *porquê* de cada escolha
- [x] **Dev Container** — clone e "Reopen in Container" no VSCode, ambiente pronto
- [x] **Postman Collection** versionada em `docs/collection.json`

**AI features:**
- [x] **OpenRouter como gateway unificado** — chat e embeddings no mesmo provider, zero vendor lock-in, swap de modelo via env var
- [x] **Resumo automático via LLM** — se `summary` vier vazio no POST, a API gera via OpenRouter (`openai/gpt-4o-mini`)
- [x] **Busca semântica multilíngue** — endpoint `/books/search/semantic` usando embeddings `baai/bge-m3` (SOTA open-source multilíngue, 1024 dims, context 8192)
- [x] **Embeddings armazenados no SQLite** (BLOB) e recalculados em updates
- [x] **Integração consistente entre repos** — mesma `AI Layer`, mesmo padrão de client reutilizado nos demais projetos do portfólio

**Qualidade de código:**
- [x] **Pre-commit hooks** (ruff, mypy, pytest rápido)
- [x] **Conventional Commits** + **CHANGELOG automático** via release-please
- [x] **Schemathesis** — testes de contrato gerados a partir do OpenAPI spec
- [x] **RFC 7807 Problem Details** — formato padrão de erros HTTP
- [x] **Structured logging** (structlog) com `request_id` em todas as camadas

**DevOps:**
- [x] **Multi-stage Dockerfile** (~80 MB final vs ~500 MB single-stage)
- [x] **Makefile** com comandos comuns (`make dev`, `make test`, `make deploy`)
- [x] **Dependabot** para updates automáticos de dependências
- [x] **Healthcheck rico** — retorna versão, commit SHA, uptime, status do DB

---

## 3. Escopo

### 3.1 Dentro do Escopo

| Funcionalidade | Detalhe |
|---|---|
| Cadastrar livro | `POST /books` com validação de campos |
| Listar livros | `GET /books` com filtros (`?title=`, `?author=`), paginação (`?skip=`, `?limit=`) e ordenação (`?sort_by=`) |
| Buscar livro por ID | `GET /books/{id}` |
| Atualizar livro | `PUT /books/{id}` |
| Remover livro | `DELETE /books/{id}` |
| Health check | `GET /health` para monitoramento/deploy |
| Documentação automática | `GET /docs` (Swagger) e `GET /redoc` |

### 3.2 Fora do Escopo

- Autenticação/autorização (JWT, OAuth) — fora do escopo atual, manter simples
- Upload de arquivos/capas de livros
- Relações com outras entidades (empréstimos, usuários, reservas)
- Rate limiting e caching
- Observabilidade avançada (métricas, tracing) — log estruturado é suficiente

---

## 4. Requisitos Não-Funcionais

| Requisito | Alvo | Justificativa |
|---|---|---|
| Latência média | < 100 ms (p95) | Operações CRUD simples em SQLite local |
| Cobertura de testes | ≥ 90% | Padrão de qualidade profissional |
| Startup cold | < 3 s | Deploy ágil e testes rápidos |
| Documentação | 100% dos endpoints | Acessibilidade via `/docs` |
| Reprodutibilidade | `docker compose up` roda tudo | Onboarding em 1 comando |

---

## 5. Stack Tecnológica

### 5.1 Tabela de Decisões

| Camada | Escolha | Alternativa | Justificativa |
|---|---|---|---|
| Framework web | **FastAPI** | Django+DRF, Flask | Async nativo, docs automáticas (OpenAPI), Pydantic integrado, performance superior, padrão de mercado para APIs de IA |
| Docs UI | **Scalar** | Swagger UI default, ReDoc | UI moderna, temas customizáveis, melhor DX para quem consome a API — diferencial visível |
| Validação | **Pydantic v2** | Marshmallow | Integrado ao FastAPI, validação declarativa, serialização rápida (Rust bindings) |
| ORM | **SQLAlchemy 2.0** | Tortoise, Peewee | Maduro, padrão de facto em Python, suporte async, type-safe API nova (`Mapped`, `mapped_column`) |
| Banco | **SQLite** | PostgreSQL | Suficiente para o escopo; arquivo único facilita deploy; demonstra domínio sem overhead de serviço externo |
| Migrations | **Alembic** | — | Padrão do SQLAlchemy, versionamento do schema, melhor prática mesmo em SQLite |
| Testes unitários | **pytest + httpx.AsyncClient** | unittest | Fixtures poderosas, sintaxe limpa, `AsyncClient` testa app async sem subir servidor |
| Testes de contrato | **Schemathesis** | — | Gera casos automaticamente a partir do OpenAPI spec; pega drift entre código e docs |
| LLM gateway | **OpenRouter** | OpenAI direto, Anthropic direto | Um provider para chat + embeddings; swap de modelo por env var; billing único; failover nativo. Usa o mesmo SDK `openai` (API compatível) |
| Chat model | **`openai/gpt-4o-mini`** (via OpenRouter) | Claude Haiku, Llama 3.1 | Custo-benefício para geração de resumos curtos (~$0.001 por call) |
| Embedding model | **`baai/bge-m3`** (via OpenRouter) | `text-embedding-3-small`, `multilingual-e5-large` | SOTA multilíngue open-source, 1024 dims, context 8192, $0.01/M tokens (2x mais barato que OpenAI) |
| Cálculo de similaridade | **numpy cosine (linear scan)** | FAISS, pgvector | Simples, 5ms para <10k livros. ADR documenta migração futura |
| Erro HTTP | **RFC 7807 Problem Details** | JSON ad-hoc | Padrão RFC, `application/problem+json`, consistência entre endpoints |
| Gerenciador de dep. | **uv** | Poetry, pip+venv | 10-100× mais rápido, lockfile determinístico, feito em Rust, padrão emergente |
| Lint + format | **Ruff** | Black + Flake8 + isort | Substitui 3 ferramentas em 1, feito em Rust, config única |
| Type check | **mypy** | pyright | Padrão da comunidade, boa integração CI |
| Pre-commit | **pre-commit** | husky, lefthook | Padrão Python, hooks rodam local antes do commit |
| Convenção de commits | **Conventional Commits + release-please** | commitizen | `feat:`, `fix:` geram CHANGELOG e releases automáticos |
| Container | **Docker (multi-stage)** | — | Build cacheado, imagem final slim (~80 MB) |
| Dev env | **Dev Container** | setup manual | Clone + "Reopen in Container" → tudo pronto. Funciona no GitHub Codespaces |
| CI | **GitHub Actions** | GitLab CI, Circle | Gratuito para repos públicos, integração nativa com GitHub |
| Deploy | **Fly.io** | Railway, Render | Free tier generoso, suporte nativo a volumes persistentes (essencial p/ SQLite), deploy via `flyctl` |
| Logs | **structlog** | logging puro | Logs estruturados (JSON) com `request_id` propagado, melhor observabilidade |
| Deps security | **Dependabot + pip-audit** | Snyk, Safety | Grátis, integra nativo no GitHub, auto-PRs |

### 5.2 Versões-alvo

```
Python 3.12
FastAPI >= 0.115
SQLAlchemy >= 2.0
Pydantic >= 2.9
Alembic >= 1.13
pytest >= 8.0
scalar-fastapi >= 1.0
openai >= 1.50          # SDK usado com base_url do OpenRouter
numpy >= 1.26           # cosine similarity
schemathesis >= 3.30
structlog >= 24.0
tenacity >= 9.0         # retry com backoff nas chamadas OpenRouter
```

---

## 6. Arquitetura

### 6.1 Princípios

1. **Separação de responsabilidades** — rotas não falam com DB direto, passam por service/repository
2. **Dependency Injection via FastAPI** — sessão de DB, configurações, serviços injetados
3. **Schemas vs Models** — Pydantic (entrada/saída HTTP) separado de SQLAlchemy (persistência)
4. **Configuração via env vars** — `pydantic-settings` com `.env` para dev

### 6.2 Camadas

```
┌─────────────────────────────────────┐
│  API Layer (FastAPI Routers)        │  ← HTTP, validação de entrada, docs
├─────────────────────────────────────┤
│  Service Layer (lógica de negócio)  │  ← Regras, orquestração
├─────────────────────────────────────┤
│  Repository Layer (acesso a dados)  │  ← CRUD SQLAlchemy
├─────────────────────────────────────┤
│  AI Layer (OpenRouter integration)  │  ← Resumo e embeddings (chat + embed)
├─────────────────────────────────────┤
│  Database (SQLite)                  │
└─────────────────────────────────────┘
```

Para o escopo atual (CRUD simples), `Service` e `Repository` são quase triviais — mas a separação mostra conhecimento arquitetural e prepara o código para crescer. A **AI Layer** é um módulo separado (`app/ai/`) que encapsula o cliente **OpenRouter** (SDK `openai` com `base_url` customizado), isolando prompts, configuração de modelos e lógica de embeddings do resto do código. A mesma estrutura de `app/ai/` será replicada nos repos Q2 e Q3 — padrão compartilhado entre os três projetos.

### 6.3 Fluxo de uma Request

```
Client → Router → Pydantic validation → Service → Repository → SQLAlchemy → SQLite
                                                                                  ↓
Client ← JSON response ← Pydantic serialization ← Service ← Repository ← SQLAlchemy
```

---

## 7. Modelo de Dados

### 7.1 Entidade `Book`

| Campo | Tipo | Constraints | Descrição |
|---|---|---|---|
| `id` | `int` | PK, autoincrement | Identificador único |
| `title` | `str` | NOT NULL, index | Título do livro |
| `author` | `str` | NOT NULL, index | Autor principal |
| `published_date` | `date` | NOT NULL | Data de publicação |
| `summary` | `str` | NULL | Resumo/sinopse (auto-gerado via LLM se vazio) |
| `summary_source` | `enum('user', 'ai')` | NOT NULL default 'user' | Origem do resumo — transparência |
| `embedding` | `bytes` (BLOB) | NULL | Vetor float32 serializado (1024 dims para `baai/bge-m3`) |
| `embedding_model` | `str` | NULL | Modelo usado (ex: `baai/bge-m3`) — permite invalidação/rebuild ao trocar modelo |
| `created_at` | `datetime` | NOT NULL, default now | Timestamp de criação |
| `updated_at` | `datetime` | NOT NULL, auto-update | Última modificação |

Índices em `title` e `author` otimizam as buscas textuais. O `embedding` é recalculado sempre que `title`, `author` ou `summary` mudam. Em bancos com até alguns milhares de livros, a busca por cosine similarity é feita em Python com numpy (linear, ~5ms) — escala bem para o escopo.

### 7.2 Schemas Pydantic

- `BookBase` — campos comuns
- `BookCreate` — entrada para POST (sem `id`, `created_at`, `updated_at`)
- `BookUpdate` — entrada para PUT (todos os campos opcionais)
- `BookRead` — saída para GET (inclui `id` e timestamps)
- `BookList` — envelope de listagem com `items`, `total`, `skip`, `limit`

---

## 8. API Design

### 8.1 Endpoints

| Método | Rota | Descrição | Status de Sucesso |
|---|---|---|---|
| `POST` | `/books` | Cadastrar livro (auto-gera resumo e embedding) | 201 Created |
| `GET` | `/books` | Listar livros (com filtros textuais) | 200 OK |
| `GET` | `/books/{id}` | Buscar por ID | 200 OK / 404 |
| `PUT` | `/books/{id}` | Atualizar livro | 200 OK / 404 |
| `DELETE` | `/books/{id}` | Remover livro | 204 No Content / 404 |
| `GET` | `/books/search/semantic` | Busca por similaridade semântica | 200 OK |
| `POST` | `/books/{id}/summary/regenerate` | Regenerar resumo via LLM | 200 OK / 404 |
| `GET` | `/health` | Health check (DB, versão, uptime, commit SHA) | 200 OK / 503 |
| `GET` | `/` | Landing page (HTML estático com pitch + links) | 200 OK |
| `GET` | `/docs` | Scalar UI (docs interativa) | 200 OK |
| `GET` | `/openapi.json` | OpenAPI spec | 200 OK |

### 8.2 Query Params em `GET /books`

- `title` (str, opcional) — filtro case-insensitive, match parcial
- `author` (str, opcional) — filtro case-insensitive, match parcial
- `skip` (int, default 0) — paginação
- `limit` (int, default 20, max 100) — paginação
- `sort_by` (enum, default `created_at`) — `title`, `author`, `published_date`, `created_at`
- `order` (enum, default `desc`) — `asc`, `desc`

### 8.2.1 Query Params em `GET /books/search/semantic`

- `q` (str, obrigatório) — texto livre ("aventura na Terra Média", "livros sobre stoicismo")
- `top_k` (int, default 5, max 20) — quantos resultados retornar
- `min_score` (float, default 0.0) — filtro mínimo de similaridade (0-1)

Retorno inclui campo `similarity_score` em cada item.

### 8.3 Exemplo de Payload

**Request:**
```json
POST /books
{
  "title": "O Hobbit",
  "author": "J.R.R. Tolkien",
  "published_date": "1937-09-21",
  "summary": "Bilbo Bolseiro embarca em uma aventura..."
}
```

**Response 201:**
```json
{
  "id": 1,
  "title": "O Hobbit",
  "author": "J.R.R. Tolkien",
  "published_date": "1937-09-21",
  "summary": "Bilbo Bolseiro embarca em uma aventura...",
  "created_at": "2026-04-18T14:30:00Z",
  "updated_at": "2026-04-18T14:30:00Z"
}
```

### 8.4 Tratamento de Erros — RFC 7807 Problem Details

Formato padrão RFC 7807 (`Content-Type: application/problem+json`):

```json
{
  "type": "https://virtual-library-api.fly.dev/errors/book-not-found",
  "title": "Book Not Found",
  "status": 404,
  "detail": "Book with id 42 not found",
  "instance": "/books/42",
  "code": "BOOK_NOT_FOUND"
}
```

Campos:
- `type` — URI identificando o tipo do erro (ponte para docs futura)
- `title` — resumo curto legível
- `status` — código HTTP
- `detail` — explicação específica do caso
- `instance` — caminho da request que causou
- `code` — código interno da aplicação (machine-readable)

Códigos HTTP usados: `200`, `201`, `204`, `400`, `404`, `422`, `500`, `503`.

Erros tratados: `BOOK_NOT_FOUND`, `VALIDATION_ERROR`, `LLM_UNAVAILABLE`, `DB_UNAVAILABLE`.

---

## 9. Estrutura de Pastas

```
virtual-library-api/
├── app/
│   ├── __init__.py
│   ├── main.py                  # entry FastAPI, Scalar, middlewares, landing page
│   ├── config.py                # pydantic-settings (env vars)
│   ├── database.py              # engine, SessionLocal, get_db dependency
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py              # dependências compartilhadas (get_db, etc.)
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── books.py         # endpoints /books (CRUD + filtros)
│   │       ├── search.py        # endpoint /books/search/semantic
│   │       └── health.py        # endpoint /health
│   ├── models/
│   │   ├── __init__.py
│   │   └── book.py              # SQLAlchemy Book model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── book.py              # Pydantic schemas de Book
│   │   └── problem.py           # Problem Details (RFC 7807)
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── book.py              # CRUD operations
│   ├── services/
│   │   ├── __init__.py
│   │   └── book.py              # lógica de negócio (orquestra AI + Repo)
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── client.py            # wrapper OpenRouter (OpenAI SDK + base_url + retry)
│   │   ├── summary.py           # geração de resumo (prompt + parsing)
│   │   ├── embeddings.py        # gerar embedding (bge-m3) + cosine similarity
│   │   └── prompts.py           # prompts versionados
│   ├── core/
│   │   ├── __init__.py
│   │   ├── exceptions.py        # exceptions customizadas + handlers RFC 7807
│   │   ├── logging.py           # config do structlog + request_id middleware
│   │   └── version.py           # lê versão do pyproject.toml + git SHA
│   └── static/
│       └── index.html           # landing page
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── xxxx_initial.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # fixtures (test client, test db, mock OpenRouter)
│   ├── test_books_api.py        # testes dos endpoints CRUD
│   ├── test_books_repository.py # testes unitários do repository
│   ├── test_semantic_search.py  # testes de busca semântica (mock embeddings)
│   ├── test_ai_integration.py   # testes dos wrappers OpenRouter
│   ├── test_problem_details.py  # validar formato de erros
│   └── test_health.py
├── docs/
│   ├── adr/
│   │   ├── template.md
│   │   ├── 001-fastapi-over-django.md
│   │   ├── 002-uv-package-manager.md
│   │   ├── 003-fly-io-deployment.md
│   │   ├── 004-openrouter-unified-llm-gateway.md
│   │   ├── 005-scalar-over-swagger.md
│   │   ├── 006-rfc-7807-errors.md
│   │   └── 007-bge-m3-for-multilingual-embeddings.md
│   ├── diagrams/
│   │   ├── architecture.md      # mermaid: camadas
│   │   └── request-flow.md      # mermaid: fluxo de uma request
│   └── collection.json          # Postman collection
├── .devcontainer/
│   ├── devcontainer.json        # config VSCode Dev Container
│   └── post-create.sh           # comandos após criar container
├── .github/
│   ├── workflows/
│   │   ├── ci.yml               # lint + typecheck + tests + schemathesis
│   │   ├── deploy.yml           # deploy Fly.io em push para main
│   │   └── release.yml          # release-please (CHANGELOG + tags)
│   └── dependabot.yml           # auto-updates de deps
├── .pre-commit-config.yaml      # hooks: ruff, mypy, pytest (rápido)
├── .dockerignore
├── .gitignore
├── .env.example
├── Dockerfile                   # multi-stage (builder + runtime ~80 MB)
├── docker-compose.yml           # dev local
├── fly.toml                     # config do Fly.io
├── alembic.ini
├── pyproject.toml               # config do uv, ruff, mypy, pytest
├── uv.lock
├── Makefile                     # make dev, test, deploy, fmt, lint
├── CHANGELOG.md                 # gerado por release-please
├── README.md                    # badges, demo GIF, curl examples, mermaid
└── PRD.md                       # cópia deste documento
```

### 9.1 Justificativas da Estrutura

- **`app/`** como package raiz: padrão FastAPI, permite imports absolutos limpos (`from app.models import Book`)
- **Separação `models/` `schemas/` `repositories/` `services/`**: cada camada é uma pasta, não um arquivo único inchado. Escala bem ao adicionar mais entidades (usuários, empréstimos)
- **`app/ai/`** isolado: prompts, clients e lógica de LLM em um único lugar. OpenRouter como gateway já permite trocar de modelo por env var; a camada adiciona abstração extra caso queira migrar de gateway no futuro
- **`api/routers/`** em subpasta: permite agrupar routers por domínio; `main.py` fica enxuto
- **`core/`** para cross-cutting concerns: exceptions, logging, versionamento, futuramente auth/cache
- **`docs/adr/`**: Architecture Decision Records numerados e imutáveis. Cada escolha importante vira um ADR com Contexto → Decisão → Consequências
- **`docs/diagrams/`**: Mermaid renderizado pelo GitHub direto no preview
- **`.devcontainer/`**: onboarding sem fricção — clone + Reopen in Container = pronto
- **`tests/` paralelo a `app/`**: padrão pytest, não polui o código de produção

---

## 10. Estratégia de Testes

### 10.1 Pirâmide

| Nível | Ferramenta | Cobertura |
|---|---|---|
| Unit (repository, service, ai) | pytest puro | ~45% dos testes |
| Integration (API endpoints) | pytest + httpx.AsyncClient | ~45% dos testes |
| Contract (OpenAPI compliance) | Schemathesis | ~10% dos testes |
| E2E (opcional) | — | 0 |

### 10.2 Casos-chave

- **Criar livro**: sucesso, validação de campos obrigatórios, data inválida
- **Listar livros**: sem filtro, com `title`, com `author`, com ambos, paginação, ordenação
- **Buscar por ID**: sucesso, 404
- **Atualizar**: sucesso, 404, atualização parcial
- **Remover**: sucesso, 404
- **Health check**: retorna 200 com status ok

### 10.3 Infraestrutura de Teste

- **Test DB isolado**: SQLite em memória (`sqlite:///:memory:`) para cada sessão de teste
- **Fixtures**: `client` (httpx AsyncClient), `db_session` (transação revertida), `sample_book`, `mock_openrouter` (stub do client para não gastar créditos em testes)
- **Coverage**: `pytest-cov` com fail-under 90%
- **Schemathesis**: roda no CI contra a app local; gera requests aleatórias a partir do OpenAPI, valida responses contra o schema — pega divergências entre código e docs automaticamente

---

## 11. CI/CD

### 11.1 Pipeline CI (`.github/workflows/ci.yml`)

Triggers: push e PR em qualquer branch.

Jobs (em paralelo onde possível):

1. **lint**: `ruff check .` + `ruff format --check .`
2. **typecheck**: `mypy app/`
3. **test**: `pytest --cov=app --cov-fail-under=90`
4. **contract**: sobe app e roda `schemathesis run http://localhost:8000/openapi.json --checks all`
5. **security**: `pip-audit` (deps vulneráveis) + `bandit -r app/` (código)

Matrix: Python 3.12 (poderia testar 3.11 e 3.13 como stretch).

Cache do `uv` para builds rápidos (~30s).

### 11.2 Pre-commit hooks (`.pre-commit-config.yaml`)

Rodam localmente antes de cada commit — evitam CI quebrado:

- `ruff check --fix` e `ruff format`
- `mypy` nos arquivos alterados
- `pytest -x --ff` (falha rápida, só arquivos modificados)
- Validador de Conventional Commits (`commitlint`)

### 11.3 Release automation (`.github/workflows/release.yml`)

- **release-please** detecta `feat:`/`fix:` nos commits, abre PR com CHANGELOG gerado
- Merge do PR cria tag + release no GitHub automaticamente

### 11.4 Pipeline CD (`.github/workflows/deploy.yml`)

Trigger: push em `main` com CI verde.

Steps:
1. Checkout
2. Setup `flyctl`
3. `flyctl deploy --remote-only` (injeta commit SHA como build arg para o `/health`)

Secrets: `FLY_API_TOKEN`, `OPENROUTER_API_KEY` (como `flyctl secrets set`).

### 11.5 Badges no README

- Status do CI
- Cobertura de testes (Codecov ou shields.io)
- Versão do Python
- Última release (via release-please)
- License (MIT)
- Deployed on Fly.io

---

## 12. Deploy

### 12.1 Plataforma: Fly.io

**Por quê Fly.io:**
- Free tier: 3 máquinas pequenas + 3GB de volume — suficiente
- **Volume persistente nativo**: crítico para SQLite (o arquivo `.db` precisa sobreviver entre deploys)
- Deploy via `flyctl deploy` é rápido (~1min)
- TLS automático, subdomínio `*.fly.dev` grátis
- Integra bem com GitHub Actions

**Alternativas consideradas:**
- **Railway**: mais caro, bom UX mas sem free tier eterno
- **Render**: free tier tem cold start agressivo
- **Heroku**: sem free tier
- **Vercel/Netlify**: não suportam Python server-side com volume

### 12.2 Configuração (`fly.toml`)

- Região: `gru` (São Paulo) — menor latência
- Memória: 256 MB (suficiente)
- Volume mount: `/data` — arquivo SQLite vive ali
- Healthcheck: `GET /health` a cada 30s

### 12.3 Variáveis de Ambiente (produção)

| Var | Valor |
|---|---|
| `DATABASE_URL` | `sqlite:////data/library.db` |
| `LOG_LEVEL` | `INFO` |
| `ENVIRONMENT` | `production` |
| `OPENROUTER_API_KEY` | (secret) — única chave necessária para chat e embeddings |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` |
| `OPENROUTER_CHAT_MODEL` | `openai/gpt-4o-mini` — trocável sem redeploy |
| `OPENROUTER_EMBEDDING_MODEL` | `baai/bge-m3` — trocável sem redeploy |
| `OPENROUTER_APP_URL` | `https://virtual-library-api.fly.dev` — aparece no dashboard do OpenRouter |
| `OPENROUTER_APP_NAME` | `Virtual Library API` — header `X-Title` |
| `AI_FEATURES_ENABLED` | `true` — flag para desabilitar graciosamente se quota acabar |
| `GIT_SHA` | injetado no build via `flyctl deploy --build-arg GIT_SHA=$(git rev-parse HEAD)` |

---

## 13. Roadmap

Dividido em duas fases de ~7h cada. Fase 1 pode ser entregue standalone (MVP funcional); Fase 2 adiciona os diferenciais.

### Fase 1 — Fundação, CRUD e Qualidade

| Bloco | Tarefa |
|---|---|
| 0-1h | Scaffold: `uv init`, estrutura de pastas, `pyproject.toml`, `.env.example`, `.gitignore`, **Makefile** |
| 1-2h | Modelo `Book` (com `embedding` BLOB) + Alembic initial migration + schemas Pydantic |
| 2-3h | Repository + Service + Router `/books` (CRUD básico + filtros + paginação) |
| 3-4h | Tratamento de erros **RFC 7807** + **structlog** com `request_id` middleware |
| 4-5h | Testes dos endpoints CRUD (happy path + erros) + fixtures com mock OpenRouter |
| 5-6h | **Multi-stage Dockerfile** + `docker-compose.yml` + **Dev Container** (`devcontainer.json`) |
| 6-7h | **Pre-commit hooks** + **Conventional Commits** config + primeiro commit/push |

### Fase 2 — AI, CI/CD, Docs e Deploy

| Bloco | Tarefa |
|---|---|
| 0-1h | **AI Layer**: wrapper OpenRouter (chat + embeddings), geração de resumo via `gpt-4o-mini`, embeddings via `bge-m3` |
| 1-2h | Endpoint `/books/search/semantic` + recalcular embedding em create/update + testes |
| 2-3h | **Scalar UI** em `/docs` + **landing page** HTML em `/` + healthcheck rico |
| 3-4h | **CI workflow** (lint + typecheck + tests + **Schemathesis** + pip-audit) |
| 4-5h | **Fly.io** setup + deploy manual + **CD workflow** (auto-deploy em push) |
| 5-6h | **ADRs** (7 documentos) + **Mermaid diagrams** (arquitetura + request flow) |
| 6-7h | README polido (badges, demo GIF, curl examples, seção AI features) + **release-please** + **Dependabot** |

---

## 14. Relação com Outros Projetos do Portfólio

Este repo faz parte de um trio de projetos que seguem as [[../CONVENTIONS|Engineering Conventions]] compartilhadas (commits, branches, README, releases, quality bars).

| Repo | Stack principal |
|---|---|
| `virtual-library-api` (este) | FastAPI + SQLAlchemy + SQLite + OpenRouter |
| `python-tutor-chatbot` | Chainlit + Langchain + OpenRouter |
| `semantic-document-search` | FastAPI + Qdrant + OpenRouter (bge-m3) |

**OpenRouter como integração comum** nos 3 garante consistência arquitetural — mesma pasta `app/ai/`, mesmo client, mesmo padrão de secrets.

---

## 15. Riscos e Mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| Stumble no Fly.io (primeira vez) | Alto (perde tempo no dia 2) | Testar deploy ao final do dia 1 com versão mínima; ter fallback para Railway |
| Flaky tests com SQLite async | Médio | Usar `sqlite:///:memory:` + `StaticPool` ou testar síncrono |
| Cobertura < 90% | Baixo | Escrever testes junto com código, não depois |
| Escopo do README consumir muito tempo | Médio | Timebox 1h no dia 2; usar template |
| **OpenRouter fora do ar** | Alto | `tenacity` com retry exponencial (3 tentativas); flag `AI_FEATURES_ENABLED=false` desativa graciosamente; endpoints retornam 503 com `application/problem+json` |
| **Custo OpenRouter descontrolado** | Baixo | Limitar summary a 150 tokens + `gpt-4o-mini` (~$0.0005/resumo); `bge-m3` custa $0.01/M tokens; limite de spend configurado no dashboard |
| **Modelo `baai/bge-m3` depreciado ou retirado** | Baixo | Modelo via env var; `embedding_model` coluna permite detectar vetores desatualizados e rebuild |
| **Escopo dos diferenciais estoura o orçamento de tempo** | Médio | Priorizar por tier: AI features e CI/CD são must; ADRs e Mermaid podem entrar em follow-up commit |
| **Schemathesis gera edge cases difíceis** | Médio | Começar com `--hypothesis-max-examples=10` e subir gradualmente |

---

## 16. Referências

- [FastAPI docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [uv docs](https://docs.astral.sh/uv/)
- [Fly.io Python guide](https://fly.io/docs/languages-and-frameworks/python/)
- [Ruff rules](https://docs.astral.sh/ruff/rules/)
- [Scalar FastAPI integration](https://github.com/scalar/scalar/tree/main/packages/scalar_fastapi)
- [RFC 7807 Problem Details](https://datatracker.ietf.org/doc/html/rfc7807)
- [Schemathesis](https://schemathesis.readthedocs.io/)
- [release-please](https://github.com/googleapis/release-please)
- [ADR template (Michael Nygard)](https://github.com/joelparkerhenderson/architecture-decision-record)
- [Dev Containers spec](https://containers.dev/)
- [OpenRouter docs](https://openrouter.ai/docs)
- [OpenRouter embeddings](https://openrouter.ai/docs/api/reference/embeddings)
- [BAAI/bge-m3 model card](https://huggingface.co/BAAI/bge-m3)
- [MTEB leaderboard (multilingual)](https://huggingface.co/spaces/mteb/leaderboard)

---

## 17. Checklist Final de Entrega

**Core:**
- [ ] Todas as funcionalidades CRUD + busca implementadas
- [ ] Testes unitários e de integração passando
- [ ] README com setup e exemplos

**Diferenciais:**
- [ ] CI verde no GitHub (5 jobs)
- [ ] Deploy público no Fly.io funcionando
- [ ] URL pública do Scalar compartilhável
- [ ] Commits seguindo Conventional Commits
- [ ] Dev Container testado (GitHub Codespaces ou VSCode)
- [ ] Landing page em `/` funcionando
- [ ] AI features ativas em produção (resumo + busca semântica)
- [ ] 7 ADRs escritos e linkados no README
- [ ] Mermaid diagrams renderizando no GitHub
- [ ] Primeira release criada via release-please
- [ ] Dependabot configurado
- [ ] Badges: CI, coverage, Python, release, license
- [ ] Adicionar ao perfil GitHub como projeto em destaque
