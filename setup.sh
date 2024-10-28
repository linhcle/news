#!/bin/bash

# Set Playwright to install browsers within the project directory
export PLAYWRIGHT_BROWSERS_PATH=/home/appuser/.cache/ms-playwright

# Force install the specific version of Chromium you need
npx playwright install chromium

# Verify the browser installation
ls -alh /home/appuser/.cache/ms-playwright/chromium-1140/
