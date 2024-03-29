import _thread as thread
import socket
import concurrent.futures
import queue
import random
import time
import logging
import threading
import pickle


class Broker:
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 8080  # 1-65535
        self.clients = {}
        self.queue = []
        self.count = 0
        self._lock = threading.Lock()
        

    def sendMessageToClients(self, s):
        print(self.queue)
        with self._lock:  # Lock queue.
            for client_name in self.clients:  # Manda a queue para todos os clientes.
                print('enviando para: ', end='')
                print(self.clients[client_name]['host'], self.clients[client_name]['port'])
                s.connect((self.clients[client_name]['host'], self.clients[client_name]['port']))                
                print('conectado!')
                retorno = pickle.dumps(self.queue)
                s.sendall(retorno)
    
    def resolveMsg(self, msg, conn, addr, s):
        print('Resolvendo cliente...')
        
        with self._lock:
            self.count += 1
        msg = pickle.loads(msg)
        print('%3s. %s' % (self.count, msg))  # Esta mensagem pode estar fora de sincronia.
        
        msg = msg.split() # Ex.: ['Débora', '-acquire', '-var-X', '127.0.0.1', '8080']
        _id = msg[0]  # Nome do cliente.
        
        if msg[1] == 'exited':
            self.clients.pop(_id)
            try:
                self.queue.remove(_id)
            except ValueError:
                pass            
            return
        
        self.clients[_id] = {'host': msg[-2], 'port': int(msg[-1])}  # 'id': [host, port]        
        action = msg[1]
        
        if action == '-acquire':
            self.queue.append(_id)  # Põe o nome do cliente no fim da lista.            
            self.sendMessageToClients(s)
                
        elif action == '-release':
            if self.queue[0] == _id:  # -> Quem ta dando -release é quem está com o recurso?
                self.queue.pop(0)
                self.sendMessageToClients(s)
            else:
                print('ERRO CABULOSO! Requerente: %s | Fila: %s' % (_id, self.queue[0]))
    
    def dealtWithClient(self, conn, addr, s):
        with conn:
            print('Connected by ', addr)
            data = conn.recv(4096)  # Recebe a mensagem do cliente.
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                executor.submit(self.resolveMsg, data, conn, addr, s)  # Lança a thread para o cliente.

    def start(self):
        portInput = input("Enter the Broker port number: ")
        self.port = 8080 if portInput == "" else int(portInput)
        print("Default port number selected: " + str(self.port)) if portInput == "" else {}
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            
            s.listen()
            print("Listening...", end="\n\n")
            
            while True:
                try:
                    print('Esperando contato...')
                    conn, addr = s.accept()
                    self.dealtWithClient(conn, addr, s)
                        
                except KeyboardInterrupt:
                    print('Exiting.')
                    break


broker = Broker()
broker.start()
