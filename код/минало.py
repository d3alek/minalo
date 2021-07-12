#!../venv/bin/python3

import datetime
import time
import sh
import os
from помощни import време_клон, СЛУШАНЕ, сега, вземи_водачи, изчисли_водачи, вземи_съучастници, вземи_аз

аз = вземи_аз()

import colorlog
import logging
import threading
import paramiko

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

def изпращай_промени(водачи, клон_шаблон, username, host, port):
    log.info('Слушам и изпращам промени към водачите')

    намерих_себе_си = False
    with open(os.environ['HOME'] + '/.ssh/id_rsa.pub') as f:
        my_key = f.read()
    with open('authorized_keys') as f:
        for line in f:
            if line == my_key:
                намерих_себе_си = True
    if not намерих_себе_си:
        log.info('Не намерих себе си в authorized_keys')

        glog.debug(git.checkout('-B', клон_шаблон+'-'+аз))

        with open('authorized_keys', 'a+') as f:
            f.write(my_key)
        glog.debug(git.add('authorized_keys'))
        glog.debug(git.commit('--gpg-sign='+аз, '-m', 'Добавям се към authorized_keys'))

    водач_папка = os.getcwd() + '/водач' #TODO направи ако не съществува чрез git clone .git водач --bare
    if not os.path.exists(водач_папка):
        log.info('Правя гол водач с който ще общуват съучастниците')
        glog.debug(git.clone('.git', водач_папка, '--bare'))
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
        if not намерих_себе_си:
            glog.debug(git.push(водач['номер']))
        else:
            glog.debug(git.checkout('-B', водач+'-main', '--track', водач+'/main'))
            съучастници = вземи_съучастници()
            намерих_себе_си = False
            намерих_себе_си_грешен_адрес = None
            for index, съучастник in enumerate(съучастници):
                if съучастник['номер'] == аз:
                    if съучастник['адрес'] == водач_адрес:
                        намерих_себе_си = True
                    else:
                        намерих_себе_си_грешен_адрес = index

            if намерих_себе_си_грешен_адрес or not намерих_себе_си:
                if намерих_себе_си_грешен_адрес:
                    log.info('Намерих грешен адрес за себе си в съучастниците на водач %s' % водач)
                    съучастници.pop(намерих_себе_си_грешен_адрес)
                else:
                    log.info('Не намерих себе си в съучастниците на водач %s' % водач)
                            
                glog.debug(git.checkout('-B', клон_шаблон+'-'+аз))
                съучастници.append({'номер': аз, 'адрес': водач_адрес})
                with open('съучастници', 'w') as f:
                    for с in съучастници:
                        f.write('%s %s\n' % (с['номер'], с['адрес']))
                glog.debug(git.add('съучастници'))
                if намерих_себе_си_грешен_адрес:
                    glog.debug(git.commit('--gpg-sign='+аз, '-m', 'Обновявам адреса си в съучастници'))
                else:
                    glog.debug(git.commit('--gpg-sign='+аз, '-m', 'Добавям се към съучастници'))

                try:
                    glog.debug(git.push(водач))
                except sh.ErrorReturnCode_1 as e:
                    log.exception(e)

        glog.debug(git.checkout('main'))

    if remove:
        for r in remove:
            водачи.remove(r)

    # TODO още сега можем да видим че няма останали водачи и да поемем кормилото

    while сега().second < СЛУШАНЕ:
        for водач in водачи:
            fetch = git.fetch(водач)
            if len(fetch.strip()) > 0:
                log.info("Промяна")
                log.info(fetch)
        клони = вземи_клони(клон_шаблон)

        for клон in клони:
            for водач in водачи:
                glog.debug(git.push(водач, клон))

        time.sleep(1)

