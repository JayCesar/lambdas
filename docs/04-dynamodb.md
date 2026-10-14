# 4. DynamoDB em 5 minutos

NoSQL chave-valor, gerenciado e serverless. Não tem JOIN nem schema fixo. **Modele pelos padrões de acesso, não pelas entidades.**

Resumo de bolso: o Dynamo é um `Map<chave, valor>` gigante e infinito. Se você precisa "pesquisar" o dado, é SQL.

## Chaves

- **Partition key (PK):** define onde o item mora. Obrigatória.
- **Sort key (SK):** opcional; ordena os itens dentro da mesma PK.
- Exemplo: PK = `pedidoId`, SK = `evento#2026-10-13T10:00` → histórico do pedido ordenado.

## Query vs Scan

- **Query:** por PK (e condição na SK). Rápido e barato.
- **Scan:** lê a tabela inteira. Lento e caro; evite em produção.
- Busca por outro campo → **GSI** (índice com outra PK/SK).

## Recursos que aparecem no código

| Recurso | Para quê |
|---|---|
| `ConditionExpression` | escrita condicional, ex.: idempotência ("só grava se não existir") |
| TTL | expirar itens automaticamente |
| Streams | evento a cada mudança, pode disparar Lambda |
| On-demand vs provisionado | throttling = `ProvisionedThroughputExceededException` |
| `TransactWriteItems` | transações limitadas (até 100 itens) |

## Quando usar: 3 perguntas

Se as três respostas forem **sim**, é Dynamo:
1. Sempre busco o dado por uma chave que já conheço?
2. As perguntas que faço ao dado são poucas e estáveis?
3. Preciso de escala ou de zero operação, sem cruzar tabelas?

Bons casos: idempotência e deduplicação, estado de workflow, locks, sessões com TTL, eventos por chave.

## Comandos

```bash
# estrutura (PK, SK, índices): comece por aqui
aws dynamodb describe-table --table-name <tabela>

# item por chave
aws dynamodb get-item --table-name <tabela> \
  --key '{"pedidoId": {"S": "123"}}'

# query por PK
aws dynamodb query --table-name <tabela> \
  --key-condition-expression "pedidoId = :id" \
  --expression-attribute-values '{":id": {"S": "123"}}'
```
`{"S": ...}` é o formato tipado (S = string, N = número). No Python, `boto3.resource("dynamodb").Table(...)` esconde isso.
