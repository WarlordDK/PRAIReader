# utils/image_analyzer.py

import json
import io
import re
from typing import List, Dict, Any, Optional
from PIL import Image
from huggingface_hub import InferenceClient

from core.config import get_hf_token


class ImageAnalyzer:

    def __init__(self):
        self.hf_token: Optional[str] = get_hf_token()
        self.vlm_client: Optional[InferenceClient] = None
        self.llm_client: Optional[InferenceClient] = None

        self.caption_model = "Salesforce/blip2-flan-t5-xl"
        self.reasoning_model = "IlyaGusev/saiga_llama3_8b"

        self.models_initialized = False

    async def initialize_models(self):
        if self.models_initialized:
            return
        try:
            self.vlm_client = InferenceClient(model=self.caption_model, token=self.hf_token)
            self.llm_client = InferenceClient(token=self.hf_token)
            self.models_initialized = True
            print(f"[ImageAnalyzer] InferenceClient ready (model {self.caption_model})")
        except Exception as e:
            print(f"[ImageAnalyzer] init error: {e}")
            self.models_initialized = False

    async def analyze_visual_presentation(self, slide_images: List[Image.Image]) -> Dict[str, Any]:

        if not self.models_initialized:
            return self._fallback()

        slide_results = []

        # --- Extract per-slide measurements ---
        for idx, img in enumerate(slide_images, start=1):
            info = {"slide_number": idx}

            try:
                info["caption"] = self._caption(img)
            except:
                info["caption"] = ""

            stats = self._estimate_text_density(img)
            info["text_density"] = stats["text_density"]
            info["text_coverage"] = stats["text_coverage"]

            slide_results.append(info)

        prompt = self._build_global_prompt(slide_results)

        raw = self._call_llm(prompt)
        parsed = self._try_parse_json(raw)

        if parsed:
            return parsed

        return self._fallback()

    def _caption(self, img: Image.Image) -> str:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        try:
            resp = self.vlm_client.image_to_text(buf)
            return resp.get("generated_text", "").strip()
        except:
            return ""

    def _estimate_text_density(self, img: Image.Image) -> Dict[str, float]:
        gray = img.convert("L")
        hist = gray.histogram()

        dark = sum(hist[:70])
        total = sum(hist)

        density = dark / total if total else 0
        coverage = min(1.0, density * 1.8)

        return {
            "text_density": round(density, 4),
            "text_coverage": round(coverage, 4)
        }

    def _build_global_prompt(self, slides: List[Dict[str, Any]]) -> str:

        return (
            "Ты — эксперт по дизайну презентаций.\n"
            "Тебе переданы визуальные характеристики каждого слайда:\n"
            "- caption (краткое описание картинки)\n"
            "- text_density (оценка количества текста)\n"
            "- text_coverage (занятость текста на слайде)\n\n"

            "Важно: анализируй только визуальную составляющую. Не анализируй содержание текста.\n\n"

            "Используя данные по каждому слайду, определи:\n"
            "— на каких слайдах есть слишком много текста\n"
            "— на каких слайдах слишком много изображений\n"
            "— на каких слайдах мало визуальной структуры\n"
            "— где плохие пропорции, контрастность, несбалансированность\n"
            "— где встречаются повторяющиеся визуальные проблемы\n\n"

            "Обязательное требование:\n"
            "ВНИСИ НОМЕРА СЛАЙДОВ В КАЖДЫЙ ПУНКТ weaknesses и recommendations.\n"
            "Например: 'Слайды 3, 5: перегруз контентом'.\n"
            "А так же напиши сильные стороны визуального оформления презентации (2-3 пункта) \n "
            "Не пиши абстрактные рекомендации.\n\n"

            "Верни строго JSON:\n"
            "{\n"
            '  "visual_strengths": [string,...],\n'
            '  "visual_weaknesses": [string,...],\n'
            '  "recommendations": [string,...],\n'
            '  "design_style": string,\n'
            '  "visual_quality_score": int,\n'
            '  "final_verdict": string\n'
            "}\n\n"
            f"Вот данные всех слайдов:\n{json.dumps(slides, ensure_ascii=False)}"
        )

    def _call_llm(self, prompt: str) -> str:
        try:
            resp = self.llm_client.chat_completion(
                model=self.reasoning_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=900,
                temperature=0.0
            )
            if isinstance(resp, dict):
                ch = resp.get("choices") or resp.get("outputs")
                if ch:
                    msg = ch[0].get("message") or ch[0]
                    return msg.get("content") if isinstance(msg, dict) else str(msg)
            return str(resp)
        except Exception as e:
            print(f"[ImageAnalyzer] LLM error: {e}")
            return ""

    def _try_parse_json(self, text: str):
        if not text:
            return None
        cleaned = re.sub(r'```(?:json)?', '', text)
        cleaned = cleaned.replace("```", "")
        try:
            return json.loads(cleaned)
        except:
            return None


    def _fallback(self):
        return {
            "visual_strengths": ["Невозможно выполнить анализ"],
            "visual_weaknesses": ["Технический сбой"],
            "recommendations": ["Попробуйте позже"],
            "design_style": "неопределён",
            "visual_quality_score": 5,
            "final_verdict": "Fallback"
        }


image_analyzer = ImageAnalyzer()
