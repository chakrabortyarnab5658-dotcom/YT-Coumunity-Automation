# YT-Coumunity-Automation

Automate YouTube Community post creation from a JSON queue using Selenium + Chrome on **Windows**.

## Features

- Manual login flow to YouTube Studio (safe for accounts with 2FA)
- Create a **text post**
- Create a **poll post with 4 options**
- Optional **scheduling** (`YYYY-MM-DD HH:MM`)
- Post ideas stored in `post_ideas.json`
- Automatically picks the next post and updates progress in `post_state.json`

## Project files

- `automate_youtube_community.py` - Main automation script
- `post_ideas.json` - Queue of post ideas
- `post_state.json` - Auto-created state file to track next post index
- `requirements.txt` - Python dependencies

## Prerequisites (Windows)

1. Windows 10/11
2. Google Chrome installed
3. Python 3.10+ installed
4. Internet access and valid YouTube account

> Selenium Manager (built into Selenium 4) automatically downloads/uses a matching ChromeDriver in most cases.

## Setup

Open **Command Prompt** or **PowerShell** in this project folder, then run:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## JSON format

Edit `post_ideas.json`:

```json
{
  "posts": [
    {
      "type": "text",
      "text": "Your text post content",
      "schedule_datetime": "2026-02-20 19:00"
    },
    {
      "type": "poll",
      "text": "Question for the audience",
      "poll_options": ["Option A", "Option B", "Option C", "Option D"],
      "schedule_datetime": "2026-02-22 18:30"
    }
  ]
}
```

Notes:
- `type` must be `text` or `poll`.
- Poll posts must include **exactly 4** `poll_options`.
- `schedule_datetime` is optional. If omitted, the script tries to publish immediately.

## Run

```bash
python automate_youtube_community.py
```

## How it works

1. Script loads posts from `post_ideas.json`.
2. Reads `post_state.json` (or creates it) to select the next post.
3. Opens Chrome to `https://studio.youtube.com`.
4. You log in manually and navigate to **Studio > Content > Posts**.
5. Press Enter in terminal.
6. Script creates text/poll, then publishes now or schedules.
7. `post_state.json` is updated to the next item.

## Important reliability note

YouTube Studio UI changes over time. If a button/input is not found, update locators in:

- `automate_youtube_community.py` methods `_open_post_composer`, `_configure_poll`, `_schedule_post`, `_publish_now`.

## Safety tips

- Test with a secondary/private channel first.
- Keep your post schedule in future times.
- Review posts in Studio after each run.
