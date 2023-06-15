import sys
import time

from flask import Flask, request, jsonify
from datetime import datetime
import os
import threading
import boto3
import requests

app = Flask(__name__)

workQueue = []
workComplete = []
maxNumOfWorkers = 3
numOfWorkers = 0
SIBLING_IP = None
OWN_IP = None
processing_thread = None
worker_list = []


@app.route('/addIPs', methods=['PUT'])
def add_ips():
    data = request.get_json()
    own_ip = data.get('own_ip')
    sibling_ip = data.get('sibling_ip')

    if own_ip and sibling_ip:
        global SIBLING_IP
        global OWN_IP
        SIBLING_IP = sibling_ip
        OWN_IP = own_ip

        return 'IPs added successfully'
    else:
        return 'Invalid IP addresses', 400


@app.route('/enqueue', methods=['PUT'])
def enqueue():
    iterations_num = request.args.get('iterations')
    data = request.data.decode('utf-8')
    if not iterations_num or not data:
        return 'Missing iterations or data parameters', 400

    iterations_num = int(iterations_num)
    workQueue.append((data, iterations_num, datetime.now()))

    if not processing_thread or not processing_thread.is_alive():
        processing_th = threading.Thread(target=timer_for_new_worker, daemon=True)
        processing_th.start()

    return f'Task accepted for buffer: {data}', 200


# ENDPOINT FOR WORKER TO PULL TASK
@app.route('/pullTask', methods=['GET'])
def pull_task():
    if workQueue:
        response = workQueue.pop(0)
        return jsonify({
            'buffer': response[0],
            'iterations': response[1]
        })
    else:
        return 'No tasks available', 204


# ENDPOINT FOR WORKER TO PUTT COMPLETED TASK
@app.route('/completed', methods=['POST'])
def put_completed():
    data = request.get_json()
    if data:
        workComplete.append(data)
        return 'Task accepted', 200
    return 'Missing data parameters', 400


@app.route('/pullCompleted', methods=['POST'])
def pull_completed_tasks():
    number_of_completed_tasks = int(request.args.get('top'))

    if not number_of_completed_tasks:
        return 'Missing top parameter', 400

    result = []
    if len(workComplete) > number_of_completed_tasks:
        for i in range(number_of_completed_tasks):
            result.append(workComplete.pop(0))
        return jsonify(result)
    elif len(workComplete) > 0:
        for i in range(len(workComplete)):
            result.append(workComplete.pop(0))
        return jsonify(result)
    else:
        try:
            global SIBLING_IP
            url = f'http://{SIBLING_IP}:5000/pullCompletedInternal?top={number_of_completed_tasks}'
            response = requests.post(url)
            if response.status_code == 200:
                data = response.json()
                return jsonify(data)
        except:
            return 'No tasks available', 204

    return 'No tasks available', 204


@app.route('/pullCompletedInternal', methods=['POST'])
def pull_completed_tasks_internal():
    number_of_completed_tasks_internal = int(request.args.get('top'))

    if not number_of_completed_tasks_internal:
        return 'Missing top parameter', 400

    result = []
    if len(workComplete) > number_of_completed_tasks_internal:
        for i in range(number_of_completed_tasks_internal):
            result.append(workComplete.pop(0))
        return jsonify(result)
    elif len(workComplete) > 0:
        for i in range(len(workComplete)):
            result.append(workComplete.pop(0))
        return jsonify(result)
    else:
        return 'No tasks available', 204


@app.route('/workerDone', methods=['POST'])
def worker_done():
    global numOfWorkers
    data = request.get_json()
    if data and 'signal' in data and data['signal'] == 1:
        numOfWorkers += data['signal']
        return 'Signal received and incremented', 200
    else:
        return 'Invalid request data', 400


def timer_for_new_worker():
    # rate limit - number of new workers per time period
    # rate limit - total number of new workers
    global workQueue
    global numOfWorkers
    global maxNumOfWorkers
    while workQueue:
        if (datetime.now() - workQueue[-1][-1]).total_seconds() > 15:
            if numOfWorkers < maxNumOfWorkers:
                worker = spawn_worker()
                if not worker:
                    continue
                else:
                    numOfWorkers += 1
                    time.sleep(30)


def spawn_worker():
    try:
        ec2_worker = boto3.resource('ec2', region_name='eu-west-1')
        instance_type = 't2.micro'
        ami_id = 'ami-00aa9d3df94c6c354'

        global OWN_IP
        global SIBLING_IP

        with open('worker.py', 'r') as file:
            worker_code = file.read()

        user_data = f'''#!/bin/bash
        sudo apt update
        sudo apt install python3-pip -y
        sudo pip3 install requests
        cat <<EOF > ./worker.py
{worker_code}
EOF
        nohup python3 ./worker.py {OWN_IP} {SIBLING_IP}
        '''

        instances = ec2_worker.create_instances(
            ImageId=ami_id,
            InstanceType=instance_type,
            InstanceInitiatedShutdownBehavior='terminate',
            MinCount=1,
            MaxCount=1,
            UserData=user_data
        )

    except Exception as e:
        print('Worker creation fail', e)
        return False
    return True


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

