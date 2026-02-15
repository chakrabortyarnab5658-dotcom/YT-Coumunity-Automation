import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


POST_IDEA_FILE = Path("post_ideas.json")
STATE_FILE = Path("post_state.json")
DEFAULT_WAIT_SECONDS = 20


@dataclass
class PostIdea:
    post_type: str
    text: str
    poll_options: Optional[List[str]] = None
    schedule_datetime: Optional[str] = None


class YouTubeCommunityAutomator:
    """Automates YouTube Community post creation in YouTube Studio."""

    def __init__(self, driver: Chrome, wait_seconds: int = DEFAULT_WAIT_SECONDS) -> None:
        self.driver = driver
        self.wait = WebDriverWait(driver, wait_seconds)

    def open_studio_for_manual_login(self) -> None:
        self.driver.get("https://studio.youtube.com")
        print("\nPlease complete login manually in the opened Chrome window.")
        print("After login, go to YouTube Studio -> Content -> Posts (Community tab).")
        input("Press Enter here when you are ready to continue...")

    def create_post_from_idea(self, idea: PostIdea) -> None:
        self._open_post_composer()
        self._add_text(idea.text)

        if idea.post_type.lower() == "poll":
            self._configure_poll(idea.poll_options or [])

        if idea.schedule_datetime:
            self._schedule_post(idea.schedule_datetime)
        else:
            self._publish_now()

    def _open_post_composer(self) -> None:
        self._click_first([
            (By.XPATH, "//button[.//span[contains(.,'Create')]]"),
            (By.XPATH, "//ytcp-button[contains(@label, 'Create')]"),
            (By.XPATH, "//*[contains(text(),'Create post')]/ancestor::button"),
            (By.XPATH, "//button[contains(., 'Create post')]"),
        ], "Could not open the post composer. Please verify you are on the Posts page.")
        time.sleep(1)

    def _add_text(self, text: str) -> None:
        field = self._find_first([
            (By.CSS_SELECTOR, "#textbox"),
            (By.XPATH, "//div[@id='textbox' and @contenteditable='true']"),
            (By.XPATH, "//ytcp-social-suggestions-textbox//div[@contenteditable='true']"),
        ], "Could not locate text input box for the post.")
        field.click()
        field.send_keys(text)

    def _configure_poll(self, options: List[str]) -> None:
        if len(options) != 4:
            raise ValueError("Poll post requires exactly 4 options.")

        self._click_first([
            (By.XPATH, "//button[contains(., 'Poll')]"),
            (By.XPATH, "//*[contains(text(),'Create poll')]/ancestor::button"),
            (By.XPATH, "//ytcp-ve[contains(@class, 'poll')]"),
        ], "Could not switch composer to poll mode.")

        input_boxes = self.wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//input[contains(@aria-label, 'Option') or contains(@placeholder, 'Option')]")
            )
        )

        if len(input_boxes) < 4:
            raise RuntimeError("Poll option inputs were not found correctly.")

        for idx, option_text in enumerate(options[:4]):
            box = input_boxes[idx]
            box.clear()
            box.send_keys(option_text)

    def _schedule_post(self, schedule_datetime: str) -> None:
        dt = datetime.strptime(schedule_datetime, "%Y-%m-%d %H:%M")

        self._click_first([
            (By.XPATH, "//button[contains(., 'Schedule')]"),
            (By.XPATH, "//ytcp-button[contains(@label, 'Schedule')]"),
        ], "Could not open schedule options.")

        date_input = self._find_first([
            (By.XPATH, "//input[contains(@aria-label, 'Date') or contains(@placeholder, 'Date') ]"),
            (By.CSS_SELECTOR, "input[type='date']"),
        ], "Could not locate scheduling date input.")
        time_input = self._find_first([
            (By.XPATH, "//input[contains(@aria-label, 'Time') or contains(@placeholder, 'Time')]"),
            (By.CSS_SELECTOR, "input[type='time']"),
        ], "Could not locate scheduling time input.")

        date_input.clear()
        date_input.send_keys(dt.strftime("%m/%d/%Y"))
        time_input.clear()
        time_input.send_keys(dt.strftime("%I:%M %p"))

        self._click_first([
            (By.XPATH, "//button[contains(., 'Done')]"),
            (By.XPATH, "//button[contains(., 'Schedule') and not(@disabled)]"),
            (By.XPATH, "//ytcp-button[contains(@label, 'Schedule') and not(contains(@disabled, 'disabled'))]"),
        ], "Could not finalize schedule action.")

        print(f"Scheduled post for {dt.isoformat(' ', timespec='minutes')}")

    def _publish_now(self) -> None:
        self._click_first([
            (By.XPATH, "//button[contains(., 'Post')]"),
            (By.XPATH, "//button[contains(., 'Publish')]"),
            (By.XPATH, "//ytcp-button[contains(@label, 'Post') or contains(@label, 'Publish')]"),
        ], "Could not publish the post.")
        print("Published post immediately.")

    def _find_first(self, locators: List[tuple], error_message: str):
        for locator in locators:
            try:
                return self.wait.until(EC.presence_of_element_located(locator))
            except TimeoutException:
                continue
        raise RuntimeError(error_message)

    def _click_first(self, locators: List[tuple], error_message: str) -> None:
        for locator in locators:
            try:
                element = self.wait.until(EC.element_to_be_clickable(locator))
                element.click()
                return
            except TimeoutException:
                continue
        raise RuntimeError(error_message)


def load_post_ideas(path: Path) -> List[PostIdea]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Create it first (see README.md for sample format)."
        )

    raw = json.loads(path.read_text(encoding="utf-8"))
    posts = []
    for item in raw.get("posts", []):
        posts.append(
            PostIdea(
                post_type=item["type"],
                text=item["text"],
                poll_options=item.get("poll_options"),
                schedule_datetime=item.get("schedule_datetime"),
            )
        )
    return posts


def get_next_post_index(total_posts: int) -> int:
    if total_posts == 0:
        raise ValueError("No post ideas found in JSON.")

    if not STATE_FILE.exists():
        STATE_FILE.write_text(json.dumps({"next_index": 0}, indent=2), encoding="utf-8")

    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    idx = state.get("next_index", 0)
    if idx >= total_posts:
        idx = 0
    return idx


def increment_post_index(current_index: int, total_posts: int) -> None:
    next_index = (current_index + 1) % total_posts
    STATE_FILE.write_text(json.dumps({"next_index": next_index}, indent=2), encoding="utf-8")


def build_driver() -> Chrome:
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    # Do not run headless so manual login is possible.
    return webdriver.Chrome(options=chrome_options)


def main() -> None:
    posts = load_post_ideas(POST_IDEA_FILE)
    current_index = get_next_post_index(len(posts))
    selected_post = posts[current_index]

    print(f"Selected post index: {current_index}")
    print(f"Type: {selected_post.post_type}")

    driver = build_driver()
    automator = YouTubeCommunityAutomator(driver)

    try:
        automator.open_studio_for_manual_login()
        automator.create_post_from_idea(selected_post)
        increment_post_index(current_index, len(posts))
        print("Done. post_state.json updated to the next post.")
    except Exception as exc:
        print(f"Automation failed: {exc}")
        print("Tip: Update locators in automate_youtube_community.py if YouTube Studio UI has changed.")


if __name__ == "__main__":
    main()
