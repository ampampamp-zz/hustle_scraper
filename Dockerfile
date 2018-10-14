FROM python:3

RUN pip install -U pip

RUN mkdir -p /opt/code
WORKDIR /opt/code

ADD ./requirements.txt /opt/code/requirements.txt
RUN pip install -r requirements.txt

ADD . /opt/code

ENV PYTHONPATH $PYTHONPATH:/opt/code/

CMD ["bash"]
