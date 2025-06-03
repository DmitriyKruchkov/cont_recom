FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y openssh-server && \
    mkdir -p /var/run/sshd /data/ssh && \
    useradd -m -s /bin/bash tunnelollama && \
    echo 'tunnelollama:ollamatunnelpass' | chpasswd


COPY sshd_config /etc/ssh/sshd_config

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
