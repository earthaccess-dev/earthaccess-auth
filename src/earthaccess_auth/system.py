"""Earthdata systems: production (`PROD`) and user acceptance testing (`UAT`)."""

from dataclasses import dataclass
from typing import NewType

CMRBaseURL = NewType("CMRBaseURL", str)
EDLHostname = NewType("EDLHostname", str)
StatusURL = NewType("StatusURL", str)
StatusApiURL = NewType("StatusApiURL", str)


@dataclass(frozen=True)
class System:
    """Host URL options, for different Earthdata domains."""

    cmr_base_url: CMRBaseURL
    status_url: StatusURL
    status_api_url: StatusApiURL
    edl_hostname: EDLHostname


PROD = System(
    CMRBaseURL("https://cmr.earthdata.nasa.gov/search/"),
    StatusURL("https://status.earthdata.nasa.gov/"),
    StatusApiURL("https://status.earthdata.nasa.gov/api/v1/statuses"),
    EDLHostname("urs.earthdata.nasa.gov"),
)
"""NASA's production Earthdata system. The default for `login(system=...)`."""

UAT = System(
    CMRBaseURL("https://cmr.uat.earthdata.nasa.gov/search/"),
    StatusURL("https://status.uat.earthdata.nasa.gov/"),
    StatusApiURL("https://status.uat.earthdata.nasa.gov/api/v1/statuses"),
    EDLHostname("uat.urs.earthdata.nasa.gov"),
)
"""NASA's user acceptance testing (UAT) Earthdata system, for pre-release testing."""
