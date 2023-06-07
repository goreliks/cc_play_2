from flask import Flask, request, jsonify
from datetime import datetime
import math

app = Flask(__name__)

parking_lots = {}
lots_in_use = []


@app.route('/entry', methods=['POST'])
def entry():
    plate = request.args.get('plate')
    parking_lot = request.args.get('parkingLot')
    if not plate or not parking_lot:
        return 'Missing plate or parkingLot parameter', 400

    if parking_lot in lots_in_use:
        return 'Parking lot already in use', 400

    ticket_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
    parking_lots[ticket_id] = {
        'plate': plate,
        'parking_lot': parking_lot,
        'entry_time': datetime.now()
    }

    lots_in_use.append(parking_lot)

    return jsonify({
        'license_plate': plate,
        'parking_lot_id': parking_lot,
        'entry_time': parking_lots[ticket_id]['entry_time'],
        'ticket_id': ticket_id
    })


@app.route('/exit', methods=['POST'])
def exit_parking():
    ticket_id = request.args.get('ticketId')

    if not ticket_id:
        return 'Missing ticketId parameter', 400
    if ticket_id not in parking_lots:
        return 'Invalid ticketId', 400

    ticket = parking_lots[ticket_id]
    parking_lot_id = ticket['parking_lot']
    license_plate = ticket['plate']
    start_time = ticket['entry_time']
    end_time = datetime.now()

    parking_time = end_time - start_time
    parking_hours = parking_time.total_seconds() / 3600.0
    parking_hours_rounded = math.ceil(parking_hours * 4) / 4.0
    parking_charge = parking_hours_rounded * 10.0

    lots_in_use.remove(parking_lot_id)
    del parking_lots[ticket_id]

    return jsonify({
        'license_plate': license_plate,
        'parking_lot_id': parking_lot_id,
        'parking_time': str(parking_time),
        'charge': parking_charge
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0')
