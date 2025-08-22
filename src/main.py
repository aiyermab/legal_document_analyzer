import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from Orchestrator import rag_app
from logger_config import logger

if __name__ == "__main__":
    logger.info("Starting legal document analysis from main.py")

    document_path = "C:\\Users\\aiyermab\\Documents\\Mock Legal Documents\\Rental Agreement With Errors.docx"

    # Check if the document exists, if not use the test document
    if not os.path.exists(document_path):
        logger.warning(f"Original document not found: {document_path}")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        document_path = os.path.join(current_dir, "test_rental_agreement.docx")
        logger.info(f"Using test document instead: {document_path}")

    try:
        logger.info(f"Processing document: {document_path}")
        result = rag_app.invoke({"document_path": document_path})

        logger.info("Legal analysis completed successfully")
        print("\n" + "="*60)
        print("LEGAL DOCUMENT ANALYSIS RESULT")
        print("="*60)
        print(result["legal_analysis"])
        print("="*60)

    except Exception as e:
        logger.error(f"Failed to process document: {str(e)}")
        print(f"Error: {str(e)}")