def сглоби_минута(клон_шаблон, кандидат_клон_шаблон, аз):
    log.info('Сглобявам минута')

    време = сега().isoformat(timespec='minutes')
    #TODO вярваме на pre-receive hook че всички получени от remote аз-а ще са валидни
    клони = вземи_клони(local=False)
    # Тук нарочно взимаме само клоните, получени от нас - само на тях можем да вярваме
    клони = list(filter(lambda к: 'refs/remotes/%s' % аз in к and клон_шаблон in к, клони))

    glog.debug(git.checkout('-B', кандидат_клон_шаблон))

    for клон in клони:
        try:
            glog.debug(git.merge(клон))
        except sh.ErrorReturnCode_1 as e:
            log.error(e)
            git.merge('--abort')

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

    glog.debug(git.push(аз))
    glog.debug(git.checkout('main'))

    time.sleep(max(0, СГЛОБЯВАНЕ - сега().second))

def гласувай(водачи, клон_шаблон, кандидат_клон_шаблон, aз, съм_водач):
    log.info('Гласувам')

    for водач in водачи:
        glog.debug(git.fetch(водач))

    клони = вземи_клони(шаблон=кандидат_клон_шаблон, local=False)
    if not клони:
        log.error('Водачите не са си свършили работата. Поемам ролята на водач')
        съм_водач = True
        сглоби_минута(клон_шаблон, кандидат_клон_шаблон, аз)
        for fellow in вземи_съучастници():
            try:
                glog.debug(git.fetch(fellow['номер']))
                водачи.append(fellow['номер']) #TODO ако са много участници това може да избухне
            except Exception:
                log.error('Не успях да изтелгя последните промени от ' + fellow['номер']) 


        клони = вземи_клони(шаблон=кандидат_клон_шаблон, local=False)

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
    glog.debug(git.checkout('-B', кандидат_клон_шаблон+'+глас', '--track', best))
    while not гласувах:
        try:
            with open('гласове', 'a+') as f:
                f.write(аз+'\n')

            glog.debug(git.add('гласове'))
            glog.debug(git.commit('--gpg-sign='+аз, '-m', 'Глас от ' + аз))
            glog.debug(git.push(remote, 'HEAD:'+кандидат_клон_шаблон))
            гласувах = True
        except sh.ErrorReturnCode_1 as e:
            log.error(e)
            glog.debug(git.reset('--hard', 'HEAD~1'))
            glog.debug(git.pull())

    time.sleep(max(0, ГЛАСУВАНЕ - сега().second))
    return съм_водач

def приеми_минута(водачи, кандидат_клон_шаблон):
    log.info('Приемам минута')

    best = None
    best_count = None

    for водач in водачи:
        try:
            glog.debug(git.fetch(водач))
        except Exception as e:
            log.error(e)
            log.error('Не успях да се свържа с водач ' + водач)

    клони = вземи_клони(кандидат_клон_шаблон, local=False)

    for клон in клони:
        count = int(git('rev-list', '--count', клон))
        if not best or count > best_count:
            best = клон
            best_count = count

    log.info('Приемам ' + best)
    glog.debug(git.checkout('main'))
    glog.debug(git.reset(best, '--hard'))
    git.push(аз, 'main', '--force')

