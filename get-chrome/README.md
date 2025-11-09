# get_chrome

A command-line tool that automatically installs Chrome for Testing and returns its executable path. Useful for automated testing, CI/CD pipelines, and development workflows that require a reliable Chrome installation.

## Installation

### Global Installation

```bash
git clone https://github.com/stone-w4tch3r/devops
cd devops/get-chrome
npm i
npm run build
sudo npm install -g .
```

### Uninstall

```bash
sudo npm uninstall get-chrome -g
```

## Usage

### Command Line

After global installation, simply run:

```bash
get-chrome | jq .path
```

This will:
1. Check if `CHROME_PATH` environment variable is set and valid
2. If not, automatically download and install Chrome for Testing
3. Return a JSON object with the Chrome executable path
4. Get path string via jq

Example output:
```json
{
  "path": "/home/user/.cache/puppeteer-browsers/chrome/linux-142.0.7444.61/chrome-linux64/chrome"
}
```

### Environment Variable Override

You can skip the automatic installation by setting the `CHROME_PATH` environment variable:

```bash
export CHROME_PATH=/usr/bin/google-chrome
get-chrome
```

## Cache Locations

Chrome for Testing is downloaded and cached in system-appropriate directories:

- **Linux**: `~/.cache/puppeteer-browsers`
- **macOS**: `~/Library/Caches/puppeteer-browsers`
- **Windows**: `%LOCALAPPDATA%/puppeteer-browsers`

The download only happens once. Subsequent runs use the cached version.
