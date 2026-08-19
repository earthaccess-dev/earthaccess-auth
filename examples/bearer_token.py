# /// script
# requires-python = ">=3.11"
# dependencies = ["earthaccess-auth"]
# ///
"""Get a raw EDL bearer token.

The minimal case: no fsspec, no obstore, just the token string. This is the
pattern a Lambda-deployed consumer with a tight dependency budget would use.
"""

import earthaccess_auth

auth = earthaccess_auth.login(strategy="environment")
token = auth.token["access_token"]
print(token)
