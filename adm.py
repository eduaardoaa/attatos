import mysql.connector
import streamlit as st
import importlib

def verificar_permissao():
    if not st.session_state.get('authenticated', False):
        st.error("Você não está autenticado!")
        st.session_state.page = None
        st.rerun()
    
    if st.session_state.user_info.get('permissao') != 'adm':
        st.error("Acesso negado: Permissão insuficiente!")
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.session_state.page = None
        st.rerun()

def conectarbanco():
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

def puxargrupos():
    conexao = conectarbanco()
    if conexao:
        cursor = conexao.cursor()
        cursor.execute("SELECT id, NomeGrupo, codigo FROM grupoempresa ORDER BY id ASC")
        grupos = cursor.fetchall()
        conexao.close()
        return grupos
    return []

def puxarusuarios():
    conexao = conectarbanco()
    if conexao:
        cursor = conexao.cursor()
        cursor.execute("SELECT id, `Nome`, usuario, senha, numero, permissao, NomeGrupo, codigo FROM usuarios ORDER BY id ASC")
        usuarios = cursor.fetchall()
        conexao.close()
        return usuarios
    return []

def atualizacaousuarios(user_id, nome, usuario, senha, numero, permissao, nome_grupo, codigo_grupo):
    conexao = conectarbanco()
    if conexao:
        cursor = conexao.cursor()

        cursor.execute("SELECT id FROM usuarios WHERE usuario = %s AND id != %s", (usuario, user_id))
        usuario_existente = cursor.fetchone()

        cursor.execute("SELECT id FROM usuarios WHERE numero = %s AND id != %s", (numero, user_id))
        numero_existente = cursor.fetchone()

        if usuario_existente:
            st.error("Nome de usuário já está sendo utilizado por outro usuário.")
            return False

        if numero_existente:
            st.error("Número já está sendo utilizado por outro usuário.")
            return False

        cursor.execute(
            "UPDATE usuarios SET `Nome` = %s, usuario = %s, senha = %s, numero = %s, permissao = %s, NomeGrupo = %s, codigo = %s WHERE id = %s",
            (nome, usuario, senha, numero, permissao, nome_grupo if nome_grupo else None, codigo_grupo if codigo_grupo else None, user_id)
        )
        conexao.commit()
        conexao.close()
        return True
    return False

def excluirusuario(user_id):
    conexao = conectarbanco()
    if conexao:
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (user_id,))
        conexao.commit()
        conexao.close()
        st.success("Usuário excluído com sucesso!")

def novousuario(nome, usuario, senha, numero, permissao, nome_grupo, codigo_grupo):
    conexao = conectarbanco()
    if conexao:
        cursor = conexao.cursor()

        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = %s", (usuario,))
        count_usuario = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE numero = %s", (numero,))
        count_numero = cursor.fetchone()[0]

        if count_usuario > 0:
            st.error("Nome de usuário já está sendo utilizado.")
            return False

        if count_numero > 0:
            st.error("Número já está sendo utilizado.")
            return False

        cursor.execute(
            "INSERT INTO usuarios (`Nome`, usuario, senha, numero, permissao, NomeGrupo, codigo) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (nome, usuario, senha, numero, permissao, nome_grupo if nome_grupo else None, codigo_grupo if codigo_grupo else None)
        )
        conexao.commit()
        conexao.close()
        return True
    return False

def novogrupo(nome_grupo, codigo):
    conexao = conectarbanco()
    if conexao:
        cursor = conexao.cursor()

        cursor.execute("SELECT COUNT(*) FROM grupoempresa WHERE NomeGrupo = %s", (nome_grupo,))
        count_grupo = cursor.fetchone()[0]

        if count_grupo > 0:
            st.error("Nome do grupo já está sendo utilizado.")
            return False

        cursor.execute(
            "INSERT INTO grupoempresa (NomeGrupo, codigo) VALUES (%s, %s)",
            (nome_grupo, codigo)
        )
        conexao.commit()
        conexao.close()
        return True
    return False

