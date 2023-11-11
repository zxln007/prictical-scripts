#!/bin/bash
COMMAND=$*
HOST_INFO=host.info
for IP in $(awk '/^[^#]/{print $1}' $HOST_INFO); do
    USER=$(awk -v ip=$IP 'ip==$1{print $2}' $HOST_INFO)
    PORT=$(awk -v ip=$IP 'ip==$1{print $3}' $HOST_INFO)
    PASS=$(awk -v ip=$IP 'ip==$1{print $4}' $HOST_INFO)
    expect -c "
    spawn ssh -p $PORT $USER@$IP
    expect {
        \"(yes/no)\" {send \"yes\r\"; exp_continue}
        \"password:\" {send \"$PASS\r\"; exp_continue}
        \"$USER@*\" {send \"$COMMAND\r exit\r\"; exp_continue}
    }
    "
    echo "-------------------"
done