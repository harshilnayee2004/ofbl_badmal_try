import requests
import hashlib
import random
import re
import time


def build_digest_header(ptz_url,username,password,uri):
    # Step 1: get challenge
    r1 = requests.post(ptz_url)
    www_auth = r1.headers.get("WWW-Authenticate")

    realm = re.search('realm="(.*?)"', www_auth).group(1)
    nonce = re.search('nonce="(.*?)"', www_auth).group(1)
    opaque = re.search('opaque="(.*?)"', www_auth).group(1)

    method = "POST"
    nc = "00000001"
    cnonce = hashlib.md5(str(random.random()).encode()).hexdigest()[:16]

    ha1 = hashlib.md5(f"{username}:{realm}:{password}".encode()).hexdigest()
    ha2 = hashlib.md5(f"{method}:{uri}".encode()).hexdigest()

    response_digest = hashlib.md5(
        f"{ha1}:{nonce}:{nc}:{cnonce}:auth:{ha2}".encode()
    ).hexdigest()

    auth_header = (
        f'Digest username="{username}", realm="{realm}", '
        f'nonce="{nonce}", uri="{uri}", '
        f'response="{response_digest}", opaque="{opaque}", '
        f'qop=auth, nc={nc}, cnonce="{cnonce}"'
    )

    return auth_header

class PTZControlService:

    def control_roof_top_1(pan, tilt, zoom):

        payload = {
            "Type": 1,
            "Dev": 1,
            "Ch": 1,
            "Data": {
                "P": pan,
                "T": tilt,
                "Z": zoom
            }
        }
        base_url = "http://192.168.0.128"
        username = "admin"
        password = "Mipl@123"

        ptz_url = f"{base_url}/digest/frmPTZDomeLocation"
        uri = "/digest/frmPTZDomeLocation"
        headers = {
            "Content-Type": "application/json",
            "Authorization": build_digest_header(ptz_url,username,password,uri)
        }

        r = requests.post(ptz_url, json=payload, headers=headers)
        print("Status:", r.status_code, r.text)

    
    def start_action_1(command):
        base_url = "http://192.168.0.129"
        if command in (13,14,11,12):
            # {Type: 1, Dev: 1, Ch: 1, Data: {Cmd: 11, IsStop: 1, Speed: 5}}
            payload = {"Type": 1, "Dev": 1, "Ch": 1, "Data": {"Cmd": command,"IsStop":0,"Speed": 5}}
            ptz_url = f"{base_url}/digest/frmPTZControl"
            uri = "/digest/frmPTZControl"
        else:
            payload = {"Type": 1, "Dev": 1, "Ch": 1, "Data": {"Cmd": command, "Speed": 10}}
            ptz_url = f"{base_url}/digest/frmPTZDomePtzControl"
            uri = "/digest/frmPTZDomePtzControl"

        username = "admin"
        password = "Mipl@123"

        headers = {
            "Content-Type": "application/json",
            "Authorization": build_digest_header(ptz_url,username,password,uri)
        }

        r = requests.post(ptz_url, json=payload, headers=headers)
        print("Status:", r.status_code, r.text)

    
    def end_action_1(command):
        
        base_url = "http://192.168.0.129"
        if command in (13,14,11,12):
            # {Type: 1, Dev: 1, Ch: 1, Data: {Cmd: 11, IsStop: 1, Speed: 5}}
            payload = {"Type": 1, "Dev": 1, "Ch": 1, "Data": {"Cmd": command,"IsStop":1,"Speed": 5}}
            ptz_url = f"{base_url}/digest/frmPTZControl"
            uri = "/digest/frmPTZControl"
        else:
            payload = {"Type": 1, "Dev": 1, "Ch": 1, "Data": {"Cmd": command, "Speed": 0}}
            ptz_url = f"{base_url}/digest/frmPTZDomePtzControl"
            uri = "/digest/frmPTZDomePtzControl"

        username = "admin"
        password = "Mipl@123"

        
        headers = {
            "Content-Type": "application/json",
            "Authorization": build_digest_header(ptz_url,username,password,uri)
        }

        r = requests.post(ptz_url, json=payload, headers=headers)
        print("Status:", r.status_code, r.text)