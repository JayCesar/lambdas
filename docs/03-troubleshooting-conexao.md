# 3. Troubleshooting: "não foi possível conectar com servidor"

Cenário: rodando sem Docker, apontando para a AWS com um perfil do AWS CLI.

## Teste que separa as hipóteses

```bash
export AWS_PROFILE=dev AWS_REGION=<regiao>
aws dynamodb list-tables
python -c "import boto3; print(boto3.client('dynamodb').list_tables())"
```
Ou rode `./scripts/diagnostico.sh`.

| Resultado | Diagnóstico | Ação |
|---|---|---|
| CLI ok, Python falha | Python não usa o proxy ou o certificado que o CLI usa | `env \| grep -i proxy`, `cat ~/.aws/config`; replicar `HTTPS_PROXY` e `AWS_CA_BUNDLE` |
| Os dois ok | Rede ok. A Lambda acessa **outra coisa** | Procurar URLs e endpoints no código e nas env vars |
| Os dois falham | Região ou credencial | Conferir região; se for SSO, `aws sso login` |

## Pelo nome da exceção

| Exceção | Causa provável |
|---|---|
| `Cannot connect to the Docker daemon` | Rodou via SAM/Toolkit sem Docker |
| `Connection refused` em `localhost` | Código aponta para DynamoDB Local (`endpoint_url`) |
| `EndpointConnectionError` / `ConnectTimeout` | Proxy, região ou recurso só acessível na VPC |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Proxy intercepta SSL; configurar `AWS_CA_BUNDLE` |
| `AccessDeniedException` | Perfil sem permissão na tabela ou recurso |
| `ExpiredToken` | Sessão expirada; renovar credencial |

## Procurar o que a Lambda acessa

```bash
grep -rn "endpoint_url\|localhost\|8000" .
grep -rn "http\|endpoint\|url\|host" --include=*.py . | grep -v test
```
Se aparecer uma URL interna ou um endpoint `vpce-...`, ela **só é alcançável de dentro da VPC**. Mocke no teste local e valide em dev.

## Lembrete

O DynamoDB tem endpoint público da AWS: com credencial, região e proxy corretos, ele é acessível da sua máquina. Aurora/RDS e APIs internas geralmente não são.
