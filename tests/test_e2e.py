import pytest
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5000"

@pytest.fixture
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        yield browser
        browser.close()

@pytest.fixture
def page(browser):
    context=browser.new_context()
    page=context.new_page()
    yield page
    context.close()

def test_add_a_new_book(page):
    page.goto(f"{BASE_URL}/add_book")
    page.fill('input[name="title"]', "E2E Book Test")
    page.fill('input[name="author"]', "E2E Author")
    page.fill('input[name="isbn"]', "1234567891055")
    page.fill('input[name="total_copies"]', "3")

    page.click("text=Add Book to Catalog")

    page.wait_for_timeout(500)
    assert "Book added" in page.content() or "success" in page.content().lower()

    page.goto(f"{BASE_URL}/catalog")
    body = page.inner_text("body")

    assert "E2E Book Test" in body
    assert "E2E Author" in body

def test_borrow_a_book(page):
    page.goto(F"{BASE_URL}/catalog")

    page.fill('input[name="patron_id"]', "123456")

    page.click("text=Borrow")

    page.wait_for_timeout(500)
    body=page.inner_text("body")
    assert "Borrow" in body or "success" in body.lower()