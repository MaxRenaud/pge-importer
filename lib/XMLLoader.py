__author__ = 'Max Renaud'

from cStringIO import StringIO
import datetime
import logging
import mechanize
import os
import re
import tempfile
import xmltodict
import zipfile


def extract_file(data):
    files = set()
    tmp_dir = tempfile.mkdtemp()
    try:
        zh = zipfile.ZipFile(StringIO(data))
        for name in zh.namelist():
            zh.extract(name, tmp_dir)
            files.add(os.path.join(tmp_dir, name))
    except Exception:
        print "Cannot parse downloaded zip file"
        quit()
    return files


def parse_file(file_name):
    intervals = list()
    logging.debug("Parsing {0}".format(file_name))
    with open(file_name) as fh:
        pge = xmltodict.parse(fh.read())
    for i in  pge['feed']['entry']:
        if type(i['link']) == list:
            continue
        if 'IntervalBlock' not in i['link']['@href']:
            continue
        #i contains what we want

        for interval in i['content']['IntervalBlock']['IntervalReading']:
            # value is in Watt-hour and cost is in 0.001 cents
            # Cost might be missing, which translates into a 0 on PG&E's website
            intervals.append((int(interval['timePeriod']['start'])+int(interval['timePeriod']['duration']),
                        int(interval['value']),
                        float(interval.get('cost',0))/1000))
    return intervals


def download_archive(start_time, username, password):
    user_agent = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    start_date = datetime.datetime.fromtimestamp(start_time).strftime("%m/%d/%Y")
    br = mechanize.Browser()
    br.addheaders =[('User-agent', user_agent)]
    logging.debug("Requesting the home page")
    br.open('https://www.pge.com/myenergyweb/appmanager/pge/customer')
    #Select the login form
    br.select_form("login")
    br.form['USER'] = username
    br.form['PASSWORD'] = password
    logging.debug("Submitting login form")
    br.submit()
    #Find "My Usage"
    logging.debug("Requesting My Usage")
    req = br.click_link(text="My Usage")
    br.open(req)
    #This is a redirect with a SAML response inside a form. Submit it
    logging.debug("Submitting the SAML form")
    req = br.forms().next().click()
    br.open(req)
    #Now for an SSO form...
    logging.debug("Submitting the SSO form")
    req = br.forms().next().click()
    br.open(req)
    logging.debug("Clicking Green Button")
    req = br.click_link(url_regex=re.compile(".*export-dialog$"))
    br.open(req)
    logging.debug("Submitting Green form")
    form = br.forms().next()
    #Select the last item (Export usage for a range)
    form.find_control("exportFormat").items[-1].selected = True
    form['xmlFrom'] = start_date
    form['xmlTo'] = datetime.datetime.now().strftime("%m/%d/%Y")
    logging.info("Requesting data from {0} to {1}".format(form['xmlFrom'], form['xmlTo']))
    req = form.click()
    resp = br.open(req)
    return resp.read()
