FROM centos:7
RUN yum update -y
RUN yum install -y epel-release
RUN yum install -y python2-pip python-devel gcc
RUN git clone https://github.com/rackeric/cryptowalletsviewer.git /app
WORKDIR /app
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["app.py"]
