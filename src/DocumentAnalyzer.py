from langchain_openai import AzureChatOpenAI
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain_core.prompts import PromptTemplate as LangChainPromptTemplate
from State import RAGState, LegalDocumentAnalysis
from logger_config import logger
import logging
import os

def get_llm_model():
    logger.info("Initializing Azure OpenAI LLM model")
    try:
        llm = AzureChatOpenAI(
            model=os.getenv("LLM_MODEL", "gpt-5"),
            azure_deployment=os.getenv("LLM_DEPLOYMENT", "gpt-5"),
            api_key=os.getenv("LLM_API_KEY"),
            azure_endpoint=os.getenv("LLM_API_URL"),
            api_version=os.getenv("LLM_API_VERSION", "2024-12-01-preview"),
            temperature=0.1,
            )
        logger.info(f"LLM model initialized successfully with deployment: {os.getenv('LLM_DEPLOYMENT', 'gpt-5')}")
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize LLM model: {str(e)}")
        raise

def load_document(file_path: str) -> str:
    """Load and extract text from DOCX file"""
    logger.info(f"Loading document from path: {file_path}")
    try:
        if not os.path.exists(file_path):
            logger.error(f"Document file not found: {file_path}")
            raise FileNotFoundError(f"Document file not found: {file_path}")

        loader = UnstructuredWordDocumentLoader(file_path)
        documents = loader.load()

        if not documents:
            logger.warning(f"No content extracted from document: {file_path}")
            return ""

        content = documents[0].page_content
        logger.info(f"Successfully loaded document with {len(content)} characters")
        logger.debug(f"Document content preview: {content[:200]}...")
        return content
    except Exception as e:
        logger.error(f"Failed to load document {file_path}: {str(e)}")
        raise

def create_prompt() -> LangChainPromptTemplate:
    """Create the analysis prompt template"""
    template = """
    You are a legal document analysis expert. Analyze the following legal document and extract the required information.
    
    Document Content:
    {document_text}
    
    Please analyze this document and provide structured output with the following information:
    - Purpose: What type of legal document this is and its main purpose
    - Parties Involved: All individuals, companies, or entities mentioned as parties
    - Date: Any dates mentioned in the document
    - Location: City, state, and country mentioned
    - Important Clauses: Key provisions, terms, conditions, or clauses that are legally significant. 

    """
    
    return LangChainPromptTemplate.from_template(template)

def get_parties_dict(result: LegalDocumentAnalysis) -> dict:
        """Convert parties with roles to a dictionary format"""
        return {party.name: party.role for party in result.parties_with_roles}

def analyze_document(state : RAGState) -> RAGState:
    """Analyze the legal document and return structured results"""
    logger.info("Starting document analysis")
    logger.debug(f"Processing document: {state.get('document_path', 'Unknown')}")

    try:
        # Load document content
        document_text = load_document(state["document_path"])
        state["document"] = document_text
        logger.info("Document loaded successfully, proceeding to next step")

        # Create prompt
        prompt = create_prompt()

        llm = get_llm_model()
        sllm= llm.with_structured_output(LegalDocumentAnalysis)

        llm_chain= prompt | sllm

        logging.info("Analyzing document...")
        # Get LLM response
        response = llm_chain.invoke({"document_text": document_text})

        state["document_report"] = response
        logging.info("Document analysis complete")
        return state
    except Exception as e:
        logger.error(f"Document analysis failed: {str(e)}")
        raise
