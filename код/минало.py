#!../venv/bin/python3

import datetime
import time
import sh
import os
from помощни import време_клон, СЛУШАНЕ, сега, вземи_водачи, изчисли_водачи, вземи_съучастници, вземи_аз

аз = вземи_аз()

import colorlog
import logging
log = colorlog.getLogger('минало')
log.setLevel(logging.DEBUG)

ch = colorlog.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(levelname)s:'+аз[:4]+':%(message)s'))

log.addHandler(ch)

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

        log.debug(git.checkout('-B', клон_шаблон+'-'+аз))

        with open('authorized_keys', 'a+') as f:
            f.write(my_key)
        log.debug(git.add('authorized_keys'))
        log.debug(git.commit('--gpg-sign='+аз, '-m', 'Добавям се към authorized_keys'))

    водач_папка = os.getcwd() + '/водач' #TODO направи ако не съществува чрез git clone .git водач --bare
    водач_адрес = 'ssh://%s@%s:%s%s' % (username, host, port, водач_папка)

    for водач in водачи:
        log.debug(git.fetch(водач['номер'], 'main'))
        if not намерих_себе_си:
            log.debug(git.push(водач['номер']))
        else:
            log.debug(git.checkout('-B', водач['номер']+'-main', '--track', водач['номер']+'/main'))
            съучастници = вземи_съучастници()
            намерих_себе_си = False
            намерих_себе_си_грешен_адрес = False
            for съучастник in съучастници:
                if съучастник['номер'] == аз:
                    if съучастник['адрес'] == водач_адрес:
                        намерих_себе_си = True
                    else:
                        намерих_себе_си_грешен_адрес = True

            if намерих_себе_си_грешен_адрес or not намерих_себе_си:
                log.info('Не намерих себе си в съучастниците на водач %s' % водач)
                log.debug(git.checkout('-B', клон_шаблон+'-'+аз))
                съучастници.append({'номер': аз, 'адрес': водач_адрес})
                with open('съучастници', 'w') as f:
                    for с in съучастници:
                        f.write('%s %s\n' % (с['номер'], с['адрес']))
                log.debug(git.add('съучастници'))
                if намерих_себе_си_грешен_адрес:
                    log.debug(git.commit('--gpg-sign='+аз, '-m', 'Обновявам адреса си в съучастници'))
                else:
                    log.debug(git.commit('--gpg-sign='+аз, '-m', 'Добавям се към съучастници'))

                try:
                    log.debug(git.push(водач['номер']))
                except sh.ErrorReturnCode_1 as e:
                    log.exception(e)

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
    клони = list(filter(lambda к: 'refs/remote/'+аз in к, вземи_клони(local=False)))

    log.debug(git.checkout('-B', кандидат_клон_шаблон))

    for клон in клони:
        log.debug(git.merge(клон))

    with open('време', 'w') as f:
        f.write(време)

    with open('гласове', 'w') as f:
        f.write('')

    with open('водачи', 'w') as f:
        f.write('\n'.join(map(lambda d: "%s" % (d['номер']), изчисли_водачи())))

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

    log.info('Гласувам за ' + best)
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

    log.info('Приемам ' + best)
    log.debug(git.checkout('main'))
    log.debug(git.merge('--ff-only', best))

