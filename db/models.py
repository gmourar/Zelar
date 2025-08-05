from db.connection import db
import streamlit as st

def criar_tabelas():

    # Tabela de usuários
    query_usuarios = """
                     CREATE TABLE IF NOT EXISTS usuarios (
                                                             id SERIAL PRIMARY KEY,
                                                             nome VARCHAR(100) NOT NULL,
                         email VARCHAR(100) UNIQUE NOT NULL,
                         senha_hash VARCHAR(255) NOT NULL,
                         tipo_usuario VARCHAR(20) NOT NULL CHECK (tipo_usuario IN ('administrador', 'enfermeiro', 'usuario_comum')),
                         ativo BOOLEAN DEFAULT TRUE,
                         criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                         atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                         ); \
                     """

    # Tabela de responsáveis
    query_responsaveis = """
                         CREATE TABLE IF NOT EXISTS responsaveis (
                                                                     id SERIAL PRIMARY KEY,
                                                                     nome VARCHAR(100) NOT NULL,
                             telefone VARCHAR(20),
                             email VARCHAR(100),
                             parentesco VARCHAR(50),
                             endereco TEXT,
                             criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                             ); \
                         """

    # Tabela de idosos
    query_idosos = """
                   CREATE TABLE IF NOT EXISTS idosos (
                                                         id SERIAL PRIMARY KEY,
                                                         nome_completo VARCHAR(150) NOT NULL,
                       idade INTEGER NOT NULL,
                       documento VARCHAR(20) UNIQUE NOT NULL,
                       foto_path VARCHAR(255),
                       responsavel_id INTEGER REFERENCES responsaveis(id),
                       observacoes TEXT,
                       ativo BOOLEAN DEFAULT TRUE,
                       criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                       ); \
                   """

    # Tabela de itens pessoais
    query_itens = """
                  CREATE TABLE IF NOT EXISTS itens_pessoais (
                                                                id SERIAL PRIMARY KEY,
                                                                idoso_id INTEGER REFERENCES idosos(id) ON DELETE CASCADE,
                      nome_item VARCHAR(100) NOT NULL,
                      descricao TEXT,
                      categoria VARCHAR(50),
                      quantidade INTEGER DEFAULT 1,
                      estado_conservacao VARCHAR(20) DEFAULT 'bom',
                      criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                      ); \
                  """

    # Executa as queries
    try:
        db.execute_query(query_usuarios)
        db.execute_query(query_responsaveis)
        db.execute_query(query_idosos)
        db.execute_query(query_itens)

        # Cria usuário administrador padrão se não existir
        criar_admin_padrao()

        return True
    except Exception as e:
        st.error(f"Erro ao criar tabelas: {e}")
        return False

def criar_admin_padrao():
    import bcrypt

    # Verifica se já existe um admin
    admin_exists = db.fetch_one("SELECT id FROM usuarios WHERE tipo_usuario = 'administrador'")

    if not admin_exists:
        # Cria senha hash
        senha = "admin123"
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        query = """
                INSERT INTO usuarios (nome, email, senha_hash, tipo_usuario)
                VALUES (:nome, :email, :senha_hash, :tipo_usuario) \
                """

        params = {
            'nome': 'Administrador',
            'email': 'admin@zelar.com',
            'senha_hash': senha_hash,
            'tipo_usuario': 'administrador'
        }

        db.execute_query(query, params)
        st.success("Usuário administrador criado: admin@zelar.com / admin123")

class UsuarioModel:
    @staticmethod
    def criar_usuario(nome, email, senha, tipo_usuario):
        import bcrypt

        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        query = """
                INSERT INTO usuarios (nome, email, senha_hash, tipo_usuario)
                VALUES (:nome, :email, :senha_hash, :tipo_usuario) \
                """

        params = {
            'nome': nome,
            'email': email,
            'senha_hash': senha_hash,
            'tipo_usuario': tipo_usuario
        }

        return db.execute_query(query, params)

    @staticmethod
    def buscar_por_email(email):
        """buscar usuário por email"""
        query = "SELECT * FROM usuarios WHERE email = :email AND ativo = TRUE"
        return db.fetch_one(query, {'email': email})

    @staticmethod
    def listar_usuarios():
        """Lista todos os usuários"""
        query = "SELECT id, nome, email, tipo_usuario, ativo, criado_em FROM usuarios ORDER BY criado_em DESC"
        return db.fetch_all(query)

