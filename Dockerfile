FROM python:3.13-slim as runtime

COPY requirements.lock ./
RUN sed '/-e/d' requirements.lock > requirements.txt
RUN pip install -r requirements.txt

# ローカルマシン(日本) のときは効果あるかも
# RUN sed -i 's@archive.ubuntu.com@ftp.jaist.ac.jp/pub/Linux@g' /etc/apt/sources.list
#一旦play.pyの導入は見送るのでとりあえずffmpegはコメントアウト
#RUN apt-get update \
#    && apt-get -y upgrade \
#    && apt-get install -y ffmpeg

COPY src /app
WORKDIR /app

ENTRYPOINT ["python", "main.py"]
CMD []
