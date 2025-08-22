from Orchestrator import rag_app
import logging

if __name__ == "__main__":
    document_path = "C:\\Users\\aiyermab\\Documents\\Mock Legal Documents\\Rental Agreement With Errors.docx"

    logging.info("Invoking Agents...")
    result = rag_app.invoke({"document_path": document_path})
    logging.info("Agents invoked successfully")
    print(result["legal_analysis"])