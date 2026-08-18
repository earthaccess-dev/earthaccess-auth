# /// script
# requires-python = ">=3.11"
# dependencies = ["earthaccess-auth[obstore]"]
#
# [tool.uv.sources]
# # TODO: switch to a released earthaccess-auth once this branch merges
# earthaccess-auth = { git = "https://github.com/maxrjones/earthaccess", subdirectory = "earthaccess-auth", branch = "poc/earthaccess-auth" }
# ///
"""Build a headers dict for HTTP-based stores fronting EDL-protected data.

Works for obstore HTTP stores and icechunk's http_store(headers=...) for
virtual chunk containers.
"""

import earthaccess_auth
from earthaccess_auth.adapters.obstore import http_client_options

auth = earthaccess_auth.login()
options = http_client_options(auth)
print(options)  # default_headers: {"authorization": "Bearer <token>"}
