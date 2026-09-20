# Arquitectura de SodaLocal

## Decisiones

SodaLocal es un monolito modular: una aplicación de servidor, una interfaz web y una base SQLite por negocio. La misma compilación de la interfaz funciona en la red local o detrás de HTTPS en un servidor remoto.

La API tiene rutas públicas de catálogo y creación de pedidos, rutas de empleados y rutas exclusivas de administración. Los servicios contienen el flujo de negocio; los modelos SQLAlchemy representan persistencia.

## Dinero y pedidos

Los importes se guardan como céntimos enteros y nunca se calculan con flotantes en el servidor. El total se calcula a partir de los precios del catálogo. El cliente no puede enviar un total autorizado por él.

Cada línea guarda nombre y precio del producto en el momento de crear el pedido. No se borran productos desde esta versión: se desactivan para conservar las referencias históricas.

El pedido tiene dos estados separados:

- Pago: `unpaid` o `paid`.
- Preparación: `awaiting_payment → queued → preparing → ready → delivered`.
- Cancelación: únicamente desde `awaiting_payment`.

Las devoluciones futuras requieren su propio registro; no deben resolverse borrando pagos.

## Concurrencia e idempotencia

SQLite usa WAL, claves foráneas y espera de bloqueo de hasta 15 segundos. Las escrituras adquieren `BEGIN IMMEDIATE` antes de consultar y modificar estado.

Los pedidos y pagos reciben una clave UUID del cliente y guardan una huella de la solicitud. Repetir una solicitud devuelve su resultado; reutilizar su clave con otros datos se rechaza. Una restricción única en el pago impide dos cobros por pedido.

Pago, cambio a cola de cocina y auditoría se confirman en una misma transacción. Un fallo revierte todo.

## Sesiones y permisos

Cada empleado tiene su propio usuario. La contraseña se deriva con PBKDF2-SHA256, 600 000 iteraciones y sal aleatoria. No se guarda la contraseña.

Las sesiones duran ocho horas. El cliente conserva el token en sessionStorage y lo envía en Authorization. El servidor conserva únicamente el hash y su vencimiento. No se utilizan cookies de autenticación.

El token del WebSocket viaja en el primer mensaje, no en la URL. El servidor revisa la sesión durante la conexión. Cambiar contraseña, rol o estado invalida las sesiones del empleado.

La comunicación HTTP en una red local no cifra el tráfico. HTTPS se configura en la infraestructura, especialmente al publicar en nube. No hay MFA ni recuperación de contraseña por correo en esta versión.

## Tiempo real

La revisión de cambios es un contador en memoria del proceso. El WebSocket avisa a los clientes y estos vuelven a consultar la API. También hay consultas periódicas para recuperar el estado si el canal se desconecta.

Por eso esta versión requiere un proceso de servidor. Múltiples procesos necesitarían un canal de eventos compartido y una revisión de la estrategia de almacenamiento.

## Caja

Hay un turno compartido por local. Todos los pagos requieren una caja abierta y registran el cajero.

Efectivo esperado = fondo inicial + ventas cobradas en efectivo + entradas − retiros − gastos.

El vuelto no aumenta ventas ni efectivo esperado. Tarjeta y SINPE se reportan aparte. El cierre registra contado, esperado, diferencia, empleado y observaciones.

Los movimientos se guardan en cash_movements, requieren una caja abierta, motivo y clave
idempotente, y no alteran los reportes de ventas. Se impide retirar más que el saldo esperado.

## Persistencia y evolución

El esquema usa `PRAGMA user_version = 2`. Se rechazan versiones desconocidas. La migración
1 → 2 crea un respaldo previo y agrega columnas en una transacción, conservando los datos.
Las fotografías se almacenan como archivos WebP inmutables junto a SQLite. Los respaldos ZIP
diarios y manuales incluyen ambos; la copia por CLI de SQLite conserva su alcance original.
Los datos fiscales se guardan aparte del perfil público y solo son accesibles para administradores.

SQLAlchemy facilita una futura migración a PostgreSQL, pero no la convierte en un cambio automático de URL: Database usa pragmas, transacciones y respaldo específicos de SQLite.

## Despliegue comercial

La unidad de instalación es un negocio. La versión inicial no es un SaaS multiempresa. El despliegue local y el remoto comparten código, pero no sincronizan datos.

Un producto con sucursales, varias réplicas o modo híbrido requiere decisiones adicionales: identidad del negocio, separación de datos, resolución de conflictos y persistencia de eventos.
