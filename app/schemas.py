from pydantic import BaseModel
from typing import List, Optional, Dict


class AddDocumentsRequest(BaseModel):
    documents : List[str]
    ids : Optional[List[int]] = None
