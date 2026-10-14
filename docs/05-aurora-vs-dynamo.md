# 5. Aurora vs DynamoDB

**Aurora:** relacional gerenciado (MySQL/PostgreSQL); você consulta como quiser.
**DynamoDB:** chave-valor serverless; você consulta do jeito que desenhou.

| | Aurora (SQL) | DynamoDB |
|---|---|---|
| Modelo | Tabelas, schema, JOIN | Itens por chave, sem schema |
| Consulta | SQL ad hoc | Por PK/SK ou GSI |
| Modelagem | Pelas entidades | Pelos padrões de acesso |
| Transações | ACID completo | Limitadas (até 100 itens) |
| Escala | Vertical + réplicas de leitura | Horizontal, praticamente ilimitada |
| Latência | Boa, varia com a query | Milissegundos, previsível |
| Rede | Dentro da VPC | Endpoint público da AWS (IAM) |
| Conexão | Pool de conexões | HTTP por request |
| Custo | Instância (ou Serverless v2) | Por request ou capacidade |
| Operação | Patch, índices, tuning | Quase zero |

## Com Lambda

- **Aurora + Lambda:** risco de estourar conexões em pico → **RDS Proxy**. A Lambda precisa estar na VPC, então normalmente não roda local apontando pro banco real.
- **Dynamo + Lambda:** sem conexão persistente; par natural de serverless e Step Functions.

## Quando escolher

| Caso | Escolha |
|---|---|
| "Essa mensagem já foi processada?" | Dynamo |
| "Em que etapa está o pedido 123?" | Dynamo |
| Lock entre Lambdas | Dynamo |
| Tela B2B com filtros livres e ordenação | Aurora (ou OpenSearch) |
| Relatório mensal por transportadora | Aurora ou Athena |
| Contrato, itens, faturas e pagamentos relacionados | Aurora |

## Os dois juntos (CQRS)

Dynamo no operacional (escrita rápida, estado do processamento) → Streams → base de leitura (Aurora/OpenSearch) para telas filtráveis e relatórios.
