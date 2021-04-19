#!/usr/bin/env bash

set -ex
docker-compose -f tests/integration/docker-compose.yaml up -d
sleep 20
export pass=$(perl -e 'print crypt($ARGV[0], "password")' "$TEST_PASSWORD")
docker exec slurmctld bash -c 'useradd -m -p "$0" "$1"' "$pass" "$TEST_USER"
docker exec slurmctld bash -c "/usr/bin/sacctmgr --immediate add cluster name=linux"
docker-compose -f tests/integration/docker-compose.yaml restart slurmdbd slurmctld
docker exec slurmctld bash -c '/usr/sbin/sshd'
docker exec slurmctld bash -c 'sacctmgr -i add account "$0" cluster=linux description="Resolos integration test user" Organization=resolos' $TEST_USER
docker exec slurmctld bash -c 'sacctmgr -i add user "$0" account="$0"' $TEST_USER $TEST_USER
export TEST_HOST=$(docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' slurmctld)
ssh-keyscan -H $TEST_HOST >> ~/.ssh/known_hosts
rm -f $HOME/.ssh/id_rsa_resolos