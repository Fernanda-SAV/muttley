import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go  # Importação adicional necessária
from datetime import datetime, timedelta
import random

# Configuração da página
st.set_page_config(page_title="Análise de Ativos Portuários", layout="wide")

# Título do dashboard
st.title("🌍 Análise de Ativos Portuários")

# Gerar dados sintéticos robustos
def generate_asset_data():
    # Definir ativos com coordenadas em São Paulo
    assets = {
        'EMAP': {'lat': -2.578183, 'lon': -44.36666, 'cor': '#FF0000'},
        'Granel Química': {'lat': -2.573947, 'lon': -44.3655073, 'cor': '#00FF00'},
        'Terminal de Cobre': {'lat': -2.570986, 'lon': -44.365199, 'cor': '#0000FF'},
    }
    
    # Gerar dados para os últimos 30 dias
    days = 30
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    dates = [base_date - timedelta(days=i) for i in range(days)]
    
    data = []
    for dt in dates:
        for asset, info in assets.items():
            # Variação por dia da semana (pico na quarta-feira)
            weekday = dt.weekday()
            weekday_factor = 1.0 + 0.7 * (weekday == 2) - 0.3 * (weekday >= 5)
            
            # Variação por hora do dia (pico às 15h)
            for hour in range(24):
                hour_factor = 0.5 + 1.5 * np.exp(-((hour - 15)/4)**2)
                
                # Valor base com variação aleatória
                base_value = 20 * weekday_factor * hour_factor
                value = max(1, int(np.random.poisson(base_value)))
                
                data.append({
                    'Data': dt.date(),
                    'DiaSemana': ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'][weekday],
                    'Ativo': asset,
                    'Latitude': info['lat'],
                    'Longitude': info['lon'],
                    'Cor': info['cor'],
                    'Ocorrências': value,
                    'Hora': hour
                })
    
    return pd.DataFrame(data)

# Carregar dados
df = generate_asset_data()
all_assets = df['Ativo'].unique()
all_dates = sorted(df['Data'].unique())
weekdays = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']

# Container para os filtros
with st.container():
    st.header("Filtros de Análise")
    
    # Seleção do modo de filtro (dia específico ou dia da semana)
    filtro_mode = st.radio(
        "Tipo de filtro temporal:",
        options=["Por dia específico", "Por dia da semana"],
        horizontal=True
    )
    
    col1, col2 = st.columns(2)
    
    if filtro_mode == "Por dia específico":
        with col1:
            selected_date = st.selectbox(
                "Selecione a data:",
                options=all_dates,
                index=len(all_dates)-1,
                format_func=lambda x: x.strftime('%d/%m/%Y')
            )
        with col2:
            # Espaço vazio para alinhamento
            st.empty()
    else:
        with col1:
            selected_weekday = st.selectbox(
                "Selecione o dia da semana:",
                options=weekdays,
                index=2  # Quarta-feira como padrão
            )
        with col2:
            # Botão para selecionar todas as ocorrências desse dia da semana
            if st.button("Mostrar todas as semanas"):
                pass  # Ação já tratada no filtro
    
    col3, col4 = st.columns(2)
    with col3:
        selected_assets = st.multiselect(
            "Selecione os ativos:",
            options=all_assets,
            default=all_assets
        )
    with col4:
        hora_inicio, hora_fim = st.slider(
            "Intervalo horário:",
            min_value=0,
            max_value=23,
            value=(8, 18)
        )

# Filtrar dados conforme o modo selecionado
if filtro_mode == "Por dia específico":
    filtered_df = df[
        (df['Data'] == selected_date) &
        (df['Ativo'].isin(selected_assets)) &
        (df['Hora'] >= hora_inicio) &
        (df['Hora'] <= hora_fim)
    ]
else:
    filtered_df = df[
        (df['DiaSemana'] == selected_weekday) &
        (df['Ativo'].isin(selected_assets)) &
        (df['Hora'] >= hora_inicio) &
        (df['Hora'] <= hora_fim)
    ]

# Agregar dados para visualizações
heatmap_data = filtered_df.groupby(['Ativo', 'Latitude', 'Longitude', 'Cor'], as_index=False)['Ocorrências'].sum()
hourly_data = filtered_df.groupby(['Hora', 'Ativo'], as_index=False)['Ocorrências'].mean()

