import streamlit as st
import folium
from streamlit_folium import st_folium
from banco_de_dados.criacao import *
from mqtt import MosquittoLocalClient

cliente = MosquittoLocalClient("python_client")
if not cliente.connect():
    exit("Não foi possível conectar ao Mosquitto local. Verifique se o broker está rodando.")
st.set_page_config(layout="wide")
st.title("Dashboard de Ação no Porto")

# Inicializa o estado da sessão para armazenar os markers ativados
if 'markers_ativos' not in st.session_state:
    st.session_state.markers_ativos = set()

# Pontos no mapa
locais = listar_buzzers_com_ativos()
col_mapa, col_acao = st.columns([2, 1])

with col_mapa:
    # Cria o mapa-2.573624, -44.363844


    mapa = folium.Map(location=[-2.573624, -44.363844], zoom_start=16)

    for p in locais:
        # Verifica se o marker está ativado
        marker_id = f"{p['lat']}_{p['lon']}"
        cor = "red" if marker_id in st.session_state.markers_ativos else "blue"
        
        folium.Marker(
            location=[p["lat"], p["lon"]],  
            tooltip=p["nome"],
            popup=p["nome"],
            icon=folium.Icon(color=cor, icon="info-sign")
        ).add_to(mapa)

    # Usamos key para garantir que o estado seja mantido corretamente
    dados_mapa = st_folium(mapa, width=1200, height=800, key="mapa")

def obter_local_selecionado(dados_mapa):
    if dados_mapa and dados_mapa.get("last_object_clicked_tooltip"):
        lat = dados_mapa["last_object_clicked"]["lat"]
        lon = dados_mapa["last_object_clicked"]["lng"]
        
        for p in locais:
            if (abs(p["lat"] - lat) < 0.0005 and 
                abs(p["lon"] - lon) < 0.0005):
                return p
    return None

with col_acao:
    st.subheader("Detalhes do ativo portuário")
    selecionado = obter_local_selecionado(dados_mapa)
    print(dados_mapa)
    if selecionado:
        st.write(f"Você clicou neste ativo portuário **{selecionado['nome']}**")
        marker_id = f"{selecionado['lat']}_{selecionado['lon']}"
        
        col_geral1, col_geral2 = st.columns(2)
        with col_geral1:
            if st.button(f"Ativar o PEM em {selecionado['nome']}", 
                        key=f"btn_ligar_{selecionado['nome']}"):
                st.session_state.markers_ativos.add(marker_id)
                st.success(f"PEM ativado no ponto {selecionado['nome']}!")
                cliente.publicar(f"ativos/{dados_mapa["last_object_clicked_tooltip"]}", "True")
                st.rerun()
        
        with col_geral2 :
            if st.button(f"Desativar o PEM em {selecionado['nome']}", 
                        key=f"btn_desligar_{selecionado['nome']}"):
                st.session_state.markers_ativos.discard(marker_id)
                st.success(f"PEM desativado no ponto {selecionado['nome']}!")
                cliente.publicar(f"ativos/{dados_mapa["last_object_clicked_tooltip"]}", "False")
                st.rerun()
        
    else:
        st.info("Clique em um ativo para liberar o pulso PEM")
        
        # Container para os botões de ação geral
        col_geral1, col_geral2 = st.columns(2)
        
        with col_geral1:
            if st.button(f"Ativar todos os PEMs", 
                        key=f"btn_ativar_geral"):
                # Ativa todos os markers
                st.session_state.markers_ativos = {f"{p['lat']}_{p['lon']}" for p in locais}
                for local in locais:
                    cliente.publicar(f"ativos/{local['nome']}", "True")
                st.success("PEM ativado em todas as áreas!")
                st.rerun()
        
        with col_geral2:
            if st.button(f"Desativar todos os PEMs", 
                        key=f"btn_desligar_geral"):
                # Limpa todos os markers ativos
                st.session_state.markers_ativos = set()
                for local in locais:
                    cliente.publicar(f"ativos/{local['nome']}", "False")
                st.success("Todos os PEMs foram desativados!")
                st.rerun()