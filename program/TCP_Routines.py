import __main__
if __name__ == "__main__":
	__main__.logfilename = "TCP_Server.log"
	__main__.backupcount = 2
import os
import sys
from Config import DBFILE, TCPPORT, TCPHOST, MAX_EXTERNAL_CONN, DB_RETRIES, DB_WAITBETWEENRETRIES
import Common_Data
from Common_Routines import get_ip_address
from LogRoutines import Logger
import threading
import time
import socket
import sqlite3
import pickle

import pandas as pd
import numpy as np
import time
import select
import errno

'''
Het doel van dit programma is om in een aparte thread naar een TCP verbinding te luisteren
Wanneer deze verbinding tot stand komt dan wordt er geluisterd naar SQL commandos

To start the TCP server and start listening for TCP connections implement the following code snippet..

	# Start the TCP SQL server to enable remote access to the database
	# Now first retrieve some network addresses....
	found_address='127.0.0.1'
	found_tcpport=65432 if TCPPORT == 0 else TCPPORT
	if TCPHOST=='':
		try:
			found_address = get_ip_address()
		except:
			Logger.error ("Can't retrieve IP address and none given in config.py file, using localhost 127.0.0.1....")
	else:
		found_address = TCPHOST

	if MAX_EXTERNAL_CONN > 0:
		# Here I start a parallel thread that executes the TCP server
		t = threading.Thread(target=TCPServer, kwargs=dict(host=found_address, port=found_tcpport, max_connections=MAX_EXTERNAL_CONN))
		t.daemon = False
		t.start()
		Logger.info("TCP-SQL Server proces started on address: %s, port: %s" % (found_address, found_tcpport))

'''
HOST = '192.168.178.220'	# The server's hostname or IP address
PORT = 65432				# The port used by the server
max_connections=2

Conn_Counter = 0

stats_dict = {'query':['unknown'], 'duration_ms':[-1], 'status':['direct_failed'], 'error_message':['']}

def TCP_Handler(r_sock, r_addr):
	global Conn_Counter
	CONN = None
	result_df = pd.DataFrame()
	stats_df = pd.DataFrame(stats_dict)
	try:
		# check if the DBstore_engine exists and is running.....
		store_direct = (Common_Data.DB_STORE is None) or (Common_Data.DB_STORE.thrd is None) or (Common_Data.DB_STORE.keeprunning is False)

		Logger.info('Connected to %s, now %s active connections...' % (r_addr,Conn_Counter))
		with r_sock:
			r_sock.setblocking(0)
			# a non blocking socket does not wait for data.. so we need an event when data is present
			ready_to_read_sockets, _, _ = select.select([r_sock], [], [])
			# wait until sockets indicates data is present
			while r_sock not in ready_to_read_sockets: pass
			data=b''
			while True:
				try:
					data += r_sock.recv(1024)
				except socket.error as e:
					if e.errno != errno.EWOULDBLOCK:
						Logger.error(str(e))
					else:
						break

			if not data: return
			start_time = time.time()
			query = data.decode('utf-8')
			Logger.debug ('Query received: %s' % query)
			stats_df.at[0,'query'] = query
			for teller in range(DB_RETRIES):
				try:
					if query.upper().startswith("SELECT"):
						CONN=sqlite3.connect(DBFILE, uri=True)
						result_df = pd.read_sql_query(query, CONN)
						stats_df.at[0,'status'] = 'direct_success'
						break

					elif query.upper().startswith("INSERT"):
						if not store_direct:
							Logger.debug('Query added to the DB_STORE queue...')
							Common_Data.DB_STORE.add_query(query)
							stats_df.at[0,'status'] = 'queue'
						else:
							Logger.debug('Query executed immediately...')
							CONN=sqlite3.connect(DBFILE)
							CONN.execute(query)
							CONN.commit()
							# Logger.debug('Query executed: %s' % query)
							stats_df.at[0,'status'] = 'direct_success'
							break
					else:
						# nog implementeren UPDATE, DELETE etc.
						stats_df.at[0,'error_message'] = 'not implemented'
						break

				except Exception as err:
					Logger.warning(str(err) + ", query failed...., attempt " + str(teller+1))
					if CONN is not None: CONN.close()
					if (teller + 1) == DB_RETRIES:
						stats_df.at[0,'error_message'] = str(err) + ', max retries exceeded'
						Logger.error (str(err) + ', max retries exceeded')
						break
					else:
						time.sleep(DB_WAITBETWEENRETRIES)

			stats_df.at[0,'duration_ms'] = int((time.time() - start_time)*1000)
			# for sending we switch back to blocking socket
			r_sock.setblocking(1)
			# create a tuple to pickle and send
			sendbytes = pickle.dumps((result_df, stats_df))
			r_sock.sendall(sendbytes)
	except Exception as err:
		Logger.exception(str(err))
	finally:
		r_sock.close()
		if CONN is not None: CONN.close()
		Conn_Counter = Conn_Counter - 1

