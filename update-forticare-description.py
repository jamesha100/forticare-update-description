import sys
import time
from datetime import datetime
import csv
import requests
import json
from configparser import ConfigParser
from tqdm import tqdm

def get_access_token(fortigateapiinfo):

    url = 'https://customerapiauth.fortinet.com/api/v1/oauth/token/'
    headers = {
        'Content-Type': 'application/json'
    }

    body = {
        'username': fortigateapiinfo['username'],
        'password': fortigateapiinfo['password'],
        'client_id': fortigateapiinfo['client_id'],
        'grant_type': 'password'
    }

    response = requests.request('POST', url, headers=headers, data=json.dumps(body))

    if response.status_code == 200:
        return response.text
    else:
        sys.exit('Error getting Authentication Token!')

    print(response.status_code)
    print(response.text)
    return response.text

def refresh_access_token(refresh_token,fortigateapiinfo):
    print(refresh_token)

    url = 'https://customerapiauth.fortinet.com/api/v1/oauth/token/'
    headers = {
        'Content-Type': 'application/json'
    }

    body = {
        'client_id': fortigateapiinfo['client_id'],
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }

    response = requests.request('POST', url, headers=headers, data=json.dumps(body))

    if response.status_code == 200:
        pass
    else:
        sys.exit('Error getting Authentication Token!')

    print(response.status_code)
    print(response.text)
    return response.text

def line_count(csv_input_file):
    fp = open(csv_input_file, 'r')
    line_count = len(fp.readlines())
    return line_count

def update_description(access_token,serialNumber,description):

    url = 'https://support.fortinet.com/ES/api/registration/v3/products/description'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    body = {
        'serialNumber': serialNumber,
        'description': description
    }

    response = requests.request('POST', url, headers=headers, data=json.dumps(body))

    if response.status_code == 200:
        pass
    else:
        # sys.exit('Error updating description!')
        pass

    # print(response.status_code)
    # print(response.text)
    return response.status_code

if __name__ == '__main__':

    print('''
    ****************************************************
    *****   FortiCare Device Description Updater   *****
    *****   Written by James Hawkins July 2022     *****
    ****************************************************
    ''')

    # Read config.ini file
    config_object = ConfigParser()
    config_object.read('config.ini')
    fortigateapiinfo = config_object['FORTIGATE_API_USER']

    # Get initial Access Token and Refresh Token for subsequent API calls

    access_token_dict = json.loads(get_access_token(fortigateapiinfo))
    # print(access_token_dict)
    # print(type(access_token_dict))

    access_token = access_token_dict['access_token']
    # print(access_token)
    refresh_token = access_token_dict['refresh_token']
    # print(refresh_token)

    # Calculate access token expiration time in epoch time seconds
    access_token_expiration = time.time() + 3600
    # print(access_token_expiration)

    # Prompt user to enter name of CSV file
    csv_input_file_name = input('Enter the name of the CSV file containing update data: ')
    print()

    # Create output filename
    csv_output_filename = csv_input_file_name.split('.', 2)[0] + datetime.today().strftime('-results-%Y-%m-%d-%H-%M-%S.csv')
    # print(csv_output_filename)

    # Loop through CSV file
    with open(csv_input_file_name) as csv_input_file:
        csv_reader = csv.reader(csv_input_file, delimiter=',')

        # Get number of lines in input CSV file
        csv_input_file_line_count = line_count(csv_input_file_name)
        # print(csv_input_file_line_count)

        total_updates = 0
        successful_updates = 0
        unsuccessful_updates = 0

        with open(csv_output_filename, 'w', newline='') as output_file:
            csv_writer = csv.writer(output_file)
            # Write headers to output CSV file
            csv_writer.writerow(['Serial Number', ' Updated Description', 'HTTP Status Code'])

            for row in tqdm(csv_reader, total=csv_input_file_line_count,ncols = 100, desc='API Update Progress'):
                serialNumber = row[0]
                description = row[1]
                # print(serialNumber)
                # print(description)

                # Check and refresh access token if necesssary
                if time.time() < access_token_expiration - 100:
                    # print('No Refresh')
                    pass
                else:
                    # print('Refresh')
                    access_token_dict = json.loads(refresh_access_token(refresh_token,fortigateapiinfo))
                    access_token = access_token_dict['access_token']
                    refresh_token = access_token_dict['refresh_token']

                # Update device description
                update_result = update_description(access_token,serialNumber,description)
                total_updates += 1
                if update_result == 200:
                    successful_updates += 1
                else:
                    unsuccessful_updates += 1

                # Write result to CSV file
                csv_writer.writerow([serialNumber,description,update_result])

            print(f'\nTotal API Updates: {total_updates}   Successful API Updates: {successful_updates}   Unsuccessful API Updates: {unsuccessful_updates}\n')
            print(f'Results have been written to {csv_output_filename}')
            sys.exit()

