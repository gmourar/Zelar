import os
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# carregar as variáveis de ambiente
load_dotenv()

class DatabaseConnection:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.engine = None
        self.SessionLocal = None

    def connect(self):
        try:
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_recycle=300
            )
            self.SessionLocal = sessionmaker(bind=self.engine)
            return True
        except Exception as e:
            st.error(f"Erro ao conectar com o banco: {e}")
            return False

    def get_session(self):
        """retorna uma sessão direto do banco"""
        if not self.SessionLocal:
            self.connect()
        return self.SessionLocal()

    def execute_query(self, query, params=None):
        try:
            session = self.get_session()
            if params:
                result = session.execute(text(query), params)
            else:
                result = session.execute(text(query))
            session.commit()
            session.close()
            return result
        except Exception as e:
            st.error(f"Erro ao executar query: {e}")
            return None

    def fetch_all(self, query, params=None):
        """Busca todos os resultados de uma query"""
        try:
            session = self.get_session()
            if params:
                result = session.execute(text(query), params)
            else:
                result = session.execute(text(query))
            data = result.fetchall()
            session.close()
            return data
        except Exception as e:
            st.error(f"Erro ao buscar dados: {e}")
            return []

    def fetch_one(self, query, params=None):
        """Busca um resultado de uma query"""
        try:
            session = self.get_session()
            if params:
                result = session.execute(text(query), params)
            else:
                result = session.execute(text(query))
            data = result.fetchone()
            session.close()
            return data
        except Exception as e:
            st.error(f"Erro ao buscar dado: {e}")
            return None

# Instância global da conexão
db = DatabaseConnection()