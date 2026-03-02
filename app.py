
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


def chart_header(title, subtitle):
    st.markdown(f'#### {title}')
    st.caption(subtitle)


def get_plotly_template():
    theme = st.session_state.get('ui_theme', 'Claro')
    return 'plotly_dark' if theme == 'Escuro' else 'plotly_white'


def style_chart(fig, y_is_percent=False, show_legend=False):
    is_dark = st.session_state.get('ui_theme', 'Claro') == 'Escuro'
    bg_color = '#111b2e' if is_dark else '#ffffff'
    font_color = '#e5e7eb' if is_dark else '#111827'

    fig.update_layout(
        template=get_plotly_template(),
        title_text='',
        margin=dict(l=20, r=20, t=10, b=20),
        showlegend=show_legend,
        legend_title_text='',
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        font=dict(color=font_color),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True)
    if y_is_percent:
        fig.update_yaxes(tickformat='.0%')
    return fig


def render_table(dataframe, height=None, hide_index=True):
    is_dark = st.session_state.get('ui_theme', 'Claro') == 'Escuro'
    table_html = dataframe.to_html(index=not hide_index, border=0)
    max_height_css = f'max-height: {height}px;' if isinstance(height, int) and height > 0 else ''

    if is_dark:
        container_bg = '#111b2e'
        header_bg = '#16243b'
        row_bg = '#111b2e'
        row_alt_bg = '#0f1a2b'
        border_color = '#2a3956'
        text_color = '#e5e7eb'
    else:
        container_bg = '#ffffff'
        header_bg = '#f3f4f6'
        row_bg = '#ffffff'
        row_alt_bg = '#f9fafb'
        border_color = '#d1d5db'
        text_color = '#111827'

    st.markdown(
        f'''
        <div style="overflow-x:auto; overflow-y:auto; {max_height_css} border:1px solid {border_color}; border-radius:10px; background-color:{container_bg};">
            <style>
                .theme-table table {{
                    width: 100%;
                    border-collapse: collapse;
                    background-color: {container_bg};
                    color: {text_color};
                    font-size: 0.95rem;
                }}
                .theme-table thead th {{
                    position: sticky;
                    top: 0;
                    background-color: {header_bg};
                    color: {text_color};
                    border: 1px solid {border_color};
                    padding: 10px;
                    text-align: left;
                }}
                .theme-table tbody td {{
                    border: 1px solid {border_color};
                    padding: 10px;
                    background-color: {row_bg};
                    color: {text_color};
                }}
                .theme-table tbody tr:nth-child(even) td {{
                    background-color: {row_alt_bg};
                }}
            </style>
            <div class="theme-table">{table_html}</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def apply_ui_theme(theme):
    if theme == 'Escuro':
        st.markdown(
            '''
            <style>
            :root {
                --bg-primary: #0b1220;
                --bg-secondary: #111b2e;
                --bg-tertiary: #0f1a2b;
                --border-soft: #2a3956;
                --text-primary: #e5e7eb;
                --text-muted: #9ca3af;
                --accent: #3b82f6;
            }

            [data-testid="stAppViewContainer"] {
                background-color: var(--bg-primary);
                color: var(--text-primary);
            }
            [data-testid="stHeader"] {
                background: transparent;
            }
            [data-testid="stAppViewContainer"] .main .block-container {
                padding-top: 1.2rem;
            }
            [data-testid="stSidebar"] {
                background-color: var(--bg-secondary);
            }
            [data-testid="stSidebar"] * {
                color: var(--text-primary);
            }

            h1, h2, h3, h4, h5, h6, p, label, span {
                color: var(--text-primary);
            }
            [data-testid="stCaptionContainer"] p,
            .stCaption {
                color: var(--text-muted) !important;
            }

            [data-testid="stMetric"] {
                background: var(--bg-secondary);
                border: 1px solid var(--border-soft);
                border-radius: 10px;
                padding: 8px 10px;
            }

            div[data-baseweb="select"] > div,
            .stTextInput input,
            .stTextArea textarea,
            .stDateInput input,
            .stNumberInput input {
                background-color: var(--bg-tertiary) !important;
                border: 1px solid var(--border-soft) !important;
                color: var(--text-primary) !important;
            }

            .stButton button {
                background-color: #1d4ed8;
                border: 1px solid #1d4ed8;
                color: #ffffff;
            }
            .stButton button:hover {
                background-color: #2563eb;
                border-color: #2563eb;
            }

            [data-testid="stExpander"] {
                border: 1px solid var(--border-soft);
                border-radius: 10px;
                background: var(--bg-secondary);
            }
            [data-testid="stDataFrame"] {
                border: 1px solid var(--border-soft);
                border-radius: 10px;
                overflow: hidden;
            }
            [data-testid="stDataFrame"] [role="grid"] {
                background-color: var(--bg-secondary) !important;
                color: var(--text-primary) !important;
            }
            [data-testid="stDataFrame"] [role="columnheader"] {
                background-color: #16243b !important;
                color: var(--text-primary) !important;
                border-color: var(--border-soft) !important;
            }
            [data-testid="stDataFrame"] [role="gridcell"],
            [data-testid="stDataFrame"] [role="rowheader"] {
                background-color: var(--bg-secondary) !important;
                color: var(--text-primary) !important;
                border-color: var(--border-soft) !important;
            }
            [data-testid="stDataFrame"] [data-testid="StyledDataFrameDataCell"] {
                color: var(--text-primary) !important;
            }
            [data-testid="stDataFrame"] [data-testid="StyledDataFrameDataCell"] a {
                color: #93c5fd !important;
            }
            </style>
            ''',
            unsafe_allow_html=True,
        )


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
    # Regra: inadimplente se vencimento já passou e saldo_aberto > 0.01
    df['inadimplente'] = (
        (df['data_vencimento'].notna())
        & (df['data_vencimento'] < hoje)
        & (df['saldo_aberto'] > 0.01)
    ).astype(int)

    # Valor inadimplente = saldo_aberto apenas se inadimplente
    df['valor_inadimplente'] = df['saldo_aberto'].where(df['inadimplente'] == 1, 0)
    df['ano'] = df['data_emissao'].dt.year
    df['mes'] = df['data_emissao'].dt.to_period('M').astype(str)
    df['vendedor_nome'] = df['nome_vendedor'].fillna('Vendedor não identificado').astype(str).str.strip()
    df['categorias_lista'] = df['categoria_produto'].fillna('Não Informado').apply(
        lambda value: [item.strip() for item in str(value).split('/') if item.strip()]
    )
    df['qtd_categorias'] = df['categorias_lista'].apply(lambda items: max(len(items), 1))

    return df


@st.cache_data(ttl=1800)
def load_official_inad_metrics():
    engine = get_engine_from_env()
    query = text('''
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
    ''')

    resumo = pd.read_sql(query, engine)
    carteira_total = float(resumo.loc[0, 'carteira_total'])
    valor_em_atraso = float(resumo.loc[0, 'valor_em_atraso'])
    taxa_oficial = (valor_em_atraso / carteira_total) if carteira_total else 0.0

    return {
        'carteira_total': carteira_total,
        'valor_em_atraso': valor_em_atraso,
        'taxa_oficial': taxa_oficial,
    }


st.set_page_config(page_title='Dashboard BI - TechVendas', layout='wide', initial_sidebar_state='expanded')

if 'ui_theme' not in st.session_state:
    st.session_state.ui_theme = 'Claro'

st.sidebar.markdown('### Aparência')
st.sidebar.radio('Modo', ['Claro', 'Escuro'], key='ui_theme', horizontal=True)
apply_ui_theme(st.session_state.ui_theme)

st.image('Logo.png', width=220)
st.title('Painel de Inteligência de Negócios - TechVendas')

try:
    df = load_data()
    inad_oficial = load_official_inad_metrics()
except Exception as exc:
    st.error(f'Erro ao carregar dados do banco: {exc}')
    st.stop()

if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = [
        {
            'role': 'assistant',
            'content': 'Olá! Sou seu assistente financeiro. Pergunte sobre risco, sazonalidade, vendedores ou categorias.'
        }
    ]

st.sidebar.header('Filtros')
anos = sorted([int(a) for a in df['ano'].dropna().unique()])
cats = sorted(set(df['categorias_lista'].explode().dropna().tolist()))
vends = sorted(df['vendedor_nome'].dropna().unique())

ano_sel = st.sidebar.multiselect('Ano', anos, default=[])
cat_sel = st.sidebar.multiselect('Categoria de Produto', cats, default=[])
vend_sel = st.sidebar.multiselect('Vendedor', vends, default=[])

st.sidebar.divider()
st.sidebar.markdown('### Tech Bot')
st.sidebar.caption('Converse com a IA sobre vendas, inadimplência, vendedores e categorias usando os dados filtrados.')

if st.sidebar.button('Limpar conversa', key='clear_chat', width='stretch'):
    st.session_state.chat_messages = [
        {
            'role': 'assistant',
            'content': 'Conversa reiniciada. Como posso ajudar na análise financeira?'
        }
    ]
    st.rerun()

with st.sidebar.container(border=True):
    st.markdown('**Histórico**')
    with st.container(height=320):
        for msg in st.session_state.chat_messages[-20:]:
            role_label = '👤 Você' if msg['role'] == 'user' else '🤖 Tech Bot'
            st.markdown(f"**{role_label}:** {msg['content']}")

    st.markdown('**Nova mensagem**')
    pending_question = st.chat_input(
        'Digite sua pergunta para o Tech Bot',
        key='chat_question_input'
    )

if pending_question:
    pending_question = pending_question.strip()

f = df.copy()
if ano_sel:
    f = f[f['ano'].isin(ano_sel)]
if vend_sel:
    f = f[f['vendedor_nome'].isin(vend_sel)]
if cat_sel:
    f = f[f['categorias_lista'].apply(lambda items: any(cat in items for cat in cat_sel))]

if f.empty:
    st.warning('Nenhum registro encontrado com os filtros atuais. Ajustando filtros para exibir todos os dados.')
    f = df.copy()

total_vendido = f['valor_total'].sum()
ticket_medio = f['valor_total'].mean() if len(f) else 0
total_inadimplente_filtros = f['valor_inadimplente'].sum()
taxa_inadimplencia_filtros = (total_inadimplente_filtros / total_vendido) if total_vendido else 0

carteira_total_oficial = inad_oficial['carteira_total']
total_inadimplente_oficial = inad_oficial['valor_em_atraso']
taxa_inadimplencia_oficial = inad_oficial['taxa_oficial']

qtd_notas_total = f['id_nota_fiscal'].nunique()
qtd_notas_inad = f[f['inadimplente'] == 1]['id_nota_fiscal'].nunique()
taxa_contagem = (qtd_notas_inad / qtd_notas_total) if qtd_notas_total else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric('Total Vendido', format_currency_human(total_vendido))
k2.metric('Ticket Médio', format_currency_human(ticket_medio))
k3.metric(
    'Saldo em Atraso (Oficial)',
    format_currency_human(total_inadimplente_oficial),
    help='Soma de valor_original dos títulos vencidos e não pagos em financeiro.conta_receber.'
)
k4.metric(
    'Taxa Inad. Oficial',
    f'{taxa_inadimplencia_oficial:.2%}',
    help='Valor em atraso ÷ Carteira total, usando somente financeiro.conta_receber (metodologia oficial).'
)
k5.metric(
    'Notas Inadimplentes',
    f'{taxa_contagem:.2%}',
    help=f'{qtd_notas_inad:,} de {qtd_notas_total:,} notas fiscais com saldo vencido em aberto.'
)
st.caption(
    f'ℹ️ Metodologia oficial (resumo): valor em atraso ÷ carteira total, com base em financeiro.conta_receber.'
)
with st.expander('Ver detalhes da metodologia'):
    st.markdown(
        f'- **Base oficial:** `financeiro.conta_receber`\n'
        f'- **Carteira total:** soma de `valor_original`\n'
        f'- **Valor em atraso:** títulos com `data_recebimento IS NULL` e `vencimento < CURRENT_DATE`\n'
        f'- **Taxa oficial:** `valor_em_atraso / carteira_total`\n\n'
        f'**Carteira oficial:** {format_currency_human(carteira_total_oficial)}  \n'
        f'**Em atraso oficial:** {format_currency_human(total_inadimplente_oficial)}  \n'
        f'**Taxa por notas (visão analítica filtrada):** {qtd_notas_inad:,} de {qtd_notas_total:,} ({taxa_contagem:.2%})'
    )

st.markdown('### Análise Qualitativa com IA (Groq)')
resumo_numerico_ia = (
    f"Vendas totais: {format_currency_full(total_vendido)}\n"
    f"Ticket médio: {format_currency_full(ticket_medio)}\n"
    f"Carteira total oficial: {format_currency_full(carteira_total_oficial)}\n"
    f"Total em atraso oficial: {format_currency_full(total_inadimplente_oficial)}\n"
    f"Taxa de inadimplência oficial: {taxa_inadimplencia_oficial:.2%}"
)

total_notas = f['id_nota_fiscal'].nunique(dropna=True)
periodo_inicio = f['data_emissao'].min()
periodo_fim = f['data_emissao'].max()
periodo_texto = (
    f"{periodo_inicio.date()} até {periodo_fim.date()}"
    if pd.notna(periodo_inicio) and pd.notna(periodo_fim)
    else 'Período não identificado'
)

# Vendas por ano
vendas_ano = (
    f.groupby(f['data_emissao'].dt.year, as_index=True)['valor_total']
    .sum()
    .sort_index()
)
vendas_ano_texto = '; '.join([f"{int(ano)}: {format_currency_full(val)}" for ano, val in vendas_ano.items()])

# Top categorias com valor
top_categorias_val = (
    f[['categoria_produto', 'valor_total', 'lucro']]
    .assign(categoria_produto=f['categoria_produto'].fillna('Sem categoria'))
    .assign(categoria_produto=lambda d: d['categoria_produto'].str.split(' / '))
    .explode('categoria_produto')
    .groupby('categoria_produto', as_index=False)
    .agg(valor_total=('valor_total', 'sum'), lucro=('lucro', 'sum'))
    .sort_values('valor_total', ascending=False)
    .head(10)
)
categorias_texto = '; '.join([
    f"{row['categoria_produto']}: vendas={format_currency_full(row['valor_total'])}, lucro={format_currency_full(row['lucro'])}"
    for _, row in top_categorias_val.iterrows()
]) if len(top_categorias_val) else 'Sem categorias encontradas.'

# Top UFs com inadimplência
top_ufs_val = (
    f.groupby('uf', as_index=False)
    .agg(valor_total=('valor_total', 'sum'), inad=('valor_inadimplente', 'sum'))
    .assign(taxa_inad=lambda d: d['inad'] / d['valor_total'].where(d['valor_total'] != 0, 1))
    .sort_values('valor_total', ascending=False)
    .head(10)
)
ufs_texto = '; '.join([
    f"{row['uf']}: vendas={format_currency_full(row['valor_total'])}, inadimplência={row['taxa_inad']:.1%}"
    for _, row in top_ufs_val.iterrows()
]) if len(top_ufs_val) else 'Sem UFs encontradas.'

# Top vendedores com valores
vendedores_top = (
    f.groupby('nome_vendedor', dropna=True)['valor_total']
    .sum()
    .sort_values(ascending=False)
    .head(20)
)
vendedores_lista = [f"{v}: {format_currency_full(val)}" for v, val in vendedores_top.items() if str(v).strip()]
vendedores_texto = '; '.join(vendedores_lista) if vendedores_lista else 'Sem vendedores encontrados.'
total_vendedores = f['nome_vendedor'].nunique(dropna=True)

contexto_chat = (
    f"{resumo_numerico_ia}\n"
    f"Total de notas fiscais: {total_notas}\n"
    f"Período dos dados: {periodo_texto}\n"
    f"Vendas por ano: {vendas_ano_texto}\n"
    f"Total de vendedores únicos: {total_vendedores}\n"
    f"Top vendedores por valor vendido (até 20): {vendedores_texto}\n"
    f"Categorias com vendas e lucro (até 10): {categorias_texto}\n"
    f"UFs com vendas e inadimplência (até 10): {ufs_texto}"
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
                    'Você é um assistente de dados somente leitura da empresa TechVendas.\n'
                    'Responda em português, de forma objetiva, usando apenas os dados reais da empresa abaixo.\n'
                    'Não invente informações.\n\n'
                    'Quando solicitado a gerar SQL, siga OBRIGATORIAMENTE estas regras:\n'
                    'PERMITIDO: apenas SELECT, WHERE, GROUP BY, ORDER BY, JOIN, LIMIT.\n'
                    'PROIBIDO: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, DO, EXECUTE, CALL ou qualquer função que modifique dados.\n'
                    'Use LIMIT 100 obrigatoriamente nas queries SQL.\n'
                    'Não use ponto e vírgula nas queries SQL.\n'
                    'Se a pergunta não puder ser respondida com esses dados, diga claramente que não há dados suficientes.\n\n'
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
    .sort_values('valor_total', ascending=False)
)

with g1:
    chart_header('Vendas por Categoria', 'Compara o faturamento acumulado por categoria (base filtrada).')
    fig_bar = px.bar(
        vendas_cat,
        x='categoria_produto',
        y='valor_total',
        labels={'categoria_produto': 'Categoria', 'valor_total': 'Valor vendido'},
        color_discrete_sequence=[px.colors.sequential.Blues[5]],
    )
    fig_bar.update_traces(opacity=0.9)
    fig_bar.update_layout(xaxis_tickangle=-20)
    fig_bar = style_chart(fig_bar)
    g1.plotly_chart(fig_bar, width='stretch', theme=None)

serie_tempo = f.groupby('mes', as_index=False)['valor_total'].sum().sort_values('mes')
with g2:
    chart_header('Evolução de Vendas', 'Mostra tendência mensal de faturamento para leitura de sazonalidade.')
    fig_line = px.line(
        serie_tempo,
        x='mes',
        y='valor_total',
        labels={'mes': 'Mês', 'valor_total': 'Valor vendido'},
        markers=True,
        color_discrete_sequence=[px.colors.sequential.Blues[7]],
    )
    fig_line = style_chart(fig_line)
    g2.plotly_chart(fig_line, width='stretch', theme=None)

st.markdown('### Análise de Receita: evolução mensal e sazonalidade')

MESES_PT = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio',
            6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro',
            11: 'Novembro', 12: 'Dezembro'}

receita_mes = f.copy()
receita_mes['mes_num'] = receita_mes['data_emissao'].dt.month
receita_mes['mes_nome'] = receita_mes['mes_num'].map(MESES_PT)

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
rec_c2.metric('Mês de menor receita', mes_fraco['mes'] if mes_fraco is not None else '-')
rec_c3.metric('Variação pico x menor receita', f'{variacao_sazonal:.2%}')

st.info('Existe sazonalidade? ' + ('Sim, há indícios relevantes.' if ha_sazonalidade else 'Não, a variação mensal é relativamente estável.'))

sazonalidade_view = sazonalidade[['mes', 'venda_total', 'venda_media']].copy()
sazonalidade_view['venda_total'] = sazonalidade_view['venda_total'].apply(
    lambda value: f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
)
sazonalidade_view['venda_media'] = sazonalidade_view['venda_media'].apply(
    lambda value: f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
)
sazonalidade_view = sazonalidade_view.rename(columns={
    'mes': 'Mês',
    'venda_total': 'Venda Total',
    'venda_media': 'Venda Média',
})
render_table(sazonalidade_view, hide_index=True)

st.subheader('Análises Complementares')

gx1, gx2 = st.columns(2)
altura_cards_complementares = 520

with gx1:
    chart_header('Participação por Categoria', 'Distribuição percentual das vendas entre as categorias.')
    vendas_cat_bar = vendas_cat.copy()
    total_categoria = vendas_cat_bar['valor_total'].sum()
    vendas_cat_bar['participacao'] = (
        vendas_cat_bar['valor_total'] / total_categoria if total_categoria else 0
    )
    vendas_cat_bar['valor_vendido_fmt'] = vendas_cat_bar['valor_total'].apply(format_currency_full)
    vendas_cat_bar = vendas_cat_bar.sort_values('participacao', ascending=False)

    fig_participacao = px.bar(
        vendas_cat_bar,
        x='participacao',
        y='categoria_produto',
        orientation='h',
        text='participacao',
        labels={
            'categoria_produto': 'Categoria',
            'participacao': 'Participação',
            'valor_vendido_fmt': 'Valor Vendido',
        },
        color='participacao',
        color_continuous_scale='Blues',
        hover_data={'valor_vendido_fmt': True, 'valor_total': False},
    )
    fig_participacao.update_traces(
        texttemplate='%{text:.1%}',
        textposition='outside',
        hovertemplate='<b>Categoria</b>: %{y}<br><b>Participação</b>: %{x:.1%}<br><b>Valor Vendido</b>: %{customdata[0]}<extra></extra>',
    )
    fig_participacao.update_layout(
        height=altura_cards_complementares,
        yaxis={'categoryorder': 'total ascending'},
        coloraxis_showscale=False,
    )
    fig_participacao = style_chart(fig_participacao)
    fig_participacao.update_xaxes(tickformat='.0%')
    gx1.plotly_chart(fig_participacao, width='stretch', theme=None)

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
analise_view['custo_total'] = analise_view['custo_total'].apply(
    lambda value: f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
)
analise_view['lucro_total'] = analise_view['lucro_total'].apply(
    lambda value: f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
)
analise_view['margem_lucro'] = analise_view['margem_lucro'].apply(lambda value: f'{value:.2%}')
analise_view = analise_view.rename(columns={
    'categoria_produto': 'Categoria do Produto',
    'volume_vendido': 'Volume Vendido',
    'custo_total': 'Custo Total',
    'lucro_total': 'Lucro Total',
    'margem_lucro': 'Margem de Lucro',
})
render_table(analise_view, hide_index=True)

top_vendedores = (
    f.groupby('vendedor_nome', as_index=False)['valor_total']
    .sum()
    .sort_values('valor_total', ascending=False)
    .head(10)
)
top_vendedores['comissao_2_5_pct'] = top_vendedores['valor_total'] * 0.025

inad_uf = f.groupby('uf', as_index=False).agg(total=('valor_total', 'sum'), inad_valor=('valor_inadimplente', 'sum'))
inad_uf['taxa_inadimplencia'] = inad_uf['inad_valor'] / inad_uf['total'].where(inad_uf['total'] != 0, 1)
inad_uf = inad_uf.sort_values('taxa_inadimplencia', ascending=False)

with gx2:
    chart_header('Top 10 Vendedores', 'Ranking por valor vendido e comissão de 2,5%.')
top_vendedores_view = top_vendedores.rename(
    columns={
        'vendedor_nome': 'Vendedor',
        'valor_total': 'Valor Vendido',
        'comissao_2_5_pct': 'Comissão (2,5%)',
    }
).copy()
top_vendedores_view['Valor Vendido'] = top_vendedores_view['Valor Vendido'].apply(
    lambda value: f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
)
top_vendedores_view['Comissão (2,5%)'] = top_vendedores_view['Comissão (2,5%)'].apply(
    lambda value: f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
)
top_vendedores_view.insert(0, 'Ranking', range(1, len(top_vendedores_view) + 1))
with gx2:
    render_table(top_vendedores_view, height=altura_cards_complementares, hide_index=True)

chart_header(
    'Inadimplência por UF',
    f'Taxa monetária filtrada (saldo vencido ÷ total vendido). Linha tracejada = média filtrada ({taxa_inadimplencia_filtros:.2%}).'
)
fig_inad_uf = px.bar(
    inad_uf,
    x='uf',
    y='taxa_inadimplencia',
    text='taxa_inadimplencia',
    color='taxa_inadimplencia',
    color_continuous_scale='Reds',
    labels={'uf': 'UF', 'taxa_inadimplencia': 'Taxa Inad.'},
)
fig_inad_uf.update_traces(texttemplate='%{text:.1%}', textposition='outside')
fig_inad_uf.update_layout(coloraxis_showscale=False)
fig_inad_uf.add_hline(
    y=taxa_inadimplencia_filtros,
    line_dash='dash',
    line_color=px.colors.sequential.Reds[-1],
    annotation_text=f'Média: {taxa_inadimplencia_filtros:.1%}',
    annotation_position='top right',
)
fig_inad_uf = style_chart(fig_inad_uf, y_is_percent=True)
st.plotly_chart(fig_inad_uf, width='stretch', theme=None)

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
render_table(inad_uf_view, hide_index=True)

# --- Pergunta extra: UFs com alta receita E alta inadimplência (prioridade de ação) ---
chart_header('Prioridade por UF', 'Ranking de UFs com alta receita e alta inadimplência para foco de cobrança.')

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
    coloraxis_colorbar_title='Taxa Inad.',
    coloraxis_colorbar_tickformat='.0%',
)
fig_prioridade = style_chart(fig_prioridade)
st.plotly_chart(fig_prioridade, width='stretch', theme=None)

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
prioridade_view.insert(0, 'Ranking', range(1, len(prioridade_view) + 1))
render_table(prioridade_view, hide_index=True)

