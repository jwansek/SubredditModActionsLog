FROM ubuntu:latest
MAINTAINER Eden Attenborough "eddie.atten.ea29@gmail.com"
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y
RUN apt-get install -y tzdata python3-pip python-dev build-essential pkg-config 
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3"]
CMD ["runprog.py"]
