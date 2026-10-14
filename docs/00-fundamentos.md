# 0. Fundamentos: o que você precisa saber antes de mexer

Guia para quem vai corrigir ou evoluir uma Lambda que roda dentro de uma Step Function e usa DynamoDB, num ambiente de banco. Leia uma vez inteiro; depois use como consulta.

---

## Parte 1: AWS Lambda

### O modelo mental

Uma Lambda é **uma função que a AWS executa quando um evento chega**. Você não gerencia servidor; paga por invocação e por tempo de execução.

```
evento (JSON) ──► handler(event, context) ──► retorno (JSON) ou exceção
```

- **`event`:** o JSON de entrada. Quem define o formato é quem chama: a Step Function, o SQS, o API Gateway etc.
- **`context`:** metadados da execução (`aws_request_id`, tempo restante, nome da função).
- **Retorno:** numa Step Function, vira o output do estado. **Exceção:** vira um erro que a Step Function pode tratar.

### Configurações que mudam o comportamento

| Configuração | O que é | Por que importa |
|---|---|---|
| **Runtime** | Linguagem e versão (ex.: `python3.12`) | Use a mesma versão localmente |
| **Handler** | `arquivo.funcao` | É o ponto de entrada |
| **Memória** | 128 MB a 10 GB; CPU escala junto | Lambda lenta às vezes é falta de memória |
| **Timeout** | Até 15 min | Estourou → `Task timed out` |
| **Env vars** | Configuração (nome da tabela, flags) | Faltando localmente → erro "misterioso" |
| **Layers** | Pacotes de dependências compartilhadas | Faltando localmente → `ModuleNotFoundError` |
| **Role (IAM)** | Permissões da função | `AccessDenied` = role sem permissão |
| **VPC** | Se a função roda dentro da rede privada | Acessa RDS/APIs internas; da sua máquina, não |

Ver tudo de uma vez:
```bash
aws lambda get-function-configuration --function-name <nome>
```

### Ciclo de vida e cold start

1. **Cold start:** a AWS cria um ambiente novo, carrega o código e roda o que está **fora** do handler (imports, criação de clients).
2. **Warm:** invocações seguintes reutilizam o ambiente; só o handler roda.

Consequências práticas:
- Crie clients do boto3 **fora** do handler (são reaproveitados).
- **Não guarde estado** em variáveis globais achando que ele persiste ou que é exclusivo de uma execução. O ambiente pode ser reutilizado ou descartado a qualquer momento.

### Concorrência e reexecução

- Várias invocações rodam **em paralelo**, em ambientes separados.
- A mesma entrada pode ser processada **mais de uma vez** (retry da Step Function, reentrega de fila).
- Portanto: **toda Lambda que escreve precisa ser idempotente.** É o mesmo conceito de consumidor de fila que você já conhece. No Dynamo, isso costuma ser feito com `ConditionExpression`.

---

## Parte 2: AWS Step Functions

### O modelo mental

Uma Step Function é uma **máquina de estados** declarada em JSON/YAML (Amazon States Language). Ela orquestra passos: chama Lambdas, decide caminhos, repete em caso de erro e guarda o histórico de tudo.

Pense nela como o **orquestrador** de uma saga: ela sabe a ordem dos passos e o que fazer quando um falha. As Lambdas só fazem a sua parte.

### Tipos de estado

| Estado | Faz o quê |
|---|---|
| **Task** | Executa trabalho: chama Lambda ou um serviço AWS direto (Dynamo, SQS, SNS…) |
| **Choice** | `if/else` baseado no JSON |
| **Map** | Loop: processa uma lista, item a item ou em paralelo |
| **Parallel** | Executa ramos ao mesmo tempo |
| **Wait** | Espera um tempo ou até uma data |
| **Pass** | Transforma o JSON sem chamar nada |
| **Succeed / Fail** | Termina a execução |

