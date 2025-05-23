# This links to tmccombs/hcl2json:0.6 -- published ~March 2025
# https://hub.docker.com/layers/tmccombs/hcl2json/0.6/images/sha256-312ac54d3418b87b2ad64f82027483cb8b7750db6458b7b9ebe42ec278696e96
#
# NOTE: We do not intend/expect to make any modifications to this asset. 
#       Dockerfile exists in repo for 1st-time push and documentation purposes.
FROM tmccombs/hcl2json@sha256:312ac54d3418b87b2ad64f82027483cb8b7750db6458b7b9ebe42ec278696e96

LABEL maintainer="graham.wright@seqera.io,sushma.chaluvadi@seqera.io"
LABEL version="1.0"
LABEL org.opencontainers.image.source="https://github.com/seqeralabs/cx-field-tools-installer"

# Build Command:
# docker build -t ghcr.io/seqeralabs/cx-field-tools-installer/hcl2json:vendored .
