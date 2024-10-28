#!/bin/bash

# Set Playwright to install browsers within the container or the right path.
export PLAYWRIGHT_BROWSERS_PATH=0

# Force reinstallation of the exact Chromium 1140 version
npx playwright install chromium@114.0.5735.90

# Verify that the correct version is installed
ls -alh /root/.cache/ms-playwright/
