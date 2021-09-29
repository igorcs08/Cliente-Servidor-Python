import socket
import pyaudio
import sys
import wave
import struct
import time

argumentos = sys.argv[1:]

HOST = ''
PORTA = int(argumentos[0])

udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

origem = (HOST, PORTA)
udp.bind(origem)
CHUNK = 64000

serializar = struct.Struct('iii')
info, _ = udp.recvfrom(CHUNK)
info = serializar.unpack(info)

amostra_tamanho = int(info[0])
canal = int(info[1])
framerate = int(info[2])

p = pyaudio.PyAudio()

stream = p.open(format = p.get_format_from_width(amostra_tamanho),
				channels = canal,
				rate = framerate,
				output=True)

data, _ = udp.recvfrom(CHUNK)
try:
	while len(data) > 0:
		# --- TESTANDO PYAUDIO
		udp.settimeout(10)
		stream.write(data)
		data, _ = udp.recvfrom(CHUNK)
except socket.timeout :
	stream.stop_stream()
	stream.close()
	p.terminate()	
	udp.close()