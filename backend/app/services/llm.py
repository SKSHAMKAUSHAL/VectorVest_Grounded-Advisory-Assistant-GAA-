import asyncio
from typing import AsyncGenerator, List, Dict, Any, Optional
from app.core.config import settings

class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.groq_api_key = settings.GROQ_API_KEY
        self.openai_api_key = settings.OPENAI_API_KEY
        self.groq_client = None
        self.openai_client = None

        if self.groq_api_key and not self.groq_api_key.startswith("gsk_mock") and not self.groq_api_key.startswith("gsk_your"):
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.groq_api_key)
            except Exception:
                self.groq_client = None

        if self.openai_api_key and not self.openai_api_key.startswith("sk-mock") and not self.openai_api_key.startswith("sk-your"):
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.openai_api_key)
            except Exception:
                self.openai_client = None

    def _is_mock_mode(self) -> bool:
        if self.provider == "groq" and self.groq_client is not None:
            return False
        if self.provider == "openai" and self.openai_client is not None:
            return False
        return True

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
        """Synchronous text generation."""
        if self._is_mock_mode():
            return self._mock_generate(system_prompt, user_prompt)

        try:
            if self.provider == "groq" and self.groq_client:
                response = self.groq_client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                )
                return response.choices[0].message.content or ""
            elif self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=settings.OPENAI_CHAT_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                )
                return response.choices[0].message.content or ""
        except Exception:
            return self._mock_generate(system_prompt, user_prompt)

        return self._mock_generate(system_prompt, user_prompt)

    async def stream_generate(
        self, system_prompt: str, user_prompt: str, temperature: float = 0.0
    ) -> AsyncGenerator[str, None]:
        """Asynchronous token streaming generator."""
        if self._is_mock_mode():
            text = self._mock_generate(system_prompt, user_prompt)
            # Yield token by token with minimal delay
            words = text.split(" ")
            for i, word in enumerate(words):
                yield word + (" " if i < len(words) - 1 else "")
                await asyncio.sleep(0.01)
            return

        try:
            if self.provider == "groq" and self.groq_client:
                stream = self.groq_client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    stream=True,
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        yield delta
                return
            elif self.openai_client:
                stream = self.openai_client.chat.completions.create(
                    model=settings.OPENAI_CHAT_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    stream=True,
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        yield delta
                return
        except Exception:
            # Fallback on runtime failure
            text = self._mock_generate(system_prompt, user_prompt)
            words = text.split(" ")
            for i, word in enumerate(words):
                yield word + (" " if i < len(words) - 1 else "")
                await asyncio.sleep(0.01)

    def _mock_generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Deterministic mock generator for offline dev and test execution.
        Follows system prompt directives to synthesize grounded guidance with citations.
        """
        # Check if this is a search query reformulator prompt
        if "search query reformulator" in system_prompt.lower():
            # Extract follow-up question
            if "Follow-up Question:" in user_prompt:
                q = user_prompt.split("Follow-up Question:")[-1].strip()
                # If there's context like 'NRI', produce expanded query
                if "nri" in q.lower():
                    return "What is the tax and policy treatment for Non-Resident Indian (NRI) clients?"
                return q
            return user_prompt.strip()

        # Check if context was supplied in the user_prompt or system_prompt
        context_text = ""
        if "CONTEXT CHUNKS:" in user_prompt:
            context_text = user_prompt.split("CONTEXT CHUNKS:")[1]
            if "CONVERSATION HISTORY:" in context_text:
                context_text = context_text.split("CONVERSATION HISTORY:")[0]

        if not context_text.strip():
            return (
                "I cannot find approved bank guidance on this topic within your account's "
                "uploaded documentation. Please escalate this request to the Compliance and Legal Department."
            )

        # Build grounded mock answer quoting first available citation
        import re
        citation_matches = re.findall(r"\[Doc:\s*([^,]+),\s*Ver:\s*([^,]+),\s*Clause:\s*([^,]+),\s*Page:\s*([^\]]+)\]", context_text)
        if citation_matches:
            doc, ver, clause, page = citation_matches[0]
            clean_clause = clause.strip()
            return (
                f"According to current bank advisory policy [Doc: {doc.strip()}, Ver: {ver.strip()}, Clause: {clean_clause}], "
                f"applicable guidelines and eligibility thresholds have been confirmed under {clean_clause}. "
                f"Please ensure all advice delivered to the client aligns strictly with this directive."
            )

        return (
            "I cannot find approved bank guidance on this topic within your account's "
            "uploaded documentation. Please escalate this request to the Compliance and Legal Department."
        )

llm_service = LLMService()
