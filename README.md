# intelligent-cam-server

## Installation
- Install dependencies: ```pip install -r requirements.txt ```
- Install openCV
- Copy two folders **imagezmq** and **raspberrypi** onto the raspberry pi
## Usage
- On the Raspberry Pi: ```python client.py -i <IP address of the server>```
- To host on localhost: ``` flask run```
- To host on LAN: ``` flask run --host=0.0.0.0```

