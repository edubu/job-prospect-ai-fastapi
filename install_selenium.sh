#!/usr/bin/bash

echo "Changing to home directory..."
pushd "$HOME"

echo "Update the repository and any packages..."
sudo apt update && sudo apt upgrade -y

echo "Install prerequisite packages..."
sudo apt install wget curl unzip -y

echo "Download the latest Chrome .deb file..."
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

echo "Install Google Chrome..."
sudo dpkg -i google-chrome-stable_current_amd64.deb

echo "Fix dependencies..."
sudo apt --fix-broken install -y

chrome_version=($(google-chrome-stable --version))
echo "Chrome version: ${chrome_version[2]}"
