from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import tempfile
from typing import Optional
import sys

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from Orchestrator import rag_app

app = FastAPI(
    title="Legal Document Analyzer API",
    description="REST API for analyzing legal documents using AI",
    version="1.0.0"
)

class FilePathRequest(BaseModel):
    file_path: str

class AnalysisResponse(BaseModel):
    legal_analysis: str
    status: str
    message: str

@app.post("/analyze/file", response_model=AnalysisResponse)
async def analyze_uploaded_file(file: UploadFile = File(...)):
    """
    Analyze a legal document by uploading a file.
    Supports .txt, .pdf, .docx files.
    """
    try:
        # Validate file type
        allowed_extensions = {'.txt', '.pdf', '.docx'}
        file_extension = os.path.splitext(file.filename)[1].lower()

        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
            )

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Process the document using the existing orchestrator
            result = rag_app.invoke({"document_path": temp_file_path})

            return AnalysisResponse(
                legal_analysis=result["legal_analysis"],
                status="success",
                message=f"Successfully analyzed uploaded file: {file.filename}"
            )

        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/analyze/filepath", response_model=AnalysisResponse)
async def analyze_file_by_path(request: FilePathRequest):
    """
    Analyze a legal document by providing a file path.
    For local demo purposes - accepts file paths on the local system.
    """
    try:
        file_path = request.file_path

        # Validate file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

        # Validate file type
        allowed_extensions = {'.txt', '.pdf', '.docx'}
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
            )

        # Process the document using the existing orchestrator
        result = rag_app.invoke({"document_path": file_path})

        return AnalysisResponse(
            legal_analysis=result["legal_analysis"],
            status="success",
            message=f"Successfully analyzed file: {os.path.basename(file_path)}"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/analyze/combined")
async def analyze_document(
    file_path: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    Analyze a legal document by either uploading a file OR providing a file path.
    This endpoint accepts either parameter but not both.
    """
    try:
        if file and file_path:
            raise HTTPException(
                status_code=400,
                detail="Please provide either a file upload OR a file path, not both"
            )

        if not file and not file_path:
            raise HTTPException(
                status_code=400,
                detail="Please provide either a file upload OR a file path"
            )

        # Handle file upload
        if file:
            return await analyze_uploaded_file(file)

        # Handle file path
        if file_path:
            request = FilePathRequest(file_path=file_path)
            return await analyze_file_by_path(request)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/")
async def root():
    """
    Root endpoint providing API information.
    """
    return {
        "message": "Legal Document Analyzer API",
        "version": "1.0.0",
        "endpoints": {
            "/analyze/file": "POST - Upload a file for analysis",
            "/analyze/filepath": "POST - Analyze file by providing local file path",
            "/analyze/combined": "POST - Upload file OR provide file path",
            "/docs": "GET - Interactive API documentation"
        }
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "service": "legal-document-analyzer"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
