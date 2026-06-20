from app.generator.prompts import build_generation_prompt
from app.llm.ollama_llm import OllamaLLM
from app.rag.langchain_rag import LangChainRAGService


class TestGenerator:
    """
    Week 2 generator.

    Flow:
    1. Take natural language user prompt.
    2. Retrieve similar historical automation code from ChromaDB.
    3. Build final prompt.
    4. Send prompt to local LLM through Ollama.
    5. Return generated automation code.
    """

    def __init__(self):
        self.rag_service = LangChainRAGService()
        self.llm = OllamaLLM()

    def generate(
        self,
        prompt: str,
        framework: str,
        top_k: int = 4,
    ) -> dict:
        retrieved_docs = self.rag_service.search(
            query=prompt,
            framework=framework,
            top_k=top_k,
        )

        llm_prompt = build_generation_prompt(
            user_prompt=prompt,
            framework=framework,
            retrieved_docs=retrieved_docs,
        )

        generated_code = self.llm.generate(llm_prompt)

        return {
            "framework": framework,
            "prompt": prompt,
            "retrieved_context_count": len(retrieved_docs),
            "generated_code": generated_code,
        }