def TCPServer(host='127.0.0.1', port=65432, max_connections=2):
	'''
	This routine continuously listens on the host IP adres, port for a n incoming connection request.
	It will refuse any connection above the max_connections number.
	When the connection is accepted it fires a handler to handle an incoming SQL query on that connection.
	The handler routine will close the connection when the query is handled...
	'''
	global Conn_Counter
	try:
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			Logger.info ("TCP-SQL Server listening on: %s, on port: %s" % (host,port))
			s.bind((host, port))
			while True:
				s.listen()
				conn, addr = s.accept()
				if Conn_Counter >= max_connections:
					Logger.debug('Connection attempt from %s, connection refused...' % addr[0])
					conn.shutdown(socket.SHUT_RDWR)
					conn.close()
				else:
					Conn_Counter +=1
					t = threading.Thread(target=TCP_Handler, kwargs=dict(r_sock=conn, r_addr=addr))
					t.daemon = True
					t.start()
	except Exception as err:
		Logger.exception(err)
	finally:
		pass

def TestServer(*args, **kwargs):
	print(
'''
=================== TCP - SQL Server ============================================================
TCP-SQL Server facilitates a direct connection to the JSEM database on the operational JSEM machine.
Enter the correct IP address and port (HOST and PORT) and the max allowed connections
The server will start listening on that address/port and wait for incoming SQL requests
''')

	# Here I start a parallel thread that executes the TCP server
	t = threading.Thread(target=TCPServer, kwargs=dict(host=HOST, port=PORT, max_connections=max_connections))
	t.daemon = False
	t.start()
	Logger.info("TCP-SQL Server proces started on address: %s, port: %s" % (HOST, PORT))



def tcp_sql_query(query=None, host=HOST, port=PORT):
	# print ('Receiving query in tcp_sql_client:')
	# print (query)
	result = None
	stats = None
	while True:
		try:
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
				# the client runs the socket in blocking mode
				s.connect((host, port))

				sendbytes = query.encode('utf-8')
				# print('Bytesstream to send:')
				# print(sendbytes)
				s.sendall(sendbytes)
				# print('Bytesstream is send...')

				# first get the result of the query in a dataframe (None for INSERT or UPDATE queries)
				data = b""
				while True:
					packet = s.recv(4096)
					if not packet: break
					data += packet
				# print('Answer received from TCP-SQL host....')
				# print(data)
				result, stats = pickle.loads(data)
				break
				# print(stats)
		except Exception as err:
			print(str(err))

	return result, stats



