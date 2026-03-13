FROM python:3.12-slim-bookworm

# Install system utilities and Git
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    git \
    openssh-client \
    curl \
    ca-certificates \
    tar \
    gzip \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root devuser matching the host UID/GID
ARG USER_UID=1000
ARG USER_GID=1000
RUN groupadd --gid $USER_GID devuser \
    && useradd --uid $USER_UID --gid $USER_GID -m -s /bin/bash devuser \
    && mkdir -p /workspace \
    && chown -R $USER_UID:$USER_GID /workspace

# Install uv for Python dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install Spec Framework CLI (Requires Node for npm packages if Speckit/OpenSpec is used)
RUN apt-get update && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs && npm install -g speckit

# Copy init script
COPY init-workspace.sh /usr/local/bin/init-workspace.sh
RUN chmod +x /usr/local/bin/init-workspace.sh

# Set the default user
USER devuser
