import traceback
PREFIX='[MCDaemon]:'

def log(data):
  print(PREFIX + data)

def errlog(data,traceback=''):
  print(PREFIX + data + traceback)

def exitlog(data, crit=0, traceback=''):
  if crit == 0:
    print(PREFIX + data)
    print(PREFIX + 'Saliendo...')
  if crit == 1:
    print(PREFIX + 'Error critico')
    print(PREFIX + 'Razon:' + data)
    if traceback != '':
      print(traceback)
    print(PREFIX + 'Saliendo...')

  
