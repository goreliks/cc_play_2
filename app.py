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
OWN_IP = os.getenv('OWN_IP')
processing_thread = None


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

    # # TODO: check if task_id below is relevant
    # task_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
    # return jsonify({
    #     'task_id': task_id
    # })
    return 'Task accepted', 200


# ENDPOINT FOR WORKER TO PULL TASK
@app.route('/pullTask', methods=['GET'])
def pull_task():
    if workQueue:
        response = workQueue.pop()
        return jsonify({
            'buffer': response[0],
            'iterations': response[1]
        })
    else:
        return None


# ENDPOINT FOR WORKER TO PUTT COMPLETED TASK
@app.route('/completed', methods=['PUT'])
def put_completed():
    data = request.data.decode('utf-8')
    if not data:
        return 'Missing data parameters', 400

    workComplete.append(data)

    return 'Task accepted', 200


@app.route('/pullCompleted', methods=['POST'])
def pull_completed_tasks():
    number_of_completed_tasks = int(request.args.get('top'))

    if not number_of_completed_tasks:
        return 'Missing top parameter', 400

    # TODO: check if this is the correct way to return the results
    # TODO: make that number_of_completed_tasks will be returner to the user even from other node (not MUST)
    result = []
    if len(workComplete) > number_of_completed_tasks:
        for i in range(number_of_completed_tasks):
            result.append(workComplete.pop())
        return result
    elif len(workComplete) > 0:
        for i in range(len(workComplete)):
            result.append(workComplete.pop())
        return result
    else:
        try:
            url = f'http://{SIBLING_IP}:5000/pullCompletedInternal?top={number_of_completed_tasks}'
            response = requests.post(url)
            if response.status_code == 200:
                data = response.json()
                return data
            pass
        # TODO: check what to return if there are no results
        except:
            return []


@app.route('/pullCompletedInternal', methods=['POST'])
def pull_completed_tasks_internal():
    number_of_completed_tasks_internal = int(request.args.get('top'))

    if not number_of_completed_tasks_internal:
        return 'Missing top parameter', 400

    result = []
    if len(workComplete) > number_of_completed_tasks_internal:
        for i in range(number_of_completed_tasks_internal):
            result.append(workComplete.pop())
        return result
    elif len(workComplete) > 0:
        for i in range(len(workComplete)):
            result.append(workComplete.pop())
        return result
    else:
        return result


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
                if not spawn_worker():
                    continue
        time.sleep(10)


def spawn_worker():
    try:
        ec2_worker = boto3.client('ec2')
        instance_type = 't2.micro'
        ami_id = 'ami-00aa9d3df94c6c354'

        own_ip = os.getenv('OWN_IP')
        sibling_ip = os.getenv('SIBLING_IP')

        with open('worker.py', 'r') as file:
            worker_code = file.read()

        user_data = f'''#!/bin/bash
        export PARENT_IP={own_ip}
        export SIBLING_IP={sibling_ip}
        sudo apt update
        sudo apt install python3-pip -y
        sudo pip3 install requests
        cat <<EOF > /home/worker.py
        {worker_code}
        EOF
        nohup python3 /home/worker.py
        '''

        response = ec2_worker.run_instances(
            ImageId=ami_id,
            InstanceType=instance_type,
            InstanceInitiatedShutdownBehavior='terminate',
            MinCount=1,
            MaxCount=1,
            UserData=user_data
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            global numOfWorkers
            numOfWorkers += 1
            return True

    except Exception as e:
        print(e)
        return False


def add_sibling():
    sibling_ip = os.getenv('SIBLING_IP')
    if sibling_ip:
        return sibling_ip
    else:
        return None


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
    SIBLING_IP = add_sibling()

