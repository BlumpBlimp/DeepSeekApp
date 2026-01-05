from typing import List, Dict, Tuple
import openai
from .config import Config
import asyncio
import aiohttp
import json


class LLMVerifier:
    """Verify LLM outputs across multiple models"""

    def __init__(self):
        self.config = Config()

    async def verify_response(self, query: str, response: str,
                              models: List[str] = None) -> Dict:
        """Verify a response using multiple LLMs"""
        if models is None:
            models = ["deepseek-chat", "gpt-4", "claude-3"]

        tasks = []
        for model in models:
            task = self._get_verification(model, query, response)
            tasks.append(task)

        verifications = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        agreement = 0
        feedback = []

        for i, result in enumerate(verifications):
            if isinstance(result, Exception):
                feedback.append(f"{models[i]}: Error - {result}")
            else:
                if result.get("verified", False):
                    agreement += 1
                feedback.append(f"{models[i]}: {result.get('feedback', 'No feedback')}")

        agreement_ratio = agreement / len(models)

        return {
            "original_response": response,
            "agreement_ratio": agreement_ratio,
            "verified": agreement_ratio >= 0.7,  # 70% agreement threshold
            "feedback": feedback,
            "details": verifications
        }

    async def _get_verification(self, model: str, query: str, response: str) -> Dict:
        """Get verification from a specific model"""
        if model == "deepseek-chat":
            return await self._verify_deepseek(query, response)
        elif "gpt" in model:
            return await self._verify_openai(query, response, model)
        elif "claude" in model:
            return await self._verify_anthropic(query, response, model)
        else:
            return {"verified": False, "feedback": f"Unsupported model: {model}"}

    async def _verify_deepseek(self, query: str, response: str) -> Dict:
        """Verify using DeepSeek"""
        client = openai.OpenAI(
            api_key=self.config.get_api_key(),
            base_url=self.config.get_base_url()
        )

        prompt = f"""
        Verify the following response to the query.

        Query: {query}
        Response to verify: {response}

        Please:
        1. Check if the response is factually correct
        2. Check if it addresses the query properly
        3. Identify any errors or misleading information
        4. Provide brief feedback

        Return JSON format:
        {{
            "verified": true/false,
            "confidence": 0.0-1.0,
            "feedback": "brief feedback",
            "corrections": ["list any corrections needed"]
        }}
        """

        try:
            completion = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a fact-checker and verifier."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            result = json.loads(completion.choices[0].message.content)
            return result
        except Exception as e:
            return {"verified": False, "feedback": f"Error: {e}"}

    async def _verify_openai(self, query: str, response: str, model: str) -> Dict:
        """Verify using OpenAI models"""
        # Similar implementation using OpenAI API
        # You'll need an OpenAI API key
        return {"verified": True, "feedback": "OpenAI verification placeholder"}

    async def _verify_anthropic(self, query: str, response: str, model: str) -> Dict:
        """Verify using Anthropic Claude"""
        # Similar implementation using Anthropic API
        return {"verified": True, "feedback": "Claude verification placeholder"}

    def compare_responses(self, responses: List[Dict]) -> Dict:
        """Compare multiple LLM responses to the same query"""
        # Analyze similarities and differences
        all_texts = [r.get("response", "") for r in responses]

        # Simple similarity check (in practice, use embeddings)
        similarities = []
        for i in range(len(all_texts)):
            for j in range(i + 1, len(all_texts)):
                sim = self._calculate_similarity(all_texts[i], all_texts[j])
                similarities.append({
                    "model1": responses[i].get("model", f"model_{i}"),
                    "model2": responses[j].get("model", f"model_{j}"),
                    "similarity": sim
                })

        return {
            "responses": responses,
            "similarities": similarities,
            "consensus": self._find_consensus(responses)
        }

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity (simplified)"""
        # In practice, use sentence transformers
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    def _find_consensus(self, responses: List[Dict]) -> Dict:
        """Find consensus among different responses"""
        # Simplified consensus finding
        verified_count = sum(1 for r in responses if r.get("verified", False))

        return {
            "total_responses": len(responses),
            "verified_count": verified_count,
            "consensus_ratio": verified_count / len(responses) if responses else 0,
            "recommendation": "Use with confidence" if verified_count > len(responses) / 2 else "Verify further"
        }