# План
## 1. Всички промени се пращат към водачите до 30тата секунда от минутата. Водачите имат отговорност да синхронизират промените по между си.
## 2. Водачите слобяват кандидат минута, която съдържа ново време и нови водачи.
## 3. Всички кандидатстват за най-добрата минута, която водачите са предложили. Тоест, пращат комит.
## 4. Когато има много неразбирателство, увеличи броя водачи като добавиш себе си към водачите
## 5. Всички приемат минутата на водача с най-много гласове. Тоест, комити.
def минута(username, host, port):
    #TODO какво да правим когато сме изостанали от веригата? Може би за това ни служи origin...
    # Друг вариант е да си изберем водач на базата на сегашното време и да питаме него?
    stored_exception = None

    try:
        log.debug(git.checkout('main'))
        log.debug(git.pull('--ff-only', 'origin'))
        log.debug(git.push(аз, 'main', '--force'))
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
                    git.remote('set-url', съучастник['номер'], съучастник['адрес'])

            git.checkout('main')
            #if сега().second > СЛУШАНЕ:
            #    print(сега(), "Изчаквам новата минута")
            #    time.sleep(ПРИЕМАНЕ - сега().second - сега().microsecond/1000000) # TODO това работи добре
            #    continue

            изпращай_промени(водачи, клон_шаблон, username, host, port)

            if съм_водач:
                сглоби_минута(кандидат_клон_шаблон, аз)
            else:
                time.sleep(max(0, СГЛОБЯВАНЕ - сега().second))

            гласувай(водачи, кандидат_клон_шаблон, аз)

            приеми_минута(водачи, кандидат_клон_шаблон)

            if stored_exception:
                break

            time.sleep(max(0, ПРИЕМАНЕ - сега().second))

            log.info('Изтривам излишни клони')
            if съм_водач:
                клони = вземи_клони(local=False)
                git.push(аз,'main')
                for клон in клони:
                    шаблон = 'refs/remotes/%s/' % аз
                    if шаблон in клон and клон != 'refs/remotes/%s/main' % аз:

                        log.debug(клон)
                        клон = клон.split(шаблон)[1]
                        log.debug(git.push(аз, '--delete', клон))

            клони = вземи_клони(local=True)
            for клон in клони:
                if клон != 'refs/heads/main':
                    клон = клон.split('refs/heads/')[1]
                    log.debug(git.branch('-D', клон))
        except KeyboardInterrupt:
            if stored_exception:
                raise 
            import sys
            stored_exception = sys.exc_info()
            log.warning('Ще изляза в края на тази минута. Прекъсни отново за да изляза веднага')


# Промени в кода се приемат само с няколко (3) подписа на разработчици (такива които са правили вече промени по кода).

def handler(chan, host, port):
    import socket
    import select
    sock = socket.socket()
    try:
        sock.connect((host, port))
    except Exception as e:
        log.debug("Forwarding request to %s:%d failed: %r" % (host, port, e))
        return

    log.debug(
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
    log.debug("Tunnel closed from %r" % (chan.origin_addr,))

def reverse_forward_loop(transport):
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
    import threading
    transport.request_port_forward("", server_port)
    thr = threading.Thread(target=reverse_forward_loop, args=(transport,))
    thr.daemon = True
    thr.start()


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
        import paramiko
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())

        #TODO find server in съучастници където реда няма %(hostname)s
        server = None
        server_port = None
        for съучастник in вземи_съучастници():
            username, server = съучастник['адрес'].split('@')
            username = username.split('/')[-1]
            server = server.split('/')[0]
            if server[-1] == ':':
                server_port = 22
            else:
                server_port = int(server.split(':')[1])
            if server_port > relay_ports_range[0] and server_port < relay_ports_range[1]:
                continue
            server = server.split(':')[0]
        if not server:
            raise RuntimeError("Нямам реално IP, но нямам и прехвърлящ сървър")

        log.debug("Connecting to ssh host %s:%d ..." % (server, server_port))
        try:
            client.connect(
                server,
                server_port,
                username=username,
                #key_filename=options.keyfile,
                #look_for_keys=options.look_for_keys,
                #password=password,
            )
        except Exception as e:
            log.error(e)
            sys.exit(1)

        import random 
        remote_port = random.randint(*relay_ports_range)

        log.info(
            "Now forwarding remote port %d to %s:%d ..."
            % (remote_port, 'localhost', args.ssh_port)
        )

        reverse_forward_tunnel(
            remote_port, 'localhost', args.ssh_port, client.get_transport()
        )
        ssh_host = server
        ssh_port = remote_port
    else:
        ssh_host = args.ssh_host
        ssh_port = args.ssh_port

    минута(args.ssh_user, ssh_host, ssh_port)
