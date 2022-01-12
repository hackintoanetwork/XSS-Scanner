#XSS-Scanner
import requests
from urllib.parse import urljoin, urlencode
from bs4 import BeautifulSoup
from pprint import pprint

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

base_url="https://bwapp.hakhub.net"
target_url=f"{base_url}/xss_get.php"
login_url=f"{base_url}/login.php"
xss_payload="xss_payload.txt"

def get_cookie():
    with requests.Session()  as s:
        data = {
            "login": "bee",
            "password": "bug",
            "security_level": "0",
            "form": "submit",
        }
        s.post(login_url, data=data, verify=False)
        return s.cookies.get_dict()


def load_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("window-size=1920,1080")
    options.add_argument("lang=ko_KR")
    return webdriver.Chrome("drivers/chromedriver.exe", options = options)

def get_forms(url):
    page_content = requests.get(url, cookies=cookies, verify=False).content
    soup = BeautifulSoup(page_content, "html.parser")
    return soup.find_all("form")

def get_form_details(form):
    details={}
    action = form.attrs.get("action")
    method = form.attrs.get("method", "get").lower()
    inputs=[]
    for input_tag in form.find_all("input"):
        input_type = input_tag.attrs.get("type", "text")
        input_name = input_tag.attrs.get("name")
        inputs.append({"type": input_type, "name": input_name})
    details["action"]=action
    details["method"]=method
    details["inputs"]=inputs
    return details

def get_payloads():
    payloads=[]
    with open(xss_payload, "r", encoding="utf-8")as vector_file:
        for vector in vector_file.read().splitlines():
            payloads.append(vector)
    return payloads

def submit_form(form_details, url, value):
    target_url=urljoin(url, form_details["action"])
    joined_url=""
    inputs=form_details["inputs"]
    data={}
    for input in inputs:
        if input["type"]=="text" or input["type"]=="search":
            input["value"]=value
        input_name=input.get("name")
        input_value=input.get("value")
        if input_name and input_value:
            data[input_name]=input_value
    try:
        driver.switch_to.window(driver.current_window_handle)
        if form_details["method"]=="get":
            joined_url=target_url+"?"+urlencode(data)
            driver.get(joined_url)
            WebDriverWait(driver, 0.1).until(expected_conditions.alert_is_present())
            driver.switch_to.alert.accept()
        elif form_details["method"]=="post":
            inject_post_function="""function port_to_url(path, params, method) {
    method=method || "post";
    let form = document.createElement("form");
    form._submit_function_=form.submit;

    form.setAttribute("method", method);
    form.setAttribute("action", path);

    for(let key in params) {
        let hiddenField =document.createElement("input");
        hiddenField.setAttribute("type", "hidden");
        hiddenField.setAttribute("name", key);
        hiddenField.setAttribute("value", params[key]);

        form.appendChild(hiddenField);
    }

    docuemtn.body.appendChild(form);
    form._submit_fuction_();
}
post_to_url(arguments[0, arguments[1]);
            """
            driver.execute_script(inject_post_function, target_url, data)

            WebDriverWait(driver, 0.1).until(expected_conditions.alert_is_present())

            driver.switch_to.alert.accept()
    except Exception:
        pass
    else:
        print("[Found XSS!]")

        if form_details["method"]=="get":
            print("[GET Method]")
            print(urlencode(data))
            print(f"URL: {joined_url}")
        print("="*50)

        check_alert=None
        while check_alert is None:
            try:
                driver.switch_to.alert.accept()
            except:
                check_alert=True
if __name__=="__main__":
    cookies=get_cookie()
    print(f"Cookies: {cookies}")
    driver=load_driver()

    driver.get(login_url)

    for key, value in cookies.items():
        driver.add_cookie({"name": key, "value": value})
    driver.get(target_url)
    forms=get_forms(target_url)

    for form in forms:
        form_details=get_form_details(form)
        print(form_details)
        payloads=get_payloads()
        for payload in payloads:
            submit_form(form_details, base_url, payload)
    driver.close()

