def onPlayerJoin(server, player):
    msg = 'Bienvenido ' + player + '!'
    server.tell(player, msg)
