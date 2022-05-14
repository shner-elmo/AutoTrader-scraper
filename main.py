import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import traceback


timer_start = time.time()
s = Service('chromedriver.exe')
options = webdriver.ChromeOptions()
options.add_experimental_option('excludeSwitches', ['enable-logging'])
driver = webdriver.Chrome(service=s, options=options)
URL = 'https://www.autotrader.ca/motorcycles-atvs/all/?rcp=15&rcs=0&srt=7&prx=-2&hprc=False&wcp=False&iosp=True&sts=New-Used&showcpo=1&inMarket=basicSearch'
driver.get(URL)

time.sleep(3)
driver.find_element(By.CLASS_NAME, 'close-button').click()
print(f'Time elapsed: {time.time() - timer_start :.2f}')


def get_sublist_index(mylist, char):
    """
    get index of a char in a nested list
    :return: char index
    """
    for sub_list in mylist:
        if char in sub_list:
            return mylist.index(sub_list), sub_list.index(char)
    raise ValueError(f"'{char}' is not in list")


def dict_contains(dict_key, dictionary):
    """
    if dict contains key: return dictionary[dict_key]
    """
    if dict_key in dictionary:
        return dictionary[dict_key]


def click_next_page():
    """
    click the next page
    :return: bool, current_page, next_page, last_page
    """
    page_index_lst = driver.find_elements(By.XPATH, page_list)
    pages_lst = []
    for num, i in zip(range(10), page_index_lst):
        pages_lst.append([i.get_attribute('class'), i.get_attribute('data-page'), i])

    x = get_sublist_index(pages_lst, 'page-item active')
    current_page = pages_lst[x[0]][1]
    x = get_sublist_index(pages_lst, 'last-page page-item')
    last_page = pages_lst[x[0]][1]

    if current_page != last_page:
        x = get_sublist_index(pages_lst, 'page-item active')
        next_page = pages_lst[x[0] + 1][2]
        next_page.click()
        return True, current_page, pages_lst[x[0] + 1][1], last_page
    else:
        print(f'Last page ({last_page})')
        return [False]


page_list = '/html/body/div[3]/div/div[2]/div/div[1]/div[2]/div/div[10]/div/div/ul/li'
table_keys = '/html/body/div[3]/div/div[2]/app-root-vdp-fuji/vdp-fuji-app/section/div[1]/div[1]/div/vdp-specifications-list/div/div/ul/li/span[1]'
table_vals = '/html/body/div[3]/div/div[2]/app-root-vdp-fuji/vdp-fuji-app/section/div[1]/div[1]/div/vdp-specifications-list/div/div/ul/li/span[2]/strong'

variable = True
pages = (None, None, None, None)
error_ids = []
rows = []

while variable:
    try:
        try:
            while True:
                page_listings = driver.find_elements(By.XPATH,
                                                     '/html/body/div[3]/div/div[2]/div/div[1]/div[2]/div/div[13]/div')
                list_ids = [i.get_attribute('id') for i in page_listings if i.get_attribute('id').isdigit()]

                box_link = '/html/body/div[3]/div/div[2]/div/div[1]/div[2]/div/div[13]/div/div[2]/div[2]/div/div/h2/a'
                elements = driver.find_elements(By.XPATH, box_link)
                list_links = [[i.get_attribute('data-list-numerical-position'), i.get_attribute('href')] for i in elements]

                if len(list_links) != 25 and len(list_ids) != 25:
                    time.sleep(0.5)
                else:
                    break

            for link in list_links:
                driver.execute_script(f'window.open("{link[1]}");')
                driver.switch_to.window(driver.window_handles[1])
                time.sleep(3)
                page_id_lst = driver.find_elements(By.XPATH, '/html/body/div/div/div')
                page_id = [x.get_attribute('data-fdmid') for x in page_id_lst if x.get_attribute('data-fdmid')
                           is not None and x.get_attribute('data-fdmid').isdigit()]

                if page_id[0] in list_ids:
                    print(f'(active={pages[1]}, next={pages[2]}, last={pages[3]}), listing id: {page_id[0]}, num position: {link[0]}, scraping: {link[1]}')
                    title = driver.find_element(By.CSS_SELECTOR, 'p.hero-title').text
                    year = int(title.split()[0]) if title.split()[0].isdigit() else None
                    price = driver.find_element(By.CSS_SELECTOR, 'p.hero-price').text.replace(',', '')
                    location = driver.find_element(By.CSS_SELECTOR, 'p.hero-location').text
                    if '|' in location:
                        mileage = float(location.split()[0].replace(',', ''))
                        city = location.split('|')[1]
                    else:
                        mileage = None
                        city = location
                    description = driver.find_element(By.CSS_SELECTOR, '#vdp-collapsible-content-text').text

                    lst_keys = driver.find_elements(By.XPATH, table_keys)
                    lst_vals = driver.find_elements(By.XPATH, table_vals)
                    table_specs = {key.text: val.text for key, val in zip(lst_keys, lst_vals)}
                    status = dict_contains('Status', table_specs)
                    make = dict_contains('Make', table_specs)
                    model = dict_contains('Model', table_specs)

                    rows.append({
                        'listing_id': page_id[0], 'num_pos': link[0], 'href': link[1], 'title': title, 'year': year,
                        'price': price, 'city': city, 'mileage': mileage, 'description': description, 'status': status,
                        'make': make, 'model': model})
                else:
                    print('ERROR! page_id not in list_ids')

                driver.close()
                driver.switch_to.window(driver.window_handles[0])

            out = click_next_page()
            pages = out
            if pages[0] is False:
                variable = False

        except Exception as Error:
            print(f'Error Line: {traceback.format_exc()} \n'
                  f'ERROR!: {Error} \n'
                  f'Rows content: \n', str(rows).replace('}, {', '}, \n{'))
            try:
                error_ids.append({'listing_id': page_id[0], 'num_pos': link[0], 'href': link[1]})
            except:
                print('ERROR! listing_id is None')
            print('Error-ids content: \n', str(error_ids).replace('}, {', '}, \n{'))

    finally:
        df = pd.DataFrame(data=rows)
        df.to_csv('AutoTraderData.csv', index=False, mode='w')

        print('Rows content: \n', str(rows).replace('}, {', '}, \n{'))
        print('Error-ids content: \n', str(error_ids).replace('}, {', '}, \n{'))
        driver.switch_to.window(driver.window_handles[0])
        driver.close()
        driver.quit()
        print('exited correctly')
