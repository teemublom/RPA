import pandas as pd
from playwright.sync_api import sync_playwright
from playwright.sync_api import expect

df = pd.read_excel('challenge.xlsx', dtype=str)
df.columns = df.columns.str.strip()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://rpachallenge.com/")
    page.get_by_role("button", name="Start").click()
    for row_tuple in df.iterrows():
        #row_tuple == (index, row_data)
        row = row_tuple[1]
        for col in df.columns:
            page.get_by_text(col).locator('../input').fill(row[col])
        page.get_by_role("button", name="submit").click()
    expect(page.get_by_text('Congratulations!')).to_be_visible()
    print(page.get_by_text('Your success rate').text_content())
    browser.close()