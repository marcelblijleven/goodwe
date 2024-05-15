class InverterError(Exception):
    """Indicates error communicating with inverter"""


class RequestFailedException(InverterError):
    """
    Indicates request sent to inverter has failed and did not yield in valid response,
    even after several retries.

    Attributes:
        message -- explanation of the error
        consecutive_failures_count -- number requests failed in a consecutive streak
    """

    def __init__(self, message: str = '', consecutive_failures_count: int = 0):
        self.message: str = message
        self.consecutive_failures_count: int = consecutive_failures_count


class RequestRejectedException(InverterError):
    """
    Indicates request sent to inverter was rejected and protocol exception response was received.

    Attributes:
        message -- rejection reason
    """

    def __init__(self, message: str = ''):
        self.message: str = message


class PartialResponseException(InverterError):
    """
    Indicates the received response data are incomplete and is probably fragmented to multiple packets.

    Attributes:
        length -- received data length
        expected -- expected data lenght
    """

    def __init__(self, lenght: int, expected: int):
        self.length: int = lenght
        self.expected: int = expected


class MaxRetriesException(InverterError):
    """Indicates the maximum number of retries has been reached"""
