/**
 * Modulo de exportacion ZIP - Crea archivos ZIP de las coincidencias y dispara la descarga.
 */
window.ZipExport = (function () {

  /**
   * Descarga las fotos coincidentes como un archivo ZIP.
   * @param {Array} matches - Array de resultados con propiedad .file (File object)
   * @param {function} onProgress - callback(current, total)
   */
  async function downloadMatches(matches, onProgress) {
    if (matches.length === 0) return;

    var zip = new JSZip();
    var usedNames = {};

    for (var i = 0; i < matches.length; i++) {
      var match = matches[i];
      var name = getUniqueName(match.file.name, usedNames);

      try {
        var buffer = await match.file.arrayBuffer();
        zip.file(name, buffer);
      } catch (err) {
        console.warn('Error al leer archivo para ZIP:', match.file.name, err);
      }

      if (onProgress) onProgress(i + 1, matches.length);
    }

    var blob = await zip.generateAsync(
      { type: 'blob', compression: 'DEFLATE', compressionOptions: { level: 6 } },
      function (metadata) {
        // Progreso de compresion (opcional, ya incluido en el flujo principal)
      }
    );

    saveAs(blob, 'coincidencias-rostro.zip');
  }

  /**
   * Genera un nombre unico para evitar duplicados en el ZIP.
   * Si "IMG_001.jpg" ya existe, genera "IMG_001_2.jpg", "IMG_001_3.jpg", etc.
   */
  function getUniqueName(name, usedNames) {
    if (!usedNames[name]) {
      usedNames[name] = 1;
      return name;
    }

    usedNames[name]++;
    var dotIndex = name.lastIndexOf('.');
    if (dotIndex === -1) {
      return name + '_' + usedNames[name];
    }

    var base = name.substring(0, dotIndex);
    var ext = name.substring(dotIndex);
    return base + '_' + usedNames[name] + ext;
  }

  return {
    downloadMatches: downloadMatches
  };
})();
