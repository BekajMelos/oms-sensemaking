from typing import List

from .base_observable import BaseObservable, StatusCriteria


class SearchObservable(BaseObservable):
    criteria: List[StatusCriteria]

    def update_data(self):
        """Update data for search observable."""
        # TODO: implement search query
        pass
