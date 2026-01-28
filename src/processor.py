import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings 
from langchain_chroma import Chroma
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def process_documents():
    # Set paths for data and vector database
    data_path = "./data"
    persist_directory = "./vector_db"
    
    # Load PDF files
    documents = []
    print("reading PDF files...")
    
    # Check if data folder exists
    if not os.path.exists(data_path):
        print(f"erorr:folder {data_path} not founded.")
        return

    # Process each PDF file in the data folder
    for file in os.listdir(data_path):
        if file.endswith(".pdf"):
            print(f"processing {file}")
            loader = PyPDFLoader(os.path.join(data_path, file))
            documents.extend(loader.load())
    
    # Check if any documents were loaded
    if not documents:
        print("no file found to process.")
        return

    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    print(f"text to {len(chunks)} divided.")

    # Create embeddings using HuggingFace model
    print("creating vector database (may take a few minutes) ")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Create vector database from documents
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    
    # Save vector database to disk
    print(f"datbase successfuly on {persist_directory} saved.")

# Execute main function
if __name__ == "__main__":
    process_documents()