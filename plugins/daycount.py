import datetime

startday = datetime.datetime.strptime('2018-11-09', '%Y-%m-%d')

def onServerInfo(server, info):
  if info.isPlayer == 1:
    if info.content.startswith('!!day'):
      server.say('Han pasado ' + getday() + ' dias')

def getday():
  now = datetime.datetime.now()
  output = now - startday
  return str(output.days)