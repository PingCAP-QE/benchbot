FROM python:3.8-alpine
RUN apk update
RUN echo "http://dl-8.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories
RUN apk --no-cache --update-cache add gcc gfortran build-base wget freetype-dev libpng-dev openblas-dev
RUN ln -s /usr/include/locale.h /usr/include/xlocale.h

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /src

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install -e .

COPY --from=mahjonp/go-ycsb /go-ycsb /bin/go-ycsb

CMD ["tail", "-f", "/dev/null"]