### Como o JSON flui (onde muito bug mora)

Cada estado recebe um input, pode filtrar ou transformar, e passa um output adiante:

| Campo | Para quê |
|---|---|
| `InputPath` | Seleciona parte do input |
| `Parameters` | Monta o payload enviado à Task |
| `ResultSelector` | Filtra o resultado da Task |
| `ResultPath` | Onde o resultado é colocado no JSON (pode **substituir** o input inteiro) |
| `OutputPath` | Seleciona o que segue para o próximo estado |

Clássico: a Lambda funciona, mas o próximo estado quebra porque o `ResultPath` sobrescreveu um campo que ele precisava. **Sempre compare o input e o output de cada estado no console.**

Na versão nova da linguagem (JSONata), esses campos são substituídos por `Arguments` e `Output`. Veja qual a sua state machine usa.

### Tratamento de erro: Retry e Catch

```json
"Retry": [{
  "ErrorEquals": ["Lambda.ServiceException", "Lambda.TooManyRequestsException"],
  "IntervalSeconds": 2, "MaxAttempts": 3, "BackoffRate": 2
}],
"Catch": [{
  "ErrorEquals": ["States.ALL"],
  "ResultPath": "$.erro",
  "Next": "TratarFalha"
}]
```

- **Retry:** tenta de novo (com backoff). Por isso a idempotência importa.
- **Catch:** desvia para um estado de tratamento, como uma DLQ do fluxo.
- Erros comuns: `States.TaskFailed`, `States.Timeout`, `Lambda.Unknown` (a Lambda morreu, ex.: falta de memória) e o **nome da exceção** que a sua Lambda lançou.

Uma consequência útil: lançar exceções com nomes específicos (`PedidoNaoEncontrado`) permite que a Step Function trate cada caso de forma diferente.

### Standard vs Express

| | Standard | Express |
|---|---|---|
| Duração | Até 1 ano | Até 5 min |
| Semântica | Exactly-once por estado | At-least-once |
| Histórico | Completo no console | Só em CloudWatch Logs |
| Uso | Workflows de negócio | Alto volume, curto |

Se for Express, o histórico de execução fica no CloudWatch Logs, não no console da Step Function.

---

## Parte 3: DynamoDB (resumo)

Detalhes em [04](04-dynamodb.md) e [05](05-aurora-vs-dynamo.md). O mínimo:

- Chave-valor: PK obrigatória, SK opcional.
- **Query** por chave = bom. **Scan** = evite.
- Modele pelos padrões de acesso.
- Escrita condicional = idempotência.
- Comece sempre por `aws dynamodb describe-table`.

---

## Parte 4: IAM em 2 minutos

- **Quem** (principal: você, a role da Lambda) pode fazer **o quê** (ação: `dynamodb:GetItem`) em **qual recurso** (ARN da tabela).
- Localmente você usa **as suas permissões** (o perfil do CLI), não as da role da Lambda. Algo pode funcionar na sua máquina e falhar na AWS, ou o contrário.
- `AccessDenied` sempre diz qual ação foi negada. Leia a mensagem inteira.
- Princípio do menor privilégio: cada role só com o que precisa.

---

## Parte 5: Observabilidade

| Ferramenta | Para quê |
|---|---|
| **CloudWatch Logs** | Tudo que a Lambda imprime; um log group por função |
| **Histórico da Step Function** | Input, output e erro de cada estado |
| **CloudWatch Metrics** | Invocações, erros, duração, throttles |
| **X-Ray** (se ativado) | Trace ponta a ponta: quanto tempo cada chamada levou |

Boas práticas que você pode trazer como contribuição:
- **Log estruturado** (JSON) com um **id de correlação** (ex.: `pedidoId` e `aws_request_id`) em toda linha.
- Logar **entrada e decisão**, nunca dado sensível (CPF, conta, token).
- Erro com contexto: `"falha ao buscar pedido" + pedidoId`, não só `"erro"`.

