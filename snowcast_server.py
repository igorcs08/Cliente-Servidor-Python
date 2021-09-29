import socket
import struct
import threading
import sys
import os
import pyaudio
import wave
import time

class clientes(threading.Thread):

	def __init__(self, conexao, cliente, mutex):
		self.conexao = conexao
		self.cliente = cliente
		self.porta_udp = 0
		self.estacao = 0
		self.ouvindo = True
		self.commandType = 0
		self.estacao_anterior = 0
		self.mutex = mutex
		threading.Thread.__init__(self)

	def run(self):
		# --- RECEBENDO HELLO DO CLIENTE E A PORTA UDP
		msg = self.conexao.recv(1024)
		self.commandType, self.porta_udp = struct.unpack('iH', msg)
		self.commandType = socket.ntohs(self.commandType)
		self.porta_udp = socket.ntohs(self.porta_udp)
		print("\nHello recebido {} do cliente {}".format((self.commandType, self.porta_udp), self.cliente))

		if self.commandType == 0:
			#print("\nHello recebido do ", self.cliente)
			#print(self.getDestino())
			# --- ENVIANDO LISTA DAS ESTACOES	
			a = welcome(len(threads_musicas))
			serializar = struct.Struct('ii')
			self.conexao.send(serializar.pack(*a))
			print("\nLista de estacoes enviadas para ", self.cliente)
			
			# --- RECEBENDO ESTACAO ESCOLHIDA
			self.receiveStation()
			if self.verificaInvalido(self.estacao):
				self.estacao_anterior = self.estacao
				while True:
					with self.mutex:
						if self.verificaInvalido(self.estacao):
							if threads_musicas[self.estacao].verificarConectados(self):
								try:
									self.receiveStation()
									threads_musicas[self.estacao_anterior].removeCliente(self)
									self.estacao_anterior = self.estacao
									self.control()
								except:
									if self.verificaInvalido(self.estacao) and threads_musicas[self.estacao].verificarConectados(self):
										threads_musicas[self.estacao].removeCliente(self)
									threads_clientes.remove(self)
									print("\nCliente "+str(self.cliente)+" desconectado")
									break								
							else:
								try:
									self.control()
								except:
									print("\nCliente "+str(self.cliente)+" desconectado")
									break								
						else:
							self.invalidCommand()
			else:
				self.invalidCommand()						
		else :
			print("\nNao foi recebido Hello")
			self.conexao.close()	
	
	def getDestino(self):
		return (self.cliente[0], self.porta_udp)

	def getConexao(self):
		return self.conexao

	def verificaInvalido(self, estacao):
		if 0 <= estacao < len(threads_musicas):
			return True
		return False

	def receiveStation(self):
		msg = self.conexao.recv(1024)
		self.commandType, self.estacao = struct.unpack('iH', msg)
		self.commandType = socket.ntohs(self.commandType)		
		self.estacao = socket.ntohs(self.estacao)

	def control(self):		
		print("\nRecebi do cliente {} a estacao {}".format(self.cliente, self.estacao))
		#print("\nEstacao recebida: ", self.estacao)
		if self.commandType == 1:
			# --- SENDING ANNOUNCE
			if self.verificaInvalido(self.estacao):
				musica = announce(threads_musicas[self.estacao].nome_musica)
				serializar = struct.Struct("ii{}s" .format(musica[1]))
				musica = serializar.pack(*musica)
				tam = "{}".format(len(threads_musicas[self.estacao].nome_musica)).encode()
				self.conexao.send(tam)
				time.sleep(0.1)
				self.conexao.send(musica)
				print("\nAnnounce enviado para: ", self.cliente)
				threads_musicas[self.estacao].addCliente(self)
			else:
				self.invalidCommand()
		
	def invalidCommand(self):		
		replyMsg = self.comandoInvalido(self.commandType, self.estacao)
		tam = "{}".format(replyMsg[1]).encode()
		serializar = struct.Struct('ii{}s'.format(replyMsg[1]))
		self.conexao.send(tam)
		replyMsg = serializar.pack(*replyMsg)
		self.conexao.send(replyMsg)
		print("\nInvalidCommand enviado para: ", self.cliente)
		with self.mutex:
			if not self.ouvindo:				
				threads_musicas[self.estacao].removeCliente(self)
			threads_clientes.remove(self)
		self.conexao.close()

	def parar(self):
		try:
			self.conexao.shutdown(0)
		except:
			self.conexao.close()

	def comandoInvalido(self, commandType, estacao = None):
		replyType = 2
		if commandType == 1:
			if 0 < estacao >= len(threads_musicas):
				replyString = "Estacao {} nao existe".format(estacao).encode()
				replyStringSize = len(replyString)
				info = [socket.htons(replyType), replyStringSize, replyString]
				return info

