import socket
import struct
import sys
import threading, time

"""
class Cliente(threading.Thread):
	def __init__(self, host, porta, porta_udp, socket_tcp):
		self.host = host
		self.porta = porta
		self.porta_udp = porta_udp
		self.socket_tcp = socket_tcp
		threading.Thread.__init__(self)

	def run(self):
		while True:
			tam = self.socket_tcp.recv(1024).decode()
			time.sleep(0.5)
			serializar = struct.Struct("ii{}s" .format(tam))
			announce = serializar.unpack(self.socket_tcp.recv(1024))
			print(announce[2].decode())
	
	def parar_thread(self):
		try:
			tcp.shutdown(0)
		except:
			tcp.close()
"""

def hello(udpPort: int):
	commandType = socket.htons(0)
	udpPort = socket.htons(udpPort)
	return struct.pack('iH', commandType, udpPort)

def setStation(stationNumber: int):
	commandType = socket.htons(1)
	stationNumber = socket.htons(stationNumber)
	return struct.pack('iH', commandType, stationNumber)

if __name__ == '__main__':
	argumentos = sys.argv[1:]
	tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	
	destino = (argumentos[0], int(argumentos[1]))
	tcp.connect(destino)
	"""
	cliente = Cliente(argumentos[0], int(argumentos[1]), int(argumentos[2]), tcp)
	cliente.start()
	"""

	tcp.send(hello(int(argumentos[2])))

	# --- RECEBENDO LISTA DAS ESTACOES <WELCOME>
	serializar = struct.Struct('ii')
	a = serializar.unpack(tcp.recv(1024))

	if socket.ntohs(a[0]) == 0:
		print("Qnt de estacoes: ",socket.ntohs(a[1]))
		num = int(input("Escolha a estacao: \n"))
		tcp.send(setStation(num))

		c = ''

		while c != 'q':
			tam = tcp.recv(1024).decode()
			time.sleep(0.1)
			serializar = struct.Struct("ii{}s" .format(tam))
			announce = serializar.unpack(tcp.recv(1024))
			if (socket.ntohs(announce[0]) == 1):				
				print(announce[2].decode())				
				while True:				
					c = input('Escolha uma estacao ou q seguido de enter para sair: ')
					if c == 'q':
						break
					else:
						tcp.send(setStation(int(c)))
						break					
			elif (socket.ntohs(announce[0]) == 2):
				print(announce[2].decode())
				#cliente.parar_thread()
				break
	else:
		tcp.close()
	

tcp.close()