import sys
import socket

def parse_packet(IP_packet: bytes):
    ip_bytes = IP_packet[0:4]
    dest_ip = ".".join(str(b) for b in ip_bytes)
    dest_port = int.from_bytes(IP_packet[4:6], byteorder='big')
    message = IP_packet[6:].decode('utf-8')
    
    return {
        "ip": dest_ip,
        "port": dest_port,
        "msg": message
    }

def create_packet(parsed_IP_packet: dict) -> bytes:
    ip_parts = parsed_IP_packet["ip"].split(".")
    ip_bytes = bytes([int(part) for part in ip_parts])
    port_bytes = parsed_IP_packet["port"].to_bytes(2, byteorder='big')
    msg_bytes = parsed_IP_packet["msg"].encode('utf-8')
    
    return ip_bytes + port_bytes + msg_bytes

def check_routes(routes_file_name: str, destination_address: tuple[str, int], rr_state: dict) -> tuple[str, int]:
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
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                if len(parts) < 5:
                    continue
                
                net_cidr = parts[0]
                port_ini = int(parts[1])
                port_fin = int(parts[2])
                next_hop_ip = parts[3]
                next_hop_port = int(parts[4])
                
                network_ip = net_cidr.split('/')[0]
                
                if dest_ip == network_ip and port_ini <= dest_port <= port_fin:
                    current_area = (net_cidr, port_ini, port_fin)
                    # Si ya recolectamos rutas de una regla más específica arriba (ej. antes del default),
                    # evitamos mezclarla con reglas más generales de abajo.
                    if area_key is None:
                        area_key = current_area
                    if current_area == area_key:
                        matching_routes.append((next_hop_ip, next_hop_port))
                    
    except FileNotFoundError:
        print(f"[ERROR] No se encontró el archivo de rutas: {routes_file_name}")
        return None

    if not matching_routes:
        return None

    # Obtenemos el índice actual para esta área (0 si es la primera vez)
    idx = rr_state.get(area_key, 0)
    # Por seguridad, aplicamos módulo por si la tabla cambió de tamaño
    idx = idx % len(matching_routes)
    chosen_route = matching_routes[idx]
    
    # Avanzamos el turno en círculo (Round-Robin) para esta área
    rr_state[area_key] = (idx + 1) % len(matching_routes)
    
    return chosen_route

def main():
    if len(sys.argv) != 4:
        print("Uso correcto: python3 router.py router_IP router_puerto router_rutas.txt")
        sys.exit(1)

    router_ip = sys.argv[1]
    router_port = int(sys.argv[2])
    routes_file = sys.argv[3]

    router_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    router_socket.bind((router_ip, router_port))
    print(f"[LISTENING] Router escuchando en {router_ip}:{router_port} (rutas: {routes_file})...\n")

    current_router_address = (router_ip, router_port)
    # Estructura de memoria para mantener el estado de Round-Robin por área
    rr_state = {}

    try:
        while True:
            packet_bytes, addr = router_socket.recvfrom(4096)
            parsed = parse_packet(packet_bytes)
            destination_address = (parsed["ip"], parsed["port"])
            
            if destination_address == current_router_address:
                print(parsed["msg"])
            else:
                next_hop = check_routes(routes_file, destination_address, rr_state)
                
                if next_hop is not None:
                    print(f"redirigiendo paquete {packet_bytes} con destino final {destination_address} desde {current_router_address} hacia {next_hop}")
                    router_socket.sendto(packet_bytes, next_hop)
                else:
                    print(f"No hay rutas hacia {destination_address} para paquete {packet_bytes}")
            
    except KeyboardInterrupt:
        print("\n[EXIT] Deteniendo router...")
        router_socket.close()

if __name__ == "__main__":
    main()