from langchain_openai import AzureChatOpenAI
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain_core.prompts import PromptTemplate as LangChainPromptTemplate
from State import RAGState, LegalDocumentAnalysis
import os

def get_llm_model():
    llm = AzureChatOpenAI(
        model=os.getenv("LLM_MODEL", "gpt-5"),
        azure_deployment=os.getenv("LLM_DEPLOYMENT", "gpt-5"),
        api_key=os.getenv("LLM_API_KEY"),
        azure_endpoint=os.getenv("LLM_API_URL"),
        api_version=os.getenv("LLM_API_VERSION", "2024-12-01-preview"),
        temperature=0.1,
        )
    return llm
        
def load_document(file_path: str) -> str:
    """Load and extract text from DOCX file"""
    loader = UnstructuredWordDocumentLoader(file_path)
    documents = loader.load()
    return documents[0].page_content if documents else ""

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
    - Important Clauses: Key provisions, terms, conditions, or clauses that are legally significant

    """
    
    return LangChainPromptTemplate.from_template(template)

def get_parties_dict(result: LegalDocumentAnalysis) -> dict:
        """Convert parties with roles to a dictionary format"""
        return {party.name: party.role for party in result.parties_with_roles}

def analyze_document(state : RAGState) -> RAGState:
    """Analyze the legal document and return structured results"""
    # Load document content
    document_text = load_document(state["document_path"])
    state["document"] = document_text
    
    if not document_text:
        raise ValueError("Could not extract text from the document")
    
    # Create prompt
    prompt = create_prompt()
    
    llm = get_llm_model()
    sllm= llm.with_structured_output(LegalDocumentAnalysis)

    llm_chain= prompt | sllm
    
    # Get LLM response
    response = llm_chain.invoke({"document_text": document_text})

    state["document_report"] = response
    
    return state



