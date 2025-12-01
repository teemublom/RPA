from PIL import Image
import invoiceOCR as iv
from datetime import date

import pytesseract
import config
pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD

sample1_text = iv.img2str('sample1.jpg')
sample2_text = iv.img2str('sample2.jpg')

class TestExtractDate:
    def test_one(self):
        assert iv.extract_date(sample1_text) == "30-06-2019"

    def test_two(self):
        assert iv.extract_date(sample2_text) == "28-06-2019"

class TestExtractTotal:
    def test_one(self):
        assert iv.extract_total_due(sample1_text) == 17310.00
    
    def test_two(self):
        assert iv.extract_total_due(sample2_text) == 1800.00
    
    def test_long_number(self):
        assert iv.extract_total_due('The final Total:   $1,333,666.50') == 1333666.50

class TestExtractInvoiceNumber:
    def test_one(self):
        assert iv.extract_invoice_number(sample1_text) == 11577
    
    def test_two(self):
        assert iv.extract_invoice_number(sample2_text) == 284228

class TestExtractCompanyName:
    def test_one(self):
        assert iv.extract_company_name(sample1_text) == 'Sit Amet Corp.'
    
    def test_two(self):
        assert iv.extract_company_name(sample2_text) == 'Aenean LLC'