def atualizargrupo(grupo_id, novo_nome, novo_codigo):
    conexao = conectarbanco()
    if conexao:
        cursor = conexao.cursor()

        # Primeiro, pegar o nome atual do grupo antes da atualização
        cursor.execute("SELECT NomeGrupo FROM grupoempresa WHERE id = %s", (grupo_id,))
        nome_atual = cursor.fetchone()[0]

        # Verificar se o novo nome já existe em outro grupo
        cursor.execute("SELECT COUNT(*) FROM grupoempresa WHERE NomeGrupo = %s AND id != %s", (novo_nome, grupo_id))
        count_grupo = cursor.fetchone()[0]

        if count_grupo > 0:
            st.error("Nome do grupo já está sendo utilizado por outro grupo.")
            return False

        # Atualizar o grupo
        cursor.execute(
            "UPDATE grupoempresa SET NomeGrupo = %s, codigo = %s WHERE id = %s",
            (novo_nome, novo_codigo, grupo_id)
        )

        # Atualizar todos os usuários que tinham esse grupo
        cursor.execute(
            "UPDATE usuarios SET NomeGrupo = %s, codigo = %s WHERE NomeGrupo = %s",
            (novo_nome, novo_codigo, nome_atual)
        )

        conexao.commit()
        conexao.close()
        st.success("Grupo e usuários associados atualizados com sucesso!")
        return True
    return False

def excluirgrupo(grupo_id):
    conexao = conectarbanco()
    if conexao:
        cursor = conexao.cursor()
        
        # Primeiro, pegar o nome do grupo
        cursor.execute("SELECT NomeGrupo FROM grupoempresa WHERE id = %s", (grupo_id,))
        resultado = cursor.fetchone()
        
        if not resultado:
            st.error("Grupo não encontrado.")
            return False
            
        nome_grupo = resultado[0]
        
        # Remover referências dos usuários
        cursor.execute(
            "UPDATE usuarios SET NomeGrupo = NULL, codigo = NULL WHERE NomeGrupo = %s",
            (nome_grupo,)
        )
        
        # Agora pode excluir o grupo
        cursor.execute("DELETE FROM grupoempresa WHERE id = %s", (grupo_id,))
        
        conexao.commit()
        conexao.close()
        st.success("Grupo excluído e referências removidas dos usuários com sucesso!")
        return True
    return False

def formularionovousuario():
    col1, col2 = st.columns([9, 1])
    with col2:
        if st.button("❌ Fechar", key="fecharformulario"):
            st.session_state.novousuario = False
            st.rerun()

    st.subheader("Adicionar Novo Usuário")

    grupos = puxargrupos()
    
    with st.form(key="formnovousuario"):
        nome = st.text_input("Nome", max_chars=50)
        usuario = st.text_input("Usuário", max_chars=20)
        senha = st.text_input("Senha", type="password", max_chars=30)
        numero = st.text_input("Número", max_chars=15)
        permissao = st.radio("Permissão", ["adm", "cliente"], horizontal=True)
        
        if grupos:
            opcoes_grupo = ["Sem Grupo"] + [grupo[1] for grupo in grupos]
            nome_grupo = st.radio("Grupo da Empresa", opcoes_grupo)
            
            codigo_grupo = None
            if nome_grupo != "Sem Grupo":
                for grupo in grupos:
                    if grupo[1] == nome_grupo:
                        codigo_grupo = grupo[2]
                        break
            
            nome_grupo = None if nome_grupo == "Sem Grupo" else nome_grupo
        else:
            st.warning("Nenhum grupo cadastrado no sistema")
            nome_grupo = None
            codigo_grupo = None

        submit_button = st.form_submit_button(label="Adicionar Usuário", use_container_width=True)

        if submit_button:
            if not all([nome, usuario, senha, numero]):
                st.error("Todos os campos são obrigatórios!")
            elif novousuario(nome, usuario, senha, numero, permissao, nome_grupo, codigo_grupo):
                st.session_state.mensagem = "Novo usuário cadastrado com sucesso!"
                st.session_state.novousuario = False
                st.rerun()

