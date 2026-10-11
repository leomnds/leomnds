# Leonardo Mendes

**Data & Analytics Engineer** · São Paulo, SP · [LinkedIn](https://www.linkedin.com/in/leomnds)

Construo a camada de dados entre o banco de dados e a decisão: bases bem modeladas, métricas com uma definição única e dashboards que o negócio usa sem precisar pedir extração.

São mais de 10 anos de atuação técnica em dados, do SQL Server on-premise à nuvem (BigQuery e Redshift), em meios de pagamento, banco digital e indústria farmacêutica. Hoje atuo com Analytics Engineering na estratégia comercial de adquirência do PagBank.

## Como eu trabalho

- Modelagem pensada para reuso: uma fonte de verdade por métrica, não uma query por pedido
- Qualidade de dado como requisito, não como correção depois do problema
- Automação de cargas, atualizações e distribuição de relatórios recorrentes
- Entregas que o time de negócio usa com autonomia

## Stack

| Área | Tecnologias |
|---|---|
| Linguagens | SQL (avançado), Python, R, DAX, M (Power Query) |
| Data warehouse e bancos | Amazon Redshift, Google BigQuery, SQL Server, Oracle, PostgreSQL |
| Orquestração e ETL | Apache Airflow, Cloud Composer, SSIS, n8n |
| Modelagem e qualidade | Modelagem de dados, data warehouse, arquitetura medalhão, data quality |
| Cloud | GCP, AWS (Redshift) |
| BI | Power BI, Looker, Looker Studio |
| Automação | Power Automate, Microsoft 365 Copilot |
| Ambiente | Docker, Git, Linux (WSL) |

## Experiência

**PagBank** · Especialista em Estratégia Comercial · 2024 – atual
- Modelagem e transformação em SQL no Amazon Redshift da camada que alimenta os indicadores de performance e rentabilidade da adquirência: TPV, receita bruta e líquida, take rate, net take rate e margem operacional
- Dashboards em Power BI para acompanhamento desses indicadores e bases analíticas para os estudos da área comercial
- Automação de rotinas da área com Power Automate e IA agêntica

**PagBank** · Especialista CRM · 2021 – 2024
- Automação das rotinas de extração de mailings em SQL, com as regras de negócio traduzidas em lógica padronizada e reutilizável
- Projeto de Data Quality dos dados de contato, que aumentou a taxa de CPC (contato com a pessoa certa) dos mailings

**C6 Bank** · Analista CRM Sênior · 2020 – 2021
- Estruturação, carga e qualidade dos dados de CRM no BigQuery, com modelagem da base de clientes
- Motor de campanhas no GCP integrado ao Salesforce Marketing Cloud
- Orquestração das rotinas de extração com Cloud Composer (Airflow)

**Marketdata** · Analista DBM/BI, alocado no PagSeguro · 2017 – 2020
- Scripts em SQL Server e Oracle e pacotes SSIS para ETL e automação de processos
- Administração do banco, com otimização de processos e de armazenamento
- Modelos estatísticos aplicados direto no banco para uso recorrente

**InterPlayers** · Estágio e Analista DBM/BI · 2014 – 2017
- Procedures, views, functions e triggers em SQL Server para programas de benefício em medicamentos de indústrias como Bayer, Pfizer e Novartis

## Projetos

### [lab-dados](https://github.com/leomnds/leomnds/tree/main/lab-dados)

Laboratório de dados local com Airflow 3, PostgreSQL 18 e n8n no Docker. O pipeline `bcb_pix_medalhao` carrega os dados abertos de Pix por município do Banco Central em arquitetura medalhão:

- **Bronze:** JSON bruto da API OData do BC, guardado em `jsonb`
- **Silver:** colunas tipadas, uma linha por município e mês
- **Gold:** visão por estado e mês, com valor, quantidade, ticket médio e participação de PJ
- Cargas idempotentes e parametrizadas por mês: reprocessar substitui os dados, sem duplicar
- Validação de qualidade que barra a gold se o mês vier incompleto ou com valor negativo
- Ambiente reproduzível: versões fixas no Docker e `setup.sh` que recria tudo do zero (senhas, containers e conexão do Airflow), com scripts de backup e restore

### Outros

- [dcalendario-powerquery](https://github.com/leomnds/dcalendario-powerquery): fork de uma dCalendario completa em linguagem M
- [cobrinha-turbo](https://github.com/leomnds/leomnds/tree/main/cobrinha-turbo): jogo da cobrinha em JavaScript puro, feito por diversão

## Formação e certificações

- CST em Big Data e Inteligência Analítica, Universidade Anhembi Morumbi (2020 – 2022)
- Bacharelado em Sistemas de Informação, Uninove (2014 – 2017)
- Certificações: Power BI Series, Power Query Avançado, Estatística para Análise de Dados, ICS SQL Server Essentials e White Belt Lean Seis Sigma
- Inglês profissional
