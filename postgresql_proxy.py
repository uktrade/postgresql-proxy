from gevent import monkey
monkey.patch_all()

import itertools
import os
import gevent
import socket
import struct


class ConnectionClosed(Exception):
    pass


class ProtocolError(Exception):
    pass


class AuthenticationError(Exception):
    pass


def main():
    env = normalise_environment(os.environ)
    UPSTREAM_HOST = env['UPSTREAM']['HOST']
    UPSTREAM_PORT = env['UPSTREAM']['PORT']

    DOWNSTREAM_IP = env['DOWNSTREAM']['IP']
    DOWNSTREAM_PORT = env['DOWNSTREAM']['PORT']

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


def normalise_environment(key_values):
    separator = '__'

    def get_first_component(key):
        return key.split(separator)[0]

    def get_later_components(key):
        return separator.join(key.split(separator)[1:])

    without_more_components = {
        key: value
        for key, value in key_values.items()
        if not get_later_components(key)
    }

    with_more_components = {
        key: value
        for key, value in key_values.items()
        if get_later_components(key)
    }

    def grouped_by_first_component(items):
        def by_first_component(item):
            return get_first_component(item[0])

        return itertools.groupby(
            sorted(items, key=by_first_component),
            by_first_component,
        )

    def items_with_first_component(items, first_component):
        return {
            get_later_components(key): value
            for key, value in items
            if get_first_component(key) == first_component
        }

    nested_structured_dict = {
        **without_more_components, **{
            first_component: normalise_environment(
                items_with_first_component(items, first_component))
            for first_component, items in grouped_by_first_component(with_more_components.items())
        }}

    def all_keys_are_ints():
        def is_int(string):
            try:
                int(string)
                return True
            except ValueError:
                return False

        return all([is_int(key) for key, value in nested_structured_dict.items()])

    def list_sorted_by_int_key():
        return [
            value
            for key, value in sorted(
                nested_structured_dict.items(),
                key=lambda key_value: int(key_value[0])
            )
        ]

    return \
        list_sorted_by_int_key() if all_keys_are_ints() else \
        nested_structured_dict


if __name__ == '__main__':
    main()
