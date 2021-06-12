#!/usr/bin/python3

import datetime
from time import sleep, strftime

import pandas
from selenium import webdriver

# Change this to your own chromedriver path!
chromedriver_path = '/opt/usr/bin/chromedriver/chromedriver'

# https://sqa.stackexchange.com/questions/9904/how-to-set-browser-locale-with-chromedriver-python
chromedriver_options = webdriver.ChromeOptions()
# chromedriver_options.add_argument("--start-maximized")
# chromedriver_options.add_argument('lang=pt')
# chromedriver_options.add_argument('--lang=pt') <- Tried this option as well
# chromedriver_options.add_experimental_option('prefs', {'intl.accept_languages': 'pt,pt_BR'})

# This will open the Chrome window
driver = webdriver.Chrome(executable_path=chromedriver_path, options=chromedriver_options)


# sleep(2)

def simple_test(city_from, city_to, dates):
    kayak = 'https://www.kayak.com.br/flights/REC-YUL/2021-08-23-flexible/2adults/children-17-17?sort=bestflight_a&fs=layoverdur=-720;legdur=-1830;layoverair=-EWR,MIA,FLL,LGA,JFK,IAH,ATL'
    driver.get(kayak)
    sleep(3)

    header = '//a[@data-code = "bestflight"]'  # TODO price, bestflight
    driver.find_element_by_xpath(header).click()

    flight_table = '//div[@class = "resultWrapper"]'

    flight_containers = driver.find_elements_by_xpath(flight_table)
    flights = [flight.text for flight in flight_containers]

    # the first three results
    flights3 = flights[0:3]
    print(flights3)


def wait_progress():
    # sleep(20)
    try:
        driver.find_element_by_xpath('//*[contains(@class,"progress-bar")]/div[contains(@class,"Hidden")]')
    except:
        sleep(2)
        wait_progress()


# Load more results to maximize the scraping
def load_more():
    try:
        more_results = '//a[@class = "moreButton"]'
        driver.find_element_by_xpath(more_results).click()
        print('Loading more...')
        sleep(5)
        driver.execute_script("window.scrollTo(0,0);")
        sleep(2)
        driver.execute_script("window.scrollTo(0,0);")
    except:
        pass


# sometimes a popup shows up, so we can use a try statement to check it and close
def popup_close():
    try:
        xp_popup_close = '//button[contains(@id,"dialog-close") and contains(@class,"Button-No-Standard-Style close")]'
        driver.find_elements_by_xpath(xp_popup_close)[5].click()
        sleep(5)
        driver.execute_script("window.scrollTo(0,0);")
    except Exception as e:
        pass


def page_scrape():
    """This function takes care of the scraping part"""

    durations = driver.find_elements_by_xpath('//*[contains(@class, "section") and contains(@class, "duration")]')
    durations_list = [value.text for value in durations]
    # section_a_list = sections_list[::2]  # This is to separate the two flights
    # section_b_list = sections_list[1::2]  # This is to separate the two flights

    # if you run into a reCaptcha, you might want to do something about it
    # you will know there's a problem if the lists above are empty
    # this if statement lets you exit the bot or do something else
    # you can add a sleep here, to let you solve the captcha and continue scraping
    # i'm using a SystemExit because i want to test everything from the start
    if not durations_list:
        return pandas.DataFrame({'Date': [],
                                 'Airline': [],
                                 'Cities': [],
                                 'Stops': [],
                                 'Duration': [],
                                 'Time': [],
                                 'Total': [],
                                 'Price': [],
                                 'timestamp': []})[
            (['Date', 'Airline', 'Cities', 'Stops', 'Duration', 'Time', 'Total', 'Price', 'timestamp'])]

    dates = driver.find_elements_by_xpath('//div[contains(@class, "with-date")]')
    dates_list = [value.text for value in dates]

    # getting the prices
    totals = driver.find_elements_by_xpath('//*[@class="price-total"]')
    totals_list = [total.text.replace('R$ ', '').replace(' no total', '').replace('.', '') for total in totals if
                   total.text != '']
    totals_list = list(map(int, totals_list))
    prices_list = [(total / 4) for total in totals_list]

    # the stops are a big list with one leg on the even index and second leg on odd index
    stops = driver.find_elements_by_xpath('//div[@class="section stops"]/div[1]')
    stops_list = [stop.text[0].replace('n', '0') for stop in stops]

    stops_cities = driver.find_elements_by_xpath('//div[@class="section stops"]/div[2]')
    stops_cities_list = [stop.text for stop in stops_cities]

    # this part gets me the airline company and the departure and arrival times, for both legs
    schedules = driver.find_elements_by_xpath('//div[@class="section times"]')
    hours_list = []
    for schedule in schedules:
        hours_list.append(schedule.text.split('\n')[0])

    carriers = driver.find_elements_by_xpath('//*[@class="codeshares-airline-names"]')
    carrier_list = [stop.text for stop in carriers]

    flights_df = pandas.DataFrame({'Date': dates_list,
                                   'Airline': carrier_list,
                                   'Cities': stops_cities_list,
                                   'Stops': stops_list,
                                   'Duration': durations_list,
                                   'Time': hours_list,
                                   'Total': totals_list,
                                   'Price': prices_list})[
        (['Date', 'Airline', 'Cities', 'Stops', 'Duration', 'Time', 'Total', 'Price'])]

    flights_df['timestamp'] = strftime("%Y%m%d-%H%M")  # so we can know when it was scraped

    return flights_df


