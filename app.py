from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import chainlit as cl
import chainlit.data as cl_data
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit.data.storage_clients.base import BaseStorageClient
from chainlit.types import ThreadDict
import chromadb
import psycopg2
import bcrypt
import os
from typing import Optional
from register import register_user

username = os.environ.get( "CHAINLIT_USER" )
password = os.environ.get( "CHAINLIT_PASSWORD" )
dbhost = os.environ.get( "DB_HOST" )
dbuser = os.environ.get( "DB_USER" )
dbpassword = os.environ.get( "DB_PASSWORD" )
dbname = os.environ.get( "DB_NAME" )

conn_str = f"{dbuser}:{dbpassword}@{dbhost}:5432/{dbname}" 
cl_data._data_layer = SQLAlchemyDataLayer(f"postgresql+asyncpg://{conn_str}", storage_provider=BaseStorageClient)

def login_user (username, password):
    conn = psycopg2.connect(
        f"host={dbhost} dbname={dbname} user={dbuser} password={dbpassword}"
    )
    with conn:
         with conn.cursor() as cur:

            cur.execute(
                """ 
                SELECT logins."passwordHash"
                FROM logins 
                INNER JOIN users 
                ON logins.id=users.id
                WHERE users.identifier=%s 
                """ ,(username,)
            )
            pw = cur.fetchone()
        
    if  not pw:
         return  False 
    if pw and bcrypt.checkpw(password.encode( "utf-8" ),pw[ 0 ].encode( "utf-8" )):
         return  True 
    else :
         return  False

chroma_client = None
llm_model = "mistral"
chain = None

def initialize_chromadb():
    global chroma_client, chain

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

    retriever = vectorstore.as_retriever()

    contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
    )

    contextualize_q_prompt = ChatPromptTemplate(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
    )
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    # Create the prompt template
    system_prompt = """Use the given context to answer the question. 
    If you don't know the answer, say you don't know. 
    
    Context: {context}
    Use three sentences maximum and keep the answer concise."""
    

    question_answer_chain = create_stuff_documents_chain(
        llm=llm,
        prompt=ChatPromptTemplate(
            [
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
    )

    chain = create_retrieval_chain(
        history_aware_retriever,
        question_answer_chain
    )

@cl.password_auth_callback
async def auth_callback(username: str, password: str) -> Optional[cl.User]:

    if login_user(username, password):
        return  await cl_data.get_data_layer().get_user(username)
    else:
        return None

@cl.on_chat_start
async def start():
    try:

        initialize_chromadb()

        user = cl.user_session.get("user")
        if not user:
            await cl.Message(
                content="Please log in to continue."
            ).send()
            return

        cl.user_session.set( "chat_history" ,[])

        await cl.Message(
            content=f"Hello {user.identifier}! I'm your RAG-powered chatbot. Ask me anything about the documents in my knowledge base."
        ).send()
            
    except Exception as e:
        await cl.Message(
            content=f"Error initializing chatbot: {str(e)}"
        ).send()

@cl.on_message
async def main(message: cl.Message):
    try:
        user = cl.user_session.get("user")
        if not user:
            image=cl.Image(path="./cat.jpg", name="cat image", display="inline")
            await cl.Message(content="Please log in to continue.",
                             elements=[image],
                             ).send()
            return

        chat_history = cl.user_session.get( "chat_history" )
        chat_history.append({ "role" : "user" , "content" : message.content})

    
        response = await cl.make_async(chain.invoke)(
            {
                "chat_history": chat_history,
                "input": message.content
            }
        )

        chat_history.append({ "role" : "assistant" , "content" : response['answer']})

        msg=cl.Message(content="")
        for token in tuple(response['answer']): 
            await msg.stream_token(token)
        await msg.send()

    except Exception as e:
        await cl.Message(
            content=f"Error processing your message: {str(e)}"
        ).send()

@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    try:

        if not chain:
            initialize_chromadb()
        
        user = cl.user_session.get("user")
        if not user:
            await cl.Message(
                content="Please log in to continue."
            ).send()
            return
        
        cl.user_session.set( "chat_history" , [])
        chat_history = thread[ "metadata" ][ "chat_history" ]
        for message in chat_history:
            cl.user_session.get( "chat_history" ).append(message)
        
    except Exception as e:
        await cl.Message(
            content=f"Error resuming chat session: {str(e)}"
        ).send()

