#!../venv/bin/python3

import datetime
import time
import sh
import os
from помощни import State, calculate_minute_branch, сега, get_fellows, вземи_аз, get_head

аз = вземи_аз()
водач_папка = os.getcwd() + '/водач'

import colorlog
import logging
import paramiko
import network

import enlighten

log = colorlog.getLogger('минало')
nlog = colorlog.getLogger('мрежа')
glog = colorlog.getLogger('git')
log.setLevel(logging.DEBUG)
nlog.setLevel(logging.INFO)
glog.setLevel(logging.INFO)

ch = colorlog.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s:%(levelname)s:%(name)s:%(message)s',
    '%H:%M:%S'))

log.addHandler(ch)
nlog.addHandler(ch)
glog.addHandler(ch)

sh2 = sh(_err_to_out=True, _truncate_exc=False)
git = sh2.git

state = State.Начало

def sleep(seconds):
    global manager
    bar = manager.counter(total=seconds, desc='Sleep', unit='ticks', leave=False) 
    for s in range(seconds):
        time.sleep(1)
        bar.update()

    bar.close()

def to_state(new_state):
    global state
    if new_state == state:
        return

    l = list(State)
    state_index = l.index(state)
    previous_state = list(State)[(state_index-1)% len(l)]
    if (state_index + 1) % len(l) != l.index(new_state):
        raise RuntimeError("Неразрешено преминаване %s -> %s" % (state, new_state))

    s = сега().second
    if state != State.Начало and s < previous_state.value:
        log.info("Вероятно сме се забивили и минутата е преминала.")
        s += 60

    if s < state.value:
        seconds = state.value - s
        log.info("Изчаквам %d секунди да премине времето на %s" % (seconds, state))
        sleep(seconds)
    elif s == state.value:
        pass
    else:
        late = s - state.value
        log.warning("Закъсняваме с %d секунди във състояние %s" % (late, state))

    log.info('%s -> %s' % (state, new_state))
    state = new_state

def restart():
    import sys
    log.error('*' * 5 + ' Restarting ' + '*' * 5)
    python = sys.executable
    os.execl(python, python, *sys.argv)

def приготви():
    glog.debug(git.checkout('main'))
    modified = []
    untracked = []
    status = git.status('--porcelain')
    if not status:
        return
    glog.info(status)
    should_restart = False
    for status_line in status.strip().split('\n'):
        status, file_name = status_line.split()
        if status == 'M':
            modified.append(file_name)
        elif status == '??':
            untracked.append(file_name)

    for m in modified:
        glog.debug(git.add(m))

    if modified:
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
        glog.debug(pull)
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

def check_authorized_keys(minute_branch):
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

def check_fellows(minute_branch, username, host, port):
    водач_адрес = 'ssh://%s@%s:%s%s' % (username, host, port, водач_папка)

    съучастници = get_fellows()
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
            log.info('Намерих грешен адрес за себе си в съучастниците')
            съучастници.pop(намерих_себе_си_грешен_адрес)
        else:
            log.info('Не намерих себе си в съучастниците')
                    
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
        except sh.ErrorReturnCode_1 as e:
            glog.exception(e)

def слушай_промени(minute_branch, username, host, port):
    log.info('Слушам и изпращам промени')
    try:
        glog.debug(git.branch(minute_branch))
    except:
        pass
    glog.debug(git.checkout(minute_branch))
    try:
        glog.debug(git.pull(аз, minute_branch, '--rebase'))
    except Exception as e:
        if "couldn't find remote ref" in str(e):
            pass
        else:
            raise

    git.push(аз, minute_branch)

    check_authorized_keys(minute_branch)
    check_fellows(minute_branch, username, host, port)

    for f in get_fellows():
        try:
            pull = git.pull('--no-rebase', '--no-edit', f['id'], minute_branch)
            log.info(pull)
        except Exception as e:
            if 'CONFLICT' in str(e):
                log.error('Неразрешим конфликт при дърпането на %s от %s' % (minute_branch, f['id']))
                log.error(e)
                git.merge('--abort')
            else:
                log.error('Не успях да дръпна %s от %s' % (minute_branch, f['id']))

