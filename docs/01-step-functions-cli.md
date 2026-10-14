# 1. Entender a falha pela Step Function

Antes de rodar qualquer coisa localmente, descubra **onde** e **com qual input** a falha aconteceu.

## Conceitos

- **State machine:** a definição do fluxo (os estados e as transições).
- **Execução:** cada vez que a state machine roda. Cada uma tem um `executionArn`.
- **Histórico de eventos:** tudo que aconteceu numa execução, passo a passo.

Analogia: a execução é uma mensagem atravessando vários consumidores; o histórico é o trace dela no Datadog.

## Pelo console (comece por aqui)

Step Functions → sua state machine → execução com status **Failed** → clique no estado vermelho no grafo. Você vê o **input**, o **output** e o **erro** do estado.

## Pelo CLI

### Listar execuções que falharam
```bash
aws stepfunctions list-executions \
  --state-machine-arn <arn-da-state-machine> \
  --status-filter FAILED \
  --max-items 5
```
Retorna o `executionArn` de cada execução.

### Histórico de uma execução
```bash
aws stepfunctions get-execution-history \
  --execution-arn <arn-da-execucao> \
  --reverse-order
```
`--reverse-order` mostra do fim pro começo, com o erro primeiro.

Eventos que importam:

| Evento | O que é |
|---|---|
| `LambdaFunctionFailed` / `TaskFailed` | o erro |
| `LambdaFunctionScheduled` / `TaskScheduled` | o **input** que a Lambda recebeu (vira o seu `event.json`) |
| `ExecutionFailed` | resumo final da falha |

Extrair só o input da Lambda com `jq`:
```bash
aws stepfunctions get-execution-history --execution-arn <arn> \
  | jq -r '.events[] | select(.type=="TaskScheduled") | .taskScheduledEventDetails.parameters' \
  | jq '.Payload' > events/falha.json
```
O formato exato depende de como o estado chama a Lambda. Confira o JSON antes de usar.

### Logs da Lambda (CloudWatch)
```bash
aws logs tail /aws/lambda/<nome-da-lambda> --since 1d --follow
```
Mostra o stack trace completo, que o histórico às vezes resume.

## Cuidados

- Use só execuções de **dev/hom**. Nunca copie payload de produção com dado de cliente para a sua máquina ou para este repo.
- A Step Function pode acessar o DynamoDB **direto** (service integration), sem Lambda. Veja no grafo quem faz o acesso.
