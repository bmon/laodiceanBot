"""
An example IRC log bot - logs a channel's events to a file.

If someone says the bot's name in the channel followed by a ':',
e.g.

  <foo> logbot: hello!

the bot will reply:

  <logbot> foo: I am a log bot

Run this script with two arguments, the channel name the bot should
connect to, and file to log to, e.g.:

  $ python ircLogBot.py test test.log

will log channel #test to the file 'test.log'.
"""



# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

# system imports
import time, sys, random

class WordGame():
    wordList = open("dictionary.txt","rU")
    consonants = "bcdfghjklmnpqrstvwxyz"
    vowels = "aeiou"
    
    def __init__(self):
        self.takingWords = False
        
    def newGame(self):
        self.bestWord = ["",""]
        self.originals = []
        j = random.randint(5,9)
        for i in range(j):
            self.originals.append(self.consonants[random.randint(0,20)])
        for i in range(10-j):
            self.originals.append(self.vowels[random.randint(0,4)])
        self.startTime = time.time()
        self.takingWords = True
        
        #for line.strip() in self.wordList:
        
        return "The Letters are: "+"".join(self.originals)

    def takeWord(self,user,msg):
        if self.startTime + 30 > time.time():
            if self.checkWord(user,msg.lower()) == 1:
                return str("Best word is '"+self.bestWord[0]+"'")
        else:
            return self.endGame()
            
    def endGame(self):
        self.takingWords = False
        if self.bestWord[0] != "":
            return str("Best word was '"+self.bestWord[0]+"' by "+self.bestWord[1]+".")
        else:
            return str("Nobody got a word!")
        

                        
    def checkWord(self,user,word):
        print "Checking:",word
        self.letters = self.originals[::]
        for letter in word:
            print letter,"".join(self.letters),"".join(self.originals) 
            if letter in self.originals and letter in self.letters:
                print "Removing",letter
                self.letters.remove(letter)
                continue
            else:
                return
        print "Letters passed."
        print word, self.bestWord[0]
        if len(word) > len(self.bestWord[0]):
            print "Larger."
            for line in self.wordList:
                if line.strip() == word:
                    print "Updating best word."
                    self.bestWord[0] = word
                    self.bestWord[1] = user
                    return 1

    
    
class MessageLogger:
    """
    An independent logger class (because separation of application
    and protocol logic is a good thing).
    """
    def __init__(self, file):
        self.file = file

    def log(self, message):
        """Write a message to the file."""
        timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
        self.file.write('%s %s\n' % (timestamp, message))
        self.file.flush()

    def close(self):
        self.file.close()


class LogBot(irc.IRCClient):
    """A logging IRC bot."""
    
    nickname = "Botten_Lao"
    wordGame = WordGame()
    
    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.logger = MessageLogger(open(self.factory.filename, "a"))
        self.logger.log("[connected at %s]" % 
                        time.asctime(time.localtime(time.time())))

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.logger.log("[disconnected at %s]" % 
                        time.asctime(time.localtime(time.time())))
        self.logger.close()


    # callbacks for events

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.channel)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        self.logger.log("[I have joined %s]" % channel)

    def irc_JOIN(self, prefix, params):
            msg = ""
            if "tpg" in prefix:
                msg = "L0L TPG"
            elif "freenode" in prefix:
                msg = "Freenoder :D (see what I did there?)"
            elif "exetel" in prefix:
                msg = "Exetel :)"
            self.msg(self.factory.channel, msg)
                
                
    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]
        self.logger.log("<%s> %s" % (user, msg))
        print msg
        
        # Check to see if they're sending me a private message
        if channel == self.nickname:
            if user == "LaoD" or "Laodicean" or "Laodic3an":
                if msg != "!wordgame":
                    self.msg(self.factory.channel, msg)
                else:
                    msg = self.wordGame.newGame()
                    self.msg(self.factory.channel, msg)
            else:
                msg = "It isn't nice to whisper!  Play nice with the group."
                self.msg(user, msg)

        # Otherwise check to see if it is a message directed at me
        if msg.startswith(self.nickname):
            msg = "%s: I am a bot!" % user
            self.msg(channel, msg)
            self.logger.log("<%s> %s" % (self.nickname, msg))
        
        if "!wordgame" == msg.lower() and not self.wordGame.takingWords:
            msg = self.wordGame.newGame()
            self.msg(self.factory.channel, msg)

        elif "ping" == msg.lower():
            msg = "pong!"
            self.msg(channel, msg)

        if self.wordGame.takingWords == True:
            msg = self.wordGame.takeWord(user,msg)
            if msg != None:
                self.msg(channel, msg)
        
    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        user = user.split('!', 1)[0]
        self.logger.log("* %s %s" % (user, msg))

    # irc callbacks

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        self.logger.log("%s is now known as %s" % (old_nick, new_nick))


    # For fun, override the method that determines how a nickname is changed on
    # collisions. The default method appends an underscore.
    def alterCollidedNick(self, nickname):
        """
        Generate an altered version of a nickname that caused a collision in an
        effort to create an unused related name for subsequent registration.
        """
        return nickname + '_'



class LogBotFactory(protocol.ClientFactory):
    """A factory for LogBots.

    A new protocol instance will be created each time we connect to the server.
    """

    def __init__(self, channel, filename):
        self.channel = channel
        self.filename = filename

    def buildProtocol(self, addr):
        p = LogBot()
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()


if __name__ == '__main__':
    # initialize logging
    log.startLogging(sys.stdout)
    
    # create factory protocol and application
    f = LogBotFactory(sys.argv[1], sys.argv[2])

    # connect factory to this host and port
    reactor.connectTCP("irc.freenode.net", 6667, f)

    # run bot
    reactor.run()
