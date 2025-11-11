#!/usr/bin/env python3
"""
Codex Helper - Simple read-only utilities for AI agents working with Codex CLI

This tool does NOT wrap or execute codex commands. Instead, it:
1. Provides a comprehensive guide for AI agents
2. Extracts session information from codex's native storage
3. Fails fast with clear error messages

AI agents should call codex commands directly and use this for queries only.
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


class CodexHelper:
    """Read-only helper to query Codex CLI session data"""

    def __init__(self):
        self.codex_dir = Path.home() / ".codex"
        self.sessions_dir = self.codex_dir / "sessions"

    def get_latest_session_id(self, nth: int = 1, show_time: bool = False) -> Optional[str]:
        """
        Extract the Nth most recent session ID from codex storage.

        Args:
            nth: Which session to get (1 = most recent, 2 = second most recent, etc.)
            show_time: If True, include time ago in output

        Returns:
            Session ID string or None if not found
        """
        if not self.sessions_dir.exists():
            print("ERROR: ~/.codex/sessions/ directory not found", file=sys.stderr)
            print("Is Codex CLI installed and initialized?", file=sys.stderr)
            return None

        # Find all session files
        try:
            session_files = list(self.sessions_dir.glob("*/*/*/*.jsonl"))
            if not session_files:
                print("ERROR: No session files found in ~/.codex/sessions/", file=sys.stderr)
                return None

            # Sort by modification time, newest first
            session_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

            if nth > len(session_files):
                print(f"ERROR: Only {len(session_files)} sessions exist, cannot get #{nth}", file=sys.stderr)
                return None

            target_file = session_files[nth - 1]

            # Extract session ID from first line
            with open(target_file, 'r') as f:
                first_line = f.readline()
                if not first_line:
                    print(f"ERROR: Session file is empty: {target_file}", file=sys.stderr)
                    return None

                data = json.loads(first_line)
                session_id = data.get('payload', {}).get('id')
                timestamp = data.get('payload', {}).get('timestamp')

                if not session_id:
                    print(f"ERROR: No session ID in file: {target_file}", file=sys.stderr)
                    return None

                if show_time and timestamp:
                    time_str = time_ago(timestamp)
                    return f"{session_id}; started {time_str}"
                return session_id

        except Exception as e:
            print(f"ERROR: Failed to extract session ID: {e}", file=sys.stderr)
            return None

    def list_sessions(self, limit: int = 20) -> List[Dict]:
        """
        List recent codex sessions with metadata.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session dictionaries with metadata
        """
        if not self.sessions_dir.exists():
            print("ERROR: ~/.codex/sessions/ directory not found", file=sys.stderr)
            return []

        try:
            session_files = list(self.sessions_dir.glob("*/*/*/*.jsonl"))
            if not session_files:
                return []

            # Sort by modification time, newest first
            session_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

            sessions = []
            for session_file in session_files[:limit]:
                try:
                    with open(session_file, 'r') as f:
                        first_line = f.readline()
                        if not first_line:
                            continue

                        data = json.loads(first_line)
                        payload = data.get('payload', {})

                        # Extract first prompt and sandbox from events
                        first_prompt = None
                        sandbox_policy = None
                        f.seek(0)
                        user_messages_seen = 0
                        for line in f:
                            try:
                                event = json.loads(line)
                                # Get sandbox from turn_context
                                if not sandbox_policy and event.get('type') == 'turn_context':
                                    sp = event.get('payload', {}).get('sandbox_policy')
                                    if isinstance(sp, dict):
                                        sandbox_policy = sp.get('mode')
                                    elif isinstance(sp, str):
                                        sandbox_policy = sp
                                # Get first actual user message (skip environment_context)
                                if event.get('type') == 'response_item':
                                    event_payload = event.get('payload', {})
                                    if event_payload.get('role') == 'user':
                                        content = event_payload.get('content', [])
                                        if content and len(content) > 0:
                                            text = content[0].get('text', '') or ''
                                            # Skip environment_context messages
                                            if text and '<environment_context>' not in text:
                                                first_prompt = text.strip()[:50]
                                                if first_prompt and sandbox_policy:
                                                    break
                            except:
                                continue

                        timestamp = payload.get('timestamp')
                        sessions.append({
                            'session_id': payload.get('id'),
                            'timestamp': timestamp,
                            'time_ago': time_ago(timestamp) if timestamp else 'unknown',
                            'cwd': payload.get('cwd'),
                            'model_provider': payload.get('model_provider'),
                            'source': payload.get('source'),
                            'sandbox_policy': sandbox_policy,
                            'first_prompt': first_prompt or '',
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
        if not self.sessions_dir.exists():
            print("ERROR: ~/.codex/sessions/ directory not found", file=sys.stderr)
            return None

        try:
            # Search for session file containing this ID
            for session_file in self.sessions_dir.glob("*/*/*/*.jsonl"):
                try:
                    with open(session_file, 'r') as f:
                        first_line = f.readline()
                        if not first_line:
                            continue

                        data = json.loads(first_line)
                        payload = data.get('payload', {})

                        if payload.get('id') == session_id:
                            # Extract additional info
                            f.seek(0)
                            event_count = 0
                            first_prompt = None
                            sandbox_policy = None

                            for line in f:
                                event_count += 1
                                try:
                                    event = json.loads(line)
                                    # Get sandbox from turn_context
                                    if not sandbox_policy and event.get('type') == 'turn_context':
                                        sp = event.get('payload', {}).get('sandbox_policy')
                                        if isinstance(sp, dict):
                                            sandbox_policy = sp.get('mode')
                                        elif isinstance(sp, str):
                                            sandbox_policy = sp
                                    # Get first actual user message (skip environment_context)
                                    if not first_prompt and event.get('type') == 'response_item':
                                        event_payload = event.get('payload', {})
                                        if event_payload.get('role') == 'user':
                                            content = event_payload.get('content', [])
                                            if content and len(content) > 0:
                                                text = content[0].get('text', '') or ''
                                                if text and '<environment_context>' not in text:
                                                    first_prompt = text.strip()[:100]
                                except:
                                    continue

                            timestamp = payload.get('timestamp')
                            return {
                                'session_id': session_id,
                                'timestamp': timestamp,
                                'time_ago': time_ago(timestamp) if timestamp else 'unknown',
                                'cwd': payload.get('cwd'),
                                'model_provider': payload.get('model_provider'),
                                'cli_version': payload.get('cli_version'),
                                'source': payload.get('source'),
                                'sandbox_policy': sandbox_policy,
                                'first_prompt': first_prompt or 'N/A',
                                'file_path': str(session_file),
                                'event_count': event_count,
                                'modified_at': datetime.fromtimestamp(session_file.stat().st_mtime).isoformat()
                            }
                except Exception:
                    continue

            print(f"ERROR: Session '{session_id}' not found", file=sys.stderr)
            return None

        except Exception as e:
            print(f"ERROR: Failed to get session info: {e}", file=sys.stderr)
            return None


def ensure_start(pid: int, log_path: str) -> bool:
    """
    Verify that a codex task started successfully.
    
    Checks:
    1. Process is still alive after sleep
    2. Log file exists and has content
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
                log_lines = f.readlines()[:5]  # last 5 line
        except Exception as e:
            print(f"ERROR: Failed to read log file: {e}", file=sys.stderr)
            return False

    # Check for common startup errors
    error_indicators = [
        "error",
        "not inside a trusted directory",
        "no such file or directory",
        "permission denied",
        "fatal:",
    ]
    has_error = any(
        any(indicator in line.lower() for indicator in error_indicators)
        for line in log_lines
    )

    # Get session ID
    helper = CodexHelper()
    session_id = helper.get_latest_session_id(1, show_time=False)

    # Print results
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         CODEX STARTUP VERIFICATION RESULTS                ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()

    status = "✓ ALIVE" if is_alive else "✗ DEAD"
    print(f"Process Status:  {status} (PID: {pid})")
    print(f"Log File:        {log_path} ({log_file.stat().st_size if has_logs else 0} bytes)")
    print(f"Session ID:      {session_id or 'Not yet available'}")
    print(f"Start Time:      {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Elapsed:         {elapsed.total_seconds():.1f}s")
    print()

    if log_lines:
        print("First log lines:")
        print("─" * 60)
        for line in log_lines:
            print("  " + line.rstrip())
        print("─" * 60)
        print()

    # Determine overall success
    success = is_alive and has_logs and not has_error

    if success:
        print("✓ Task started successfully!")
    else:
        if not is_alive:
            print("✗ FAILED: Process died during initialization")
        if not has_logs:
            print("✗ FAILED: No log output detected")
        if has_error:
            print("✗ FAILED: Startup error detected in logs")

    print()
    return success


