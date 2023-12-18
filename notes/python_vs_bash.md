# Python scripting instead of Bash

### Plan

1. Intro
2. What is bash, its pros & cons
3. What is python, its pros & cons
4. Bash pain points
5. Same code in python
6. How to use python for shell scripting
7. Working with sudo in python
8. Cross-platform code in python
9. Conclusion

### Intro

...

### Bash, its pros & cons

Created in 80s, used widely in linux, macos, docker, android etc.

Pros:

- simple for simple tasks
- cross-platform
- you all know it
  Cons:
- not really cross-platform
- difficult branching and loops
- hard to read
- inconsistent syntax
- inconsistent at all
- ancient paradigm
- lack of modern features
- difficult error handling

### Python, its pros & cons

Created in 90s, used widely in production, science and for scripting

Pros:

- simple for most tasks
- truly cross-platform
- preinstalled in most systems
- supports some modern paradigms
- readable
- IDE support
- huge stdlib
- libraries
  Cons:
- not for big projects
- dynamic typing
- duck typing
- slow
- inconsistent syntax and stdlib
- interpreted

### Bash pain points

Differences between linux, macos, docker (!) and so on:

- different commands or, worse, options
  ```bash
  # linux
  cp -r
  # macos
  cp -R
  ```
- sh and bash are same in macos, but different in linux
- different versions and features

Mismatch between bash and zsh:

- rm -rf * - works in bash, but not in zsh
- shell expanding works differently

Math is awful:

```bash
#
# MAX
#
max=0
numbers=(1 2 3 4 5)
for i in "${numbers[@]}"; do
    if [[ "$i" -gt "$max" ]]; then
        max="$i"
    fi
done

# or
max=echo "${numbers[@]}" | tr ' ' '\n' | sort -nr | head -n1

#
# AVERAGE
#
sum=0
for i in "${numbers[@]}"; do
    sum=$((sum + i))
done
avg=$((sum / ${#numbers[@]}))

# or
avg=$(echo "${numbers[@]}" | tr ' ' '\n' | awk '{sum+=$1} END {print sum/NR}')

# or, using bc:
avg=$(echo "${numbers[@]}" | tr ' ' '\n' | paste -sd+ | bc -l)
```

String globbing, expansion and escaping:

```bash
# globbing/expanding
price_str="Price: $price"

# escaping
normal_string='Command: "echo \"Hello, world!\""'

```

Branching and loops:

```bash
# branching
if [[ "$1" == "hello" ]]; then
    echo "Hello, world!"
elif [[ "$1" == "bye" ]]; then
    echo "Bye!"
else
    echo "Unknown command"
fi

#But it works differently in different shells:
# sh
if [ "$1" = "hello" ]; then
    echo "Hello, world!"
elif [ "$1" = "bye" ]; then
    echo "Bye!"
else
    echo "Unknown command"
fi
```

Get current dir:

```bash
DIR="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )" || exit 1
```

Error handling:

```bash
# by default, bash will continue after error
#
# use file header for stop on error, but still not safe
# 'error' is not same thing as 'accessing undefined variable' =)
set -euo pipefail
```

And much, much more...

### Same code in python

```python
# MAX
max(numbers)

# AVERAGE
sum(numbers) / len(numbers)

# strings handling
price_str = f'Price: {price}'
normal_string = """
Command: echo "Hello, world!"
"""

# branching
if sys.argv[1] == 'hello':
    print('Hello, world!')
elif sys.argv[1] == 'bye':
    print('Bye!')
else:
    print('Unknown command')

# loops
for i in range(10):
    print(i)

# get curr dir
base_dir = os.path.dirname(os.path.abspath(__file__))
```

### How to use python for shell scripting

**Use `subprocess` for shell commands**
<br>`subprocess.run(['dotnet', 'build'])`
<bt>This is cross-platform, but not weary readable.
<br>You can use this function for simplification:

```python
def run(cmd: str, ignore_errs: bool = False):
    return subprocess.run(cmd, shell=True, check=not ignore_errs)


run('dotnet build')
run('dotnet build', ignore_errs=True)
run(f'dotnet build -c {config} && dotnet test')
```

But this may not work in cross-platform way.

### Working with sudo in python

This is not so simple. You always can just `sudo mysript.py`, but this is not the best way.

Options are:

- run all script with sudo
- run shell primitives with sudo via `subprocess`:
  ```python
  subprocess.run(['sudo', 'apt', 'install', 'python3'])
  ```
- run dedicated file with sudo via `subprocess`:
  ```python
  subprocess.run(['sudo', 'python3', 'script.py', arg1])
  ```
- save function as text and run it with sudo via `subprocess` (BAD):
  ```python
  # 1. save code as text variable
  # 2. pass it to subprocess
  # 3. call function in same command
  # 4. pass arguments
  
  func_as_text = """
  def func(str1, str2):
    print(str1, str2)
  func(arg1, arg2)
  """
  arg1 = 'hello'
  arg2 = 'world'
  subprocess.run(['sudo', 'python3', '-c', f'arg1="{arg1}";arg2="{arg2}";{func_as_text}'])
  ```

### Cross-platform code in python

- **Portable path**
  `path = os.path.join('directory', 'subdirectory', 'file.txt')`

- **Instead of ls**
  `files = os.listdir('directory')`

- **Use forward slashes in paths**
  <br>Python will convert forward slashes to the appropriate path separator for the current operating system.

- **Use binary mode for opening files**
  <br>Open files in binary mode. This prevents system-dependant translating '\n'
  ```python
  with open('file.txt', 'rb') as f:  # rb - read binary
      data = f.read()
  ```

- **Use `shutil` for high-level file operations**
  ```python
  import shutil
  shutil.copyfile('source.txt', 'dest.txt')
  shutil.move('source.txt', 'dest.txt')
  ```

### Conclusion

Python is better than bash for scripting. But it is still piece of shit)