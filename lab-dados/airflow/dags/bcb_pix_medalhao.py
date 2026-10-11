"""
### Pix por município (Banco Central) → bronze → silver → gold

**Fonte:** API de dados abertos do Pix do Banco Central (Olinda), recurso
`TransacoesPixPorMunicipio`. Um registro por município por mês.

**Destino:** banco `lab` no `lab-postgres` (conexão `lab_postgres`).

| Camada | Tabela | Conteúdo |
|---|---|---|
| bronze | `bronze.pix_municipio_raw` | Dado bruto da API (JSON), exatamente como veio |
| silver | `silver.pix_municipio` | Colunas tipadas, um registro por município e mês |
| gold | `gold.pix_uf_mes` | Visão por estado e mês, pelo lado de quem paga |

Cada execução processa **um mês** (`ano_mes`, formato AAAAMM). Se o mês não for
informado em *Run Parameters*, usa dois meses antes da data lógica, por causa do
prazo de publicação do BC. Reprocessar um mês substitui os dados dele, então a
carga pode ser repetida sem duplicar nada.
"""

from __future__ import annotations

import json
from datetime import timedelta

import pendulum
import requests

from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.sdk import Param, dag, task

try:  # Airflow 3
    from airflow.sdk.exceptions import AirflowSkipException
except ImportError:  # versões anteriores
    from airflow.exceptions import AirflowSkipException


CONN_ID = "lab_postgres"
API_URL = (
    "https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata/"
    "TransacoesPixPorMunicipio(DataBase=@DataBase)"
)
# A API do BC não aceita $skip (responde 500) nem $filter (responde 400), então não dá
# para paginar. Em vez disso, pede-se tudo de uma vez com um $top folgado. O parâmetro
# DataBase funciona como mês inicial: a resposta traz esse mês e todos os seguintes
# (cerca de 5.570 linhas por mês), e o mês desejado é separado aqui no Python.
LIMITE_LINHAS = 200_000
MINIMO_MUNICIPIOS = 5_000  # o Brasil tem cerca de 5.570 municípios
TOTAL_UFS = 27  # 26 estados + Distrito Federal


# ---------------------------------------------------------------------------
# SQL
# O "::text" depois de %(ano_mes)s deixa o tipo explícito. Sem ele, o driver
# do PostgreSQL usado pelo Airflow (psycopg 3) rejeita o mesmo parâmetro
# aparecendo como texto num lugar e como char(6) em outro.
# ---------------------------------------------------------------------------

DDL = """
CREATE TABLE IF NOT EXISTS bronze.pix_municipio_raw (
    ano_mes      char(6)     NOT NULL,
    payload      jsonb       NOT NULL,
    carregado_em timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_pix_municipio_raw_ano_mes
    ON bronze.pix_municipio_raw (ano_mes);

CREATE TABLE IF NOT EXISTS silver.pix_municipio (
    ano_mes             char(6)       NOT NULL,
    data_ref            date          NOT NULL,
    municipio_ibge      integer       NOT NULL,
    municipio           text,
    estado_ibge         integer,
    estado              text,
    sigla_regiao        text,
    regiao              text,
    vl_pagador_pf       numeric(20,2) NOT NULL,
    qt_pagador_pf       bigint        NOT NULL,
    vl_pagador_pj       numeric(20,2) NOT NULL,
    qt_pagador_pj       bigint        NOT NULL,
    vl_recebedor_pf     numeric(20,2) NOT NULL,
    qt_recebedor_pf     bigint        NOT NULL,
    vl_recebedor_pj     numeric(20,2) NOT NULL,
    qt_recebedor_pj     bigint        NOT NULL,
    qt_pes_pagador_pf   bigint,
    qt_pes_pagador_pj   bigint,
    qt_pes_recebedor_pf bigint,
    qt_pes_recebedor_pj bigint,
    carregado_em        timestamptz   NOT NULL DEFAULT now(),
    PRIMARY KEY (ano_mes, municipio_ibge)
);

CREATE TABLE IF NOT EXISTS gold.pix_uf_mes (
    ano_mes        char(6)       NOT NULL,
    data_ref       date          NOT NULL,
    sigla_regiao   text,
    estado         text          NOT NULL,
    municipios     integer       NOT NULL,
    valor_pago     numeric(20,2) NOT NULL,
    qtd_transacoes bigint        NOT NULL,
    ticket_medio   numeric(20,2),
    pct_valor_pj   numeric(5,2),
    atualizado_em  timestamptz   NOT NULL DEFAULT now(),
    PRIMARY KEY (ano_mes, estado)
);
"""

