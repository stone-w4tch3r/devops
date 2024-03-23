from enum import auto, Enum
from urllib.parse import urlparse, ParseResult

APT_UPDATE_CACHE_TIME: int = 86400  # 24 hours


class OS(Enum):
    win = auto()
    ubuntu = auto()
    debian = auto()
    osx = auto()
    fedora = auto()


class URL:
    _parsed_url: ParseResult
    _url_str: str

    def __init__(self, url):
        result = urlparse(url)
        if all([result.scheme, result.netloc, result.path]) and result.scheme in ['http', 'https']:
            self._parsed_url = result
            self._url_str = url
        else:
            raise ValueError(f"Invalid URL [{url}]")

    @property
    def parsed(self) -> ParseResult:
        return self._parsed_url

    @property
    def url_str(self) -> str:
        return self._url_str
