"""Module for sensemaking exceptions"""


class SensemakingError(Exception):
    """Sensemaking Exception"""


class TrackLengthError(SensemakingError):
    """
    Tracks must have at least two points
    """


class MilSymbolInvalidIdCharError(SensemakingError):
    """
    All characters within a MylSymbol Id must be valid
    """
