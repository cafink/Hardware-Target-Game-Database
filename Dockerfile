# This creates an environment with the optional archive formats (7z and rar) and
# the test tools already installed. The image holds dependencies only; mount the
# repo when running it.

FROM python:3-alpine

# rar extraction needs an external utility. Alpine packages unrar-free only in
# its edge/testing repository, so take just that package from there.
RUN apk add --no-cache \
    --repository=https://dl-cdn.alpinelinux.org/alpine/edge/testing unrar-free

WORKDIR /usr/src/app
COPY requirements-archives.txt requirements-dev.txt ./
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements-dev.txt
