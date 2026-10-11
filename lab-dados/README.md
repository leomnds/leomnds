# lab-dados

Meu laboratório de dados local: PostgreSQL, n8n e Airflow rodando no Docker (WSL 2). Montei para estudar pipelines de ponta a ponta sem depender de nuvem, e deixei tudo no repositório para conseguir recriar o ambiente do zero com um comando.

O primeiro pipeline é o `bcb_pix_medalhao`, que baixa os dados abertos de Pix por município do Banco Central e carrega em três camadas (bronze, silver e gold) no Postgres.

## O que roda aqui

- **PostgreSQL 18** em `localhost:5432`, já com os schemas `bronze`, `silver` e `gold`
- **n8n 2.42.6** em http://localhost:5678, para automações
- **Airflow 3.3.2** em http://localhost:8080, para orquestrar os pipelines

As versões estão fixas nos arquivos do Docker, para o ambiente sair igual toda vez.

## Estrutura

```
lab-dados/
├── docker-compose.yml          PostgreSQL + n8n
├── .env.example                modelo do arquivo de senhas
├── postgres/init/              SQL que cria os schemas bronze, silver e gold
├── n8n/workflows/              workflows do n8n exportados em JSON
├── airflow/
│   ├── docker-compose.yaml            Airflow (arquivo oficial, porta presa ao computador)
│   ├── docker-compose.override.yaml   liga o worker à rede do laboratório
│   ├── .env.example                   modelo das variáveis do Airflow
│   └── dags/bcb_pix_medalhao.py       pipeline Pix por município
├── scripts/
│   ├── setup.sh                monta tudo do zero
│   ├── backup.sh               backup do banco e do n8n
│   └── restore.sh              restaura um backup
└── windows/
    ├── iniciar-airflow.ps1     abre o Airflow (sobe o que estiver parado)
    └── criar-atalho.ps1        cria o atalho "Airflow" na área de trabalho
```

Senhas e chaves ficam em arquivos `.env`, que não vão para o Git. O `setup.sh` gera os dois sozinho.

## Recriar do zero

### 1. Preparar o Windows (uma vez só)

1. Em um PowerShell como administrador: `wsl --install`. Reinicie o computador. Na volta, o Ubuntu abre e pede um usuário e uma senha (são só do Linux).
2. Instale o **Docker Desktop** pelo site docker.com, com a opção do **WSL 2** marcada.
3. No Docker Desktop, em **Settings > Resources > WSL Integration**, ative o **Ubuntu**.
4. No terminal do Ubuntu, teste com `docker run hello-world`.

### 2. Baixar e subir

