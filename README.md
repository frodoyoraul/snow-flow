# Buscador de Rostros en Fotos

Encuentra a una persona en tu coleccion de fotos usando reconocimiento facial. Disponible en dos versiones:

- **App Web** — Para colecciones pequenas/medianas, funciona en el navegador
- **Script Python** — Para miles o decenas de miles de fotos (Google Photos, etc.)

---

## Opcion 1: App Web (navegador)

Todo el procesamiento ocurre localmente en tu navegador. Tus fotos nunca salen de tu equipo.

### Como usar

1. Abre **https://frodoyoraul.github.io/snow-flow/** en tu navegador
2. Arrastra fotos de referencia de la persona (zona izquierda)
3. Arrastra la coleccion de fotos donde buscar (zona derecha)
4. Haz clic en "Buscar Coincidencias"
5. Ajusta el slider de umbral segun necesites
6. Descarga las coincidencias como ZIP

---

## Opcion 2: Script Python (para miles de fotos)

Ideal para procesar decenas de miles de fotos exportadas desde Google Photos.

### Paso 1: Exportar fotos desde Google Photos

1. Ve a **https://takeout.google.com**
2. Haz clic en "Deseleccionar todo"
3. Busca y marca **Google Fotos**
4. Haz clic en "Siguiente paso"
5. Elige formato: **ZIP**, tamano: **2 GB** (se dividira en varios archivos)
6. Haz clic en "Crear exportacion"
7. Espera el email de Google (puede tardar horas si tienes muchas fotos)
8. Descarga todos los ZIPs y descomprimelos en una carpeta, ejemplo: `C:\Users\TuNombre\google_photos`

### Paso 2: Preparar fotos de referencia

Crea una carpeta con 3-5 fotos de la persona que quieres buscar. Ejemplo: `C:\Users\TuNombre\fotos_referencia`

Consejos para mejores resultados:
- Usa fotos con el rostro claramente visible y bien iluminado
- Incluye fotos de diferentes angulos y condiciones de luz
- Evita fotos con gafas de sol o mucho maquillaje si las fotos destino no lo tienen

### Paso 3: Instalar Python y dependencias (Windows)

1. **Instalar Python 3.10+** desde https://www.python.org/downloads/
   - IMPORTANTE: marca la casilla **"Add Python to PATH"** durante la instalacion

2. **Instalar Visual Studio Build Tools** (necesario para compilar dlib):
   - Descarga desde https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - En el instalador, marca **"Desktop development with C++"**
   - Instala y reinicia

3. **Instalar dependencias** — abre CMD o PowerShell:
   ```
   pip install -r python/requirements.txt
   ```

### Paso 4: Ejecutar el script

```
python python/find_faces.py --reference C:\fotos_referencia --search C:\google_photos --output C:\coincidencias
```

### Opciones del script

| Opcion | Descripcion | Default |
|---|---|---|
| `--reference`, `-r` | Carpeta con fotos de referencia | (obligatorio) |
| `--search`, `-s` | Carpeta donde buscar (con subcarpetas) | (obligatorio) |
| `--output`, `-o` | Carpeta donde guardar coincidencias | `coincidencias` |
| `--tolerance`, `-t` | Tolerancia (0.0-1.0, menor=mas estricto) | `0.6` |
| `--model`, `-m` | `hog` (rapido, CPU) o `cnn` (preciso, GPU) | `hog` |
| `--workers`, `-w` | Procesos paralelos | num. de CPUs |

### Ejemplos

```bash
# Busqueda basica
python python/find_faces.py -r fotos_mama -s google_photos -o regalo_mama

# Busqueda mas estricta (menos falsos positivos)
python python/find_faces.py -r fotos_mama -s google_photos -o regalo_mama -t 0.5

# Busqueda mas flexible (mas coincidencias, posibles errores)
python python/find_faces.py -r fotos_mama -s google_photos -o regalo_mama -t 0.7

# Usar modelo CNN (mas preciso pero mas lento, ideal con GPU)
python python/find_faces.py -r fotos_mama -s google_photos -o regalo_mama -m cnn
```

### Rendimiento estimado

| Fotos | Modelo HOG (CPU) | Modelo CNN (GPU) |
|---|---|---|
| 1,000 | ~3-5 min | ~2-3 min |
| 10,000 | ~30-50 min | ~15-25 min |
| 50,000 | ~2-4 horas | ~1-2 horas |

El script guarda un **cache** en la carpeta de busqueda. Si vuelves a ejecutarlo (por ejemplo, con otra tolerancia), sera mucho mas rapido porque no necesita re-procesar las fotos.

---

## Tecnologias

### App Web
- [face-api.js](https://github.com/justadudewhohacks/face-api.js) — Reconocimiento facial en el navegador
- [JSZip](https://stuk.github.io/jszip/) + [FileSaver.js](https://github.com/eligrey/FileSaver.js/) — Descarga ZIP

### Script Python
- [face_recognition](https://github.com/ageitgey/face_recognition) — Reconocimiento facial (basado en dlib)
- [Pillow](https://pillow.readthedocs.io/) — Procesamiento de imagenes
- [tqdm](https://github.com/tqdm/tqdm) — Barra de progreso

## Privacidad

Todo se procesa localmente. Ni la app web ni el script envian fotos a ningun servidor.
