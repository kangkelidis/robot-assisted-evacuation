FROM openjdk:8-jdk

# Installing Netlogo

ARG NETLOGO_VERSION=5.3.1
ARG NETLOGO_NAME=NetLogo-$NETLOGO_VERSION
ARG NETLOGO_URL=https://ccl.northwestern.edu/netlogo/$NETLOGO_VERSION/$NETLOGO_NAME-64.tgz

ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    DISPLAY=:14

RUN mkdir -p /home/netlogo_installation
RUN wget $NETLOGO_URL \
    && tar xzf $NETLOGO_NAME-64.tgz -C /home/netlogo_installation --strip-components=1 \
    && rm $NETLOGO_NAME-64.tgz \
    && apt-get update && apt-get install -y libxrender1 libxtst6

# Install base utilities
RUN apt-get update \
    && apt-get install -y build-essential \
    libtool \
    && apt-get install -y wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install miniconda
ENV CONDA_DIR /opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda

# Put conda in path so we can use conda activate
ENV PATH=$CONDA_DIR/bin:$PATH

# Copy only environment.yml
COPY ./env/environment.yml /home/env/environment.yml

# Creating the conda environment
RUN conda env create -f /home/env/environment.yml

COPY . /home/

# Unsetting to avoid a Netlogo error.
ENV DISPLAY=

# Executing evacuation simulations
WORKDIR "/home/workspace"

# entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