def start_kayak(level, city_from, city_to, dates):
    """City codes - it's the IATA codes!
    Date format -  YYYY-MM-DD"""

    matrix_prices_all = []

    df_flights = pandas.DataFrame()

    for date in dates:
        # 'layoverdur=180-;' \
        # 'layoverdur=-720;' \
        # 'legdur=-1830;' \
        url = 'https://www.kayak.com.br/flights/' \
              + city_from + '-' + city_to + '/' + date + '-flexible/' + level \
              + '/2adults/children-17-17?sort=bestflight_a&' \
                'fs=' \
                'layoverair=-ORD,EWR,MIA,FLL,LGA,CLT,JFK,IAH,DFW,PHL,ATL,LIS,CDG,MCO,IAD'

        print('URL: ' + url)
        driver.get(url)
        driver.set_window_position(800, 30)

        wait_progress()

        popup_close()

        load_more()

        print('Scraping Best')
        df_flights_best = page_scrape()
        df_flights_best['sort'] = 'best'
        df_flights_best['url'] = url
        if len(df_flights.index) == 0:
            df_flights = df_flights_best
        else:
            df_flights = df_flights.append(df_flights_best)

        print('Scraping Cheapest')
        cheap_results = '//a[@data-code = "price"]'
        driver.find_element_by_xpath(cheap_results).click()
        sleep(5)

        load_more()

        df_flights_cheap = page_scrape()
        df_flights_cheap['sort'] = 'cheap'
        df_flights_cheap['url'] = url
        df_flights = df_flights.append(df_flights_cheap)

        print('Scraping Fastest')
        quick_results = '//a[@data-code = "duration"]'
        driver.find_element_by_xpath(quick_results).click()
        sleep(5)

        load_more()

        df_flights_fast = page_scrape()
        df_flights_fast['sort'] = 'fast'
        df_flights_fast['url'] = url
        df_flights = df_flights.append(df_flights_fast)

        # We can keep track of what they predict and how it actually turns out!
        # xp_loading = '//div[contains(@id,"advice")]'
        # loading = driver.find_element_by_xpath(xp_loading).text
        # xp_prediction = '//s
        # pan[@class="info-text"]'
        # prediction = driver.find_element_by_xpath(xp_prediction).text
        # print(loading + '\n' + prediction)

        # sometimes we get this string in the loading variable, which will conflict with the email we send later
        # just change it to "Not Sure" if it happens
        # weird = '¯\\_(ツ)_/¯'
        # if loading == weird:
        #     loading = 'Not sure'

        # Let's also get the lowest prices from the matrix on top
        matrix = driver.find_elements_by_xpath('//*[contains(@id,"FlexMatrixCell")]')
        matrix_prices = [price.text.replace('R$ ', '').replace('.', '') for price in matrix]
        matrix_prices = list(filter(('').__ne__, matrix_prices))
        matrix_prices = list(map(int, matrix_prices))
        matrix_prices_all.extend(matrix_prices)

    file = '{}_{}_{}-{}.xlsx'.format(strftime("%Y%m%d-%H%M%S"), level.replace(',', '-'), city_from, city_to)

    df_flights = df_flights.sort_values(['Total', 'Duration', 'Stops'])

    df_flights.to_excel(file, index=False)

    print('Saved DataFrame to {}'.format(file))

    matrix_min = min(matrix_prices_all)
    matrix_avg = sum(matrix_prices_all) / len(matrix_prices_all)

    # (loading + '\n' + prediction)
    print('Source: {}\n'
          'Destination: {}\n'
          'Dates: {}\n'
          'Cheapest Flight: {}\n'
          'Average Price: {}\n'
          .format(city_from, city_to, dates, matrix_min, matrix_avg))


def get_dates(start, end, delta=datetime.timedelta(days=7)):
    date = start + delta / 2
    dates = []
    while date <= end:
        dates.append(date.strftime('%Y-%m-%d'))
        date += delta

    return dates


# august/2021
# economy, premium, business, first, economy,business
# start_kayak('economy', 'REC', 'YUL', get_dates(datetime.date(2021, 7, 30), datetime.date(2021, 9, 30)))
start_kayak('economy', 'REC', 'YUL', get_dates(datetime.date(2021, 7, 30), datetime.date(2021, 9, 7)))
