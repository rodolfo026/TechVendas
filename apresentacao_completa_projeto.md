# Apresentação Completa — Projeto TechVendas BI

## Slide 1 — Capa
**Projeto:** Painel de Inteligência de Negócios — TechVendas  
**Tema:** Vendas, Inadimplência e Priorização de Cobrança  
**Equipe:** (inserir nomes)  
**Disciplina:** (inserir disciplina)  
**Data:** (inserir data)

---

## Slide 2 — Contexto do problema
A empresa possui dados de vendas e financeiro, mas sem uma visão integrada para decisões rápidas.

Principais dores:
- dificuldade para acompanhar risco de inadimplência;
- baixa visibilidade de performance por vendedor, categoria e UF;
- ausência de priorização objetiva para ações de cobrança.

---

## Slide 3 — Objetivo do projeto
Construir uma solução completa de BI para:
- integrar dados técnicos e de negócio;
- calcular indicadores-chave de receita e risco;
- gerar análises visuais acionáveis;
- apoiar decisões com IA (insights qualitativos).

---

## Slide 4 — Arquitetura da solução
Fluxo da solução:
1. Banco PostgreSQL (origem de dados)
2. Extração SQL com Python
3. Tratamento e feature engineering com pandas
4. Visualizações e KPIs no Streamlit + Plotly
5. Camada de IA com Groq para recomendações

Resultado: pipeline auditável do dado bruto até o insight.

---

## Slide 5 — Estrutura técnica e conexão com dados (Etapa A)
- instalação de dependências;
- imports principais;
- conexão segura com banco via variáveis de ambiente;
- execução de queries SQL com joins entre tabelas de vendas e financeiro.

Bibliotecas:
- pandas: manipulação de dados;
- sqlalchemy: conexão e execução SQL;
- plotly: gráficos interativos;
- groq: recomendações com IA.

---

## Slide 6 — Extração de dados (Etapa A)
As consultas SQL consolidam:
- notas fiscais;
- cliente e vendedor;
- categoria de produto;
- valores de título, saldo em aberto e datas de vencimento/pagamento.

Saída da etapa: DataFrame único pronto para tratamento e análise.

---

## Slide 7 — Tratamento e feature engineering (Etapa B)
Principais ações:
- padronização de nomes de colunas;
- conversão de datas e valores numéricos;
- preenchimento de nulos com regras de negócio;
- criação de colunas derivadas (lucro, margem, inadimplência, ano/mês, categorias).

Impacto: base consistente para cálculo de KPIs e gráficos.

---

## Slide 8 — Metodologia oficial de inadimplência
Base oficial: financeiro.conta_receber

Regras:
- carteira total: soma de valor_original;
- valor em atraso: títulos com data_recebimento nula e vencimento menor que a data atual;
- taxa de inadimplência: valor em atraso dividido pela carteira total.

Valores de referência:
- carteira total: R$ 814.931.114,15
- valor em atraso: R$ 498.624.954,17
- taxa de inadimplência: 61,19%

---

## Slide 9 — KPIs do dashboard
Indicadores centrais apresentados:
- total vendido;
- ticket médio;
- saldo em atraso oficial;
- taxa de inadimplência oficial;
- taxa de notas inadimplentes (visão analítica por notas).

Diferencial: separação clara entre métrica oficial financeira e métricas analíticas por filtro.

---

## Slide 10 — Análises de negócio respondidas
Perguntas obrigatórias atendidas:
1. Receita e sazonalidade mensal
2. Top vendedores e comissão de 2,5%
3. Categorias com maior participação/lucro/margem
4. Taxa de inadimplência por UF
5. Pergunta extra: priorização de ação por UF

---

## Slide 11 — Visualizações implementadas
- evolução mensal de vendas (linha);
- vendas/participação por categoria (barras);
- taxa de inadimplência por UF (barras percentuais);
- ranking de prioridade por UF (score combinado);
- tabelas de apoio com detalhamento executivo.

A interface foi ajustada com tema claro/escuro e consistência visual.

---

## Slide 12 — Priorização de cobrança por UF
Modelo aplicado:
- score de prioridade = rank(taxa de inadimplência) + rank(total vendido)

Leitura:
- UFs sobem no ranking quando combinam risco alto e impacto financeiro alto.
- UFs com volume muito baixo ou taxa muito baixa tendem a cair no ranking.

---

## Slide 13 — Camada de IA (Etapa C)
Uso da IA:
- geração de recomendações objetivas para reduzir inadimplência;
- chatbot contextual com dados filtrados do próprio dashboard;
- respostas em português com foco gerencial.

Governança:
- contexto controlado;
- prompt com regras de segurança e escopo de dados;
- foco em apoio à decisão, não substituição da análise humana.

---

## Slide 14 — Principais ganhos do projeto
- visão unificada de vendas + risco;
- métricas padronizadas e auditáveis;
- redução de tempo para análise gerencial;
- priorização orientada por dados para cobrança;
- melhor comunicação entre áreas técnica e negócio.

---

## Slide 15 — Limitações e próximos passos
Limitações atuais:
- dependência de qualidade da base transacional;
- priorização por score simples (pesos fixos).

Próximos passos:
- calibrar pesos do score por estratégia da empresa;
- criar alertas automáticos de risco;
- incluir metas e acompanhamento por carteira de cobrança;
- adicionar testes automatizados para regras críticas de KPI.

---

## Slide 16 — Conclusão
O projeto entrega uma solução de BI ponta a ponta:
- dados conectados com segurança;
- regras de negócio claras;
- indicadores confiáveis;
- visualizações acionáveis;
- suporte de IA para recomendação.

Resumo final: a TechVendas passa a decidir com base em evidência, e não em percepção.

---

## Slide 17 — Roteiro rápido de fala por integrante (sugestão)
- Integrante 1: contexto, objetivo e arquitetura
- Integrante 2: estrutura técnica, conexão e SQL
- Integrante 3: tratamento de dados e KPIs
- Integrante 4: dashboard, análises e priorização por UF
- Integrante 5: IA, ganhos, limitações e próximos passos

---

## Slide 18 — Encerramento
Obrigado(a)!  
Perguntas?
