# Lambda Local Playbook

Guia prático para investigar, rodar localmente e corrigir uma AWS Lambda que roda dentro de uma Step Function e usa DynamoDB, a partir de uma máquina corporativa (Linux sem sudo, atrás de proxy, sem Docker).

> ⚠️ Este repositório é **genérico**. Não commite código, ARNs, account IDs, nomes de tabela, payloads ou logs do trabalho aqui.

## Ordem recomendada

0. [**Fundamentos (comece aqui)**](docs/00-fundamentos.md): Lambda, Step Functions, IAM, observabilidade, fluxo de correção, segurança e armadilhas.
1. [Entender a falha pela Step Function](docs/01-step-functions-cli.md): achar a execução que falhou e o input da Lambda.
2. [Rodar a Lambda localmente](docs/02-rodar-lambda-local.md): chamar o handler direto, sem SAM e sem Docker.
3. [Troubleshooting de conexão](docs/03-troubleshooting-conexao.md): o erro "não foi possível conectar com servidor".
4. [DynamoDB em 5 minutos](docs/04-dynamodb.md): conceitos e comandos de acesso.
5. [Aurora vs DynamoDB](docs/05-aurora-vs-dynamo.md): quando usar cada um.
6. [Posicionamento: pedir ajuda bem](docs/06-posicionamento.md): como comunicar o bloqueio sem soar perdido.
7. [Checklist completo e debug no VS Code](docs/07-checklist-e-debug.md): pré-requisitos, extensões, breakpoints.

## Estrutura

```
docs/        guias
scripts/     run_local.py (invoca o handler) e diagnostico.sh (testes de conexão)
events/      eventos de exemplo (use só dados fictícios ou de dev/hom sanitizados)
```

## Uso rápido

```bash
export AWS_PROFILE=dev AWS_REGION=sa-east-1   # ajuste
./scripts/diagnostico.sh                      # rede, credencial, proxy
python scripts/run_local.py events/exemplo.json --module app --handler handler
```

## Ferramenta

VS Code com as extensões **Python** e **AWS Toolkit** é suficiente. Evite o "Run/Debug locally" do Toolkit sem Docker, porque ele usa SAM + Docker por baixo. Prefira o terminal com o `run_local.py`.
