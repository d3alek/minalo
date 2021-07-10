# Ако имаме 33ма съучастници, на базата на коя минута от деня е, делим на броя на участниците и взимаме остатъка от деленето - този и следващите двама участника са водачи. На тях може да се пращат новите комити.

import datetime
import sh
from sh import gpg2, head, grep

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
    return head(grep(gpg2('--with-colons', '-K'), 'fpr'), '-n1').split(':')[9]

import logging

class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    grey = "\x1b[38;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
