import sys
import socket

def parse_packet(IP_packet: bytes) -> dict:
    """Header de 7 bytes: IP(4) + puerto(2) + TTL(1) + mensaje."""
    dest_ip = ".".join(str(b) for b in IP_packet[0:4])
    dest_port = int.from_bytes(IP_packet[4:6], byteorder="big")
    ttl = IP_packet[6]
    message = IP_packet[7:].decode("utf-8")
    return {"ip": dest_ip, "port": dest_port, "ttl": ttl, "msg": message}

def create_packet(parsed_IP_packet: dict) -> bytes:
    """Reconstruye los bytes del paquete a partir del diccionario."""
    ip_bytes = bytes(int(p) for p in parsed_IP_packet["ip"].split("."))
    port_bytes = parsed_IP_packet["port"].to_bytes(2, byteorder="big")
    ttl_byte = bytes([parsed_IP_packet["ttl"]])
    msg_bytes = parsed_IP_packet["msg"].encode("utf-8")
    return ip_bytes + port_bytes + ttl_byte + msg_bytes

def check_routes(routes_file_name: str, destination_address: tuple, rr_state: dict):
    """
    Busca todas las rutas que cubren el destino y devuelve la siguiente
    según round-robin. Devuelve (next_hop_ip, next_hop_port) o None.
    """
    dest_ip, dest_port = destination_address
    matching_routes = []
    try:
        with open(routes_file_name, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) < 5:
                    continue
                net_cidr = parts[0]
                port_ini, port_fin = int(parts[1]), int(parts[2])
                next_hop = (parts[3], int(parts[4]))
                network_ip = net_cidr.split("/")[0]
                if dest_ip == network_ip and port_ini <= dest_port <= port_fin:
                    matching_routes.append(((net_cidr, port_ini, port_fin), next_hop))
    except FileNotFoundError:
        print(f"[ERROR] No se encontró el archivo de rutas: {routes_file_name}")
        return None

    if not matching_routes:
        return None

    # Round-robin por regla: se guarda el índice por cada área (net, port_ini, port_fin)
    area_key = matching_routes[0][0]
    candidates = [hop for area, hop in matching_routes if area == area_key]
    idx = rr_state.get(area_key, 0) % len(candidates)
    rr_state[area_key] = (idx + 1) % len(candidates)
    return candidates[idx]

def main():
    if len(sys.argv) != 4:
        print("Uso correcto: python3 router.py router_IP router_puerto router_rutas.txt")
        sys.exit(1)

    router_ip = sys.argv[1]
    router_port = int(sys.argv[2])
    routes_file = sys.argv[3]

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((router_ip, router_port))
    print(f"[LISTENING] {router_ip}:{router_port} (rutas: {routes_file})\n")

    current = (router_ip, router_port)
    rr_state = {}

    try:
        while True:
            packet_bytes, _ = sock.recvfrom(4096)
            parsed = parse_packet(packet_bytes)
            dest = (parsed["ip"], parsed["port"])

            if dest == current:
                print(parsed["msg"])
                continue

            if parsed["ttl"] <= 0:
                print(f"Se recibió paquete {packet_bytes} con TTL 0")
                continue

            next_hop = check_routes(routes_file, dest, rr_state)
            if next_hop is None:
                print(f"No hay rutas hacia {dest} para paquete {packet_bytes}")
                continue

            parsed["ttl"] -= 1
            new_packet = create_packet(parsed)
            print(f"redirigiendo paquete {new_packet} con destino final {dest} desde {current} hacia {next_hop}")
            sock.sendto(new_packet, next_hop)
    except KeyboardInterrupt:
        print("\n[EXIT] Deteniendo router...")
        sock.close()

if __name__ == "__main__":
    main()