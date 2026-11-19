import sys
import socket

# =============================================================================
# Router de la Actividad 5 (versión sin TTL, header de 6 bytes)
#
# Cada router escucha por UDP en un par (IP, puerto), recibe paquetes con
# header IP(4) + puerto(2) + mensaje, y decide si son para él o si deben
# reenviarse según su tabla de rutas.
#
# Uso:
#     python3 router.py router_IP router_puerto router_rutas.txt
#     Ejemplo: python3 router.py 127.0.0.1 8881 rutas_R1_v1.txt
# =============================================================================

def parse_packet(IP_packet: bytes):
    # Separa el paquete en sus campos por posición de bytes:
    # IP (bytes 0-3), puerto (bytes 4-5), mensaje (desde el byte 6).
    # El mensaje se decodifica a str, válido aquí porque no hay fragmentación.
    ip_bytes = IP_packet[0:4]
    dest_ip = ".".join(str(b) for b in ip_bytes)  # cada byte es un octeto
    dest_port = int.from_bytes(IP_packet[4:6], byteorder='big')
    message = IP_packet[6:].decode('utf-8')

    return {
        "ip": dest_ip,
        "port": dest_port,
        "msg": message
    }

def create_packet(parsed_IP_packet: dict) -> bytes:
    # Operación inversa de parse_packet: convierte el diccionario en bytes
    # listos para enviar por el socket.
    ip_parts = parsed_IP_packet["ip"].split(".")
    ip_bytes = bytes([int(part) for part in ip_parts])
    port_bytes = parsed_IP_packet["port"].to_bytes(2, byteorder='big')
    msg_bytes = parsed_IP_packet["msg"].encode('utf-8')

    return ip_bytes + port_bytes + msg_bytes

def check_routes(routes_file_name: str, destination_address: tuple[str, int], rr_state: dict) -> tuple[str, int]:
    # Lee la tabla de rutas y devuelve el siguiente salto para el destino.
    # Si varias reglas cubren el destino, alterna entre ellas con round-robin.
    # rr_state guarda el índice de la última ruta usada por área y debe
    # persistir mientras el router esté corriendo.
    """
    Recolecta todas las rutas válidas para el destino y alterna entre ellas usando Round-Robin
    de manera independiente por cada área de la red (net_cidr, port_ini, port_fin).
    """
    dest_ip, dest_port = destination_address
    matching_routes = []
    area_key = None

    try:
        with open(routes_file_name, 'r') as f:
            for line in f:
                line = line.strip()
                # Ignora líneas vacías y comentarios
                if not line or line.startswith('#'):
                    continue

                parts = line.split()
                if len(parts) < 5:
                    continue

                # Campos de la fila: red/máscara, rango de puertos, siguiente salto
                net_cidr = parts[0]
                port_ini = int(parts[1])
                port_fin = int(parts[2])
                next_hop_ip = parts[3]
                next_hop_port = int(parts[4])

                network_ip = net_cidr.split('/')[0]  # descarta la máscara

                if dest_ip == network_ip and port_ini <= dest_port <= port_fin:
                    current_area = (net_cidr, port_ini, port_fin)
                    # Se fija el área con la primera coincidencia y solo se
                    # agregan rutas de esa misma área, para no mezclar reglas.
                    if area_key is None:
                        area_key = current_area
                    if current_area == area_key:
                        matching_routes.append((next_hop_ip, next_hop_port))

    except FileNotFoundError:
        print(f"[ERROR] No se encontró el archivo de rutas: {routes_file_name}")
        return None

    if not matching_routes:
        return None

    # Índice de la próxima ruta para esta área (0 la primera vez)
    idx = rr_state.get(area_key, 0)
    # Módulo por seguridad, por si la tabla cambió de tamaño
    idx = idx % len(matching_routes)
    chosen_route = matching_routes[idx]

    # Avanza el turno en círculo para la siguiente llamada de esta área
    rr_state[area_key] = (idx + 1) % len(matching_routes)

    return chosen_route

def main():
    # Levanta el router en (IP, puerto) y procesa paquetes en un bucle.
    # Si el paquete es para este router, imprime el mensaje. Si no, consulta
    # la tabla y lo reenvía al siguiente salto, o lo descarta si no hay ruta.
    if len(sys.argv) != 4:
        print("Uso correcto: python3 router.py router_IP router_puerto router_rutas.txt")
        sys.exit(1)

    router_ip = sys.argv[1]
    router_port = int(sys.argv[2])
    routes_file = sys.argv[3]

    # Socket UDP (no orientado a conexión) enlazado a la dirección del router
    router_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    router_socket.bind((router_ip, router_port))
    print(f"[LISTENING] Router escuchando en {router_ip}:{router_port} (rutas: {routes_file})...\n")

    current_router_address = (router_ip, router_port)
    # Memoria del round-robin, por área de la red
    rr_state = {}

    try:
        while True:
            # Espera de forma bloqueante hasta recibir un paquete
            packet_bytes, addr = router_socket.recvfrom(4096)
            parsed = parse_packet(packet_bytes)
            destination_address = (parsed["ip"], parsed["port"])

            # Entrega local: el paquete es para este router
            if destination_address == current_router_address:
                print(parsed["msg"])
            else:
                # Reenvío: consulta la tabla para obtener el siguiente salto
                next_hop = check_routes(routes_file, destination_address, rr_state)

                if next_hop is not None:
                    print(f"redirigiendo paquete {packet_bytes} con destino final {destination_address} desde {current_router_address} hacia {next_hop}")
                    # Envía los bytes originales sin cambios (esta versión no tiene TTL)
                    router_socket.sendto(packet_bytes, next_hop)
                else:
                    print(f"No hay rutas hacia {destination_address} para paquete {packet_bytes}")

    except KeyboardInterrupt:
        print("\n[EXIT] Deteniendo router...")
        router_socket.close()

if __name__ == "__main__":
    main()