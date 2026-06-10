import serial, time, base64, os

PORT = '/dev/cu.usbserial-144420'
FILE = os.path.join(os.path.dirname(__file__), 'main.py')

with open(FILE, 'rb') as f:
    content = f.read()

b64 = base64.b64encode(content).decode()
s = serial.Serial(PORT, 115200, timeout=1)

s.setDTR(False); s.setRTS(False); time.sleep(0.1)
s.setRTS(True);  time.sleep(0.1)
s.setRTS(False); time.sleep(2.5)

for i in range(30):
    s.write(b'\x03')
    time.sleep(0.05)
time.sleep(0.5)
s.read_all()

s.write(b'\r\x01')
time.sleep(0.8)
resp = s.read_all()

if b'raw REPL' not in resp:
    print("ERROR: Could not enter raw REPL")
    s.close()
    exit(1)

script = f"import ubinascii\ndata = ubinascii.a2b_base64('{b64}')\nf = open('main.py','wb')\nf.write(data)\nf.close()\nprint('DONE')"
s.write(script.encode() + b'\x04')
time.sleep(2.0)
out = b''
while True:
    chunk = s.read(256)
    if not chunk: break
    out += chunk

if b'DONE' in out:
    print("Upload successful!")
    s.setDTR(False); s.setRTS(False); time.sleep(0.1)
    s.setRTS(True);  time.sleep(0.1)
    s.setRTS(False)
else:
    print("ERROR:", repr(out))

s.close()