def print_guide():
    """Print comprehensive guide for AI agents"""
    guide = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                   CODEX CLI - AI AGENT GUIDE                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

You execute codex commands directly. This tool only queries session info.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 STARTING TASKS

Sync (wait for completion):
  $ codex exec "Create test file" --full-auto --cd /project

Async (background):
  $ codex exec "Build API" --full-auto --cd /project > /tmp/api.log 2>&1 &

Multiple concurrent with verification:
  $ codex exec "Task 1" --full-auto --cd /path > /tmp/t1.log 2>&1 &
  $ codex-helper ensure-start --pid $! --logs /tmp/t1.log

  $ codex exec "Task 2" --full-auto --cd /path > /tmp/t2.log 2>&1 &
  $ codex-helper ensure-start --pid $! --logs /tmp/t2.log

  $ codex exec "Task 3" --full-auto --cd /path > /tmp/t3.log 2>&1 &
  $ codex-helper ensure-start --pid $! --logs /tmp/t3.log

For complex prompts, use a separate file instead of passing via CLI args
to avoid string interpolation issues with quotes:

  Good:  codex exec "Read TASK_API.md and implement it" --full-auto --cd /project
  Bad:   codex exec "Create API with \"auth\" and \"users\" endpoints" --full-auto

Store prompts in files (e.g., TASK_API.md) and reference them in your command.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛑 INTERRUPTING TASKS

