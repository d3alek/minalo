#!venv/bin/python3

import datetime
import time
import sh
import os
from помощни import време_клон, СЛУШАНЕ, сега, вземи_водачи, изчисли_водачи, вземи_съучастници, вземи_аз, CustomFormatter

import colorlog
import logging
log = colorlog.getLogger('минало')
log.setLevel(logging.DEBUG)

ch = colorlog.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(colorlog.ColoredFormatter(
	'%(log_color)s%(levelname)s:%(name)s:%(message)s'))

log.addHandler(ch)

os.environ['GNUPGHOME'] = os.getcwd() + '/тайник'
аз = вземи_аз()

# СЛУШАНЕ идва от помощни.py
СГЛОБЯВАНЕ = 35
ГЛАСУВАНЕ = 50
ПРИЕМАНЕ = 60

sh2 = sh(_err_to_out=True, _truncate_exc=False)
git = sh2.git

#def почисти():
#    git.checkout('main')
#    modified = []
#    untracked = []
#    for status_line in git.status('--porcelain').strip().split('\n'):
#        status, file_name = status_line.split()
#        if status == 'M':
#            modified.append(file_name)
#        elif status == '??':
#            untracked.append(file_name)
#
#    git.checkout('-b', 'modified-'+време_клон())
#    for m in modified:
#        git.add(m)
#
#    git.commit('--gpg-sign='+аз, '-m', 'Запазваме локално променените файлове' + време_клон())
#
#    git.checkout('main')
#    git.checkout('-b', 'untracked-'+време_клон())
#
#    for u in untracked:
#        git.add(u)
#
#
#    git.commit('--gpg-sign='+аз, '-m', 'Запазваме локално неследените файлове ' + време)
#
#    git.checkout('main')

def вземи_клони(шаблон='', local=True):
    клони = []

    try:
        if шаблон:
            show_ref = git('show-ref', шаблон)
        else:
            show_ref = git('show-ref')

        for клон in show_ref.strip().split('\n'):
            клон = клон.strip().split()[1]
            if (local and 'heads' in клон) or (not local and 'remotes' in клон):
                клони.append(клон)
        return клони
    except:
        return []

def изпращай_промени(водачи, клон_шаблон):
    log.info('Слушам и изпращам промени към водачите')

    for водач in водачи:
        log.debug(git.fetch(водач['номер'], 'main'))
        log.debug(git.checkout('-B', водач['номер']+'-main', '--track', водач['номер']+'/main'))
        съучастници = вземи_съучастници()
        намерих_себе_си = False
        for съучастник in съучастници:
            if съучастник['номер'] == аз:
                намерих_себе_си = True

        if not намерих_себе_си:
            log.info('Не намерих себе си в съучастниците на водач', водач)
            log.debug(git.checkout('-B', клон_шаблон+'-'+аз))
            with open('съучастници', 'a+') as f:
                водач_адрес = os.getcwd() + '/водач' #TODO направи ако не съществува чрез git clone .git водач --bare

                f.write('%s %s\n' % (аз, водач_адрес))
            log.debug(git.add('съучастници'))
            log.debug(git.commit('--gpg-sign='+аз, '-m', 'Добавям се към съучастници'))

            log.debug(git.push(водач['номер']))

        log.debug(git.checkout('main'))

    while сега().second < СЛУШАНЕ:
        for водач in водачи:
            log.debug(git.fetch(водач['номер']))
        клони = вземи_клони(клон_шаблон)

        for клон in клони:
            for водач in водачи:
                log.debug(git.push(водач['номер'], клон))

        time.sleep(1)

def сглоби_минута(кандидат_клон_шаблон, аз):
    log.info('Сглобявам минута')

    време = сега().isoformat(timespec='minutes')
    #TODO вярваме на pre-receive hook че всички получени от remote аз-а ще са валидни
    клони = list(filter(lambda к: аз in к, вземи_клони(local=False)))

    log.debug(git.checkout('-B', кандидат_клон_шаблон))

    for клон in клони:
        log.debug(git.merge(клон))

    with open('време', 'w') as f:
        f.write(време)

    with open('гласове', 'w') as f:
        f.write('')

    with open('водачи', 'w') as f:
        f.write('\n'.join(map(lambda d: "%s %s" % (d['номер'], d['адрес']), изчисли_водачи())))

    log.debug(git.add('време'))
    log.debug(git.add('гласове'))
    log.debug(git.add('водачи'))
    
    log.debug(git.commit('--gpg-sign='+аз, '-m', 'време ' + време))

    log.debug(git.push(аз))
    log.debug(git.checkout('main'))

    time.sleep(max(0, СГЛОБЯВАНЕ - сега().second))

