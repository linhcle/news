#!/bin/bash

# Set Playwright to install browsers in the project cache directory
# export PLAYWRIGHT_BROWSERS_PATH=/home/appuser/.cache/ms-playwright

# Install the required version of Chromium (replace with correct version if needed)
echo "Installing Playwright browsers..."
playwright install chromium
# Verify the installation and directory structure
# ls -alh /home/appuser/.cache/ms-playwright/
