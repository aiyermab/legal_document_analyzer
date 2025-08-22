import streamlit as st
import tempfile
import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from Orchestrator import rag_app
    from src.logger_config import logger
    backend_available = True
except ImportError as e:
    st.error(f"Backend not available: {e}")
    backend_available = False

st.set_page_config(page_title="Legal Document Analyzer", layout="wide")
st.title("📄 Autonomous Agent for Legal Document/Contract Analysis")
st.markdown("""
Upload a legal document to analyze clauses, flag risks, and get suggestions based on Indian legal standards.
""")

uploaded_file = st.file_uploader("Upload your legal document (.txt, .pdf, .docx)", type=["txt", "pdf", "docx"])

if uploaded_file:
    st.success("File uploaded successfully!")

    # Process the document if backend is available
    if backend_available:
        with st.spinner("Analyzing document..."):
            try:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name

                # Process the document
                logger.info(f"Processing uploaded file: {uploaded_file.name}")
                result = rag_app.invoke({"document_path": tmp_file_path})

                # Clean up temporary file
                os.unlink(tmp_file_path)

                # Parse the legal analysis JSON
                legal_analysis = result.get("legal_analysis", "")

                # Try to parse as JSON
                analysis_data = None
                try:
                    # Handle cases where the response might be wrapped in markdown code blocks
                    if "```json" in legal_analysis:
                        json_start = legal_analysis.find("```json") + 7
                        json_end = legal_analysis.find("```", json_start)
                        json_str = legal_analysis[json_start:json_end].strip()
                    elif legal_analysis.strip().startswith("{"):
                        json_str = legal_analysis.strip()
                    else:
                        # If not JSON, treat as plain text
                        json_str = None

                    if json_str:
                        analysis_data = json.loads(json_str)
                except json.JSONDecodeError:
                    st.warning("Analysis result is not in JSON format. Displaying as text.")
                    analysis_data = None

            except Exception as e:
                st.error(f"Error processing document: {str(e)}")
                analysis_data = None
                legal_analysis = ""

    st.subheader("📘 Document Preview")
    if backend_available and 'result' in locals() and result.get("document"):
        # Show first 500 characters of the document
        doc_preview = result["document"][:500] + "..." if len(result["document"]) > 500 else result["document"]
        st.text_area("Document Content", doc_preview, height=150, disabled=True)
    else:
        st.info("Document content will be displayed here after analysis.")

    st.subheader("📑 Clause Extraction & Categorization")
    if backend_available and 'result' in locals() and result.get("document_report"):
        doc_report = result["document_report"]

        # Display extracted information
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Document Purpose:**")
            st.write(getattr(doc_report, 'purpose', 'Not identified'))

            st.write("**Date:**")
            st.write(getattr(doc_report, 'date', 'Not specified'))

        with col2:
            st.write("**Location:**")
            st.write(getattr(doc_report, 'location', 'Not specified'))

            st.write("**Parties Involved:**")
            parties = getattr(doc_report, 'parties_with_roles', [])
            if parties:
                for party in parties:
                    st.write(f"- {party.name} ({party.role})")
            else:
                st.write("No parties identified")

        st.write("**Important Clauses:**")
        clauses = getattr(doc_report, 'important_clauses', [])
        if clauses:
            for i, clause in enumerate(clauses, 1):
                st.write(f"{i}. {clause}")
        else:
            st.write("No important clauses identified")
    else:
        st.warning("Clause extraction will be displayed here after document analysis.")

    st.subheader("⚠️ Risk Flagging")
    if analysis_data and "risks" in analysis_data:
        if analysis_data["risks"]:
            for risk in analysis_data["risks"]:
                st.error(f"🚨 {risk}")
        else:
            st.success("No significant risks identified in the document.")
    else:
        st.error("Risk analysis will be displayed here after document processing.")

    st.subheader("📋 Omissions")
    if analysis_data and "omissions" in analysis_data:
        if analysis_data["omissions"]:
            for omission in analysis_data["omissions"]:
                st.warning(f"⚠️ {omission}")
        else:
            st.success("No critical omissions detected.")
    else:
        st.warning("Missing clause analysis will be displayed here.")

    st.subheader("✏️ Corrections Required")
    if analysis_data and "corrections" in analysis_data:
        if analysis_data["corrections"]:
            for correction in analysis_data["corrections"]:
                st.error(f"📝 {correction}")
        else:
            st.success("No corrections required.")
    else:
        st.warning("Correction suggestions will be displayed here.")

    st.subheader("⚖️ Compliance Issues")
    if analysis_data and "compliance" in analysis_data:
        if analysis_data["compliance"]:
            for compliance_issue in analysis_data["compliance"]:
                st.error(f"⚖️ {compliance_issue}")
        else:
            st.success("Document appears to be compliant with legal standards.")
    else:
        st.warning("Compliance analysis will be displayed here.")

    st.subheader("💡 Suggestions & Improvements")
    if analysis_data and "recommendations" in analysis_data:
        if analysis_data["recommendations"]:
            for recommendation in analysis_data["recommendations"]:
                st.success(f"💡 {recommendation}")
        else:
            st.info("No additional recommendations at this time.")
    else:
        st.success("Improvement suggestions will be provided after analysis.")

    st.subheader("📊 Executive Summary")
    if analysis_data and "executive_summary" in analysis_data:
        st.info(analysis_data["executive_summary"])
    else:
        st.info("Executive summary will be generated after document analysis.")

    st.subheader("📚 Legal References")
    if backend_available and 'result' in locals() and result.get("retrieved_laws"):
        retrieved_laws = result["retrieved_laws"]
        if retrieved_laws:
            st.write(f"Found {len(retrieved_laws)} relevant legal references:")
            for i, law in enumerate(retrieved_laws[:5], 1):  # Show top 5
                with st.expander(f"Reference {i}: {law.get('source', 'Unknown Source')}"):
                    st.write(law.get('text', 'No text available'))
                    if 'score' in law:
                        st.caption(f"Relevance Score: {law['score']:.3f}")
        else:
            st.info("No specific legal references found in the database.")
    else:
        st.info("Legal references will be mapped to Indian laws or judgments here.")

    st.subheader("🧾 Ask the Agent")
    user_query = st.text_input("Ask a question about the document (e.g., 'What is the risk in the indemnity clause?')")
    if user_query:
        if backend_available and 'result' in locals():
            with st.spinner("Processing your question..."):
                try:
                    # Simple Q&A based on the analysis
                    if analysis_data:
                        context = f"""
                        Document Analysis Summary:
                        - Risks: {analysis_data.get('risks', [])}
                        - Omissions: {analysis_data.get('omissions', [])}
                        - Recommendations: {analysis_data.get('recommendations', [])}
                        - Executive Summary: {analysis_data.get('executive_summary', '')}
                        
                        User Question: {user_query}
                        """

                        # For now, provide a contextual response based on the analysis
                        response = f"Based on the document analysis, here's what I found regarding your question about '{user_query}':\n\n"

                        # Search for relevant information in the analysis
                        query_lower = user_query.lower()
                        if "risk" in query_lower and analysis_data.get("risks"):
                            response += "**Identified Risks:**\n"
                            for risk in analysis_data["risks"]:
                                response += f"- {risk}\n"

                        if "missing" in query_lower or "omission" in query_lower and analysis_data.get("omissions"):
                            response += "\n**Missing Elements:**\n"
                            for omission in analysis_data["omissions"]:
                                response += f"- {omission}\n"

                        if "recommend" in query_lower and analysis_data.get("recommendations"):
                            response += "\n**Recommendations:**\n"
                            for rec in analysis_data["recommendations"]:
                                response += f"- {rec}\n"

                        if len(response.split('\n')) <= 3:  # If no specific matches found
                            response += analysis_data.get("executive_summary", "Please refer to the analysis sections above for detailed information.")

                        st.write(response)
                    else:
                        st.write("Please wait for the document analysis to complete before asking questions.")

                except Exception as e:
                    st.error(f"Error processing question: {str(e)}")
        else:
            st.write("Please ensure the document is fully analyzed before asking questions.")

    # Display raw analysis for debugging (optional)
    if backend_available and 'legal_analysis' in locals() and st.checkbox("Show Raw Analysis (Debug)"):
        st.subheader("🔍 Raw Analysis Output")
        st.code(legal_analysis, language="json" if analysis_data else "text")

else:
    st.info("Please upload a document to begin analysis.")