def formularioeditarusuario(user):
    col1, col2 = st.columns([9, 1])
    with col2:
        if st.button("❌ Fechar", key=f"fecharformularioeditar{user[0]}"):
            st.session_state.editar_usuario = None
            st.rerun()

    st.subheader(f"Editar Usuário: {user[1]}")

    grupos = puxargrupos()
    grupo_atual = user[6] if len(user) > 6 and user[6] else None
    codigo_atual = user[7] if len(user) > 7 and user[7] else None

    with st.form(key=f"editarusuario{user[0]}"):
        nome = st.text_input("Nome", value=user[1], max_chars=50)
        usuario = st.text_input("Usuário", value=user[2], max_chars=20)
        senha = st.text_input("Senha", value=user[3], type="password", max_chars=30)
        numero = st.text_input("Número", value=user[4], max_chars=15)
        permissao = st.radio("Permissão", ["adm", "cliente"], 
                           index=0 if user[5] == "adm" else 1,
                           horizontal=True)
        
        if grupos:
            opcoes_grupo = ["Sem Grupo"] + [grupo[1] for grupo in grupos]
            
            if grupo_atual:
                index_grupo = opcoes_grupo.index(grupo_atual) if grupo_atual in opcoes_grupo else 0
            else:
                index_grupo = 0
            
            nome_grupo = st.radio("Grupo da Empresa", opcoes_grupo, 
                                index=index_grupo)
            
            codigo_grupo = None
            if nome_grupo != "Sem Grupo":
                for grupo in grupos:
                    if grupo[1] == nome_grupo:
                        codigo_grupo = grupo[2]
                        break
            
            nome_grupo = None if nome_grupo == "Sem Grupo" else nome_grupo
        else:
            st.warning("Nenhum grupo cadastrado no sistema")
            nome_grupo = None
            codigo_grupo = None

        submit_button = st.form_submit_button(label="Atualizar Usuário", use_container_width=True)

        if submit_button:
            if not all([nome, usuario, senha, numero]):
                st.error("Todos os campos são obrigatórios!")
            elif atualizacaousuarios(user[0], nome, usuario, senha, numero, permissao, nome_grupo, codigo_grupo):
                st.session_state.mensagem = "Usuário atualizado com sucesso!"
                st.session_state.editar_usuario = None
                st.rerun()

def formularionovogrupo():
    col1, col2 = st.columns([9, 1])
    with col2:
        if st.button("❌ Fechar", key="fecharformulariogrupo"):
            st.session_state.novogrupo = False
            st.rerun()

    st.subheader("Adicionar Novo Grupo")
    
    with st.form(key="formnovogrupo"):
        nome_grupo = st.text_input("Nome do Grupo", max_chars=50)
        codigo = st.text_input("Código", max_chars=20)

        submit_button = st.form_submit_button(label="Adicionar Grupo", use_container_width=True)

        if submit_button:
            if not nome_grupo:
                st.error("O nome do grupo é obrigatório!")
            elif novogrupo(nome_grupo, codigo):
                st.session_state.mensagem = "Novo grupo cadastrado com sucesso!"
                st.session_state.novogrupo = False
                st.rerun()

def formularioeditargrupo(grupo):
    col1, col2 = st.columns([9, 1])
    with col2:
        if st.button("❌ Fechar", key=f"fecharformularioeditargrupo{grupo[0]}"):
            st.session_state.editar_grupo = None
            st.rerun()

    st.subheader(f"Editar Grupo: {grupo[1]}")
    
    with st.form(key=f"editargrupo{grupo[0]}"):
        novo_nome = st.text_input("Nome do Grupo", value=grupo[1], max_chars=50)
        novo_codigo = st.text_input("Código", value=grupo[2] if len(grupo) > 2 else "", max_chars=20)

        submit_button = st.form_submit_button(label="Atualizar Grupo", use_container_width=True)

        if submit_button:
            if not novo_nome:
                st.error("O nome do grupo é obrigatório!")
            elif atualizargrupo(grupo[0], novo_nome, novo_codigo):
                st.session_state.mensagem = "Grupo atualizado com sucesso!"
                st.session_state.editar_grupo = None
                st.rerun()

