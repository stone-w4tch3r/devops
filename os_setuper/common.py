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
    parsed_url: ParseResult
    url_str: str

    def __init__(self, url):
        result = urlparse(url)
        if all([result.scheme, result.netloc, result.path]) and result.scheme in ['http', 'https']:
            self.parsed_url = result
            self.url_str = url
        else:
            raise ValueError(f"Invalid URL [{url}]")

    @property
    def parsed(self) -> ParseResult:
        return self.parsed_url

    @property
    def str(self) -> str:
        return self.url_str
