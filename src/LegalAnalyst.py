from langchain_core.prompts import PromptTemplate as LangChainPromptTemplate
from langchain_openai import AzureChatOpenAI
from State import RAGState
from logger_config import logger
import os

def get_llm_model():
    logger.info("Initializing LLM model for legal analysis")
    try:
        llm = AzureChatOpenAI(
            model=os.getenv("LLM_MODEL", "gpt-5"),
            azure_deployment=os.getenv("LLM_DEPLOYMENT", "gpt-5"),
            api_key=os.getenv("LLM_API_KEY"),
            azure_endpoint=os.getenv("LLM_API_URL"),
            api_version=os.getenv("LLM_API_VERSION", "2024-12-01-preview"),
            temperature=0.1,
            )
        logger.info("LLM model initialized successfully for legal analysis")
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize LLM model for legal analysis: {str(e)}")
        raise

def legal_analysis(state : RAGState) -> RAGState:
    logger.info("Starting legal analysis phase")

    try:
        prompt = """
        You are a legal Analyst reviewing a document looking for omissions/corrections required. 
        Inputs are the document and a list of context documents from Government Acts and Laws.
        original document: {original_document}
        clauses from Government Acts and Laws: {clauses}

        Please analyze the document and provide the following information:
        - Omissions: Any missing information or clauses that should be included
        - Corrections: Any incorrect or misleading information that needs to be revised
        - Compliance: Any sections that do not comply with the law
        - Risks: Any potential risks or liabilities in the document
        - Recommendations: Any suggestions for improving the document
        - Executive Summary: A brief summary of the document analysis
        
        Return a structured JSON object with the following format:
        {{
            "omissions": ["Missing clause X"],
            "corrections": ["Correct clause Y"],
            "compliance": ["Non-compliant section Z"],
            "risks": ["Risk of ABC"],
            "recommendations": ["Include clause A"],
            "executive_summary": "The document is mostly compliant with the law, but there are several areas that need attention."
        }}
        """

        prompt_template = LangChainPromptTemplate.from_template(prompt)
        llm = get_llm_model()

        logger.info("Invoking LLM model for legal analysis...")
        llm_chain = prompt_template | llm

        original_document = state["document"]
        clauses = state.get("retrieved_laws", [])

        logger.debug(f"Analyzing document with {len(original_document)} characters")
        logger.debug(f"Using {len(clauses)} law clauses for context")

        response = llm_chain.invoke({
            "original_document": original_document,
            "clauses": clauses
        })

        state["legal_analysis"] = response.content
        logger.info("Legal analysis completed successfully")
        logger.debug(f"Analysis result length: {len(response.content)} characters")

        return state

    except Exception as e:
        logger.error(f"Legal analysis failed: {str(e)}")
        raise
