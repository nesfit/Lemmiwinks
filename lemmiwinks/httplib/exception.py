class HTTPClientError(Exception):
    pass


class HTTPClientConnectionFailed(HTTPClientError):
    pass


class PoolError(HTTPClientError):
    pass


class URLResolverError(HTTPClientError):
    pass


class UrlValidationError(URLResolverError):
    pass
