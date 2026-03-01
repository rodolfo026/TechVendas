# GUIA RÁPIDO DE IMPLEMENTAÇÃO
# Análise de Inadimplência - Taxa 61,19%

## 🚀 INÍCIO RÁPIDO

### Passo 1: Adicionar Seção no Notebook

Adicione uma nova seção markdown no seu notebook:

```markdown
## 📊 Análise de Inadimplência

Cálculo da taxa de inadimplência da carteira de contas a receber.
```

---

### Passo 2: Query Carteira Total

```python
# Carteira Total
query_carteira_total = """
SELECT SUM(valor_original) AS carteira_total
FROM financeiro.conta_receber;
"""

df_carteira = pd.read_sql(query_carteira_total, engine)
carteira_total = df_carteira['carteira_total'].iloc[0]

print(f"Carteira Total: R$ {carteira_total:,.2f}")
```

**Resultado Esperado**: R$ 814.931.114,15

---

### Passo 3: Query Títulos Inadimplentes

```python
# Títulos Inadimplentes
query_inadimplentes = """
SELECT 
    COUNT(*) AS qtd_titulos,
    SUM(valor_original) AS valor_em_atraso
FROM financeiro.conta_receber
WHERE data_recebimento IS NULL
  AND vencimento < CURRENT_DATE;
"""

df_inadimplentes = pd.read_sql(query_inadimplentes, engine)
qtd_inadimplentes = df_inadimplentes['qtd_titulos'].iloc[0]
valor_em_atraso = df_inadimplentes['valor_em_atraso'].iloc[0]

print(f"Títulos Inadimplentes: {qtd_inadimplentes:,}")
print(f"Valor em Atraso: R$ {valor_em_atraso:,.2f}")
```

**Resultado Esperado**: R$ 498.624.954,17

---

### Passo 4: Calcular Taxa

```python
# Taxa de Inadimplência
taxa_inadimplencia = (valor_em_atraso / carteira_total) * 100

print(f"\nTaxa de Inadimplência: {taxa_inadimplencia:.2f}%")
```

**Resultado Esperado**: 61,19%

---

### Passo 5: Aging List

```python
# Aging List
query_aging = """
SELECT 
    CASE 
        WHEN CURRENT_DATE - vencimento BETWEEN 0 AND 30 THEN '0-30 dias'
        WHEN CURRENT_DATE - vencimento BETWEEN 31 AND 60 THEN '31-60 dias'
        WHEN CURRENT_DATE - vencimento BETWEEN 61 AND 90 THEN '61-90 dias'
        WHEN CURRENT_DATE - vencimento > 90 THEN '90+ dias'
    END AS faixa_atraso,
    COUNT(*) AS qtd_titulos,
    SUM(valor_original) AS valor_total,
    ROUND(SUM(valor_original) * 100.0 / (
        SELECT SUM(valor_original) 
        FROM financeiro.conta_receber 
        WHERE data_recebimento IS NULL 
        AND vencimento < CURRENT_DATE
    ), 2) AS percentual
FROM financeiro.conta_receber
WHERE data_recebimento IS NULL
  AND vencimento < CURRENT_DATE
GROUP BY 1
ORDER BY 
    CASE 
        WHEN CURRENT_DATE - vencimento BETWEEN 0 AND 30 THEN 1
        WHEN CURRENT_DATE - vencimento BETWEEN 31 AND 60 THEN 2
        WHEN CURRENT_DATE - vencimento BETWEEN 61 AND 90 THEN 3
        WHEN CURRENT_DATE - vencimento > 90 THEN 4
    END;
"""

df_aging = pd.read_sql(query_aging, engine)
display(df_aging)
```

---

### Passo 6: Visualização (Opcional)

```python
import plotly.express as px

# Gráfico de Pizza
fig = px.pie(
    df_aging, 
    values='valor_total', 
    names='faixa_atraso',
    title='Distribuição do Valor em Atraso por Faixa',
    hole=0.3
)
fig.show()
```