def listarusuarios():
    usuarios = puxarusuarios()
    
    if not usuarios:
        st.info("Nenhum usuário cadastrado ainda.")
        return
    
    st.subheader("📋 Lista de Usuários")
    
    for user in usuarios:
        with st.container():
            st.markdown(f"### {user[1]}")
            
            col1, col2 = st.columns(2)
            col1.markdown(f"**ID:** `{user[0]}`")
            col2.markdown(f"**Usuário:** `{user[2]}`")
            
            col1, col2 = st.columns(2)
            col1.markdown(f"**Número:** `{user[4]}`")
            col2.markdown(f"**Permissão:** `{user[5]}`")
            
            col1, col2 = st.columns(2)
            col1.markdown(f"**Grupo:** `{user[6] if len(user) > 6 and user[6] else 'NULL'}`")
            col2.markdown(f"**Código Grupo:** `{user[7] if len(user) > 7 and user[7] else 'NULL'}`")
            
            btn_col1, btn_col2 = st.columns(2)
            
            if btn_col1.button("✏️ Editar", key=f"edit_{user[0]}", use_container_width=True):
                st.session_state.editar_usuario = user[0]
                st.rerun()
            
            if btn_col2.button("🗑️ Excluir", key=f"delete_{user[0]}", use_container_width=True):
                st.session_state.confirmarexclusao = user[0]
                st.session_state.usuario_a_excluir = user[1]
                st.rerun()
            
            if st.session_state.get('editar_usuario') == user[0]:
                formularioeditarusuario(user) 
            
            if ("confirmarexclusao" in st.session_state and 
                st.session_state.confirmarexclusao == user[0]):
                st.warning(f"Confirmar exclusão de {st.session_state.usuario_a_excluir}?")
                
                confirm_col1, confirm_col2 = st.columns(2)
                if confirm_col1.button("✅ Confirmar", key=f"sim_{user[0]}", use_container_width=True):
                    excluirusuario(user[0])
                    del st.session_state.confirmarexclusao
                    st.rerun()
                
                if confirm_col2.button("❌ Cancelar", key=f"nao_{user[0]}", use_container_width=True):
                    del st.session_state.confirmarexclusao
                    st.rerun()
            
            st.divider()

def listargrupos():
    grupos = puxargrupos()
    
    if not grupos:
        st.info("Nenhum grupo cadastrado ainda.")
        return
    
    st.subheader("🏢 Lista de Grupos de Empresas")
    
    for grupo in grupos:
        with st.container():
            st.markdown(f"### {grupo[1]}")
            
            col1, col2 = st.columns(2)
            col1.markdown(f"**ID:** `{grupo[0]}`")
            col2.markdown(f"**Nome do Grupo:** `{grupo[1]}`")
            
            col1, col2 = st.columns(2)
            col1.markdown(f"**Código:** `{grupo[2] if len(grupo) > 2 and grupo[2] else 'N/A'}`")
            
            btn_col1, btn_col2 = st.columns(2)
            
            if btn_col1.button("✏️ Editar", key=f"edit_grupo_{grupo[0]}", use_container_width=True):
                st.session_state.editar_grupo = grupo[0]
                st.rerun()
            
            if btn_col2.button("🗑️ Excluir", key=f"delete_grupo_{grupo[0]}", use_container_width=True):
                st.session_state.confirmarexclusaogrupo = grupo[0]
                st.session_state.grupo_a_excluir = grupo[1]
                st.rerun()
            
            if st.session_state.get('editar_grupo') == grupo[0]:
                formularioeditargrupo(grupo) 
            
            if ("confirmarexclusaogrupo" in st.session_state and 
                st.session_state.confirmarexclusaogrupo == grupo[0]):
                st.warning(f"Confirmar exclusão do grupo {st.session_state.grupo_a_excluir}?")
                
                confirm_col1, confirm_col2 = st.columns(2)
                if confirm_col1.button("✅ Confirmar", key=f"sim_grupo_{grupo[0]}", use_container_width=True):
                    if excluirgrupo(grupo[0]):
                        del st.session_state.confirmarexclusaogrupo
                        st.rerun()
                
                if confirm_col2.button("❌ Cancelar", key=f"nao_grupo_{grupo[0]}", use_container_width=True):
                    del st.session_state.confirmarexclusaogrupo
                    st.rerun()
            
            st.divider()

