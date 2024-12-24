import os
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from tqdm import tqdm
import gc
from itertools import islice

DATA_PATHS = {
    "transcriptions": "/Users/dtikhanovskii/Documents/phycho_rag/data/videos",
    "books": "/Users/dtikhanovskii/Documents/phycho_rag/data/books/books",
    "articles": "data/articles/"
}

DB_PATHS = {
    "transcriptions": "/Users/dtikhanovskii/Documents/phycho_rag/data/vectorstore/transcriptions_db_2",
    "books": "/Users/dtikhanovskii/Documents/phycho_rag/data/vectorstore/books_db_2",
    "articles": "/Users/dtikhanovskii/Documents/phycho_rag/data/vectorstore/articles_db"
}

embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", show_progress=True)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=2048, chunk_overlap=5, separators=["\n\n", "\n", ". ", " ", ""])

def chunked_iterable(iterable, size):
    """Split an iterable into chunks of the given size."""
    it = iter(iterable)
    while chunk := list(islice(it, size)):
        yield chunk

def batch_process(data, batch_size):
    """Helper function to split data into batches."""
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]

def create_embeddings_for_dataset(name, loader_cls):
    print(f"Processing {name} dataset...")
    documents = []
    errors = []

    # Load documents with error handling
    for file_chunk in chunked_iterable(os.listdir(DATA_PATHS[name]), 500):
        for file_path in file_chunk:
            if file_path.startswith("."):  # Skip hidden files
                continue
            file_full_path = os.path.join(DATA_PATHS[name], file_path)
            try:
                loader = loader_cls(file_full_path)
                docs = loader.load()
                documents.extend(docs)
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
                errors.append(file_path)

    print(f"Loaded {len(documents)} documents for {name}.")

    # Split documents into chunks
    print("Splitting documents into chunks...")
    split_docs = []
    for doc in tqdm(documents, desc="Splitting"):
        split_docs.extend(text_splitter.split_documents([doc]))

    # Debug: Check chunk sizes
    chunk_lengths = [len(doc.page_content) for doc in split_docs]
    print(f"Max chunk size: {max(chunk_lengths)}, Average chunk size: {sum(chunk_lengths) / len(chunk_lengths)}")

    print(f"Split into {len(split_docs)} chunks.")

    # Embed documents in smaller batches
    print("Creating and storing embeddings...")
    db = Chroma(persist_directory=DB_PATHS[name], embedding_function=embedding_model)
    batch_size = 41000  # Smaller batch size

    for i, batch in tqdm(enumerate(batch_process(split_docs, batch_size))):
        db.add_documents(batch)
        if i % 100 == 0:  # Log every 100 batches
            print(f"Processed {i * batch_size} documents...")
        gc.collect()  # Clean up resources

    db.persist()  # Ensure the database is saved to disk
    print(f"Stored {len(split_docs)} embeddings for {name} in {DB_PATHS[name]}")
    if errors:
        print(f"Skipped {len(errors)} files due to errors:")
        for err_file in errors:
            print(f"- {err_file}")

if __name__ == "__main__":
    create_embeddings_for_dataset("transcriptions", TextLoader)
    create_embeddings_for_dataset("books", TextLoader)
    # create_embeddings_for_dataset("articles", JSONLoader)
