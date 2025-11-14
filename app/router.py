from fastapi import APIRouter, UploadFile, File, HTTPException
from utils import pdf_reader
from utils.text_analyzer import text_analyzer
from utils.image_analyzer import image_analyzer
import os
from typing import Dict, Any, List
import asyncio

router = APIRouter(prefix='/api', tags=['Analyze Presentations'])


@router.on_event("startup")
async def startup_event():
    """Запускаем инициализацию всех моделей"""
    print("Запускаем инициализацию моделей в фоне...")

    # Запускаем инициализацию обоих анализаторов параллельно
    await asyncio.gather(
        text_analyzer.initialize_models(),
        image_analyzer.initialize_models()
    )

    print("Все модели инициализированы")


@router.get('/')
async def info():
    return {
        'message': 'PRAIReader Analysis API',
        'text_model_ready': text_analyzer.models_initialized,
        'image_model_ready': image_analyzer.models_initialized
    }


@router.get('/health')
async def health_check():
    return {
        'status': 'healthy',
        'text_model_ready': text_analyzer.models_initialized,
        'image_model_ready': image_analyzer.models_initialized,
        'service': 'PRAIReader'
    }


@router.post('/analyze')
async def analyze_presentation(file: UploadFile = File(...)):
    """Анализ презентации"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        print(f"Анализ файла: {file.filename}")
        print(f"Текстовая модель: {text_analyzer.models_initialized}")
        print(f"Image модель: {image_analyzer.models_initialized}")

        # Обрабатываем PDF
        pdf_path = pdf_reader.save_temp_pdf(file)
        slides_text = pdf_reader.extract_text_by_slides(pdf_path)
        slides_images = pdf_reader.pdf_to_images(pdf_path)

        print(f"Найдено слайдов: {len(slides_text)}")

        # Анализируем каждый слайд
        slides_analysis = []
        for i, slide_data in enumerate(slides_text):
            slide_image = slides_images[i] if i < len(slides_images) else None

            # Анализ текста
            text_analysis = text_analyzer.analyze_text(slide_data['text'])

            # Анализ изображения
            visual_analysis = image_analyzer.analyze_image(slide_image) if slide_image else {}

            # Общая оценка
            overall_score = _calculate_overall_score(text_analysis, visual_analysis)

            slides_analysis.append({
                "slide_number": slide_data['slide_number'],
                "word_count": slide_data['word_count'],
                "analysis": {
                    "text_analysis": text_analysis,
                    "visual_analysis": visual_analysis,
                    "overall_score": overall_score
                }
            })

        # Генерируем итоговый отчет
        summary_report = _generate_summary_report(slides_analysis)

        # Очищаем временный файл
        os.unlink(pdf_path)

        return {
            'filename': file.filename,
            'total_slides': len(slides_text),
            'text_model_used': text_analyzer.models_initialized,
            'image_model_used': image_analyzer.models_initialized,
            'slides_analysis': slides_analysis,
            'summary_report': summary_report
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


def _calculate_overall_score(text_analysis: Dict, visual_analysis: Dict) -> float:
    """Расчет общей оценки слайда"""
    text_score = text_analysis.get('clarity_score', 5)
    visual_score = visual_analysis.get('visual_score', 5)
    return round((text_score + visual_score) / 2, 1)


def _generate_summary_report(slides_analysis: List[Dict]) -> Dict[str, Any]:
    """Генерация итогового отчета"""
    if not slides_analysis:
        return _get_empty_summary()

    try:
        total_slides = len(slides_analysis)
        total_score = sum(slide.get('analysis', {}).get('overall_score', 5) for slide in slides_analysis)
        avg_score = total_score / total_slides

        # Собираем рекомендации и проблемы
        all_recommendations = []
        all_problems = []

        for slide in slides_analysis:
            analysis = slide.get('analysis', {})
            text_analysis = analysis.get('text_analysis', {})

            all_recommendations.extend(text_analysis.get('specific_recommendations', []))
            all_problems.extend(text_analysis.get('problems_detected', []))

        # Уникальные элементы
        unique_recommendations = list(set([r for r in all_recommendations if len(r) > 5]))[:3]
        unique_problems = list(set([p for p in all_problems if len(p) > 5]))[:3]

        return {
            "presentation_score": round(avg_score, 1),
            "total_slides_analyzed": total_slides,
            "key_strengths": _extract_strengths(avg_score),
            "critical_issues": unique_problems if unique_problems else ["Серьезные проблемы не выявлены"],
            "priority_recommendations": unique_recommendations if unique_recommendations else [
                "Презентация в хорошем состоянии"],
            "target_audience": _determine_audience(avg_score),
            "overall_verdict": _get_verdict(avg_score)
        }

    except Exception as e:
        print(f"Ошибка генерации отчета: {e}")
        return _get_empty_summary()


def _extract_strengths(avg_score: float) -> List[str]:
    if avg_score >= 7:
        return ["Хорошая структура", "Понятное изложение"]
    elif avg_score >= 5:
        return ["Информативная подача", "Логичное построение"]
    else:
        return ["Потенциал для развития"]


def _determine_audience(avg_score: float) -> str:
    if avg_score >= 8:
        return "Широкая аудитория"
    elif avg_score >= 6:
        return "Общая аудитория"
    else:
        return "Требуется адаптация"


def _get_verdict(avg_score: float) -> str:
    if avg_score >= 8:
        return "Отличная презентация"
    elif avg_score >= 6:
        return "Хорошая основа"
    elif avg_score >= 4:
        return "Требует доработки"
    else:
        return "Необходима переработка"


def _get_empty_summary() -> Dict[str, Any]:
    return {
        "presentation_score": 0,
        "total_slides_analyzed": 0,
        "key_strengths": ["Данные отсутствуют"],
        "critical_issues": ["Анализ не выполнен"],
        "priority_recommendations": ["Загрузите презентацию"],
        "target_audience": "Не определена",
        "overall_verdict": "Анализ не выполнен"
    }