#############################################################################
# Projeto Hospital Inova Parque (Contagem)
# Equipe: 
# Carlos Soares 
# Francisco Cardoso 
# Ivan Black 
# Lasara Fabricia Rodrigues 
# Desenvolvimento: João Flávio de Freitas Almeida <joao.flavio@dep.ufmg.br>
# LEPOINT: Laboratório de Estudos em Planejamento de Operações Integradas
# Departamento de Engenharia de Produção
# Universidade Federal de Minas Gerais - Escola de Engenharia
#############################################################################

import streamlit as st
import pandas as pd
import folium
import json
from streamlit_folium import st_folium
from branca.element import Template, MacroElement

# Rodando...
# streamlit run app.py
# echo Running Streamlit ...
# streamlit run app.py --server.runOnSave true


# ---------- Cabeçalho com logo ----------

from PIL import Image

st.set_page_config(layout="wide")

logo_esquerda = Image.open("figs/logo.png")         # Substitua pelo caminho da sua logo da esquerda
logo_direita = Image.open("figs/logo2.png")  # Substitua pelo caminho da sua logo da direita

col1, col2, col3 = st.columns([1, 4, 1])

with col1:
    st.image(logo_esquerda, width=120)

with col3:
    st.image(logo_direita, width=120)

st.markdown(
    """
    <h1 style='text-align: center; color: #444;'>Mapa de Fluxos de pacientes para o Inova Parque</h1>
    <h4 style='text-align: center; color: #777;'>Equipe: Carlos, Francisco, Ivan, João Flávio, Lasara, Leonardo e Marcone</h4>
    <hr>
    """,
    unsafe_allow_html=True
)

# ---------- 1. Título ----------
st.title("Fluxos de municípios para o Inova Parque")


# ---------- 2. Carregar dados ----------
df = pd.read_csv("AtendMunicipios.csv")
df_municipios = df.copy()

df["Servico"] = df["Servico"].str.strip().str.upper()

with open("municipios.json", encoding="utf-8-sig") as f:
    municipios = json.load(f)

geo_df = pd.DataFrame(municipios)[["codigo_ibge", "nome", "latitude", "longitude"]]
geo_df["Codigo"] = geo_df["codigo_ibge"].astype(str).str[:6].astype(int)

# Merge com as coordenadas
df = df.merge(geo_df[["Codigo", "nome", "latitude", "longitude"]], on="Codigo", how="left")
df["Municipio"] = df["nome"]
df = df.drop(columns=["nome"])

# Coordenadas de Contagem
# contagem_coords = geo_df[geo_df["Codigo"] == 311860][["latitude", "longitude"]].iloc[0].tolist()
contagem_coords = geo_df[geo_df["Codigo"] == 100000][["latitude", "longitude"]].iloc[0].tolist()


# ---------- 3. Interface de Filtros ----------

# Lista de serviços
servico_legenda = {
    'S1':  "Pronto Atendimento Emergência",
    'S2':  "Diagnóstico por Imagem / Radioterapia",
    'S3':  "Endoscopia / Colonoscopia",
    'S4':  "Internação Clínica",
    'S5':  "Cirurgia Ambulatorial",
    'S6':  "UTI / Terapia Intensiva",
    'S7':  "Internação Cirúrgica",
    'S8':  "Hemodinâmica",
    'S9':  "Hemodiálise / TRS",
    'S10': "Quimioterapia / Hemoterapia",
    'S11': "Consultas Eletivas / Pós-Cirúrgicas"
}

colors = {
    'S1': 'red',
    'S2': 'blue',
    'S3': 'green',
    'S4': 'purple',
    'S5': 'orange',
    'S6': 'pink',
    'S7': 'cadetblue',
    'S8': 'darkred',
    'S9': 'lightgreen',
    'S10': 'darkblue',
    'S11': 'gray'
}

# Inverter o dicionário: descrição -> key
descricao_para_key = {v: k for k, v in servico_legenda.items()}

