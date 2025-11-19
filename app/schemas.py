from pydantic import BaseModel
from typing import List, Optional

class AddDocumentsRequest(BaseModel):
    documents : List[str]
    ids : Optional[List[int]] = None