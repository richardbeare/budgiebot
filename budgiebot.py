#!/usr/bin/env python3
import sys
import pywikibot as pwb
from pywikibot import pagegenerators
from pywikibot import config

import pandas as pd

from pywikibot.bot import (
    ExistingPageBot,
    SingleSiteBot
)

import mwparserfromhell as mwph
import re
# codes cmn, kxd, quw

# global variables
IGNORE=set(["ENGLISH", "SPANISH", "FRENCH", "GERMAN"])
globalsite = None
LangInfoBox = None

def findInfobox(page, lang_infobox = LangInfoBox):
    """
    Iterate through the templages on the page and return the dictionary associated with the infobox language
    return none if not found
    """
    if lang_infobox is None:
        print("Null infobox")
    code = mwph.parse(page.text)
    for tmpl in code.filter_templates():
        link = pwb.Link(tmpl.name, page.site,
                        default_namespace=10)
        link = pwb.Page(link, page.site)
        if link == lang_infobox:
            return tmpl
    return None
 
def checkISO639(isocode, site = pwb.Site('wikipedia:en')):
    """
    Attempt to get the specified iso code, and return
    the page it redirects to.
    This doesn't deal with the ENGLISH, SPANISH, GERMAN
    entries - just returns None if there is a problem
    """
    if type(isocode) is not str:
        return None #pwb.Page(site, dummytitle)
    isourl = "ISO_639:" + isocode.lower()
    isopage = pwb.Page(site, isourl)
    if not isopage.isRedirectPage():
        print(isocode)
        print("Some problem - not a redirect")
        return None #pwb.Page(site, dummytitle)
    target = isopage.getRedirectTarget()
    return target

def checkISO639df(isorow, site = pwb.Site('wikipedia:en')):
    """
    Attempt to get the specified iso code, and return
    the page it redirects to.
    This one takes a line from the spreadsheed and attaches
    it to the page for later use.
    This doesn't deal with the ENGLISH, SPANISH, GERMAN
    entries - just returns None if there is a problem
    """
    isocode = isorow["ISOcodeEdited"]
    print(isocode)
    if type(isocode) is not str:
        return None #pwb.Page(site, dummytitle)
    isourl = "ISO_639:" + isocode.lower()
    isopage = pwb.Page(site, isourl)
    if not isopage.isRedirectPage():
        print(isocode)
        print("Some problem - not a redirect")
        return None #pwb.Page(site, dummytitle)
    target = isopage.getRedirectTarget()
    target.__isodf__ = isorow
    return target

# I think I need to write my own page generator that works with the excel file
def lang_isocode_generator(isocodelist, thissite):
    """
    custom page generator for JIPA citations
    """
    for code in isocodelist:
        yield checkISO639(code, thissite)

def lang_isocode_generator_df(isocodedf, thissite):
    """
    custom page generator for JIPA citations
    """
    for idx, row in isocodedf.iterrows():
        yield checkISO639df(row, thissite)

def getISOfromInfoBox(infobox):
    # mwparserfromhell version
    # seem to be several potential keys
    # iso3, lc1, lc2...
    # not sure how many lc? options there can be - seems to be a lot.
    allkeys = [p.name for p in infobox.params]
    # keep the ones matching lc.. Note that sometimes there is whitespace around the keys
    # in the dictionary..
    keystrings = [k for k in allkeys if k.strip().startswith('lc')]
    # find the iso3 tag - sometimes it also has leading/trailing spaces
    isostrings = [k for k in allkeys if k.strip().startswith('iso3')]
    keystrings += isostrings
    allcodes = [infobox.get(x).value for x in keystrings]
    result = set([i.strip() for i in allcodes if i is not None])
    if len(result) == 0:
        print(allkeys)
        print("Couldn't find iso codes")
    return result

def checkForDOI(section, doi):
    # returns True if doi is already in a citation
    # template in the section
    for tmpl in section.filter_templates():
        if tmpl.has("doi"):
            thisdoi = tmpl.get("doi").value
            if thisdoi == doi:
                print("DOI found")
                if not tmpl.name.matches("Cite JIPA"):
                    print(tmpl.name)
                    print("Not using cite jipa")
                return True
    return False