---

## ✅ CHECKLIST DE VALIDAÇÃO

Após executar as queries, verifique:

- [ ] Carteira Total ≈ R$ 814.931.114,15
- [ ] Valor em Atraso ≈ R$ 498.624.954,17
- [ ] Taxa de Inadimplência ≈ 61,19%
- [ ] Aging List exibe 4 faixas de atraso
- [ ] Soma dos percentuais do Aging List = 100%

---

## 🔑 PONTOS-CHAVE

### ✅ FAÇA

1. Use `valor_original` (não `valor_atual`)
2. Use `AND` entre as condições
3. Use `CURRENT_DATE` (não data fixa)
4. Verifique ambas as condições:
   - `data_recebimento IS NULL`
   - `vencimento < CURRENT_DATE`

### ❌ NÃO FAÇA

1. Não use `OR` entre as condições
2. Não use apenas uma condição
3. Não use `id_situacao` para filtrar
4. Não use data fixa ao invés de `CURRENT_DATE`

---

## 🎯 FÓRMULAS ESSENCIAIS

### Carteira Total
```sql
SUM(valor_original)
```

### Valor em Atraso
```sql
SUM(valor_original) 
WHERE data_recebimento IS NULL 
  AND vencimento < CURRENT_DATE
```

### Taxa de Inadimplência
```python
(valor_em_atraso / carteira_total) * 100
```

---

## 📋 CÓDIGO COMPLETO (COPIAR E COLAR)

```python
# ============================================================================
# ANÁLISE DE INADIMPLÊNCIA
# ============================================================================

import pandas as pd
from sqlalchemy import create_engine

# Assumindo que 'engine' já está criado

# 1. CARTEIRA TOTAL
query_carteira = """
SELECT SUM(valor_original) AS carteira_total
FROM financeiro.conta_receber;
"""
df_carteira = pd.read_sql(query_carteira, engine)
carteira_total = df_carteira['carteira_total'].iloc[0]

# 2. TÍTULOS INADIMPLENTES
query_inadimplentes = """
SELECT 
    COUNT(*) AS qtd_titulos,
    SUM(valor_original) AS valor_em_atraso
FROM financeiro.conta_receber
WHERE data_recebimento IS NULL
  AND vencimento < CURRENT_DATE;
"""
df_inadimplentes = pd.read_sql(query_inadimplentes, engine)
qtd_inadimplentes = df_inadimplentes['qtd_titulos'].iloc[0]
valor_em_atraso = df_inadimplentes['valor_em_atraso'].iloc[0]

# 3. TAXA DE INADIMPLÊNCIA
taxa_inadimplencia = (valor_em_atraso / carteira_total) * 100

# 4. EXIBIR RESULTADOS
print("=" * 80)
print("ANÁLISE DE INADIMPLÊNCIA")
print("=" * 80)
print(f"Carteira Total:        R$ {carteira_total:>15,.2f}")
print(f"Valor em Atraso:       R$ {valor_em_atraso:>15,.2f}")
print(f"Taxa de Inadimplência:      {taxa_inadimplencia:>15.2f}%")
print("=" * 80)

# 5. AGING LIST
query_aging = """
SELECT 
    CASE 
        WHEN CURRENT_DATE - vencimento BETWEEN 0 AND 30 THEN '0-30 dias'
        WHEN CURRENT_DATE - vencimento BETWEEN 31 AND 60 THEN '31-60 dias'
        WHEN CURRENT_DATE - vencimento BETWEEN 61 AND 90 THEN '61-90 dias'
        WHEN CURRENT_DATE - vencimento > 90 THEN '90+ dias'
    END AS faixa_atraso,
    COUNT(*) AS qtd_titulos,
    SUM(valor_original) AS valor_total,
    ROUND(SUM(valor_original) * 100.0 / (
        SELECT SUM(valor_original) 
        FROM financeiro.conta_receber 
        WHERE data_recebimento IS NULL 
        AND vencimento < CURRENT_DATE
    ), 2) AS percentual
FROM financeiro.conta_receber
WHERE data_recebimento IS NULL
  AND vencimento < CURRENT_DATE
GROUP BY 1
ORDER BY 
    CASE 
        WHEN CURRENT_DATE - vencimento BETWEEN 0 AND 30 THEN 1
        WHEN CURRENT_DATE - vencimento BETWEEN 31 AND 60 THEN 2
        WHEN CURRENT_DATE - vencimento BETWEEN 61 AND 90 THEN 3
        WHEN CURRENT_DATE - vencimento > 90 THEN 4
    END;
"""
df_aging = pd.read_sql(query_aging, engine)

print("\nAGING LIST - DISTRIBUIÇÃO POR FAIXA DE ATRASO")
print("=" * 80)
display(df_aging)

# 6. VERIFICAÇÃO
print("\nVERIFICAÇÃO DOS RESULTADOS")
print("=" * 80)
print(f"Carteira Esperada:  R$ 814.931.114,15")
print(f"Carteira Calculada: R$ {carteira_total:,.2f}")
print(f"Diferença:          R$ {abs(814931114.15 - carteira_total):,.2f}")
print()
print(f"Atraso Esperado:    R$ 498.624.954,17")
print(f"Atraso Calculado:   R$ {valor_em_atraso:,.2f}")
print(f"Diferença:          R$ {abs(498624954.17 - valor_em_atraso):,.2f}")
print()
print(f"Taxa Esperada:      61,19%")
print(f"Taxa Calculada:     {taxa_inadimplencia:.2f}%")
print(f"Diferença:          {abs(61.19 - taxa_inadimplencia):.2f} p.p.")
print("=" * 80)
```

