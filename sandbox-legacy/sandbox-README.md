# Claude Code + gvc Sandbox

The `./sandbox` script creates a sandbox to restrict the actions of Claude Code and
gvc inside of it. It's intended to allow safe usage of Claude Code to
develop gvc without being slowed down by interactive permission prompts.
Any actions not deemed to be safe are automatically denied by the sandbox.

## Installation

### Shell Startup File: Move out secrets

Inspect your shell startup file to see if they contain any secrets in environment variables.
Move any secrets to separate files that are included by your main shell startup file:

```
# .bash_profile
source .bashrc
```

```
# .bashrc
source .bashrc_secrets  # 👈 move secrets out of the main shell startup files

echo PATH="$HOME/bin:$PATH"  # for example
```

```
# .bashrc_secrets
echo AWS_ACCESS_KEY_ID=...
echo AWS_SECRET_ACCESS_KEY=...
```

### Agents File: Notify that sandbox is active

Recommend that you add the following to your `CLAUDE.md` or `AGENTS.md`:
```
**Sandboxed**: All your tool calls in this session (Bash, Read, Write, etc)
are being run inside a sandbox located at: ./sandbox.
Permission denied errors may be caused by the sandbox rather than the underlying command - 
if it matters to distinguish, ask the user to rerun the command themselves.
For simple cases, consult ./sandbox-README.md or ./sandbox directly to see what actions are allowed.
You cannot disable the sandbox.
```

## Usage (Outer Mode)

Normally this sandbox is intended to wrap Claude Code itself in an "outer sandbox":

```
./sandbox claude --dangerously-skip-permissions
```

## Usage (Inner Mode)

It is also possible to wrap a gvc-related command with a stricter "inner sandbox":

```
./sandbox <command> [args...]  # any gvc-related command
```

For example:

```
./sandbox poetry run pytest
```

The inner sandbox notably does not allow any network communication except to localhost
(except for gvc-specific file-based Unix sockets).

## Known Issues

- No network isolation (when in Outer Mode)
    - Therefore it is possible for sensitive data inside the sandbox to be
      exfiltrated to an attacker-controlled remote server. Regular gvc
      development does not involve any sensitive data.

- No authenticated GitHub access (By Design)
    - SSH keys for connecting to GitHub.com are NOT readable from inside the sandbox.
      In fact no ~/.ssh access of any kind is granted.
      Therefore you must `git push` from outside the sandbox. Claude cannot push itself.

- No writable Claude Code settings (By Design)
    - Changing the model (`/model`) or effort level (`/effort`) within
      a sandboxed Claude Code will not work.
        - Workaround with `/exit`, relaunch unsandboxed, run `/model` or `/effort`, 
          `/exit` again, relaunch sandboxed.

## Security Model

The sandbox itself and any process running inside it has access to some of the
following (valuable) resources:

- Disk contents (i.e. persisted local data)
    - System data (🔍 read-only, with a few exceptions below)
        - General temporary files at /private/var/folders/*/*/T
          (✏️ READ-WRITE in Outer Mode; 🔍 read-only in Inner Mode)
        - Claude Code temporary files at /private/tmp (✏️ READ-WRITE in Outer Mode)
        - gvc temporary files at /private/tmp (✏️ READ-WRITE)
        - General cache files at /private/var/folders/*/*/C (✏️ WRITE ONLY)
    - All users' data (❌ no access, with a few exceptions below)
        - Filesystem change notifications via FSEvents (🔍 read-only in Outer Mode)
    - Current user data (❌ no access, with several exceptions below)
        - bash startup scripts at ~/.bash_profile and ~/.bashrc (🔍 read-only)
            - Necessary to discover $PATH customizations
            - Assumes any secret environment variables have been moved to
              other script files, as mentioned in §Installation above
        - Claude Code configuration at ~/.claude
          (🔍 read-only in Outer Mode, with a few exceptions below)
            - Claude Code conversation history, session state, and plans,
              including non-sandboxed sessions (✏️ READ-WRITE)
            - Claude Code subscription/API key at ~/.claude.json (✏️ READ-WRITE)
        - Keychain data at ~/Library/Keychains (🔍 read-only in Outer Mode)
            - The keychain data is encrypted so cannot be interpreted directly
        - Python caches at ~/Library/Caches/{org.python.python, com.apple.python}
          (✏️ READ-WRITE and 🔍 read-only)
        - Python and gvc.app WebKit storage at ~/Library/WebKit (✏️ READ-WRITE)
        - Claude Code cache and logs at ~/Library/Caches/claude-cli-nodejs
          (✏️ READ-WRITE in Outer Mode)
        - gvc logs at ~/Library/Logs/gvc (✏️ WRITE ONLY)
        - Git configuration at ~/.gitconfig (🔍 read-only)
            - Does NOT contain GitHub credentials for modern versions of the `gh` CLI tool
                - Modern `gh` stores credentials in the keychain
                  (and possibly ~/.config/gh/hosts.yml) (❌ no access)
        - Local binaries at ~/.local/bin (🔍 read-only)
        - pipx-installed binaries at ~/.local/pipx/venvs (🔍 read-only)
        - Claude Code binary at ~/.local/share/claude (🔍 read-only in Outer Mode)
        - poetry configuration at ~/Library/Application Support/pypoetry (🔍 read-only)
        - pip and poetry cache (🔍 read-only)
    - Current project data (✏️ READ-WRITE, with a few exceptions below)
        - Claude Code local configuration at ./.claude (🔍 read-only)
        - Sandbox script at ./sandbox (🔍 read-only)
- Disk usage (i.e. bytes stored) (∞ UNRESTRICTED)
- Disk throughput (∞ UNRESTRICTED)
    - IOPS, bytes read/written per second, % of time performing I/O
- Memory usage (i.e. bytes stored) (∞ UNRESTRICTED)
- CPU usage (i.e. % of time performing calculations) (∞ UNRESTRICTED)
- Network communication outbound (∞ UNRESTRICTED in Outer Mode; 🔒 localhost + gvc Unix sockets only in Inner Mode)
    - identity/authority, data/command inputs, data/command outputs
    - persisted remote data
    - packets/second, bytes read/written per second, % of link bandwidth used

Resources **protected** now:
- All users' data, including the current user, EXCLUDING the current project,
  EXCLUDING cached files, temporary files, log files, and configuration files
  for {Claude Code, Python, pipx, poetry, gvc}
    - Block reads (exfiltration)
    - Block writes (corruption, destruction)
- System data, EXCLUDING cached files and temporary files
    - Block writes (corruption, destruction)

Resources NOT protected now but will be in the future:
- Network communication outbound
    - FUTURE: Limit outbound protocols to allowlist (e.g. http, https)
    - FUTURE: Limit outbound domains that can be contacted
    - FUTURE: Limit outbound URL path prefixes that can be read or written

Resources NOT protected now and **out of scope** to be protected in the future:
- Disk usage and throughput
- Memory usage
- CPU usage
- System identity
    - System can be fingerprinted through hardware configuration information

Attackers are assumed to have full (but non-root) shell access inside the sandbox
but to not have any kind of local access outside the sandbox.

## Externalizability

Currently this sandbox is customized for gvc development. It may however serve
as a useful base for a general sandbox for Claude Code development on other projects.

If this sandbox is generalized in that manner in the future,
it will need some **extensibility hooks** to allow it to be extended to accommodate
the needs of whatever project is under development. For example the gvc project
specifically needs access to many Mach services to run as a standalone .app bundle.
It also requires a lot of permissions related to using WKWebView (embedded WebKit).
