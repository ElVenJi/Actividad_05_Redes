from router import check_routes

# Simulamos la tabla de rutas de R2 del Ejemplo 2
archivo_rutas = "rutas_R2_v2.txt"

# Test 1: Paquete dirigido al puerto 8881 (debe retornar el next hop hacia 8881)
destino_1 = ("127.0.0.1", 8881)
resultado_1 = check_routes(archivo_rutas, destino_1)
print(f"Destino {destino_1} -> Siguiente salto: {resultado_1}")

# Test 2: Paquete dirigido al puerto 8883 (debe retornar el next hop hacia 8883)
destino_2 = ("127.0.0.1", 8883)
resultado_2 = check_routes(archivo_rutas, destino_2)
print(f"Destino {destino_2} -> Siguiente salto: {resultado_2}")

# Test 3: Paquete dirigido al puerto 8884 (fuera de rango en esta tabla, debe retornar None)
destino_3 = ("127.0.0.1", 8884)
resultado_3 = check_routes(archivo_rutas, destino_3)
print(f"Destino {destino_3} -> Siguiente salto: {resultado_3}")