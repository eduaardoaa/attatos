import streamlit as st
import pandas as pd
import plotly.express as px

def verificar_autenticacao():
    """Verifica se o usuário está autenticado (fez login)"""
    if not st.session_state.get('authenticated', False):
        st.error("Você precisa fazer login para acessar esta página!")
        st.session_state.page = None
        st.rerun()

def paginaresidencia():
    verificar_autenticacao()
    
    # Configuração da página
    st.set_page_config(page_title="TESTEAARNAISNAND", page_icon="📊", layout="wide")
    
    # Barra lateral
    if 'user_info' in st.session_state:

        # Adicionar botão Voltar apenas para administradores
        if st.session_state.user_info['permissao'].lower() == 'adm':
            if st.sidebar.button("⬅️ Voltar para Administração"):
                st.session_state.page = 'adm'  # Assumindo que 'adm' é o nome do módulo/arquivo
                st.rerun()
    

    
