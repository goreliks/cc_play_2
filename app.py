from flask import Flask, request, jsonify
from datetime import datetime
import math

app = Flask(__name__)

workQueue = []
workComplete = []
maxNumOfWorkers = 2
numOfWorkers = 0


@app.route('/enqueue', methods=['PUT'])
def enqueue():
    iterations_num = request.args.get('iterations')
    data = request.data.decode('utf-8')
    if not iterations_num or not data:
        return 'Missing iterations or data parameters', 400

    iterations_num = int(iterations_num)
    workQueue.append((data, iterations_num, datetime.now()))
    if not numOfWorkers:
        spawn_worker()

    # # TODO: check if task_id below is relevant
    # task_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
    # return jsonify({
    #     'task_id': task_id
    # })
    return 'Task accepted', 200


@app.route('/pullTask', methods=['GET'])
def pull_task():
    if workQueue:
        return workQueue.pop()
    return None


@app.route('/completed', methods=['PUT'])
def put_completed():
    data = request.data.decode('utf-8')
    if not data:
        return 'Missing data parameters', 400

    workComplete.append(data)

    return 'success'


@app.route('/pullCompleted', methods=['POST'])
def pull_completed_tasks():
    number_of_completed_tasks = int(request.args.get('top'))

    if not number_of_completed_tasks:
        return 'Missing top parameter', 400

    # TODO: check if this is the correct way to return the results
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
            # TODO: should otherNode return to user directly?
            # return otherNode.pullCompleteInternal(n)
            pass
        # TODO: check what to return if there are no results
        except:
            return []


def timer_for_new_worker():
    # rate limit - number of new workers per time period
    # rate limit - total number of new workers
    # check the Queue is not empty
    if (datetime.now() - workQueue[-1][-1]) > 15:
        if numOfWorkers < maxNumOfWorkers:
            spawn_worker()
        else:
            # if otherNode.TryGetNodeQuota():
            #     maxNumOfWorkers+=1
            pass


def spawn_worker():
    pass


def add_sibling(other):
    pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
