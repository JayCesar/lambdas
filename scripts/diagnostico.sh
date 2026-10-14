#!/usr/bin/env bash
# Diagnóstico de conexão local -> AWS (CLI vs Python), sem sudo.
# Uso: export AWS_PROFILE=dev AWS_REGION=sa-east-1 && ./scripts/diagnostico.sh

echo "== Perfil e região"
echo "AWS_PROFILE=${AWS_PROFILE:-<vazio>}  AWS_REGION=${AWS_REGION:-<vazio>}"

echo; echo "== Variáveis de proxy e certificado"
env | grep -iE '^(https?_proxy|no_proxy|aws_ca_bundle|requests_ca_bundle|ssl_cert_file)=' || echo "(nenhuma)"

echo; echo "== Identidade (credencial válida?)"
aws sts get-caller-identity --query Arn --output text 2>&1 | sed 's/[0-9]\{12\}/<account>/g'

echo; echo "== CLI -> DynamoDB"
if aws dynamodb list-tables --max-items 1 >/dev/null 2>&1; then
  echo "OK"
else
  echo "FALHOU:"; aws dynamodb list-tables --max-items 1 2>&1 | tail -2
fi

echo; echo "== Python (boto3) -> DynamoDB"
python3 - <<'PY'
try:
    import boto3
    boto3.client("dynamodb").list_tables(Limit=1)
    print("OK")
except Exception as e:
    print(f"FALHOU: {type(e).__name__}: {e}")
PY

echo; echo "== Leitura do resultado"
echo "CLI ok + Python falha -> proxy/certificado não chegam no Python"
echo "Os dois ok             -> a Lambda acessa outra coisa (VPC/API interna)"
echo "Os dois falham         -> região ou credencial"
