import socket
import select
import colorlog
import threading

nlog = colorlog.getLogger('мрежа')

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
