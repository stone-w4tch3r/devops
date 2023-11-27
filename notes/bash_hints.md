# Get path to curr file
```bash
DIR="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd "$DIR"/../ || exit 1
```
