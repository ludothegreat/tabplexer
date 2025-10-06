# Tabplexer

A lightweight tab management system for terminal emulators like Alacritty that don't support native tabs. It uses `xdotool` to manage multiple terminal windows and presents them as a single, tabbed interface.

## Dependencies

Ensure the following software is installed on your system:

*   **Alacritty:** The terminal emulator.
*   **Python 3:** The language the script is written in.
*   **xdotool:** A command-line tool for window manipulation.
*   **jq:** A command-line JSON processor for reading the session status.

> [!NOTE]
> The script validates that the required commands are available before it runs any
> action. If something is missing you will see a descriptive error with the list
> of dependencies that need to be installed.

You can typically install `xdotool` and `jq` using your system's package manager:
```bash
# For Debian/Ubuntu
sudo apt-get install xdotool jq

# For Fedora
sudo dnf install xdotool jq

# For Arch Linux
sudo pacman -S xdotool jq
```

## Files

This project consists of a single script:

*   `tabs.py`: The main script for managing tabs.

## Setup

1.  **Place the script:**
    Place the `tabs.py` script in a known location, for example `~/scripts/tabplexer/tabs.py`. Make sure it is executable:
    ```bash
    chmod +x ~/scripts/tabplexer/tabs.py
    ```

2.  **Configure Alacritty:**
    Add the following key bindings to your Alacritty configuration file (`~/.config/alacritty/alacritty.toml`). **Make sure to update the path to `tabs.py` if you placed it elsewhere.**

    ```toml
    [[keyboard.bindings]]
    key = "T"
    mods = "Control|Shift"
    command = { program = "~/scripts/tabplexer/tabs.py", args = ["new"] }

    [[keyboard.bindings]]
    key = "Right"
    mods = "Control|Shift"
    command = { program = "~/scripts/tabplexer/tabs.py", args = ["next"] }

    [[keyboard.bindings]]
    key = "Left"
    mods = "Control|Shift"
    command = { program = "~/scripts/tabplexer/tabs.py", args = ["prev"] }
    ```

3.  **Configure Your Shell Prompt (Optional):**
    To display the current tab status (e.g., `[2/3]`) in your shell prompt, add the appropriate snippet to your shell's startup file.

    **For Zsh (`~/.zshrc`):**
    ```zsh
    # --- Tabplexer Tab Status ---
    _update_tabplexer_status() {
      typeset -gx TABPLEXER_STATUS
      if [ -f "$HOME/.tabplexer_session.json" ]; then
        TABPLEXER_STATUS=$(jq -r '.status' "$HOME/.tabplexer_session.json")
      else
        TABPLEXER_STATUS=""
      fi
    }
    autoload -U add-zsh-hook
    add-zsh-hook precmd _update_tabplexer_status
    _update_tabplexer_status
    # --- End Tabplexer Tab Status ---
    ```

    *   **Using the stock Zsh prompt:** If you are not managing a custom prompt, append the status to the built-in prompt by updating `PROMPT` right after the snippet above:

        ```zsh
        PROMPT='${TABPLEXER_STATUS} '$PROMPT
        ```

        This keeps your default prompt intact while prefixing the active tab indicator.

    *   **Using third-party prompts (Starship, Oh My Zsh themes, Pimp my Prompt, etc.):** Leave the `PROMPT` assignment to your theme, but expose the `TABPLEXER_STATUS` environment variable so your prompt manager can render it. For example, with Starship add this to `~/.config/starship.toml`:

        ```toml
        [custom.tabplexer]
        command = 'echo -n ${TABPLEXER_STATUS}'
        when = 'test -n "${TABPLEXER_STATUS}"'
        format = '[$output ](bold cyan)'
        ```

        Then include `"$TABPLEXER_STATUS"` (or the custom module) wherever your prompt framework allows.


    **For Bash (`~/.bashrc`):**
    ```bash
    # --- Tabplexer Tab Status ---
    _set_tabplexer_prompt() {
      local TABPLEXER_STATUS=""
      if [ -f "$HOME/.tabplexer_session.json" ]; then
        TABPLEXER_STATUS=$(jq -r '.status' "$HOME/.tabplexer_session.json")
      fi
      export TABPLEXER_STATUS
      PS1="\[\033[36m\]${TABPLEXER_STATUS}\[\033[0m\] ${ORIGINAL_PS1}"
    }
    if [ -z "${ORIGINAL_PS1+x}" ]; then
      ORIGINAL_PS1=$PS1
    fi
    if [[ ! "$PROMPT_COMMAND" =~ _set_tabplexer_prompt ]]; then
      PROMPT_COMMAND="_set_tabplexer_prompt;${PROMPT_COMMAND}"
    fi
    # --- End Tabplexer Tab Status ---
    ```

    *   **Using the default Bash prompt:** The snippet above saves your original prompt the first time it runs and prefixes it with the Tabplexer status, so no additional changes are required.

    *   **Using third-party Bash prompts (Starship, Liquid Prompt, etc.):** Keep the function so `TABPLEXER_STATUS` is refreshed, but let your prompt framework handle `PS1`. For Starship, for example, add the custom module shown in the Zsh section and reference it from your theme configuration.

## Usage

*   **Start a session:** Open a terminal and run `/path/to/your/tabs.py start`.
*   **New Tab:** Use `Ctrl+Shift+T`.
*   **Switch Tabs:** Use `Ctrl+Shift+Left` and `Ctrl+Shift+Right`.
*   **End a session:** Run `/path/to/your/tabs.py end`. This will close all windows associated with the session.

The session file keeps track of the active window and also stores a `[current/total]`
status string under the `status` key. This value is refreshed automatically
whenever you create, close, or switch between tabs, so your shell prompt remains
accurate even after manually closing windows.