BRONZE_SQL = [
    "DELETE FROM bronze.pix_municipio_raw WHERE ano_mes = %(ano_mes)s::text",
    """
    INSERT INTO bronze.pix_municipio_raw (ano_mes, payload)
    SELECT %(ano_mes)s::text, elem
    FROM jsonb_array_elements(%(dados)s::jsonb) AS elem
    """,
]

SILVER_SQL = [
    "DELETE FROM silver.pix_municipio WHERE ano_mes = %(ano_mes)s::text",
    """
    INSERT INTO silver.pix_municipio (
        ano_mes, data_ref, municipio_ibge, municipio, estado_ibge, estado,
        sigla_regiao, regiao,
        vl_pagador_pf, qt_pagador_pf, vl_pagador_pj, qt_pagador_pj,
        vl_recebedor_pf, qt_recebedor_pf, vl_recebedor_pj, qt_recebedor_pj,
        qt_pes_pagador_pf, qt_pes_pagador_pj, qt_pes_recebedor_pf, qt_pes_recebedor_pj
    )
    SELECT DISTINCT ON ((payload->>'Municipio_Ibge')::numeric::integer)
        %(ano_mes)s::text,
        to_date(%(ano_mes)s::text, 'YYYYMM'),
        (payload->>'Municipio_Ibge')::numeric::integer,
        payload->>'Municipio',
        (payload->>'Estado_Ibge')::numeric::integer,
        payload->>'Estado',
        payload->>'Sigla_Regiao',
        payload->>'Regiao',
        COALESCE((payload->>'VL_PagadorPF')::numeric, 0),
        COALESCE((payload->>'QT_PagadorPF')::numeric, 0)::bigint,
        COALESCE((payload->>'VL_PagadorPJ')::numeric, 0),
        COALESCE((payload->>'QT_PagadorPJ')::numeric, 0)::bigint,
        COALESCE((payload->>'VL_RecebedorPF')::numeric, 0),
        COALESCE((payload->>'QT_RecebedorPF')::numeric, 0)::bigint,
        COALESCE((payload->>'VL_RecebedorPJ')::numeric, 0),
        COALESCE((payload->>'QT_RecebedorPJ')::numeric, 0)::bigint,
        (payload->>'QT_PES_PagadorPF')::numeric::bigint,
        (payload->>'QT_PES_PagadorPJ')::numeric::bigint,
        (payload->>'QT_PES_RecebedorPF')::numeric::bigint,
        (payload->>'QT_PES_RecebedorPJ')::numeric::bigint
    FROM bronze.pix_municipio_raw
    WHERE ano_mes = %(ano_mes)s::text
      AND payload->>'Municipio_Ibge' IS NOT NULL
    ORDER BY (payload->>'Municipio_Ibge')::numeric::integer, carregado_em DESC
    """,
]

QUALIDADE_SQL = """
SELECT
    count(*)                                                        AS linhas,
    count(*) FILTER (WHERE vl_pagador_pf < 0 OR vl_pagador_pj < 0
                        OR qt_pagador_pf < 0 OR qt_pagador_pj < 0)  AS negativos,
    -- a API traz uma linha "NAO INFORMADO" (sem código de estado) que não é uma UF
    count(DISTINCT estado) FILTER (WHERE estado_ibge IS NOT NULL)   AS estados
FROM silver.pix_municipio
WHERE ano_mes = %(ano_mes)s::text
"""

GOLD_SQL = [
    "DELETE FROM gold.pix_uf_mes WHERE ano_mes = %(ano_mes)s::text",
    """
    INSERT INTO gold.pix_uf_mes (
        ano_mes, data_ref, sigla_regiao, estado, municipios,
        valor_pago, qtd_transacoes, ticket_medio, pct_valor_pj
    )
    SELECT
        ano_mes,
        data_ref,
        sigla_regiao,
        estado,
        count(*),
        sum(vl_pagador_pf + vl_pagador_pj),
        sum(qt_pagador_pf + qt_pagador_pj),
        round(sum(vl_pagador_pf + vl_pagador_pj)
              / nullif(sum(qt_pagador_pf + qt_pagador_pj), 0), 2),
        round(100 * sum(vl_pagador_pj)
              / nullif(sum(vl_pagador_pf + vl_pagador_pj), 0), 2)
    FROM silver.pix_municipio
    WHERE ano_mes = %(ano_mes)s::text
    GROUP BY ano_mes, data_ref, sigla_regiao, estado
    """,
]


