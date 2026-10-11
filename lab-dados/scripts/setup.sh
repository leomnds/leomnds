#!/usr/bin/env bash
# Monta o laboratório do zero: gera as senhas, sobe PostgreSQL, n8n e Airflow e cria a
# conexão do Airflow com o banco. Pode rodar de novo sem estragar nada: o que já existe é mantido.
#
#   ./scripts/setup.sh              faz tudo
#   ./scripts/setup.sh --apenas-env só gera os arquivos .env (sem subir nada)
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"

etapa() { printf '\n==> %s\n' "$*"; }
falha() { printf '\nERRO: %s\n' "$*" >&2; exit 1; }

senha_aleatoria() { openssl rand -hex 16; }
# Chave Fernet do Airflow: 32 bytes aleatórios em base64 "url-safe"
fernet_aleatoria() { openssl rand -base64 32 | tr '+/' '-_'; }

etapa "Arquivos de senha"
if [ ! -f .env ]; then
  cp .env.example .env
  sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(senha_aleatoria)|" .env
  echo ".env criado, com uma senha aleatória para o PostgreSQL"
else
  echo ".env já existe, mantido"
fi

if [ ! -f airflow/.env ]; then
  printf 'AIRFLOW_UID=%s\nFERNET_KEY=%s\n' "$(id -u)" "$(fernet_aleatoria)" > airflow/.env
  echo "airflow/.env criado, com uma chave Fernet nova"
else
  echo "airflow/.env já existe, mantido"
fi
mkdir -p airflow/logs airflow/plugins airflow/config

[ "${1:-}" = "--apenas-env" ] && exit 0

etapa "Docker"
command -v docker >/dev/null || falha "Docker não encontrado. Instale o Docker Desktop e ative a integração com o WSL (veja o README)."
docker info >/dev/null 2>&1 || falha "O Docker não está respondendo. Abra o Docker Desktop e tente de novo."
docker compose version >/dev/null 2>&1 || falha "O plugin 'docker compose' não foi encontrado."

# Usuário, banco e senha do PostgreSQL, usados na conexão do Airflow
set -a
. ./.env
set +a

etapa "PostgreSQL e n8n"
docker compose up -d --wait

etapa "Airflow"
(
  cd airflow
  docker compose up airflow-init
  docker compose up -d
)

etapa "Esperando o Airflow responder"
for _ in $(seq 1 60); do
  if curl -fs http://localhost:8080/api/v2/monitor/health >/dev/null 2>&1; then
    pronto=1
    break
  fi
  sleep 5
done
[ "${pronto:-0}" = 1 ] || falha "O Airflow não respondeu em 5 minutos. Veja: cd airflow && docker compose logs --tail 50"

etapa "Conexão lab_postgres no Airflow"
(
  cd airflow
  if docker compose exec -T airflow-scheduler airflow connections get lab_postgres >/dev/null 2>&1; then
    echo "a conexão já existe, mantida"
  else
    docker compose exec -T airflow-scheduler airflow connections add lab_postgres \
      --conn-type postgres --conn-host lab-postgres --conn-port 5432 \
      --conn-login "$POSTGRES_USER" --conn-schema "$POSTGRES_DB" \
      --conn-password "$POSTGRES_PASSWORD"
  fi
)

cat <<FIM

Pronto.

  Airflow     http://localhost:8080   (usuário airflow, senha airflow)
  n8n         http://localhost:5678   (crie a conta de dono na primeira vez)
  PostgreSQL  localhost:5432          (banco ${POSTGRES_DB}, usuário ${POSTGRES_USER}, senha no arquivo .env)

Para carregar os dados do Pix: no Airflow, abra o DAG bcb_pix_medalhao e clique em Trigger
(informe o mês no formato AAAAMM, por exemplo 202512).
FIM