Rodo tudo pelo terminal do Ubuntu e deixo o projeto dentro do disco do Linux, porque rodar a partir de `C:\` (`/mnt/c`) é bem mais lento para o Airflow.

```bash
mkdir -p ~/projetos && cd ~/projetos
git clone https://github.com/leomnds/leomnds.git
cd leomnds/lab-dados
./scripts/setup.sh
```

O `setup.sh` faz, nesta ordem:

1. cria o `.env` (senha aleatória do PostgreSQL) e o `airflow/.env` (chave Fernet nova)
2. sobe PostgreSQL e n8n
3. inicializa e sobe o Airflow
4. espera o Airflow responder
5. cria a conexão `lab_postgres` no Airflow, lendo usuário, banco e senha do `.env`

Dá para rodar de novo quando quiser: o que já existe é mantido. A primeira vez baixa as imagens e leva alguns minutos. O Airflow precisa de pelo menos 4 GB de memória no Docker.

### 3. Carregar os dados

No Airflow (usuário `airflow`, senha `airflow`), abra o DAG `bcb_pix_medalhao` e clique em Trigger, informando o mês (`ano_mes`, formato AAAAMM, por exemplo `202512`).

## Pipeline: Pix por município

Fonte: API de dados abertos do Pix do BC (Olinda), recurso `TransacoesPixPorMunicipio`.

| Camada | Tabela | O que tem |
|---|---|---|
| bronze | `bronze.pix_municipio_raw` | JSON bruto, do jeito que veio da API |
| silver | `silver.pix_municipio` | colunas tipadas, uma linha por município e mês |
| gold | `gold.pix_uf_mes` | valor, quantidade, ticket médio e % PJ por estado e mês |

Cada execução processa um mês. Se o `ano_mes` não for informado, ele pega dois meses antes da data lógica, por causa do prazo de publicação do BC. Reprocessar um mês apaga e regrava, então não duplica.

Antes da gold tem uma tarefa de qualidade que barra a carga se o mês vier incompleto: menos de 5.000 municípios, número de estados diferente de 27 ou algum valor negativo.

### Coisas que aprendi com essa API

- Ela devolve erro 500 com `$skip` e 400 com `$filter`, então não tem como paginar nem filtrar. A saída foi pedir tudo de uma vez com um `$top` alto e separar o mês no Python.
- O `DataBase` não filtra o mês, ele é o mês inicial. A resposta traz aquele mês e todos os seguintes.
- Vem uma linha `NAO INFORMADO` sem código de estado. Ela não conta como UF na validação.

## Acessar os dados

No DBeaver, conexão PostgreSQL com host `localhost`, porta `5432`, banco `lab`, usuário `lab` e a senha que está no `.env`. De dentro de um workflow do n8n, o host é `postgres` (o nome do serviço).

```sql
SELECT estado, valor_pago, qtd_transacoes, ticket_medio, pct_valor_pj
FROM gold.pix_uf_mes
WHERE ano_mes = '202512'
ORDER BY valor_pago DESC;
```

## Dia a dia

```bash
docker compose up -d       # sobe PostgreSQL e n8n (dentro de airflow/ sobe o Airflow)
docker compose stop        # para sem apagar nada
docker compose down        # remove os containers, os dados ficam nos volumes
docker compose logs -f n8n # log de um serviço
```

Cuidado com `docker compose down -v`: apaga os volumes, ou seja, o banco e os dados do n8n.

### Backup

```bash
./scripts/backup.sh
```

Grava em `backups/AAAAMMDD-HHMMSS/` o dump do banco e o volume do n8n, e exporta os workflows do n8n para `n8n/workflows/` (esses sim vão para o Git). A pasta `backups/` fica fora do Git, porque o volume do n8n guarda credenciais.

Para voltar um backup (substitui o banco e o n8n atuais, e pede confirmação):

```bash
./scripts/restore.sh backups/AAAAMMDD-HHMMSS
```

Os dados do Pix também dá para refazer a qualquer momento disparando o DAG de novo.

### Atalho do Airflow no Windows

No PowerShell, dentro de `windows/`:

```powershell
.\criar-atalho.ps1 -PastaWsl ~/projetos/leomnds/lab-dados
```

Cria o atalho **Airflow** na área de trabalho. Ao clicar, ele abre o Airflow; se estiver parado, abre o Docker Desktop, sobe os containers e só então abre o navegador. O `-PastaWsl` é a pasta do `lab-dados` dentro do Ubuntu.

## Se der problema

- **`./scripts/setup.sh: Permission denied`:** rode com `bash scripts/setup.sh`.
- **`bad interpreter` ou `\r` no erro:** o Git do Windows converteu os scripts para CRLF. O `.gitattributes` evita isso em clones novos; num clone antigo, `git add --renormalize .`.
- **Porta 5432 ocupada:** já tem um Postgres instalado no Windows. Trocar a porta no `docker-compose.yml` para `"127.0.0.1:5433:5432"`.
- **Airflow travando:** é memória. Parar o n8n e o Postgres do laboratório ou aumentar a memória do WSL no `.wslconfig`.
- **Schemas não apareceram:** o script de `postgres/init` só roda na primeira criação do banco. Se o volume já existia, criar os schemas na mão.