Kill a running task:
  $ kill <PID>                    # Graceful termination
  $ kill -9 <PID>                 # Force kill if needed

Check if process finished:
  $ kill -0 $PID 2>/dev/null && echo "Running" || echo "Done"
  $ ps aux | grep $PID

⚠️  IMPORTANT: Always verify the previous task has completed before continuing
    a conversation. Check the PID status first to avoid inconsistent results:
  
  $ kill -0 $PREV_PID 2>/dev/null && echo "Still running!" || echo "Finished"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 QUERYING SESSIONS & CONTINUING CONVERSATIONS

Get session ID:
  $ codex-helper get-id                # Latest
  $ codex-helper get-id --nth 2        # 2nd most recent

List sessions:
  $ codex-helper list
  $ codex-helper list --limit 50 --json

Session details:
  $ codex-helper info 019a7174-1f4c-7482-8846-b2f7bd5d2d3e

Continue conversation by session ID (always verify task is done first!):
  $ kill -0 $PREV_PID 2>/dev/null || codex exec "follow up message" --full-auto --cd /project resume $SESSION_ID
  
  Example:
  $ kill -0 2290964 2>/dev/null || codex exec "what's the status?" --full-auto --cd ~/Projects/job/ resume 019a7491-d609-7542-b918-d61bf703e227

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 MONITORING

Check process:
  $ ps aux | grep $PID
  $ kill -0 $PID 2>/dev/null && echo "Running" || echo "Done"

View logs:
  $ cat /tmp/api.log | tail -100

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 COMPLETE EXAMPLE

# Start 3 concurrent agents
codex exec "Build API" --full-auto --cd /project > /tmp/api.log 2>&1 &
codex-helper ensure-start --pid $! --logs /tmp/api.log

codex exec "Build UI" --full-auto --cd /project > /tmp/ui.log 2>&1 &
codex-helper ensure-start --pid $! --logs /tmp/ui.log

codex exec "Write tests" --full-auto --cd /project > /tmp/tests.log 2>&1 &
codex-helper ensure-start --pid $! --logs /tmp/tests.log

# Monitor
codex-helper list --limit 3

# Wait for completion
wait $API_PID $UI_PID $TESTS_PID

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚙️  IMPORTANT FLAGS

--full-auto
  Auto-approve all actions (safer, recommended for most cases)
  Use by default unless user specifically asks otherwise

--dangerously-bypass-approvals-and-sandbox
  Skip ALL approvals AND sandboxing (less strict than --full-auto)
  ONLY use when user explicitly requests it
  Gives full system access without restrictions

