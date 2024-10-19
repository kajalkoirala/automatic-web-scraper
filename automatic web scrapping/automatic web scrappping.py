import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from apscheduler.schedulers.background import BackgroundScheduler

# Case numbers and their corresponding URLs
case_urls = {
    "080-CR-0096": "https://supremecourt.gov.np/lic/sys.php?d=reports&f=case_details&num=1&mode=view&caseno=278473",
    "080-CR-0123": "https://supremecourt.gov.np/lic/sys.php?d=reports&f=case_details&num=1&mode=view&caseno=278797",
    "080-CR-0199": "https://supremecourt.gov.np/lic/sys.php?d=reports&f=case_details&num=1&mode=view&caseno=279673",
    "080-CR-0187": "https://supremecourt.gov.np/lic/sys.php?d=reports&f=case_details&num=1&mode=view&caseno=279599",
    "080-CR-0190": "https://supremecourt.gov.np/lic/sys.php?d=reports&f=case_details&num=1&mode=view&caseno=279607",
    "080-CR-0202": "https://supremecourt.gov.np/lic/sys.php?d=reports&f=case_details&num=1&mode=view&caseno=279741",
    "080-CR-0212": "https://supremecourt.gov.np/lic/sys.php?d=reports&f=case_details&num=1&mode=view&caseno=279991",
    "080-CR-0001": "https://supremecourt.gov.np/lic/sys.php?d=reports&f=case_details&num=1&mode=view&caseno=276885",
    "080-CR-0002": "https://supremecourt.gov.np/lic/sys.php?d=reports&f=case_details&num=1&mode=view&caseno=276893"
}

def convert_empty_to_null(data):
    if isinstance(data, dict):
        return {k: convert_empty_to_null(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_empty_to_null(i) for i in data]
    elif data == "" or data is None:
        return None
    else:
        return data

def fetch_case_data(case_number=None):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Determine which case numbers to fetch
    case_numbers_to_fetch = [case_number] if case_number else case_urls.keys()

    for case_number in case_numbers_to_fetch:
        if case_number not in case_urls:
            print(f"Case number {case_number} not found.")
            continue

        try:
            print(f"Fetching data for case number: {case_number}")
            # Navigate to the URL
            driver.get(case_urls[case_number])

            # Give the page some time to load
            time.sleep(3)

            # Initialize the data structure
            case_data = {
                case_number: {
                    "मुद्दाको विवरण": {},
                    "लगाब मुद्दाहरुको विवरण": [],
                    "तारेख विवरण": [],
                    "मुद्दाको स्थितीको बिस्तृत विवरण": [],
                    "पेशी को विवरण": []
                }
            }

            # Extract "मुद्दाको विवरण"
            try:
                details_rows = driver.find_elements(By.XPATH, "/html/body/div[3]/div/table/tbody/tr[position() <= 15 and position() != 12]")
                for row in details_rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 2:
                        key = cols[0].text.strip().replace(':', '').strip()
                        value = cols[1].text.strip() if cols[1].text.strip() else None  # Set empty value to None
                        case_data[case_number]["मुद्दाको विवरण"][key] = value
            except Exception as e:
                print(f"Error extracting मुद्दाको विवरण for {case_number}: {e}")

            # Extract "लगाब मुद्दाहरुको विवरण"
            try:
                rows = driver.find_elements(By.XPATH, "//table[contains(@class, 'table-bordered')][1]/tbody/tr[td]")  # Assuming this is the first table for linked cases
                for row in rows[1:]:  
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 6:
                        linked_case = {
                            "दर्ता नँ .": cols[0].text.strip() or None,
                            "दर्ता मिती": cols[1].text.strip() or None,
                            "मुद्दा": cols[2].text.strip() or None,
                            "वादीहरु": cols[3].text.strip() or None,
                            "प्रतिवादीहरु": cols[4].text.strip() or None,
                            "हालको स्थिती": cols[5].text.strip() or None
                        }
                        case_data[case_number]["लगाब मुद्दाहरुको विवरण"].append(linked_case)
            except Exception as e:
                print(f"Error extracting लगाब मुद्दाहरुको विवरण for {case_number}: {e}")

            # Extract "तारेख विवरण"
            try:
                rows = driver.find_elements(By.XPATH, "//tbody/tr[td[1][text()='तारेख मिती']]/following-sibling::tr[td]")
                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 3:
                        date_detail = {
                            "तारेख मिती": cols[0].text.strip() or None,
                            "विवरण": cols[1].text.strip() or None,
                            "तारेखको किसिम": cols[2].text.strip() or None
                        }
                        case_data[case_number]["तारेख विवरण"].append(date_detail)
            except Exception as e:
                print(f"Error extracting तारेख विवरण for {case_number}: {e}")

            # Extract "मुद्दाको स्थितीको बिस्तृत विवरण"
            try:
                rows = driver.find_elements(By.XPATH, "//table[contains(@class, 'table-bordered')][2]/tbody/tr[td]")  # Assuming this is the second table
                for row in rows[1:]:  
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 3:
                        status_detail = {
                            "मिती": cols[0].text.strip() or None,
                            "विवरण": cols[1].text.strip() or None,
                            "स्थिती": cols[2].text.strip() or None
                        }
                        case_data[case_number]["मुद्दाको स्थितीको बिस्तृत विवरण"].append(status_detail)
            except Exception as e:
                print(f"Error extracting मुद्दाको स्थितीको बिस्तृत विवरण for {case_number}: {e}")

            # Extract "पेशी को विवरण"
            try:
                rows = driver.find_elements(By.XPATH, "//tbody/tr[td[1][text()='सुनवाइ मिती']]/following-sibling::tr")
                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 4:
                        hearing_detail = {
                            "सुनवाइ मिती": cols[0].text.strip() or None,
                            "न्यायाधीशहरू": "\n".join([judge.strip() for judge in cols[1].text.strip().split("\n")]) or None,
                            "मुद्दाको स्थिती": cols[2].text.strip() or None,
                            "आ देश /फैसलाको किसिम": cols[3].text.strip() or None
                        }
                        case_data[case_number]["पेशी को विवरण"].append(hearing_detail)
            except Exception as e:
                print(f"Error extracting पेशी को विवरण for {case_number}: {e}")

            
            cleaned_data = convert_empty_to_null(case_data)

            print(json.dumps(cleaned_data, ensure_ascii=False, indent=4))

            #save json
            with open(f"{case_number}_data.json", "w", encoding='utf-8') as json_file:
                json.dump(cleaned_data, json_file, ensure_ascii=False, indent=4)

        except Exception as e:
            print(f"Error fetching data for case number {case_number}: {e}")


    driver.quit()

def schedule_scraping():
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_case_data, 'cron', hour=10, minute=30)
    scheduler.add_job(fetch_case_data, 'cron', hour=17, minute=30)
    scheduler.start()

    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

schedule_scraping()


#----------Note if you dont want to wait for the schedule scraping, run this with uncommenting. --- (extra)

#fetch_case_data()




