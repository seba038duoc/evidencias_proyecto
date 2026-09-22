# LogiSLA — Sprint 1 completo (backend + frontend)

Esta carpeta ya está lista para correr en tu computador. Para verla:

1. Doble clic en **`iniciar.bat`**.
2. La primera vez va a tardar unos minutos (instala las dependencias de Python y Node).
3. Al final se abre tu navegador solo en `http://localhost:3000`, y en la ventana del script queda impreso tu `company_id` (cópialo, sin el `company_id=` de adelante).
4. Pegá el `company_id` en la página, subí un CSV/Excel de envíos, y listo.

Quedan dos ventanas de terminal abiertas (Backend y Frontend) mientras la uses — no las cierres hasta terminar.

## Requisitos

- Python 3.10 o superior, instalado y en el PATH (`python --version` en una terminal debería funcionar).
- Node.js 18 o superior (`node --version`).

Si no los tenés, instalalos desde python.org y nodejs.org (elegí la opción "Add to PATH" durante la instalación de Python).

## Nota sobre la base de datos

Esta versión usa SQLite (un archivo `backend/logisla.db`) en vez de PostgreSQL, para que no tengas que instalar nada más — es la misma app, mismo código, solo cambia dónde vive el dato. Cuando el equipo despliegue de verdad (Sprint 4, GCP), ahí sí se usa PostgreSQL como está planeado en el proyecto.

Si en algún momento querés probarlo con PostgreSQL real, `backend/README.md` tiene las instrucciones (`docker-compose.yml` incluido).

## Archivos de prueba

`backend/sample_data/envios_piloto.csv` — 60 guías con headers normales (el mapeo automático los reconoce solo).
`backend/sample_data/envios_headers_no_reconocidos.csv` — headers raros, para probar el formulario de mapeo manual.

## Si algo falla

`iniciar.bat` revisa que Python y Node estén instalados y avisa con un
mensaje claro si falta alguno, en vez de fallar en silencio. Si aun así la
instalación del backend o del frontend falla, **queda un archivo
`install.log`** dentro de `backend\` o `frontend\` (según cuál haya
fallado) con el detalle completo del error — aunque la ventana se cierre
sola, ese archivo se queda ahí. Mandale ese archivo a Claude (o pegale el
contenido) para que te diga exactamente qué pasó.

Otros casos conocidos:

- Si tenés **más de un Python instalado** (por ejemplo el de Microsoft
  Store y el de python.org al mismo tiempo), el script ya usa siempre la
  ruta completa al Python de adentro del entorno virtual
  (`backend\.venv\Scripts\python.exe`) para evitar que se mezclen — pero
  si necesitás correr algo a mano en una terminal nueva, usá esa misma
  ruta completa en vez de escribir `python` o `pip` sueltos.
- Si abrís una terminal nueva para correr algo del backend a mano, acordate
  de setear primero `set DATABASE_URL=sqlite:///./logisla.db` (esa
  ventana no hereda la variable que sí tiene la que abrió el script).
- Si la carpeta está sincronizada con OneDrive y algo se ve "vacío" en el
  Explorador justo después de copiar o extraer archivos, primero refrescá
  la ventana (F5) antes de asumir que faltan.

## Tip: dónde extraer la carpeta

Si es posible, extraé/copiá esta carpeta dentro de tu carpeta **Documents**
de Windows en vez de Escritorio/OneDrive. Es la carpeta a la que Claude
tiene acceso directo desde esta sesión, así que si algo vuelve a fallar
puedo revisar los archivos (y el `install.log`) yo mismo sin que tengas que
copiar y pegar nada.
