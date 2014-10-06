from bs4 import BeautifulSoup
from StringIO import StringIO
from config import vip_qa_data
from PIL import Image
import mechanize
import urllib2
import re
import math
import os


class VectorCompare:
    def magnitude(self, concordance):
        total = 0
        for word, count in concordance.iteritems():
            total += count ** 2
        return math.sqrt(total)

    def relation(self, concordance1, concordance2):
        topvalue = 0
        for word, count in concordance1.iteritems():
            if word in concordance2:
                topvalue += count * concordance2[word]
        return topvalue / (self.magnitude(concordance1) * self.magnitude(
            concordance2))


def openImage(url):
    response = urllib2.urlopen(url)
    im = Image.open(StringIO(response.read()))
    return im


def convertImage(image, colors):
    im = image.convert("P")
    im2 = Image.new("P", im.size, 255)
    im = im.convert("P")
    temp = {}
    for x in range(im.size[1]):
        for y in range(im.size[0]):
            pix = im.getpixel((y, x))
            temp[pix] = pix
            if pix in colors:
                im2.putpixel((y, x), 0)
    return im2


def identifyEdges(image):
    inletter = False
    foundletter = False
    start = 0
    end = 0
    letters = []
    for y in range(image.size[0]):
        for x in range(image.size[1]):
            pix = image.getpixel((y, x))
            if pix != 255:
                inletter = True
        if inletter and not foundletter:
            foundletter = True
            start = y
        if foundletter and not inletter:
            foundletter = False
            end = y
            letters.append((start, end))
        inletter = False
    set = []
    for letter in letters:
        if letter[1] - letter[0] > 3:
            set.append(letter)
    return set


def splitImages(convertedImage, letters, imageset, comparison):
    guesses = []
    for letter in letters:
        im = convertedImage.crop((letter[0], 0, letter[1],
                                  convertedImage.size[1]))
        guess = []
        for image in imageset:
            for x, y in image.iteritems():
                if len(y) != 0:
                    guess.append((
                        comparison.relation(y[0], buildVector(im)), x))
        guess.sort(reverse=True)
        guesses.append(guess[0])
    return guesses


def buildVector(image):
    d1 = {}
    count = 0
    for i in image.getdata():
        d1[count] = i
        count += 1
    return d1


def compareToVector(image):
    iconset = ['2', '3', '4', '6', '7', '8', '9', 'A', 'B', 'C', 'D',
               'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q',
               'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    imageset = []
    path = vip_qa_data.replace('Target_Smart_Data/states-full/', '')
    for letter in iconset:
        for img in os.listdir(
                '{0}letters/{1}/'.format(
                    path, letter)):
            temp = []
            temp.append(buildVector(Image.open(
                '{0}letters/{1}/{2}'.format(
                    path, letter, img))))
            imageset.append({letter: temp})
    return imageset


def getSecurity(url):
    comparison = VectorCompare()
    print url
    first = []
    second = []
    third = []
    fourth = []
    fifth = []
    for j in range(10):
        while True:
            image = openImage(url)
            converted = convertImage(image, [22, 16, 59])
            letterSet = identifyEdges(converted)
            if len(letterSet) != 5:
                continue
            imageSet = compareToVector(image)
            guesses = splitImages(converted, letterSet, imageSet, comparison)
            first.append(guesses[0][1])
            second.append(guesses[1][1])
            third.append(guesses[2][1])
            fourth.append(guesses[3][1])
            fifth.append(guesses[4][1])
            break
    text = '{0}{1}{2}{3}{4}'.format(max(set(first), key=first.count),
                                    max(set(second), key=second.count),
                                    max(set(third), key=third.count),
                                    max(set(fourth), key=fourth.count),
                                    max(set(fifth), key=fifth.count))
    print text
    return text


def getValues(row, townDict):
    town = row['vf_reg_cass_city'].upper()
    townValue = str(townDict[town])
    fname = row['tsmart_first_name']
    lname = row['tsmart_last_name']
    date = row['voterbase_dob']
    return townValue, fname, lname, date


def generateTownDict(soup):
    townDict = {}
    city = soup.find('select',
                     {'name': 'ctl00$MainContentPlaceHolder$ddlCity'})
    for item in city.find_all('option'):
        townDict[item.text.upper()] = item.get('value')
    return townDict


def getOutputValues(soup):
    ppid = ''
    IDBase = 'ctl00_MainContentPlaceHolder_rptPollingPlace_ctl01_'
    name = soup.find('span', {'id': IDBase + 'lblPollingPlaceName'}).string
    street1 = soup.find('span', {'id': IDBase + 'lblPollingAddress'}).string
    street2 = soup.find('span', {'id': IDBase + 'lblPollingAddress2'}).string
    address = '{0} {1}'.format(street1.strip(), street2.strip())
    return ppid, name, address


def startBrowser():
    agent1 = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    agent2 = '(KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36'
    agent = 'User-Agent', agent1 + ' ' + agent2
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.set_handle_refresh(False)
    br.addheaders = [('User-Agent', agent)]
    return br


def getImageURL(soup):
    img = soup.find('img', {'src': re.compile('Captcha')})
    src = img.get('src')
    url = 'http://cfs.sos.nh.gov/app/Public/' + src
    return url


def run(row):
    formURL = 'http://cfs.sos.nh.gov/app/Public/PollingPlaceSearch.aspx'
    browser = startBrowser()
    while True:
        try:
            response = browser.open(formURL)
            soup = BeautifulSoup(response.read())
            imageURL = getImageURL(soup)
            security = getSecurity(imageURL)
            townDict = generateTownDict(soup)
            townValue, fname, lname, date = getValues(row, townDict)
            browser.select_form("aspnetForm")
            browser.set_all_readonly(False)
            baseName = 'ctl00$MainContentPlaceHolder$'
            browser[baseName + 'ddlCity'] = [townValue]
            browser[baseName + 'txtFirstName'] = fname
            browser[baseName + 'txtLastName'] = lname
            browser[baseName + 'ddlYear'] = [str(int(date[:4]))]
            browser[baseName + 'ddlMonth'] = [str(int(date[4:6]))]
            browser[baseName + 'ddlDay'] = [str(int(date[6:8]))]
            browser[baseName + 'capObject'] = security
            response = browser.submit(name=baseName + 'btnSearch')
            soup = response.read()
            return getOutputValues(soup)
        except Exception:
            pass
