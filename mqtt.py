import paho.mqtt.client as mqtt
import time
import json

class MosquittoLocalClient:
    def __init__(self, client_id=""):
        """
        Inicializa o cliente para Mosquitto local
        
        Args:
            client_id (str): ID do cliente (opcional)
        """
        # Configurações padrão para Mosquitto local
        self.broker = "localhost"  # Ou "127.0.0.1"
        self.port = 1883           # Porta padrão do Mosquitto
        self.keepalive = 60        # Keepalive em segundos
        
        self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = self._on_connect
        self.client.on_publish = self._on_publish
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback quando conecta ao broker"""
        if rc == 0:
            pass
            #print(f"Conectado ao Mosquitto em {self.broker}:{self.port}")
        else:
            print(f"Falha na conexão. Código: {rc}")

    def _on_publish(self, client, userdata, mid):
        """Callback quando publica mensagem"""
        print(f"Mensagem publicada (ID: {mid})")

    def connect(self):
        """Conecta ao broker Mosquitto local"""
        try:
            self.client.connect(self.broker, self.port, self.keepalive)
            self.client.loop_start()
            time.sleep(0.5)  # Pequena pausa para estabilizar
            return True
        except Exception as e:
            print(f"Erro ao conectar ao Mosquitto local: {e}")
            return False

    def disconnect(self):
        """Desconecta do broker"""
        self.client.loop_stop()
        self.client.disconnect()
        print("Desconectado do Mosquitto")

    def publicar(self, topico, mensagem, reter=False, qos=1):
        """
        Publica uma mensagem no tópico especificado
        
        Args:
            topico (str): Tópico MQTT
            mensagem (str/dict): Conteúdo da mensagem
            reter (bool): Se True, mensagem fica retida no broker
            qos (int): Qualidade de serviço (0, 1 ou 2)
        
        Returns:
            bool: True se publicado com sucesso
        """
        try:
            # Converte dicionário para JSON se necessário
            if isinstance(mensagem, dict):
                mensagem = json.dumps(mensagem, ensure_ascii=False)
            
            result = self.client.publish(topico, mensagem, qos=qos, retain=reter)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            print(f"Erro ao publicar: {e}")
            return False

    def sobrescrever(self, topico, mensagem, qos=1):
        """
        Sobrescreve uma mensagem (com retain=True)
        
        Args:
            topico (str): Tópico MQTT
            mensagem (str/dict): Conteúdo da mensagem
            qos (int): Qualidade de serviço (0, 1 ou 2)
        """
        return self.publicar(topico, mensagem, reter=True, qos=qos)


# Exemplo de uso com Mosquitto local
if __name__ == "__main__":
    # Cria o cliente
    cliente = MosquittoLocalClient("python_client")
    
    if not cliente.connect():
        exit("Não foi possível conectar ao Mosquitto local. Verifique se o broker está rodando.")
    
    try:
        # Tópico de exemplo
        TOPICO_TESTE = "casa/sala/temperatura"
        
        # Publica mensagem simples
        if cliente.publicar(TOPICO_TESTE, "22.5°C"):
            print("Mensagem publicada!")
        
        # Publica dados estruturados (como JSON)
        dados_sensor = {
            "valor": 22.5,
            "unidade": "Celsius",
            "local": "sala",
            "timestamp": time.time()
        }
        if cliente.publicar(TOPICO_TESTE, dados_sensor):
            print("Dados do sensor publicados!")
        
        # Sobrescreve a mensagem
        if cliente.sobrescrever(TOPICO_TESTE, {"status": "ativo", "temp": 23.0}):
            print("Mensagem sobrescrita com sucesso!")
        
        time.sleep(1)
        
    finally:
        cliente.disconnect()