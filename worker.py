from datetime import datetime
import hashlib
import requests
import time
import os
import sys

parent_ip = None
sibling_ip = None
nodes = []


def do_work(buffer, iterations):
    if isinstance(buffer, str):
        buffer = buffer.encode('utf-8')
    output = hashlib.sha512(buffer).digest()
    for i in range(iterations-1):
        output = hashlib.sha512(output).digest()
    return output.hex()


def give_me_work(node_ip):
    url = f'http://{node_ip}:5000/pullTask'
    response = requests.get(url)
    if response.status_code == 200:
        # gets a task from the node in form of a dictionary
        # {'buffer': buffer, 'iterations': iterations}
        return response.json()
    else:
        return None


def completed(node_ip, buffer, iters, result):
    url = f'http://{node_ip}:5000/completed'
    data = {'buffer': buffer, 'iterations': iters, 'result': result}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return True
    else:
        return None


def worker_done(node_ip):
    url = f'http://{node_ip}:5000/workerDone'
    data = {'signal': 1}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return True
    else:
        return None


def loop():
    global nodes
    last_time = datetime.now()
    while (datetime.now() - last_time).total_seconds() <= 30:
        for node in nodes:
            work = give_me_work(node)
            if work:
                result = do_work(work['buffer'], work['iterations'])
                res = completed(node, work['buffer'], work['iterations'], result)
                last_time = datetime.now()
                continue

        time.sleep(5)

    worker_done(nodes[0])
    os.system('sudo shutdown -h now')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python3 worker.py <parent_ip> <sibling_ip>')
        sys.exit(1)
    parent_ip = sys.argv[1]
    sibling_ip = sys.argv[2]
    nodes = [parent_ip, sibling_ip]
    loop()
