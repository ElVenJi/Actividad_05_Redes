import sys
import socket

# =============================================================================
# Script de envío línea a línea (versión TTL, header de 7 bytes)
#
# Lee el archivo archivo_test.txt, arma un paquete por cada línea con el header
# IP(4) + puerto(2) + TTL(1) + mensaje, y lo envía por UDP al primer router.
#
# Uso:
#     python3 test_router.py "IP_destino;puerto_destino;TTL" IP_router_inicial puerto_router_inicial
#     Ejemplo: python3 test_router.py "127.0.0.1;8885;10" 127.0.0.1 8881
# =============================================================================

def main():
    # Valida la cantidad de argumentos: headers, IP inicial y puerto inicial
    if len(sys.argv) != 4:
        print("Uso: python3 test_router.py headers IP_router_inicial puerto_router_inicial")
        sys.exit(1)

    # El primer argumento trae destino y TTL separados por ';'
    ip_dest, port_dest, ttl = sys.argv[1].split(";")
    # Primer salto: dónde se envían los paquetes (no es el destino final)
    first_ip = sys.argv[2]
    first_port = int(sys.argv[3])

    # Codifica cada campo del header en bytes
    ip_bytes = bytes(int(p) for p in ip_dest.split("."))  # 4 bytes, uno por octeto
    port_bytes = int(port_dest).to_bytes(2, byteorder="big")  # 2 bytes
    ttl_byte = bytes([int(ttl)])  # 1 byte

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Lee el archivo línea por línea; cada línea es un paquete independiente
    with open("archivo_test.txt", "r", encoding="utf-8") as f:
        for line in f:
            # Quita solo el salto de línea final; el resto es el mensaje
            msg = line.rstrip("\n").encode("utf-8")
            if not msg:
                continue  # evita enviar paquetes sin mensaje (líneas vacías)
            # Concatena header y mensaje, y envía al primer router
            sock.sendto(ip_bytes + port_bytes + ttl_byte + msg, (first_ip, first_port))
    sock.close()
    print("Archivo enviado.")

if __name__ == "__main__":
    main()