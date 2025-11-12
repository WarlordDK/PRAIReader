from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from utils import pdf_reader, report_builder
from utils.analysis import analyzer
import os
from typing import Dict, Any
import asyncio

router = APIRouter(prefix='/api', tags=['Analyze Presentations'])


@router.on_event("startup")
async def startup_event():
    """Запускаем инициализацию моделей при старте приложения"""
    print(" Запускаем инициализацию ML моделей в фоне...")
    asyncio.create_task(analyzer.initialize_models())


@router.get('/')
async def info():
    return {
        'message': 'PRAIReader Analysis API',
        'ml_models_ready': analyzer.models_initialized
    }


@router.get('/health')
async def health_check():
    """Проверка статуса ML моделей"""
    return {
        'status': 'healthy',
        'ml_models_initialized': analyzer.models_initialized,
        'service': 'PRAIReader'
    }


@router.post('/analyze')
async def analyze_presentation(file: UploadFile = File(...)):
    """Анализ презентации"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        print(f" Анализ файла: {file.filename}")
        print(f" ML модели готовы: {analyzer.models_initialized}")

        pdf_path = pdf_reader.save_temp_pdf(file)
        slides_text = pdf_reader.extract_text_by_slides(pdf_path)
        slides_images = pdf_reader.pdf_to_images(pdf_path)

        print(f" Слайдов: {len(slides_text)}")

        slides_analysis = []
        for i, slide_data in enumerate(slides_text):
            slide_image = slides_images[i] if i < len(slides_images) else None

            analysis_result = analyzer.analyze_slide_content(
                text=slide_data['text'],
                image=slide_image
            )

            slides_analysis.append({
                "slide_number": slide_data['slide_number'],
                "word_count": slide_data['word_count'],
                "analysis": analysis_result
            })

        summary_report = analyzer.generate_summary_report(slides_analysis)

        os.unlink(pdf_path)

        return {
            'filename': file.filename,
            'total_slides': len(slides_text),
            'ml_models_used': analyzer.models_initialized,
            'slides_analysis': slides_analysis,
            'summary_report': summary_report
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")