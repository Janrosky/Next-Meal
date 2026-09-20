# Operación y despliegue

## Instalación local

Ejecutar Instalar.cmd y después Iniciar.cmd. El primer arranque crea un administrador mediante entrada interactiva y agrega un catálogo de ejemplo si está vacío.

El servidor escucha por defecto en todas las interfaces, puerto 8000. Para restringirlo a la computadora:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1 -BindAddress 127.0.0.1
```

Para otro puerto:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1 -Port 8080
```

El acceso de los clientes se realiza desde un navegador por IP o nombre del servidor. No se necesita Node.js ni Python en caja, cocina o kioscos.

La carpeta de datos debe ser local a la máquina servidor. Para clientes conectados mediante Wi-Fi de invitados, verificar que la configuración permita únicamente el acceso necesario a la aplicación y no al resto de la computadora.

## Respaldos y restauración

La interfaz ahora crea y descarga ZIP con `soda.sqlite3`, `media/` y `RESTORE.txt`.
Los respaldos automáticos también usan este formato. Detener el servidor y extraer en una
carpeta nueva; mantener las imágenes junto a la base. No publicar la carpeta de respaldos.
La migración inicial 1 → 2 conserva un respaldo SQLite previo a la actualización.
El comando CLI `backup` y los pasos siguientes siguen siendo válidos para respaldos de solo base;
en ese caso copiar también la carpeta `media` para no perder fotografías y logos.

1. Crear un respaldo consistente desde la app o con `python -m app.cli backup`.
2. Copiarlo fuera del disco del servidor.
3. Para restaurar, detener todas las instancias de SodaLocal.
4. Conservar una copia de toda la carpeta de datos anterior antes de reemplazar nada.
5. Preparar una carpeta de datos nueva y colocar el respaldo como `soda.sqlite3`. No mezclar archivos WAL/SHM antiguos con la copia restaurada.
6. Configurar `SODA_DATABASE` para apuntar al archivo restaurado, o usar la ubicación predeterminada una vez archivada la carpeta anterior.
7. Arrancar la misma versión compatible del sistema y comprobar usuarios, catálogo, últimos pedidos y cierre de caja.

No restaurar una copia encima de una base en uso. La prueba automatizada comprueba integridad SQLite y lectura de pedidos desde el respaldo; cada negocio debe verificar también su procedimiento operativo de recuperación.

## Traslado de local a nube

1. Planificar una ventana sin pedidos ni cobros.
2. Generar y conservar un respaldo final.
3. Detener el servidor local.
4. Copiar el respaldo al disco persistente del servidor remoto.
5. Arrancar una sola instancia con `SODA_DATABASE` apuntando a ese archivo.
6. Configurar HTTPS y la dirección del negocio.
7. Revisar la información restaurada y reconectar los dispositivos.

Evitar que las instalaciones local y remota acepten pedidos a la vez: no hay sincronización entre ellas.

## Docker

Desde la raíz del repositorio:

```bash
docker compose build
docker compose run --rm sodalocal python -m app.cli init --demo
docker compose up -d
docker compose logs -f
```

El puerto es 8000, publicado solamente en localhost por defecto, y el volumen persistente es `soda-data`. Para acceso desde la red configurar SODA_BIND con la IP del host y limitar el tráfico; ver SECURITY.md. Para detener el servicio conservando el volumen:

```bash
docker compose down
```

No usar `docker compose down -v` sobre una instalación con información que se quiera conservar.

El contenedor corre como un usuario sin privilegios. Una VM o un volumen montado externamente debe permitir escritura de ese usuario sobre /data. El Dockerfile incluye compilación del frontend y comprobación de salud.

**Validación pendiente:** el contenedor no se ha construido en el entorno de desarrollo actual por no disponer de Docker.

## AWS y Azure

Esta entrega aporta una aplicación empaquetable y no recursos cloud provisionados. Para una primera instalación se propone una VM con Docker y disco persistente del propio servidor. El proveedor puede ser AWS, Azure u otro.

El despliegue debe configurar:

- Una instancia de SodaLocal y un proceso Uvicorn.
- Almacenamiento persistente para SQLite y respaldos.
- HTTPS delante del servidor.
- Acceso a la app desde los dispositivos autorizados del local, preferiblemente mediante red privada o VPN si el autoservicio no debe ser público.
- Copia de respaldos a almacenamiento independiente.
- Arranque automático del contenedor, observación de fallos y prueba de recuperación.

No se ha validado ninguna combinación concreta de plataforma o volumen cloud. SQLite no debe ponerse en un recurso de archivos compartido sin verificar sus garantías de bloqueo; la alternativa más simple para esta versión es el disco de una sola VM.

## Límites operativos

- Sin internet, un despliegue remoto no puede recibir nuevos pedidos de los clientes.
- Apagar la PC del despliegue local detiene la operación.
- No se encolan pedidos offline: la interfaz necesita confirmación del servidor.
- Las copias automáticas se comprueban al arrancar y cada hora. No se generan con el servidor apagado.
- No hay rotación automática de respaldos ni alertas externas de fallo.
- Hay 120 intentos de creación de pedido cada cinco minutos por IP. Los reintentos cuentan.
- El inicio de sesión limita a 10 intentos cada cinco minutos por IP.
- Si un proxy agrupa clientes en una IP, revisar límites y configuración de IP real sin confiar en encabezados enviados por clientes arbitrarios.

