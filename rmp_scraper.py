from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
import time
import requests
import json
import urllib.parse

def get_courses_by_subjects(subject_codes, semester, campus, level):
    base_url = "https://sis.rutgers.edu/oldsoc/courses.json"
    subArray = []
    seen_entries = set()

    for subject in subject_codes.split(","):
        subject = subject.strip()
        params = {
            "subject": subject,
            "semester": semester,
            "campus": campus,
            "level": level,
        }
        response = requests.get(base_url, params=params)

        if response.status_code == 200:
            courses = response.json()

            for course in courses:
                course_number = course.get("courseNumber", "Unknown")
                subject_code = course.get("subject", "Unknown")

                if subject_code == "198" and course_number == "494": # independent topics
                    continue

                for section in course.get("sections", []):
                    for instructor in section.get("instructors", []):
                        instructor_name = instructor.get("name", "Unknown")
                        entry = {
                            "courseCode": f"{subject_code},{course_number}",
                            "professor": instructor_name,
                        }
                        tple = (entry["courseCode"], entry["professor"])
                        if tple not in seen_entries:
                            subArray.append(entry)
                            seen_entries.add(tple)
        else:
            print(f"Subject {subject} Error {response.status_code}")

    return subArray

def get_rmp_url(name):
    name = name.split(",")
    fullName = name[0]
    if len(name) == 2:
        fullName = (name[1] + " " + fullName)[1:]
    link = (
        "https://www.ratemyprofessors.com/search/professors/825?q="
        + urllib.parse.quote(fullName)
    )

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    # remove the annoying messages
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(link)

    driver.implicitly_wait(5)

    rmp_prof_links = []
    searchResults = driver.find_elements(By.CSS_SELECTOR, "[class*=SearchResultsPage__StyledResultsWrapper]")
    if not searchResults:
        return rmp_prof_links # no professors found
    # extract all the professor links from the search
    for res in searchResults:
        links = res.find_elements(By.TAG_NAME, "a")
        for link in links:
            href = link.get_attribute("href")
            if href:
                rmp_prof_links.append(href)

    rmp_prof_names = []
    # and all their corresponding names
    searchResults = driver.find_elements(By.CSS_SELECTOR, "[class*=CardName__StyledCardName]")
    for res in searchResults:
        if res.text:
            rmp_prof_names.append(res.text)

    driver.quit()

    profs_list = list(zip(rmp_prof_names, rmp_prof_links))

    # for now, just choose the first professor in the list
    # TODO: in the future, select the closest matching to the professor name
    # because RMP search function is complete trash and puts the wrong prof first
    return profs_list[0][1]

def scrape_reviews(url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    # remove the annoying messages
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)

    driver.implicitly_wait(5)

    # gets rid of ads (possibly)
    ads = driver.find_elements(By.CLASS_NAME, "bx-close")
    if len(ads) > 0:
        try:
            ads[0].click()
        except:
            ads
    # closes the modal overlay to allow button clicks
    try:
        modal = driver.find_element(By.CLASS_NAME, "ReactModal__Overlay")
        close_button = modal.find_element(By.TAG_NAME, "button")
        close_button.click()
        time.sleep(2)
    except NoSuchElementException:
        pass
    # how many times to click the "load more reviews" button
    max_clicks = 3
    click_count = 0
    while click_count < max_clicks:
        try:
            print("CLICKING LOAD MORE RATINGS")
            next_button = driver.find_element(By.CSS_SELECTOR, "[class*=PaginationButton__StyledPaginationButton]")
            next_button.click()
            click_count += 1
            time.sleep(2) # wait for button to be ready again
        except NoSuchElementException:
            break

    reviews = []
    comments = driver.find_elements(By.CSS_SELECTOR, "[class*=Comments]")
    for comment in comments:
        if comment.text:
            reviews.append(comment.text)

    driver.quit()
	
    return reviews


def main():
    # subject_codes = "440"
    # semester = "12025"
    # campus = "NB"
    # level = "UG"
    # subArray = get_courses_by_subjects(subject_codes, semester, campus, level)
    # prof_names = set()
    # for object in subArray:
    #     prof_names.add(object["professor"])
    # prof_names = list(prof_names)
    # print(prof_names)

    # for prof_name in prof_names:
    #     get_rmp_url(prof_name)

    profName = "CENTENO"
    url = get_rmp_url(profName)
    # url = get_rmp_url("MOLNAR")
    print(url)
    reviews = scrape_reviews(url)
    print(reviews)

    with open(profName+".txt", "w") as file:
        for review in reviews:
            file.write(f"{review}\n")
	

if __name__ == "__main__":
    main()
