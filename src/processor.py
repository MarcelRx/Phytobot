import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings 
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

def process_documents():
    data_path = "./data"
    persist_directory = "./vector_db"
    
    # load PDF files
    documents = []
    print("reading PDF files...")
    if not os.path.exists(data_path):
        print(f"erorr:folder {data_path} not founded.")
        return

    for file in os.listdir(data_path):
        if file.endswith(".pdf"):
            print(f"processing {file}")
            loader = PyPDFLoader(os.path.join(data_path, file))
            documents.extend(loader.load())
    
    if not documents:
        print("no file found to process.")
        return

    # text segmentation
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    print(f"text to {len(chunks)} divided.")

    # convert to vector and store in database (free)
    print("creating vector database (may take a few minutes) ")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    
    print(f"datbase successfuly on {persist_directory} saved.")

if __name__ == "__main__":
    process_documents()