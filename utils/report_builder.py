from typing import Dict, Any, List
from datetime import datetime


class ReportBuilder:
    @staticmethod
    def build_presentation_report(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Построение финального отчета по презентации"""

        return {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_slides": analysis_results.get('total_slides', 0),
                "filename": analysis_results.get('filename', '')
            },
            "summary": analysis_results.get('summary_report', {}),
            "slides_analysis": analysis_results.get('slides_analysis', []),
            "statistics": ReportBuilder._calculate_statistics(analysis_results)
        }

    @staticmethod
    def _calculate_statistics(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Расчет статистики по презентации"""
        slides_analysis = analysis_results.get('slides_analysis', [])

        if not slides_analysis:
            return {}

        total_slides = len(slides_analysis)
        avg_score = sum(
            slide.get('analysis', {}).get('overall_score', 0)
            for slide in slides_analysis
        ) / total_slides

        return {
            "average_score": round(avg_score, 1),
            "total_words": analysis_results.get('total_words', 0),
            "words_per_slide": round(analysis_results.get('total_words', 0) / total_slides, 1),
            "quality_assessment": ReportBuilder._assess_quality(avg_score)
        }

    @staticmethod
    def _assess_quality(score: float) -> str:
        """Оценка общего качества"""
        if score >= 8:
            return "отличное"
        elif score >= 6:
            return "хорошее"
        elif score >= 4:
            return "удовлетворительное"
        else:
            return "требует улучшений"