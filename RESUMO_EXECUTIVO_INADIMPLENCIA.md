# RESUMO EXECUTIVO - ANÁLISE DE INADIMPLÊNCIA
# Taxa de 61,19%

## 📊 RESULTADOS FINAIS

```
Carteira Total:        R$ 814.931.114,15
Valor em Atraso:       R$ 498.624.954,17
Taxa de Inadimplência:        61,19%
```

---

## 🎯 DEFINIÇÕES TÉCNICAS

### 1. Carteira Total
**Definição**: Soma de todos os títulos registrados na tabela `financeiro.conta_receber`

**Query SQL**:
```sql
SELECT SUM(valor_original) AS carteira_total
FROM financeiro.conta_receber;
```

**Resultado**: R$ 814.931.114,15

**Observações**:
- Inclui TODOS os títulos, independente do status
- Usa `valor_original` (não `valor_atual`)
- Não aplica nenhum filtro

---

### 2. Título Inadimplente
**Definição**: Um título é considerado inadimplente quando atende **AMBAS** as condições:

1. ✅ `data_recebimento IS NULL` → Não foi pago
2. ✅ `vencimento < CURRENT_DATE` → Está vencido

**Query SQL**:
```sql
SELECT 
    COUNT(*) AS qtd_titulos_inadimplentes,
    SUM(valor_original) AS valor_em_atraso
FROM financeiro.conta_receber
WHERE data_recebimento IS NULL
  AND vencimento < CURRENT_DATE;
```

**Resultado**: R$ 498.624.954,17

**Observações**:
- Ambas as condições devem ser verdadeiras simultaneamente
- Usa operador `AND` (não `OR`)
- Usa `CURRENT_DATE` para data de referência

---

### 3. Taxa de Inadimplência
**Definição**: Percentual do valor em atraso em relação à carteira total

**Fórmula**:
```
Taxa = (Valor em Atraso / Carteira Total) × 100
Taxa = (498.624.954,17 / 814.931.114,15) × 100
Taxa = 0,6119 × 100
Taxa = 61,19%
```

**Código Python**:
```python
taxa_inadimplencia = (valor_em_atraso / carteira_total) * 100
# Resultado: 61.19
```

---

## 🔍 POR QUE 61,19%?

### Análise Matemática

1. **Numerador** (Valor em Atraso): R$ 498.624.954,17
   - Representa apenas títulos que:
     - NÃO foram pagos (data_recebimento IS NULL)
     - E estão vencidos (vencimento < hoje)

2. **Denominador** (Carteira Total): R$ 814.931.114,15
   - Representa TODOS os títulos da carteira
   - Inclui: pagos, não pagos, vencidos, a vencer

3. **Divisão**:
   ```
   498.624.954,17 ÷ 814.931.114,15 = 0,611899...
   ```

4. **Multiplicação por 100**:
   ```
   0,611899... × 100 = 61,1899...%
   ```

5. **Arredondamento**:
   ```
   61,1899...% ≈ 61,19%
   ```

### Interpretação Financeira

**O que significa 61,19%?**

- De cada R$ 100,00 na carteira, R$ 61,19 estão inadimplentes
- Mais da metade da carteira está em risco
- Apenas 38,81% da carteira está regular (paga ou a vencer)

**Composição da Carteira**:
```
100,00% - Carteira Total (R$ 814.931.114,15)
  ├─ 61,19% - Inadimplente (R$ 498.624.954,17)
  └─ 38,81% - Regular (R$ 316.306.159,98)
```

---

## ❌ ERROS COMUNS QUE GERAM TAXA DIFERENTE

### Erro 1: Usar apenas `data_recebimento IS NULL`

**Query Incorreta**:
```sql
SELECT SUM(valor_original)
FROM financeiro.conta_receber
WHERE data_recebimento IS NULL;
```

**Problema**: Inclui títulos não pagos mas ainda não vencidos

**Exemplo**:
- Título com vencimento em 31/12/2025
- Hoje é 01/01/2025
- Título não foi pago (data_recebimento IS NULL)
- ❌ Não é inadimplente (ainda não venceu)

**Resultado**: Taxa MAIOR que 61,19%

---

### Erro 2: Usar apenas `vencimento < CURRENT_DATE`

**Query Incorreta**:
```sql
SELECT SUM(valor_original)
FROM financeiro.conta_receber
WHERE vencimento < CURRENT_DATE;
```

**Problema**: Inclui títulos vencidos mas já pagos

