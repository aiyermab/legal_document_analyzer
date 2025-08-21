import logging
from pymilvus import connections, Collection
from langchain_openai import AzureOpenAIEmbeddings
from State import RAGState
import os

log = logging.getLogger(__name__)


def get_embed_model():
    embeddings = AzureOpenAIEmbeddings(
            azure_deployment=os.getenv("EMBED_DEPLOYMENT", "text-embedding-3-large"),
            model=os.getenv("EMBED_MODEL", "text-embedding-3-large"),
            openai_api_version=os.getenv("EMBED_API_VERSION", "2024-02-01"),
            azure_endpoint=os.getenv("EMBED_API_URL"),
            api_key=os.getenv("EMBED_API_KEY")
        )
    return embeddings


def retriever(state: RAGState) -> RAGState:
    try:
        # Connect to Milvus
        connections.connect("default", host="localhost", port=19530)
        collection = Collection("legal_documents")
        collection.load()

        final_results=  []
        embed_model=get_embed_model()
        
        clauses= state["document_report"].important_clauses
        # Query for similar documents
        for clause in clauses:
            query_embedding = embed_model.embed_query(clause)
            results = collection.search(
                data=[query_embedding],
                param={"nprobe": 32},
                anns_field="embedding",
                limit=5,
                output_fields=["id", "source", "text"],
                partition_names=None,
            )
            formatted_results = []
            for hits in results:
                for hit in hits:
                    formatted_results.append({
                        "text": hit['entity'].get("text", "N/A"),
                        "source": hit['entity'].get("source", "N/A")
                    })
            final_results.extend(formatted_results)
        state["retrieved_laws"] = final_results
        return state
    except Exception as e:
        log.error(f"Error in retriever: {e}")
        raise
