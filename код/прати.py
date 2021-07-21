import argparse
import sys
import sh
from sh import rm
import os
import yaml
from помощни import calculate_minute_branch, get_fellows, сега, вземи_аз, git, сега, get_head

import datetime

import colorlog
import logging
log = colorlog.getLogger('прати')
log.setLevel(logging.DEBUG)

ch = colorlog.StreamHandler()
ch.setLevel(logging.DEBUG)
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

    log.info('Аз ' + аз)
    log.debug(git.checkout('main'))
    fellow = None
    for f in get_fellows():
        rm('-rf', 'clone')
        try:
            #TODO instead of clone, inspect file
            log.debug(git.clone(f['remote'], 'clone'))
            os.chdir('clone')
            with open('време', 'r') as fi:
                t = datetime.datetime.fromisoformat(fi.read())

            expected = сега() - datetime.timedelta(minutes=1)
            expected = expected.replace(second = 0, microsecond=0)
            if t != expected:
                log.error('Съучастник %s има грешно време %s, очавано %s' % (f['id'], t, expected))
                continue
            else:
                log.info('Използвам %s' % (f['id'],))
                fellow = f
        except Exception as e:
            log.warning('Не успях да се свържа със %s' % (f['id'],))
            log.error(e)


    if fellow == None:
        return

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
        клон = calculate_minute_branch(ключ=аз, време=сега() - datetime.timedelta(minutes=1))
    elif атака == "грешен клон main":
        клон = 'main'
    else:
        клон = calculate_minute_branch()

    start_id = get_head()

    log.debug(git.checkout('-B', клон))
    log.debug(git.add(файл_пращач, файл_получател))
    log.debug(git.commit('--gpg-sign='+аз, '-m', '%s праща %s на %s' % (пращач, количество, получател)))

    commit_id = get_head()

    try:
        log.debug(git.push(fellow['remote']))
        if атака:
            log.info('ЛОШ УСПЯ: Атака %s успя' % атака)

        max_sleep_until = сега() + datetime.timedelta(minutes=2)
        while сега() < max_sleep_until:
            git.fetch(fellow['remote'], main)
            rev_list = git('rev-list', '^'+start_id)
            if commit_id in rev_list:
                log.info("Изпращането потвърдено!")
                break

            log.info('Чакам потвърждение - ' + len(rev_list) + ' нови промени откакто изпратихме')


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
