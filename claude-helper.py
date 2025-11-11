#!/usr/bin/env python3
"""
Claude Helper - Simple read-only utilities for AI agents working with Claude CLI

This tool does NOT wrap or execute claude commands. Instead, it:
1. Provides a comprehensive guide for AI agents
2. Extracts session information from claude's native storage
3. Fails fast with clear error messages

AI agents should call claude commands directly and use this for queries only.
"""

import argparse
import json
import sys
import time
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


def time_ago(timestamp_str: str) -> str:
    """
    Convert ISO timestamp to human-readable 'X ago' format.

    Args:
        timestamp_str: ISO format timestamp string (UTC)

    Returns:
        Human-readable time difference (e.g., '5 minutes ago')
    """
    try:
        from datetime import timezone

        # Parse timestamp (handle both with and without microseconds)
        if '.' in timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00') if timestamp_str.endswith('Z') else timestamp_str)

        # Convert UTC to local time
        if timestamp.tzinfo is not None:
            timestamp = timestamp.astimezone().replace(tzinfo=None)

        now = datetime.now()
        diff = now - timestamp

        seconds = int(diff.total_seconds())

        if seconds < 60:
            return f"{seconds} seconds ago"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = seconds // 86400
            return f"{days} day{'s' if days != 1 else ''} ago"
    except:
        return "unknown time ago"


def escape_path(path: str) -> str:
    """
    Escape a filesystem path the way Claude does for project directories.

    Args:
        path: Absolute path to escape

    Returns:
        Escaped path suitable for ~/.claude/projects/ lookup
    """
    # Convert /path/to/dir to -path-to-dir
    if path.startswith('/'):
        path = path[1:]  # Remove leading slash
    return '-' + path.replace('/', '-')


