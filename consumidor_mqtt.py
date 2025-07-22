import paho.mqtt.client as mqtt
import json

class ConsumidorMQTT:
    def __init__(self, client_id="consumidor_python"):
        """
        Inicializa o consumidor MQTT para Mosquitto local
        
        Args:
            client_id (str): ID do cliente (opcional)
        """
        self.broker = "localhost"
        self.port = 1883
        self.client = mqtt.Client(client_id=client_id)
        
        # Configura callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_subscribe = self._on_subscribe
        
        # Dicionário para armazenar as últimas mensagens por tópico
        self.ultimas_mensagens = {}
        
    def _on_connect(self, client, userdata, flags, rc):
        """Callback quando conecta ao broker"""
        if rc == 0:
            print(f"Conectado ao broker Mosquitto em {self.broker}:{self.port}")
        else:
            print(f"Falha na conexão. Código: {rc}")

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback quando se inscreve em um tópico"""
        print(f"Inscrito no tópico (ID: {mid}, QoS: {granted_qos[0]})")

    def _on_message(self, client, userdata, msg):
        """Callback quando recebe uma mensagem"""
        try:
            # Tenta decodificar JSON, se não for possível, usa o payload direto
            try:
                payload = json.loads(msg.payload.decode())
            except json.JSONDecodeError:
                payload = msg.payload.decode()
            
            print(f"\nNova mensagem recebida:")
            print(f"Tópico: {msg.topic}")
            print(f"QoS: {msg.qos}")
            print(f"Payload: {payload}")
            
            # Armazena a última mensagem recebida para cada tópico
            self.ultimas_mensagens[msg.topic] = {
                'payload': payload,
                'qos': msg.qos,
                'retain': msg.retain,
                'timestamp': time.time()
            }
            
        except Exception as e:
            print(f"Erro ao processar mensagem: {e}")

    def conectar(self):
        """Conecta ao broker e inicia o loop"""
        try:
            self.client.connect(self.broker, self.port)
            self.client.loop_start()
            time.sleep(1)  # Pausa para estabilizar conexão
            return True
        except Exception as e:
            print(f"Erro ao conectar: {e}")
            return False

    def inscrever(self, topico, qos=1):
        """
        Inscreve-se em um tópico específico
        
        Args:
            topico (str): Tópico para se inscrever
            qos (int): Qualidade de serviço desejada
        """
        result, mid = self.client.subscribe(topico, qos=qos)
        if result == mqtt.MQTT_ERR_SUCCESS:
            print(f"Solicitada inscrição no tópico: {topico} (QoS: {qos})")
        else:
            print(f"Falha ao se inscrever no tópico {topico}")

    def desconectar(self):
        """Desconecta do broker"""
        self.client.loop_stop()
        self.client.disconnect()
        print("Desconectado do broker MQTT")

    def obter_ultima_mensagem(self, topico):
        """
        Retorna a última mensagem recebida de um tópico específico
        
        Args:
            topico (str): Tópico desejado
        
        Returns:
            dict/None: Dados da mensagem ou None se não houver mensagens
        """
        return self.ultimas_mensagens.get(topico)


# Exemplo de uso do consumidor
if __name__ == "__main__":
    import time
    
    # Cria o consumidor
    consumidor = ConsumidorMQTT()
    
    if not consumidor.conectar():
        exit("Não foi possível conectar ao Mosquitto local")
    
    try:
        # Tópico para assinar (deve ser o mesmo usado pelo publicador)
        TOPICO = "ativos/Terminal de Cobre"
        
        # Inscreve-se no tópico
        consumidor.inscrever(TOPICO)
        
        print(f"Monitorando tópico: {TOPICO}")
        print("Pressione Ctrl+C para parar...")
        
        # Mantém o consumidor ativo
        while True:
            # Mostra a última mensagem a cada 5 segundos
            ultima = consumidor.obter_ultima_mensagem(TOPICO)
            if ultima:
                print(f"\nÚltima mensagem em {time.ctime(ultima['timestamp'])}:")
                print(ultima['payload'])
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nEncerrando consumidor...")
    finally:
        consumidor.desconectar()