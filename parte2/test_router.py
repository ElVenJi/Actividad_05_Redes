import sys
import socket

def main():
    if len(sys.argv) != 4:
        print("Uso: python3 test_router.py headers IP_router_inicial puerto_router_inicial")
        sys.exit(1)

    ip_dest, port_dest, ttl = sys.argv[1].split(";")
    first_ip = sys.argv[2]
    first_port = int(sys.argv[3])

    ip_bytes = bytes(int(p) for p in ip_dest.split("."))
    port_bytes = int(port_dest).to_bytes(2, byteorder="big")
    ttl_byte = bytes([int(ttl)])

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    with open("archivo_test.txt", "r", encoding="utf-8") as f:
        for line in f:
            msg = line.rstrip("\n").encode("utf-8")
            if not msg:
                continue  # evita paquetes vacíos
            sock.sendto(ip_bytes + port_bytes + ttl_byte + msg, (first_ip, first_port))
    sock.close()
    print("Archivo enviado.")

if __name__ == "__main__":
    main()