FROM alpine:3.6

RUN apk update
RUN apk add python2 python2-dev py-pip gcc linux-headers musl-dev libffi-dev openssl-dev make
WORKDIR /home
COPY . .
RUN pip install -r requirements.txt

CMD ["python", "chomps/chomps.py"]