class ClaudeHelper:
    """Read-only helper to query Claude CLI session data"""

    def __init__(self):
        self.claude_dir = Path.home() / ".claude"
        self.projects_dir = self.claude_dir / "projects"
        self.history_file = self.claude_dir / "history.jsonl"

    def get_latest_session_id(self, nth: int = 1, show_time: bool = False, cwd: Optional[str] = None) -> Optional[str]:
        """
        Extract the Nth most recent session ID from claude storage.

        Args:
            nth: Which session to get (1 = most recent, 2 = second most recent, etc.)
            show_time: If True, include time ago in output
            cwd: Optional working directory to filter sessions by

        Returns:
            Session ID string or None if not found
        """
        if not self.projects_dir.exists():
            print("ERROR: ~/.claude/projects/ directory not found", file=sys.stderr)
            print("Is Claude CLI installed and initialized?", file=sys.stderr)
            return None

        try:
            # Find all session files
            session_files = []

            if cwd:
                # Search in specific project directory
                escaped_path = escape_path(os.path.abspath(cwd))
                project_dir = self.projects_dir / escaped_path
                if project_dir.exists():
                    session_files = [f for f in project_dir.glob("*.jsonl") if not f.name.startswith('agent-')]
            else:
                # Search all project directories
                for project_dir in self.projects_dir.iterdir():
                    if project_dir.is_dir():
                        session_files.extend([f for f in project_dir.glob("*.jsonl") if not f.name.startswith('agent-')])

            if not session_files:
                print("ERROR: No session files found", file=sys.stderr)
                return None

            # Sort by modification time, newest first
            session_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

            if nth > len(session_files):
                print(f"ERROR: Only {len(session_files)} sessions exist, cannot get #{nth}", file=sys.stderr)
                return None

            target_file = session_files[nth - 1]

            # Extract session ID from filename (it's the UUID before .jsonl)
            session_id = target_file.stem

            # Get timestamp from first event
            with open(target_file, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        timestamp = data.get('timestamp')
                        if timestamp:
                            if show_time:
                                time_str = time_ago(timestamp)
                                return f"{session_id}; started {time_str}"
                            return session_id
                    except:
                        continue

            # If no timestamp found, return just the ID
            return session_id

        except Exception as e:
            print(f"ERROR: Failed to extract session ID: {e}", file=sys.stderr)
            return None

    def list_sessions(self, limit: int = 20, cwd: Optional[str] = None) -> List[Dict]:
        """
        List recent claude sessions with metadata.

        Args:
            limit: Maximum number of sessions to return
            cwd: Optional working directory to filter sessions by

        Returns:
            List of session dictionaries with metadata
        """
        if not self.projects_dir.exists():
            print("ERROR: ~/.claude/projects/ directory not found", file=sys.stderr)
            return []

        try:
            # Find all session files
            session_files = []

            if cwd:
                # Search in specific project directory
                escaped_path = escape_path(os.path.abspath(cwd))
                project_dir = self.projects_dir / escaped_path
                if project_dir.exists():
                    session_files = [f for f in project_dir.glob("*.jsonl") if not f.name.startswith('agent-')]
            else:
                # Search all project directories
                for project_dir in self.projects_dir.iterdir():
                    if project_dir.is_dir():
                        session_files.extend([f for f in project_dir.glob("*.jsonl") if not f.name.startswith('agent-')])

            if not session_files:
                return []

            # Sort by modification time, newest first
            session_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

            sessions = []
            for session_file in session_files[:limit]:
                try:
                    session_id = session_file.stem
                    first_user_msg = None
                    timestamp = None
                    session_cwd = None
                    event_count = 0

                    with open(session_file, 'r') as f:
                        for line in f:
                            event_count += 1
                            try:
                                event = json.loads(line)

                                # Get first timestamp
                                if not timestamp:
                                    timestamp = event.get('timestamp')

                                # Get cwd
                                if not session_cwd:
                                    session_cwd = event.get('cwd')

                                # Get first user message (not meta)
                                if not first_user_msg and event.get('type') == 'user' and not event.get('isMeta'):
                                    msg = event.get('message', {})
                                    content = msg.get('content', '')
                                    if isinstance(content, str) and content:
                                        first_user_msg = content.strip()[:100]
                                    elif isinstance(content, list) and content:
                                        for item in content:
                                            if isinstance(item, dict) and item.get('type') == 'text':
                                                first_user_msg = item.get('text', '').strip()[:100]
                                                break
                            except:
                                continue

                    sessions.append({
                        'session_id': session_id,
                        'timestamp': timestamp,
                        'time_ago': time_ago(timestamp) if timestamp else 'unknown',
                        'cwd': session_cwd or 'unknown',
                        'first_prompt': first_user_msg or 'N/A',
                        'event_count': event_count,
                        'file_path': str(session_file),
                        'modified_at': datetime.fromtimestamp(session_file.stat().st_mtime).isoformat()
                    })
                except Exception as e:
                    print(f"WARNING: Failed to parse {session_file}: {e}", file=sys.stderr)
                    continue

            return sessions

        except Exception as e:
            print(f"ERROR: Failed to list sessions: {e}", file=sys.stderr)
            return []

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Get detailed info about a specific session.

        Args:
            session_id: The session ID to look up

        Returns:
            Session metadata dict or None if not found
        """
        if not self.projects_dir.exists():
            print("ERROR: ~/.claude/projects/ directory not found", file=sys.stderr)
            return None

        try:
            # Search for session file in all project directories
            for project_dir in self.projects_dir.iterdir():
                if not project_dir.is_dir():
                    continue

                session_file = project_dir / f"{session_id}.jsonl"
                if session_file.exists():
                    # Parse session file
                    first_user_msg = None
                    timestamp = None
                    session_cwd = None
                    event_count = 0
                    user_count = 0
                    assistant_count = 0

                    with open(session_file, 'r') as f:
                        for line in f:
                            event_count += 1
                            try:
                                event = json.loads(line)
                                event_type = event.get('type')

                                # Count event types
                                if event_type == 'user':
                                    user_count += 1
                                elif event_type == 'assistant':
                                    assistant_count += 1

                                # Get first timestamp
                                if not timestamp:
                                    timestamp = event.get('timestamp')

                                # Get cwd
                                if not session_cwd:
                                    session_cwd = event.get('cwd')

                                # Get first user message (not meta)
                                if not first_user_msg and event_type == 'user' and not event.get('isMeta'):
                                    msg = event.get('message', {})
                                    content = msg.get('content', '')
                                    if isinstance(content, str) and content:
                                        first_user_msg = content.strip()[:200]
                                    elif isinstance(content, list) and content:
                                        for item in content:
                                            if isinstance(item, dict) and item.get('type') == 'text':
                                                first_user_msg = item.get('text', '').strip()[:200]
                                                break
                            except:
                                continue

                    return {
                        'session_id': session_id,
                        'timestamp': timestamp,
                        'time_ago': time_ago(timestamp) if timestamp else 'unknown',
                        'cwd': session_cwd or 'unknown',
                        'first_prompt': first_user_msg or 'N/A',
                        'event_count': event_count,
                        'user_messages': user_count,
                        'assistant_messages': assistant_count,
                        'file_path': str(session_file),
                        'modified_at': datetime.fromtimestamp(session_file.stat().st_mtime).isoformat()
                    }

            print(f"ERROR: Session '{session_id}' not found", file=sys.stderr)
            return None

        except Exception as e:
            print(f"ERROR: Failed to get session info: {e}", file=sys.stderr)
            return None


def ensure_start(pid: int, log_path: str) -> bool:
    """
    Verify that a claude task started successfully.

    Checks:
    1. Process is still alive after sleep
    2. Log file exists and has content (or task completed)
    3. No startup errors in first lines

    Args:
        pid: Process ID to check
        log_path: Path to log file

    Returns:
        True if all checks pass, False otherwise
    """
    log_file = Path(log_path)
    start_time = datetime.now()

    # Sleep 3 seconds to let process initialize
    print(f"⌛ Waiting 3 seconds for initialization...", file=sys.stderr)
    time.sleep(3)

    # Check if process is still alive
    try:
        os.kill(pid, 0)  # Signal 0 just checks if process exists
        is_alive = True
    except (ProcessLookupError, OSError):
        is_alive = False

    # Check log file
    has_logs = log_file.exists() and log_file.stat().st_size > 0
    elapsed = datetime.now() - start_time

    # Read first lines of log
    log_lines = []
    if has_logs:
        try:
            with open(log_file, 'r') as f:
                log_lines = f.readlines()[:10]
        except Exception as e:
            print(f"ERROR: Failed to read log file: {e}", file=sys.stderr)
            return False

    # Check for error keywords in logs (case-insensitive)
    error_keywords = [
        "error",
        "fatal",
        "failed",
        "exception",
    ]
    has_error = any(
        any(keyword in line.lower() for keyword in error_keywords)
        for line in log_lines
    )

    # Get session ID
    helper = ClaudeHelper()
    session_id = helper.get_latest_session_id(1, show_time=False)

    # Print results
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         CLAUDE STARTUP VERIFICATION RESULTS               ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()

    status = "✓ ALIVE" if is_alive else "✓ COMPLETED" if has_logs else "✗ DEAD"
    print(f"Process Status:  {status} (PID: {pid})")
    print(f"Log File:        {log_path} ({log_file.stat().st_size if has_logs else 0} bytes)")
    print(f"Session ID:      {session_id or 'Not yet available'}")
    print(f"Start Time:      {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Elapsed:         {elapsed.total_seconds():.1f}s")
    print()

    if log_lines:
        print("First log lines:")
        print("─" * 60)
        for line in log_lines[:5]:
            print("  " + line.rstrip())
        print("─" * 60)
        print()

    # Determine overall success
    # Success if: (alive OR completed with logs) AND no errors
    success = (is_alive or has_logs) and not has_error

    if success:
        if is_alive:
            print("✓ Task started successfully and is running!")
        else:
            print("✓ Task completed successfully!")
    else:
        if not has_logs:
            print("✗ FAILED: No log output detected")
        if has_error:
            print("✗ FAILED: Startup error detected in logs")
        if not is_alive and not has_logs:
            print("✗ FAILED: Process died without producing output")

    print()
    return success


def print_guide():
    """Print comprehensive guide for AI agents"""
    guide = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                   CLAUDE CLI - AI AGENT GUIDE                                ║
╚══════════════════════════════════════════════════════════════════════════════╝

You execute claude commands directly. This tool only queries session info.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 STARTING TASKS

Sync (wait for completion):
  $ claude -p --dangerously-skip-permissions "Create test file"

Async (background):
  $ claude -p --dangerously-skip-permissions "Build API" > /tmp/api.log 2>&1 &

Multiple concurrent with verification:
  $ claude -p --dangerously-skip-permissions "Task 1" > /tmp/t1.log 2>&1 &
  $ claude-helper ensure-start --pid $! --logs /tmp/t1.log

  $ claude -p --dangerously-skip-permissions "Task 2" > /tmp/t2.log 2>&1 &
  $ claude-helper ensure-start --pid $! --logs /tmp/t2.log

  $ claude -p --dangerously-skip-permissions "Task 3" > /tmp/t3.log 2>&1 &
  $ claude-helper ensure-start --pid $! --logs /tmp/t3.log

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔄 CONTINUING CONVERSATIONS

Resume specific session:
  $ claude -p --resume {session-id} --dangerously-skip-permissions "Next task"

Resume most recent:
  $ claude --continue -p --dangerously-skip-permissions "Continue from where we left off"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 QUERYING SESSIONS (use helper)

Get session ID:
  $ claude-helper get-id                # Latest
  $ claude-helper get-id --nth 2        # 2nd most recent
  $ claude-helper get-id --cwd /path    # Latest in specific directory

List sessions:
  $ claude-helper list
  $ claude-helper list --limit 50 --json
  $ claude-helper list --cwd /project   # Filter by directory

Session details:
  $ claude-helper info 7a2c19a1-8555-4a4b-942f-8a5a5def79ea

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 MONITORING

Check process:
  $ ps aux | grep $PID
  $ kill -0 $PID 2>/dev/null && echo "Running" || echo "Done"

View logs:
  $ cat /tmp/api.log | tail -100

Interrupt task:
  $ kill $PID
  Note: Killing the process will interrupt the agent's work immediately.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  IMPORTANT NOTES ON LOG OUTPUT

Log files contain ONLY final response:
  Claude does NOT print intermediate thoughts or actions to stdout.
  The log file (e.g., /tmp/task.log) will only contain Claude's final response.
  Use this for capturing end results, not for tracking progress.

Track progress with explicit logging:
  To monitor task progress, ask Claude to write status updates to a separate log:
  
  $ claude -p --dangerously-skip-permissions \
      "Create API. Report your step-by-step progress into /tmp/job-progress.log"
  
  Then monitor with:
  $ tail -f /tmp/job-progress.log

Continue conversations safely:
  Always ensure the task is complete (PID not active) before resuming conversation:
  
  $ wait $PID
  $ echo $?  # Check exit code
  $ claude -p --resume {session-id} --dangerously-skip-permissions "Continue..."
  
  Resuming while task is running may cause context conflicts.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 COMPLETE EXAMPLE

# Start 3 concurrent agents
claude -p --dangerously-skip-permissions "Build API" > /tmp/api.log 2>&1 &
API_PID=$!
claude-helper ensure-start --pid $API_PID --logs /tmp/api.log

claude -p --dangerously-skip-permissions "Build UI" > /tmp/ui.log 2>&1 &
UI_PID=$!
claude-helper ensure-start --pid $UI_PID --logs /tmp/ui.log

claude -p --dangerously-skip-permissions "Write tests" > /tmp/tests.log 2>&1 &
TESTS_PID=$!
claude-helper ensure-start --pid $TESTS_PID --logs /tmp/tests.log

# Get their session IDs
API_SESSION=$(claude-helper get-id --nth 3)
UI_SESSION=$(claude-helper get-id --nth 2)
TESTS_SESSION=$(claude-helper get-id --nth 1)

# Monitor
claude-helper list --limit 3

# Continue a conversation
claude -p --resume $API_SESSION --dangerously-skip-permissions "Add authentication"

# Wait for completion
wait $API_PID $UI_PID $TESTS_PID

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚙️  IMPORTANT FLAGS

-p, --print
  Non-interactive mode - execute once and exit
  Required for background/async execution

--dangerously-skip-permissions
  Skip ALL permission checks
  Required for unattended execution
  Use with caution - only in trusted environments

--continue
  Continue most recent conversation

--resume {session-id}
  Resume specific conversation by ID


--output-format {text|json|stream-json}
  Format output (only with -p)

--model {sonnet|opus|haiku}
  Override model for session

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 BEST PRACTICES

1. Always use -p for unattended execution
2. Always use --dangerously-skip-permissions for background tasks
3. Always redirect output: > /tmp/task.log 2>&1 &
4. Always store PIDs: PID=$! after starting background task
5. Always verify startup: claude-helper ensure-start --pid $PID --logs /tmp/out.log
6. Context is preserved when using --resume or --continue
7. Always ask claude to log progress of complex tasks
8. Always ensure previous task is stopped before continuing conversation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛠️  claude-helper Commands

  get-id [--nth N] [--cwd PATH]               Get Nth most recent session ID
  list [--limit N] [--cwd PATH] [--json]      List recent sessions
  info <session-id>                            Get detailed session info
  ensure-start --pid <PID> --logs <PATH>       Verify task started successfully
  guide                                        Show this guide

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
    print(guide)


def main():
    parser = argparse.ArgumentParser(
        description="Claude Helper - Read-only utilities for querying Claude CLI sessions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="This tool does NOT execute claude commands. Use it for queries only."
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # get-id command
    getid_parser = subparsers.add_parser(
        "get-id",
        help="Get the Nth most recent session ID"
    )
    getid_parser.add_argument(
        "--nth",
        type=int,
        default=1,
        help="Which session (1=most recent, 2=second, etc.)"
    )
    getid_parser.add_argument(
        "--cwd",
        type=str,
        help="Filter sessions by working directory"
    )

    # list command
    list_parser = subparsers.add_parser(
        "list",
        help="List recent claude sessions"
    )
    list_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of sessions to show"
    )
    list_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    list_parser.add_argument(
        "--cwd",
        type=str,
        help="Filter sessions by working directory"
    )

    # info command
    info_parser = subparsers.add_parser(
        "info",
        help="Get detailed info about a session"
    )
    info_parser.add_argument(
        "session_id",
        help="Session ID to look up"
    )

    # guide command
    guide_parser = subparsers.add_parser(
        "guide",
        help="Show comprehensive guide for AI agents"
    )

    # ensure-start command
    ensure_parser = subparsers.add_parser(
        "ensure-start",
        help="Verify claude task started successfully"
    )
    ensure_parser.add_argument(
        "--pid",
        type=int,
        required=True,
        help="Process ID of the claude command"
    )
    ensure_parser.add_argument(
        "--logs",
        type=str,
        required=True,
        help="Path to the log file"
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    helper = ClaudeHelper()

    try:
        if args.command == "get-id":
            session_id = helper.get_latest_session_id(args.nth, show_time=True, cwd=getattr(args, 'cwd', None))
            if session_id:
                print(session_id)
                sys.exit(0)
            else:
                sys.exit(1)

        elif args.command == "list":
            sessions = helper.list_sessions(args.limit, cwd=getattr(args, 'cwd', None))
            if not sessions:
                print("No sessions found", file=sys.stderr)
                sys.exit(1)

            if args.json:
                print(json.dumps(sessions, indent=2))
            else:
                print(f"\n{'SESSION ID':<37} {'TIME':<18} {'CWD':<30} {'PROMPT':<40}")
                print("─" * 130)
                for session in sessions:
                    session_id = session['session_id'] or 'N/A'
                    session_id = session_id[:36] if session_id != 'N/A' else 'N/A'

                    time_ago_str = session.get('time_ago', 'N/A')[:17]

                    cwd = session.get('cwd') or 'N/A'
                    # Shorten cwd
                    if cwd != 'N/A' and len(cwd) > 28:
                        cwd = '...' + cwd[-25:]
                    cwd = cwd[:29]

                    prompt = (session.get('first_prompt') or '')[:38]
                    if len((session.get('first_prompt') or '')) > 38:
                        prompt += '..'

                    print(f"{session_id:<37} {time_ago_str:<18} {cwd:<30} {prompt:<40}")
                print()

        elif args.command == "info":
            info = helper.get_session_info(args.session_id)
            if info:
                print(f"\nSession: {info['session_id']}")
                print("─" * 80)
                print(f"Timestamp:      {info.get('timestamp', 'N/A')}")
                print(f"Started:        {info.get('time_ago', 'N/A')}")
                print(f"Working Dir:    {info.get('cwd', 'N/A')}")
                print(f"Events:         {info.get('event_count', 0)}")
                print(f"User Messages:  {info.get('user_messages', 0)}")
                print(f"AI Messages:    {info.get('assistant_messages', 0)}")
                print(f"Modified:       {info.get('modified_at', 'N/A')}")
                print(f"First Prompt:   {info.get('first_prompt', 'N/A')}")
                print(f"File:           {info.get('file_path', 'N/A')}")
                print()
                sys.exit(0)
            else:
                sys.exit(1)

        elif args.command == "guide":
            print_guide()
            sys.exit(0)

        elif args.command == "ensure-start":
            result = ensure_start(args.pid, args.logs)
            sys.exit(0 if result else 1)

    except KeyboardInterrupt:
        print("\n\nInterrupted", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
