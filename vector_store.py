import sys
import pysqlite3
sys.modules["sqlite3"] = pysqlite3  # 🔧 Force Chroma to use modern SQLite

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings

def get_vector_store(persist_directory="data/chroma_db"):
    embedding = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    vectordb = Chroma(persist_directory=persist_directory, embedding_function=embedding)
    return vectordb

