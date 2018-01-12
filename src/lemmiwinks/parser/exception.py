class ParserError(Exception):
    pass


class CSSParseError(ParserError):
    pass


class HTMLParseError(ParserError):
    pass


class TagDoesNotExists(HTMLParseError):
    pass
