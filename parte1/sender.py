import sys
import socket
from router import create_packet

def main():
    # Verificamos que se entreguen exactamente los 5 argumentos necesarios:
    # 1. IP final | 2. Puerto final | 3. IP de envío (primer salto) | 4. Puerto de envío | 5. Mensaje
    if len(sys.argv) != 6:
        print("Uso correcto: python3 sender.py IP_router_final puerto_router_final IP_envio puerto_envio mensaje")
        sys.exit(1)

    # Capturamos los argumentos desde sys.argv
    final_ip = sys.argv[1]
    final_port = int(sys.argv[2])
    send_ip = sys.argv[3]
    send_port = int(sys.argv[4])
    message = sys.argv[5]

    # Creamos el diccionario con la estructura conveniente para create_packet
    parsed_packet = {
        "ip": final_ip,
        "port": final_port,
        "msg": message
    }

    # Generamos el paquete IP en formato de bytes (6 bytes de header + mensaje)
    packet_bytes = create_packet(parsed_packet)

    # Creamos un socket UDP no orientado a conexión
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Dirección donde enviaremos físicamente el paquete (ej: la IP y puerto de R1)
    target_address = (send_ip, send_port)
    
    # Enviamos el paquete binario a través del socket
    sender_socket.sendto(packet_bytes, target_address)
    
    print(f"[SENDER] Paquete enviado exitosamente.")
    print(f"         - Enviado físicamente a: {target_address}")
    print(f"         - Destino final (Header): ({final_ip}, {final_port})")
    print(f"         - Mensaje: '{message}'")
    
    sender_socket.close()

if __name__ == "__main__":
    main()