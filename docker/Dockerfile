FROM apache/airflow:2.5.0-python3.10
MAINTAINER "kyoonlee@tidesquare.com"

USER root
RUN apt update \
    && apt-get install -y openjdk-11-jdk libgomp1

ENV JAVA_HOME /usr/lib/jvm/java-11-openjdk-amd64
ENV PATH "${PATH}:${JAVA_HOME}/bin"

RUN ln -snf /usr/share/zoneinfo/Asia/Seoul /etc/localtime \
    && echo Asia/Seoul > /etc/timezone

USER airflow
COPY ./requirements_local.txt /requirements.txt
RUN if [ -e "/requirements.txt" ]; then pip install --no-cache-dir -r /requirements.txt; fi
