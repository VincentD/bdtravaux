#!/bin/bash
for file in bd*.py
do
  echo "Traitement de $file ..."
  sed -i 's/192.168.0.10/127.0.0.1/g' "$file"
done



