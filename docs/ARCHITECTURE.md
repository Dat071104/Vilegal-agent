# Planned Architecture

This is the original aspirational architecture. The current audited repo intentionally stops before QA generation, fine-tuning, RAG/vector indexing, and deployment; those phases remain blocked.

The planned architecture for the ViLegal Agent is as follows:

1.  **Data Pipeline:**
    *   Ingests Vietnamese legal documents.
    *   Cleans and structures data into a standard format.
2.  **Fine-tuned LLM:**
    *   Base model fine-tuned using QLoRA on a curated Vietnamese legal dataset.
3.  **LangGraph Agent:**
    *   Manages the state and routing for answering complex legal queries.
4.  **RAG + Citation Verification:**
    *   Retrieves relevant legal clauses using vector search.
    *   Cross-references and verifies generated claims against source texts.
5.  **Evaluation:**
    *   Automated metrics and manual human-in-the-loop review for legal accuracy.
6.  **Deployment:**
    *   API and user interface (TBD) for interacting with the agent.
