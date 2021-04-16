FROM giovtorres/slurm-docker-cluster

RUN set -ex \
    && yum makecache fast \
    && yum -y install epel-release \
    && yum -y install \
       openssh-server \
       openssh-clients \
    && yum clean all \
    && ssh-keygen -A \
    && /usr/sbin/sshd