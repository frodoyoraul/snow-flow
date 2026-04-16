/**
 * Modulo de deteccion facial - Wrapper de face-api.js
 * Maneja carga de modelos, extraccion de descriptores y comparacion.
 */
window.FaceDetection = (function () {
  const MODEL_URLS = [
    'https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js@master/weights',
    'https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights'
  ];

  let modelsLoaded = false;

  /**
   * Carga los 3 modelos necesarios desde CDN.
   * Intenta la URL principal y si falla usa el fallback.
   */
  async function loadModels() {
    if (modelsLoaded) return;

    let lastError = null;
    for (const url of MODEL_URLS) {
      try {
        await Promise.all([
          faceapi.nets.ssdMobilenetv1.loadFromUri(url),
          faceapi.nets.faceLandmark68Net.loadFromUri(url),
          faceapi.nets.faceRecognitionNet.loadFromUri(url)
        ]);
        modelsLoaded = true;
        console.log('Modelos cargados correctamente desde:', url);
        return;
      } catch (err) {
        console.warn('Fallo al cargar modelos desde:', url, err);
        lastError = err;
      }
    }
    throw new Error('No se pudieron cargar los modelos de IA. ' + (lastError ? lastError.message : ''));
  }

  /**
   * Crea un HTMLImageElement a partir de un File.
   */
  function createImageElement(file) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      const url = URL.createObjectURL(file);
      img.onload = () => resolve({ img, url });
      img.onerror = () => {
        URL.revokeObjectURL(url);
        reject(new Error('No se pudo cargar la imagen: ' + file.name));
      };
      img.src = url;
    });
  }

  /**
   * Redimensiona imagen grande a un canvas mas pequeno para mejorar rendimiento.
   */
  function resizeForDetection(img, maxDim) {
    maxDim = maxDim || 1024;
    if (img.width <= maxDim && img.height <= maxDim) return img;
    var canvas = document.createElement('canvas');
    var scale = maxDim / Math.max(img.width, img.height);
    canvas.width = Math.round(img.width * scale);
    canvas.height = Math.round(img.height * scale);
    canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height);
    return canvas;
  }

  /**
   * Extrae descriptores faciales de una imagen.
   * Retorna array de { descriptor, detection }.
   */
  async function extractDescriptors(imgElement) {
    var input = resizeForDetection(imgElement);
    var detections = await faceapi
      .detectAllFaces(input)
      .withFaceLandmarks()
      .withFaceDescriptors();

    return detections.map(function (d) {
      // Calcular box relativo al tamano original si fue redimensionado
      var scaleX = imgElement.width / (input.width || imgElement.width);
      var scaleY = imgElement.height / (input.height || imgElement.height);
      var box = d.detection.box;
      return {
        descriptor: d.descriptor,
        detection: {
          box: {
            x: box.x * scaleX,
            y: box.y * scaleY,
            width: box.width * scaleX,
            height: box.height * scaleY
          },
          score: d.detection.score
        }
      };
    });
  }

  /**
   * Distancia euclidiana entre dos descriptores.
   */
  function computeDistance(d1, d2) {
    return faceapi.euclideanDistance(d1, d2);
  }

  /**
   * Procesa las fotos de referencia y extrae todos sus descriptores.
   * @param {File[]} files
   * @param {function} onProgress - callback(current, total)
   * @returns {{ descriptors: Float32Array[] }}
   */
  async function processReferencePhotos(files, onProgress) {
    var allDescriptors = [];
    for (var i = 0; i < files.length; i++) {
      if (onProgress) onProgress(i + 1, files.length);
      try {
        var result = await createImageElement(files[i]);
        var descs = await extractDescriptors(result.img);
        descs.forEach(function (d) {
          allDescriptors.push(d.descriptor);
        });
        URL.revokeObjectURL(result.url);
      } catch (err) {
        console.warn('Error procesando referencia:', files[i].name, err);
      }
      // Yield al UI thread
      await new Promise(function (r) { setTimeout(r, 0); });
    }
    return { descriptors: allDescriptors };
  }

  /**
   * Busca coincidencias en la coleccion de fotos.
   * @param {File[]} files - Fotos a buscar
   * @param {Float32Array[]} referenceDescriptors
   * @param {number} maxThreshold - Umbral generoso para capturar posibles coincidencias
   * @param {function} onProgress - callback(current, total, fileName)
   * @param {object} cancelToken - { cancelled: boolean }
   * @returns {Array} Resultados con score, file, imageUrl, faceBox, similarity
   */
  async function searchPhotos(files, referenceDescriptors, maxThreshold, onProgress, cancelToken) {
    var results = [];
    for (var i = 0; i < files.length; i++) {
      if (cancelToken && cancelToken.cancelled) break;
      var file = files[i];
      if (onProgress) onProgress(i + 1, files.length, file.name);

      try {
        var result = await createImageElement(file);
        var faces = await extractDescriptors(result.img);

        var bestScore = Infinity;
        var bestFace = null;

        for (var f = 0; f < faces.length; f++) {
          for (var r = 0; r < referenceDescriptors.length; r++) {
            var dist = computeDistance(faces[f].descriptor, referenceDescriptors[r]);
            if (dist < bestScore) {
              bestScore = dist;
              bestFace = faces[f];
            }
          }
        }

        if (bestScore <= maxThreshold && bestFace) {
          results.push({
            file: file,
            imageUrl: result.url, // Mantener vivo para la galeria
            score: bestScore,
            similarity: Math.round((1 - bestScore) * 100),
            faceBox: bestFace.detection.box,
            imgWidth: result.img.width,
            imgHeight: result.img.height
          });
        } else {
          URL.revokeObjectURL(result.url);
        }
      } catch (err) {
        console.warn('Error procesando foto:', file.name, err);
      }
      // Yield al UI thread
      await new Promise(function (r) { setTimeout(r, 0); });
    }

    // Ordenar por similitud (mayor primero = menor distancia primero)
    results.sort(function (a, b) { return a.score - b.score; });
    return results;
  }

  /**
   * Libera URLs de resultados que ya no se necesitan.
   */
  function cleanupResults(results) {
    results.forEach(function (r) {
      if (r.imageUrl) {
        URL.revokeObjectURL(r.imageUrl);
        r.imageUrl = null;
      }
    });
  }

  return {
    loadModels: loadModels,
    processReferencePhotos: processReferencePhotos,
    searchPhotos: searchPhotos,
    cleanupResults: cleanupResults,
    isReady: function () { return modelsLoaded; }
  };
})();
