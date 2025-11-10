from fastapi import APIRouter

router = APIRouter(prefix='/analyze', tags=['Analyze Presentations'])

@router.get('/')
async def info():
    return {'message' : 'analyze router'}
