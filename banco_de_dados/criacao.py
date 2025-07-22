import sqlite3

def criar_esquema_completo():
    """Cria todo o esquema do banco de dados com todas as tabelas e relacionamentos"""
    conexao = sqlite3.connect('monitoramento.db')
    cursor = conexao.cursor()
    
    # Tabela de ativos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ativos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        latitude TEXT,
        longitude TEXT
    )
    ''')
    
    # Tabela de câmeras
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cameras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        latitude TEXT,
        longitude TEXT
    )
    ''')
    
    # Tabela de junção para relação NxN entre ativos e câmeras
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ativos_cameras (
        ativo_id INTEGER,
        camera_id INTEGER,
        PRIMARY KEY (ativo_id, camera_id),
        FOREIGN KEY (ativo_id) REFERENCES ativos(id) ON DELETE CASCADE,
        FOREIGN KEY (camera_id) REFERENCES cameras(id) ON DELETE CASCADE
    )
    ''')
    
    # Tabela de buzzers com relação 1-1 com ativos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS buzzers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        latitude TEXT NOT NULL,
        longitude TEXT NOT NULL,
        ativo_id INTEGER UNIQUE,
        FOREIGN KEY (ativo_id) REFERENCES ativos(id) ON DELETE SET NULL
    )
    ''')
    
    conexao.commit()
    conexao.close()
    print("Esquema completo criado com sucesso!")

# Funções para manipulação de ativos
def inserir_ativo(nome, latitude, longitude):
    conexao = sqlite3.connect('monitoramento.db')
    cursor = conexao.cursor()
    
    cursor.execute('''
    INSERT INTO ativos (nome, latitude, longitude)
    VALUES (?, ?, ?)
    ''', (nome, str(latitude), str(longitude)))
    
    conexao.commit()
    conexao.close()
    print("Ativo inserido com sucesso!")

# Funções para manipulação de câmeras
def inserir_camera(nome, latitude, longitude):
    conexao = sqlite3.connect('monitoramento.db')
    cursor = conexao.cursor()
    
    cursor.execute('''
    INSERT INTO cameras (nome, latitude, longitude)
    VALUES (?, ?, ?)
    ''', (nome, str(latitude), str(longitude)))
    
    conexao.commit()
    conexao.close()
    print("Câmera inserida com sucesso!")

def associar_camera_ativo(ativo_id, camera_id):
    conexao = sqlite3.connect('monitoramento.db')
    cursor = conexao.cursor()
    
    cursor.execute('''
    INSERT INTO ativos_cameras (ativo_id, camera_id)
    VALUES (?, ?)
    ''', (ativo_id, camera_id))
    
    conexao.commit()
    conexao.close()
    print("Associação câmera-ativo criada com sucesso!")

# Funções para manipulação de buzzers
def inserir_buzzer(latitude, longitude, ativo_id=None):
    conexao = sqlite3.connect('monitoramento.db')
    cursor = conexao.cursor()
    
    cursor.execute('''
    INSERT INTO buzzers (latitude, longitude, ativo_id)
    VALUES (?, ?, ?)
    ''', (str(latitude), str(longitude), ativo_id))
    
    conexao.commit()
    conexao.close()
    print("Buzzer inserido com sucesso!")

def vincular_buzzer_ativo(buzzer_id, ativo_id):
    conexao = sqlite3.connect('monitoramento.db')
    cursor = conexao.cursor()
    
    # Remove qualquer vínculo existente deste ativo
    cursor.execute('UPDATE buzzers SET ativo_id = NULL WHERE ativo_id = ?', (ativo_id,))
    
    # Cria o novo vínculo
    cursor.execute('UPDATE buzzers SET ativo_id = ? WHERE id = ?', (ativo_id, buzzer_id))
    
    conexao.commit()
    conexao.close()
    print(f"Buzzer {buzzer_id} vinculado ao ativo {ativo_id} com sucesso!")

