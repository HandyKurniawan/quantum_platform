import requests
import json
import mysql.connector
import time

mysql_config = {
    'user': 'handy',
    'password': 'handy',
    'host': 'ec2-13-51-79-239.eu-north-1.compute.amazonaws.com',
    'database': 'framework'
}


def send_rest_api_request(url, token):
    

    headers = {"Authorization": token}

    response = requests.request("GET", url, headers=headers)

    return response.json()

def get_ionq_characterization(token, UUID):

    url = "https://api.ionq.co/v0.3/characterizations/{}".format(UUID)

    response_json = send_rest_api_request(url, token)

    print(response_json)

    return response_json


import requests

APIKey = "xK95en5OdAnh8PzXSchJLGGLLTjgzfdt"
# APIKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImhhbmR5a3VyQHVjbS5lcyIsIm9yZ2FuaXphdGlvbiI6IjM0ZjYwZWM4IiwiaXNWZXJpZmllZCI6dHJ1ZSwiaWF0IjoxNzI0MzIxMzU0LCJleHAiOjE3MjQ5MjYxNTQsImF1ZCI6ImFwaSIsImlzcyI6Ik1wVE55Y3kzNzB4dklXTnV3cEVmWFJNM0xXMUQyT1A5Iiwic3ViIjoiZjMwYzFkYzQtNGQ1Zi00NzY4LThjMjQtMjJkM2Y0YzNkZTBkIiwianRpIjoiNDNiYWI2NzEtNzhiYS00NGUxLWFiOTEtYzlkYzViNTY0ZGMwIn0.AoUzteZhWXSDkn3S_Lny-QpkjIjgQLBMq3BDNV9c-TY"


# url = "https://api.ionq.co/v0.3/characterizations/backends/qpu.harmony/current"

url = "https://api.ionq.co/v0.3/characterizations/backends/qpu.forte-1/current"


# url = "https://api.ionq.co/v0.3/characterizations/05400dfa-e369-4a81-9d0a-30d1df1d0f12"

# headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImhhbmR5a3VyQHVjbS5lcyIsIm9yZ2FuaXphdGlvbiI6IjM0ZjYwZWM4IiwiaXNWZXJpZmllZCI6dHJ1ZSwiaWF0IjoxNzI0MzIxMzU0LCJleHAiOjE3MjQ5MjYxNTQsImF1ZCI6ImFwaSIsImlzcyI6Ik1wVE55Y3kzNzB4dklXTnV3cEVmWFJNM0xXMUQyT1A5Iiwic3ViIjoiZjMwYzFkYzQtNGQ1Zi00NzY4LThjMjQtMjJkM2Y0YzNkZTBkIiwianRpIjoiNDNiYWI2NzEtNzhiYS00NGUxLWFiOTEtYzlkYzViNTY0ZGMwIn0.AoUzteZhWXSDkn3S_Lny-QpkjIjgQLBMq3BDNV9c-TY"}

headers={
            "Accept": "application/json",
            "Authorization": "apiKey {}".format(APIKey)
        }

# "OnDufq8S8bMafAxLooRNwvaUjnCC5Oec"

response = requests.request("GET", url, headers=headers)

print(response.text)
# print(response.json()["fidelity"])
# print(response.json()["timing"])
# print(response.json()["date"])
# print(response.json()["id"])

# sh submit-job.sh xK95en5OdAnh8PzXSchJLGGLLTjgzfdt ghz-nine-qubits--ideal.json