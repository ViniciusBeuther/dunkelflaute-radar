# Dunkelflaute Radar

ELT diário de dados de clima, energia e qualidade do ar da Europa para prever
janelas de baixa geração eólica/solar ("Dunkelflaute") e quantificar seu
impacto em preço, carbono e qualidade do ar. Ver [DESCRIPTION.md](DESCRIPTION.md)
para o contexto completo do problema e a arquitetura-alvo.

Projeto de aprendizado: construído incrementalmente enquanto se aprende dbt,
Airflow e engenharia de dados moderna. Estado atual: **Fase 1 — Encanamento
sólido** (ingestão + landing zone + dbt staging, sem orquestrador ainda).

## Setup

Pré-requisitos: [uv](https://docs.astral.sh/uv/) instalado.

```bash
uv sync                    # cria .venv e instala dependências, usando Python 3.11 (fixado em .python-version)
cp .env.example .env       # preencha ENTSOE_API_TOKEN (ver instruções no arquivo)
```

## Estrutura

- `ingestion/` — scripts Python de ingestão por fonte (Open-Meteo, ENTSO-E)
- `data/raw/` — landing zone local em Parquet, particionada por zona/data,
  simulando um data lake S3 (migração para S3/MinIO real fica para depois)
- `dbt/dunkelflaute_radar/` — projeto dbt (staging → intermediate → marts)
- `warehouse/` — arquivo DuckDB local (gerado, não versionado)
- `tests/` — testes unitários dos scripts de ingestão

## Rodando a ingestão (manual, sem orquestrador por enquanto)

_A ser preenchido conforme os marcos M3–M5 do plano forem implementados._
