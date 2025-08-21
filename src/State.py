from typing import Dict
from pydantic import BaseModel, Field
from typing import List, Optional

class PartyRole(BaseModel):
    name: str = Field(description="Name of the party")
    role: str = Field(description="Role or designation of the party in the document")

class LegalDocumentAnalysis(BaseModel):
    purpose: str = Field(description="The main purpose or type of the legal document")
    parties_involved: List[PartyRole] = Field(description="List of all parties mentioned in the document")
    date: Optional[str] = Field(description="Date mentioned in the document (if any)")
    city: Optional[str] = Field(description="City mentioned in the document")
    state: Optional[str] = Field(description="State mentioned in the document") 
    country: Optional[str] = Field(description="Country mentioned in the document")
    important_clauses: List[str] = Field(description="List of important clauses or provisions in the document")


class RAGState(Dict):
    document_path: str
    document: str
    document_report:LegalDocumentAnalysis
    retrieved_laws: dict
    legal_analysis: dict
