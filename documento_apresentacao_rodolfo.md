# Apresentação — Rodolfo
## Estrutura Técnica e Conexão com Dados (com mapeamento Notebook + App)

## 1) Objetivo do projeto
Transformar dados de vendas e financeiro em indicadores confiáveis para decisão.

Na prática, minha parte garante:
- conexão segura com o banco;
- extração correta de dados com SQL;
- base consolidada para análises, KPIs e dashboard.

---

## 2) Mapa completo das etapas (Aula 11)

### Etapa A — Extração e conexão SQL
- **Notebook (Jupyter):**
   - Célula 3: instalação de dependências
   - Célula 5: imports e variáveis `.env`
   - Célula 8: conexão e query SQL principal (extração)
- **App (`app.py`):**
   - `get_engine_from_env()`: leitura de credenciais e criação da conexão
   - `load_data()`: query SQL principal de extração

### Etapa B — Tratamento e feature engineering
- **Notebook:**
   - Célula 11: tipagem, limpeza, tratamento de nulos e criação de métricas derivadas
- **App (`app.py`):**
   - `load_data()`: bloco de tratamento e criação de features (`lucro`, `margem_pct`, `inadimplente`, etc.)

### Etapa C — IA
- **Notebook:**
   - Célula 19: geração de recomendações com Groq
- **App (`app.py`):**
   - bloco “Análise Qualitativa com IA (Groq)”
   - bloco “Tech Bot” (chat contextual)

### Etapa D — Dashboard
- **Notebook (apoio):**
   - Células 14 e 16: KPIs e visualizações
   - Célula 22: pergunta extra
- **App (`app.py`):**
   - layout Streamlit + filtros + KPIs + gráficos + tabelas + priorização por UF

### Célula de checagem oficial de inadimplência
- **Notebook:**
   - Célula 31: validação da taxa oficial (`financeiro.conta_receber`)
- **App (`app.py`):**
   - `load_official_inad_metrics()`: mesma lógica oficial para carteira, atraso e taxa

---

## 3) SQL principal do aplicativo (extração consolidada)
Este SQL está em `load_data()` no `app.py`.

```sql
WITH item_agg AS (
      SELECT
            inf.id_nota_fiscal,
            STRING_AGG(DISTINCT c.descricao, ' / ') AS categoria_produto,
            SUM(COALESCE(inf.quantidade, 0) * COALESCE(pr.valor_custo, 0)) AS custo_total
      FROM vendas.item_nota_fiscal inf
      LEFT JOIN vendas.produto pr
            ON pr.id = inf.id_produto
      LEFT JOIN vendas.categoria c
            ON c.id = pr.id_categoria
      GROUP BY inf.id_nota_fiscal
),
receber_agg AS (
      SELECT
            pa.id_nota_fiscal,
            MAX(cr.vencimento) AS data_vencimento,
            MAX(cr.data_recebimento) AS data_pagamento,
            SUM(COALESCE(cr.valor_original, 0) - COALESCE(cr.valor_atual, 0)) AS valor_recebido,
            SUM(COALESCE(cr.valor_original, 0)) AS valor_titulo,
            SUM(COALESCE(cr.valor_atual, 0)) AS saldo_aberto
      FROM vendas.parcela pa
      LEFT JOIN financeiro.conta_receber cr
            ON cr.id_parcela = pa.id
      GROUP BY pa.id_nota_fiscal
)
SELECT
      nf.id AS id_nota_fiscal,
      nf.data_venda AS data_emissao,
      nf.id_cliente,
      COALESCE(pf_cli.nome, pj_cli.razao_social) AS nome_cliente,
      COALESCE(est.sigla, 'NI') AS uf,
      nf.id_vendedor,
      COALESCE(pf_vend.nome, pj_vend.razao_social, CONCAT('Vendedor ', nf.id_vendedor::text)) AS nome_vendedor,
      ia.categoria_produto,
      nf.valor AS valor_total,
      ia.custo_total,
      ra.data_vencimento,
      ra.data_pagamento,
      ra.valor_recebido,
      ra.valor_titulo,
      ra.saldo_aberto
FROM vendas.nota_fiscal nf
LEFT JOIN item_agg ia
      ON ia.id_nota_fiscal = nf.id
LEFT JOIN receber_agg ra
      ON ra.id_nota_fiscal = nf.id
LEFT JOIN geral.pessoa_fisica pf_cli
      ON pf_cli.id = nf.id_cliente
LEFT JOIN geral.pessoa_juridica pj_cli
      ON pj_cli.id = nf.id_cliente
LEFT JOIN geral.endereco e
      ON e.id_pessoa = nf.id_cliente
LEFT JOIN geral.bairro b
      ON b.id = e.id_bairro
LEFT JOIN geral.cidade ci
      ON ci.id = b.id_cidade
LEFT JOIN geral.estado est
      ON est.id = ci.id_estado
LEFT JOIN geral.pessoa_fisica pf_vend
      ON pf_vend.id = nf.id_vendedor
LEFT JOIN geral.pessoa_juridica pj_vend
      ON pj_vend.id = nf.id_vendedor
```