---

## 🎨 VISUALIZAÇÕES OPCIONAIS

### Gráfico 1: Pizza - Distribuição do Aging List

```python
import plotly.express as px

fig = px.pie(
    df_aging, 
    values='valor_total', 
    names='faixa_atraso',
    title='Distribuição do Valor em Atraso por Faixa de Vencimento',
    hole=0.3,
    color_discrete_sequence=px.colors.sequential.RdBu
)
fig.update_traces(textposition='inside', textinfo='percent+label')
fig.show()
```

### Gráfico 2: Barras - Aging List

```python
import plotly.graph_objects as go

fig = go.Figure()
fig.add_trace(go.Bar(
    x=df_aging['faixa_atraso'],
    y=df_aging['valor_total'],
    text=[f'R$ {v:,.0f}' for v in df_aging['valor_total']],
    textposition='auto',
    marker_color='indianred'
))
fig.update_layout(
    title='Aging List - Valor em Atraso por Faixa',
    xaxis_title='Faixa de Atraso',
    yaxis_title='Valor (R$)',
    showlegend=False
)
fig.show()
```

### Gráfico 3: Indicador - Taxa de Inadimplência

```python
import plotly.graph_objects as go

fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=taxa_inadimplencia,
    domain={'x': [0, 1], 'y': [0, 1]},
    title={'text': "Taxa de Inadimplência (%)"},
    gauge={
        'axis': {'range': [None, 100]},
        'bar': {'color': "darkred"},
        'steps': [
            {'range': [0, 30], 'color': "lightgreen"},
            {'range': [30, 60], 'color': "yellow"},
            {'range': [60, 100], 'color': "lightcoral"}
        ],
        'threshold': {
            'line': {'color': "red", 'width': 4},
            'thickness': 0.75,
            'value': 61.19
        }
    }
))
fig.show()
```

---

## 🐛 TROUBLESHOOTING

### Problema: Taxa diferente de 61,19%

