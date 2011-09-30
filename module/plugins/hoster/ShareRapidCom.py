#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.Hoster import Hoster
from module.network.RequestFactory import getURL

def getInfo(urls):
    result = []

    for url in urls: 
        html = getURL(url, decode=True)
        if re.search(ShareRapidCom.FILE_OFFLINE_PATTERN, html):
            # File offline
            result.append((url, 0, 1, url))
        else:
            # Get file info
            name, size = url, 0

            found = re.search(ShareRapidCom.FILE_SIZE_PATTERN, html)
            if found is not None:
                size, units = found.groups()
                size = float(size) * 1024 ** {'kB': 1, 'MB': 2, 'GB': 3}[units]
            
            found = re.search(ShareRapidCom.FILE_NAME_PATTERN, html)
            if found is not None:
                name = found.group(1)

            if found or size > 0:
                result.append((name, size, 2, url))
    yield result

class ShareRapidCom(Hoster):
    __name__ = "ShareRapidCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?share-rapid\.(com|cz)/"
    __version__ = "0.3"
    __description__ = """share-rapid Plugin"""
    __author_name__ = ("MikyWoW", "zoidberg")
    __author_mail__ = ("MikyWoW@seznam.cz", "zoidberg@mujmail.cz")

    FILE_NAME_PATTERN = r'<h3>([^<]+)</h3>'
    FILE_SIZE_PATTERN = r'<td class="i">Velikost:</td>\s*<td class="h"><strong>\s*([0-9.]+) (kB|MB|GB)</strong></td>'
    DOWNLOAD_URL_PATTERN = r'<a href="([^"]+)" title="Stahnout">([^<]+)</a>'
    ERR_LOGIN_PATTERN = ur'<div class="error_div"><strong>Stahování je přístupné pouze přihlášeným uživatelům'
    ERR_CREDIT_PATTERN = ur'<div class="error_div"><strong>Stahování zdarma je možné jen přes náš'
    FILE_OFFLINE_PATTERN = ur'Nastala chyba 404|Soubor byl smazán'

    def setup(self):
        self.chunkLimit = 1
        self.resumeDownload = True

    def process(self, pyfile):
        if not self.account: self.fail("User not logged in")

        self.html = self.load(pyfile.url, decode=True)
        size, units = re.search(self.FILE_SIZE_PATTERN, self.html).groups()
        pyfile.size = float(size) * 1024 ** {'kB': 1, 'MB': 2, 'GB': 3}[units]

        found = re.search(self.DOWNLOAD_URL_PATTERN, self.html)
        if found is not None:
            self.logDebug(found)
            link, pyfile.name = found.groups()
            self.logInfo("Downloading file: %s (%s %s)" % (pyfile.name, size, units))
            self.logInfo("Premium link: %s" % link)
            self.download(link)
        else:
            self.logError("Download URL not found")
            if re.search(self.ERR_LOGIN_PATTERN, self.html):
                self.relogin()
                self.retry(3,0,"User login failed")
            elif re.search(self.ERR_CREDIT_PATTERN, self.html):
                self.fail("Not enough credit left")
            else:
                self.fail("Download link not found")