# Layout principal
tab1, tab2, tab3 = st.tabs(["🗺️ Mapa de Calor", "📈 Análise Temporal", "📋 Resumo"])

with tab1:
    if filtro_mode == "Por dia específico":
        st.subheader(f"Mapa de Calor - {selected_date.strftime('%d/%m/%Y')}")
    else:
        st.subheader(f"Mapa de Calor - Todas as {selected_weekday}s")
    
    if not heatmap_data.empty:
        # Criar figura com mapa de calor
        fig = go.Figure(go.Densitymapbox(
            lat=heatmap_data['Latitude'],
            lon=heatmap_data['Longitude'],
            z=heatmap_data['Ocorrências'],
            radius=30,  # Ajuste o raio para suavizar a interpolação
            colorscale='Hot',  # Escala de cores quentes
            opacity=0.8,
            hovertext=heatmap_data['Ativo'],
            hoverinfo='text+z'
        ))
        
        # Adicionar marcadores para os pontos exatos
        fig.add_trace(go.Scattermapbox(
            lat=heatmap_data['Latitude'],
            lon=heatmap_data['Longitude'],
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=8,
                color=heatmap_data['Cor'],
                opacity=0.8
            ),
            text=heatmap_data['Ativo'] + ': ' + heatmap_data['Ocorrências'].astype(str),
            hoverinfo='text'
        ))
        
        fig.update_layout(
            mapbox_style="open-street-map",
            margin={"r":0,"t":0,"l":0,"b":0},
            mapbox=dict(
                center=dict(lat=-2.573624, lon=-44.363844),
                zoom=15
            ),
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Nenhum dado disponível para os filtros selecionados.")

with tab2:
    if filtro_mode == "Por dia específico":
        st.subheader(f"Variação Horária - {selected_date.strftime('%d/%m/%Y')}")
    else:
        st.subheader(f"Variação Horária - Todas as {selected_weekday}s")
    
    if not hourly_data.empty:
        fig = px.line(
            hourly_data,
            x='Hora',
            y='Ocorrências',
            color='Ativo',
            markers=True,
            title=f"Padrão de Ocorrências ({hora_inicio}h-{hora_fim}h)"
        )
        fig.update_xaxes(tickvals=list(range(hora_inicio, hora_fim+1)))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Nenhum dado disponível para os filtros selecionados.")

with tab3:
    if filtro_mode == "Por dia específico":
        st.subheader(f"Resumo - {selected_date.strftime('%d/%m/%Y')}")
    else:
        st.subheader(f"Resumo - Todas as {selected_weekday}s")
    
    if not filtered_df.empty:
        col1, col2, col3 = st.columns(3)
        total = filtered_df['Ocorrências'].sum()
        avg = filtered_df['Ocorrências'].mean()
        peak = filtered_df['Ocorrências'].max()
        
        col1.metric("Total de Ocorrências", f"{total:,.0f}")
        col2.metric("Média por Ativo/Hora", f"{avg:.1f}")
        col3.metric("Pico em um Ativo", f"{peak:,.0f}")
        
        st.dataframe(
            filtered_df.groupby('Ativo')[['Ocorrências']].agg(['sum', 'mean', 'max'])
            .droplevel(0, axis=1)
            .rename(columns={'sum': 'Total', 'mean': 'Média', 'max': 'Pico'})
            .style.format("{:.1f}"),
            use_container_width=True
        )
        
        with st.expander("Visualizar dados completos"):
            st.dataframe(
                filtered_df.sort_values(['Ativo', 'Hora']),
                hide_index=True,
                use_container_width=True
            )
    else:
        st.warning("Nenhum dado disponível para os filtros selecionados.")

# Mapa alternativo na sidebar
st.sidebar.markdown("### 📍 Mapa de Referência")
if not heatmap_data.empty:
    map_data = heatmap_data[['Latitude', 'Longitude', 'Ativo', 'Cor', 'Ocorrências']].copy()
    map_data['Tamanho'] = np.log(map_data['Ocorrências']) * 10
    st.sidebar.map(map_data,
                   latitude='Latitude',
                   longitude='Longitude',
                   size='Tamanho',
                   color='Cor')
else:
    st.sidebar.warning("Nenhum dado para exibir no mapa")