**Exemplo**:
- Título com vencimento em 01/01/2024
- Pago em 05/01/2024 (data_recebimento = '2024-01-05')
- Hoje é 01/01/2025
- ❌ Não é inadimplente (foi pago, mesmo com atraso)

**Resultado**: Taxa DIFERENTE de 61,19%

---

### Erro 3: Usar `valor_atual` ao invés de `valor_original`

**Query Incorreta**:
```sql
SELECT SUM(valor_atual)  -- ❌ ERRADO
FROM financeiro.conta_receber
WHERE data_recebimento IS NULL
  AND vencimento < CURRENT_DATE;
```

**Problema**: `valor_atual` pode incluir:
- Juros de mora
- Multas
- Descontos
- Correção monetária

**Exemplo**:
- Valor Original: R$ 1.000,00
- Valor Atual: R$ 1.150,00 (com juros)
- Base de cálculo diferente

**Resultado**: Taxa DIFERENTE de 61,19%

---

### Erro 4: Usar `id_situacao` para filtrar

**Query Incorreta**:
```sql
SELECT SUM(valor_original)
FROM financeiro.conta_receber
WHERE id_situacao = 3;  -- Supondo que 3 = inadimplente
```

**Problema**: O campo `id_situacao` pode:
- Estar desatualizado
- Ter regras de negócio diferentes
- Não refletir a definição correta de inadimplência

**Resultado**: Taxa INCORRETA

---

### Erro 5: Usar data fixa ao invés de `CURRENT_DATE`

**Query Incorreta**:
```sql
SELECT SUM(valor_original)
FROM financeiro.conta_receber
WHERE data_recebimento IS NULL
  AND vencimento < '2024-12-31';  -- ❌ Data fixa
```

**Problema**: Resultados desatualizados

**Exemplo**:
- Query executada em 01/01/2025
- Usa data de referência 31/12/2024
- Títulos vencidos em 01/01/2025 não são contabilizados

**Resultado**: Taxa DESATUALIZADA

---

### Erro 6: Usar `OR` ao invés de `AND`

**Query Incorreta**:
```sql
SELECT SUM(valor_original)
FROM financeiro.conta_receber
WHERE data_recebimento IS NULL
   OR vencimento < CURRENT_DATE;  -- ❌ OR ao invés de AND
```

**Problema**: Inclui títulos que atendem apenas UMA das condições

**Exemplo**:
- Título A: Não pago, mas não vencido → Incluído ❌
- Título B: Vencido, mas pago → Incluído ❌
- Título C: Não pago E vencido → Incluído ✅

**Resultado**: Taxa MUITO MAIOR que 61,19%

---

## ✅ QUERY CORRETA

```sql
-- Carteira Total
SELECT SUM(valor_original) AS carteira_total
FROM financeiro.conta_receber;

-- Valor em Atraso
SELECT SUM(valor_original) AS valor_em_atraso
FROM financeiro.conta_receber
WHERE data_recebimento IS NULL    -- Condição 1: Não pago
  AND vencimento < CURRENT_DATE;  -- Condição 2: Vencido

-- Taxa de Inadimplência (Python)
taxa = (valor_em_atraso / carteira_total) * 100
```

---

## 📈 AGING LIST

### Definição
Classificação dos títulos inadimplentes por tempo de atraso

### Query SQL
```sql
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
```

### Interpretação
- **0-30 dias**: Inadimplência recente, maior chance de recuperação
- **31-60 dias**: Inadimplência moderada, requer ação de cobrança
- **61-90 dias**: Inadimplência grave, risco elevado
- **90+ dias**: Inadimplência crítica, provável perda

---

## 🔧 IMPLEMENTAÇÃO NO NOTEBOOK

### Estrutura Recomendada

1. **Célula Markdown**: Título e definições
2. **Célula Código**: Query carteira total
3. **Célula Código**: Query títulos inadimplentes
4. **Célula Código**: Cálculo da taxa
5. **Célula Código**: Aging List
6. **Célula Código**: Visualizações gráficas
7. **Célula Markdown**: Explicação dos resultados

### Código Completo (Python + SQL)

