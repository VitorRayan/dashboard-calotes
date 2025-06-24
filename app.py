import os
import pandas as pd
import streamlit as st
import zipfile
from kaggle.api.kaggle_api_extended import KaggleApi
import plotly.express as px

st.set_page_config(page_title="Dashboard Calotes", layout="wide")

# ===== Estilo CSS moderno =====
st.markdown("""
    <style>
        .element-container {
            transition: transform 0.3s ease;
        }
        .element-container:hover {
            transform: scale(1.02);
            box-shadow: 0 0 15px rgba(0,0,0,0.1);
        }
        .block-container {
            padding-top: 2rem;
        }
        .stButton>button {
            color: white;
            background: #0083B8;
            border-radius: 8px;
        }
        /* Cards KPIs */
        .kpi {
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            margin-bottom: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .kpi-value {
            font-size: 2rem;
            font-weight: bold;
            color: #0083B8;
        }
        .kpi-label {
            font-size: 1rem;
            color: #333;
        }
    </style>
""", unsafe_allow_html=True)

# ===== Função de carregamento com API do Kaggle =====
@st.cache_data(show_spinner=True)
def load_data():
    dataset = 'uciml/default-of-credit-card-clients-dataset'
    file_name = 'UCI_Credit_Card.csv'
    zip_file = 'default-of-credit-card-clients-dataset.zip'

    api = KaggleApi()
    api.authenticate()

    if not os.path.exists(file_name):
        if not os.path.exists(zip_file):
            api.dataset_download_files(dataset, path='.', unzip=False)
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall('.')

    df = pd.read_csv('UCI_Credit_Card.csv')

    df['Educação'] = df['EDUCATION'].map({1: 'Pós-graduação', 2: 'Universitário', 3: 'Ensino Médio',
                                          4: 'Outros', 5: 'Outros', 6: 'Outros', 0: 'Outros'})
    df['Sexo'] = df['SEX'].map({1: 'Homem', 2: 'Mulher'})
    df['Estado_Civil'] = df['MARRIAGE'].map({1: 'Casado(a)', 2: 'Solteiro(a)', 3: 'Outro'}).fillna('Outro')
    df['Calote'] = df['default.payment.next.month'].map({0: 'Não Deu Calote', 1: 'Deu Calote'})
    df['Faixa_Idade'] = pd.cut(df['AGE'], bins=range(20, 81, 10), right=False)
    return df

# ===== Carregar dados =====
df = load_data()

# ===== Sidebar: Filtros =====
st.sidebar.header("🎛️ Filtros")

sexo = st.sidebar.multiselect("Sexo", df['Sexo'].unique(), default=df['Sexo'].unique())
educ = st.sidebar.multiselect("Educação", df['Educação'].unique(), default=df['Educação'].unique())
estado = st.sidebar.multiselect("Estado Civil", df['Estado_Civil'].unique(), default=df['Estado_Civil'].unique())

# Filtro faixa de idade slider
idade_min = int(df['AGE'].min())
idade_max = int(df['AGE'].max())
faixa_idade = st.sidebar.slider("Faixa de Idade", min_value=idade_min, max_value=idade_max, value=(idade_min, idade_max))

df_filtrado = df[
    (df['Sexo'].isin(sexo)) &
    (df['Educação'].isin(educ)) &
    (df['Estado_Civil'].isin(estado)) &
    (df['AGE'] >= faixa_idade[0]) & (df['AGE'] <= faixa_idade[1])
]

# ===== KPIs =====
total_clientes = len(df_filtrado)
pct_calote = 0 if total_clientes == 0 else (df_filtrado['Calote'] == 'Deu Calote').mean() * 100
media_limite = 0 if total_clientes == 0 else df_filtrado['LIMIT_BAL'].mean()

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.markdown(f"""
    <div class="kpi">
        <div class="kpi-value">{total_clientes}</div>
        <div class="kpi-label">Clientes Filtrados</div>
    </div>
""", unsafe_allow_html=True)
kpi2.markdown(f"""
    <div class="kpi">
        <div class="kpi-value">{pct_calote:.2f}%</div>
        <div class="kpi-label">Percentual de Calote</div>
    </div>
""", unsafe_allow_html=True)
kpi3.markdown(f"""
    <div class="kpi">
        <div class="kpi-value">R$ {media_limite:,.2f}</div>
        <div class="kpi-label">Limite Médio</div>
    </div>
""", unsafe_allow_html=True)

# ===== Título =====
st.title("📊 Dashboard Interativo - Análise de Calotes")
st.markdown("Visualização interativa dos dados de crédito e inadimplência dos clientes.")

# ===== Gráficos =====

# 1. Calote por idade
fig1 = px.histogram(
    df_filtrado, x="AGE", color="Calote", nbins=20, barmode="stack",
    color_discrete_map={"Não Deu Calote": "green", "Deu Calote": "red"},
    labels={"AGE": "Idade"},
    title="Distribuição de Idade com Calote",
    hover_data={"AGE": True, "Calote": True}
)
st.plotly_chart(fig1, use_container_width=True)

# 2. Limite por faixa de idade (convertendo intervalo para string)
df_filtrado['Faixa_Idade_Str'] = df_filtrado['Faixa_Idade'].astype(str)
limite = df_filtrado.groupby('Faixa_Idade_Str')['LIMIT_BAL'].mean().reset_index()
fig2 = px.bar(limite, x='Faixa_Idade_Str', y='LIMIT_BAL', title="Média de Limite por Faixa de Idade",
              labels={'LIMIT_BAL': 'Limite Médio', 'Faixa_Idade_Str': 'Faixa de Idade'},
              color='LIMIT_BAL', color_continuous_scale='Blues',
              hover_data={'LIMIT_BAL': ':.2f'})
st.plotly_chart(fig2, use_container_width=True)

# 3. Calote por Estado Civil
estado_data = df_filtrado.groupby(['Estado_Civil', 'Calote']).size().reset_index(name='Contagem')
fig3 = px.bar(estado_data, x='Estado_Civil', y='Contagem', color='Calote', barmode='group',
              color_discrete_map={"Não Deu Calote": "green", "Deu Calote": "red"},
              title="Calote por Estado Civil",
              hover_data={'Contagem': True})
st.plotly_chart(fig3, use_container_width=True)

# 4. Calote por Educação
educ_data = df_filtrado.groupby(['Educação', 'Calote']).size().reset_index(name='Total')
fig4 = px.bar(educ_data, x='Educação', y='Total', color='Calote', barmode='group',
              color_discrete_map={"Não Deu Calote": "green", "Deu Calote": "red"},
              title="Calote por Escolaridade",
              hover_data={'Total': True})
st.plotly_chart(fig4, use_container_width=True)

# ===== Tabela final =====
st.subheader("📋 Tabela com Dados Filtrados")
st.dataframe(df_filtrado[['ID', 'Sexo', 'Educação', 'Estado_Civil', 'AGE', 'LIMIT_BAL', 'Calote']].reset_index(drop=True))
