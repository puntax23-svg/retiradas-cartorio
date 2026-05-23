#!/usr/bin/env bash

apt-get update
apt-get install -y tesseract-ocr
apt-get install -y tesseract-ocr-por

pip install -r requirements.txt
