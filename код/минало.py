#!../venv/bin/python3

import datetime
import time
import sh
import os
from помощни import calculate_minute_branch, СЛУШАНЕ, сега, вземи_водачи, изчисли_водачи, вземи_съучастници, вземи_аз

аз = вземи_аз()
водач_папка = os.getcwd() + '/водач'

import colorlog
import logging
import paramiko
import network

log = colorlog.getLogger('минало')
nlog = colorlog.getLogger('мрежа')
glog = colorlog.getLogger('git')
log.setLevel(logging.DEBUG)
nlog.setLevel(logging.INFO)
glog.setLevel(logging.INFO)

ch = colorlog.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(levelname)s:%(name)s:'+аз[:4]+':%(message)s'))

log.addHandler(ch)
nlog.addHandler(ch)
glog.addHandler(ch)

# СЛУШАНЕ идва от помощни.py
СГЛОБЯВАНЕ = 45
ГЛАСУВАНЕ = 50
ПРИЕМАНЕ = 60

sh2 = sh(_err_to_out=True, _truncate_exc=False)
git = sh2.git

def приготви():
    glog.debug(git.checkout('main'))
    modified = []
    untracked = []
    status = git.status('--porcelain')
    if not status:
        return
    glog.info(status)
    for status_line in status.strip().split('\n'):
        status, file_name = status_line.split()
        if status == 'M':
            modified.append(file_name)
        elif status == '??':
            untracked.append(file_name)

    for m in modified:
        glog.debug(git.add(m))

    glog.info(git.commit('--gpg-sign='+аз, '-m', 'Автоматично запазвам локално променени %s' % modified))
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

def rush(*args):
    try:
        pull = git.pull(*args, '--rebase')
        glog.info(pull)
    except Exception as e:
        glog.info('Failed to pull --rebase as part of rebase-and-push')
        glog.info(e)
    while True:
        try:
            return git.push(*args)
        except Exception as e:
            try:
                pull = git.pull(*args, '--rebase')
                glog.info(pull)
            except Exception as e:
                glog.error(e)


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

