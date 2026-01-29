import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()


def is_database_hit(docs, min_chars=300):
    if not docs:
        return False
    total_chars = sum(len(doc.page_content) for doc in docs)
    return total_chars >= min_chars


def get_phytobot_response(user_query):
    """
    Uses existing ChromaDB located at ./vector_db
    """

    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    # ✅ LOAD existing database (no creation, no overwrite)
    vector_db = Chroma(
        persist_directory="./vector_db",
        embedding_function=embeddings
    )

    retriever = vector_db.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(user_query)

    use_database = is_database_hit(docs)

    if use_database:
        context = "\n\n".join(doc.page_content for doc in docs)
        source_type = "Verified Internal Database (vector_db)"
    else:
        context = ""
        source_type = "Internet Sources"

    llm = ChatGroq(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.1-8b-instant",
        temperature=0.2,
        streaming=True
    )

    prompt_template = """
You are Phytobot, a medicinal plant expert.

RULES:
- If context is provided, ONLY use the context.
- If context is empty, use general herbal knowledge AND cite reputable online sources
  (WHO website, PubMed, NHS, scientific reviews).
- Never diagnose disease.
- Always include precautions and contraindications.
- Dosage must be general ranges only.
- Always end with:
  "This information is not a substitute for professional medical advice."

Context:
{context}

Question:
{question}
"""

    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = prompt | llm

    def stream_response():
        for chunk in chain.stream(
            {"context": context, "question": user_query}
        ):
            yield getattr(chunk, "content", str(chunk))

    return stream_response(), (docs if use_database else []), source_type
