from dataclasses import dataclass

from antarest.matrixstore.service import MatrixService
from antarest.storage.business.common.uri_resolver_service import (
    UriResolverService,
)


@dataclass
class ContextServer:
    matrix: MatrixService
    resolver: UriResolverService
