from subprocess import Popen, PIPE
import fcntl
import os
import select
import time
import traceback
import threading
import sys
import serverinfoparser

stop_flag = 0


def listplugins(plugins):
    result = ''
    result = result + 'loaded plugins:\n'
    for singleplugin in plugins.plugins:
        result = result + str(singleplugin) + '\n'
    result = result + 'loaded startup plugins:\n'
    for singleplugin in plugins.startupPlugins:
        result = result + str(singleplugin) + '\n'
    result = result + 'loaded onPlayerJoin plugins:\n'
    for singleplugin in plugins.onPlayerJoinPlugins:
        result = result + str(singleplugin) + '\n'
    result = result + 'loaded onPlayerLeavePlugins plugins:\n'
    for singleplugin in plugins.onPlayerLeavePlugins:
        result = result + str(singleplugin) + '\n'
    return result


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
        print('Server Running at PID:' + str(self.process.pid))

    def tick(self):
        try:
            global stop_flag
            receive = self.recv().decode('utf-8')
            if receive != '':
                for line in receive.splitlines():
                    print(line)
                    if line[11:].startswith('[Server Shutdown Thread/INFO]: Stopping server') or line[11:].startswith(
                            '[Server thread/INFO]: Stopping server'):
                        if stop_flag > 0:
                            print('Plugin called a reboot')
                        else:
                            print('El servidor se detuvo. Saliendo...')
                            sys.exit(0)
                        stop_flag -= 1
                    if line[11:].startswith('[Server Watchdog/FATAL]: A single server tick'):
                        print('single tick took too long for server and watchdog forced the server off', 1)
                        sys.exit(0)
                    result = serverinfoparser.parse(line)
                    if (result.isPlayer == 1) and (result.content == '!!MCDReload'):
                        try:
                            self.say('[MCDaemon] :Reloading plugins')
                            plugins.initPlugins()
                            plugins_inf = listplugins(plugins)
                            for singleline in plugins_inf.splitlines():
                                server.say(singleline)
                        except:
                            server.say('error initalizing plugins,check console for detailed information')
                            print('error initalizing plugins,printing traceback.', traceback.format_exc())
                    elif (result.isPlayer == 0) and (result.content.endswith('joined the game')):
                        player = result.content.split(' ')[0]
                        for singleplugin in plugins.onPlayerJoinPlugins:
                            try:
                                t = threading.Thread(target=singleplugin.onPlayerJoin, args=(server, player))
                                t.setDaemon(True)
                                t.start()
                            except:
                                print('error processing plugin: ' + str(singleplugin), traceback.format_exc())
                    elif (result.isPlayer == 0) and (result.content.endswith('left the game')):
                        player = result.content.split(' ')[0]
                        for singleplugin in plugins.onPlayerLeavePlugins:
                            try:
                                t = threading.Thread(target=singleplugin.onPlayerLeave, args=(server, player))
                                t.setDaemon(True)
                                t.start()
                            except:
                                print('error processing plugin: ' + str(singleplugin), traceback.format_exc())
                    for singleplugin in plugins.plugins:
                        t = threading.Thread(target=self.callplugin, args=(result, singleplugin))
                        t.setDaemon(True)
                        t.start()
                time.sleep(1)
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
    print('Iniciando plugins...')
    try:
        import mcdplugin

        plugins = mcdplugin.mcdplugin()
        plugins_inf = listplugins(plugins)
        print(plugins_inf)

    except:
        print('error iniciando plugins :( .', traceback.format_exc())
        sys.exit(0)
    try:
        server = Server()
    except:
        print('fallo al inicial el server.', 1, traceback.format_exc())
        os._exit(0)

    for singleplugin in plugins.startupPlugins:
        try:
            t = threading.Thread(target=singleplugin.onServerStartup, args=(server,))
            t.setDaemon(True)
            t.start()
        except:
            print('error initalizing startup plugins,printing traceback.', traceback.format_exc())
    cmd = threading.Thread(target=getInput, args=(server,))

    cmd = threading.Thread(target=getInput, args=(server,))
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