def изпращай_промени(водачи, minute_branch, username, host, port):
    log.info('Слушам и изпращам промени към водачите')
    try:
        glog.debug(git.branch(minute_branch))
    except:
        pass
    glog.debug(git.checkout(minute_branch))
    glog.debug(rush(аз, minute_branch))

    намерих_себе_си = False
    with open(os.environ['HOME'] + '/.ssh/id_rsa.pub') as f:
        my_key = f.read()
    with open('authorized_keys') as f:
        for line in f:
            if line == my_key:
                намерих_себе_си = True
    if not намерих_себе_си:
        log.info('Не намерих себе си в authorized_keys')
        with open('authorized_keys', 'a+') as f:
            f.write(my_key)
        glog.debug(git.add('authorized_keys'))
        glog.debug(git.commit('--gpg-sign='+аз, '-m', 'Добавям се към authorized_keys'))
        # Това обновява minute_branch от нашия водач, като обновява и него. По него ние получаваме съобщения от другите, затова е хубаво да се обновяваме. После обновения клон пращаме на сегашния водач
        glog.debug(rush(аз, minute_branch))
        glog.debug(rush(водач, minute_branch))

    водач_адрес = 'ssh://%s@%s:%s%s' % (username, host, port, водач_папка)

    remove = []
    for водач in водачи:
        try:
            glog.debug(git.fetch(водач, 'main'))
        except Exception as e:
            log.error(e)
            log.error('Не успях да се свържа с водач ' + водач)
            remove.append(водач)
            continue

        glog.debug(git.checkout('-B', водач+'-main', '--track', водач+'/main'))
        съучастници = вземи_съучастници()
        намерих_себе_си = False
        намерих_себе_си_грешен_адрес = None
        for index, съучастник in enumerate(съучастници):
            if съучастник['id'] == аз:
                if съучастник['remote'] == водач_адрес:
                    намерих_себе_си = True
                else:
                    намерих_себе_си_грешен_адрес = index

        if намерих_себе_си_грешен_адрес or not намерих_себе_си:
            if намерих_себе_си_грешен_адрес:
                log.info('Намерих грешен адрес за себе си в съучастниците на водач %s' % водач)
                съучастници.pop(намерих_себе_си_грешен_адрес)
            else:
                log.info('Не намерих себе си в съучастниците на водач %s' % водач)
                        
            glog.debug(git.checkout(minute_branch))
            съучастници.append({'id': аз, 'remote': водач_адрес})
            with open('съучастници', 'w') as f:
                for с in съучастници:
                    f.write('%s %s\n' % (с['id'], с['remote']))
            glog.debug(git.add('съучастници'))
            if намерих_себе_си_грешен_адрес:
                glog.debug(git.commit('--gpg-sign='+аз, '-m', 'Обновявам адреса си в съучастници'))
            else:
                glog.debug(git.commit('--gpg-sign='+аз, '-m', 'Добавям се към съучастници'))

            try:
                glog.debug(rush(аз, minute_branch))
                glog.debug(rush(водач, minute_branch))
            except sh.ErrorReturnCode_1 as e:
                glog.exception(e)

        glog.debug(git.checkout('main'))

    if remove:
        for r in remove:
            водачи.remove(r)

    # TODO още сега можем да видим че няма останали водачи и да поемем кормилото

    git.checkout(minute_branch)
    while сега().second < СЛУШАНЕ:
        for водач in водачи:
            try:
                fetch = git.fetch(водач, minute_branch)
                if len(fetch.strip()) > 0:
                    log.info("Промяна")
                    log.info(fetch)
                    промяна = True
                else:
                    промяна = False
            except:
                log.error('Не успях да се свържа с водач ' + водач)

        for водач in водачи:
            glog.debug(rush(аз, minute_branch))
            glog.debug(rush(водач, minute_branch))

        time.sleep(1)

def сглоби_минута(minute_branch, аз):
    log.info('Сглобявам минута')

    време = сега().isoformat(timespec='minutes')
    #TODO вярваме на pre-receive hook че всички получени от remote аз-а ще са валидни
    клони = вземи_клони(local=False)

    glog.debug(git.checkout(minute_branch))
    glog.debug(git.pull(аз, minute_branch))

    with open('време', 'w') as f:
        f.write(време)

    with open('водачи', 'w') as f:
        f.write('\n'.join(map(lambda d: "%s" % d, изчисли_водачи()))) # това трябва да стане преди да нулираме гласове по-долу

    with open('гласове', 'w') as f:
        f.write('')

    glog.debug(git.add('време'))
    glog.debug(git.add('гласове'))
    glog.debug(git.add('водачи'))
    
    glog.debug(git.commit('--gpg-sign='+аз, '-m', 'време ' + време))

    glog.debug(git.push(аз, minute_branch))

def гласувай(водачи, minute_branch, aз):
    log.info('Гласувам')

    for fellow in вземи_съучастници():
        try:
            glog.debug(git.fetch(fellow['id'], minute_branch))
        except:
            log.error('Не успях да изтелгя последните промени от ' + fellow['id']) 


    клони = вземи_клони(шаблон=minute_branch, local=False)
