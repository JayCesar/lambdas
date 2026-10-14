#!/usr/bin/env python3
"""Invoca o handler de uma Lambda Python localmente, sem SAM e sem Docker.

Uso:
    export AWS_PROFILE=dev AWS_REGION=sa-east-1
    python scripts/run_local.py events/exemplo.json --module app --handler handler

Rode a partir da raiz do projeto da Lambda (ou use --path).
"""
import argparse
import importlib
import json
import logging
import sys
import time
import traceback
import uuid


class FakeContext:
    """Context mínimo compatível com o objeto que a AWS passa ao handler."""

    def __init__(self, function_name: str, timeout_ms: int):
        self.function_name = function_name
        self.function_version = "$LATEST"
        self.memory_limit_in_mb = 512
        self.aws_request_id = f"local-{uuid.uuid4()}"
        self.invoked_function_arn = f"arn:aws:lambda:local:000000000000:function:{function_name}"
        self.log_group_name = f"/aws/lambda/{function_name}"
        self.log_stream_name = "local"
        self._deadline = time.time() * 1000 + timeout_ms

    def get_remaining_time_in_millis(self) -> int:
        return max(0, int(self._deadline - time.time() * 1000))


def main() -> int:
    parser = argparse.ArgumentParser(description="Roda um handler de Lambda localmente")
    parser.add_argument("event", help="caminho do event.json")
    parser.add_argument("--module", default="app", help="módulo do handler (ex.: app ou src.main)")
    parser.add_argument("--handler", default="handler", help="nome da função handler")
    parser.add_argument("--path", default=".", help="diretório a adicionar no sys.path")
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--verbose-aws", action="store_true",
                        help="log DEBUG do botocore: mostra endpoint, região e proxy de cada chamada")
    parser.add_argument("--layer", action="append", default=[],
                        help="pasta de layer extraída (ex.: layers/minha-layer/python); pode repetir")
    args = parser.parse_args()

    if args.verbose_aws:
        import boto3
        boto3.set_stream_logger("botocore", logging.DEBUG)

    for layer in args.layer:
        sys.path.insert(0, layer)
    sys.path.insert(0, args.path)

    with open(args.event, encoding="utf-8") as f:
        event = json.load(f)

    module = importlib.import_module(args.module)
    handler = getattr(module, args.handler)
    context = FakeContext(function_name=args.module, timeout_ms=args.timeout_ms)

    start = time.perf_counter()
    try:
        result = handler(event, context)
    except Exception as exc:  # mostra o erro completo, como no CloudWatch
        traceback.print_exc()
        print(f"\n>>> Exceção: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        print(f">>> Duração: {(time.perf_counter() - start) * 1000:.0f} ms", file=sys.stderr)

    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
