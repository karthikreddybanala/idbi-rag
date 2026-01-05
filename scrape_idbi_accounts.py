import os
import requests
from bs4 import BeautifulSoup
import time

# Folder to save scraped text files
os.makedirs("data", exist_ok=True)

BASE_URL = "https://www.idbi.bank.in/personal-banking/"

# Structure of the sections and sub-sections you mentioned
ACCOUNT_STRUCTURE = {
    "Savings Account": [
        "Advantage Account",
        "Advantage Plus Account",
        "Advantage DIVA Account",
        "Advantage Superior Senior Citizen Account",
        "Advantage Prime Account",
        "Advantage Kids Account",
        "Advantage Bonanza Account",
        "Savings Account Using Video KYC",
        "Small Account - Relaxed KYC",
        "Basic Savings Account - Complete KYC",
        "Pension Savings Account (Central Govt. Emp)",
        "Capital Gain Account Scheme"
    ],
    "Fixed Deposit Account": [
        "Suvidha Fixed Deposit",
        "Suvidha Tax Saving Fixed Deposit",
        "Systematic Savings Plan (SSP/SSP Plus)",
        "Floating Rate Term Deposit",
        "Vasundhara Green Deposit"
    ],
    "Salary Accounts": [
        "Salary Account Overview",
        "Platinum Salary Account",
        "Gold Salary Account",
        "Silver Salary Account",
        "Bronze Salary Account",
        "Pride Salary Account",
        "Indian Army Salary Account",
        "Indian Navy Salary Account"
    ],
    "Current Account": [
        "Elite Plus Business Account",
        "Umang Business Account",
        "Unnati Business Account",
        "Gram Unnati Business Account",
        "eMerchant Current Account"
    ],
    "Kutumb Family Banking": []
}

# Helper to clean filenames
def clean_filename(name):
    return name.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "").replace("-", "_")

# Function to scrape text from URL
def scrape_page(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        # Extract all text
        text = soup.get_text(separator="\n", strip=True)
        return text
    except Exception as e:
        print(f"⚠️ Failed to scrape {url}: {e}")
        return ""

# Function to save text
def save_text(filename, content):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    for main_account, sub_accounts in ACCOUNT_STRUCTURE.items():
        main_filename = f"data/{clean_filename(main_account)}.txt"
        print(f"🏦 Processing: {main_account}")

        # Main page
        main_url = BASE_URL + clean_filename(main_account).lower() + ".aspx"
        text = scrape_page(main_url)
        if text:
            save_text(main_filename, text)
            print(f"✅ Saved main account: {main_filename}")
        else:
            print(f"⚠️ Skipped {main_account}, no content found")

        # Sub-accounts
        for sub in sub_accounts:
            sub_filename = f"data/{clean_filename(main_account)}_{clean_filename(sub)}.txt"
            sub_url = BASE_URL + clean_filename(sub).lower() + ".aspx"
            text = scrape_page(sub_url)
            if text:
                save_text(sub_filename, text)
                print(f"   ↳ ✅ Saved sub-account: {sub}")
            else:
                print(f"   ↳ ⚠️ No content for: {sub}")
            time.sleep(1)

if __name__ == "__main__":
    main()
