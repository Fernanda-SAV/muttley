import streamlit as st

st.set_page_config(
    page_title="Iniciativa Muttley",
    page_icon="🦅",
    layout="wide"
)

st.title("Sistema de Monitoramento de Pombos")

# Container para centralização
container = st.container()

with container:
    # Criando colunas para centralizar
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.image("pombo.png", width=1440)
        
        # Adicionando algum espaço vertical
        st.write("")
        st.write("")

st.sidebar.success("Selecione uma página acima.")