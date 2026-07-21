# Dunkelflaute Radar — Alerta precoce de seca de renováveis + camada carbon-aware

> ELT diário de dados públicos de clima, energia e qualidade do ar da Europa
> (Open-Meteo · DWD · ENTSO-E) → data lake em S3 → warehouse → API + dashboard.
> Prevê janelas de baixa geração eólica/solar (*Dunkelflaute*) com dias de
> antecedência e traduz cada evento em impacto de **preço (€/MWh)**,
> **carbono (tCO₂)** e **qualidade do ar (μg/m³)** — medindo continuamente a
> própria acurácia de previsão.

---

## 1. O problema

*Dunkelflaute* ("calmaria escura") é o período prolongado de pouco vento **e**
pouco sol simultâneos, típico do inverno europeu sob alta pressão. Quando
acontece, a geração eólica+solar despenca e o continente inteiro sente ao mesmo
tempo (padrões meteorológicos correlacionados entre países):

- **Preços disparam.** Nos eventos de nov/dez 2024 o spot alemão passou de
  €820/MWh e, em dezembro, ultrapassou €1.000/MWh — a máxima em quase 20 anos.
- **O mix vira fóssil.** Numa das semanas de novembro, renováveis caíram para
  ~30% da geração pública e os fósseis (gás/carvão) cobriram os 70% restantes.
- **A rede importa energia.** A Alemanha importou ~10,5 GW em média ao longo de
  três dias, puxando preços de vizinhos junto.
- **É recorrente.** Estimativas de mercado apontam ~1,6 evento/ano em média na
  Europa, com forte variação regional (mercados do norte, dependentes de eólica
  offshore, são os mais expostos).

Problema real, caro, recorrente e sem solução fechada → há valor em prever e
quantificar esses eventos.

---

## 2. O produto

Um sistema que, para cada *bidding zone* europeia, faz diariamente:

1. **Prevê** o fator de capacidade de eólica e solar a partir do clima.
2. **Detecta e alerta** janelas de *Dunkelflaute* de 1 a 10 dias à frente.
3. **Quantifica** o impacto esperado: spike de preço, intensidade de carbono da
   rede e piora de qualidade do ar.
4. **Mede a própria acurácia** ao longo do tempo (track record público).

### Superfícies de produto (mesma fundação de dados)

| Público | Pergunta que respondemos |
|---|---|
| Consumidor industrial / PME | Quando travar hedge? Quando reduzir consumo? |
| Demand-shifting / EV / cargas flexíveis | Quais são as horas mais baratas e mais limpas dos próximos dias? |
| ESG / contabilidade de emissões | Qual a intensidade de carbono *marginal* por hora? |
| Trader / analista | Sinal de risco de shortfall de renováveis por zona |

---

## 3. A cadeia de insight (o diferencial)

O valor não está em "clima vs preço", está em quantificar a cadeia inteira:

```
clima (vento em várias altitudes + irradiância)
        │
        ▼
fator de capacidade eólica/solar
        │
        ▼
folga / estresse da rede  ── detecção de Dunkelflaute
        │
        ▼
spike de preço (€/MWh)
        │
        ▼
mix vira fóssil → intensidade de carbono da rede sobe (tCO₂/MWh)
        │
        ▼
qualidade do ar piora (PM2.5, NO₂…)
```

Cada elo é mensurável. Uma semana nublada e sem vento deixa de ser "tempo ruim"
e vira *X* €/MWh a mais, *Y* toneladas de CO₂ e *Z* μg/m³ de PM2.5.

**Ângulo transfronteiriço (o insight não-óbvio):** quando a Alemanha entra em
*Dunkelflaute*, a importação marginal vem da **França (nuclear, limpa)** ou da
**Polônia (carvão, suja)**? A fonte marginal inverte completamente a história de
carbono do evento — poucos projetos capturam isso.

> **Rigor:** o elo clima→qualidade do ar é confundido por inversão térmica de
> inverno e aquecimento residencial. Tratar esse confundimento explicitamente
> (controles, decomposição) é o que faz o projeto parecer sério, não ingênuo.

---

## 4. O diferencial de engenharia: modelagem bitemporal

O que separa "plataforma" de "notebook": guardar **previsão × realizado** ao
longo do tempo.

- Todo dia ingerimos previsões meteorológicas (e as previsões da própria ENTSO-E).
- Dias depois, ingerimos o **realizado** (geração real por tipo).
- O warehouse guarda, para cada `(zona, hora)`, a previsão **como era conhecida
  em cada lead time** (D-1, D-3, D-7…) **e** o valor que de fato aconteceu.

Isso entrega de graça:

- **Auto-scoring contínuo** — o sistema mede a própria acurácia (credibilidade).
- **Correção de viés / calibração** — camada aprendida sobre o baseline físico.
- **Degradação de skill por horizonte** — quão confiável é a previsão a D-7 vs D-1.

É o padrão *as-of* / slowly-changing raramente feito em portfólio — e é
exatamente o caso de uso de backtesting de energia que o Open-Meteo divulga.

---

## 5. Arquitetura

