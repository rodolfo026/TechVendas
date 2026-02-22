
import os
import unicodedata

import pandas as pd
import streamlit as st
import plotly.express as px
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from groq import Groq


OUT_OF_SCOPE_MESSAGE = 'Não Sei te responder essa pergunta'


def pick(existing_columns, candidates):
    for col in candidates:
        if col in existing_columns:
            return col
    return None


def table_columns(engine, schema, table):
    sql = text("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema = :schema AND table_name = :table
    ORDER BY ordinal_position
    """)
    cols = pd.read_sql(sql, engine, params={"schema": schema, "table": table})
    return cols["column_name"].tolist()


def get_secret(key, default=None):
    """Lê segredos do st.secrets (Streamlit Cloud) ou do .env (local)."""
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)


def get_engine_from_env():
    load_dotenv('.env')
    db_host = get_secret('DB_HOST')
    db_port = get_secret('DB_PORT', '5432')
    db_name = get_secret('DB_NAME')
    db_user = get_secret('DB_USER') or get_secret('DB_USERNAME')
    db_password = get_secret('DB_PASSWORD')

    if not all([db_host, db_port, db_name, db_user, db_password]):
        raise ValueError('Credenciais de banco incompletas. Verifique o .env ou os Secrets do Streamlit Cloud.')

    conn_str = f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    return create_engine(conn_str)


def format_num_human(value):
    if pd.isna(value):
        return '0'
    abs_value = abs(float(value))
    if abs_value >= 1_000_000_000:
        return f'{value / 1_000_000_000:.2f} bi'
    if abs_value >= 1_000_000:
        return f'{value / 1_000_000:.2f} mi'
    if abs_value >= 1_000:
        return f'{value / 1_000:.1f} mil'
    return f'{value:.0f}'


def format_currency_human(value):
    return f'R$ {format_num_human(value)}'


def format_currency_full(value):
    return f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def normalize_text(value):
    if value is None:
        return ''
    normalized = unicodedata.normalize('NFKD', str(value))
    return normalized.encode('ASCII', 'ignore').decode('ASCII').lower()


def is_company_context_question(question):
    q = normalize_text(question)
    context_terms = [
        'venda', 'vendas', 'inadimplencia', 'inadimplente', 'cliente', 'clientes',
        'vendedor', 'vendedores', 'categoria', 'categorias', 'produto', 'produtos',
        'receita', 'ticket', 'nota fiscal', 'nf', 'uf', 'estado', 'cobranca',
        'pagamento', 'parcela', 'financeiro', 'margem', 'lucro', 'custo',
        'sazonalidade', 'mensal', 'empresa', 'dados'
    ]
    return any(term in q for term in context_terms)


@st.cache_data(ttl=1800)
def load_data():
    engine = get_engine_from_env()

    query = '''
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
    '''

    df = pd.read_sql(query, engine)
    df.columns = [c.lower().strip() for c in df.columns]

    df['data_emissao'] = pd.to_datetime(df['data_emissao'], errors='coerce')
    df['data_vencimento'] = pd.to_datetime(df['data_vencimento'], errors='coerce')
    df['data_pagamento'] = pd.to_datetime(df['data_pagamento'], errors='coerce')

    for col in ['valor_total', 'custo_total', 'valor_recebido', 'valor_titulo', 'saldo_aberto']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df['categoria_produto'] = df['categoria_produto'].fillna('Não Informado')
    df['uf'] = df['uf'].fillna('NI')
    df['nome_cliente'] = df['nome_cliente'].fillna('Cliente não identificado')
    df['nome_vendedor'] = df['nome_vendedor'].fillna('Vendedor não identificado')

    df = df.dropna(subset=['id_nota_fiscal', 'data_emissao', 'valor_total']).copy()

    if 'valor_titulo' in df.columns and 'saldo_aberto' in df.columns:
        calc_recebido = (df['valor_titulo'].fillna(0) - df['saldo_aberto'].fillna(0)).clip(lower=0)
        if 'valor_recebido' not in df.columns:
            df['valor_recebido'] = calc_recebido
        else:
            df['valor_recebido'] = df['valor_recebido'].fillna(calc_recebido)

    if 'valor_recebido' not in df.columns:
        df['valor_recebido'] = 0
    if 'saldo_aberto' not in df.columns:
        df['saldo_aberto'] = (df['valor_total'] - df['valor_recebido']).clip(lower=0)

    df['valor_recebido'] = df['valor_recebido'].fillna(0)
    df['saldo_aberto'] = df['saldo_aberto'].fillna((df['valor_total'] - df['valor_recebido']).clip(lower=0))
    df['custo_total'] = df['custo_total'].fillna(0)

    df['lucro'] = df['valor_total'] - df['custo_total']
    df['margem_pct'] = (df['lucro'] / df['valor_total']).replace([float('inf'), -float('inf')], 0).fillna(0)

    hoje = pd.Timestamp.today().normalize()
    df['inadimplente'] = (
        (df['data_vencimento'].notna())
        & (hoje > df['data_vencimento'])
        & (df['saldo_aberto'] > 0.01)
    ).astype(int)

    df['valor_inadimplente'] = df['saldo_aberto'].where(df['inadimplente'] == 1, 0)
    df['ano'] = df['data_emissao'].dt.year
    df['mes'] = df['data_emissao'].dt.to_period('M').astype(str)
    df['vendedor_nome'] = df['nome_vendedor'].fillna('Vendedor não identificado').astype(str).str.strip()
    df['categorias_lista'] = df['categoria_produto'].fillna('Não Informado').apply(
        lambda value: [item.strip() for item in str(value).split('/') if item.strip()]
    )
    df['qtd_categorias'] = df['categorias_lista'].apply(lambda items: max(len(items), 1))

    return df


st.set_page_config(page_title='Dashboard BI - TechVendas', layout='wide')
st.image('Logo.png', width=220)
st.title('Painel de Inteligência de Negócios - TechVendas')

try:
    df = load_data()
except Exception as exc:
    st.error(f'Erro ao carregar dados do banco: {exc}')
    st.stop()

st.sidebar.header('Filtros')
anos = sorted([int(a) for a in df['ano'].dropna().unique()])
cats = sorted(set(df['categorias_lista'].explode().dropna().tolist()))
vends = sorted(df['vendedor_nome'].dropna().unique())

ano_sel = st.sidebar.multiselect('Ano', anos, default=anos)
cat_sel = st.sidebar.multiselect('Categoria de Produto', cats, default=cats)
vend_sel = st.sidebar.multiselect('Vendedor', vends, default=vends)

if not ano_sel:
    ano_sel = anos
if not cat_sel:
    cat_sel = cats
if not vend_sel:
    vend_sel = vends

f = df[df['ano'].isin(ano_sel) & df['vendedor_nome'].isin(vend_sel)].copy()
if cat_sel:
    f = f[f['categorias_lista'].apply(lambda items: any(cat in items for cat in cat_sel))]

if f.empty:
    st.warning('Nenhum registro encontrado com os filtros atuais. Ajustando filtros para exibir todos os dados.')
    f = df.copy()

total_vendido = f['valor_total'].sum()
ticket_medio = f['valor_total'].mean() if len(f) else 0
total_inadimplente = f['valor_inadimplente'].sum()
taxa_inadimplencia = (total_inadimplente / total_vendido) if total_vendido else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric('Total Vendido', format_currency_human(total_vendido))
k2.metric('Ticket Médio', format_currency_human(ticket_medio))
k3.metric('Saldo Inadimplente', format_currency_human(total_inadimplente))
k4.metric('Taxa de Inadimplência', f'{taxa_inadimplencia:.2%}')

st.markdown('### Análise Qualitativa com IA (Groq)')
resumo_numerico_ia = (
    f"Vendas totais: {format_currency_full(total_vendido)}\n"
    f"Ticket médio: {format_currency_full(ticket_medio)}\n"
    f"Total inadimplente: {format_currency_full(total_inadimplente)}\n"
    f"Taxa de inadimplência: {taxa_inadimplencia:.2%}"
)

total_notas = f['id_nota_fiscal'].nunique(dropna=True)
periodo_inicio = f['data_emissao'].min()
periodo_fim = f['data_emissao'].max()
periodo_texto = (
    f"{periodo_inicio.date()} até {periodo_fim.date()}"
    if pd.notna(periodo_inicio) and pd.notna(periodo_fim)
    else 'Período não identificado'
)

top_categorias = (
    f['categoria_produto']
    .fillna('Sem categoria')
    .str.split(' / ')
    .explode()
    .value_counts()
    .head(10)
)
categorias_texto = ', '.join(top_categorias.index.tolist()) if len(top_categorias) else 'Sem categorias encontradas.'

top_ufs = (
    f['uf']
    .fillna('NI')
    .value_counts()
    .head(10)
)
ufs_texto = ', '.join(top_ufs.index.tolist()) if len(top_ufs) else 'Sem UFs encontradas.'

vendedores_top = (
    f.groupby('nome_vendedor', dropna=True)['valor_total']
    .sum()
    .sort_values(ascending=False)
    .head(20)
)
vendedores_lista = [v for v in vendedores_top.index.tolist() if str(v).strip()]
vendedores_texto = ', '.join(vendedores_lista) if vendedores_lista else 'Sem vendedores encontrados.'
total_vendedores = f['nome_vendedor'].nunique(dropna=True)

contexto_chat = (
    f"{resumo_numerico_ia}\n"
    f"Total de notas fiscais: {total_notas}\n"
    f"Período dos dados: {periodo_texto}\n"
    f"Total de vendedores únicos: {total_vendedores}\n"
    f"Top vendedores por valor vendido (até 20): {vendedores_texto}\n"
    f"Categorias mais frequentes (até 10): {categorias_texto}\n"
    f"UFs mais frequentes (até 10): {ufs_texto}"
)

st.text_area('Resumo numérico enviado para a IA', value=resumo_numerico_ia, height=110)

if st.button('Gerar 3 recomendações'):
    try:
        load_dotenv('.env')
        groq_api_key = get_secret('GROQ_API_KEY')
        if not groq_api_key:
            st.error('GROQ_API_KEY não encontrada. Configure no .env (local) ou em Secrets (Streamlit Cloud).')
        else:
            prompt = (
                "Atue como um consultor financeiro e sugira 3 ações para reduzir essa inadimplência.\n"
                "Use linguagem objetiva em português e inclua uma justificativa curta por ação.\n\n"
                f"Resumo numérico:\n{resumo_numerico_ia}"
            )
            client = Groq(api_key=groq_api_key)
            response = client.chat.completions.create(
                model='llama-3.3-70b-versatile',
                messages=[
                    {'role': 'system', 'content': 'Você é um consultor financeiro sênior especializado em redução de inadimplência.'},
                    {'role': 'user', 'content': prompt},
                ],
                temperature=0.3,
            )
            analise_ia = response.choices[0].message.content
            st.success('Análise gerada com sucesso.')
            st.markdown(analise_ia)
    except Exception as exc:
        st.error(f'Erro ao gerar análise com Groq: {exc}')

st.markdown('### Tech Bot')
st.caption('Converse com a IA sobre vendas, inadimplência, vendedores e categorias usando os dados filtrados.')

if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = [
        {
            'role': 'assistant',
            'content': 'Olá! Sou seu assistente financeiro. Pergunte sobre risco, sazonalidade, vendedores ou categorias.'
        }
    ]

if st.button('Limpar conversa', width='stretch'):
    st.session_state.chat_messages = [
        {
            'role': 'assistant',
            'content': 'Conversa reiniciada. Como posso ajudar na análise financeira?'
        }
    ]
    st.rerun()

with st.container(border=True):
    st.markdown('**Tech Bot**')
    st.caption('Faça perguntas sobre vendas, inadimplência, vendedores e categorias.')

    st.markdown('**Histórico**')
    with st.container(height=320):
        for msg in st.session_state.chat_messages[-20:]:
            with st.chat_message(msg['role']):
                st.markdown(msg['content'])

    st.markdown('**Nova mensagem**')
    user_question = st.text_area(
        'Digite sua pergunta para o Tech Bot',
        placeholder='Ex.: Quais ações podem reduzir a inadimplência em curto prazo?',
        height=90,
        key='chat_question_input'
    )

    send_col1, send_col2 = st.columns([5, 1])
    with send_col2:
        send_clicked = st.button('Enviar', width='stretch')


pending_question = None
if send_clicked:
    if not user_question or not user_question.strip():
        st.warning('Digite uma mensagem antes de enviar.')
    else:
        pending_question = user_question.strip()

if pending_question:
    st.session_state.chat_messages.append({'role': 'user', 'content': pending_question})

    try:
        q_norm = normalize_text(pending_question)
        if any(term in q_norm for term in ['oi', 'ola', 'bom dia', 'boa tarde', 'boa noite']):
            answer = 'Olá! Posso ajudar com vendas, inadimplência, vendedores, categorias e sazonalidade.'
        elif 'vendedor' in q_norm:
            answer = f"Vendedores encontrados (top 20 por vendas): {vendedores_texto}"
        else:
            load_dotenv('.env')
            groq_api_key = get_secret('GROQ_API_KEY')
            if not groq_api_key:
                answer = 'GROQ_API_KEY não encontrada. Configure no .env (local) ou em Secrets (Streamlit Cloud).'  
            else:
                client = Groq(api_key=groq_api_key)
                system_context = (
                    'Você é um consultor financeiro sênior. '
                    'Responda em português, de forma objetiva, usando apenas os dados reais da empresa abaixo. '
                    'Não invente informações. '
                    'Se a pergunta não puder ser respondida com esses dados, diga claramente que não há dados suficientes e explique o limite.\n\n'
                    f'{contexto_chat}'
                )
                history = [
                    {'role': 'system', 'content': system_context}
                ]
                for msg in st.session_state.chat_messages[-8:]:
                    history.append({'role': msg['role'], 'content': msg['content']})

                response = client.chat.completions.create(
                    model='llama-3.3-70b-versatile',
                    messages=history,
                    temperature=0.3,
                )
                answer = response.choices[0].message.content

        st.session_state.chat_messages.append({'role': 'assistant', 'content': answer})
        st.rerun()
    except Exception as exc:
        error_msg = f'Erro no chat com Groq: {exc}'
        st.session_state.chat_messages.append({'role': 'assistant', 'content': error_msg})
        st.rerun()

g1, g2 = st.columns(2)

vendas_cat = (
    f[['id_nota_fiscal', 'valor_total', 'categorias_lista', 'qtd_categorias']]
    .explode('categorias_lista')
    .assign(valor_rateado=lambda d: d['valor_total'] / d['qtd_categorias'])
    .groupby('categorias_lista', as_index=False)['valor_rateado']
    .sum()
    .rename(columns={'categorias_lista': 'categoria_produto', 'valor_rateado': 'valor_total'})
)

fig_bar = px.bar(vendas_cat, x='categoria_produto', y='valor_total', title='Vendas por Categoria')
fig_bar.update_layout(xaxis_title='Categoria', yaxis_title='Valor vendido')
g1.plotly_chart(fig_bar, width='stretch')

serie_tempo = f.groupby('mes', as_index=False)['valor_total'].sum().sort_values('mes')
fig_line = px.line(serie_tempo, x='mes', y='valor_total', title='Evolução Mensal de Vendas')
fig_line.update_layout(xaxis_title='Mês', yaxis_title='Valor vendido')
g2.plotly_chart(fig_line, width='stretch')

st.markdown('### Análise de Receita: evolução mensal e sazonalidade')

receita_mes = f.copy()
receita_mes['mes_num'] = receita_mes['data_emissao'].dt.month
receita_mes['mes_nome'] = receita_mes['data_emissao'].dt.month_name(locale='pt_BR') if hasattr(receita_mes['data_emissao'].dt, 'month_name') else receita_mes['mes_num'].astype(str)

sazonalidade = (
    receita_mes.groupby('mes_num', as_index=False)
    .agg(venda_media=('valor_total', 'mean'), venda_total=('valor_total', 'sum'))
    .sort_values('mes_num')
)

mapa_meses = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
    7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}
sazonalidade['mes'] = sazonalidade['mes_num'].map(mapa_meses)

mes_pico = sazonalidade.loc[sazonalidade['venda_total'].idxmax()] if len(sazonalidade) else None
mes_fraco = sazonalidade.loc[sazonalidade['venda_total'].idxmin()] if len(sazonalidade) else None

if mes_pico is not None and mes_fraco is not None and mes_fraco['venda_total'] > 0:
    variacao_sazonal = (mes_pico['venda_total'] / mes_fraco['venda_total']) - 1
else:
    variacao_sazonal = 0

ha_sazonalidade = variacao_sazonal >= 0.15

rec_c1, rec_c2, rec_c3 = st.columns(3)
rec_c1.metric('Mês pico de vendas', mes_pico['mes'] if mes_pico is not None else '-')
rec_c2.metric('Mês mais fraco', mes_fraco['mes'] if mes_fraco is not None else '-')
rec_c3.metric('Variação pico x fraco', f'{variacao_sazonal:.2%}')

st.info('Existe sazonalidade? ' + ('Sim, há indícios relevantes.' if ha_sazonalidade else 'Não, a variação mensal é relativamente estável.'))

sazonalidade_view = sazonalidade[['mes', 'venda_total', 'venda_media']].copy()
sazonalidade_view['venda_total'] = sazonalidade_view['venda_total'].apply(
    lambda value: f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
)
sazonalidade_view['venda_media'] = sazonalidade_view['venda_media'].apply(
    lambda value: f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
)
st.dataframe(sazonalidade_view, width='stretch')

st.subheader('Análises Complementares')

gx1, gx2 = st.columns(2)

fig_pie = px.pie(
    vendas_cat,
    names='categoria_produto',
    values='valor_total',
    title='Participação nas Vendas por Categoria'
)
fig_pie.update_traces(textposition='inside', textinfo='percent+label')
gx1.plotly_chart(fig_pie, width='stretch')

# Análise de Produto (volume, lucro e margem)
categoria_produto_analise = (
    f[['id_nota_fiscal', 'valor_total', 'custo_total', 'categorias_lista', 'qtd_categorias']]
    .explode('categorias_lista')
    .assign(
        valor_rateado=lambda d: d['valor_total'] / d['qtd_categorias'],
        custo_rateado=lambda d: d['custo_total'].fillna(0) / d['qtd_categorias']
    )
    .groupby('categorias_lista', as_index=False)
    .agg(
        volume_vendido=('valor_rateado', 'sum'),
        custo_total=('custo_rateado', 'sum')
    )
    .rename(columns={'categorias_lista': 'categoria_produto'})
)
categoria_produto_analise['lucro_total'] = categoria_produto_analise['volume_vendido'] - categoria_produto_analise['custo_total']
categoria_produto_analise['margem_lucro'] = (
    categoria_produto_analise['lucro_total'] / categoria_produto_analise['volume_vendido']
).where(categoria_produto_analise['volume_vendido'] != 0, 0)

st.markdown('### Análise de Produto: categorias com maior margem ou volume')

rank_volume = categoria_produto_analise.sort_values('volume_vendido', ascending=False).head(10).copy()
rank_lucro = categoria_produto_analise.sort_values('lucro_total', ascending=False).head(10).copy()
rank_margem = categoria_produto_analise.sort_values('margem_lucro', ascending=False).head(10).copy()

prod_c1, prod_c2, prod_c3 = st.columns(3)
prod_c1.metric('Top categoria por volume', rank_volume.iloc[0]['categoria_produto'] if len(rank_volume) else '-')
prod_c2.metric('Top categoria por lucro', rank_lucro.iloc[0]['categoria_produto'] if len(rank_lucro) else '-')
prod_c3.metric('Top categoria por margem', rank_margem.iloc[0]['categoria_produto'] if len(rank_margem) else '-')

analise_view = categoria_produto_analise.sort_values(['lucro_total', 'volume_vendido'], ascending=False).copy()
analise_view['volume_vendido'] = analise_view['volume_vendido'].apply(
    lambda value: f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
)
analise_view['lucro_total'] = analise_view['lucro_total'].apply(
    lambda value: f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
)
analise_view['margem_lucro'] = analise_view['margem_lucro'].apply(lambda value: f'{value:.2%}')
st.dataframe(analise_view, width='stretch')

top_vendedores = (
    f.groupby('vendedor_nome', as_index=False)['valor_total']
    .sum()
    .sort_values('valor_total', ascending=False)
    .head(5)
)
top_vendedores['comissao_2_5_pct'] = top_vendedores['valor_total'] * 0.025

inad_uf = f.groupby('uf', as_index=False).agg(total=('valor_total', 'sum'), inad_valor=('valor_inadimplente', 'sum'))
inad_uf['taxa_inadimplencia'] = inad_uf['inad_valor'] / inad_uf['total'].where(inad_uf['total'] != 0, 1)
inad_uf = inad_uf.sort_values('taxa_inadimplencia', ascending=False)

gx2.markdown('### Top 5 Vendedores e Comissão (2,5%)')
top_vendedores_view = top_vendedores.rename(
    columns={
        'vendedor_nome': 'nome_vendedor',
        'valor_total': 'valor_nota',
        'comissao_2_5_pct': 'comissao_2_5',
    }
).copy()
top_vendedores_view['valor_nota'] = top_vendedores_view['valor_nota'].apply(
    lambda value: f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
)
top_vendedores_view['comissao_2_5'] = top_vendedores_view['comissao_2_5'].apply(
    lambda value: f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
)
gx2.dataframe(top_vendedores_view, width='stretch')

fig_inad_uf = px.bar(
    inad_uf,
    x='uf',
    y='taxa_inadimplencia',
    title='Taxa de Inadimplência por UF',
    text='taxa_inadimplencia'
)
fig_inad_uf.update_traces(texttemplate='%{text:.2%}', textposition='outside')
fig_inad_uf.update_layout(xaxis_title='UF', yaxis_title='Taxa de inadimplência')
st.plotly_chart(fig_inad_uf, width='stretch')

st.subheader('Risco por UF')
inad_uf_view = inad_uf.rename(
    columns={
        'uf': 'UF',
        'total': 'Total vendido',
        'inad_valor': 'Saldo inadimplente',
        'taxa_inadimplencia': 'Taxa de inadimplência',
    }
).copy()
inad_uf_view['Total vendido'] = inad_uf_view['Total vendido'].apply(format_currency_human)
inad_uf_view['Saldo inadimplente'] = inad_uf_view['Saldo inadimplente'].apply(format_currency_human)
inad_uf_view['Taxa de inadimplência'] = inad_uf_view['Taxa de inadimplência'].apply(lambda value: f'{value:.2%}')
st.dataframe(inad_uf_view, width='stretch')

# --- Pergunta extra: UFs com alta receita E alta inadimplência (prioridade de ação) ---
st.subheader('Prioridade de Ação por UF')
st.caption('UFs com maior receita e maior inadimplência simultaneamente â€” onde concentrar esforços de cobrança.')

prioridade_uf = inad_uf.copy()
prioridade_uf['score_prioridade'] = (
    prioridade_uf['taxa_inadimplencia'].rank(ascending=True) +
    prioridade_uf['total'].rank(ascending=True)
)
prioridade_uf = prioridade_uf.sort_values('score_prioridade', ascending=False)

top_prioridade = prioridade_uf.head(15).copy()
top_prioridade['label'] = (
    top_prioridade['uf'] + ' | Taxa: ' +
    top_prioridade['taxa_inadimplencia'].apply(lambda v: f'{v:.1%}') +
    ' | Vendido: ' +
    top_prioridade['total'].apply(format_currency_human)
)
top_prioridade = top_prioridade.sort_values('score_prioridade', ascending=True)

fig_prioridade = px.bar(
    top_prioridade,
    x='score_prioridade',
    y='label',
    orientation='h',
    title='Top 15 UFs por Prioridade de Ação (alta receita + alta inadimplência)',
    color='taxa_inadimplencia',
    color_continuous_scale='Reds',
    labels={
        'score_prioridade': 'Score de Prioridade',
        'label': 'UF',
        'taxa_inadimplencia': 'Taxa Inad.',
    },
    text='score_prioridade',
)
fig_prioridade.update_traces(texttemplate='%{text:.1f}', textposition='outside')
fig_prioridade.update_layout(
    height=500,
    yaxis_title='',
    xaxis_title='Score de Prioridade',
    coloraxis_colorbar_title='Taxa Inad.',
    coloraxis_colorbar_tickformat='.0%',
)
st.plotly_chart(fig_prioridade, width='stretch')

prioridade_view = prioridade_uf.head(10).rename(columns={
    'uf': 'UF',
    'total': 'Total Vendido',
    'inad_valor': 'Saldo Inadimplente',
    'taxa_inadimplencia': 'Taxa de Inadimplência',
    'score_prioridade': 'Score de Prioridade',
}).copy()
prioridade_view['Total Vendido'] = prioridade_view['Total Vendido'].apply(format_currency_human)
prioridade_view['Saldo Inadimplente'] = prioridade_view['Saldo Inadimplente'].apply(format_currency_human)
prioridade_view['Taxa de Inadimplência'] = prioridade_view['Taxa de Inadimplência'].apply(lambda v: f'{v:.2%}')
prioridade_view['Score de Prioridade'] = prioridade_view['Score de Prioridade'].apply(lambda v: f'{v:.1f}')
st.dataframe(prioridade_view, width='stretch')

