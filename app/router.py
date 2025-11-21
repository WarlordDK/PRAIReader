from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status

from app.schemas import AddDocumentsRequest
from utils import pdf_reader
from utils.all_text_analyzer import AllTextAnalyzer
from utils.content_analyzer import content_analyzer
from utils.image_analyzer import image_analyzer
from utils.rag_analyzer import rag_analyzer
from core.config import get_model_list
import os
import asyncio

router = APIRouter(prefix="/api", tags=["Analyze Presentations"])


@router.on_event("startup")
async def startup_event():
    await asyncio.gather(
        content_analyzer.initialize_models(),
        image_analyzer.initialize_models(),
    )

    rag_analyzer.initialize()


def _filter_slides_by_flags(slides_text, first_slide: bool, last_slide: bool):
    """
    slides_text: list of dicts {'slide_number': int, 'text': str, ...}
    Возвращает (included_slides, excluded_slide_numbers)
    included_slides — список словарей, которые попадут в анализ (в том же формате),
    excluded_slide_numbers — список номеров исключённых слайдов.
    """
    if not slides_text:
        return [], []

    first_num = slides_text[0]['slide_number']
    last_num = slides_text[-1]['slide_number']

    excluded = set()
    if not first_slide:
        excluded.add(first_num)
    if not last_slide:
        excluded.add(last_num)

    included = [s for s in slides_text if s['slide_number'] not in excluded]
    return included, sorted(list(excluded))

@router.get('/models')
async def get_all_models():
    return get_model_list()

@router.get('/model/{model_id}')
async def get_model(model_id : int, models = Depends(get_all_models)):
    for model in models:
        if model.get('id') == model_id : return model
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Указанной модели не существует")

@router.post("/analyze/structure")
async def analyze_presentation(
    file: UploadFile = File(...),
    model_id : int = 1,
    use_rag: bool = False,
    user_context: str = "",
    first_slide: bool = True,
    last_slide: bool = True,
    max_tokens : int = 2000,
    temperature : float = 0.0,
    models = Depends(get_all_models)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    model_name = None
    for model in models:
        if model.get('id') == model_id : model_name = model.get('model_name')
    if not model_name:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Модель не найдена')

    try:
        pdf_path = pdf_reader.save_temp_pdf(file)
        slides_text = pdf_reader.extract_text_by_slides(pdf_path)

        included_slides, excluded_slide_numbers = _filter_slides_by_flags(slides_text, first_slide, last_slide)

        full_text_blocks = []
        for slide in included_slides:
            idx = slide.get("slide_number", "?")
            text = slide.get("text", "").strip()
            full_text_blocks.append(f"--- SLIDE {idx} ---\n{text}")

        full_text = "\n\n".join(full_text_blocks)
        rag_output = "rag-система не использовалась"

        if use_rag and user_context:
            relevant_docs = rag_analyzer.query(user_context, top_k=3)
            context_text = "\n".join([d["text"] for d in relevant_docs])
            prompt_with_context = f"{context_text}\n\n{full_text}"
            rag_output = rag_analyzer.query(prompt_with_context)
        else:
            prompt_with_context = full_text

        all_text_analyzer = AllTextAnalyzer(model_name=model_name, max_tokens=max_tokens, temperature=temperature)
        await all_text_analyzer.initialize_models()
        result = all_text_analyzer.analyze_full_text(prompt_with_context)

        os.unlink(pdf_path)

        return {
            "filename": file.filename,
            "total_slides": len(slides_text),
            "excluded_slides": excluded_slide_numbers,
            "summary_report": result,
            "rag_info": rag_output
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze/content")
async def analyze_content(
    file: UploadFile = File(...),
    first_slide: bool = True,
    last_slide: bool = True
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        pdf_path = pdf_reader.save_temp_pdf(file)
        slides_text = pdf_reader.extract_text_by_slides(pdf_path)

        included_slides, excluded_slide_numbers = _filter_slides_by_flags(slides_text, first_slide, last_slide)

        full_text_blocks = []
        for slide in included_slides:
            idx = slide.get("slide_number", "?")
            text = slide.get("text", "").strip()
            full_text_blocks.append(f"--- SLIDE {idx} ---\n{text}")

        full_text = "\n\n".join(full_text_blocks)

        analysis = content_analyzer.analyze_full_content(full_text)

        os.unlink(pdf_path)

        return {
            "filename": file.filename,
            "total_slides": len(slides_text),
            "excluded_slides": excluded_slide_numbers,
            "content_analysis": analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content analysis failed: {e}")

@router.post("/analyze/visual")
async def analyze_visual(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        pdf_path = pdf_reader.save_temp_pdf(file)

        slide_images = pdf_reader.pdf_to_images(pdf_path)


        result = await image_analyzer.analyze_visual_presentation(slide_images)

        os.unlink(pdf_path)

        return {
            "filename": file.filename,
            "total_slides": len(slide_images),
            "visual_report": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add")
def add_documents_to_rag(data: AddDocumentsRequest):
    """
    Добавление новых документов в коллекцию RAG (Qdrant).
    """
    try:
        if not rag_analyzer.initialized:
            rag_analyzer.initialize()

        rag_analyzer.add_documents(
            docs=data.documents,
            ids=data.ids
        )

        return {
            "status": "success",
            "added": len(data.documents)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))