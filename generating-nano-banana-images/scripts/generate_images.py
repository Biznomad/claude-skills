#!/usr/bin/env python3
"""
Nano Banana Image Generator
Automates bulk image generation via Google AI Studio using Playwright.
Supports Nano Banana (free) and Nano Banana Pro (paid/Ultra).
"""

import argparse
import json
import os
import sys
import time
import glob
import shutil
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("ERROR: playwright not installed. Run: pip3 install playwright")
    sys.exit(1)

# Aspect ratio mapping
ASPECT_RATIOS = {
    "square": "1:1",
    "portrait": "3:4",
    "story": "9:16",
}

MODEL_URLS = {
    "nano-banana": "https://aistudio.google.com/prompts/new_chat?model=gemini-2.5-flash-image",
    "nano-banana-pro": "https://aistudio.google.com/prompts/new_chat?model=gemini-3-pro-image-preview",
}

DOWNLOADS_DIR = os.path.expanduser("~/Downloads")


def find_latest_download(before_files: set, timeout: int = 120) -> str | None:
    """Wait for a new file to appear in Downloads."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        current = set(glob.glob(os.path.join(DOWNLOADS_DIR, "Generated Image*.png")))
        new_files = current - before_files
        if new_files:
            # Wait a moment for download to finish
            time.sleep(1)
            return max(new_files, key=os.path.getmtime)
        time.sleep(2)
    return None


def kill_chrome():
    """Kill existing Chrome processes to avoid Playwright conflicts."""
    os.system('pkill -9 "Google Chrome" 2>/dev/null')
    time.sleep(2)
    # Remove singleton lock
    lock_pattern = os.path.expanduser("~/Library/Caches/ms-playwright/*/SingletonLock")
    for lock in glob.glob(lock_pattern):
        try:
            os.remove(lock)
        except OSError:
            pass


def generate_images(prompts_file: str, output_dir: str, model: str,
                    start_from: int = 0, chrome_profile: str | None = None):
    """Generate images from a prompts JSON file."""
    # Load prompts
    with open(prompts_file) as f:
        prompts = json.load(f)

    os.makedirs(output_dir, exist_ok=True)

    total = len(prompts)
    if start_from > 0:
        prompts = prompts[start_from:]
        print(f"Resuming from prompt {start_from + 1}/{total}")

    print(f"\n{'='*60}")
    print(f"Nano Banana Image Generator")
    print(f"Model: {model}")
    print(f"Prompts: {len(prompts)} remaining of {total}")
    print(f"Output: {output_dir}")
    print(f"{'='*60}\n")

    # Kill Chrome first
    print("Closing existing Chrome sessions...")
    kill_chrome()

    # Set up Chrome profile - use MCP Playwright profile (already authenticated)
    if chrome_profile is None:
        # Try the MCP Playwright profile first (already has Google auth)
        mcp_profile = os.path.expanduser(
            "~/Library/Caches/ms-playwright/mcp-chrome-438dc2f"
        )
        if os.path.exists(mcp_profile):
            chrome_profile = mcp_profile
        else:
            chrome_profile = os.path.expanduser(
                "~/Library/Caches/ms-playwright/nano-banana-profile"
            )

    model_url = MODEL_URLS.get(model, MODEL_URLS["nano-banana"])
    results = {"success": [], "failed": []}

    with sync_playwright() as p:
        print("Launching Chrome...")
        browser = p.chromium.launch_persistent_context(
            chrome_profile,
            channel="chrome",
            headless=False,
            viewport={"width": 1400, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        # Navigate to AI Studio
        print(f"Navigating to AI Studio ({model})...")
        page.goto(model_url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)

        # Wait for AI Studio to load (may need extra time for auth redirect)
        print("Waiting for AI Studio to load...")
        for attempt in range(3):
            try:
                page.wait_for_selector(
                    'textarea, [role="textbox"], [placeholder*="prompt"]',
                    timeout=20000,
                )
                print("AI Studio loaded successfully")
                break
            except PWTimeout:
                if attempt < 2:
                    print(f"  Retrying... (attempt {attempt + 2}/3)")
                    page.reload(wait_until="domcontentloaded", timeout=60000)
                    time.sleep(5)
                else:
                    print("ERROR: AI Studio did not load after 3 attempts.")
                    print("Ensure you are logged into Google in this Chrome profile.")
                    browser.close()
                    sys.exit(1)

        for idx, prompt_data in enumerate(prompts):
            prompt_id = prompt_data["id"]
            fmt = prompt_data.get("format", "square")
            prompt_text = prompt_data["prompt"]
            aspect = ASPECT_RATIOS.get(fmt, "1:1")

            print(f"\n--- [{start_from + idx + 1}/{total}] {prompt_id} ({fmt} → {aspect}) ---")

            try:
                # Start a new chat for each image
                if idx > 0:
                    page.goto(model_url, wait_until="domcontentloaded", timeout=60000)
                    time.sleep(3)

                # Set aspect ratio
                try:
                    ar_combo = page.locator('[role="combobox"]').filter(has_text="Aspect ratio").or_(
                        page.get_by_role("combobox", name="Aspect ratio")
                    ).first
                    if ar_combo.is_visible(timeout=3000):
                        ar_combo.click()
                        time.sleep(0.5)
                        # Select the right option
                        option = page.get_by_role("option", name=aspect)
                        if option.is_visible(timeout=2000):
                            option.click()
                            time.sleep(0.5)
                            print(f"  Aspect ratio set to {aspect}")
                        else:
                            print(f"  Warning: Aspect ratio {aspect} not found, using default")
                            page.keyboard.press("Escape")
                except Exception as e:
                    print(f"  Warning: Could not set aspect ratio: {e}")

                # Enter prompt
                textbox = page.get_by_role("textbox", name="Enter a prompt").or_(
                    page.locator("textarea")
                ).first
                textbox.click()
                time.sleep(0.3)
                textbox.fill(prompt_text)
                time.sleep(0.5)

                # Snapshot downloads before
                before_files = set(glob.glob(os.path.join(DOWNLOADS_DIR, "Generated Image*.png")))

                # Click Run (use type="submit" to avoid matching other buttons with "run" in name)
                run_btn = page.locator('button[type="submit"]').first
                if run_btn.is_visible(timeout=3000):
                    run_btn.click()
                else:
                    # Try pressing Cmd+Enter
                    textbox.press("Meta+Enter")

                print(f"  Generating image...")

                # Wait for generation to complete
                # Look for the Stop button to appear then disappear
                try:
                    page.get_by_role("button", name="Stop").wait_for(state="visible", timeout=10000)
                    page.get_by_role("button", name="Stop").wait_for(state="hidden", timeout=120000)
                except PWTimeout:
                    # Maybe it completed very fast
                    time.sleep(5)

                time.sleep(2)

                # Check for generated image
                img = page.locator('img[alt*="Generated Image"]').first
                if not img.is_visible(timeout=10000):
                    print(f"  ERROR: No image generated for {prompt_id}")
                    results["failed"].append(prompt_id)
                    continue

                # Click on the image to open preview
                img.click()
                time.sleep(1)

                # Click download
                download_btn = page.get_by_role("button", name="Download")
                if download_btn.is_visible(timeout=5000):
                    with page.expect_download(timeout=30000) as download_info:
                        download_btn.click()
                    download = download_info.value
                    # Save to output directory
                    out_path = os.path.join(output_dir, f"{prompt_id}.png")
                    download.save_as(out_path)
                    fsize = os.path.getsize(out_path) / 1024 / 1024
                    print(f"  SAVED: {out_path} ({fsize:.1f} MB)")
                    results["success"].append(prompt_id)
                else:
                    # Fallback: check Downloads folder
                    print(f"  Download button not found, checking Downloads folder...")
                    new_file = find_latest_download(before_files, timeout=30)
                    if new_file:
                        out_path = os.path.join(output_dir, f"{prompt_id}.png")
                        shutil.move(new_file, out_path)
                        fsize = os.path.getsize(out_path) / 1024 / 1024
                        print(f"  SAVED: {out_path} ({fsize:.1f} MB)")
                        results["success"].append(prompt_id)
                    else:
                        print(f"  ERROR: Could not download {prompt_id}")
                        results["failed"].append(prompt_id)

                # Close preview if open
                try:
                    close_btn = page.get_by_role("button", name="Close")
                    if close_btn.is_visible(timeout=2000):
                        close_btn.click()
                except Exception:
                    pass

                # Rate limit delay
                time.sleep(3)

            except Exception as e:
                print(f"  ERROR on {prompt_id}: {e}")
                results["failed"].append(prompt_id)
                continue

        browser.close()

    # Summary
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Success: {len(results['success'])}/{total}")
    if results["failed"]:
        print(f"Failed:  {', '.join(results['failed'])}")
    print(f"Output:  {output_dir}")

    # Save results
    results_path = os.path.join(output_dir, "_generation_results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results: {results_path}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Generate images via Google AI Studio Nano Banana"
    )
    parser.add_argument("--prompts", required=True, help="Path to prompts JSON file")
    parser.add_argument("--output", default="./out", help="Output directory")
    parser.add_argument(
        "--model",
        default="nano-banana",
        choices=["nano-banana", "nano-banana-pro"],
        help="Model to use",
    )
    parser.add_argument(
        "--start-from", type=int, default=0, help="Resume from prompt index"
    )
    parser.add_argument("--chrome-profile", help="Chrome user data directory")

    args = parser.parse_args()

    if not os.path.exists(args.prompts):
        print(f"ERROR: Prompts file not found: {args.prompts}")
        sys.exit(1)

    generate_images(
        prompts_file=args.prompts,
        output_dir=args.output,
        model=args.model,
        start_from=args.start_from,
        chrome_profile=args.chrome_profile,
    )


if __name__ == "__main__":
    main()
