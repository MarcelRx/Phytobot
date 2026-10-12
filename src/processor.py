# Import required libraries
import logging
import os

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import NegativeKnowledgeConfig, TextConfig, VectorDBConfig
from src.negative_knowledge import load_negative_knowledge

# Load environment variables (if needed for embeddings)
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


# Function: process_documents
# - Loads PDF files from the 'data' folder
# - Loads negative knowledge from JSON files
# - Splits text into smaller chunks
# - Converts text into embeddings
# - Saves embeddings into a Chroma vector database with metadata
def process_documents():
    data_path = "./data"
    persist_directory = VectorDBConfig.VECTOR_DB_PATH

    # Load PDF files (medicinal knowledge)
    documents = []
    logger.info("Reading PDF files...")

    if not os.path.exists(data_path):
        logger.error(f"Folder {data_path} not found.")
        return

    for file in os.listdir(data_path):
        if file.endswith(".pdf"):
            logger.info(f"Processing: {file}")
            try:
                loader = PyPDFLoader(os.path.join(data_path, file))
                pdf_docs = loader.load()
                # Add metadata to mark as medicinal knowledge
                for doc in pdf_docs:
                    doc.metadata[NegativeKnowledgeConfig.NEGATIVE_METADATA_KEY] = (
                        "medicinal"
                    )
                    doc.metadata["source_type"] = "authoritative_pdf"
                documents.extend(pdf_docs)
            except Exception as e:
                logger.error(f"Failed to load {file}: {e}")

    if not documents:
        logger.warning("No PDF files found to process.")
    else:
        logger.info(f"Loaded {len(documents)} pages from PDF files.")

    # Load negative knowledge (safety information)
    logger.info("Loading negative knowledge...")
    negative_docs = load_negative_knowledge()
    documents.extend(negative_docs)

    if not documents:
        logger.warning("No documents found to process.")
        return

    # Split text into chunks
    # AI models cannot process very long documents at once,
    # so we split them into chunks with overlap
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=TextConfig.CHUNK_SIZE, chunk_overlap=TextConfig.CHUNK_OVERLAP
    )
    chunks = text_splitter.split_documents(documents)
    logger.info(f"Text split into {len(chunks)} chunks.")

    # Convert text into embeddings and store in vector database
    # This allows retrieval of similar content later
    logger.info("Creating vector database (this may take a few minutes)...")
    try:
        embeddings = HuggingFaceEmbeddings(model_name=VectorDBConfig.EMBEDDING_MODEL)

        # Add documents in batches to avoid ChromaDB batch size limits
        batch_size = 5000
        vector_db = None
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            if vector_db is None:
                vector_db = Chroma.from_documents(
                    documents=batch,
                    embedding=embeddings,
                    persist_directory=persist_directory,
                )
            else:
                vector_db.add_documents(batch)
            logger.info(f"Processed batch {i // batch_size + 1}: {len(batch)} chunks")

        logger.info(f"Database successfully saved to {persist_directory}.")
        logger.info(f"Total chunks: {len(chunks)} (medicinal + safety knowledge)")
    except Exception as e:
        logger.error(f"Failed to create vector database: {e}")
        raise


# Run the function if script is executed directly
if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(level=logging.INFO)
    process_documents()
