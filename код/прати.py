import argparse
import sys
import sh
from sh import rm
import os
import yaml
from помощни import calculate_minute_branch, сега, вземи_аз, git

import colorlog
log = colorlog.getLogger('прати')
log.setLevel(colorlog.DEBUG)

ch = colorlog.StreamHandler()
ch.setLevel(colorlog.DEBUG)
ch.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s:%(levelname)s:%(name)s:%(message)s',
    '%H:%M:%S'))

log.addHandler(ch)

АТАКИ = [
    'праща чужди пари',
    'получава чужди пари',
    'различни праща получава',
    'грешен клон main',
    'грешен клон време',
]

def прати(пращач, получател, количество, атака):
    папка = os.getcwd()
    os.environ['GNUPGHOME'] = папка + '/тайник'
    аз = вземи_аз()

    log.info('Аз', аз)
    log.debug(git.checkout('main'))
    
    fellow = get_fellows()

    rm('-rf', 'clone')

    log.debug(git.clone(fellow[0], 'clone'))
    os.chdir('clone')


    if атака == 'праща чужди пари':
        файл_пращач = 'пари/участници/%s' % 'лошия' 
    else:
        файл_пращач = 'пари/участници/%s' % пращач
    with open(файл_пращач, 'w+') as f:
        пари = yaml.safe_load(f)
        if not пари:
            пари = {'пари': 0}
        пари['пари'] = пари['пари'] - количество
        yaml.dump(пари, f, allow_unicode=True)
        log.info(пращач, пари)

    if атака == 'получава чужди пари':
        файл_получател = 'пари/участници/%s' % 'лошия' 
    else: 
        файл_получател = 'пари/участници/%s' % получател
    with open(файл_получател, 'a+') as f:
        пари = yaml.safe_load(f)
        if not пари:
            пари = {'пари': 0}
        пари['пари'] = пари['пари'] + количество
        yaml.dump(пари, f, allow_unicode=True)
        log.info(получател, пари)

    if атака == "грешен клон време":
        import datetime
        клон = calculate_minute_branch(ключ=аз, време=сега() - datetime.timedelta(minutes=1))
    elif атака == "грешен клон main":
        клон = 'main'
    else:
        клон = calculate_minute_branch(аз)
    log.debug(git.checkout('-B', клон))
    log.debug(git.add(файл_пращач, файл_получател))
    log.debug(git.commit('--gpg-sign='+аз, '-m', '%s праща %s на %s' % (пращач, количество, получател)))


    try:
        log.debug(git.push(fellow[0]))
        if атака:
            log.info('ЛОШ УСПЯ: Атака %s успя' % атака)


    except sh.ErrorReturnCode_1 as e:
        log.error(str(e.stdout,'utf-8'))
        if атака:
            log.info('ЛОШ НЕ УСПЯ: Атака %s не успя' % атака)
        raise e

    finally:
        os.chdir(папка)

def откажи():
    аз = вземи_аз()
    клон = calculate_minute_branch(аз)
    fellows = get_fellows()

    for fellow in fellows:
        try:
            log.debug(git.push(fellow, '--delete', клон))
            print('Успешно отказано пратено към', fellow)
        except:
            print('Не успях да откажа пратено към', fellow)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('пращач')
    parser.add_argument('получател')
    parser.add_argument('количество', type=float)
    parser.add_argument('--атака', choices=АТАКИ)
    parser.add_argument('--откажи', action='store_true')

    args = parser.parse_args()

    if args.откажи:
        откажи()
        sys.exit(0) 
    пращач, получател, количество = args.пращач, args.получател, args.количество

    атака = args.атака
    if атака:
        print("ЛОШ")

    прати(пращач, получател, количество, атака)
