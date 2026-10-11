#!/usr/bin/env bash
# Restaura um backup feito pelo backup.sh. SUBSTITUI o conteúdo atual do banco e do n8n.
#
#   ./scripts/restore.sh backups/20261011-163000
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"

ORIGEM="${1:-}"
[ -n "$ORIGEM" ] && [ -f "$ORIGEM/banco.dump" ] || { echo "Uso: $0 backups/AAAAMMDD-HHMMSS" >&2; exit 1; }

set -a
. ./.env
set +a

echo "Isso vai SUBSTITUIR o banco '$POSTGRES_DB' e os dados do n8n pelo backup $ORIGEM."
read -r -p "Digite 'sim' para continuar: " resposta
[ "$resposta" = "sim" ] || { echo "Cancelado."; exit 1; }

echo "==> Banco ${POSTGRES_DB}"
docker exec -i lab-postgres pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner < "$ORIGEM/banco.dump"

if [ -f "$ORIGEM/n8n_dados.tgz" ]; then
  echo "==> Dados do n8n"
  docker compose stop n8n
  docker run --rm -v lab-dados_n8n_data:/dados -v "$RAIZ/$ORIGEM:/backup:ro" \
    --entrypoint sh postgres:18 -c 'rm -rf /dados/* /dados/.[!.]* 2>/dev/null; tar xzf /backup/n8n_dados.tgz -C /dados'
  docker compose start n8n
fi

echo "Restaurado."
