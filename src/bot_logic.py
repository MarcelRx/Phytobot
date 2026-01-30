import os
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

def get_phytobot_response(user_query):
    # Tools Setup
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_db = Chroma(persist_directory="./vector_db", embedding_function=embeddings)
    retriever = vector_db.as_retriever(search_kwargs={"k": 3})
    llm = ChatGroq(model_name="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY"), temperature=0.1)
    
    # Dual Search (Internal + Web)
    internal_docs = retriever.invoke(user_query)
    db_context = "\n".join([d.page_content for d in internal_docs])
    
    web_context = ""
    try:
        search = TavilySearchResults(max_results=2)
        web_results = search.invoke(user_query)
        web_context = str(web_results)
    except:
        web_context = "Web search currently unavailable."

    # Multi-Mode Prompt
    prompt = ChatPromptTemplate.from_template("""
    You are Phytobot, a scientific herbalism assistant. 
    User Question: {question}

    Follow these rules:
    - If symptoms are mentioned: Recommend herbs but emphasize safety.
    - If tea/medicine is requested: Provide a clear "Preparation" section.
    - If education is requested: Focus on active compounds and scientific names.

    Structure your answer in these EXACT blocks:
    
    ### Verified WHO/Encyclopedia Data (Trust: 100%)
    (Use INTERNAL PDF DATA. If not found, say 'No specific match in our medical library.')

    ### Internet Research & Traditional Use (Trust: 50%)
    (Summarize INTERNET DATA. Provide recipe steps or traditional uses found online.)

    ### Safety & Disclaimer
    (List side effects or drug interactions. End with: 'Not a substitute for medical advice.')

    INTERNAL DATA: {internal_context}
    INTERNET DATA: {web_context}
    """)

    chain = prompt | llm
    response = chain.invoke({"question": user_query, "internal_context": db_context, "web_context": web_context})
    return response.content, internal_docs