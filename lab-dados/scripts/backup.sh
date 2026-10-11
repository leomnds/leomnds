#!/usr/bin/env bash
# Faz o backup do que não está no Git: o banco do laboratório e os dados do n8n.
# Também exporta os workflows do n8n para n8n/workflows/ (JSON, esse sim vai para o Git).
#
# Os backups ficam em backups/AAAAMMDD-HHMMSS/ (a pasta está no .gitignore, porque o
# volume do n8n guarda credenciais e a chave que as criptografa).
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"

set -a
. ./.env
set +a

DESTINO="backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$DESTINO"

echo "==> Banco ${POSTGRES_DB}"
docker exec lab-postgres pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB" > "$DESTINO/banco.dump"

echo "==> Dados do n8n (volume inteiro)"
docker run --rm -v lab-dados_n8n_data:/dados:ro -v "$RAIZ/$DESTINO:/backup" \
  --entrypoint tar postgres:18 czf /backup/n8n_dados.tgz -C /dados .

echo "==> Workflows do n8n para n8n/workflows/"
mkdir -p n8n/workflows
if saida=$(docker exec lab-n8n sh -c 'rm -rf /tmp/exportacao && mkdir /tmp/exportacao && n8n export:workflow --all --separate --output=/tmp/exportacao/' 2>&1); then
  docker cp lab-n8n:/tmp/exportacao/. n8n/workflows/
elif ! grep -q 'No workflows found' <<< "$saida"; then
  # o n8n sai com erro quando ainda não existe nenhum workflow; qualquer outro erro é de verdade
  echo "$saida" >&2
  exit 1
fi
docker exec lab-n8n rm -rf /tmp/exportacao
echo "$(find n8n/workflows -name '*.json' | wc -l) workflow(s) exportado(s)"

echo
echo "Backup em $DESTINO:"
ls -lh "$DESTINO" | tail -n +2