# Filtro de serviços - mostra descrições
servicos_descricoes_selecionadas = st.multiselect(
    "Selecione os serviços:", 
    # options=list(servico_legenda.keys()), 
    options=list(servico_legenda.values()), 
    default=[],  # Nenhum selecionado inicialmente
    key="servicos_municipios")

# Filtro de serviços
servicos_selecionados = [descricao_para_key[desc] for desc in servicos_descricoes_selecionadas]

# Filtro de distância
dist_max = st.slider("Distância máxima (km):", min_value=0, max_value=700, value=250)

# Aplicar os filtros
df_filtrado = df[df["Servico"].isin(servicos_selecionados) & (df["Distancia"] <= dist_max)]

# ---------- 4. Gerar o Mapa ----------
m = folium.Map(location=contagem_coords, zoom_start=7, tiles="CartoDB positron")

for _, row in df_filtrado.iterrows():
    if pd.isna(row["latitude"]):
        continue

    origem_coords = (row["latitude"], row["longitude"])
    servico = row["Servico"]
    atendimento = row["Atendimento"]
    cor = colors.get(servico, "gray")
    radius = 5 + atendimento / 30
    radius = min(radius, 15)

    folium.PolyLine(
        locations=[origem_coords, contagem_coords],
        color=cor,
        weight=2,
        tooltip=(
            f"<b>{row['Municipio']}</b> → Inova Parque<br>"
            f"Serviço: {servico} - {servico_legenda[servico]}<br>"
            f"Atendimentos: {atendimento}<br>"
            f"Distância: {row['Distancia']} km"
        ),
        opacity=0.7
    ).add_to(m)

    folium.CircleMarker(
        location=origem_coords,
        radius=radius,
        color=cor,
        fill=True,
        fill_color=cor,
        fill_opacity=0.8,
        popup=row["Municipio"]
    ).add_to(m)

# Marcador de Contagem
folium.Marker(
    location=contagem_coords,
    popup="Inova Parque (Destino)",
    # icon=folium.Icon(color="black", icon="hospital", prefix='fa') 
    # icones = ['hospital', 'plus-square', 'medkit', 'ambulance', 'stethoscope']
    icon=folium.Icon(color="red", icon="medkit", prefix='fa') 
).add_to(m)

# ---------- 5. Exibir o Mapa no Streamlit ----------
st.subheader("Atendimentos previstos no Inova Parque")
# st_data = st_folium(m, width=900, height=600)
st_data = st_folium(m, width=1600, height=800)



# -- FLUXO INTERNO A CONTAGEM: UPAS E UBS --

# Taxa de encaminhamento das UPAs de Contagem
# Contagem (JK) = (20 000 / 45 356) × 100 ≈ 44,1 %
# Industrial = (7 500 / 45 356) × 100 ≈ 16,5 %
# Vargem das Flores = (6 935 / 45 356) × 100 ≈ 15,3 %
# Ressaca = (6 421 / 45 356) × 100 ≈ 14,2 %
# Petrolândia = (4 500 / 45 356) × 100 ≈ 9,9 %
               
# Taxa de encaminhamento UBS -> Hospital: ≈ 20%, com resolutividade de 85%
# Estimativa da distribuição dos tipos de encaminhamentos 
# (casos entre 100 pacientes encaminhados):
# S2	30%
# S3	5%
# S4	15%
# S5	1%
# S6	5%
# S7	1%
# S8	2%
# S9	8%
# S10	8%
# S11	7%

# ------------ 1. Carregar dados ------------
# Lê o CSV de atendimentos
dfu = pd.read_csv("AtendContagem.csv")
df_upa_ubs = df.copy()

dfu["Servico"] = dfu["Servico"].str.strip().str.upper()

# Converte a coluna Atendimento para numérico (caso não esteja)
dfu["Atendimento"] = pd.to_numeric(dfu["Atendimento"], errors="coerce")

