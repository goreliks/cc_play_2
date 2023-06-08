from datetime import datetime
import hashlib
import requests
import time
import os

parent_ip = os.getenv('PARENT_IP')
sibling_ip = os.getenv('SIBLING_IP')
nodes = [parent_ip, sibling_ip]


def do_work(buffer, iterations):
    output = hashlib.sha512(buffer).digest()
    for i in range(iterations-1):
        output = hashlib.sha512(output).digest()
    return output


def give_me_work(node_ip):
    url = f'http://{node_ip}:5000/pullTask'
    response = requests.get(url)
    if response.status_code == 200:
        # gets a task from the node in form of a dictionary
        # {'buffer': buffer, 'iterations': iterations}
        return response.json()
    else:
        return None


def completed(node_ip, result):
    url = f'http://{node_ip}:5000/completed'
    headers = {'Content-Type': 'text/plain'}
    response = requests.put(url, data=result, headers=headers)
    if response.status_code == 200:
        return True
    else:
        return None


def worker_done(node_ip):
    url = f'http://{node_ip}:5000/workerDone'
    headers = {'Content-Type': 'application/json'}
    data = {'signal': 1}
    response = requests.post(url, data=data, headers=headers)
    if response.status_code == 200:
        return True
    else:
        return None


def loop():
    global nodes
    last_time = datetime.now()
    while (datetime.now() - last_time).total_seconds() <= 60*10:
        for node in nodes:
            work = give_me_work(node)
            if work:
                result = do_work(work['buffer'], work['iterations'])
                res = completed(node, result)
                last_time = datetime.now()
                continue

        time.sleep(100)

    worker_done(nodes[0])
    os.system('sudo shutdown -h now')


if __name__ == '__main__':
    loop()