### Explicação por trecho

#### `item_agg` (CTE 1)
- Agrupa por nota fiscal (`id_nota_fiscal`).
- Monta categorias concatenadas (`STRING_AGG`) para usar no dashboard.
- Calcula custo total da nota: `quantidade * valor_custo`.

#### `receber_agg` (CTE 2)
- Também agrupa por nota fiscal.
- Traz datas financeiras principais (`vencimento`, `data_recebimento`).
- Calcula:
   - `valor_recebido` = `valor_original - valor_atual`;
   - `valor_titulo` = soma de `valor_original`;
   - `saldo_aberto` = soma de `valor_atual`.

#### `SELECT` final
- Usa `vendas.nota_fiscal` como tabela base.
- Enriquecimento por joins com:
   - itens/categorias (`item_agg`);
   - contas a receber (`receber_agg`);
   - cadastro de cliente/vendedor e geografia (UF).
- `COALESCE` evita campos nulos críticos para análise.

#### Resultado final do SQL
Dataset analítico único por nota fiscal, com dados de:
- valor vendido;
- custo/lucro;
- situação de recebimento;
- vendedor;
- cliente;
- categoria;
- UF.

---

## 4) SQL oficial de inadimplência do aplicativo
Este SQL está em `load_official_inad_metrics()` no `app.py`.

```sql
SELECT
      COALESCE(SUM(valor_original), 0) AS carteira_total,
      COALESCE(
            SUM(
                  CASE
                        WHEN data_recebimento IS NULL AND vencimento < CURRENT_DATE THEN valor_original
                        ELSE 0
                  END
            ),
            0
      ) AS valor_em_atraso
FROM financeiro.conta_receber
```

### Explicação por trecho
- `carteira_total`: soma de todos os títulos (`valor_original`).
- `valor_em_atraso`: soma apenas de títulos:
   - não pagos (`data_recebimento IS NULL`),
   - vencidos (`vencimento < CURRENT_DATE`).
- `COALESCE(..., 0)` evita retorno nulo.

Taxa oficial usada no app:
- `taxa_oficial = valor_em_atraso / carteira_total`.

---

## 5) Como explicar “string de conexão” e “engine” na apresentação

### Montagem da string de conexão
É a composição do endereço completo para o banco:
`postgresql+psycopg2://usuario:senha@host:porta/banco`

### Criação do engine
É a instância do SQLAlchemy que gerencia o acesso ao banco:
- recebe a string de conexão;
- permite executar SQL;
- é reutilizado para carregar dados com `pd.read_sql`.

---

## 6) Roteiro de fala (90s)
“Na Etapa A da Aula 11, nós fizemos instalação de dependências (célula 3), imports e variáveis de ambiente (célula 5), e conexão+SQL principal (célula 8). No app, isso corresponde às funções `get_engine_from_env()` e `load_data()`. A query principal usa duas CTEs: uma para itens/categorias e custo, outra para contas a receber e saldo financeiro. Depois o SELECT final junta vendas, financeiro, cliente, vendedor e UF em uma base única por nota fiscal. Também implementamos no app o SQL oficial de inadimplência em `load_official_inad_metrics()`, que soma carteira total e títulos vencidos não pagos. Assim garantimos que o dashboard usa a mesma lógica auditável validada no notebook.”

---

## 7) Perguntas da banca (respostas rápidas)
**Por que JOIN?**
Para integrar o ciclo completo: venda + cadastro + recebimento.

**Por que `COALESCE`?**
Para evitar nulos quebrando KPIs e cálculos.

**Por que duas queries no app?**
Uma para base analítica geral (`load_data`) e outra para métrica oficial de inadimplência (`load_official_inad_metrics`).

**Como provar rastreabilidade?**
Mapeando etapa por etapa entre notebook (células) e app (funções).

---

## 8) Fechamento sugerido
“A parte técnica garante que o projeto não seja só visualmente bom, mas metodologicamente correto: os dados são extraídos com SQL consistente, tratados com regras claras e apresentados com métricas auditáveis no dashboard.”
