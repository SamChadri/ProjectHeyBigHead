FROM python:3.7.5
WORKDIR /usr/src/projectAlfred/

COPY . .
RUN ls -a
RUN cp -r .aws ~/

RUN ls -a ~/

RUN apt-get update
RUN apt-get -y install sudo
RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo

RUN sudo apt-get -y install cmake
RUN wget http://downloads.sourceforge.net/project/fann/fann/2.2.0/FANN-2.2.0-Source.zip

RUN unzip FANN-2.2.0-Source.zip
RUN cd FANN-2.2.0-Source && \
    cmake . && \
    sudo make install
RUN pip install --upgrade pip

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN sudo ./aws/install

RUN apt-get -y install swig
RUN apt-get -y install sox

RUN pip3 install pandas
RUN pip3 install deepspeech
RUN pip3 install numpy
RUN pip3 install sox
RUN pip3 install webrtcvad
RUN pip3 install glob2
RUN pip3 install padatious
RUN pip3 install dataclasses
RUN pip3 install pymongo
RUN pip3 install boto3
RUN pip3 install asyncio
RUN pip3 install flask
RUN pip3 install requests
RUN pip3 install datetime
RUN pip3 install azure-cognitiveservices-search-websearch
RUN pip3 install pywikibot
RUN pip3 install google-api-python-client
RUN pip3 install dateparser
RUN pip3 install "wikitextparser>=0.47.5"
RUN pip3 install google_auth_oauthlib

RUN echo 'export PYWIKIBOT_DIR="/Users/BEATFREAK/busyWork/projectAflred/alfred/models/api_models/"' >> ~/.bashrc
RUN echo 'export MONGO_DB="mongodb://alfred-mongo:27017/"' >> ~/.bashrc
RUN echo 'export FLASK_APP=alfred.alfred_api' >> ~/.bashrc
RUN . ~/.bashrc



CMD  ["flask", "run", "--host=0.0.0.0"]
