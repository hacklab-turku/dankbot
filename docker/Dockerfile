# To build the image, run `docker build` command from the root of the
# repository:
#
#    docker build -f docker/Dockerfile .
#
# There is an optional PYTHON_VERSION build argument which sets the
# version of python to build against. For example:
#
#    docker build -f docker/Dockerfile --build-arg PYTHON_VERSION=3.8 .
#
# An optional LIBOLM_VERSION build argument which sets the
# version of libolm to build against. For example:
#
#    docker build -f docker/Dockerfile --build-arg LIBOLM_VERSION=3.1.4 .
#


##
## Creating a builder container
##

# We use an initial docker container to build all of the runtime dependencies,
# then transfer those dependencies to the container we're going to ship,
# before throwing this one away
ARG PYTHON_VERSION=3.8
FROM docker.io/python:${PYTHON_VERSION}-alpine3.11 as builder

##
## Build libolm for matrix-nio e2e support
##

# Install libolm build dependencies
ARG LIBOLM_VERSION=3.1.4
RUN apk add --no-cache \
    make \
    cmake \
    gcc \
    g++ \
    git \
    libffi-dev \
    yaml-dev \
    python3-dev

# Build libolm
#
# Also build the libolm python bindings and place them at /python-libs
# We will later copy contents from both of these folders to the runtime
# container
COPY docker/build_and_install_libolm.sh /scripts/
RUN /scripts/build_and_install_libolm.sh ${LIBOLM_VERSION} /python-libs

# Install Postgres dependencies
RUN apk add --no-cache \
    musl-dev \
    libpq \
    postgresql-dev

# Install python runtime modules. We do this before copying the source code
# such that these dependencies can be cached
# This speeds up subsequent image builds when the source code is changed
RUN mkdir -p /src/dankbot
COPY dankbot/__init__.py /src/dankbot/
COPY README.md dankbot /src/

# Build the dependencies
COPY setup.py /src/setup.py
RUN pip install --prefix="/python-libs" --no-warn-script-location "/src/.[postgres]"

# Now copy the source code
COPY *.py *.md /src/
COPY dankbot/*.py /src/dankbot/

# And build the final module
RUN pip install --prefix="/python-libs" --no-warn-script-location "/src/.[postgres]"

##
## Creating the runtime container
##

# Create the container we'll actually ship. We need to copy libolm and any
# python dependencies that we built above to this container
FROM docker.io/python:${PYTHON_VERSION}-alpine3.11

# Copy python dependencies from the "builder" container
COPY --from=builder /python-libs /usr/local

# Copy libolm from the "builder" container
COPY --from=builder /usr/local/lib/libolm* /usr/local/lib/

# Install any native runtime dependencies
RUN apk add --no-cache \
    libstdc++ \
    libpq \
    postgresql-dev

# Specify a volume that holds the config file, SQLite3 database,
# and the matrix-nio store
VOLUME ["/data"]

# Start the bot
ENTRYPOINT ["dankbot", "/data/config.yaml"]
