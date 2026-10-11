# lab-dados

Meu laboratório de dados local: PostgreSQL, n8n e Airflow rodando no Docker (WSL 2). Montei para estudar pipelines de ponta a ponta sem depender de nuvem.

O primeiro pipeline é o `bcb_pix_medalhao`, que baixa os dados abertos de Pix por município do Banco Central e carrega em três camadas (bronze, silver e gold) no Postgres.

## O que roda aqui

- **PostgreSQL 18** em `localhost:5432`, já com os schemas `bronze`, `silver` e `gold`
- **n8n** em http://localhost:5678, para automações
- **Airflow 3.3.2** em http://localhost:8080, para orquestrar os pipelines

O Postgres e o n8n sobem pelo `docker-compose.yml` da raiz. O Airflow fica separado, na pasta `airflow/`, porque é bem mais pesado e eu só subo quando vou usar.

## Como subir

Precisa de Docker Desktop com WSL 2. Rodo tudo pelo terminal do Ubuntu, com o projeto dentro do Linux (em `C:\` fica muito lento).

```bash
git clone https://github.com/leomnds/leomnds.git
cd leomnds/lab-dados
cp .env.example .env    # trocar a senha
docker compose up -d
```

No DBeaver a conexão é `localhost:5432`, com usuário, senha e banco do `.env`. De dentro do n8n o host é `postgres`.

### Airflow

Uso o `docker-compose.yaml` oficial da versão 3.3.2. A única mudança foi prender a porta 8080 em `127.0.0.1`. Precisa de pelo menos 4 GB de memória no Docker.

```bash
cd airflow
mkdir -p ./logs ./plugins ./config
echo "AIRFLOW_UID=$(id -u)" > .env
docker compose up airflow-init
docker compose up -d
```

Login padrão: `airflow` / `airflow`.

Depois da primeira subida, gero a Fernet key, que é o que criptografa as senhas das conexões:

```bash
echo "FERNET_KEY=$(docker compose exec -T airflow-scheduler python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" >> .env
docker compose up -d
```

O `docker-compose.override.yaml` coloca o worker na mesma rede do laboratório, então os DAGs enxergam o banco pelo host `lab-postgres`. Por isso o Postgres tem que estar no ar antes do Airflow. A conexão `lab_postgres` é criada uma vez, lendo os dados do `.env` da raiz:

```bash
docker compose exec airflow-scheduler airflow connections add lab_postgres \
  --conn-type postgres --conn-host lab-postgres --conn-port 5432 \
  --conn-login "$(grep POSTGRES_USER ../.env | cut -d= -f2)" \
  --conn-schema "$(grep POSTGRES_DB ../.env | cut -d= -f2)" \
  --conn-password "$(grep POSTGRES_PASSWORD ../.env | cut -d= -f2)"
```

## Pipeline: Pix por município

Fonte: API de dados abertos do Pix do BC (Olinda), recurso `TransacoesPixPorMunicipio`.

| Camada | Tabela | O que tem |
|---|---|---|
| bronze | `bronze.pix_municipio_raw` | JSON bruto, do jeito que veio da API |
| silver | `silver.pix_municipio` | colunas tipadas, uma linha por município e mês |
| gold | `gold.pix_uf_mes` | valor, quantidade, ticket médio e % PJ por estado e mês |

Cada execução processa um mês. Dá para informar o `ano_mes` (AAAAMM) no Trigger; em branco, ele pega dois meses antes da data lógica, por causa do prazo de publicação do BC. Reprocessar um mês apaga e regrava, então não duplica.

Antes da gold tem uma tarefa de qualidade que barra a carga se o mês vier incompleto: menos de 5.000 municípios, número de estados diferente de 27 ou algum valor negativo.

### Coisas que aprendi com essa API

- Ela devolve erro 500 com `$skip` e 400 com `$filter`, então não tem como paginar nem filtrar. A saída foi pedir tudo de uma vez com um `$top` alto e separar o mês no Python.
- O `DataBase` não filtra o mês, ele é o mês inicial. A resposta traz aquele mês e todos os seguintes.
- Vem uma linha `NAO INFORMADO` sem código de estado. Ela não conta como UF na validação.

## Comandos do dia a dia

```bash
docker compose up -d       # sobe
docker compose stop        # para sem apagar nada
docker compose down        # remove os containers, os dados ficam nos volumes
docker compose logs -f n8n # log de um serviço
```

Cuidado com `docker compose down -v`: apaga os volumes, ou seja, o banco e os workflows do n8n.

## Se der problema

- **Porta 5432 ocupada:** já tem um Postgres instalado no Windows. Trocar a porta no `docker-compose.yml` para `"127.0.0.1:5433:5432"`.
- **Airflow travando:** é memória. Parar o n8n e o Postgres do laboratório ou aumentar a memória do WSL no `.wslconfig`.
- **Schemas não apareceram:** o script de `postgres/init` só roda na primeira criação do banco. Se o volume já existia, criar os schemas na mão.