test_query = "insert into 'Values' (datapointID,timestamp,value) values (334,1690322400,8.967151641845703),(334,1690326000,8.844771385192871),(334,1690329600,8.577960968017578),(334,1690333200,8.095672607421875),(334,1690336800,8.413169860839844),(334,1690340400,8.779047012329102),(334,1690344000,9.755335807800293),(334,1690347600,11.193509101867676),(334,1690351200,11.508744239807129),(334,1690354800,10.396058082580566),(334,1690358400,10.025674819946289),(334,1690362000,9.351410865783691),(334,1690365600,8.785594940185547),(334,1690369200,7.879150867462158),(334,1690372800,7.270354747772217),(334,1690376400,5.656667232513428),(334,1690380000,6.147604465484619),(334,1690383600,7.5605621337890625),(334,1690387200,9.553057670593262),(334,1690390800,11.238004684448242),(334,1690394400,11.899806022644043),(334,1690398000,12.19567584991455),(334,1690401600,12.326273918151855),(334,1690405200,11.73877239227295),(334,1690408800,9.430020332336426),(334,1690412400,9.252610206604004),(334,1690416000,9.078627586364746),(334,1690419600,8.89873218536377),(334,1690423200,8.81740665435791),(334,1690426800,8.919526100158691),(334,1690430400,9.956007957458496),(334,1690434000,11.306042671203613),(334,1690437600,11.63072681427002),(334,1690441200,10.817971229553223),(334,1690444800,10.30075740814209),(334,1690448400,9.268004417419434),(334,1690452000,8.725865364074707),(334,1690455600,8.365662574768066),(334,1690459200,8.032435417175293),(334,1690462800,7.740065097808838),(334,1690466400,7.878742218017578),(334,1690470000,8.432975769042969),(334,1690473600,9.999932289123535),(334,1690477200,10.778388023376465),(334,1690480800,11.180560111999512),(334,1690484400,10.937712669372559),(334,1690488000,10.5303955078125),(334,1690491600,10.021197319030762),(334,1690495200,9.015260696411133),(334,1690498800,8.954768180847168),(334,1690502400,9.319783210754395),(334,1690506000,9.758745193481445),(334,1690509600,9.334035873413086),(334,1690513200,8.901105880737305),(334,1690516800,8.856051445007324),(334,1690520400,9.2481050491333),(334,1690524000,9.534760475158691),(334,1690527600,9.076910972595215),(334,1690531200,7.848467826843262),(334,1690534800,6.692702293395996),(334,1690538400,5.678885459899902),(334,1690542000,5.458362579345703),(334,1690545600,5.144841194152832),(334,1690549200,6.100715160369873),(334,1690552800,6.404677867889404),(334,1690556400,7.955542087554932),(334,1690560000,9.232596397399902),(334,1690563600,10.56653118133545),(334,1690567200,11.143351554870605),(334,1690570800,10.606319427490234),(334,1690574400,11.641196250915527),(334,1690578000,11.264084815979004),(334,1690581600,9.883033752441406),(334,1690585200,9.776528358459473),(334,1690588800,10.404887199401855),(334,1690592400,9.640438079833984),(334,1690596000,9.035439491271973),(334,1690599600,8.529646873474121),(334,1690603200,7.970392227172852),(334,1690606800,8.820677757263184),(334,1690610400,9.0730562210083),(334,1690614000,8.968253135681152),(334,1690617600,8.737664222717285),(334,1690621200,8.234332084655762),(334,1690624800,7.55165958404541),(334,1690628400,5.522337913513184),(334,1690632000,6.519430637359619),(334,1690635600,7.013383865356445),(334,1690639200,7.430377006530762),(334,1690642800,8.224967002868652),(334,1690646400,9.166733741760254),(334,1690650000,10.340649604797363),(334,1690653600,9.967229843139648),(334,1690657200,10.68681812286377),(334,1690660800,10.99312686920166),(334,1690664400,10.925804138183594),(334,1690668000,10.708840370178223),(334,1690671600,10.174229621887207),(334,1690675200,8.464624404907227),(334,1690686000,3.3419883251190186),(334,1690696800,2.9524781703948975),(334,1690707600,2.268768310546875),(334,1690718400,2.0290071964263916),(334,1690729200,4.883273124694824),(334,1690740000,10.020977973937988),(334,1690750800,10.144660949707031),(334,1690761600,7.956318378448486),(334,1690772400,7.951809883117676),(334,1690783200,9.14011287689209),(334,1690794000,7.132083892822266),(334,1690804800,3.8831984996795654),(334,1690815600,6.975003242492676),(334,1690826400,13.389510154724121),(334,1690837200,10.837063789367676),(334,1690848000,8.542177200317383),(334,1690858800,8.921647071838379),(334,1690869600,9.954079627990723),(334,1690880400,9.968026161193848),(334,1690891200,6.493528366088867),(334,1690902000,8.113103866577148),(334,1690912800,13.424555778503418),(334,1690923600,12.626696586608887),(334,1690934400,8.49398136138916),(334,1690945200,7.9357194900512695),(334,1690956000,10.48256778717041),(334,1690966800,8.87952709197998),(334,1690977600,6.872481822967529),(334,1690988400,8.044431686401367),(334,1690999200,12.670117378234863),(334,1691010000,12.467852592468262),(334,1691020800,9.399397850036621),(334,1691031600,9.255227088928223),(334,1691042400,10.329257011413574),(334,1691053200,10.033548355102539),(334,1691064000,7.90476131439209),(334,1691074800,7.7380781173706055),(334,1691085600,12.161271095275879),(334,1691096400,12.472830772399902),(334,1691107200,9.965027809143066)"


def TestClient(*args, **kwargs):
	print(
'''
=================== TCP - SQL Client ============================================================
TCP-SQL client provides a direct connection to the JSEM database on the operational JSEM machine.
For now only SELECT statements are allowed and results are returned in a pandas dataframe object.

Enter a SELECT or INSERT query...or hit RETURN to transmit a test dataframe to update the database
''')
	try:
		import readline
		while True:
			# om de een of anderee reden truncate input een lange query.....snap niet waarom... de test_query kan bijvoorbeeld NIET via input
			# ingegeven worden....wel via een variabele (zie onder)
			query = input('TCP-SQL>')
			if query.lower()=='t': query = test_query
			# print ('Query received by input statement:')
			# print (query)
			# input ('Any key...')

			if not query:
				from Common_Routines import store_df_in_database
				test_df = {
								'table':["Values","Values","Values","Values","Values"],
								'datapointID' :[334,334,334,334,334],
								'timestamp':[1690297200,1690297200+3600,1690297200+2*3600,1690297200+3*3600,1690297200+4*3600],
								'value':[10.0,-10.0,10.0,-10.0,10.0]
								}
				df = pd.DataFrame(test_df)
				result, stats = store_df_in_database(df=df, use_remote_JSEM_DB=True)
				print(result)
			else:
				result, stats = tcp_sql_query(query=query, host=HOST, port=PORT)
				print(result)
			print(stats)

	except KeyboardInterrupt as e:
		print('tcp_sql_client terminated by user...')
	except EOFError as e:
		print('tcp_sql_client terminated by user...')


def main(*args, **kwargs):
	if input('Run SERVER (S) or CLIENT(C)(Default)? :').upper()=='S':
		TestServer()
	else:
		TestClient()


if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))

