##
# Copyright (c) 2012, spline
# All rights reserved.
#
#
###

from BeautifulSoup import BeautifulSoup
import urllib2
import re
import collections
from itertools import izip, groupby, count

import datetime
import string
import sqlite3

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('MLB')

@internationalizeDocstring
class MLB(callbacks.Plugin):
    """Add the help for "@plugin help MLB" here
    This should describe *how* to use this plugin."""
    threaded = True
   
    def _validate(self, date, format):
        """Check if date is valid. Return true or false"""
        try:
            datetime.datetime.strptime(date, format) # format = "%m/%d/%Y"
            return True
        except ValueError:
            return False

    # http://code.activestate.com/recipes/303279/#c7
    def _batch(self, iterable, size):
        c = count()
        for k, g in groupby(iterable, lambda x:c.next()//size):
            yield g

    def _validteams(self):
        """Returns a list of valid teams for input verification."""
        db_filename = self.registryValue('dbLocation')
        with sqlite3.connect(db_filename) as conn:
            cursor = conn.cursor()
            query = "select team from mlb"
            cursor.execute(query)
            teamlist = []
            for row in cursor.fetchall():
                teamlist.append(str(row[0]))

        return teamlist
    
    def _translateTeam(self, db, column, optteam):
        """Translates optteam into proper string using database"""
        db_filename = self.registryValue('dbLocation')
        with sqlite3.connect(db_filename) as conn:
            cursor = conn.cursor()
            query = "select %s from mlb where %s='%s'" % (db, column, optteam)
            self.log.info(query)
            cursor.execute(query)
            row = cursor.fetchone()
            
            return (str(row[0]))

    def mlbteams(self, irc, msg, args):
        """Display a list of valid teams for input."""
        
        teams = self._validteams()
        
        irc.reply("Valid teams are: %s" % (string.join([item for item in teams], " | ")))

    mlbteams = wrap(mlbteams)
    
    def baseball(self, irc, msg, args):
        """Display a silly baseball."""
    
        irc.reply("    ____     ")
        irc.reply("  .'    '.   ")
        irc.reply(" /'-....-'\  ")
        irc.reply(" |        |  ")
        irc.reply(" \.-''''-./  ")
        irc.reply("  '.____.'   ")
    
    baseball = wrap(baseball)
                
    # mlbscores. use gd2 (gameday) data.
    def mlbscores(self, irc, msg, args, optdate):
        """[date]
        Display current MLB scores.
        """
        import xmltodict
                    
        url = 'http://gd2.mlb.com/components/game/mlb/year_%s/month_%s/day_%s/miniscoreboard.xml' % (year, month, day)

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failed to fetch: %s" % url)
            return

        doc = xmltodict.parse(html)
        games = doc['games']['game'] # always there.

        object_list = []

        for each in games:
            d = collections.OrderedDict()
            d['outs'] = str(each.get('@outs', None))
            d['top_inning'] = str(each.get('@top_inning', None))
            d['inning'] = str(each.get('@inning', None))
            d['awayteam'] = str(each.get('@away_name_abbrev', None))
            d['hometeam'] = str(each.get('@home_name_abbrev', None))
            d['awayruns'] = str(each.get('@away_team_runs', None))
            d['homeruns'] = str(each.get('@home_team_runs', None))
            d['time'] = str(each.get('@time', None))
            d['ampm'] = str(each.get('@ampm', None))
            d['status'] = str(each.get('@status', None))
            object_list.append(d)

        for each in object_list:
            irc.reply(each)
    
    mlbscores = wrap(mlbscores, [optional('somethingWithoutSpaces')])

    # display various nba award winners.
    def mlbawards(self, irc, msg, args, optyear):
        """<year>
        Display various MLB awards for current (or previous) year. Use YYYY for year. Ex: 2011
        """
        
        if optyear: # crude way to find the latest awards.
            testdate = self._validate(optyear, '%Y')
            if not testdate:
                irc.reply("Invalid year. Must be YYYY.")
                return
        else:
            url = 'http://www.baseball-reference.com/awards/'
            req = urllib2.Request(url)
            response = urllib2.urlopen(req)
            html = response.read()
            soup = BeautifulSoup(html) #
            link = soup.find('big', text="Baseball Award Voting Summaries").findNext('a')['href'].strip()
            optyear = ''.join(i for i in link if i.isdigit())

        url = 'http://www.baseball-reference.com/awards/awards_%s.shtml' % optyear

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failure to load: %s" % url)
            return

        # soup
        soup = BeautifulSoup(html)
        alvp = soup.find('h2', text="AL MVP Voting").findNext('table', attrs={'id':'AL_MVP_voting'}).findNext('a').text
        nlvp = soup.find('h2', text="NL MVP Voting").findNext('table', attrs={'id':'NL_MVP_voting'}).findNext('a').text
        alcy = soup.find('h2', text="AL Cy Young Voting").findNext('table', attrs={'id':'AL_Cy_Young_voting'}).findNext('a').text
        nlcy = soup.find('h2', text="NL Cy Young Voting").findNext('table', attrs={'id':'NL_Cy_Young_voting'}).findNext('a').text
        alroy = soup.find('h2', text="AL Rookie of the Year Voting").findNext('table', attrs={'id':'AL_Rookie_of_the_Year_voting'}).findNext('a').text
        nlroy = soup.find('h2', text="NL Rookie of the Year Voting").findNext('table', attrs={'id':'NL_Rookie_of_the_Year_voting'}).findNext('a').text
        almgr = soup.find('h2', text="AL Mgr of the Year Voting").findNext('table', attrs={'id':'AL_Mgr_of_the_Year_voting'}).findNext('a').text
        nlmgr = soup.find('h2', text="NL Mgr of the Year Voting").findNext('table', attrs={'id':'NL_Mgr_of_the_Year_voting'}).findNext('a').text

        output = "{0} MLB Awards :: MVP: AL {1} NL {2}  CY: AL {3} NL {4}  ROY: AL {5} NL {6}  MGR: AL {6} NL {7}".format( \
            ircutils.mircColor(optyear, 'red'), ircutils.bold(alvp),ircutils.bold(nlvp), \
            ircutils.bold(alcy),ircutils.bold(nlcy),ircutils.bold(alroy),ircutils.bold(nlroy), ircutils.bold(almgr),ircutils.bold(nlmgr))

        irc.reply(output)

    mlbawards = wrap(mlbawards, [optional('somethingWithoutSpaces')])
    
    # display upcoming next 5 games.
    def mlbschedule(self, irc, msg, args, optteam):
        """[team]
        Display the last and next five upcoming games for team.
        """
        
        optteam = optteam.upper().strip()

        if optteam not in self._validteams():
            irc.reply("Team not found. Must be one of: %s" % self._validteams())
            return
            
        lookupteam = self._translateTeam('yahoo', 'team', optteam) # (db, column, optteam)

        url = 'http://sports.yahoo.com/mlb/teams/%s/calendar/rss.xml' % lookupteam
        
        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Cannot open: %s" % url)
            return
            
        if "Schedule for" not in html:
            irc.reply("Cannot find schedule. Broken url?")
            return
            
        # clean this stuff up
        html = html.replace('<![CDATA[','') #remove cdata
        html = html.replace(']]>','') # end of cdata
        html = html.replace('EDT','') # tidy up times
        html = html.replace('\xc2\xa0','') # remove some stupid character.

        soup = BeautifulSoup(html)
        items = soup.find('channel').findAll('item')

        append_list = []

        for item in items:
            title = item.find('title').renderContents().strip() # title is good.
            day, date = title.split(',')
            desc = item.find('description') # everything in desc but its messy.
            desctext = desc.findAll(text=True) # get all text, first, but its in a list.
            descappend = (''.join(desctext).strip()) # list transform into a string.
            if not descappend.startswith('@'): # if something is @, it's before, but vs. otherwise.
                descappend = 'vs. ' + descappend
            descappend += " [" + date.strip() + "]" # can't translate since Yahoo! sucks with the team names here. 
            append_list.append(descappend) # put all into a list.

        descstring = string.join([item for item in append_list], " | ")
        output = "{0} {1}".format(ircutils.bold(optteam), descstring)
        
        irc.reply(output)

    mlbschedule = wrap(mlbschedule, [('somethingWithoutSpaces')])

    def mlbmanager(self, irc, msg, args, optteam):
        """[team]
        Display the manager for team.
        """
        
        optteam = optteam.upper().strip()

        if optteam not in self._validteams():
            irc.reply("Team not found. Must be one of: %s" % self._validteams())
            return

        # build the url and request.
        url = 'http://espn.go.com/mlb/managers'

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Cannot fetch URL: %s" % url)
            return

        # change some strings to parse better.
        html = html.replace('class="evenrow', 'class="oddrow')

        soup = BeautifulSoup(html)
        rows = soup.findAll('tr', attrs={'class':'oddrow'})

        object_list = []

        for row in rows:
            manager = row.find('td').find('a')
            exp = manager.findNext('td')
            record = exp.findNext('td')
            team = record.findNext('td').find('a').renderContents().strip()
            
            d = collections.OrderedDict()
            d['manager'] = manager.renderContents().strip().replace('  ',' ') 
            d['exp'] = exp.renderContents().strip()
            d['record'] = record.renderContents().strip()
            d['team'] = self._translateTeam('team', 'fulltrans', team) # translate from full to short
            object_list.append(d)

        for each in object_list:
            if each['team'] == optteam:
                output = "Manager of {0} is {1}({2}) with {3} years experience.".format( \
                    ircutils.bold(each['team']), ircutils.bold(each['manager']), each['record'], each['exp'])
                irc.reply(output)

    mlbmanager = wrap(mlbmanager, [('somethingWithoutSpaces')])

    # alternative: http://erikberg.com/mlb/standings-wildcard.xml
    # http://espn.go.com/mlb/standings/_/type/wild-card
    def mlbstandings(self, irc, msg, args, optlist, optdiv):
        """<ALE|ALC|ALW|NLC|NLC|NLW>
        Display divisional standings for a division.
        """

        expanded, vsdivision = False, False
        for (option, arg) in optlist:
            if option == 'expanded':
                expanded = True
            if option == 'vsdivision':
                vsdivision = True

        # lower the div to match against leaguetable
        optdiv = optdiv.lower()
        leaguetable =   { 
                            'ale': {'league':'American League', 'division':'EAST' },
                            'alc': {'league':'American League', 'division':'CENTRAL' },
                            'alw': {'league':'American League', 'division':'WEST' },
                            'nle': {'league':'National League', 'division':'EAST' },
                            'nlc': {'league':'National League', 'division':'CENTRAL' },
                            'nlw': {'league':'National League', 'division':'WEST' }
                        }

        # sanity check to make sure we have a league.
        if optdiv not in leaguetable:
            irc.reply("League must be one of: %s" % leaguetable.keys())
            return

        # now, go to work.
        if expanded:
            url = 'http://espn.go.com/mlb/standings/_/type/expanded'
        elif vsdivision:
            url = 'http://espn.go.com/mlb/standings/_/type/vs-division'
        else:
            url = 'http://espn.go.com/mlb/standings'

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Problem opening up: %s" % url)
            return
        
        # change to help parsing rows
        html = html.replace('class="evenrow', 'class="oddrow')

        # soup time.
        soup = BeautifulSoup(html)
        rows = soup.findAll('tr', attrs={'class': re.compile('^oddrow*')})

        object_list = []

        for row in rows:
            team = row.find('td', attrs={'align':'left'}).find('a')
            wins = team.findNext('td')
            loss = wins.findNext('td')
            wpct = loss.findNext('td')
            gmsb = wpct.findNext('td')
            home = gmsb.findNext('td')
            road = home.findNext('td')
            rs = road.findNext('td')
            ra = rs.findNext('td')
            diff = ra.findNext('td')
            strk = diff.findNext('td')
            if not vsdivision:
                l10 = strk.findNext('td')
            if not expanded and not vsdivision:
                poff = l10.findNext('td')

            div = row.findPrevious('tr', attrs={'class':'colhead'}).findNext('td', attrs={'align':'left'}) 

            if vsdivision:
                league = row.findPrevious('tr', attrs={'class':'stathead'}).findNext('td', attrs={'colspan': re.compile('^11')})
            elif expanded:
                league = row.findPrevious('tr', attrs={'class':'stathead'}).findNext('td', attrs={'colspan': re.compile('^12')})
            else:
                league = row.findPrevious('tr', attrs={'class':'stathead'}).findNext('td', attrs={'colspan': re.compile('^13')})

            # now putting into a dict. cleanup.
            d = collections.OrderedDict()
            d['league'] = league.renderContents().strip()
            d['div'] = div.renderContents().strip()
            d['team'] = team.renderContents().strip()
            d['wins'] = wins.renderContents().strip()
            d['loss'] = loss.renderContents().strip()
            d['wpct'] = wpct.renderContents().strip()
            d['gmsb'] = gmsb.renderContents().strip()
            d['home'] = home.renderContents().strip()
            d['road'] = road.renderContents().strip()
            d['rs'] = rs.renderContents().strip()
            d['ra'] = ra.renderContents().strip()
            if expanded or vsdivision:
                d['diff'] = diff.renderContents().strip()
            else:
                d['diff'] = diff.find('span').renderContents().strip()
            d['strk'] = strk.renderContents().strip()
            if not vsdivision:
                d['l10'] = l10.renderContents().strip()
            if not expanded and not vsdivision:
                d['poff'] = poff.renderContents().strip()

            object_list.append(d)

        if expanded:
            header = "{0:15} {1:3} {2:3} {3:5} {4:5} {5:8} {6:8} {7:4} {8:8} {9:8} {10:<7} {11:6}".format( \
                    "Team", "W", "L", "PCT", "GB", "DAY", "NIGHT", "GRASS", "TURF", "1-RUN", "XTRA", "ExWL")
        elif vsdivision:
            header = "{0:15} {1:3} {2:3} {3:5} {4:5} {5:8} {6:8} {7:4} {8:8} {9:8} {10:<7}".format( \
                    "Team", "W", "L", "PCT", "GB", "EAST", "CENT", "WEST", "INTR", "RHP", "LHP")
        else:
            header = "{0:15} {1:3} {2:3} {3:5} {4:5} {5:8} {6:8} {7:4} {8:4} {9:4} {10:<7} {11:6} {12:6}".format( \
                    "Team", "W", "L", "PCT", "GB", "HOME", "ROAD", "RS", "RA", "DIFF", "STRK", "L10", "POFF")

        irc.reply(header)

        for tm in object_list:
            if tm['league'] == leaguetable[optdiv].get('league') and tm['div'] == leaguetable[optdiv].get('division'):
                if expanded:
                    output = "{0:15} {1:3} {2:3} {3:5} {4:5} {5:8} {6:8} {7:4} {8:8} {9:8} {10:<7} {11:6}".format( \
                    tm['team'], tm['wins'], tm['loss'], tm['wpct'], tm['gmsb'], tm['home'], tm['road'], tm['rs'], \
                    tm['ra'], tm['diff'], tm['strk'], tm['l10'])
                elif vsdivision:
                    output = "{0:15} {1:3} {2:3} {3:5} {4:5} {5:8} {6:8} {7:4} {8:8} {9:8} {10:<7}".format( \
                    tm['team'], tm['wins'], tm['loss'], tm['wpct'], tm['gmsb'], tm['home'], tm['road'], tm['rs'], \
                    tm['ra'], tm['diff'], tm['strk'])
                else:
                    output = "{0:15} {1:3} {2:3} {3:5} {4:5} {5:8} {6:8} {7:4} {8:4} {9:4} {10:<7} {11:6} {12:6}".format( \
                    tm['team'], tm['wins'], tm['loss'], tm['wpct'], tm['gmsb'], tm['home'], tm['road'], tm['rs'], \
                    tm['ra'], tm['diff'], tm['strk'], tm['l10'], tm['poff']) 

                irc.reply(output)

    mlbstandings = wrap(mlbstandings, [getopts({'expanded':'', 'vsdivision':''}), ('somethingWithoutSpaces')])
    
    def mlblineup(self, irc, msg, args, optteam):
        """<team>
        Gets lineup for MLB team. Example: NYY
        """

        optteam = optteam.upper().strip()
        
        if optteam not in self._validteams():
            irc.reply("Team not found. Must be one of: %s" % self._validteams())
            return
                    
        url = 'http://m.espn.go.com/mlb/lineups?wjb='
        
        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Problem fetching: %s" % url)
            return

        # have to do some replacing for the regex to work
        html = html.replace('<b  >', '<b>')
        html = html.replace('<b>TAM</b>','<b>TB</b>')
        html = html.replace('<b>WAS</b>','<b>WSH</b>')
        html = html.replace('<b>CHW</b>','<b>CWS</b>')

        outdict = {}

        for matches in re.findall(r'<b>(\w\w+)</b>(.*?)</div>', html, re.I|re.S|re.M):
            team = matches[0].strip()
            lineup = matches[1].strip()
            out = {team:lineup}
            outdict.update(out)

        lineup = outdict.get(optteam)
        if lineup != None:
            output = "{0:5} - {1:150}".format(ircutils.bold(optteam), lineup)
            irc.reply(output)
        else:
            irc.reply("Could not find lineup. Check closer to game time.")
            return

    mlblineup = wrap(mlblineup, [('somethingWithoutSpaces')])
    
    # display short as default. offer --details option.
    def mlbinjury(self, irc, msg, args, optlist, optteam):
        """<--details> [TEAM]
        Show all injuries for team. Example: BOS or NYY. Use --details to 
        display full table with team injuries.
        """
        
        details = False
        for (option, arg) in optlist:
            if option == 'details':
                details = True
        
        optteam = optteam.upper().strip()
        
        if optteam not in self._validteams():
            irc.reply("Team not found. Must be one of: %s" % self._validteams())
            return
        
        lookupteam = self._translateTeam('roto', 'team', optteam) 

        url = 'http://rotoworld.com/teams/injuries/mlb/%s/' % lookupteam

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failed to grab: %s" % url)
            return

        soup = BeautifulSoup(html)
        team = soup.find('div', attrs={'class': 'player'}).find('a').text
        table = soup.find('table', attrs={'align': 'center', 'width': '600px;'})
        t1 = table.findAll('tr')

        object_list = []

        for row in t1[1:]:
            td = row.findAll('td')
            d = collections.OrderedDict()
            d['name'] = td[0].find('a').text
            d['position'] = td[2].renderContents().strip()
            d['status'] = td[3].renderContents().strip()
            d['date'] = td[4].renderContents().strip().replace("&nbsp;", " ")
            d['injury'] = td[5].renderContents().strip()
            d['returns'] = td[6].renderContents().strip()
            object_list.append(d)

        if len(object_list) < 1:
            irc.reply("No injuries for: %s" % team)

        if details:
            irc.reply(ircutils.underline(str(team)) + " - " + str(len(object_list)) + " total injuries")
            irc.reply("{0:25} {1:3} {2:6} {3:<7} {4:<15} {5:<10}".format("Name","POS","Status","Date","Injury","Returns"))

            for inj in object_list:
                output = "{0:27} {1:<3} {2:<6} {3:<7} {4:<15} {5:<10}".format(ircutils.bold( \
                    inj['name']),inj['position'],inj['status'],inj['date'],inj['injury'],inj['returns'])
                irc.reply(output)
        else:
            irc.reply(ircutils.underline(str(team)) + " - " + str(len(object_list)) + " total injuries")
            irc.reply(string.join([item['name'] + " (" + item['returns'] + ")" for item in object_list], " | "))

    mlbinjury = wrap(mlbinjury, [getopts({'details':''}), ('somethingWithoutSpaces')])

    #23:51 <laburd> @injury cle  returns: player 1, player 2, player 3.. on one line
    #23:51 <laburd> then if you want the injur details you do
    #23:51 <laburd> @injury player
    #23:51 <laburd> It cuts the spam down by an order of magnitude

    def mlbpowerrankings(self, irc, msg, args):
        """
        Display this week's MLB Power Rankings.
        """
        
        url = 'http://espn.go.com/mlb/powerrankings' 

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failed to fetch: %s" % url)
            return
            
        html = html.replace("evenrow", "oddrow")

        soup = BeautifulSoup(html)
        table = soup.find('table', attrs={'class': 'tablehead'})
        prdate = table.find('td', attrs={'colspan': '6'}).renderContents()
        t1 = table.findAll('tr', attrs={'class': 'oddrow'})

        if len(t1) < 30:
            irc.reply("Failed to parse MLB Power Rankings. Did something break?")
            return

        object_list = []

        for row in t1:
            rowrank = row.find('td', attrs={'class': 'pr-rank'}).renderContents().strip()
            rowteam = row.find('div', attrs={'style': re.compile('^padding.*')}).find('a').text.strip()
            rowrecord = row.find('span', attrs={'class': 'pr-record'}).renderContents().strip()
            rowlastweek = row.find('span', attrs={'class': 'pr-last'}).renderContents().strip().replace("Last Week", "prev") 

            d = collections.OrderedDict()
            d['rank'] = int(rowrank)
            d['team'] = str(rowteam)
            d['record'] = str(rowrecord)
            d['lastweek'] = str(rowlastweek)
            object_list.append(d)

        if len(object_list) < 30:
            irc.reply("Failed to parse the list. Check your code and formatting.")
            return

        if prdate:
            irc.reply(ircutils.mircColor(prdate, 'blue'))

        for N in self._batch(object_list, 6):
            irc.reply(' '.join(str(str(n['rank']) + "." + " " + ircutils.bold(n['team'])) + " (" + n['lastweek'] + ")" for n in N))
        
    mlbpowerrankings = wrap(mlbpowerrankings)

    def mlbteamleaders(self, irc, msg, args, optteam, optcategory):
        """[TEAM] [category]
        Display team leaders in stats for a specific team in category.
        """

        optteam = optteam.upper().strip()
        optcategory = optcategory.lower().strip()
        
        if optteam not in self._validteams():
            irc.reply("Team not found. Must be one of: %s" % self._validteams())
            return
            
        category = {'avg':'avg', 'hr':'homeRuns', 'rbi':'RBIs', 'r':'runs', 'ab':'atBats', 'obp':'onBasePct', 
                    'slug':'slugAvg', 'ops':'OPS', 'sb':'stolenBases', 'runscreated':'runsCreated',
                    'w': 'wins', 'l': 'losses', 'win%': 'winPct', 'era': 'ERA',  'k': 'strikeouts', 
                    'k/9ip': 'strikeoutsPerNineInnings', 'holds': 'holds', 's': 'saves',
                    'gp': 'gamesPlayed', 'cg': 'completeGames', 'qs': 'qualityStarts', 'whip': 'WHIP' }

        if optcategory not in category:
            irc.reply("Error. Category must be one of: %s" % category.keys())
            return

        lookupteam = self._translateTeam('eid', 'team', optteam)

        url = 'http://m.espn.go.com/mlb/teamstats?teamId=%s&season=2012&lang=EN&category=%s&y=1&wjb=' % (lookupteam, category[optcategory])

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failed to fetch: %s" % url)
            return

        html = html.replace('<b  >', '<b>')
        html = html.replace('class="ind alt', 'class="ind')
        html = html.replace('class="ind tL', 'class="ind')

        soup = BeautifulSoup(html)
        table = soup.find('table', attrs={'class':'table'})
        rows = table.findAll('tr')

        object_list = []

        for row in rows[1:6]: # grab the first through ten.
            rank = row.find('td', attrs={'class':'ind', 'width': '10%'}).renderContents().strip()
            player = row.find('td', attrs={'class':'ind', 'width': '65%'}).find('a').renderContents().strip()
            stat = row.find('td', attrs={'class':'ind', 'width': '25%'}).renderContents().strip()
            object_list.append(rank + ". " + player + " " + stat)

        thelist = string.join([item for item in object_list], " | ")
        irc.reply("Leaders in %s for %s: %s" % (ircutils.bold(optteam.upper()), ircutils.bold(optcategory.upper()), thelist))

    mlbteamleaders = wrap(mlbteamleaders, [('somethingWithoutSpaces'), ('somethingWithoutSpaces')])

    def mlbleagueleaders(self, irc, msg, args, optleague, optcategory):
        """[MLB|AL|NL] [category] 
        Display leaders (top 5) in category for teams in the MLB.
        Categories: hr, avg, rbi, r, sb, era, whip, k 
        """

        league = {'mlb': '9', 'al':'7', 'nl':'8'} # do our own translation here for league/category.
        category = {'avg':'avg', 'hr':'homeRuns', 'rbi':'RBIs', 'r':'runs', 'sb':'stolenBases', 'era':'ERA', 'whip':'whip', 'k':'strikeoutsPerNineInnings'}

        optleague = optleague.lower()
        optcategory = optcategory.lower()

        if optleague not in league:
            irc.reply("League must be one of: %s" % league.keys())
            return

        if optcategory not in category:
            irc.reply("Category must be one of: %s" % category.keys())
            return

        url = 'http://m.espn.go.com/mlb/aggregates?category=%s&groupId=%s&y=1&wjb=' % (category[optcategory], league[optleague])

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failed to fetch: %s" % url)
            return
            
        html = html.replace('class="ind alt nw"', 'class="ind nw"')

        soup = BeautifulSoup(html)
        table = soup.find('table', attrs={'class':'table'})
        rows = table.findAll('tr')
        
        append_list = []
        
        for row in rows[1:6]:
            rank = row.find('td', attrs={'class':'ind nw', 'nowrap':'nowrap', 'width':'10%'}).renderContents()
            team = row.find('td', attrs={'class':'ind nw', 'nowrap':'nowrap', 'width':'70%'}).find('a').text
            num = row.find('td', attrs={'class':'ind nw', 'nowrap':'nowrap', 'width':'20%'}).renderContents()
            append_list.append(rank + ". " + team + " " + num)

        thelist = string.join([item for item in append_list], " | ")

        irc.reply("Leaders in %s for %s: %s" % (ircutils.bold(optleague.upper()), ircutils.bold(optcategory.upper()), thelist))

    mlbleagueleaders = wrap(mlbleagueleaders, [('somethingWithoutSpaces'), ('somethingWithoutSpaces')])

    def mlbrumors(self, irc, msg, args):
        """
        Display the latest mlb rumors.
        """

        url = 'http://m.espn.go.com/mlb/rumors?wjb='

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Something broke trying to read: %s" % url)
            return
        
        html = html.replace('<div class="ind alt">', '<div class="ind">') 

        soup = BeautifulSoup(html)
        t1 = soup.findAll('div', attrs={'class': 'ind'})

        if len(t1) < 1:
            irc.reply("No mlb rumors found. Check formatting?")
            return
        for t1rumor in t1[0:7]:
            # dont print <a href="/mlb/
            item = t1rumor.find('div', attrs={'class': 'noborder bold tL'}).renderContents()
            item = re.sub('<[^<]+?>', '', item)
            rumor = t1rumor.find('div', attrs={'class': 'inline rumorContent'}).renderContents().replace('\r','')
            irc.reply(ircutils.bold(item) + " :: " + rumor)

    mlbrumors = wrap(mlbrumors)

    def mlbteamtrans(self, irc, msg, args, optteam):
        """[team]
        Shows recent MLB transactions for [team]. Ex: NYY
        """
        
        optteam = optteam.upper().strip()

        if optteam not in self._validteams():
            irc.reply("Team not found. Must be one of: %s" % self._validteams())
            return
            
        lookupteam = self._translateTeam('eid', 'team', optteam) 
        
        url = 'http://m.espn.go.com/mlb/teamtransactions?teamId=%s&wjb=' % lookupteam

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failed to load: %s" % url)
            return
        
        html = html.replace('<div class="ind tL"','<div class="ind"').replace('<div class="ind alt"','<div class="ind"')

        soup = BeautifulSoup(html)
        t1 = soup.findAll('div', attrs={'class': 'ind'})

        if len(t1) < 1:
            irc.reply("No transactions found for %s" % optteam)
            return

        for item in t1:
            if "href=" not in str(item):
                trans = item.findAll(text=True)
                irc.reply("{0:8} {1}".format(ircutils.bold(str(trans[0])), str(trans[1])))

    mlbteamtrans = wrap(mlbteamtrans, [('somethingWithoutSpaces')])

    def mlbtrans(self, irc, msg, args, optdate):
        """[YYYYmmDD]
        Display all mlb transactions. Will only display today's. Use date in format: 20120912
        """

        url = 'http://m.espn.go.com/mlb/transactions?wjb='

        if optdate:
            try:
                #time.strptime(optdate, '%Y%m%d') # test for valid date
                datetime.datetime.strptime(optdate, '%Y%m%d')
            except:
                irc.reply("ERROR: Date format must be in YYYYMMDD. Ex: 20120714")
                return
        else:
            now = datetime.datetime.now()
            optdate = now.strftime("%Y%m%d")

        url += '&date=%s' % optdate

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Something broke trying to read: %s" % url)
            return
            
        if "No transactions today." in html:
            irc.reply("No transactions for: %s" % optdate)
            return

        soup = BeautifulSoup(html)
        t1 = soup.findAll('div', attrs={'class': 'ind alt'})
        t1 += soup.findAll('div', attrs={'class': 'ind'})

        out_array = []

        for trans in t1:
            if "<a href=" not in trans: # no links
                match1 = re.search(r'<b>(.*?)</b><br />(.*?)</div>', str(trans), re.I|re.S) #strip out team and transaction
                if match1:
                    team = match1.group(1) 
                    transaction = match1.group(2)
                    output = ircutils.mircColor(team, 'red') + " - " + ircutils.bold(transaction)
                    out_array.append(output)

        if len(out_array) > 0:
            for output in out_array:
                irc.reply(output)
        else:
            irc.reply("Did something break?")
            return
    
    mlbtrans = wrap(mlbtrans, [optional('somethingWithoutSpaces')])

    def mlbprob(self, irc, msg, args, optdate, optteam):
        """[YYYYMMDD] <TEAM>
        Display the MLB probables for date. Defaults to today. To search
        for a specific team, use their abbr. like NYY
        """

        # without optdate and optteam, we only do a single day (today)
        # with optdate and optteam, show only one date with one team
        # with no optdate and optteam, show whatever the stuff today is.
        # with optdate and no optteam, show all matches that day.

        dates = []
        date = datetime.date.today()
        dates.append(date)

        for i in range(4):
                date += datetime.timedelta(days=1)
                dates.append(date)

        out_array = []

        for eachdate in dates:
                outdate = eachdate.strftime("%Y%m%d")
                url = 'http://m.espn.go.com/mlb/probables?wjb=&date=%s' % outdate # date=20120630&wjb=

                try:
                    req = urllib2.Request(url)
                    html = (urllib2.urlopen(req)).read().replace("ind alt tL spaced", "ind tL spaced")
                except:
                    irc.reply("Failed to load: %s" % url)
                    return

                if "No Games Scheduled" in html:
                    irc.reply("No games scheduled this day.")
                    next

                soup = BeautifulSoup(html)
                t1 = soup.findAll('div', attrs={'class': 'ind tL spaced'})

                for row in t1:
                    matchup = row.find('a', attrs={'class': 'bold inline'}).text.strip()
                    textmatch = re.search(r'<a class="bold inline".*?<br />(.*?)<a class="inline".*?=">(.*?)</a>(.*?)<br />(.*?)<a class="inline".*?=">(.*?)</a>(.*?)$', row.renderContents(), re.I|re.S|re.M)
                    d = collections.OrderedDict()
                    d['date'] = outdate
                    d['matchup'] = matchup

                    if textmatch:
                        d['vteam'] = textmatch.group(1).strip().replace(':','')
                        d['vpitcher'] = textmatch.group(2).strip()
                        d['vpstats'] = textmatch.group(3).strip()
                        d['hteam'] = textmatch.group(4).strip().replace(':','')
                        d['hpitcher'] = textmatch.group(5).strip()
                        d['hpstats'] = textmatch.group(6).strip()
                        out_array.append(d)
        
        for eachentry in out_array:
            if optteam:
                if optteam in eachentry['matchup']:
                    irc.reply("{0:25} {1:4} {2:15} {3:12} {4:4} {5:15} {6:12}".format(matchup, vteam, vpitcher,vpstats, hteam, hpitcher, hpstats))

    mlbprob = wrap(mlbprob, [optional('somethingWithoutSpaces'), optional('somethingWithoutSpaces')])

Class = MLB


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=250:
