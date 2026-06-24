# MiniProjeto DataView

## Sobre o projeto

O DataView e um mini-projeto de analise exploratoria de dados de vendas desenvolvido em Python. O fluxo gera um dataset sintetico com problemas intencionais, limpa e transforma os dados, trata outliers, calcula metricas, segmenta clientes e exporta resultados em CSV, JSON e PNG.

## Objetivo

Simular o trabalho de um analista de dados junior em uma empresa de varejo, respondendo perguntas como:

- Como as vendas se comportam ao longo dos meses e trimestres;
- Quais produtos e categorias geram mais receita;
- Quais regioes tem melhor desempenho;
- Quais clientes sao mais valiosos por nivel de gasto.

## Arquivos principais

- `notebooks/dataview.ipynb`: notebook principal para abrir e executar no VS Code.
- `notebooks/dataview.py`: versao em celulas do VS Code, util para execucao direta.
- `data/raw/vendas.csv`: dataset bruto sintetico.
- `data/processed/v1_com_outliers/vendas_v1.csv`: dados limpos com outliers mantidos.
- `data/processed/v2_outliers_tratado/vendas_v2.csv`: dados com outliers tratados.
- `data/final/vendas_final.csv`: dataset final enriquecido.
- `outputs/metricas_por_mes.csv`: metricas mensais.
- `outputs/segmentacao_clientes.csv`: segmentacao Bronze, Prata e Ouro.
- `outputs/estatisticas_gerais.json`: estatisticas calculadas com NumPy.
- `outputs/graficos/`: graficos exportados em PNG, incluindo o pairplot.
- `outputs/pipeline.log`: log simples de monitoramento do pipeline.

## Como executar no VS Code

1. Abra a pasta `dataview` no VS Code.
2. Instale as dependencias, se necessario:

```bash
python3 -m pip install -r requirements.txt
```

3. Abra `notebooks/dataview.ipynb`.
4. Execute as celulas em ordem, de cima para baixo.

Tambem e possivel executar a versao `.py`:

```bash
cd notebooks
python dataview.py
```

Observacao: o projeto nao depende de pastas locais de bibliotecas. Para executar
em outra maquina, use sempre `python3 -m pip install -r requirements.txt`.

## Ferramentas utilizadas

- Python 3;
- VS Code;
- Jupyter Notebook;
- Pandas, NumPy, Matplotlib e Seaborn;
- Git e GitHub para versionamento.

## Estrutura do projeto

```text
dataview/
|-- data/
|   |-- raw/
|   |-- processed/
|   |   |-- v1_com_outliers/
|   |   |-- v2_outliers_tratado/
|   |-- final/
|-- notebooks/
|   |-- dataview.ipynb
|   |-- dataview.py
|-- outputs/
|   |-- graficos/
|   |-- metricas_por_mes.csv
|   |-- segmentacao_clientes.csv
|   |-- estatisticas_gerais.json
|   |-- pipeline.log
|-- scripts/
|   |-- convert_percent_to_ipynb.py
|-- README.md
|-- requirements.txt
```

## Conceitos aplicados

- Logica de programacao com Python;
- Condicionais, repeticoes e funcoes com parametros e retorno;
- Funcoes lambda e funcao de ordem superior;
- Leitura e escrita de CSV e JSON;
- Manipulacao de datas com `datetime` e `pandas`;
- Limpeza de strings com expressoes regulares;
- Pandas: DataFrames, filtros, `groupby`, `agg` e transformacoes;
- NumPy: arrays, operacoes vetorizadas, broadcasting e estatisticas;
- Deteccao e tratamento de outliers com IQR;
- Matplotlib e Seaborn para visualizacoes, incluindo pairplot;
- Logging simples para monitoramento do pipeline.

## Decisoes de implementacao

O dataset foi gerado sinteticamente para garantir reprodutibilidade e evitar dependencia de download externo. A versao final escolhida foi a `v2_outliers_tratado`, pois ela mantem a limpeza geral da v1 e remove valores extremos detectados pelo metodo IQR.

Como diferencial, o projeto registra as etapas principais em `outputs/pipeline.log`. Isso ajuda a identificar se cada fase foi executada corretamente e aproxima o notebook de um pipeline real de dados.

## Graficos gerados

- Receita total por mes;
- Top 5 produtos por receita;
- Distribuicao de receita por regiao;
- Clientes por segmento de gasto.
- Pairplot das relacoes entre quantidade, preco unitario e receita total.

## Video de demonstracao

https://drive.google.com/file/d/1Cbc98pl5Khbn9YBHrpvMRS4Zvq_bz6-L/view?usp=sharing

## Repositorio

https://github.com/Luizhprovin/dataview
