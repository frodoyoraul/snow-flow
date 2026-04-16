# Buscador de Rostros en Fotos

App web que encuentra a una persona en una coleccion de fotos usando reconocimiento facial. Todo el procesamiento ocurre localmente en tu navegador — tus fotos nunca salen de tu equipo.

## Como usar

1. **Servir la app** (necesario por CORS):
   ```bash
   python3 -m http.server 8080
   ```
   Luego abre `http://localhost:8080` en tu navegador.

2. **Subir fotos de referencia**: Arrastra o selecciona 1 o mas fotos de la persona que quieres encontrar. Cuantas mas fotos (diferentes angulos, iluminacion), mejor sera la deteccion.

3. **Subir coleccion de fotos**: Arrastra o selecciona las fotos donde buscar.

4. **Buscar**: Haz clic en "Buscar Coincidencias" y espera a que se procesen todas las fotos.

5. **Ajustar resultados**: Usa el slider de umbral para ser mas estricto o mas flexible con las coincidencias.

6. **Descargar**: Haz clic en "Descargar Coincidencias" para obtener un ZIP con todas las fotos donde aparece la persona.

## Tecnologias

- [face-api.js](https://github.com/justadudewhohacks/face-api.js) — Deteccion y reconocimiento facial (basado en TensorFlow.js)
- [JSZip](https://stuk.github.io/jszip/) — Creacion de archivos ZIP en el navegador
- [FileSaver.js](https://github.com/eligrey/FileSaver.js/) — Descarga de archivos desde el navegador
- HTML/CSS/JS vanilla — Sin frameworks ni dependencias de build

## Privacidad

Todas las fotos se procesan localmente en tu navegador. No se envian a ningun servidor. Los modelos de IA se descargan una sola vez desde un CDN publico.
