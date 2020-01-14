from subprocess import Popen, PIPE
import fcntl
import os
import select
import time
import traceback
import threading

stop_flag = 0


def getInput(server):
  inp = ''
  while True:
    inp = input()
    if inp != '':
      if inp == 'stop':
        server.cmdstop()
      else:
        server.execute(inp)


class Server(object):

  def __init__(self):
    self.start()

  def start(self):
    self.process = Popen('./start.sh', stdin=PIPE,
                         stdout=PIPE, stderr=PIPE, shell=True)
    flags = fcntl.fcntl(self.process.stdout, fcntl.F_GETFL)
    fcntl.fcntl(self.process.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    print('Server Running at PID:'+str(self.process.pid))

  def tick(self):
    try:
      global stop_flag
      receive = self.recv().decode('utf-8')
      if receive != '':
          for line in receive.splitlines():
              print(line)
              if line[11:].startswith('[Server Shutdown Thread/INFO]: Stopping server') or line[11:].startswith('[Server thread/INFO]: Stopping server'):
                  print('El servidor se cerró. Saliendo...')
                  os._exit(0)
    except(KeyboardInterrupt, SystemExit):
        self.stop()
        os._exit(0)

  def send(self, data):  # enviar string a STDIN
    self.process.stdin.write(data.encode())
    self.process.stdin.flush()

  def execute(self, data, tail='\n'):  # pone un comando + \n para ejecutar
    self.send(data + tail)

  def recv(self, t=0.1):  # devuelve el ultimo STDOUT
    r = ''
    pr = self.process.stdout
    while True:
      if not select.select([pr], [], [], 0.1)[0]:
        time.sleep(t)
        continue
      r = pr.read()
      return r.rstrip()
    return r.rstrip()

  def cmdstop(self):  # detiene el server usando un comandp
    self.send('stop\n')

  def forcestop(self):  # detiene el server usando pclose, no lo uses hasta que sea necesario
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
      print('forced server to stop')
    except:
      pass

  def say(self, data):
    self.execute('tellraw @a {"text":"' + str(data) + '"}')

  def tell(self, player, data):
    self.execute('tellraw ' + player + ' {"text":"' + str(data) + '"}')


if __name__ == "__main__":
  try:
    server = Server()
  except:
    print('failed to initalize the server.', 1, traceback.format_exc())
    os._exit(0)
  cmd = threading.Thread(target=getInput, args=(server, ))
  cmd.setDaemon(True)
  cmd.start()
  while True:
    try:
      server.tick()
    except (SystemExit, IOError):
      print('server stopped')
      os._exit(0)
    except:
      print('error ticking MCD')
      print(traceback.format_exc())
      server.stop()
      os._exit(0)
