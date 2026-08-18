# /// script
# requires-python = ">=3.11"
# dependencies = ["earthaccess-auth"]
#
# [tool.uv.sources]
# # TODO: switch to a released earthaccess-auth once this branch merges
# earthaccess-auth = { git = "https://github.com/maxrjones/earthaccess", subdirectory = "earthaccess-auth", branch = "poc/earthaccess-auth" }
# ///
"""Get temporary AWS S3 credentials for a DAAC.

For anything that wants key/secret/token directly: boto3, s3fs, or the AWS
CLI. Credentials are scoped to that DAAC's cloud bucket(s) and expire in
about an hour.
"""

import earthaccess_auth

auth = earthaccess_auth.login()
creds = auth.get_s3_credentials(daac="NSIDC")
print(creds)  # accessKeyId, secretAccessKey, sessionToken, expiration
