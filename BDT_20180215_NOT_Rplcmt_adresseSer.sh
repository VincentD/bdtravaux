#!/bin/bash
for file in bd*.py
do
  echo "Traitement de $file ..."
  sed -i 's/127.0.0.1/192.168.0.10/g' "$file"
done



