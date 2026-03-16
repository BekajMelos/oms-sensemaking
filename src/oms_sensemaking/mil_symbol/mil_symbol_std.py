"""Module for base mil symbol classes"""

import uuid
from abc import ABC, abstractmethod
from queue import PriorityQueue
from typing import Dict, List, Tuple

from oms_sensemaking.clients.instances import aac_client


class MilSymbol(ABC):
    """Base Class for Mil Symbols"""

    def __init__(self, code: str, settings: Dict) -> None:
        self.code = code.upper()
        self.settings = settings
        self.acms: List[Dict] = []

        # priority queue prioritize sources in order: affiliation, status, context
        self.source_ids: PriorityQueue[Tuple[int, uuid.UUID]] = PriorityQueue()

    @property
    @abstractmethod
    def formatted_code(self) -> str: ...

    def get_acm(self) -> Dict:
        """Rollup the acm from the attributes"""
        return aac_client.get_acm_rollup([{"ACM": acm} for acm in self.acms])

    def update_code(self, index: int, value: str) -> str:
        """Update string "in place"

        :param index: index of code character to update
        :param value: value to update at index
        :return: the new code
        """
        symbol_code = list(self.code)
        symbol_code[index] = value
        self.code = "".join(symbol_code)
        return self.code