def appendCitation(section, citation):
    """
    Add the jipa citation before {{refend}}
    Report if no {{refend}}
    If no refend, add before the first "\n\n"
    Sometimes the further reading title is followed
    by \n\n - probably should check and replace
    Can't use the last \n\n because sometimes there are 
    internal links at the end - e.g. {{Languages of ...}}
    """
    #print(section.nodes)
    refend = section.filter_templates(matches="refend")
    if len(refend) != 1:
        print("No refend in further reading or multiple refends")
        # insert at the end - perhaps look for first double newline
        endmarker = section.filter(matches="\n\n")
        if len(endmarker) == 0:
            print("can't find usual end of section marker")
            endmarker = section.nodes[-1]
            section.insert_after(endmarker, citation)
            section.insert_after(endmarker, "*")
            section.insert_after(endmarker, "\n")
        else:
            endmarker = section.nodes[section.nodes.index(endmarker[0])]
            section.insert_before(endmarker, "\n")
            section.insert_before(endmarker, "*")
            section.insert_before(endmarker, citation)
    else:
        section.insert_before(refend, "*")
        section.insert_before(refend, citation)
    return section

def mkCiteJIPA(df):
    """
    df is a single row dataframe
    https://en.wikipedia.org/wiki/Template:Cite_JIPA
    {cite JIPA |author= |title= |printdate= |volume= |issue= |pages= |doi= }
    
    Looks like dates should by yyyy-mm-dd, with -dd optional
    """
    # format the date
    dt = df["DA"]
    dt=re.sub("/+","-", dt)
    dt=re.sub('-$', '', dt)
    jipa_tmpl = mwph.nodes.Template(name='Cite JIPA')
    jipa_tmpl.add("author", df["author"])
    jipa_tmpl.add("title", df["title"])
    if not pd.isnull(df["volume"]):
        jipa_tmpl.add("volume", int(df["volume"]))
    if not pd.isnull(df["issue"]):
        jipa_tmpl.add("issue", int(df["issue"]))
        
    pp = re.sub("-+", '&ndash;', df["pages"])
    jipa_tmpl.add("pages", pp)
    jipa_tmpl.add("doi", df["doi"])
    jipa_tmpl.add("printdate", dt)
    if pd.isnull(df["SoundFiles"]):
        soundfiles = "no"
    else:
        soundfiles = df["SoundFiles"]
    jipa_tmpl.add("soundfiles", soundfiles)

    return jipa_tmpl

def mkFurtherReading(citation):
    """
    For when we need to create a new further reading section containing
    the JIPA reference
    """
    pgtext = "== Further Reading ==\n{{refbegin}}\n*"
    pgtext += str(citation)
    pgtext += "\n{{refend}}\n\n"
    FR = mwph.parse(pgtext)
    return(FR)

def checkPage(details, page):
    """
    Cross checks the code against contents of infobox,
    and whether there is a "Further reading section".
    details is a line from the spreadsheet (single line
    pandas df)
    """
    global LangInfoBox
    isocode = details["ISOcodeEdited"]
    doi = details["doi"]
    
    if page is None:
        return None
    if isocode in IGNORE:
        return None
    isocode = isocode.lower().strip()
    infobox = findInfobox(page, LangInfoBox)
    iso_from_infobox = getISOfromInfoBox(infobox)
    if isocode not in iso_from_infobox:
        print("entry on redirected page doesn't match " + isocode)
        print(iso_from_infobox)
        return(None)
    
    # get the citation ready
    thiscite = mkCiteJIPA(details)
    # Now find further reading
    allsections = mwph.parse(page.text)
    have_furtherreading = False
    for sect in allsections.get_sections():
        for f in sect.filter_headings():
            if f.title.matches("further reading"):
                print("Found further reading")
                have_furtherreading = True
                # can check for DOI in this section
                if not checkForDOI(sect, doi):
                    # add the citation
                    appendCitation(sect, thiscite)
                    #print(sect.nodes)
                break
    if not have_furtherreading:
        # need to create and insert our own
        # ==See also==
        # ==Notes== and ==References==
        # ==Further reading==
        # ==External links==
        #
        # search for External links and place further reading before,
        # search for References in External links doesn't exist
        # and place after, and continue
        FurtherReading = mkFurtherReading(thiscite)
        el = allsections.filter_headings(matches = "External Links")
        # this can sometimes match stuff like "other ordering preferences"
        refs = allsections.filter_headings(matches = "References", flags = re.DOTALL)
        notes = allsections.filter_headings(matches = "Notes", flags = re.DOTALL)
        seealso = allsections.filter_headings(matches = "See also", flags = re.DOTALL)
        insertedFR = False
        if len(el) > 0:
            #print("Using external links")
            if len(el) > 1:
                print("Too many external link matches")
            allsections.insert_before(el[0], FurtherReading)
            insertedFR = True
        elif len(refs) > 0:
            #print("Using references")
            if len(refs) > 1:
                print("Too many ref matches")
            allsections.insert_after(refs[0], FurtherReading)
            insertedFR = True
        elif len(notes) > 0:
            #print("Using notes")
            if len(notes) > 1:
                print("Too many notes matches")
            allsections.insert_after(notes[0], FurtherReading)
            insertedFR = True
        elif len(seealso) > 0:
            #print("Using external see also")
            if len(seealso) > 1:
                print("Too many ref matches")
            allsections.insert_after(seealso[0], FurtherReading)
            insertedFR = True
        # check whether we were successful
        if not insertedFR:
            print("Can't figure out where to insert Further Reading")
    return str(allsections)
    #return None

