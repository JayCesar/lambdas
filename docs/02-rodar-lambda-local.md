# 2. Rodar a Lambda localmente

## Opções

| Opção | Precisa de | Quando usar |
|---|---|---|
| **Chamar o handler direto** (`run_local.py`) | Python + credenciais | Padrão. Loop rápido, sem Docker. |
| **Teste unitário com mock** (pytest + `unittest.mock`/`moto`) | Python | Reproduzir o bug sem depender de rede. |
| `sam local invoke` / "Run locally" do Toolkit | **Docker** | Só se houver Docker. Em RHEL sem sudo, geralmente não. |
| Invocar a Lambda real em dev (`aws lambda invoke`) | Deploy em dev | Validação final e quando o recurso só existe na VPC. |

## Passo a passo

1. Gere o `event.json` a partir da execução que falhou (ver [01](01-step-functions-cli.md)).
2. Copie as env vars da Lambda real:
   ```bash
   aws lambda get-function-configuration --function-name <nome> --query Environment
   ```
   Exporte as necessárias no terminal. Se alguma for referência a segredo, não cole o valor em arquivo versionado.
3. Rode no **mesmo terminal** em que o CLI funciona:
   ```bash
   export AWS_PROFILE=dev AWS_REGION=<regiao>
   python scripts/run_local.py events/falha.json --module app --handler handler
   ```

## Isolar dependências (hexagonal)

Se o handler acessa algo inalcançável da sua máquina (recurso dentro da VPC, API interna), não lute com a rede:

- Separe a lógica (domínio) do acesso a dados (adapter).
- No teste, substitua o adapter por um mock.
- Escreva primeiro o **teste que reproduz o bug** (red), corrija (green), refatore.

```python
# tests/test_handler.py (exemplo genérico)
from unittest.mock import patch
import json
from app import handler

def test_reproduz_bug():
    event = json.load(open("events/exemplo.json"))
    with patch("app.repositorio.buscar_pedido") as fake:
        fake.return_value = {"pedidoId": "123", "status": "EM_ROTA"}
        resultado = handler(event, None)
    assert resultado["status"] == "EM_ROTA"
```

## Validação final em dev

```bash
aws lambda invoke --function-name <nome> \
  --payload fileb://events/falha.json \
  --cli-binary-format raw-in-base64-out \
  saida.json && cat saida.json
```
Depois, reexecute a Step Function em dev com o mesmo input.