```python
import pandas as pd
from sqlalchemy import create_engine

# Conexão
engine = create_engine('postgresql://...')

# 1. Carteira Total
query_carteira = """
SELECT SUM(valor_original) AS carteira_total
FROM financeiro.conta_receber;
"""
df_carteira = pd.read_sql(query_carteira, engine)
carteira_total = df_carteira['carteira_total'].iloc[0]

# 2. Valor em Atraso
query_atraso = """
SELECT SUM(valor_original) AS valor_em_atraso
FROM financeiro.conta_receber
WHERE data_recebimento IS NULL
  AND vencimento < CURRENT_DATE;
"""
df_atraso = pd.read_sql(query_atraso, engine)
valor_em_atraso = df_atraso['valor_em_atraso'].iloc[0]

# 3. Taxa de Inadimplência
taxa_inadimplencia = (valor_em_atraso / carteira_total) * 100

# 4. Exibir Resultados
print(f"Carteira Total: R$ {carteira_total:,.2f}")
print(f"Valor em Atraso: R$ {valor_em_atraso:,.2f}")
print(f"Taxa de Inadimplência: {taxa_inadimplencia:.2f}%")
```

---

## 📊 VALIDAÇÃO DOS RESULTADOS

### Checklist de Verificação

- [ ] Carteira Total = R$ 814.931.114,15 (±R$ 1,00)
- [ ] Valor em Atraso = R$ 498.624.954,17 (±R$ 1,00)
- [ ] Taxa de Inadimplência = 61,19% (±0,01%)
- [ ] Query usa `valor_original` (não `valor_atual`)
- [ ] Query usa `AND` (não `OR`)
- [ ] Query usa `CURRENT_DATE` (não data fixa)
- [ ] Ambas as condições são verificadas (não pago E vencido)

### Teste de Sanidade

```python
# Verificar se os valores estão corretos
assert abs(carteira_total - 814931114.15) < 1.0, "Carteira Total incorreta"
assert abs(valor_em_atraso - 498624954.17) < 1.0, "Valor em Atraso incorreto"
assert abs(taxa_inadimplencia - 61.19) < 0.01, "Taxa incorreta"
print("✅ Todos os valores estão corretos!")
```

---

## 🎓 CONCEITOS IMPORTANTES

### 1. Inadimplência vs. Atraso
- **Atraso**: Pagamento após o vencimento (mas foi pago)
- **Inadimplência**: Não pagamento após o vencimento

### 2. Valor Original vs. Valor Atual
- **Valor Original**: Valor do título na emissão
- **Valor Atual**: Valor com juros, multas, descontos

### 3. Data de Referência
- Sempre usar `CURRENT_DATE` para cálculos atualizados
- Evitar datas fixas que desatualizam a análise

### 4. Operadores Lógicos
- **AND**: Ambas as condições devem ser verdadeiras
- **OR**: Pelo menos uma condição deve ser verdadeira

---

## 📝 CONCLUSÃO

A taxa de inadimplência de **61,19%** é calculada corretamente quando:

1. ✅ Usa `valor_original` como base
2. ✅ Considera apenas títulos não pagos (`data_recebimento IS NULL`)
3. ✅ Considera apenas títulos vencidos (`vencimento < CURRENT_DATE`)
4. ✅ Usa operador `AND` para combinar as condições
5. ✅ Divide o valor em atraso pela carteira total
6. ✅ Multiplica por 100 para obter o percentual

**Fórmula Final**:
```
Taxa = (Σ valor_original WHERE não_pago AND vencido) / (Σ valor_original) × 100
Taxa = 498.624.954,17 / 814.931.114,15 × 100
Taxa = 61,19%
```

---

## 📚 REFERÊNCIAS

- Tabela: `financeiro.conta_receber`
- Colunas principais:
  - `valor_original`: Valor do título
  - `data_recebimento`: Data do pagamento (NULL se não pago)
  - `vencimento`: Data de vencimento
  - `id_situacao`: Status do título (não usado no cálculo)

---

## 🆘 TROUBLESHOOTING

### Problema: Taxa diferente de 61,19%

**Possíveis causas**:
1. Usando `valor_atual` ao invés de `valor_original`
2. Usando `OR` ao invés de `AND`
3. Faltando uma das condições (não pago OU vencido)
4. Usando data fixa ao invés de `CURRENT_DATE`
5. Usando `id_situacao` para filtrar

**Solução**: Revisar a query e garantir que:
- Usa `valor_original`
- Usa `AND` entre as condições
- Verifica ambas: `data_recebimento IS NULL` E `vencimento < CURRENT_DATE`
- Usa `CURRENT_DATE` (não data fixa)

---

**Documento criado em**: 2025
**Versão**: 1.0
**Status**: ✅ Validado