# Funções de consulta
def listar_ativos_com_dispositivos():
    conexao = sqlite3.connect('monitoramento.db')
    cursor = conexao.cursor()
    
    print("\n=== Ativos com seus Dispositivos ===")
    cursor.execute('SELECT id, nome FROM ativos')
    ativos = cursor.fetchall()
    
    for ativo in ativos:
        ativo_id, nome = ativo
        print(f"\nAtivo: {nome} (ID: {ativo_id})")
        
        # Busca câmeras associadas
        cursor.execute('''
        SELECT c.id, c.nome 
        FROM cameras c
        JOIN ativos_cameras ac ON c.id = ac.camera_id
        WHERE ac.ativo_id = ?
        ''', (ativo_id,))
        cameras = cursor.fetchall()
        
        if cameras:
            print("  Câmeras:")
            for cam in cameras:
                print(f"    - {cam[1]} (ID: {cam[0]})")
        
        # Busca buzzer associado
        cursor.execute('SELECT id FROM buzzers WHERE ativo_id = ?', (ativo_id,))
        buzzer = cursor.fetchone()
        
        if buzzer:
            print(f"  Buzzer: (ID: {buzzer[0]})")
    
    conexao.close()

def listar_buzzers_com_ativos():
    """
    Retorna um dicionário com os buzzers cadastrados e suas informações de ativos associados.
    Formato de retorno:
    {
        buzzer_id: {
            "ativo_nome": nome_do_ativo,
            "latitude": float(latitude_do_ativo),
            "longitude": float(longitude_do_ativo)
        },
        ...
    }
    """
    conexao = sqlite3.connect('monitoramento.db')
    cursor = conexao.cursor()
    
    # Consulta para obter buzzers com seus ativos associados
    cursor.execute('''
    SELECT 
        b.id,
        a.nome,
        a.latitude,
        a.longitude
    FROM 
        buzzers b
    LEFT JOIN 
        ativos a ON b.ativo_id = a.id
    WHERE 
        b.ativo_id IS NOT NULL
    ''')
    
    buzzers = cursor.fetchall()
    conexao.close()
    
    # Formatando o resultado como dicionário
    resultado = {}
    for buzzer in buzzers:
        buzzer_id, ativo_nome, lat, long = buzzer
        resultado[buzzer_id] = {
            "nome": ativo_nome,
            "lat": float(lat) if lat else None,
            "lon": float(long) if long else None,
            "id": buzzer_id
        }
    
    return list(resultado.values())

if __name__ == "__main__":
    # Criar todas as tabelas
    '''
    criar_esquema_completo()
    
    # Exemplos de uso:
    print("\n=== Inserindo dados de exemplo ===")
    
    # Inserir ativos
    inserir_ativo("EMAP", "-2.578183", "-44.36666")
    inserir_ativo("Granel Química", "-2.573947", "-44.3655073")
    inserir_ativo("Terminal de Cobre", "-2.570986", "-44.365199")
    
    # Inserir câmeras
    inserir_camera("Cam EMAP", "-2.578183", "-44.36666")
    inserir_camera("Cam Granel Química", "-2.573947", "-44.3655073")
    inserir_camera("Cam Terminal de Cobre", "-2.570986", "-44.365199")
    
    # Associar câmeras a ativos
    associar_camera_ativo(1, 1)  # Torre Principal + Cam Entrada
    associar_camera_ativo(1, 3)  # Torre Principal + Cam Segurança
    associar_camera_ativo(2, 2)  # Galpão A + Cam Estacionamento
    
    # Inserir buzzers
    inserir_buzzer("-2.578183", "-44.36666")
    inserir_buzzer("-2.573947", "-44.3655073")
    inserir_buzzer("-2.570986", "-44.365199")
    
    # Vincular buzzers a ativos
    vincular_buzzer_ativo(1, 1)  # Buzzer 1 na Torre Principal
    vincular_buzzer_ativo(2, 2)  # Buzzer 2 no Galpão A
    vincular_buzzer_ativo(3, 3)  # Buzzer 2 no Galpão A
    # Listar todos os ativos com seus dispositivos
    '''
    print(listar_buzzers_com_ativos())