def pagina_usuarios():
    st.title("👨🏽‍💼 Gerenciamento de Usuários")
    
    with st.container():
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("➕ Adicionar Novo Usuário", use_container_width=True, 
                        help="Cadastrar novo usuário no sistema"):
                st.session_state.novousuario = True
                st.rerun()
        with col2:
            if st.button("🏢 Gerenciar Grupos", use_container_width=True, 
                        help="Gerenciar grupos de empresas"):
                st.session_state.pagina_atual = 'grupos'
                st.rerun()
        with col3:
            if st.button("📊 Ir para Dashboard", use_container_width=True, 
                        help="Voltar ao painel principal"):
                st.session_state.show_dashboard_options = True
                st.rerun()
    
    if "mensagem" in st.session_state:
        st.success(st.session_state.mensagem)
        del st.session_state.mensagem
    
    if st.session_state.get("novousuario", False):
        formularionovousuario()
    
    # Mostrar opções de dashboard se o botão foi clicado
    if st.session_state.get("show_dashboard_options", False):
        st.subheader("Selecione o Dashboard")
        
        grupos = puxargrupos()
        if not grupos:
            st.warning("Nenhum grupo cadastrado para selecionar dashboard")
        else:
            grupo_selecionado = st.selectbox(
                "Escolha o grupo para acessar o dashboard:",
                options=[grupo[1] for grupo in grupos],
                index=0
            )
            
            # Encontrar o código do grupo selecionado
            codigo_dashboard = None
            for grupo in grupos:
                if grupo[1] == grupo_selecionado:
                    codigo_dashboard = grupo[2]
                    break
            
            col1, col2 = st.columns(2)
            if col1.button("Acessar Dashboard", use_container_width=True):
                if codigo_dashboard:
                    # Remove a extensão .py se existir e converte para lowercase
                    nome_pagina = codigo_dashboard.replace('.py', '').lower().strip()
                    st.session_state.page = nome_pagina
                    st.session_state.show_dashboard_options = False
                    st.rerun()
                else:
                    st.error("Este grupo não tem um código de dashboard associado")
            
            if col2.button("Cancelar", use_container_width=True):
                st.session_state.show_dashboard_options = False
                st.rerun()
    
    listarusuarios()

def pagina_grupos():
    st.title("🏢 Gerenciamento de Grupos de Empresas")
    
    with st.container():
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("➕ Adicionar Novo Grupo", use_container_width=True, 
                        help="Cadastrar novo grupo no sistema"):
                st.session_state.novogrupo = True
                st.rerun()
        with col2:
            if st.button("👥 Voltar para Usuários", use_container_width=True, 
                        help="Voltar ao gerenciamento de usuários"):
                st.session_state.pagina_atual = None
                st.rerun()
    
    if "mensagem" in st.session_state:
        st.success(st.session_state.mensagem)
        del st.session_state.mensagem
    
    if st.session_state.get("novogrupo", False):
        formularionovogrupo()
    
    listargrupos()

def paginaadm():
    verificar_permissao()
    
    st.set_page_config(layout="wide", page_title="Admin - Gerenciamento de Usuários", page_icon="👨‍💼")
    
    with st.sidebar:
        st.subheader("👤 Painel Administrativo")
        
        if 'user_info' in st.session_state:
            st.markdown(f"""
            **Nome:** {st.session_state.user_info['nome']}  
            **Permissão:** `{st.session_state.user_info['permissao']}`
            """)
        
        st.divider()
        
        if st.button("🚪 Sair", use_container_width=True, type="primary", help="Encerrar sessão"):
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.session_state.page = None
            st.rerun()
    
    if st.session_state.get('pagina_atual') == 'grupos':
        pagina_grupos()
    else:
        pagina_usuarios()

if __name__ == "__main__":
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = {'nome': 'Admin Teste', 'permissao': 'adm'}
    if 'page' not in st.session_state:
        st.session_state.page = None
    if 'pagina_atual' not in st.session_state:
        st.session_state.pagina_atual = None
    if 'show_dashboard_options' not in st.session_state:
        st.session_state.show_dashboard_options = False
    
    st.session_state.authenticated = True
    paginaadm()