def сглоби_минута(minute_branch, аз):
    log.info('Сглобявам минута')

    време = сега().isoformat(timespec='minutes')
    #TODO вярваме на pre-receive hook че всички получени от remote аз-а ще са валидни
    клони = вземи_клони(local=False)

    glog.debug(git.checkout(minute_branch))
    glog.debug(git.pull(аз, minute_branch))

    with open('време', 'w') as f:
        f.write(време)

    with open('гласове', 'w') as f:
        f.write('')

    glog.debug(git.add('време'))
    glog.debug(git.add('гласове'))
    
    glog.debug(git.commit('--gpg-sign='+аз, '-m', 'време ' + време))

    glog.debug(git.push(аз, minute_branch))

def гласувай(minute_branch, aз):
    log.info('Гласувам')

    for fellow in get_fellows():
        try:
            glog.debug(git.fetch(fellow['id'], minute_branch))
        except:
            log.error('Не успях да изтелгя последните промени от ' + fellow['id']) 


    клони = вземи_клони(шаблон=minute_branch, local=False)

    best = None
    best_count = None
    for клон in клони:
        count = int(git('rev-list', '--count', клон))
        if not best or count > best_count:
            best = клон
            best_count = count

    log.info('Гласувам за ' + best)
    remote = best.split('/')[2]
    glog.debug(git.checkout(minute_branch))
    if remote != аз:
        git.reset('HEAD~1', '--hard') # махаме нашия време комит
    гласувах = False
    #TODO ако имаме промени които remote-а няма, ще се запазят ли или не?
    glog.debug(git.pull('--no-edit', '-s', 'recursive', '-X', 'theirs', remote, minute_branch))

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

def приеми_минута(minute_branch):
    log.info('Приемам минута')

    best = None
    best_count = None

    for f in get_fellows():
        try:
            glog.debug(git.fetch(f['id'], minute_branch))
            log.info('Изтеглих последни промени от ' + f['id'])
        except Exception as e:
            if 'Could not read from remote repository.' in str(e):
                log.error('Не успях да се свържа с ' + f['id'])
            elif "couldn't find remote ref" in str(e):
                log.error('Не успях да се намеря клон %s в %s' % (minute_branch, f['id']))
            else:
                log.error(e)

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

