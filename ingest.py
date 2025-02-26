import chromadb
from langchain_chroma import Chroma
import os
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

llm_model = "mistral"
llm = ChatOllama(model=llm_model, temperature=1.0)

embedding = OllamaEmbeddings(
    model=llm_model,
    base_url="http://localhost:11434"
)

chroma_client = chromadb.PersistentClient(path=os.path.join(os.getcwd(), "chroma_db"))

collection_name="chaingpt"

vectorstore = Chroma(
    client=chroma_client,
    collection_name=collection_name,
    embedding_function=embedding
)

text_splitter = RecursiveCharacterTextSplitter()

folder_path="src"

if __name__ == "__main__":

    if collection_name in chroma_client.list_collections():
        print("Collection already exists. Skipping PDF loading.")
    else:
        print("Loading and chunking the PDF(s)...")

        documents=[]
        for filename in os.listdir(folder_path):
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(folder_path, filename)
                loader = PyPDFLoader(pdf_path)
                docs = loader.load()
                chunks = text_splitter.split_documents(docs)
                documents.extend(chunks)
        
        vectorstore.add_documents(documents)   
