from typing import List

from oms_sensemaking.iw.sensemakers.base_observable import BaseObservable, StatusCriteria


class StatusObservable(BaseObservable):
    statuses: List[StatusCriteria]

    def update_data(self):
        """Update data for status observable."""
        # TODO: implement status query
        pass
