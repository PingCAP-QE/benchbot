FROM python:3.8-buster
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.19.0/bin/linux/amd64/kubectl
RUN chmod +x ./kubectl
RUN mv ./kubectl /usr/local/bin/kubectl

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /src

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install -e .

#COPY --from=mahjonp/go-ycsb /go-ycsb /bin/go-ycsb
COPY bin/naglfar /bin/naglfar

CMD ["tail", "-f", "/dev/null"]