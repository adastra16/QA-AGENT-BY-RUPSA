#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pathlib
import time
import os

# -----------------------------
# 1) Launch Chrome
# -----------------------------
driver = webdriver.Chrome()

# -----------------------------
# 2) Load checkout.html
# -----------------------------
checkout_path = pathlib.Path("uploaded_docs/checkout.html").absolute()
driver.get(f"file:///{checkout_path.as_posix()}")

wait = WebDriverWait(driver, 10)

# -----------------------------
# 3) Helper to find discount input with fallback selectors
# -----------------------------
def find_with_fallback():
    selectors = [
        (By.ID, "discount-code"),
        (By.NAME, "discount-code"),
        (By.NAME, "discount"),
        (By.CSS_SELECTOR, "input[id*='discount']"),
        (By.CSS_SELECTOR, "input[name*='discount']"),
        (By.XPATH, "//input[contains(translate(@id,'DISCOUNT','discount'),'discount')]"),
        (By.XPATH, "//input[contains(translate(@name,'DISCOUNT','discount'),'discount')]"),
        (By.CSS_SELECTOR, "input[placeholder*='discount']"),
    ]

    for by, sel in selectors:
        try:
            return wait.until(EC.presence_of_element_located((by, sel)))
        except:
            pass

    return None

# -----------------------------
# 4) Execute test case
# -----------------------------
try:
    time.sleep(0.5)

    discount_input = find_with_fallback()

    if discount_input is None:
        debug_dir = pathlib.Path("selenium_debug")
        debug_dir.mkdir(exist_ok=True)

        screenshot_path = debug_dir / "no_discount_element.png"
        html_path = debug_dir / "page_source.html"

        driver.save_screenshot(str(screenshot_path))
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        raise Exception(f"Could not find discount input. Debug saved.")

    discount_input.clear()
    discount_input.send_keys("DISCOUNT50")

    button_selectors = [
        (By.ID, "apply-discount"),
        (By.CSS_SELECTOR, "button.apply-discount"),
        (By.XPATH, "//button[contains(translate(.,'APPLY','apply'),'apply')]"),
    ]

    clicked = False
    for by, sel in button_selectors:
        try:
            btn = wait.until(EC.element_to_be_clickable((by, sel)))
            btn.click()
            clicked = True
            break
        except:
            pass

    if not clicked:
        discount_input.send_keys(Keys.RETURN)

    print("\n✓ Test Completed\n")

except Exception as e:
    print("\n✗ Test failed:", e, "\n")

finally:
    driver.quit()