# План
## 0. Теглим main от някой от съучастниците които са на линия.
## 1. Всички промени се пращат към водачите до 30тата секунда от минутата. Водачите имат отговорност да синхронизират промените по между си.
## 2. Водачите слобяват кандидат минута, която съдържа ново време и нови водачи.
## 3. Всички кандидатстват за най-добрата минута, която водачите са предложили. Тоест, пращат комит.
## 4. Когато има много неразбирателство, увеличи броя водачи като добавиш себе си към водачите
## 5. Всички приемат минутата на водача с най-много гласове. Тоест, комити.
def минута(username, host, port):
    stored_exception = None

    glog.debug(git.checkout('main'))
    glog.debug(git.pull('--ff-only', 'origin'))

    fellows = вземи_съучастници()
    remotes = list(map(str.strip, git.remote().split('\n')))
    for fellow in fellows:
        if fellow['номер'] not in remotes:
            git.remote.add(fellow['номер'], fellow['адрес'])
        else:
            git.remote('set-url', fellow['номер'], fellow['адрес'])
        try:
            pull = git.pull('--ff-only', fellow['номер'], 'main')
            glog.debug(pull)
            if 'Already up to date' not in pull:
                log.info('Изтеглих най-новото състояние от ' + fellow['номер'])
        except Exception as e:
            log.debug('Не успях да се свържа с ' + fellow['номер'])
            continue

    glog.debug(git.push(аз, 'main', '--force'))

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
                съм_водач = съм_водач or водач == аз

            if съм_водач:
                log.info('Водач съм')
            else:
                log.info('Не съм водач. Водачи: %s' % водачи)
            съучастници = вземи_съучастници()

            remotes = list(map(str.strip, git.remote().split('\n')))
            for съучастник in съучастници:
                if съучастник['номер'] not in remotes:
                    git.remote.add(съучастник['номер'], съучастник['адрес'])
                else:
                    git.remote('set-url', съучастник['номер'], съучастник['адрес'])

            git.checkout('main')
            #if сега().second > СЛУШАНЕ:
            #    print(сега(), "Изчаквам новата минута")
            #    time.sleep(ПРИЕМАНЕ - сега().second - сега().microsecond/1000000) # TODO това работи добре
            #    continue

            изпращай_промени(водачи, клон_шаблон, username, host, port)

            if съм_водач:
                сглоби_минута(клон_шаблон, кандидат_клон_шаблон, аз)
            else:
                time.sleep(max(0, СГЛОБЯВАНЕ - сега().second))

            съм_водач = гласувай(водачи, клон_шаблон, кандидат_клон_шаблон, аз, съм_водач)

            приеми_минута(водачи, кандидат_клон_шаблон)

            if stored_exception:
                break

            time.sleep(max(0, ПРИЕМАНЕ - сега().second))
            log.info('Изтривам излишни клони')
            if съм_водач:
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

import socket
import select

def handler(chan, host, port):
    sock = socket.socket()
    try:
        sock.connect((host, port))
    except Exception as e:
        nlog.debug("Forwarding request to %s:%d failed: %r" % (host, port, e))
        return

    nlog.debug(
        "Connected!  Tunnel open %r -> %r -> %r"
        % (chan.origin_addr, chan.getpeername(), (host, port))
    )
    while True:
        r, w, x = select.select([sock, chan], [], [])
        if sock in r:
            data = sock.recv(1024)
            if len(data) == 0:
                break
            chan.send(data)
        if chan in r:
            data = chan.recv(1024)
            if len(data) == 0:
                break
            sock.send(data)
    chan.close()
    sock.close()
    nlog.debug("Tunnel closed from %r" % (chan.origin_addr,))

def reverse_forward_loop(transport, remote_host, remote_port):
    while True:
        chan = transport.accept(1000)
        if chan is None:
            continue
        thr = threading.Thread(
            target=handler, args=(chan, remote_host, remote_port)
        )
        thr.daemon = True
        thr.start()

def reverse_forward_tunnel(server_port, remote_host, remote_port, transport):
    transport.request_port_forward("", server_port)
    thr = threading.Thread(target=reverse_forward_loop, args=(transport, remote_host, remote_port))
    thr.daemon = True
    thr.start()

def раздели_адрес(адрес):
    username, server = адрес.split('@')
    username = username.split('/')[-1]
    server = server.split('/')[0]
    if server[-1] == ':':
        server_port = 22
    else:
        server_port = int(server.split(':')[1])
    server = server.split(':')[0]
    return username, server, server_port

if __name__ == '__main__':
    import argparse
    import getpass
    parser = argparse.ArgumentParser()
    parser.add_argument('--ssh-user', default=getpass.getuser())
    parser.add_argument('--ssh-host')
    parser.add_argument('--ssh-port', type=int, default=22)

    args = parser.parse_args()

    relay_ports_range = [10000, 11000]
 
    if not args.ssh_host:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())

        relays = []
        remote_port = None
        for съучастник in вземи_съучастници():
            nlog.debug('Пробвам %s за реле' % съучастник)
            username, server, port = раздели_адрес(съучастник['адрес'])

            if съучастник['номер'] == аз:
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

        reverse_forward_tunnel(
            remote_port, 'localhost', args.ssh_port, client.get_transport())
        ssh_host = server
        ssh_port = remote_port
    else:
        ssh_host = args.ssh_host
        ssh_port = args.ssh_port

    минута(args.ssh_user, ssh_host, ssh_port)
