FROM ubuntu:18.04
MAINTAINER dsp_qa
RUN apt-get update -y
RUN apt-get install -y python2.7
RUN apt-get install -y python-pip python-dev build-essential
RUN apt-get install -y git
RUN pip install nose
RUN pip install behave
RUN pip install pymongo
RUN pip install requests
RUN pip install PyHamcrest
RUN pip install protobuf
RUN pip install lxml
RUN mkdir -p /data
RUN mkdir -p /root/.ssh
ADD ./id_rsa /root/.ssh/
ADD ./known_hosts /root/.ssh/
RUN chmod 600 /root/.ssh/id_rsa
RUN chmod 644 /root/.ssh/known_hosts
WORKDIR /data
RUN git clone git@gitlab.mobvista.com:mvbjqa/dsp_autocase.git
WORKDIR /data/dsp_autocase/utils
CMD ["python","update_campaign.py"]
