# React + Django Template
Proyecto full-stack con React (Vite) en el frontend y Django en el backend, completamente dockerizado.
## 🚀 Inicio Rápido
### Desarrollo
1. Clonar el repositorio
2. Copiar variables de entorno:
   ```bash
   cp .env.example .env
Iniciar contenedores:
docker-compose up --build
Acceder a:
Frontend: http://localhost:5173
Backend: http://localhost:8000
Base de datos: localhost:5432
Producción
Configurar .env con valores de producción
Construir e iniciar:
docker-compose -f docker-compose.prod.yml up -d --build
Acceder a:
Frontend: http://localhost
Backend: http://localhost:8000


 Comandos Útiles
Desarrollo
# Iniciar servicios
docker-compose up
# Reconstruir imágenes
docker-compose up --build
# Ver logs
docker-compose logs -f
# Ejecutar comando en backend
docker-compose exec backend python manage.py migrate
# Ejecutar comando en frontend
docker-compose exec frontend npm install nueva-dependencia
# Detener servicios
docker-compose down
Producción

# Iniciar en background
docker-compose -f docker-compose.prod.yml up -d --build
# Ver logs
docker-compose -f docker-compose.prod.yml logs -f
# Detener
docker-compose -f docker-compose.prod.yml down