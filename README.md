# Leonardo Mendes

Engenheiro de dados e analytics engineer, em São Paulo. Hoje estou no PagBank, na área comercial de adquirência, cuidando das tabelas e dos painéis que o time usa para acompanhar receita e rentabilidade. [LinkedIn](https://www.linkedin.com/in/leomnds)

Comecei em 2015 como estagiário, escrevendo procedures em SQL Server para um sistema de benefício em medicamentos. De lá para cá o banco mudou de lugar algumas vezes (servidor próprio, BigQuery, Redshift), mas o trabalho continua o mesmo: descobrir de onde o número vem, deixar a carga previsível e dar a quem consome o dado um motivo para confiar nele.

## Stack

- **No dia a dia:** SQL em Redshift, SQL Server e Oracle; Power BI com DAX e Power Query; Power Automate
- **Em empregos anteriores:** BigQuery, Cloud Composer, SSIS, Looker, Salesforce Marketing Cloud, Python e R
- **No meu laboratório:** Airflow, PostgreSQL, Docker, n8n e Python

## Por onde passei

- **InterPlayers (2014 a 2017):** entrei pela infraestrutura, com jobs e backups de SQL Server, e passei para o desenvolvimento de procedures e relatórios
- **Marketdata (2017 a 2020):** consultoria, com atuação dentro do PagSeguro. ETL em SSIS, administração do banco e modelos estatísticos rodando direto no SQL Server e no Oracle
- **C6 Bank (2020 a 2021):** dados de CRM no BigQuery, da carga à qualidade, e um motor de campanhas no GCP ligado ao Salesforce Marketing Cloud
- **PagBank (2021 até hoje):** primeiro no CRM, automatizando extrações de mailing e limpando os dados de contato; desde 2024 na estratégia comercial, com Redshift e Power BI

## Projetos

### [lab-dados](https://github.com/leomnds/leomnds/tree/main/lab-dados)

Um laboratório que roda inteiro no meu computador, com Airflow, PostgreSQL e n8n no Docker. Para ter o que processar, montei um pipeline com os dados abertos de Pix por município do Banco Central, em três camadas: o JSON bruto, uma tabela tipada e um resumo por estado e mês.

Cada execução carrega um mês e pode ser repetida sem duplicar nada. Antes de montar o resumo, uma checagem confere se o mês veio inteiro (municípios, estados e valores negativos), para não publicar número de um mês pela metade.

A parte que mais deu trabalho foi a API do Banco Central. Ela devolve erro 500 quando recebe `$skip` e erro 400 com `$filter`, então não dá para paginar nem filtrar no servidor. O parâmetro que parece escolher o mês é, na verdade, o mês inicial: a resposta traz esse mês e todos os seguintes. A solução foi pedir tudo de uma vez e separar o mês no Python, tratando a linha "NAO INFORMADO" que vem sem código de estado.

O ambiente também é reproduzível: versões fixas, um script que sobe tudo do zero, backup e restore.

### Outros

- [cobrinha-turbo](https://github.com/leomnds/leomnds/tree/main/cobrinha-turbo): jogo da cobrinha em JavaScript puro, em um único arquivo, em que a cobra acelera a cada fruta
- [dcalendario-powerquery](https://github.com/leomnds/dcalendario-powerquery): fork de uma tabela calendário completa, escrita em M

## Formação

Tecnólogo em Big Data e Inteligência Analítica pela Anhembi Morumbi (2020 a 2022) e bacharel em Sistemas de Informação pela Uninove (2014 a 2017). Certificações em Power BI, Power Query avançado, estatística para análise de dados e SQL Server. Inglês profissional.
