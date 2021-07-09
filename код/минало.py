#!venv/bin/python3

import datetime
import time
import sh
import os
from помощни import време_клон, СЛУШАНЕ, сега, вземи_водачи, изчисли_водачи, вземи_съучастници, вземи_аз

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
    print(сега(), 'Слушам и изпращам промени към водачите')

    while сега().second < СЛУШАНЕ:
        for водач in водачи:
            print(git.fetch(водач['номер']))
        клони = вземи_клони(клон_шаблон)

        for клон in клони:
            for водач in водачи:
                print(git.push(водач['номер'], клон))

        time.sleep(1)

def сглоби_минута(клон_шаблон, кандидат_клон_шаблон, аз):
    print(сега(), 'Сглобявам минута')

    време = сега().isoformat(timespec='minutes')
    клони = вземи_клони(клон_шаблон)

    print(git.checkout('-B', кандидат_клон_шаблон))

    for клон in клони:
        print(git.merge(клон))

    with open('време', 'w') as f:
        f.write(време)

    with open('гласове', 'w') as f:
        f.write('')

    git.add('време')
    git.add('гласове')
    #TODO предложи следващи водачи
    git.commit('--gpg-sign='+аз, '-m', 'време ' + време)

    print(git.push(аз))
    print(git.checkout('main'))

    time.sleep(max(0, СГЛОБЯВАНЕ - сега().second))

def гласувай(водачи, кандидат_клон_шаблон, aз):
    print(сега(), 'Гласувам')

    best = None
    best_count = None

    for водач in водачи:
        print(git.fetch(водач['номер']))

    клони = вземи_клони(шаблон=кандидат_клон_шаблон, local=False)

    for клон in клони:
        count = int(git('rev-list', '--count', клон))
        if not best or count > best_count:
            best = клон
            best_count = count

    if not best:
        raise RuntimeError('!!! Не намерих най-добър клон', клони)

    print(сега(), 'Гласувам за', best)
    remote = best.split('/')[2]
    print(git.checkout('-B', кандидат_клон_шаблон+'+глас', '--track', best))

    with open('гласове', 'a+') as f:
        f.write(аз+'\n')

    print(git.add('гласове'))
    print(git.commit('--gpg-sign='+аз, '-m', 'Глас от ' + аз))
    print(git.push(remote, 'HEAD:'+кандидат_клон_шаблон))

    time.sleep(max(0, ГЛАСУВАНЕ - сега().second))

def приеми_минута(водачи, кандидат_клон_шаблон):
    print(сега(), 'Приемам минута')

    best = None
    best_count = None

    for водач in водачи:
        print(git.fetch(водач['номер']))

    клони = вземи_клони(кандидат_клон_шаблон, local=False)

    for клон in клони:
        count = int(git('rev-list', '--count', клон))
        if not best or count > best_count:
            best = клон
            best_count = count

    print(сега(), 'Приемам', best)
    print(git.checkout('main'))
    print(git.merge('--ff-only', best))

# План
## 1. Всички промени се пращат към водачите до 30тата секунда от минутата. Водачите имат отговорност да синхронизират промените по между си.
## 2. Водачите слобяват кандидат минута, която съдържа ново време и нови водачи.
## 3. Всички кандидатстват за най-добрата минута, която водачите са предложили. Тоест, пращат комит.
## 4. Когато има много неразбирателство, увеличи броя водачи като добавиш себе си към водачите
## 5. Всички приемат минутата на водача с най-много гласове. Тоест, комити.
def минута():
    while True:
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
            print('Водач съм')
        else:
            print('Не съм водач')
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
            сглоби_минута(клон_шаблон, кандидат_клон_шаблон, аз)
        else:
            time.sleep(max(0, СГЛОБЯВАНЕ - сега().second))

        гласувай(водачи, кандидат_клон_шаблон, аз)

        приеми_минута(водачи, кандидат_клон_шаблон)


        print('Изтривам излишни клони')
        if съм_водач:
            клони = вземи_клони(local=False)
            print(клони)
            git.push(аз,'main')
            for клон in клони:
                if аз in клон and клон != 'refs/remotes/%s/main' % аз:

                    клон = клон.split('refs/remotes/%s/' % аз)[1]
                    print(git.push(аз, '--delete', клон))

        клони = вземи_клони(local=True)
        for клон in клони:
            if клон != 'refs/heads/main':
                клон = клон.split('refs/heads/')[1]
                print(git.branch('-D', клон))

        time.sleep(max(0, ПРИЕМАНЕ - сега().second))

# Промени в кода се приемат само с няколко (3) подписа на разработчици (такива които са правили вече промени по кода).

if __name__ == '__main__':
    минута()