#    if not клони:
#        log.error('Водачите не са си свършили работата. Поемам ролята на водач')
#        сглоби_минута(minute_branch, аз) # TODO това вече не следва да се случва:
#        for fellow in вземи_съучастници():
#            try:
#                glog.debug(git.fetch(fellow['id'], minute_branch))
#                водачи.append(fellow['id']) #TODO ако са много участници това може да избухне
#            except Exception:
#                log.error('Не успях да изтелгя последните промени от ' + fellow['id']) 


    клони = вземи_клони(шаблон=minute_branch, local=False)
        # Вече със сигурност имаме поне 1 кандидат минута - тази който ние сме направили

    best = None
    best_count = None
    for клон in клони:
        count = int(git('rev-list', '--count', клон))
        if not best or count > best_count:
            best = клон
            best_count = count

    log.info('Гласувам за ' + best)
    remote = best.split('/')[2]
    гласувах = False
    glog.debug(git.checkout(minute_branch))
    glog.debug(git.pull(remote, minute_branch))

    while not гласувах:
        try:
            with open('гласове', 'a+') as f:
                f.write(аз+'\n')

            glog.debug(git.add('гласове'))
            glog.debug(git.commit('--gpg-sign='+аз, '-m', 'Глас от ' + аз))
            glog.debug(git.push(remote, minute_branch))
            гласувах = True
        except sh.ErrorReturnCode_1 as e:
            glog.debug(e)
            glog.debug(git.reset('--hard', 'HEAD~1'))
            glog.debug(git.pull(remote, minute_branch))

    time.sleep(max(0, ГЛАСУВАНЕ - сега().second))

def приеми_минута(водачи, minute_branch):
    log.info('Приемам минута')

    best = None
    best_count = None

    for водач in водачи:
        try:
            glog.debug(git.fetch(водач, minute_branch))
        except Exception as e:
            log.error(e)
            log.error('Не успях да се свържа с водач ' + водач)

    клони = вземи_клони(шаблон=minute_branch, local=False)

    for клон in клони:
        count = int(git('rev-list', '--count', клон))
        if not best or count > best_count:
            best = клон
            best_count = count

    log.info('Приемам ' + best)
    glog.debug(git.checkout('main'))
    glog.debug(git.reset(best, '--hard'))
    git.push(аз, 'main', '--force')

def am_leader(leaders):
    leader = False
    for l in leaders:
        leader = leader or l == аз

    return leader
# План
## 0. Теглим main от някой от съучастниците които са на линия.
## 1. Всички промени се пращат към водачите до 30тата секунда от минутата във един и същ клон (зависещ от минутата). Този който е пратил промени следва да ги наблюдава - комита ако влезе в main, всичко точно, ако не, следва да се повтори следващата минута ( Водачите имат отговорност да синхронизират промените по между си.)
## 2. Водачите слобяват кандидат минута, която съдържа ново време и нови водачи.
## 3. Всички кандидатстват за най-добрата минута, която водачите са предложили. Тоест, пращат комит.
## 3.1 Когато има много неразбирателство, увеличи броя водачи като добавиш себе си към водачите
## 3.2 Когато няма кандидат минута, всеки поема водачеството и прави такава.
## 4. Всички приемат минутата на водача с най-много гласове. Тоест, комити.
def минута(username, host, port):
    приготви()
    stored_exception = None

    log.info('Взимаме от origin')
    glog.debug(git.checkout('main'))
    glog.debug(git.pull('--ff-only', 'origin'))

    if not os.path.exists(водач_папка):
        log.info('Правя гол водач с който ще общуват съучастниците')
        glog.debug(git.clone('.git', водач_папка, '--bare'))

    #TODO отдели
    fellows = вземи_съучастници()
    remotes = list(map(str.strip, git.remote().split('\n')))
    for fellow in fellows:
        remote = fellow['remote']
        if fellow['id'] == аз:
            remote = водач_папка
        if fellow['id'] not in remotes:
            git.remote.add(fellow['id'], remote)
        else:
            git.remote('set-url', fellow['id'], remote)
        try:
            pull = git.pull('--ff-only', fellow['id'], 'main')
            glog.debug(pull)
            if 'Already up to date' not in pull:
                log.info('Изтеглих най-новото състояние от ' + fellow['id'])
            else:
                log.info('Не взимам нищо ново от ' + fellow['id'])
        except Exception as e:
            log.debug('Не успях да се свържа с ' + fellow['id'])
            continue

    glog.debug(git.push(аз, 'main', '--force'))

    while True:
        try:
            # Това е нужно защото може да сме влезли в цикъла след СЛУШАНЕ, тук имаме два варианта: 1/ да се преструваме че сме влезли по-рано, което правим по-долу, или 2/ да се включим само за частта, до която се е стигнало. TODO опитай вариант 2
            if сега().second > СЛУШАНЕ:
                t = сега() - datetime.timedelta(minutes=1)
            else:
                t = сега()

            minute_branch = calculate_minute_branch(t)

            водачи = вземи_водачи()

            if am_leader(водачи):
                log.info('Водач съм')
            else:
                log.info('Не съм водач. Водачи: %s' % водачи)

            git.checkout('main')

            изпращай_промени(водачи, minute_branch, username, host, port)

            # какви са последиците че всички правят това?
            сглоби_минута(minute_branch, аз)
            time.sleep(max(0, СГЛОБЯВАНЕ - сега().second))

            гласувай(водачи, minute_branch, аз)

            приеми_минута(водачи, minute_branch)

            if stored_exception:
                break

            time.sleep(max(0, ПРИЕМАНЕ - сега().second))
            log.info('Изтривам излишни клони')
            if am_leader(водачи):
                клони = вземи_клони(local=False)
                for клон in клони:
                    шаблон = 'refs/remotes/%s/' % аз
                    if шаблон in клон and клон != 'refs/remotes/%s/main' % аз:

                        log.debug(клон)
                        клон = клон.split(шаблон)[1]
                        glog.debug(git.push(аз, '--delete', клон))

            клони = вземи_клони(local=True)
            for клон in клони:
                if клон != 'refs/heads/main':
                    клон = клон.split('refs/heads/')[1]
                    glog.debug(git.branch('-D', клон))
        except KeyboardInterrupt:
            if stored_exception:
                raise 
            import sys
            stored_exception = sys.exc_info()
            log.warning('Ще изляза в края на тази минута. Прекъсни отново за да изляза веднага')


