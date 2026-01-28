import os
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_phytobot_response(user_query):
    # Set up free Embedding model
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Load vector database
    vector_db = Chroma(persist_directory="./vector_db", embedding_function=embeddings)
    retriever = vector_db.as_retriever(search_kwargs={"k": 3})

    # Configure Groq model
    llm = ChatGroq(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.1-8b-instant",
        temperature=0.1
    )

    # Design response template with Phytobot rules
    template = """You are Phytobot, a medicinal plant expert. 
    Use the following pieces of retrieved context from verified sources to answer the user's question. 
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    
    Always include a medical disclaimer.
    State if information is from internal database.

    Context: {context}
    Question: {question}
    Answer:"""
    
    prompt = ChatPromptTemplate.from_template(template)

    # Build RAG chain
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    # Execute query and get response
    response = rag_chain.invoke(user_query)
    
    # Get source documents for display
    sources = retriever.invoke(user_query)
    
    return response, sources