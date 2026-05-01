# React + Django Template

Proyecto full-stack con React (Vite) en el frontend y Django en el backend, completamente dockerizado.

## Inicio Rápido

### Desarrollo

1. Clonar el repositorio
2. Copiar variables de entorno:
   ```bash
   cp .env.example .env
   ```
3. Iniciar contenedores:
   ```bash
   docker compose up --build
   ```
4. Acceder a:
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000
   - Base de datos: localhost:5432

### Producción

1. Configurar `.env` con valores de producción
2. Construir e iniciar:
   ```bash
   docker compose -f docker-compose.prod.yml up --build -d
   ```
3. Acceder a:
   - Frontend: http://localhost
   - Backend: http://localhost:8000

## Comandos Útiles

### Desarrollo

```bash
# Iniciar servicios
docker compose up

# Reconstruir imágenes
docker compose up --build

# Ver logs
docker compose logs -f

# Ejecutar migraciones en el backend
docker compose exec backend python manage.py migrate

# Instalar dependencia en el frontend
docker compose exec frontend npm install <dependencia>

# Detener servicios
docker compose down
```

### Producción

```bash
# Iniciar en background
docker compose -f docker-compose.prod.yml up --build -d

# Ver logs
docker compose -f docker-compose.prod.yml logs -f

# Detener
docker compose -f docker-compose.prod.yml down
```
