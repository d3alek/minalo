# Ако имаме 33ма съучастници, на базата на коя минута от деня е, делим на броя на участниците и взимаме остатъка от деленето - този и следващите двама участника са водачи. На тях може да се пращат новите комити.

import datetime
import sh
from sh import gpg2

СЛУШАНЕ = 30

sh2 = sh(_err_to_out=True)
git = sh2.git

def сега():
  return datetime.datetime.utcnow()

def минута_от_деня():
  return сега().minute + сега().hour*60

полета = ['номер', 'адрес']

def вземи_водачи():
  with open('водачи') as f:
    return list(map(lambda s: dict(zip(полета, s.strip().split(' '))), f.readlines()))

def вземи_съучастници():
  with open('съучастници') as f:
    return list(map(lambda s: dict(zip(полета, s.strip().split(' '))), f.readlines()))

def изчисли_водачи():
  съучастници = вземи_съучастници()
  брой = len(съучастници)
  номер = минута_от_деня() % брой
  return [съучастници[номер]]

def време_клон(кандидат=False, време=None):
  if време == None:
    време = сега()
  if време.second > СЛУШАНЕ:
    време = време + datetime.timedelta(minutes=1)   
  време = време.isoformat(timespec='minutes').replace(':','-') # защото Git клоните не могат да съдържат :
  if кандидат:
    време += '-кандидат'
  #if ключ:
  #  време += '-' + ключ
  return време

def вземи_аз():
    keys = gpg2('--with-colons', '-K')
    for line in keys:
        if 'fpr' in line:
            return line.split(':')[9]

if __name__ == '__main__':
    print(вземи_аз())
