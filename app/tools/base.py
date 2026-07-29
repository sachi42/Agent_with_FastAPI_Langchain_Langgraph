import abc
from typing import List, Dict, Any

class VectorStoreInterface(abc.ABC):
    @abc.abstractmethod
    def add_documents(self, documents: List[str]) -> None: pass
    @abc.abstractmethod
    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]: pass
