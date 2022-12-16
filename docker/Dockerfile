FROM openjdk:8-jdk

# Installing Netlogo

ARG MODEL_NAME=v2.11.0.nlogo
ARG NETLOGO_VERSION=5.3.1
ARG NETLOGO_NAME=NetLogo-$NETLOGO_VERSION
ARG NETLOGO_URL=https://ccl.northwestern.edu/netlogo/$NETLOGO_VERSION/$NETLOGO_NAME-64.tgz

ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    DISPLAY=:14

RUN mkdir /home/netlogo \
    && wget $NETLOGO_URL \
    && tar xzf $NETLOGO_NAME-64.tgz -C /home/netlogo --strip-components=1 \
    && rm $NETLOGO_NAME-64.tgz \
    && apt-get update && apt-get install -y libxrender1 libxtst6

COPY . /home/

# Installing Anaconda

# Install base utilities
RUN apt-get update \
    && apt-get install -y build-essential \
    && apt-get install -y wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install miniconda
ENV CONDA_DIR /opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda2-py27_4.8.3-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda

# Put conda in path so we can use conda activate
ENV PATH=$CONDA_DIR/bin:$PATH

# Creating the conda environment
RUN conda env create -f /home/python/environment.yml


