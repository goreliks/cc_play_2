import sys
import requests


def update_ips(ip1, ip2):
    endpoint1 = f'http://{ip1}:5000/addIPs'
    endpoint2 = f'http://{ip2}:5000/addIPs'

    # Prepare the data to be sent in the PUT request
    data_for_1 = {
        'own_ip': ip1,
        'sibling_ip': ip2
    }

    data_for_2 = {
        'own_ip': ip2,
        'sibling_ip': ip1
    }

    try:
        # Send PUT request to Endpoint 1
        response1 = requests.put(endpoint1, json=data_for_1)
        response1.raise_for_status()  # Raise an exception for 4xx or 5xx status codes

        # Send PUT request to Endpoint 2
        response2 = requests.put(endpoint2, json=data_for_2)
        response2.raise_for_status()

        print('IPs updated successfully')
    except requests.exceptions.RequestException as e:
        print(f'Error updating IPs: {e}')


if __name__ == '__main__':
    # Check if both IP addresses are provided as command-line arguments
    if len(sys.argv) != 3:
        print('Usage: python3 update_ips.py <IP1> <IP2>')
        sys.exit(1)

    own_ip = sys.argv[1]
    sibling_ip = sys.argv[2]

    update_ips(own_ip, sibling_ip)
