from langgraph.graph import StateGraph, END
from DocumentAnalyzer import analyze_document
from Retriever import retriever
from LegalAnalyst import legal_analysis
from State import RAGState
from logger_config import logger

logger.info("Initializing Legal Document Analyzer orchestrator")

graph = StateGraph(RAGState)

graph.add_node("DocumentAnalyzer", analyze_document)
graph.add_node("Retriever", retriever)
graph.add_node("LegalAnalyst", legal_analysis)

graph.add_edge("DocumentAnalyzer", "Retriever")
graph.add_edge("Retriever", "LegalAnalyst")
graph.add_edge("LegalAnalyst", END)

graph.set_entry_point("DocumentAnalyzer")


# Compile app
logging.info("Compiling RAG App...")
rag_app = graph.compile()
logger.info("Legal Document Analyzer orchestrator initialized successfully")