Consultar logs:
```bash
aws logs tail /aws/lambda/<nome> --since 1h --follow
aws logs filter-log-events --log-group-name /aws/lambda/<nome> --filter-pattern "ERROR"
```

---

## Parte 6: O fluxo de uma correção

1. **Entender o bug:** execução que falhou → estado vermelho → input, erro, logs. Escreva em uma frase o que acontece e o que deveria acontecer.
2. **Reproduzir:** evento real de dev/hom → `run_local.py` ou um teste.
3. **Teste que falha** (red), reproduzindo o bug.
4. **Corrigir** com a menor mudança que resolve (green). Refatore só se ajudar a entender.
5. **Pensar nos efeitos colaterais:** a correção continua idempotente? Muda o formato do output (quebra o próximo estado)? Muda permissão (IAM)?
6. **PR** com descrição clara (template abaixo).
7. **Deploy em dev** → reexecutar a Step Function com o mesmo input → validar.
8. **Homologação e produção** seguindo o processo do time (GMUD, janela, aprovações).
9. **Fechar o ciclo:** documentar o aprendizado e como rodar local no README do time.

### Template de descrição de PR

```markdown
## Problema
<o que falhava, em qual estado, com qual erro>

## Causa
<por que falhava>

## Solução
<o que mudou e por quê>

## Como testei
- [ ] teste unitário reproduzindo o bug
- [ ] execução local com evento de dev
- [ ] reexecução da Step Function em dev

## Riscos
<idempotência, formato do output, permissões, impacto em outros estados>
```

---

## Parte 7: Segurança no banco (não negociável)

- **Nunca** use payload, log ou dado de produção na sua máquina, em repo pessoal ou em ferramenta externa (inclusive IA).
- **Nunca** commite credencial, `.env`, ARN com account ID ou nome interno em repositório pessoal.
- Segredos ficam no **Secrets Manager / Parameter Store**, não em env var em texto puro nem no código.
- Na dúvida se algo é sensível, trate como sensível.

---

## Parte 8: Armadilhas comuns

| Sintoma | Causa provável |
|---|---|
| Funciona local, falha na AWS | Permissão da role, env var diferente, timeout, memória |
| Falha local, funciona na AWS | Recurso dentro da VPC, proxy, layer faltando, região |
| `Task timed out` | Timeout baixo, chamada externa lenta, loop |
| `Lambda.Unknown` | Processo morreu (memória estourada) |
| Lambda ok, próximo estado quebra | `ResultPath`/`OutputPath` mudou o JSON |
| Registro duplicado | Retry sem idempotência |
| `ProvisionedThroughputExceeded` | Throttling no Dynamo |
| `ValidationException` no Dynamo | Chave com tipo ou nome errado |

---

## Parte 9: Glossário rápido

- **ARN:** identificador único de qualquer recurso AWS.
- **Cold start:** primeira execução num ambiente novo, mais lenta.
- **Execução:** uma rodada da Step Function.
- **Handler:** função de entrada da Lambda.
- **Idempotência:** processar duas vezes tem o mesmo efeito que processar uma.
- **Layer:** pacote de dependências compartilhado entre Lambdas.
- **Role:** identidade IAM que a Lambda assume para ter permissões.
- **State machine:** a definição do fluxo da Step Function.
- **Throttling:** a AWS recusando requisições por excesso de volume.

---

## Parte 10: O que estudar depois (sem pressa)

1. **AWS Step Functions Developer Guide**, seções "Error handling" e "Input and output processing": é onde está a maioria dos bugs reais.
2. **Powertools for AWS Lambda (Python)**: logs estruturados, idempotência e tracing prontos; vale ver se o time já usa.
3. **The DynamoDB Book (Alex DeBrie)**, capítulos iniciais: modelagem por padrão de acesso, se o Dynamo virar parte do seu dia a dia.
