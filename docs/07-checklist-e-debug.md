# 7. Checklist completo e debug no VS Code

## Checklist antes de rodar

| # | Item | Como conferir |
|---|---|---|
| 1 | Runtime e handler | `aws lambda get-function-configuration --function-name <nome> --query '[Runtime,Handler]'` |
| 2 | Python na mesma versão do runtime | `python3 --version`; sem sudo, use `uv python install 3.12` |
| 3 | venv | `python3 -m venv .venv && source .venv/bin/activate` |
| 4 | Dependências | `pip install -r requirements.txt boto3 pytest` (boto3 vem no runtime da AWS, não na sua máquina) |
| 5 | Layers | `--query Layers`; baixe com `aws lambda get-layer-version-by-arn --arn <arn> --query Content.Location` e extraia |
| 6 | Credencial | `aws sts get-caller-identity` (se SSO: `aws sso login`) |
| 7 | Região | `AWS_REGION` igual à da Lambda |
| 8 | Env vars | `--query Environment` → `.env` (não versionado) |
| 9 | Proxy / certificado | `scripts/diagnostico.sh` |
| 10 | Evento | input da execução que falhou (doc 01) → `events/falha.json` |

O `Handler` `src/app.handler` vira `--path src --module app --handler handler`.

## Extensões

| Extensão | Precisa? | Para quê |
|---|---|---|
| Python | Sim | interpretador, venv, testes |
| Python Debugger (debugpy) | Sim | breakpoints e F5 |
| Pylance | Vem junto | autocomplete, tipos, navegação |
| AWS Toolkit | Opcional | ver logs, Step Functions, Dynamo pela IDE |

Não use o "Run/Debug locally" do AWS Toolkit sem Docker.

## Debug

1. `Ctrl+Shift+P` → **Python: Select Interpreter** → escolha a `.venv`.
2. Copie `.env.example` → `.env` e preencha.
3. Ajuste `args` no `.vscode/launch.json` (módulo, handler, evento).
4. Breakpoint na primeira linha do handler → **F5** → "Lambda: rodar local (debug)".
5. No painel **Breakpoints**, marque **Raised Exceptions**: o debugger para exatamente onde o erro nasce, não onde ele é tratado.
6. Inspecione `event` e variáveis no painel **Variables** ou no **Debug Console**.
7. `justMyCode: false` deixa você entrar no código do boto3 com F11.

Para o erro de conexão: rode "Lambda: rodar local + log AWS". O log do botocore mostra a URL do endpoint, a região e se passou pelo proxy.
