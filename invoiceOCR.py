from PIL import Image
from datetime import date, datetime
from playwright.sync_api import sync_playwright, expect

import pandas as pd
import re
import pytesseract
import requests
import io
import config

pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD
dateformat = '%d-%m-%Y'

def img2str(filename: str) -> str:
    return pytesseract.image_to_string(Image.open(filename), config='-l eng')

def extract_date(text: str) -> str:
    # Two types of dates, "YYYY-MM-DD" and "Month_abbreviation DD, YYYY"
    match = re.search(r'\d{4}-\d{2}-\d{2}', text)
    if match:
        result = date.fromisoformat(match[0])
        return result.strftime(dateformat)
    match = re.search(r'Date:\s*([A-Z][a-z]{2} \d{1,2}, \d{4})', text)
    assert match != None
    result = datetime.strptime(match.group(1), '%b %d, %Y').date()
    return result.strftime(dateformat)

def extract_total_due(text: str) -> float:
    match = re.search(r'Total:\s*\$(\d{1,3},)*\d{1,3}.\d\d', text)
    if match:
        result = match[0].split('$')[1]
        result = result.replace(',', '')
        return float(result)
    match = re.search(r'Total\s*(\d+.\d\d)', text)
    assert match != None
    return float(match.group(1))

def extract_invoice_number(text: str) -> int:
    match = re.search(r'INVOICE\s*#\s*(\d+)', text, flags=re.IGNORECASE)
    return int(match.group(1))

def extract_company_name(text: str) -> str:
    # Janky solution, but we only need to find one of two possible company names
    match = re.search(r'^Aenean LLC', text)
    if match:
        return match[0]
    match = re.search(r'\n(Sit Amet Corp.)', text)
    assert match != None
    return match.group(1)

def extract_data(text) -> list:
    company_name = extract_company_name(text)
    invoice_number = extract_invoice_number(text)
    invoice_date = extract_date(text)
    total_due = extract_total_due(text)
    return {'company_name':company_name, 'invoice_number':invoice_number,
             'invoice_date':invoice_date, 'total_due':total_due}

def main():
    with sync_playwright() as p:
        with open('data/example.csv') as f:
            cols = f.readline()
        df = pd.DataFrame(columns=cols.strip().split(','))

        browser = p.chromium.launch(slow_mo=50)
        page = browser.new_page()
        home_page = 'https://rpachallengeocr.azurewebsites.net'
        page.goto(home_page)
        page.get_by_role('button', name='START').click()
        table_body = page.locator('tbody')
        row_n = table_body.locator('tr').count()
        for table_idx in range(3):
            for i in range(1,row_n+1):
                row = table_body.locator(f'//tr[{i}]')
                invoice_ID = row.locator(f'//td[2]').text_content()
                due_date = datetime.strptime(row.locator('//td[3]').text_content(), '%d-%m-%Y').date()
                invoice_link = row.locator('//td[4]').get_by_role('link').get_attribute('href')
                if due_date <= date.today():
                    response = requests.get(home_page + invoice_link)
                    assert response.status_code == 200
                    invoice_img = Image.open(io.BytesIO(response.content))
                    extracted_text = pytesseract.image_to_string(invoice_img, config='-l eng')
                    data = extract_data(extracted_text)
                    new_row = pd.DataFrame([[invoice_ID, due_date.strftime(dateformat), data['invoice_number'], data['invoice_date'], 
                                            data['company_name'], "{:.2f}".format(data['total_due'])]], columns=df.columns)
                    df = pd.concat([df, new_row])
            if table_idx < 2: 
                page.locator('//a[@id="tableSandbox_next"]').click()
        df.to_csv('invoice_data.csv', index=False)
        with page.expect_file_chooser() as fc_info:
            page.locator('//input[@type="file"]').click()
        file_chooser = fc_info.value
        file_chooser.set_files('invoice_data.csv')
        expect(page.get_by_text('CONGRATS!')).to_be_visible()
        print(page.get_by_text('You beat the challenge').text_content())
        browser.close()

if __name__ == '__main__':
    main()