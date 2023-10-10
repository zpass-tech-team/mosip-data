#!/bin/bash

set -e
properties_file="$1"
echo `date "+%m/%d/%Y %H:%M:%S"` ": $properties_file"
if [ -f "$properties_file" ]
then
    echo `date "+%m/%d/%Y %H:%M:%S"` ": Property file \"$properties_file\" found."
    while IFS='=' read -r key value
    do
        key=$(echo $key | tr '.' '_')
        eval ${key}=\${value}
    done < "$properties_file"
else
     echo `date "+%m/%d/%Y %H:%M:%S"` ": Property file not found, Pass property file name as argument."
fi

echo "Action: $ACTION"

line_number=0
# Execute upgrade or rollback
if [ "$ACTION" == "upgrade" ]; then
  while read command; do
    let "line_number=line_number+1"
    echo "==================== Executing Command : $line_number ==========================="
    eval ${command}
  done < upgrade_commands.txt

elif [ "$ACTION" == "rollback" ]; then
  while read command; do
    let "line_number=line_number+1"
    echo "==================== Executing Command : $line_number ==========================="
    eval ${command}
  done < rollback_commands.txt

else
  echo "Unknown action: $ACTION, must be 'upgrade' or 'rollback'."
  exit 1
fi