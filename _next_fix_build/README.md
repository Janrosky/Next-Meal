# Next-Fix

Sistema local y personalizable para gestionar reparaciones de automóviles, celulares,
computadoras, electrodomésticos, bicicletas y cualquier otro equipo.

## Primera versión funcional

- Panel ejecutivo con métricas y flujo de trabajo.
- Tickets con código correlativo, prioridad y seis etapas operativas.
- Registro de clientes, equipos, series, IMEI o placas.
- Costos de mano de obra, repuestos y pagos.
- Búsqueda global y filtros por estado.
- Cambio de etapa desde el detalle del ticket.
- Personalización de nombre, dirección, prefijo y colores de marca.
- Datos locales en SQLite y datos de demostración iniciales.
- Interfaz responsive para computadora, tableta y teléfono.
- API documentada automáticamente en `/docs`.

## Instalación en Windows

Requisitos: Python 3.12 o superior y Node.js 22 o superior.

1. Ejecutar `Instalar.cmd`.
2. Ejecutar `Iniciar.cmd`.
3. Abrir `http://127.0.0.1:8000`.

Los datos se guardan en `data/nextfix.sqlite3`. Después de la instalación, la operación
normal no necesita internet.

## Desarrollo

Backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

Frontend:

```powershell
cd frontend
npm run dev
```

## Arquitectura

- React 19 + TypeScript + Vite
- FastAPI + SQLAlchemy
- SQLite con WAL y claves foráneas
- Capas separadas de API, modelos, contratos y servicios

Esta es la base profesional del producto. Las siguientes etapas contemplan autenticación y
roles, inventario completo, fotos, presupuestos aprobables, QR, impresión, garantías,
respaldos, notificaciones y varias sucursales.