# ---------------------------------------------------------------------------
# DAG
# ---------------------------------------------------------------------------


@dag(
    dag_id="bcb_pix_medalhao",
    description="Pix por município (BCB) → bronze, silver e gold no lab-postgres",
    schedule="0 6 5 * *",  # todo dia 5 do mês, às 6h
    start_date=pendulum.datetime(2025, 1, 1, tz="America/Sao_Paulo"),
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=2)},
    params={
        "ano_mes": Param(
            "",
            type="string",
            title="Mês de referência (AAAAMM)",
            description="Exemplo: 202512. Em branco, usa dois meses antes da data lógica.",
        )
    },
    tags=["portfolio", "pix", "medalhao"],
    doc_md=__doc__,
)
def bcb_pix_medalhao():
    @task
    def definir_mes(**context) -> str:
        """Decide qual mês processar: o informado no gatilho ou dois meses antes da data lógica."""
        informado = str(context["params"].get("ano_mes") or "").strip()
        if informado:
            if len(informado) != 6 or not informado.isdigit():
                raise ValueError(f"ano_mes deve estar no formato AAAAMM. Recebido: {informado!r}")
            return informado

        base = context.get("logical_date") or pendulum.now("America/Sao_Paulo")
        return pendulum.instance(base).subtract(months=2).strftime("%Y%m")

    @task
    def criar_tabelas() -> None:
        """Cria as tabelas das três camadas, se ainda não existirem."""
        PostgresHook(postgres_conn_id=CONN_ID).run(DDL)

    @task
    def extrair_bronze(ano_mes: str) -> int:
        """Baixa o mês na API do BC e grava o JSON bruto em bronze."""
        url = f"{API_URL}?@DataBase='{ano_mes}'&$format=json&$top={LIMITE_LINHAS}"
        resposta = requests.get(url, timeout=300)
        resposta.raise_for_status()
        todos = resposta.json().get("value", [])

        if len(todos) >= LIMITE_LINHAS:
            raise ValueError(
                f"A API devolveu {len(todos)} linhas, o limite pedido. "
                "A resposta pode estar truncada: aumente LIMITE_LINHAS."
            )

        registros = [r for r in todos if r.get("AnoMes") == int(ano_mes)]
        print(f"API devolveu {len(todos)} linhas; {len(registros)} são de {ano_mes}")

        if not registros:
            raise AirflowSkipException(f"O BC ainda não publicou os dados de {ano_mes}.")

        PostgresHook(postgres_conn_id=CONN_ID).run(
            BRONZE_SQL,
            parameters={"ano_mes": ano_mes, "dados": json.dumps(registros)},
        )
        print(f"{len(registros)} registros de {ano_mes} gravados em bronze.pix_municipio_raw")
        return len(registros)

    @task
    def transformar_silver(ano_mes: str) -> None:
        """Converte o JSON bruto em colunas tipadas, um registro por município."""
        PostgresHook(postgres_conn_id=CONN_ID).run(SILVER_SQL, parameters={"ano_mes": ano_mes})

    @task
    def validar_qualidade(ano_mes: str) -> None:
        """Barra a carga da gold se o mês vier incompleto ou com valores inválidos."""
        linhas, negativos, estados = PostgresHook(postgres_conn_id=CONN_ID).get_first(
            QUALIDADE_SQL, parameters={"ano_mes": ano_mes}
        )
        problemas = []
        if linhas < MINIMO_MUNICIPIOS:
            problemas.append(f"só {linhas} municípios (mínimo esperado: {MINIMO_MUNICIPIOS})")
        if negativos:
            problemas.append(f"{negativos} municípios com valor ou quantidade negativa")
        if estados != TOTAL_UFS:
            problemas.append(f"{estados} estados (esperado: {TOTAL_UFS})")

        if problemas:
            raise ValueError(f"Falha de qualidade em {ano_mes}: " + "; ".join(problemas))
        print(f"Qualidade OK em {ano_mes}: {linhas} municípios, {estados} estados")

    @task
    def agregar_gold(ano_mes: str) -> None:
        """Consolida por estado: valor, quantidade, ticket médio e participação de PJ."""
        PostgresHook(postgres_conn_id=CONN_ID).run(GOLD_SQL, parameters={"ano_mes": ano_mes})

    mes = definir_mes()
    tabelas = criar_tabelas()
    bronze = extrair_bronze(mes)
    silver = transformar_silver(mes)
    qualidade = validar_qualidade(mes)
    gold = agregar_gold(mes)

    tabelas >> bronze >> silver >> qualidade >> gold


bcb_pix_medalhao()
