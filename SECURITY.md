# Seguridad y exposición de red

## Qué se publica en GitHub

El repositorio público contiene código, documentación, dependencias declaradas y capturas con datos ficticios.

Se excluyen bases SQLite, respaldos, archivos .env, claves privadas, carpetas de secretos, entornos de Python, node_modules y resultados de prueba. No hay usuarios de producción preconfigurados.

Las contraseñas visibles en los tests son exclusivamente de cuentas de prueba, creadas en una base aislada. No deben reutilizarse en una instalación real.

## Puertos y duración

| Modo | Puerto | Dirección | Mientras está activo |
| --- | --- | --- | --- |
| Iniciar.cmd | TCP 8000 | Todas las interfaces de la PC | Mientras el proceso del servidor corre |
| Arranque con BindAddress 127.0.0.1 | TCP 8000 | Solo la misma PC | Mientras el proceso corre |
| Desarrollo Vite | TCP 5173 por defecto | Solo la misma PC | Mientras Vite corre |
| Pruebas de navegador | TCP 8011 | Solo la misma PC | Durante las pruebas |
| Docker Compose | TCP 8000 | Solo localhost por defecto | Mientras el contenedor corre |

WebSocket comparte el mismo puerto que la API; no necesita otro. SQLite no escucha en un puerto.

Detener el servidor elimina su escucha. No elimina reglas que alguien haya creado en el firewall o router. Docker usa restart: unless-stopped, por lo que puede reiniciar el servicio después de reiniciar la máquina si no se detuvo explícitamente.

**Los scripts de Windows no crean reglas de firewall, no abren puertos en el router y no configuran redirección desde internet.**

## Aplicación, firewall y router son cosas distintas

1. El servidor empieza a escuchar cuando se ejecuta.
2. El firewall decide quién puede conectarse.
3. Un router, una dirección pública o las reglas cloud determinan si puede llegar tráfico de internet.

No basta con decir que es una app local: escuchar en todas las interfaces también incluye las interfaces de VPN u otras redes que tenga la PC. No se ha auditado la configuración completa del equipo o del router.

En Windows, una regla de entrada debe limitarse al puerto, programa y orígenes necesarios. Para clientes de IP fija es preferible permitir esas IP concretas. Una regla con toda la subred también permitiría otros equipos de esa subred.

La regla queda configurada hasta que se deshabilite o elimine. Puede combinar programa y puerto, de modo que autorice tráfico solo cuando exista una aplicación escuchando.

[Documentación de reglas de Windows Firewall](https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/rules).

## Configuración recomendada para un local

- Servidor en una PC dedicada o con acceso de administrador restringido.
- Red operativa separada del Wi-Fi libre de clientes.
- Firewall limitado a los equipos autorizados y a la red privada del local.
- Sin redirección del puerto 8000 en el router.
- HTTPS para cifrar la sesión, especialmente sobre Wi-Fi o redes compartidas.
- Cuentas individuales y desactivación inmediata de empleados que ya no deban acceder.
- Copias fuera del disco del servidor y acceso restringido a SQLite y respaldos.

El menú y la creación de pedidos son públicos para cualquier dispositivo que pueda llegar a la aplicación. Esta versión no tiene emparejamiento de kioscos ni autorización por dispositivo. Una persona con acceso podría enviar pedidos falsos pendientes de pago. Los límites de frecuencia reducen abuso básico pero no reemplazan controles de acceso de red.

## Configuración para nube

No publicar el puerto de Uvicorn directamente en internet. Usar HTTPS delante del servicio y controles de red, VPN o autorización de dispositivos según el modelo del negocio.

Docker Compose publica en localhost de forma predeterminada. Para permitir acceso en una LAN de forma deliberada, configurar SODA_BIND con la IP del servidor o 0.0.0.0, y restringir el tráfico con controles de red. Publicar en 0.0.0.0 permite tráfico por todas las interfaces alcanzables; no equivale a limitarlo a la LAN.

[Documentación de publicación de puertos en Docker](https://docs.docker.com/engine/network/port-publishing/).

## Protecciones presentes

- Verificación de roles en la API.
- Contraseñas derivadas con PBKDF2 y sal aleatoria.
- Tokens aleatorios con caducidad, almacenados como hash en el servidor.
- Revocación de sesiones al cambiar la cuenta.
- Validación de datos y límites de frecuencia básicos.
- Cálculo de totales en servidor.
- Transacciones e idempotencia para evitar cobros duplicados.
- Auditoría de operaciones.

## Límites

No es una certificación de seguridad ni una auditoría de penetración. La instalación inicial no configura certificados, MFA, aislamiento por dispositivo, gestión de vulnerabilidades o protección frente a ataques volumétricos.

El archivo SQLite y los respaldos no se cifran desde la aplicación. Aplicar cifrado y permisos a nivel de disco cuando corresponda.

La tokenización protege cómo se guardan las sesiones, no su transporte: HTTP no cifra contraseñas ni tokens durante la conexión.

## Reporte de vulnerabilidades

No publicar secretos, bases reales ni datos de clientes en un issue público. Usar un canal privado acordado con el propietario del repositorio. Todavía no existe un canal dedicado de soporte de seguridad.

