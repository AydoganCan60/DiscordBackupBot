# Discord Project Backup Bot

This Python script automatically backs up your local project folders by creating separate Discord channels for each project, generating webhooks, compressing the projects into RAR archives, splitting them into parts (if necessary), and uploading them to the respective channels via the webhooks.

It's designed for users who want to store backups on Discord without paying for cloud storage, using a bot account and its webhooks.

## Features

*   **Automatic Channel & Webhook Creation:** Creates a dedicated text channel and a webhook for each project on your specified Discord server.
*   **Project Compression:** Compresses each project folder into a single ZIP file.
*   **RAR Splitting:** Uses WinRAR's command-line tool (`rar.exe`) to convert the ZIP into multi-volume RAR archives, splitting them into parts smaller than Discord's file size limit (e.g., 9 MB).
*   **Easy Extraction:** Names the RAR parts as `projectname.part1.rar`, `projectname.part2.rar`, etc., making them easy to extract with WinRAR.
*   **Rate Limit Handling:** Includes built-in delays and checks for Discord API rate limits and file size limits.
*   **Cleanup:** Automatically deletes temporary ZIP and RAR files after uploading.

## Requirements

1.  **Python 3.6+:** Make sure Python is installed on your system.
2.  **`requests` library:** Install using `pip install requests`.
3.  **Discord Bot:** You need to create a Discord bot application and obtain its token. The bot must be invited to your server with `Manage Channels` and `Manage Webhooks` permissions.
4.  **WinRAR:** The `rar.exe` command-line tool must be installed on your system. The script expects it to be either in your system's PATH or you need to specify its full path in the script (`self.rar_path`).

## Setup

1.  **Clone or Download:** Get the project files.
2.  **Install Python Dependencies:**
    ```bash
    pip install requests
    ```
3.  **Create a Discord Bot:**
    *   Go to the [Discord Developer Portal](https://discord.com/developers/applications).
    *   Create a "New Application".
    *   Go to the "Bot" tab and add a bot.
    *   Copy the bot's token.
    *   Go to "OAuth2" -> "URL Generator".
    *   Select scopes: `bot`, `applications.commands`.
    *   Select bot permissions: `Manage Channels`, `Manage Webhooks`, `Send Messages`, `Attach Files`.
    *   Copy the generated URL and open it in your browser to invite the bot to your server.
4.  **Configure the Script:**
    *   Create a `config.json` file in the same directory as `main.py`. It should look like this:
        ```json
        {
            "discord_token": "YOUR_BOT_TOKEN_HERE",
            "server_id": "YOUR_SERVER_ID_HERE",
            "category_id": "OPTIONAL_CATEGORY_ID_HERE"
        }
        ```
        *   Replace `YOUR_BOT_TOKEN_HERE` with the token you copied.
        *   Replace `YOUR_SERVER_ID_HERE` with the ID of the Discord server you invited the bot to (enable Developer Mode in Discord settings, right-click the server icon, and copy the ID).
        *   Optionally, replace `OPTIONAL_CATEGORY_ID_HERE` with the ID of a category where you want the project channels to be created.
    *   **Place Your Backup Files:** Create a folder named `backupfiles` in the same directory. Put each project folder you want to back up directly inside the `backupfiles` folder.
        ```
        your_script_directory/
        ├── main.py
        ├── config.json
        ├── requirements.txt
        └── backupfiles/
            ├── backupfilelol123/
            │   ├── file1.txt
            │   └── ...
            ├── backupfileilikeboys123/
            │   ├── fileA.py
            │   └── ...
            └── ...
        ```
5.  **Configure WinRAR Path (if needed):**
    *   Open `main.py`.
    *   Find the line `self.rar_path = r"C:\Program Files\WinRAR\Rar.exe"`.
    *   If `rar.exe` is in your PATH, you can change it to just `"rar"`. Otherwise, ensure the path points to the correct location of `Rar.exe` on your system.

## Usage

1.  Ensure your `config.json` is set up correctly and your projects are in the `backupfiles` folder.
2.  Run the script from your terminal or command prompt:
    ```bash
    python main.py
    ```
3.  The script will:
    *   Create a new text channel for each project in `backupfiles`.
    *   Create a webhook for each channel.
    *   Compress the project into a ZIP file.
    *   Split the ZIP into RAR parts (e.g., `projectname.part1.rar`, `projectname.part2.rar`) using WinRAR.
    *   Upload each RAR part to its corresponding Discord channel.
    *   Clean up temporary files.

## Notes

*   **File Size Limit:** The script uses a 9 MB part size by default (`max_size_mb=9` in `rar_file`). Adjust this if your bot/webhook has a different effective limit.
*   **Discord API Limits:** The script includes delays (`time.sleep`) to avoid hitting rate limits. You can adjust these if needed, but be cautious.
*   **Webhook Name Restrictions:** The script automatically replaces "discord" in webhook names to comply with Discord's naming rules.
*   **Unicode Errors:** The `subprocess` call for WinRAR is configured to handle potential character encoding issues.

## License

This project is open-source and available under the MIT License.