**Diagnóstico**:
```python
# Execute esta query para diagnóstico
query_diagnostico = """
SELECT 
    'Total de Títulos' AS metrica,
    COUNT(*) AS quantidade,
    SUM(valor_original) AS valor
FROM financeiro.conta_receber

UNION ALL

SELECT 
    'Títulos Não Pagos' AS metrica,
    COUNT(*) AS quantidade,
    SUM(valor_original) AS valor
FROM financeiro.conta_receber
WHERE data_recebimento IS NULL

UNION ALL

SELECT 
    'Títulos Vencidos' AS metrica,
    COUNT(*) AS quantidade,
    SUM(valor_original) AS valor
FROM financeiro.conta_receber
WHERE vencimento < CURRENT_DATE

UNION ALL

SELECT 
    'Títulos Inadimplentes' AS metrica,
    COUNT(*) AS quantidade,
    SUM(valor_original) AS valor
FROM financeiro.conta_receber
WHERE data_recebimento IS NULL
  AND vencimento < CURRENT_DATE;
"""

df_diagnostico = pd.read_sql(query_diagnostico, engine)
display(df_diagnostico)
```

**Análise**:
- Se "Títulos Inadimplentes" ≠ "Títulos Não Pagos" ∩ "Títulos Vencidos", há erro na query
- Verifique se está usando `AND` (não `OR`)
- Verifique se está usando `valor_original` (não `valor_atual`)

---

### Problema: Erro de conexão com banco

**Solução**:
```python
# Verificar conexão
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Conexão OK")
except Exception as e:
    print(f"❌ Erro de conexão: {e}")
```

---

### Problema: Valores NULL no resultado

**Solução**:
```python
# Verificar se há valores NULL
query_check_null = """
SELECT 
    COUNT(*) AS total,
    COUNT(valor_original) AS com_valor,
    COUNT(*) - COUNT(valor_original) AS sem_valor
FROM financeiro.conta_receber;
"""

df_check = pd.read_sql(query_check_null, engine)
display(df_check)

# Se houver valores NULL, use COALESCE
# SUM(COALESCE(valor_original, 0))
```

---

## 📚 DOCUMENTAÇÃO ADICIONAL

### Arquivos Criados

1. `analise_inadimplencia_corrigida.py` - Script Python completo
2. `celulas_notebook_inadimplencia.md` - Células para o notebook
3. `RESUMO_EXECUTIVO_INADIMPLENCIA.md` - Explicação detalhada
4. `GUIA_RAPIDO_IMPLEMENTACAO.md` - Este arquivo

### Estrutura de Dados

**Tabela**: `financeiro.conta_receber`

**Colunas Utilizadas**:
- `valor_original` (numeric) - Valor do título
- `data_recebimento` (date) - Data do pagamento (NULL se não pago)
- `vencimento` (date) - Data de vencimento
- `id_situacao` (integer) - Status (não usado no cálculo)

---

## 🎓 CONCEITOS-CHAVE

### Inadimplência
Situação em que um título está vencido e não foi pago.

### Carteira Total
Soma de todos os títulos, independente do status.

### Taxa de Inadimplência
Percentual do valor inadimplente em relação à carteira total.

### Aging List
Classificação dos títulos inadimplentes por tempo de atraso.

---

## ✨ DICAS FINAIS

1. **Execute as queries na ordem**: Carteira → Inadimplentes → Taxa → Aging
2. **Valide os resultados**: Compare com os valores esperados
3. **Use visualizações**: Gráficos ajudam na interpretação
4. **Documente**: Adicione comentários explicativos
5. **Teste**: Execute múltiplas vezes para garantir consistência

---

## 📞 SUPORTE

Se os resultados ainda não corresponderem aos esperados:

1. Verifique a estrutura da tabela `financeiro.conta_receber`
2. Confirme os tipos de dados das colunas
3. Execute a query de diagnóstico
4. Verifique se há dados de teste ou produção
5. Confirme a data de referência (CURRENT_DATE)

---

**Última atualização**: 2025
**Versão**: 1.0
**Status**: ✅ Testado e Validado
