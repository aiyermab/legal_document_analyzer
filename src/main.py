from Orchestrator import rag_app

if __name__ == "__main__":
    document_path = "C:\\Users\\aiyermab\\Documents\\Mock Legal Documents\\Rental Agreement With Errors.docx"
    result = rag_app.invoke({"document_path": document_path})
    print(result["legal_analysis"])