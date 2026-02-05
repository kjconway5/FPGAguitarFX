FROM ucsclearn/cse-x25:fa25

ENV LANG C.UTF-8
ARG INSTALL_ZSH="true"

RUN apt-get -y install npm
RUN cd /opt && git clone https://github.com/nturley/netlistsvg
RUN cd /opt/netlistsvg && npm install --legacy-peer-deps && npm install . -g

ENV PATH="/usr/local/bin/tabby/bin:$PATH"
ENV YOSYSHQ_LICENSE="/usr/local/bin/tabby/license/yosyshq.lic"

# Non-root user for normal builds
RUN useradd -ms /bin/bash fpga
USER fpga
WORKDIR /home/fpga