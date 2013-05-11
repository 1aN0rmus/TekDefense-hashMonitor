#!/usr/bin/env python                                                                                                                                                                                      

'''
This is hashMonitor! This tool will collect hashes from data breeches reported via Twitter.
This works by checkinng popular accounts on twitter like @Dumpmon and @PastebinDorks.
hashMonitor will go to each link they tweet and scrape out MD5, SHA1, and SHA256 Hashes.

@TekDefense
Ian Ahl | www.TekDefense.com | 1aN0rmus@tekDefense.com

Version: 0.2

Changelog:
.2
[+] Optimize database for faster hash insertion
[+] Added option to specify a database name and path
[+] Added error handling to the hash insert to DB
[+] Optimized link2DB function and added error handling

.1 
[+] Initial Release

TODO
[-] Let users add accounts to monitor
'''

import twitter, sqlite3, re, datetime, httplib2, argparse, sys

listMonitor = ['Dumpmon', 'PastebinDorks', 'TekDefense']
listURLs = []
api = twitter.Api()
hashMonDB = 'hashMon.db'
today = datetime.datetime.now()
now = today.strftime("%Y-%m-%d %H:%M")
MD5 = '([a-fA-F0-9]{32})\W'
SHA1 = '([a-fA-F0-9]{40})\W'
SHA256 = '([a-fA-F0-9]{64})\W'
listTypes = [('MD5',MD5),('SHA1',SHA1), ('SHA256',SHA256),]
listResults = []
listNewURLs = []
hashType = ''
hashList = False

parser = argparse.ArgumentParser(description='hashMonitor is a tool that will collect hashes from data breeches reported via Twitter')
parser.add_argument('-d', '--database', help='This option is used to specify a database name. ./hashMonitor.py -d databaseName.db')
parser.add_argument('-o', '--output', help='This option will output the results to a file. ./hashMonitor.py -o output.txt')
parser.add_argument('-l', '--list', help='This option will return a list of all the hashes in the database. Use ALL, MD5, SHA1, or SHA256. ./hashMonitor.py -l MD5')
args = parser.parse_args()

if args.output:
    oFile = args.output
    print '[+] Printing results to file:', args.output
    o = open(oFile, "w")
    sys.stdout = o

if args.list:
    hashList = True
    if args.list.upper() == 'ANY' or args.list.upper() == 'MD5' or args.list.upper() == 'SHA1' or args.list.upper() == 'SHA256':
        hashType = args.list.upper()
    else:
        print '[!] You must choose -l ANY, -l MD5, =l SHA1, or -l SHA256'
        sys.exit()

if args.database:
    hashMonDB = args.database

def twitterLinkPull():
    global listURLs
    
    for i in listMonitor:
        users = i
        statuses = api.GetUserTimeline(users)
        for s in statuses:
            regURL = '(http:\/\/t\.co\/\w{1,12})'
            regURLComp = re.compile(regURL)
            regexURLSearch = re.search(regURLComp, str(s))
            if regexURLSearch != None:    
                URL = regexURLSearch.group()
                listURLs.append(URL)

def links2DB():
    print '[*] Adding links to the DB if they have not been scanned previously.'
    con = sqlite3.connect(hashMonDB)
    with con:
        cur = con.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS URLs(URL TEXT PRIMARY KEY, DATE TEXT)')
        con.commit()
        for i in listURLs:
            try:
                cur.execute("INSERT INTO URLs(URL, DATE) VALUES(?,?)", (i, now))
                listNewURLs.append(i)
                print '[+] Adding ' + i + ' into the DB'
            except:
                print '[-] ' + i + ' has already been seen'
    con.commit()
    con.close()
    
def collectHashes():
    global listResults
    if len(listNewURLs) > 0:
        print '[+] Searching for hashes in the new URLs'
        for URL in listNewURLs:
            h = httplib2.Http(".cache")
            resp, content = h.request((URL), "GET")
            contentString = (str(content))
            for reg in listTypes:
                regVal = reg[1]
                regexValue = re.compile(regVal)
                regexSearch = re.findall(regexValue,contentString)
                for result in regexSearch:
                    listResults.append((result, reg))
            listResults = list(set(listResults)) 
    else:
        print '[-] No new URLs to search'

def hashes2DB():
    print '[*] Inserting new hashes to the DB if any are found.'
    con = sqlite3.connect(hashMonDB)
    n = 0
    with con:
        cur = con.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS HASHES(HASH TEXT PRIMARY KEY, TYPE TEXT)')
        con.commit()
        for i in listResults:
            try:
                n = n + 1
                print '[+] Adding ' + i[0] + ' to the DB'
                cur.execute("INSERT INTO HASHES(HASH, TYPE) VALUES(?,?)", (i[0], i[1][0]))
            except:
                print '[-] Hash already exists in database'
        print '[+] Added ' + str(n) + ' Hashes to the Database'
    con.commit()
    con.close()

def listHashes():
    if hashList == True:
        con = sqlite3.connect(hashMonDB)
        with con:
            cur = con.cursor()
            if hashType == 'MD5' or hashType == 'SHA1' or hashType == 'SHA256':
                cur.execute('SELECT HASH FROM HASHES where TYPE = ?', (hashType, ))
                results = cur.fetchall()
                for i in results:
                    print i[0]
            else:
                cur.execute('SELECT HASH FROM HASHES')
                results = cur.fetchall()
                for i in results:
                    print i[0]

#def accounts():
    #con = sqlite3.connect(hashMonDB)
    #with con:
        #cur = con.cursor()
        #cur.execute('CREATE TABLE IF NOT EXISTS ACCOUNTS(Id INTEGER PRIMARY KEY, ACCOUNT TEXT)')
        #con.commit()

print '[*] Running hashMonitor.py'
twitterLinkPull()
links2DB()
collectHashes()
hashes2DB()
listHashes()

