import os
import json
from typing import List, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_core.documents import Document
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
import logging

class DataIngestor:
    def __init__(
        self,
        milvus_host: str = "localhost",
        milvus_port: int = 19530,
        collection_name: str = "legal_documents"
    ):
        
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        self.collection_name = collection_name
        
        # Initialize embeddings
        self.embeddings = AzureOpenAIEmbeddings(
            azure_deployment=os.getenv("EMBED_DEPLOYMENT", "text-embedding-3-large"),
            model=os.getenv("EMBED_MODEL", "text-embedding-3-large"),
            openai_api_version=os.getenv("EMBED_API_VERSION", "2024-02-01"),
            azure_endpoint=os.getenv("EMBED_API_URL"),
            api_key=os.getenv("EMBED_API_KEY")
        )
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2048,
            chunk_overlap=200,
        )
        
        # Connect to Milvus
        self._connect_to_milvus()
        
    def _connect_to_milvus(self):
        """Connect to Milvus database"""
        try:
            connections.connect("default", uri=os.getenv("MIVLUS_URL"), user=os.getenv("MILVUS_USER"), password=os.getenv("MILVUS_PASSWORD"))
            logging.info("Connected to Milvus successfully")
        except Exception as e:
            logging.error(f"Failed to connect to Milvus: {e}")
            raise
    
    def _create_collection_if_not_exists(self, dim: int = 1536):
        """Create Milvus collection if it doesn't exist"""
        if utility.has_collection(self.collection_name):
            logging.info(f"Collection {self.collection_name} already exists")
            return
        
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=1000),
        ]
        
        schema = CollectionSchema(fields, "Legal document collection")
        collection = Collection(self.collection_name, schema)
        
        # Create index
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index("embedding", index_params)
        logging.info(f"Collection {self.collection_name} created successfully")
    
    def load_document(self, file_path: str):
        """Load document based on file extension"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        text_documents = []
        for d in data["text_by_page"]:
            text_documents.append(d["text"])   

        lang_docs= [Document(page_content=page) for page in text_documents]   
        return lang_docs
    
    def chunk_documents(self, documents):
        """Split documents into chunks"""
        return self.text_splitter.split_documents(documents)
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        return self.embeddings.embed_documents(texts)
    
    def store_in_milvus(self, chunks, embeddings, sources):
        """Store chunks and embeddings in Milvus"""
        # Create collection if it doesn't exist
        self._create_collection_if_not_exists(len(embeddings[0]))
        
        collection = Collection(self.collection_name)
        
        # Prepare data for insertion
        data = [
            [chunk.page_content for chunk in chunks],  # text
            embeddings,  # embedding
            sources  # source
        ]
        
        # Insert data
        mr = collection.insert(data)
        collection.flush()
        logging.info(f"Inserted {len(chunks)} chunks into Milvus")
        
        return mr
    
    def ingest_file(self, file_path: str):
        """Complete ingestion pipeline for a single file"""
        try:
            # Load document
            logging.info(f"Loading document: {file_path}")
            documents = self.load_document(file_path)
            
            # Chunk documents
            logging.info("Chunking documents...")
            chunks = self.chunk_documents(documents)
            
            # Generate embeddings
            logging.info("Generating embeddings...")
            texts = [chunk.page_content for chunk in chunks]
            embeddings = self.embed_texts(texts)
            
            # Prepare sources
            sources = [file_path] * len(chunks)
            
            # Store in Milvus
            logging.info("Storing in Milvus...")
            self.store_in_milvus(chunks, embeddings, sources)
            
            logging.info(f"Successfully ingested {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error ingesting file {file_path}: {e}")
            return False
    


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    ingestor = DataIngestor()
    ingestor.ingest_file("ingestion\\tnrrrlt_act_2017_extracted.json")
    