Medallion (raw → staged → curated) com stack moderna e barata.

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ Open-Meteo  │   │    DWD      │   │  ENTSO-E    │
│ forecast /  │   │ open data   │   │ geração/    │
│ histórico / │   │             │   │ carga/preço/│
│ air quality │   │             │   │ fluxos      │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       └────────────┬────┴─────────────────┘
                    ▼
         Ingestão (Python) — cadências distintas
                    ▼
     ┌──────────────────────────────────┐
     │  S3 / MinIO / R2  (RAW, Parquet)  │  ← imutável, com ingest_ts
     │  particionado por zona/data       │     (habilita bitemporalidade)
     └───────────────┬──────────────────┘
                     ▼
        Warehouse (DuckDB / Snowflake / ClickHouse)
                     ▼
              dbt  (staging → intermediate → marts)
                     ▼
     ┌──────────────┴───────────────┐
     ▼                              ▼
 FastAPI (serving)          Dashboard (Evidence.dev)
     └──────────── alertas ─────────┘

 Orquestração: Dagster (assets + partitions)  ·  CI/CD: GitHub Actions
 Qualidade: dbt tests + Great Expectations/Soda  ·  IaC: Terraform
```

### Escolhas de stack

| Camada | Opção principal | Alternativas |
|---|---|---|
| Object storage | S3 | MinIO (local), Cloudflare R2, Backblaze B2 |
| Orquestração | Dagster | Airflow, Prefect |
| Warehouse | DuckDB (local-first, barato) | Snowflake, BigQuery, ClickHouse |
| Transformação | dbt | SQLMesh |
| Qualidade | dbt tests + Great Expectations | Soda |
| Serving | FastAPI | — |
| Dashboard | Evidence.dev | Streamlit, Metabase, Superset |
| ML (opcional) | baseline físico + correção de viés | — |

---

## 6. Modelo de dados (dbt)

**Staging** (`stg_`) — tipagem e limpeza 1:1 com a fonte:
`stg_openmeteo__weather`, `stg_openmeteo__air_quality`,
`stg_entsoe__generation`, `stg_entsoe__load`, `stg_entsoe__day_ahead_prices`,
`stg_entsoe__crossborder_flows`.

**Intermediate** (`int_`) — lógica de negócio:
- `int_capacity_factor` — fator de capacidade eólico/solar a partir de vento
  (curva de potência) e irradiância.
- `int_forecast_vs_actual` — join bitemporal (previsão por lead time × realizado).
- `int_grid_carbon_intensity` — intensidade de carbono por zona/hora a partir do mix.
- `int_dunkelflaute_events` — detecção (limiar de fator de capacidade combinado
  eólica+solar por N horas).

**Marts** (`mart_`) — consumo:
- `mart_dunkelflaute_alerts` — janelas previstas por zona e lead time.
- `mart_event_impact` — €/MWh, tCO₂, μg/m³ por evento.
- `mart_forecast_accuracy` — skill por horizonte e por variável.
- `mart_marginal_source` — origem da importação marginal por evento.

---

## 7. Fontes de dados

| Fonte | O que traz | Chave? |
|---|---|---|
| **Open-Meteo** | Forecast (16 d) + arquivo histórico (60 anos) + irradiância/GTI por orientação de painel + vento em múltiplas altitudes + air quality (CAMS) + ensembles/probabilístico | Não (tier grátis, ~10k req/dia, **não-comercial**) |
| **DWD Open Data** | Dados meteorológicos abertos da Alemanha | Não |
| **ENTSO-E Transparency** | Geração por tipo, carga, preço day-ahead, fluxos entre países — todas as *bidding zones* | **Sim** — token grátis (registro + email `transparency@entsoe.eu`, assunto "RESTful API access"). Cliente Python: `entsoe-py` |

---

## 8. Roadmap por fases

### Fase 1 — Encanamento sólido
- Ingestão de clima + ENTSO-E para 1–2 zonas (DE, talvez FR).
- Landing em S3 (Parquet particionado) **com `ingest_ts` desde o dia 1**.
- dbt até o warehouse; painel "share de renovável vs clima".
- Testes de qualidade e freshness na ingestão.

### Fase 2 — Inteligência
- Modelo de fator de capacidade (baseline físico).
- Detector de *Dunkelflaute*.
- Scoring forecast-vs-actual + skill por horizonte.

### Fase 3 — Produto
- Overlay de intensidade de carbono + qualidade do ar.
- História da fonte marginal transfronteiriça.
- API (FastAPI) + alertas.
- Camada de correção de viés (opcional, sempre medida contra baseline).

---

## 9. KPIs / métricas do próprio sistema

- **Skill de previsão** vs baselines de persistência e climatologia (MAE/RMSE do
  fator de capacidade por horizonte).
- **Lead time útil** — com quantos dias de antecedência detectamos eventos com
  precisão/recall aceitáveis.
- **Erro de impacto** — €/MWh e tCO₂ previstos vs realizados por evento.
- **Freshness / uptime** do pipeline.

---

## 10. Avisos práticos

- **ENTSO-E precisa de token** (grátis, mas não keyless). O brief pede "sem API
  key" para Open-Meteo/DWD; a ENTSO-E é um passo de ~5 min que vale muito a pena.
- **Licença Open-Meteo:** o tier grátis é **não-comercial**. Para virar produto
  de verdade, é plano pago.
- **Correlação × causação:** o elo qualidade do ar ↔ *Dunkelflaute* é confundido
  (inversão térmica, aquecimento). Trate com controles explícitos.

---

## 11. Ideias de expansão (stretch)

- Backtest climático: com 60 anos de histórico, estimar frequência futura de
  eventos sob diferentes cenários.
- Battery/arbitragem: quantas horas de armazenamento "salvariam" cada evento.
- Recomendação carbon-aware para cargas flexíveis (as N horas mais limpas/baratas).
- Ensembles: usar o espalhamento probabilístico como medida de incerteza no alerta.