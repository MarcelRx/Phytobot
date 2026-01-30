# Import required libraries
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings 
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

# Load environment variables (if needed for embeddings)
load_dotenv()


# Function: process_documents
# - Loads PDF files from the 'data' folder
# - Splits text into smaller chunks
# - Converts text into embeddings
# - Saves embeddings into a Chroma vector database
def process_documents():
    data_path = "./data"
    persist_directory = "./vector_db"

    # Load PDF files
    documents = []
    print("Reading PDF files...")
    if not os.path.exists(data_path):
        print(f"Error: Folder {data_path} not found.")
        return

    for file in os.listdir(data_path):
        if file.endswith(".pdf"):
            print(f"Processing: {file}")
            loader = PyPDFLoader(os.path.join(data_path, file))
            documents.extend(loader.load())

    if not documents:
        print("No files found to process.")
        return

    # Split text into chunks
    # AI models cannot process very long documents at once,
    # so we split them into 1000-character chunks with 200-character overlap
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Text split into {len(chunks)} chunks.")

    # Convert text into embeddings and store in vector database
    # This allows retrieval of similar content later
    print("Creating vector database (this may take a few minutes)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )

    print(f"✨ Database successfully saved to {persist_directory}.")


# Run the function if script is executed directly
if __name__ == "__main__":
    process_documents()
