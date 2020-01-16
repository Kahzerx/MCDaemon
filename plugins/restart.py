 
def onServerInfo(server, info):
  if (info.isPlayer == 0):
    pass
  else:
    if info.content.startswith('!!restart'):
      server.say('reiniciando')
      server.stop()
      server.start()