def гласувай(водачи, кандидат_клон_шаблон, aз):
    log.info('Гласувам')

    best = None
    best_count = None

    for водач in водачи:
        log.debug(git.fetch(водач['номер']))

    клони = вземи_клони(шаблон=кандидат_клон_шаблон, local=False)

    for клон in клони:
        count = int(git('rev-list', '--count', клон))
        if not best or count > best_count:
            best = клон
            best_count = count

    if not best:
        raise RuntimeError('!!! Не намерих най-добър клон', клони)

    log.info('Гласувам за', best)
    remote = best.split('/')[2]
    гласувах = False
    log.debug(git.checkout('-B', кандидат_клон_шаблон+'+глас', '--track', best))
    while not гласувах:
        try:
            with open('гласове', 'a+') as f:
                f.write(аз+'\n')

            log.debug(git.add('гласове'))
            log.debug(git.commit('--gpg-sign='+аз, '-m', 'Глас от ' + аз))
            log.debug(git.push(remote, 'HEAD:'+кандидат_клон_шаблон))
            гласувах = True
        except sh.ErrorReturnCode_1 as e:
            log.error(e)
            log.debug(git.reset('--hard', 'HEAD~1'))
            log.debug(git.pull())

    time.sleep(max(0, ГЛАСУВАНЕ - сега().second))

def приеми_минута(водачи, кандидат_клон_шаблон):
    log.info('Приемам минута')

    best = None
    best_count = None

    for водач in водачи:
        log.debug(git.fetch(водач['номер']))

    клони = вземи_клони(кандидат_клон_шаблон, local=False)

    for клон in клони:
        count = int(git('rev-list', '--count', клон))
        if not best or count > best_count:
            best = клон
            best_count = count

    log.info('Приемам', best)
    log.debug(git.checkout('main'))
    log.debug(git.merge('--ff-only', best))

# План
## 1. Всички промени се пращат към водачите до 30тата секунда от минутата. Водачите имат отговорност да синхронизират промените по между си.
## 2. Водачите слобяват кандидат минута, която съдържа ново време и нови водачи.
## 3. Всички кандидатстват за най-добрата минута, която водачите са предложили. Тоест, пращат комит.
## 4. Когато има много неразбирателство, увеличи броя водачи като добавиш себе си към водачите
## 5. Всички приемат минутата на водача с най-много гласове. Тоест, комити.
def минута():
    stored_exception = None

    try:
        log.debug(git.pull(аз, 'main'))
        log.debug(git.push(аз, 'main'))
    except:
        pass

    while True:
        try:
            if сега().second > СЛУШАНЕ:
                време = сега() - datetime.timedelta(minutes=1)
            else:
                време = сега()

            клон_шаблон = време_клон(време=време)
            кандидат_клон_шаблон = време_клон(кандидат=True, време=време)

            водачи = вземи_водачи()
            съм_водач = False
            for водач in водачи:
                съм_водач = съм_водач or водач['номер'] == аз

            if съм_водач:
                log.info('Водач съм')
            else:
                log.info('Не съм водач')
            съучастници = вземи_съучастници()

            remotes = list(map(str.strip, git.remote().split('\n')))
            for съучастник in съучастници:
                if съучастник['номер'] not in remotes:
                    git.remote.add(съучастник['номер'], съучастник['адрес'])
                else:
                    #TODO update url
                    continue

            git.checkout('main')
            #if сега().second > СЛУШАНЕ:
            #    print(сега(), "Изчаквам новата минута")
            #    time.sleep(ПРИЕМАНЕ - сега().second - сега().microsecond/1000000) # TODO това работи добре
            #    continue

            изпращай_промени(водачи, клон_шаблон)

            if съм_водач:
                сглоби_минута(кандидат_клон_шаблон, аз)
            else:
                time.sleep(max(0, СГЛОБЯВАНЕ - сега().second))

            гласувай(водачи, кандидат_клон_шаблон, аз)

            приеми_минута(водачи, кандидат_клон_шаблон)


            log.info('Изтривам излишни клони')
            if съм_водач:
                клони = вземи_клони(local=False)
                git.push(аз,'main')
                for клон in клони:
                    if аз in клон and клон != 'refs/remotes/%s/main' % аз:

                        клон = клон.split('refs/remotes/%s/' % аз)[1]
                        log.debug(git.push(аз, '--delete', клон))

            клони = вземи_клони(local=True)
            for клон in клони:
                if клон != 'refs/heads/main':
                    клон = клон.split('refs/heads/')[1]
                    log.debug(git.branch('-D', клон))

            if stored_exception:
                break

            time.sleep(max(0, ПРИЕМАНЕ - сега().second))
        except KeyboardInterrupt:
            if stored_exception:
                raise 
            import sys
            stored_exception = sys.exc_info()
            log.warn('Ще изляза в края на тази минута. Прекъсни отново за да изляза веднага')


# Промени в кода се приемат само с няколко (3) подписа на разработчици (такива които са правили вече промени по кода).

if __name__ == '__main__':
    минута()
