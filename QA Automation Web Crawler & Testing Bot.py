from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, urljoin
import time
import os
import re

# =========================
# SETUP
# =========================
options = Options()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

base_url = "https://example.com"

visited = set()
queue = [base_url]

report_rows = []

# =========================
# SCREENSHOT FOLDER
# =========================
SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# =========================
# HELPERS
# =========================
def is_internal(url):
    return urlparse(url).netloc == urlparse(base_url).netloc

def clean(url):
    return url.split("#")[0].rstrip("/")

def is_image(url):
    img_ext = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".bmp", ".ico")
    return url.lower().endswith(img_ext)

def is_tag_or_category(url):
    keywords = ("/tag/", "/category/", "?tag=", "?cat=")
    return any(k in url.lower() for k in keywords)

def is_date_url(url):
    return re.search(r"/\d{4}/\d{2}/\d{2}/", url) is not None

# 🔥 NUMERIC FILTER (ADDED)
def is_numeric_path(url):
    return re.search(r"/\d+/", url) is not None

# =========================
# EXTRACT LINKS
# =========================
def get_links_in_order():
    links = []
    elements = driver.find_elements(By.TAG_NAME, "a")

    for el in elements:
        href = el.get_attribute("href")

        if href:
            full = urljoin(base_url, href)

            # 🔥 ALL FILTERS APPLIED
            if (
                is_internal(full)
                and not is_image(full)
                and not is_tag_or_category(full)
                and not is_date_url(full)
                and not is_numeric_path(full)
            ):
                links.append(clean(full))

    return links

# =========================
# START BOT
# =========================
print("🚀 LINE FLOW QA BOT STARTED...\n")

driver.get(base_url)

print("⚠️ CAPTCHA aaye to solve karo manually")
input("👉 Solve CAPTCHA then press ENTER to continue...\n")

step = 1

# =========================
# MAIN LOOP WITH STOP SUPPORT
# =========================
try:
    while queue:
        url = clean(queue.pop(0))

        if url in visited:
            continue

        try:
            print(f"\n➡️ STEP {step}: Opening {url}")

            driver.get(url)

            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            time.sleep(2)

            visited.add(url)

            title = driver.title

            # =========================
            # SCREENSHOT
            # =========================
            name = url.replace(base_url, "").replace("/", "_")
            if name == "":
                name = "home"

            screenshot = os.path.join(SCREENSHOT_DIR, f"{step}_{name}.png")
            driver.save_screenshot(screenshot)

            print(f"📄 Page Title: {title}")

            report_rows.append(f"""
            <tr>
                <td>{step}</td>
                <td>{url}</td>
                <td>{title}</td>
                <td>PASS</td>
                <td><img src="{screenshot}" width="120"></td>
            </tr>
            """)

            links = get_links_in_order()

            for link in links:
                if link not in visited and link not in queue:
                    queue.append(link)

            step += 1

        except Exception as e:
            print("❌ Error:", url, e)

            report_rows.append(f"""
            <tr>
                <td>{step}</td>
                <td>{url}</td>
                <td>Error</td>
                <td>FAIL</td>
                <td>{str(e)}</td>
            </tr>
            """)

            step += 1

except KeyboardInterrupt:
    print("\n⛔ STOPPED BY USER (CTRL + C)")

# =========================
# ALWAYS RUN (REPORT)
# =========================
finally:
    driver.quit()

    html = f"""
    <html>
    <head>
    <title>LINE FLOW QA REPORT</title>
    <style>
    body {{ font-family: Arial; }}
    table {{ width:100%; border-collapse: collapse; }}
    th, td {{ border:1px solid black; padding:8px; }}
    th {{ background:#eee; }}
    img {{ border:1px solid #ccc; }}
    </style>
    </head>
    <body>

    <h2>🧪 LINE FLOW QA REPORT</h2>
    <p><b>Total Pages Tested:</b> {len(visited)}</p>

    <table>
    <tr>
    <th>Step</th>
    <th>URL</th>
    <th>Title</th>
    <th>Status</th>
    <th>Screenshot</th>
    </tr>

    {''.join(report_rows)}

    </table>

    </body>
    </html>
    """

    with open("QA_Report.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("\n========================")
    print("📊 REPORT GENERATED (PARTIAL OR FULL)")
    print("📄 Pages:", len(visited))
    print("📁 Screenshots: screenshots/")
    print("========================")