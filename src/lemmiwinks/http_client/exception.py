class HTTPClientError(Exception):
    pass


class HTTPClientConnectionFailed(HTTPClientError):
    pass


class PoolError(HTTPClientError):
    pass
