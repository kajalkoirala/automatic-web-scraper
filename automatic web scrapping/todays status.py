

import requests
from bs4 import BeautifulSoup

def scrape_daily_status(url):
    response = requests.get(url, verify=False)
    soup = BeautifulSoup(response.content, 'html.parser')
    daily_status_div = soup.find('div', class_='col-md-4 daily-status')
    table = daily_status_div.find('table')
    rows = table.find_all('tr')
    daily_status = {}
    for row in rows:
        cols = row.find_all(['th', 'td'])
        if len(cols) > 1:
            key = cols[0].text.strip()
            value = cols[1].text.strip()
            daily_status[key] = value
    return daily_status

def post_case_number(url, case_number):
    payload = {"regno": case_number}
    response = requests.post(url, data=payload, verify=False)
    return response

def main():
    url = "https://supremecourt.gov.np/web/"
    daily_status = scrape_daily_status(url)
    print("Today's Case Status:")
    for key, value in daily_status.items():
        print(f"{key}: {value}")

    # case_number_url = "https://supremecourt.gov.np/lic/sys.php?d=reports&f=case_details"
    # case_number = input("Enter the case number: ")
    # response = post_case_number(case_number_url, case_number)
    # print("Response Status Code:", response.status_code)
    # print("Response Content:", response.content)

if __name__ == "__main__":
    main()
