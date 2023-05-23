import os
import sqlite3

PATH = ""


def CreateDb():
    with sqlite3.connect('data/logs.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS Passwords(login TEXT, password TEXT, cookies TEXT)""")

        result = 0

        for dir in os.listdir('source'):
            for subdir in os.listdir('source/' + dir):
                try:
                    path = 'source/' + dir + '/' + subdir + '/Password'
                    for file in os.listdir(path):
                        with open(path + '/' + file, 'r') as fp:
                            lines = fp.readlines()
                            for line_number, line in enumerate(lines):
                                if 'reddit.com' in line:
                                    if (lines[line_number + 1] == 'Username: \n'):
                                        continue
                                    else:
                                        result = result + 1
                                        cursor.execute('INSERT INTO Passwords VALUES (?,?,?)',
                                                       (lines[line_number + 1][10:-1], lines[line_number + 2][10:-1],
                                                        'source/' + dir + '/' + subdir + '/Cookies'))


                except:
                    pass
        print(result)


if __name__ == "main":
    CreateDb()
