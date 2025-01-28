from typing import List

import httpx

from oms_sensemaking.config import SETTINGS


class AacClient:
    def get_acm_rollup(self, acms: List[dict]) -> dict:
        """Use AAC to rollup a list of ACMs"""
        response = httpx.post(f"{SETTINGS.aac_url}/acms/rollup", json={"AccessTuples": acms})
        return response.json()["RollupACM"]
