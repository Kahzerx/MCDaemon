#!/bin/bash
# -*- coding: utf-8 -*-
# this file includes basic minecraft server class functions

from subprocess import Popen, PIPE
import select
import fcntl, os
import time
import sys
import traceback
import threading
import mcdplugin
from mcdlog import *
import serverinfoparser

stop_flag = 0

  
def listplugins(plugins):
  result = ''
  result = result + 'loaded plugins:\n'
  for singleplugin in plugins.plugins:
    result = result +str(singleplugin) + '\n'
  result = result +'loaded startup plugins:\n'
  for singleplugin in plugins.startupPlugins:
    result = result +str(singleplugin) + '\n'
  result = result + 'loaded onPlayerJoin plugins:\n'
  for singleplugin in plugins.onPlayerJoinPlugins:
    result = result + str(singleplugin) + '\n'
  result = result +'loaded onPlayerLeavePlugins plugins:\n'
  for singleplugin in plugins.onPlayerLeavePlugins:
    result = result +str(singleplugin) + '\n'
  return result

def getInput(server):
  inp = ''
  while True:
    inp = input()
    if inp != '' :
      if inp == 'stop':
        server.cmdstop()
      elif inp == 'MCDReload':
        print('Recargando...')
        plugins.initPlugins()
        plugins_inf = listplugins(plugins)
        for singleline in plugins_inf.splitlines():
          print(singleline)
      else:
        server.execute(inp)

class Server(object):
  def __init__(self):
    self.start()

  def start(self):
    self.process = Popen('./start.sh', stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
    flags = fcntl.fcntl(self.process.stdout, fcntl.F_GETFL)
    fcntl.fcntl(self.process.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    log('Servidor ejecutandose en PID:'+str(self.process.pid))

  def tick(self):
    try:
      global stop_flag
      receive = self.recv().decode('utf-8')
      if receive != '':
        print(receive)
        for line in receive.splitlines():
          if line[11:].startswith('[Server Shutdown Thread/INFO]: Stopping server') or line[11:].startswith('[Server thread/INFO]: Stopping server'):
            if stop_flag > 0:
              log('plugin reinicio el server')
            else:
              log('El server se detuvo. Reiniciando...')
              sys.exit(0)
            stop_flag -= 1
          if line[11:].startswith('[Server Watchdog/FATAL]: A single server tick'):
            exitlog('single tick took too long for server and watchdog forced the server off', 1)
            sys.exit(0)
          result = serverinfoparser.parse(line)
          if (result.isPlayer == 1) and (result.content == '!!MCDReload'):
            try:
              self.say('[MCDaemon] :Recargando plugins')
              plugins.initPlugins()
              plugins_inf = listplugins(plugins)
              for singleline in plugins_inf.splitlines():
                server.say(singleline)
            except:
              server.say('error inicializando plugins, comprueba la consola para mas informacion')
              errlog('error inicializando plugins, traceback.', traceback.format_exc())
          elif (result.isPlayer == 0) and(result.content.endswith('joined the game')):
            player = result.content.split(' ')[0]
            for singleplugin in plugins.onPlayerJoinPlugins:
              try:
                t =threading.Thread(target=singleplugin.onPlayerJoin,args=(server, player))
                t.setDaemon(True)
                t.start()
              except:
                errlog('error procesando plugin: ' + str(singleplugin), traceback.format_exc())
          elif (result.isPlayer == 0) and(result.content.endswith('left the game')):
            player = result.content.split(' ')[0]
            for singleplugin in plugins.onPlayerLeavePlugins:
              try:
                t =threading.Thread(target=singleplugin.onPlayerLeave,args=(server, player))
                t.setDaemon(True)
                t.start()
              except:
                errlog('error procesando plugin: ' + str(singleplugin), traceback.format_exc())
          for singleplugin in plugins.plugins:
            t =threading.Thread(target=self.callplugin,args=(result, singleplugin))
            t.setDaemon(True)
            t.start()
        time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
      self.stop()
      sys.exit(0) 

  def send(self, data): #enviar string a STDIN
    self.process.stdin.write(data.encode())
    self.process.stdin.flush()

  def execute(self, data , tail = '\n'): #ejecutar comando en STDIN
    self.send(data + tail)

  def recv(self, t=0.1): #devuelve STDOUT
    r = ''
    pr = self.process.stdout
    while True:
      if not select.select([pr], [], [], 0.1)[0]:
        time.sleep(t)
        continue
      r = pr.read()
      return r.rstrip()
    return r.rstrip()

  def cmdstop(self): #detiene el server usando comandos
    self.send('stop\n')

  def forcestop(self): #detiene el proceso del server, no usar a no ser que sea totalmente necesario
    try:
      self.process.kill()
    except:
      raise RuntimeError
      
  def stop(self):
    global stop_flag
    stop_flag = 2
    self.cmdstop()
    try:
      self.forcestop()
      log('server detenido forzosamente')
    except:
      pass
    
  def say(self, data):
    self.execute('tellraw @a {"text":"' + str(data) + '"}')

  def tell(self, player, data):
    self.execute('tellraw '+ player + ' {"text":"' + str(data) + '"}')
    
  def callplugin(self, result, plugin):
    try:
      plugin.onServerInfo(self, result)
    except:
      errlog('error procesando plugin: ' + str(plugin), traceback.format_exc())
    

if __name__ == "__main__":
  log('inicializando plugins')
  try:
    import mcdplugin
    plugins = mcdplugin.mcdplugin()
    plugins_inf = listplugins(plugins)
    print(plugins_inf)
  except:
    errlog('error inicializando plugins, traceback.', traceback.format_exc())
    sys.exit(0)
  try:
    server = Server()
  except:
    exitlog('fallo al iniciar el server.', 1, traceback.format_exc())
    sys.exit(0)
  for singleplugin in plugins.startupPlugins:
    try:
      t =threading.Thread(target=singleplugin.onServerStartup,args=(server, ))
      t.setDaemon(True)
      t.start()
    except:
      errlog('error iniciando startup plugins,printing traceback.', traceback.format_exc())
  cmd =threading.Thread(target=getInput,args=(server, ))
  cmd.setDaemon(True)
  cmd.start()
  while True:
    try:
      server.tick()
    except (SystemExit,IOError):
      log('el servidor se detuvo')
      sys.exit(0)
    except:
      errlog('error ticking MCD')
      print(traceback.format_exc())
      server.stop()
      sys.exit(0)

