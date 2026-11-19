from router import parse_packet, create_packet

# Creamos un paquete manual de prueba (6 bytes de header + mensaje)
# IP: 127.0.0.1 (4 bytes)
ip_bytes = bytes([127, 0, 0, 1])
# Puerto: 8882 (2 bytes)
port_bytes = (8882).to_bytes(2, byteorder='big')
# Mensaje: "hola" (bytes)
msg_bytes = "hola".encode('utf-8')

IP_packet_v1 = ip_bytes + port_bytes + msg_bytes

# Probamos parse_packet
parsed = parse_packet(IP_packet_v1)
print("Resultado parse_packet:", parsed)

# Probamos create_packet
IP_packet_v2 = create_packet(parsed)

# Verificamos si son iguales
print(f"IP_packet_v1 == IP_packet_v2 ? {IP_packet_v1 == IP_packet_v2}")

