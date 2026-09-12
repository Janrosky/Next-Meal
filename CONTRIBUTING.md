# Desarrollo y contribuciones

## Principios

- Mantener las reglas del negocio en servicios y las rutas centradas en HTTP y autorización.
- Usar nombres explícitos y funciones con una responsabilidad clara.
- Guardar dinero como enteros en céntimos.
- Validar permisos en el servidor para toda operación de empleados.
- Conservar precios históricos y auditoría.
- No registrar contraseñas ni tokens.
- No añadir dependencias o abstracciones sin una necesidad concreta.
- No mezclar datos de demostración con ventas reales.

## Antes de entregar cambios

1. Instalar herramientas: `.venv/Scripts/python.exe -m pip install -e "./backend[dev]"`.
2. Ejecutar Ruff, pytest, compilación TypeScript y pruebas de navegador con `scripts/check.ps1`.
3. Añadir pruebas de comportamiento para reglas de dinero, permisos y estados.
4. Documentar cambios de operación, variables o instalación.
5. Si cambia el esquema, implementar y probar una migración desde la versión anterior antes de distribuirla.

## Datos

La carpeta data, entornos, dependencias descargadas y archivos .env se excluyen de Git. Usar las bases temporales de las pruebas para desarrollo y validación. Nunca subir respaldos de un cliente al repositorio.

## Organización

Consultar docs/ARQUITECTURA.md para responsabilidades y límites del despliegue. Mantener las páginas del frontend separadas por función y reutilizar el cliente HTTP y los componentes comunes.

