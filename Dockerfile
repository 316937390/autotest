FROM ubuntu:18.04
MAINTAINER dsp_qa
RUN apt-get update -y
RUN apt-get install -y python2.7
RUN apt-get install -y python-pip python-dev build-essential
RUN apt-get install -y git
RUN apt-get install -y openssh-server
#RUN apt-get install init
RUN pip install nose
RUN pip install behave
RUN pip install pymongo
RUN pip install requests
RUN pip install PyHamcrest
RUN pip install protobuf
RUN pip install lxml
RUN pip install pytest-xdist
RUN mkdir -p /data/
RUN mkdir -p /run/sshd
RUN echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
RUN echo "RSAAuthentication yes" >> /etc/ssh/sshd_config
RUN echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config
RUN echo "AuthorizedKeysFile .ssh/authorized_keys" >> /etc/ssh/sshd_config
ADD ./authorized_keys /root/.ssh/
ADD ./known_hosts /root/.ssh/
ADD ./id_rsa /root/.ssh/
RUN chmod 600 /root/.ssh/authorized_keys
RUN chmod 644 /root/.ssh/known_hosts
RUN chmod 600 /root/.ssh/id_rsa
RUN sed -i 's/UsePAM yes/UsePAM no/g' /etc/ssh/sshd_config
EXPOSE 22
CMD ["/usr/sbin/sshd","-D"]
#CMD ["/sbin/init"]
