 FROM ubuntu:xenial

# install required packages
RUN apt-get clean
RUN apt-get update \
    && apt-get install -y  git \
    python-setuptools \
    python-dev \
    python-pip \
    vim


RUN pip install ryu

COPY learning_switch.py .

EXPOSE 6633

CMD ryu-manager --verbose learning_switch.py
