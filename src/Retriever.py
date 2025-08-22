import logging
from pymilvus import connections, Collection
from langchain_openai import AzureOpenAIEmbeddings
from State import RAGState
from logger_config import logger
import os


def get_embed_model():
    logger.info("Initializing Azure OpenAI embeddings model")
    try:
        embeddings = AzureOpenAIEmbeddings(
            azure_deployment=os.getenv("EMBED_DEPLOYMENT", "text-embedding-3-large"),
            model=os.getenv("EMBED_MODEL", "text-embedding-3-large"),
            openai_api_version=os.getenv("EMBED_API_VERSION", "2024-02-01"),
            azure_endpoint=os.getenv("EMBED_API_URL"),
            api_key=os.getenv("EMBED_API_KEY")
        )
        logger.info("Embeddings model initialized successfully")
        return embeddings
    except Exception as e:
        logger.error(f"Failed to initialize embeddings model: {str(e)}")
        raise


def retriever(state: RAGState) -> RAGState:
    logger.info("Starting document retrieval phase")

    try:
        # Connect to Milvus
        logger.info("Connecting to Milvus database")
        connections.connect(
            "default",
            uri=os.getenv("MILVUS_URL", "http://localhost:19530"),
            user=os.getenv("MILVUS_USER", ""),
            password=os.getenv("MILVUS_PASSWORD", "")
        )

        collection = Collection("legal_documents")
        collection.load()
        logger.info("Connected to Milvus collection 'legal_documents'")

        final_results = []
        embed_model = get_embed_model()

        clauses = state["document_report"].important_clauses
        logger.info(f"Retrieving similar documents for {len(clauses)} clauses")

        # Query for similar documents
        for i, clause in enumerate(clauses):
            logger.debug(f"Processing clause {i+1}: {clause[:100]}...")

            query_embedding = embed_model.embed_query(clause)
            results = collection.search(
                data=[query_embedding],
                param={"nprobe": 32},
                anns_field="embedding",
                limit=3,  # Increased limit for better context
                output_fields=["id", "source", "text"],
                partition_names=None,
            )

            formatted_results = []
            for hits in results:
                for hit in hits:
                    formatted_results.append({
                        "text": hit['entity'].get("text", "N/A"),
                        "source": hit['entity'].get("source", "N/A"),
                        "score": hit.score,
                        "id": hit['entity'].get("id", "N/A")
                    })

            final_results.extend(formatted_results)
            logger.debug(f"Found {len(formatted_results)} relevant documents for clause {i+1}")

        state["retrieved_laws"] = final_results
        logger.info(f"Document retrieval completed. Retrieved {len(final_results)} relevant law documents")

        return state

    except Exception as e:
        logger.error(f"Document retrieval failed: {str(e)}")
        # For demo purposes, continue with empty retrieval if Milvus is not available
        logger.warning("Continuing with empty law retrieval due to database connection issues")
        state["retrieved_laws"] = []
        return state