class IdosoModel:
    @staticmethod
    def criar_idoso(nome_completo, idade, documento, foto_path, responsavel_id, observacoes=""):
        """Cria um novo idoso"""
        query = """
                INSERT INTO idosos (nome_completo, idade, documento, foto_path, responsavel_id, observacoes)
                VALUES (:nome_completo, :idade, :documento, :foto_path, :responsavel_id, :observacoes) \
                """

        params = {
            'nome_completo': nome_completo,
            'idade': idade,
            'documento': documento,
            'foto_path': foto_path,
            'responsavel_id': responsavel_id,
            'observacoes': observacoes
        }

        return db.execute_query(query, params)

    @staticmethod
    def listar_idosos():
        """Lista todos os idosos com dados do responsável"""
        query = """
                SELECT
                    i.id, i.nome_completo, i.idade, i.documento, i.foto_path, i.observacoes,
                    r.nome as responsavel_nome, r.telefone as responsavel_telefone
                FROM idosos i
                         LEFT JOIN responsaveis r ON i.responsavel_id = r.id
                WHERE i.ativo = TRUE
                ORDER BY i.nome_completo \
                """
        return db.fetch_all(query)

    @staticmethod
    def buscar_por_id(idoso_id):
        """Busca idoso por ID"""
        query = """
                SELECT
                    i.*, r.nome as responsavel_nome, r.telefone, r.email as responsavel_email
                FROM idosos i
                         LEFT JOIN responsaveis r ON i.responsavel_id = r.id
                WHERE i.id = :id AND i.ativo = TRUE \
                """
        return db.fetch_one(query, {'id': idoso_id})

class ResponsavelModel:
    @staticmethod
    def criar_responsavel(nome, telefone="", email="", parentesco="", endereco=""):
        """Cria um novo responsável"""
        query = """
                INSERT INTO responsaveis (nome, telefone, email, parentesco, endereco)
                VALUES (:nome, :telefone, :email, :parentesco, :endereco)
                    RETURNING id \
                """

        params = {
            'nome': nome,
            'telefone': telefone,
            'email': email,
            'parentesco': parentesco,
            'endereco': endereco
        }

        result = db.execute_query(query, params)
        return result.fetchone()[0] if result else None

    @staticmethod
    def listar_responsaveis():
        """Lista todos os responsáveis"""
        query = "SELECT * FROM responsaveis ORDER BY nome"
        return db.fetch_all(query)

class ItemModel:
    @staticmethod
    def criar_item(idoso_id, nome_item, descricao="", categoria="", quantidade=1, estado_conservacao="bom"):
        """Cria um novo item pessoal"""
        query = """
                INSERT INTO itens_pessoais
                (idoso_id, nome_item, descricao, categoria, quantidade, estado_conservacao)
                VALUES (:idoso_id, :nome_item, :descricao, :categoria, :quantidade, :estado_conservacao) \
                """

        params = {
            'idoso_id': idoso_id,
            'nome_item': nome_item,
            'descricao': descricao,
            'categoria': categoria,
            'quantidade': quantidade,
            'estado_conservacao': estado_conservacao
        }

        return db.execute_query(query, params)

    @staticmethod
    def listar_itens_por_idoso(idoso_id):
        """Lista itens de um idoso específico"""
        query = """
                SELECT * FROM itens_pessoais
                WHERE idoso_id = :idoso_id
                ORDER BY categoria, nome_item \
                """
        return db.fetch_all(query, {'idoso_id': idoso_id})