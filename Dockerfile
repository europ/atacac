FROM fedora:32

RUN dnf install -y --setopt=tsflags=nodocs python3 python3-pip git \
    && dnf clean all

COPY . /app
RUN pip3 install /app

RUN mkdir /workdir
VOLUME /workdir
WORKDIR /workdir

ENTRYPOINT ["atacac"]
