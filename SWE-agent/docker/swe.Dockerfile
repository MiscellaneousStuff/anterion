FROM ubuntu:jammy

# Install necessary dependencies for adding NodeSource repository
RUN apt-get update && apt-get install -y curl software-properties-common

# Add the NodeSource PPA to get the latest Node.js and npm versions
RUN curl -fsSL https://deb.nodesource.com/setup_current.x | bash -

# Install Node.js and npm
RUN apt-get update && apt-get install -y nodejs

# Check versions
RUN node -v
RUN npm -v

# Install netlify-cli global
RUN npm install netlify-cli -g

ARG MINICONDA_URL

# Install third party tools
RUN apt-get update && \
    apt-get install -y bash gcc git jq wget g++ make && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Initialize git
RUN git config --global user.email "sweagent@pnlp.org"
RUN git config --global user.name "sweagent"

# Environment variables
ENV ROOT='/dev/'
RUN prompt() { echo " > "; };
ENV PS1="> "

# Create file for tracking edits, test patch
RUN touch /root/files_to_edit.txt
RUN touch /root/test.patch

# add ls file indicator
RUN echo "alias ls='ls -F'" >> /root/.bashrc

# Install miniconda
ENV PATH="/root/miniconda3/bin:${PATH}"
ARG PATH="/root/miniconda3/bin:${PATH}"
RUN wget ${MINICONDA_URL} -O miniconda.sh \
    && mkdir /root/.conda \
    && bash miniconda.sh -b \
    && rm -f miniconda.sh
RUN conda --version \
    && conda init bash \
    && conda config --append channels conda-forge

# Install python packages
COPY docker/requirements.txt /root/requirements.txt
RUN pip install -r /root/requirements.txt

WORKDIR /

CMD ["/bin/bash"]