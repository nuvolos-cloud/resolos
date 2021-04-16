FROM giovtorres/slurm-docker-cluster

RUN yum –y install openssh-server openssh-clients \
    && ssh-keygen -A \
    && /usr/sbin/sshd