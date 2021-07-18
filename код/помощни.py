# Ако имаме 33ма съучастници, на базата на коя минута от деня е, делим на броя на участниците и взимаме остатъка от деленето - този и следващите двама участника са водачи. На тях може да се пращат новите комити.

import datetime
import sh
from sh import gpg2

import os

from enum import Enum
class State(Enum):
    Начало = 0
    Слушане = 25
    Сглобяване = 30
    Гласуване = 43
    Приемане = 55
    Почистване = 60

sh2 = sh(_err_to_out=True)
git = sh2.git

def сега():
  return datetime.datetime.utcnow()

def минута_от_деня():
  return сега().minute + сега().hour*60

полета = ['id', 'remote']

def get_fellows():
  with open('съучастници') as f:
      return list(map(lambda s: dict(zip(полета, s.strip().split(' '))), f.readlines()))

def вземи_гласували():
  with open('гласове') as f:
      return list(map(lambda s: s.strip(), f.readlines()))

def calculate_minute_branch(t=None):
  if t == None:
    t = сега()
  if t.second > State.Слушане.value:
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
