# -*- coding: utf-8 -*-

import re
import time

def onServerInfo(server, info):
    dimension_convert = {"0":"overworld ","-1":"nether ","1":"end "}

    if info.content.startswith('!!here'):
        server.execute('data get entity ' + info.player)
    
    elif 'following entity data' in info.content:
        name = info.content.split(" ")[0]
        dimension = re.search("(?<=Dimension: )-?\d",info.content).group()

        position_str = re.search("(?<=Pos: )\[.*?\]",info.content).group()
        position = re.findall("\[(-?\d*).*?, (-?\d*).*?, (-?\d*).*?\]",position_str)[0]
        position_show = "[x:"+str(position[0])+",y:"+str(position[1])+",z:"+str(position[2])+"]"

        if dimension == '0':
            server.say("§e" + name + "§r §2" + dimension_convert[dimension] + position_show)
        elif dimension == '1':
            server.say("§e" + name + "§r §5" + dimension_convert[dimension] + position_show)
        elif dimension == '-1':
            server.say("§e" + name + "§r §4" + dimension_convert[dimension] + position_show)
        
        server.execute("effect give " + name + " minecraft:glowing 15 1 true")