class Estacao(threading.Thread):

	def __init__(self, nome_musica, destino = None):
		self.nome_musica = nome_musica
		self.clientes_conectados = []
		self.info_musica = 0
		self.vaiTocar = True		
		threading.Thread.__init__(self)

	def run(self):
		CHUNK = 16000
		udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		print("\nEnviando musica %s"%(self.nome_musica))
		while self.vaiTocar:
			wavefile = wave.open('musicas/'+self.nome_musica, 'rb')
			info = [wavefile.getsampwidth(), wavefile.getnchannels(), wavefile.getframerate()]
			serializar = struct.Struct('iii')
			self.info_musica = serializar.pack(*info)
			
			data = wavefile.readframes(CHUNK)
			tempo_inicial = 0.35		

			while len(data)>0 and self.vaiTocar:
				time.sleep(tempo_inicial)
				if len(self.clientes_conectados) > 0:
					for cliente in self.clientes_conectados:
						if cliente.ouvindo :
							cliente.ouvindo = False
							udp.sendto(serializar.pack(*info), cliente.getDestino())
						udp.sendto(data, cliente.getDestino()) # --- enviando dados
				data = wavefile.readframes(CHUNK)
			if self.vaiTocar:
				print("\nEnviando musica %s novamente"%(self.nome_musica))
			"""
			if len(self.clientes_conectados) > 0:
				musica = announce(self.nome_musica)
				serializar = struct.Struct("ii{}s" .format(musica[1]))
				musica = serializar.pack(*musica)
				tam = "{}".format(len(self.nome_musica)).encode()
				for i in self.clientes_conectados:
					i.getConexao().send(tam)
					time.sleep(0.1)
					i.getConexao().send(musica)
			"""
	def addCliente(self, cliente):
		self.clientes_conectados.append(cliente)

	def removeCliente(self, cliente):
		self.clientes_conectados.remove(cliente)
	
	def verificarConectados(self, cliente):
		for i in self.clientes_conectados:
			if id(i) == id(cliente):
				return True			
		return False

	def parar(self):
		self.vaiTocar = False


def welcome(numStation: int):
	return [socket.htons(0), socket.htons(numStation)]

def announce(songname):
	return [socket.htons(1), len(songname), songname.encode()]

def iniciar_musicas(arquivo):
	with open(arquivo) as file:
		for line in file:
			if line == '' or line == ' ' or line == '\n':
				pass
			else:
				lista_musicas.append(line[:-1])
				thread = Estacao(line[:-1])
				thread.start()
				threads_musicas.append(thread)

def mostrar_clientes_por_estacao():
	for i in threads_musicas:
		print("\nNome da estacao: ", i.nome_musica)
		for j in i.clientes_conectados:
			print("                ",j.cliente)

global threads_musicas, threads_clientes, lista_musicas
global udp, destino
threads_musicas = []
threads_clientes = []
lista_musicas = []


class Servidor(threading.Thread):
	def __init__(self, host, porta):
		self.host = host
		self.porta = porta
		self.parar = True
		self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		threading.Thread.__init__(self)

	def run(self):
		origem = (self.host, self.porta)		
		self.tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.tcp.bind(origem)
		self.tcp.listen(5) # --- OUVINDO
		try:
			while self.parar:
				con, cliente = self.tcp.accept()
				client = clientes(con, cliente, threading.Lock())
				client.start()
				threads_clientes.append(client)	
				print("\nCliente conectado e adicionado a lista ", cliente)			
		except:
			pass

	def pare(self):
		try:
			self.tcp.shutdown(0)
		except:
			self.tcp.close()			


if __name__ == '__main__':

	argumentos = sys.argv[1:]
	iniciar_musicas(argumentos[2])
	server = Servidor(argumentos[0], int(argumentos[1]))
	server.start()
	while True:
		entrada = input("\nq seguido de enter para sair\np seguido de enter para mostrar clientes\n")
		if entrada == 'p':
			mostrar_clientes_por_estacao()
		elif entrada == 'q':
			for i in threads_musicas:
				i.parar()				
			for i in threads_clientes:
				i.parar()				
			server.pare()
			
			break