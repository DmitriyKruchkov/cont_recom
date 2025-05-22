FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y openssh-server && \
    mkdir -p /var/run/sshd /data/ssh && \
    useradd -m -s /bin/bash tunneluser && \
    echo "tunnelollama:ollamatunnelpass" | chpasswd

COPY sshd_config /etc/ssh/sshd_config

# Если есть старые ключи — используем их
RUN test -f /data/ssh/ssh_host_rsa_key || ssh-keygen -A

VOLUME /data/ssh
EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
