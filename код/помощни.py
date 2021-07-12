# Ако имаме 33ма съучастници, на базата на коя минута от деня е, делим на броя на участниците и взимаме остатъка от деленето - този и следващите двама участника са водачи. На тях може да се пращат новите комити.

import datetime
import sh
from sh import gpg2

import os

СЛУШАНЕ = 30

sh2 = sh(_err_to_out=True)
git = sh2.git

def сега():
  return datetime.datetime.utcnow()

def минута_от_деня():
  return сега().minute + сега().hour*60

полета = ['id', 'remote']

def вземи_водачи():
  with open('водачи') as f:
    return list(map(lambda s: s.strip(), f.readlines()))

def вземи_съучастници():
  with open('съучастници') as f:
      return list(map(lambda s: dict(zip(полета, s.strip().split(' '))), f.readlines()))

def вземи_гласували():
  with open('гласове') as f:
      return list(map(lambda s: s.strip(), f.readlines()))

def изчисли_водачи():
  гласували = вземи_гласували()
  брой = len(гласували)
  if брой == 0:
      return []
  номер = минута_от_деня() % брой
  return [гласували[номер]]

def calculate_minute_branch(t=None):
  if t == None:
    t = сега()
  if t.second > СЛУШАНЕ:
    t = t + datetime.timedelta(minutes=1)   
  t = t.isoformat(timespec='minutes').replace(':','-') # защото Git клоните не могат да съдържат :
  return t

def вземи_аз():
    os.environ['GNUPGHOME'] = os.getcwd() + '/тайник'
    keys = gpg2('--with-colons', '-K')
    for line in keys:
        if 'fpr' in line:
            return line.split(':')[9]

if __name__ == '__main__':
    print(вземи_аз())
