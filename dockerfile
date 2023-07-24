FROM nvidia/cuda:11.0.3-base-ubuntu20.04

USER root
ENV DEBIAN_FRONTEND=noninteractive
RUN adduser --gecos "" --disabled-password yubo1336
RUN apt update
RUN apt install -y ffmpeg sudo curl unzip vim wget git less llvm-8 make g++ clang


USER yubo1336
WORKDIR /home/yubo1336
RUN curl -sSf https://rye-up.com/get | RYE_NO_AUTO_INSTALL=1 RYE_INSTALL_OPTION="--yes" bash
RUN echo "$PATH=\"$HOME/.rye/shims:$PATH\"" >> ~/.bashrc