--cd <dir>
  Set working directory (always use this)

--json
  Output structured events (useful for parsing logs)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 BEST PRACTICES

1. Always use --full-auto for unattended execution
2. Always specify --cd /path/to/project
3. Always redirect output for async: > /tmp/task.log 2>&1 &
4. Always store PIDs: PID=$! or echo $! > /tmp/session_id
5. Always ensure codex started: codex-helper ensure-start --pid $! --logs /tmp/out.log
6. Always use a file for complex prompts

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛠️  codex-helper Commands

  get-id [--nth N]                             Get Nth most recent session ID
  list [--limit N] [--json]                    List recent sessions
  info <session-id>                            Get detailed session info
  ensure-start --pid <PID> --logs <PATH>       Verify task started successfully
  guide                                        Show this guide

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  LIMITATIONS & NOTES

• Task Interruption: Use `kill <PID>` or `kill -9 <PID>` to stop long-running tasks
  Always check process status before continuing conversations to avoid inconsistencies

• Session ID Timing: Wait ~2 seconds after starting before querying

• Git Repo: Required unless using --skip-git-repo-check

• Resume Reliability: Works better if you verify the previous process is done:
  1. Check: kill -0 $OLD_PID 2>/dev/null && echo "Still running" || echo "Done"
  2. If done, continue with: codex exec "message" --full-auto resume $SESSION_ID

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
    print(guide)


def main():
    parser = argparse.ArgumentParser(
        description="Codex Helper - Read-only utilities for querying Codex CLI sessions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="This tool does NOT execute codex commands. Use it for queries only."
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

    # list command
    list_parser = subparsers.add_parser(
        "list",
        help="List recent codex sessions"
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
        help="Verify codex task started successfully"
    )
    ensure_parser.add_argument(
        "--pid",
        type=int,
        required=True,
        help="Process ID of the codex command"
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

    helper = CodexHelper()

    try:
        if args.command == "get-id":
            session_id = helper.get_latest_session_id(args.nth, show_time=True)
            if session_id:
                print(session_id)
                sys.exit(0)
            else:
                sys.exit(1)

        elif args.command == "list":
            sessions = helper.list_sessions(args.limit)
            if not sessions:
                print("No sessions found", file=sys.stderr)
                sys.exit(1)

            if args.json:
                print(json.dumps(sessions, indent=2))
            else:
                print(f"\n{'SESSION ID':<37} {'TIME':<10} {'SANDBOX':<12} {'PROMPT':<50}")
                print("─" * 115)
                for session in sessions:
                    session_id = session['session_id'] or 'N/A'
                    session_id = session_id[:36] if session_id != 'N/A' else 'N/A'

                    timestamp = session.get('timestamp') or 'N/A'
                    if timestamp and timestamp != 'N/A' and 'T' in str(timestamp):
                        timestamp = str(timestamp).split('T')[1][:8]  # Just time

                    sandbox = session.get('sandbox_policy') or 'N/A'
                    if sandbox and sandbox != 'N/A':
                        # Shorten common sandbox values
                        sandbox = str(sandbox).replace('workspace-write', 'ws-write').replace('read-only', 'readonly')
                    sandbox = str(sandbox or 'N/A')[:11]

                    prompt = (session.get('first_prompt') or '')[:48]
                    if len((session.get('first_prompt') or '')) > 48:
                        prompt += '..'

                    print(f"{session_id:<37} {timestamp:<10} {sandbox:<12} {prompt:<50}")
                print()

        elif args.command == "info":
            info = helper.get_session_info(args.session_id)
            if info:
                print(f"\nSession: {info['session_id']}")
                print("─" * 80)
                print(f"Timestamp:      {info.get('timestamp', 'N/A')}")
                print(f"Started:        {info.get('time_ago', 'N/A')}")
                print(f"Working Dir:    {info.get('cwd', 'N/A')}")
                print(f"Model Provider: {info.get('model_provider', 'N/A')}")
                print(f"CLI Version:    {info.get('cli_version', 'N/A')}")
                print(f"Source:         {info.get('source', 'N/A')}")
                print(f"Sandbox:        {info.get('sandbox_policy', 'N/A')}")
                print(f"Events:         {info.get('event_count', 0)}")
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