# План
## 0. Теглим main от някой от съучастниците които са на линия.
## 1. Всички промени се пращат към водачите до 30тата секунда от минутата във един и същ клон (зависещ от минутата). Този който е пратил промени следва да ги наблюдава - комита ако влезе в main, всичко точно, ако не, следва да се повтори следващата минута ( Водачите имат отговорност да синхронизират промените по между си.)
## 2. Водачите слобяват кандидат минута, която съдържа ново време и нови водачи.
## 3. Всички кандидатстват за най-добрата минута, която водачите са предложили. Тоест, пращат комит.
## 3.1 Когато има много неразбирателство, увеличи броя водачи като добавиш себе си към водачите
## 3.2 Когато няма кандидат минута, всеки поема водачеството и прави такава.
## 4. Всички приемат минутата на водача с най-много гласове. Тоест, комити.
def минути(username, host, port):
    stored_exception = None
    приготви()

    glog.debug(git.checkout('main'))
    #log.info('Взимаме от origin')
    #glog.debug(git.pull('--ff-only', 'origin'))

    if not os.path.exists(водач_папка):
        log.info('Правя гол водач с който ще общуват съучастниците')
        glog.debug(git.clone('.git', водач_папка, '--bare'))

    #TODO отдели
    fellows = get_fellows()
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
            if 'Fast-forward' in pull:
                log.info('Изтеглих най-новото състояние от ' + fellow['id'])
                if 'код/' in pull:
                    log.info('*'*3 + ' Промени в кода ' + '*'*3)
                    restart()
            else:
                log.info('Не взимам нищо ново от ' + fellow['id'])
        except Exception as e:
            log.debug('Не успях да се свържа с ' + fellow['id'])
            continue

    glog.debug(git.push(аз, 'main', '--force'))

    previous_head = None
    while True:
        try:
            head = get_head()
            if previous_head and git('rev-list', previous_head+'...'+ head, '--', 'код'):
                log.info('*'*3 + ' Промени в кода ' + '*'*3)
                restart()

            # Това е нужно защото може да сме влезли в цикъла след СЛУШАНЕ, тук имаме два варианта: 1/ да се преструваме че сме влезли по-рано, което правим по-долу, или 2/ да се включим само за частта, до която се е стигнало. TODO опитай вариант 2
            if сега().second > State.Слушане.value:
                to_state(State.Начало)

            to_state(State.Слушане)

            update_state('Слушам')
            minute_branch = calculate_minute_branch()

            git.checkout('main')

            слушай_промени(minute_branch, username, host, port)

            to_state(State.Сглобяване)

            # какви са последиците че всички правят това?
            update_state('Сглобявам')
            сглоби_минута(minute_branch, аз)

            to_state(State.Гласуване)
            update_state('Гласувам')
            гласувай(minute_branch, аз)

            to_state(State.Приемане)
            update_state('Приемам')
            приеми_минута(minute_branch)

            if stored_exception:
                break

            to_state(State.Почистване)

            update_state('Почиствам')
            log.info('Почиствам')

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

            приготви()
            to_state(State.Начало)
        except KeyboardInterrupt:
            if stored_exception:
                raise 
            import sys
            stored_exception = sys.exc_info()
            log.warning('Ще изляза в края на тази минута. Прекъсни отново за да изляза веднага')
        finally:
            previous_head = head

    #TODO if we have modified код since last loop, restart here

# Промени в кода се приемат само с няколко (3) подписа на разработчици (такива които са правили вече промени по кода).

def get_branch():
    return git.branch('--show-current').strip()

def get_votes():
    with open('гласове', 'r') as f:
        гласове = f.read().strip().split('\n')

    return гласове

def update_state(state):
    global status_bar
    status_bar.update(id=аз[:7], state=state, branch=get_branch(), head=get_head(),votes=len(get_votes()))

if __name__ == '__main__':
    import argparse
    import getpass
    parser = argparse.ArgumentParser()
    parser.add_argument('--ssh-user', default=getpass.getuser())
    parser.add_argument('--ssh-host')
    parser.add_argument('--ssh-port', type=int, default=22)

    args = parser.parse_args()

    global manager
    global status_bar
    manager = enlighten.get_manager()
    status_bar = manager.status_bar(
            status_format='{id}:{branch}/{head}({votes}){fill}{state}{fill}{elapsed}',
            color='bold_underline_bright_white_on_lightslategray',
            justify=enlighten.Justify.CENTER,
            id=аз[:7],
            branch=get_branch(),
            head=get_head(),
            votes=0,
            state='-',
            autorefresh=True,
            min_delta=0.5,
            leave=False)

    network_status = manager.status_bar(
            status_format='{address}{fill}{state}{fill}{threads}',
            color='bold_underline_bright_white_on_lightslategray',
            justify=enlighten.Justify.CENTER,
            state='...',
            address='Undefined',
            threads='0',
            autorefresh=True,
            min_delta=0.5,
            leave=False)

    #TODO премести в network.py
    relay_ports_range = [10000, 11000]
 
    if not args.ssh_host:
        #network_status.update(state='Търся реле')
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())

        relays = []
        remote_port = None
        for съучастник in get_fellows():
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

        #network_status.update(state='Свързвам се с реле ' + server)
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
            server, remote_port, 'localhost', args.ssh_port, client.get_transport(), network_status)
        ssh_host = server
        ssh_port = remote_port
    else:
        ssh_host = args.ssh_host
        ssh_port = args.ssh_port

    update_state('*')

    try:
        минути(args.ssh_user, ssh_host, ssh_port)
    finally:
        manager.stop()
