from gevent import monkey
monkey.patch_all()

import os
import gevent
import socket


def main():
    UPSTREAM_HOST = os.environ['UPSTREAM_HOST']
    UPSTREAM_PORT = os.environ['UPSTREAM_PORT']
    DOWNSTREAM_IP = os.environ['DOWNSTREAM_IP']
    DOWNSTREAM_PORT = os.environ['DOWNSTREAM_PORT']
    MAX_READ = 66560

    def handle_downstream(downstream_sock):
        upstream_sock = None

        try:
            upstream_sock = upstream_connect()
            proxy_both_directions(downstream_sock, upstream_sock)
        except:
            pass
        finally:
            if upstream_sock is not None:
                try:
                    upstream_sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    # Could have shutdown already
                    pass
                finally:
                    upstream_sock.close()

            try:
                downstream_sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                # Could have shutdown already
                pass
            finally:
                downstream_sock.close()

    def upstream_connect():
        upstream_sock = socket.create_connection((UPSTREAM_HOST, UPSTREAM_PORT))
        upstream_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        return upstream_sock

    def proxy_both_directions(sock_a, sock_b):
        done = gevent.event.Event()

        def _proxy(source, target):
            try:
                chunk = source.recv(MAX_READ)
                while chunk:
                    target.sendall(chunk)
                    chunk = source.recv(MAX_READ)
            finally:
                done.set()

        a_to_b_greenlet = gevent.spawn(_proxy, sock_a, sock_b)
        b_to_a_greenlet = gevent.spawn(_proxy, sock_b, sock_a)
        done.wait()

        a_to_b_greenlet.kill()
        b_to_a_greenlet.kill()
        a_to_b_greenlet.join()
        b_to_a_greenlet.join()

    def get_new_socket():
        sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM,
                             proto=socket.IPPROTO_TCP)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        return sock

    sock = get_new_socket()
    sock.bind((DOWNSTREAM_IP, int(DOWNSTREAM_PORT)))
    sock.listen(socket.IPPROTO_TCP)

    while True:
        downstream_sock, _ = sock.accept()
        gevent.spawn(handle_downstream, downstream_sock)


if __name__ == '__main__':
    main()