# Промени в кода се приемат само с няколко (3) подписа на разработчици (такива които са правили вече промени по кода).

if __name__ == '__main__':
    import argparse
    import getpass
    parser = argparse.ArgumentParser()
    parser.add_argument('--ssh-user', default=getpass.getuser())
    parser.add_argument('--ssh-host')
    parser.add_argument('--ssh-port', type=int, default=22)

    args = parser.parse_args()

    #TODO премести в network.py
    relay_ports_range = [10000, 11000]
 
    if not args.ssh_host:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())

        relays = []
        remote_port = None
        for съучастник in вземи_съучастници():
            nlog.debug('Пробвам %s за реле' % съучастник)
            username, server, port = network.раздели_адрес(съучастник['remote'])

            if съучастник['id'] == аз:
                remote_port = port
            if port >= relay_ports_range[0] and port <= relay_ports_range[1]:
                nlog.debug('Не става за реле - вече е зад тунел')
            else:
                relays.append((username, server, port))

        if not relays:
            raise RuntimeError("Нямам реално IP, но нямам и реле")

        username, server, port = relays[0] #TODO random or iterate over all

        nlog.debug("Connecting to ssh host %s@%s:%d ..." % (username, server, port))
        try:
            client.connect(
                server,
                port,
                username=username,
                #key_filename=options.keyfile,
                #look_for_keys=options.look_for_keys,
                #password=password,
            )
        except Exception as e:
            nlog.error(e)
            import sys
            sys.exit(1)


        if not remote_port:
            import random 
            remote_port = random.randint(*relay_ports_range)

        nlog.info(
            "Now forwarding remote port %d to %s:%d ..."
            % (remote_port, 'localhost', args.ssh_port)
        )

        network.reverse_forward_tunnel(
            remote_port, 'localhost', args.ssh_port, client.get_transport())
        ssh_host = server
        ssh_port = remote_port
    else:
        ssh_host = args.ssh_host
        ssh_port = args.ssh_port

    минута(args.ssh_user, ssh_host, ssh_port)
