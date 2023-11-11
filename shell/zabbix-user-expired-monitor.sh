#!/bin/bash
diskarray=(`awk -F':' '$NF ~ /\/bin\/bash/||/\/bin\/sh/{print $1}' /etc/passwd`)
length=${#diskarray[@]}
printf "{\n"
printf '\t'"\"data\":["
for ((i=0;i<$length;i++))
do
    printf '\n\t\t{'
    printf "\"{#USER_NAME}\":\"${diskarray[$i]}\"}"
    if [ $i -lt $[$length-1] ];then
        printf ','
    fi
done
printf "\n\t]\n"
printf "}\n"
# 检查用户密码过期
#!/bin/bash
export LANG=en_US.UTF-8
SEVEN_DAYS_AGO=$(date -d '-7 day' +'%s')
user="$1"
# 将Sep 09, 2018格式的时间转换成unix时间
expires_date=$(chage -l $user | awk -F':' '/Password expires/{print $NF}' | sed -n 's/^ //p')
if [[ "$expires_date" != "never" ]];then
    expires_date=$(date -d "$expires_date" +'%s')
    if [ "$expires_date" -le "$SEVEN_DAYS_AGO" ];then
        echo "1"
    else
        echo "0"
    fi
else
    echo "0"
fi