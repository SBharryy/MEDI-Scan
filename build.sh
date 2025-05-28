#!/bin/bash
set -e

# Install system dependencies
apt-get update
apt-get install -y tesseract-ocr libtesseract-dev

# Install Python dependencies
pip install -r requirements.txt