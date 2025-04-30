import mysql.connector
import streamlit as st
from adm import paginaadm
from atos import paginaatos
from unit import paginaunit
from residencia import paginaresidencia

def conexaobanco():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="dudu2305",
            database="atoscapital"
        )
        return conn
    except mysql.connector.Error as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

def validacao(usr, passw):
    conn = conexaobanco()
    if not conn:
        return

    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM usuarios WHERE usuario = %s AND senha = %s"
    cursor.execute(query, (usr, passw))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user:
        st.session_state.authenticated = True  
        st.session_state.user_info = {
            'id': user['id'],
            'nome': user['Nome'],
            'permissao': user['permissao'],
            'nomegrupo': user.get('NomeGrupo', '')  # Adiciona NomeGrupo ao session_state
        }
        st.success('Login feito com sucesso!')

        if user['permissao'] == 'adm':
            st.session_state.page = "adm"
            st.rerun()
        elif user['permissao'] == 'cliente':
            # Verifica o NomeGrupo para redirecionar para a página correta
            nome_grupo = user.get('NomeGrupo', '').lower()
            if 'atos capital' in nome_grupo:
                st.session_state.page = "atos"
            elif 'residencia' in nome_grupo:
                st.session_state.page = "residencia"
            elif 'unit' in nome_grupo:
                st.session_state.page = "unit"
            else:
                st.session_state.page = "dashboard"  # Página padrão caso não encontre o grupo
            st.rerun()
        else:
            st.error('Permissão desconhecida. Não foi possível redirecionar.')
    else:
        st.error('Usuário ou senha incorretos, tente novamente.')

def arealogin():
    st.set_page_config(page_title="Login", page_icon="🔒", layout="centered")
    
    col1, col2, col3 = st.columns([3, 2, 3])
    with col2:
        st.image("logoatos.png", width=150)

    with st.form('sign_in'):
        st.caption('Por favor, insira seu usuário e senha.')
        username = st.text_input('Usuário')
        password = st.text_input('Senha', type='password')

        botaoentrar = st.form_submit_button(label="Entrar", type="primary", use_container_width=True)

    if botaoentrar:
        validacao(username, password)

def main():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        arealogin()
    else:
        if "page" in st.session_state:
            if st.session_state.page == "adm":
                paginaadm()

            elif st.session_state.page == "atos":
                paginaatos()
            elif st.session_state.page == "residencia":
                paginaresidencia()
            elif st.session_state.page == "unit":
                paginaunit()

if __name__ == "__main__":
    main()