# Filtra apenas as linhas com Atendimento > 0
# dfu = dfu[dfu["Atendimento"] > 0]
# print(dfu.head())

# Coordenadas de Inova Parque
inova_row = dfu[dfu['Unidade'] == 'Inova Parque'].iloc[0]
unid_coords = [inova_row['latitude'], inova_row['longitude']]


# ---------- 4. Criar o mapa ----------
mu = folium.Map(location=unid_coords, zoom_start=15, tiles="CartoDB positron")

# # Filtro de serviços
# servicos_selecionados_upa_ubs = st.multiselect(
#     "Selecione os serviços:",
#     # options=list(servico_legenda.keys()),
#     options=list(servico_legenda.values()),
#     default=[],  # Nenhum selecionado inicialmente
#     key="servicos_upa_ubs")

# Filtro de serviços - mostra descrições
servicos_descricoes_selecionadas_upa_ubs = st.multiselect(
    "Selecione os serviços:", 
    # options=list(servico_legenda.keys()), 
    options=list(servico_legenda.values()), 
    default=[],  # Nenhum selecionado inicialmente
    key="servicos_municipios_upa_ubs")

# Inverter o dicionário: descrição -> key
descricao_para_key_upa_ubs = {v: k for k, v in servico_legenda.items()}

# Filtro de serviços
servicos_selecionados_upa_ubs = [descricao_para_key_upa_ubs[desc] for desc in servicos_descricoes_selecionadas_upa_ubs]


# Aplicar os filtros
dfu_filtrado = dfu[dfu["Servico"].isin(servicos_selecionados_upa_ubs)]
print(dfu_filtrado.head())

# ---------- 5. Adicionar fluxos ----------
for _, row in dfu_filtrado.iterrows():
    if pd.isna(row["latitude"]):
        continue

    origem_coords = (row["latitude"], row["longitude"])
    servico = row["Servico"]
    atendimento = row["Atendimento"]    
    cor = colors.get(servico, "gray")

    descricao = row['Unidade']  # ou 'Descricao', dependendo da sua planilha

    if "upa" in descricao.lower():
        cor = "red"
        radius= 5 + atendimento / 30  # opcional: ajusta o tamanho ao volume        
        if radius > 15:
            radius = 15
    else:
    # elif "basica" in descricao.lower():
        cor = colors.get(servico, "gray")
        # cor = "blue"
        radius= 5 + atendimento / 30  # opcional: ajusta o tamanho ao volume        
        if radius > 10:
            radius = 10
    # else:
    #     cor = "gray"
    #     radius = 5
    

    folium.PolyLine(
        locations=[origem_coords, unid_coords],
        color=cor,
        # weight=2 + atendimento / 20,
        weight=2,
        tooltip=(
            f"<b>{row['Unidade']}</b> → Inova Parque<br>"
            f"Serviço: {servico} - {servico_legenda[servico]}<br>"
            f"Atendimentos: {atendimento}<br>"
            f"Distância: {row['Distancia']} km"
        ),
        opacity=0.7
    ).add_to(mu)


    folium.CircleMarker(
        location=origem_coords,
        radius=radius,
        color=cor,
        fill=True,
        fill_color=cor,
        fill_opacity=0.8,
        popup=row["Unidade"]
    ).add_to(mu)


# Marcador de Contagem
folium.Marker(
    location=unid_coords,
    popup="Inova Parque (Destino)",
    # icon=folium.Icon(color="black", icon="hospital", prefix='fa') 
    # icones = ['hospital', 'plus-square', 'medkit', 'ambulance', 'stethoscope']
    icon=folium.Icon(color="red", icon="medkit", prefix='fa') 
).add_to(mu)

# ---------- 5. Exibir o Mapa no Streamlit ----------

st.subheader("Em Contagem: Encaminhamentos de UPAs (S1) e Regiões  (S2 a S11) ao Inova Parque")
# st_data = st_folium(m, width=900, height=600)
st_data = st_folium(mu, width=1600, height=800)
