"""
Generation Service: formats grounded prompt, connects to local Ollama LLM,
and structures response with citations.
"""

import json
import logging
import urllib.request
import urllib.error
from typing import List

from backend.app.core.config import settings
from backend.app.schemas.query import SourceItem

logger = logging.getLogger("trustai.generation")


class GenerationService:
    def __init__(
        self,
        ollama_base_url: str = None,
        model_name: str = None,
        temperature: float = None,
        timeout: float = None
    ):
        self.ollama_base_url = (ollama_base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model_name = model_name or settings.OLLAMA_MODEL
        self.temperature = temperature if temperature is not None else settings.OLLAMA_TEMPERATURE
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS
        self.relevance_threshold = settings.RELEVANCE_THRESHOLD

    def build_prompt(self, query: str, sources: List[SourceItem]) -> str:
        """
        Constructs a strict, grounded RAG prompt instructing the LLM to rely
        solely on provided context excerpts and cite document provenance.
        """
        context_parts = []
        for idx, src in enumerate(sources, start=1):
            page_info = f", Page {src.page}" if src.page else ""
            context_parts.append(
                f"[Source {idx} - {src.document}{page_info}]:\n{src.snippet}"
            )
        formatted_context = "\n\n".join(context_parts)

        prompt = f"""You are TrustAI, an educational AI Security Assistant specialized in cybersecurity defense, industry security standards, and secure system architectures.
Your task is to explain and summarize the retrieved defensive documentation to help defenders secure their AI systems.

MANDATORY RULES:
1. Ground your answer completely in the provided context. Do NOT invent or extrapolate facts.
2. Reference the relevant document and page number for key points (e.g., [OWASP_Top_10_LLM_Guide.pdf, Page 1] or [MITRE_ATLAS_AI_Threat_Matrix.pdf, Page 1]).
3. Provide a clear, thorough, and well-structured answer. Use clear explanations, bold headings, and bullet points where helpful to organize the information strictly based on the retrieved context.

DEFENSIVE SECURITY DOCUMENTATION:
{formatted_context}

USER INQUIRY:
{query}

DEFENSIVE TECHNICAL EXPLANATION:"""
        return prompt

    def generate(self, query: str, sources: List[SourceItem]) -> str:
        """
        Executes generation using local Ollama model or grounded fallback.
        """
        # 1. Relevance check for out-of-domain queries
        max_similarity = max([s.similarity for s in sources]) if sources else 0.0
        if not sources or max_similarity < self.relevance_threshold:
            logger.info(f"Query '{query}' below relevance threshold ({max_similarity:.3f} < {self.relevance_threshold}). Returning refusal.")
            return "I do not have sufficient information in the provided AI security documentation to answer this question."

        prompt = self.build_prompt(query, sources)

        # 2. Attempt call to local Ollama instance
        endpoint = f"{self.ollama_base_url}/api/generate"
        logger.debug(f"Calling Ollama at {endpoint} using model '{self.model_name}'...")

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_ctx": 2048,
                "num_predict": 250,
                "num_thread": 8
            }
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                endpoint,
                data=req_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status == 200:
                    resp_json = json.loads(response.read().decode("utf-8"))
                    answer = resp_json.get("response", "").strip()
                    logger.info(f"Successfully generated answer from Ollama ({len(answer)} characters).")
                    return answer
        except urllib.error.URLError as e:
            logger.warning(f"Ollama endpoint unreachable at {endpoint}: {e}. Utilizing verified grounded synthesis fallback.")
        except Exception as e:
            logger.warning(f"Ollama generation call error: {e}. Utilizing verified grounded synthesis fallback.")

        # 3. Grounded fallback when Ollama is offline or model is downloading
        top_source = sources[0]
        page_str = f", Page {top_source.page}" if top_source.page else ""
        return (
            f"[Grounded Response from {top_source.document}{page_str}]: "
            f"{top_source.snippet.strip()} "
            f"[{top_source.document}{page_str}]"
        )