class BudgieBot(ExistingPageBot, SingleSiteBot):
    
    update_options={
            'isoexcel': None,
            'dryrun': False,   # don't strictly need this, but it is faster than -simulate
            'summary': None,
            'interactive' : False
        }

    def treat_page(self):
        """Load the given page, do some changes, and save it."""
        #print(self.current_page)
        #print(self.current_page.__isodf__)
        text = checkPage(self.current_page.__isodf__, self.current_page)
        if text is not None:
            # modifications made
            print("Mods made - update")
            if self.opt.dryrun:
                # only show the diffs
                pwb.showDiff(self.current_page.text, text)
            elif self.opt.interactive:
                pwb.showDiff(self.current_page.text, text)
                submit = pwb.input_yn('Do you want to submit the changes above?', default=False)
                if submit:
                    print("Submitting changes") 
                    self.put_current(text, summary=self.opt.summary)
            else:
                self.put_current(text, summary=self.opt.summary)        

# boilerplate main from https://doc.wikimedia.org/pywikibot/stable/library_usage.html
def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    # args seems to be handled by the pwb wrapper
    options = {}
    # Process global arguments to determine desired site
    local_args = pwb.handle_args(args)
    # Now site is set, so use it
    sitestring = pwb.config.family + ":" + pwb.config.mylang
    global globalsite 
    globalsite = pwb.Site(sitestring)
    global LangInfoBox
    LangInfoBox =  pwb.Page(globalsite, 'Template:Infobox language')

    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    #
    # factory grabs the site flag
    gen_factory = pagegenerators.GeneratorFactory()
    
    # Process pagegenerators arguments
    local_args = gen_factory.handle_args(local_args)
    print(local_args)

    # Parse your own command line arguments
    for arg in local_args:
        arg, _, value = arg.partition(':')
        option = arg[1:]
        if option in ('isoexcel'):
            if not value:
                pwb.input('Please enter a value for ' + arg)
            options[option] = value
        elif option in ('summary'):
            if not value:
                pwb.input('Please enter a value for ' + arg)
            options[option] = value
        # take the remaining options as booleans.
        # You will get a hint if they aren't pre-defined in your bot class
        else:
            options[option] = True
   
    if "isoexcel" not in options.keys():
        print("Must specify excel file - exit")
        return

    isodata = pd.read_excel(options.get("isoexcel"))
    isodata = isodata.loc[  ~pd.isnull(isodata.ISOcodeEdited)& (~isodata.ISOcodeEdited.isin(IGNORE))]
    print(len(isodata))
    # The preloading option is responsible for downloading multiple
    # pages from the wiki simultaneously.
    isogen = lang_isocode_generator_df(isocodedf = isodata, thissite = globalsite)
    gen = gen_factory.getCombinedGenerator(gen = isogen, preload=True)
    
    # check if further help is needed
    if not pwb.bot.suggest_help(missing_generator=not gen):
        print("running")
        # pass generator and private options to the bot
        bot = BudgieBot(generator=gen, **options)
        bot.run()  

if __name__ == '__main__':
    main()