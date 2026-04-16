/**
 * Modulo principal - Orquesta la app, maneja estado y conecta los modulos.
 */
(function () {
  // Estado de la aplicacion
  var state = {
    referenceFiles: [],
    searchFiles: [],
    referenceDescriptors: [],
    allResults: [],
    threshold: 0.6,
    modelsLoaded: false,
    isProcessing: false,
    cancelToken: { cancelled: false }
  };

  // Referencias al DOM
  var els = {};

  function init() {
    // Cachear elementos del DOM
    els.referenceZone = document.getElementById('reference-zone');
    els.referenceInput = document.getElementById('reference-input');
    els.searchZone = document.getElementById('search-zone');
    els.searchInput = document.getElementById('search-input');
    els.searchBtn = document.getElementById('search-btn');
    els.progressSection = document.getElementById('progress-section');
    els.progressText = document.getElementById('progress-text');
    els.progressBar = document.getElementById('progress-bar');
    els.progressDetail = document.getElementById('progress-detail');
    els.resultsSection = document.getElementById('results-section');
    els.downloadBtn = document.getElementById('download-btn');
    els.modelStatus = document.getElementById('model-status');
    els.modelStatusText = document.getElementById('model-status-text');
    els.statusDot = els.modelStatus.querySelector('.status-dot');

    // Configurar zonas de drag-and-drop
    setupDropZone(els.referenceZone, els.referenceInput, handleReferenceFiles);
    setupDropZone(els.searchZone, els.searchInput, handleSearchFiles);

    // Boton de busqueda
    els.searchBtn.addEventListener('click', startSearch);

    // Boton de descarga
    els.downloadBtn.addEventListener('click', handleDownload);

    // Cargar modelos en background
    loadModelsInBackground();
  }

  // === Drag and Drop ===

  function setupDropZone(zone, input, onFiles) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(function (evt) {
      zone.addEventListener(evt, function (e) {
        e.preventDefault();
        e.stopPropagation();
      });
    });

    ['dragenter', 'dragover'].forEach(function (evt) {
      zone.addEventListener(evt, function () {
        zone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(function (evt) {
      zone.addEventListener(evt, function () {
        zone.classList.remove('dragover');
      });
    });

    zone.addEventListener('drop', function (e) {
      var files = filterImageFiles(e.dataTransfer.files);
      if (files.length > 0) onFiles(files);
    });

    zone.addEventListener('click', function (e) {
      // No abrir file picker si se hizo clic en una preview
      if (e.target.tagName === 'IMG') return;
      input.click();
    });

    input.addEventListener('change', function () {
      var files = filterImageFiles(input.files);
      if (files.length > 0) onFiles(files);
      input.value = ''; // Permitir re-seleccionar los mismos archivos
    });
  }

  function filterImageFiles(fileList) {
    return Array.from(fileList).filter(function (f) {
      return f.type.startsWith('image/');
    });
  }

  // === Manejo de archivos ===

  function handleReferenceFiles(files) {
    state.referenceFiles = files;
    els.referenceZone.classList.add('has-files');
    Gallery.showReferencePreview(files);
    updateSearchButton();
  }

  function handleSearchFiles(files) {
    state.searchFiles = files;
    els.searchZone.classList.add('has-files');
    Gallery.showSearchCount(files.length);
    updateSearchButton();
  }

  function updateSearchButton() {
    els.searchBtn.disabled = state.referenceFiles.length === 0 ||
      state.searchFiles.length === 0 ||
      state.isProcessing;
  }

  // === Carga de modelos ===

  async function loadModelsInBackground() {
    try {
      await FaceDetection.loadModels();
      state.modelsLoaded = true;
      els.statusDot.className = 'status-dot ready';
      els.modelStatusText.textContent = 'Modelos de IA listos';
    } catch (err) {
      els.statusDot.className = 'status-dot error';
      els.modelStatusText.textContent = 'Error al cargar modelos';
      showError('Error al cargar los modelos de IA. Verifica tu conexion a internet y recarga la pagina.');
    }
  }

  // === Flujo de busqueda ===

  async function startSearch() {
    if (state.isProcessing) return;
    state.isProcessing = true;
    state.cancelToken = { cancelled: false };
    els.searchBtn.disabled = true;
    els.resultsSection.classList.add('hidden');
    els.progressSection.classList.remove('hidden');

    // Limpiar resultados anteriores
    if (state.allResults.length > 0) {
      FaceDetection.cleanupResults(state.allResults);
      state.allResults = [];
    }

    try {
      // 1. Asegurar que los modelos estan cargados
      if (!state.modelsLoaded) {
        updateProgress('Cargando modelos de IA...', 0, '');
        await FaceDetection.loadModels();
        state.modelsLoaded = true;
        els.statusDot.className = 'status-dot ready';
        els.modelStatusText.textContent = 'Modelos de IA listos';
      }

      // 2. Procesar fotos de referencia
      updateProgress('Procesando fotos de referencia...', 0, '');
      var refResult = await FaceDetection.processReferencePhotos(
        state.referenceFiles,
        function (current, total) {
          var pct = Math.round((current / total) * 30); // 0-30%
          updateProgress(
            'Procesando fotos de referencia...',
            pct,
            'Foto ' + current + ' de ' + total
          );
        }
      );

      state.referenceDescriptors = refResult.descriptors;

      if (state.referenceDescriptors.length === 0) {
        showError('No se detectaron rostros en las fotos de referencia. Usa fotos donde el rostro sea claramente visible y este bien iluminado.');
        resetAfterSearch();
        return;
      }

      // 3. Buscar coincidencias (usar umbral generoso de 0.9 para capturar todo)
      updateProgress('Buscando coincidencias...', 30, '');
      state.allResults = await FaceDetection.searchPhotos(
        state.searchFiles,
        state.referenceDescriptors,
        0.9,
        function (current, total, fileName) {
          var pct = 30 + Math.round((current / total) * 70); // 30-100%
          updateProgress(
            'Buscando coincidencias...',
            pct,
            'Foto ' + current + ' de ' + total + ' - ' + fileName
          );
        },
        state.cancelToken
      );

      // 4. Mostrar resultados
      els.progressSection.classList.add('hidden');
      els.resultsSection.classList.remove('hidden');

      state.threshold = parseFloat(document.getElementById('threshold-slider').value);
      Gallery.render(state.allResults, state.threshold);
      Gallery.setupThresholdSlider(state.allResults, function (newThreshold) {
        state.threshold = newThreshold;
      });

      if (state.allResults.length === 0) {
        document.getElementById('match-count').textContent = 'No se detectaron rostros en las fotos';
        document.getElementById('no-results').classList.remove('hidden');
      }

    } catch (err) {
      console.error('Error durante la busqueda:', err);
      showError('Ocurrio un error durante la busqueda: ' + err.message);
    }

    resetAfterSearch();
  }

  function resetAfterSearch() {
    state.isProcessing = false;
    els.progressSection.classList.add('hidden');
    updateSearchButton();
  }

  function updateProgress(text, percent, detail) {
    els.progressText.textContent = text;
    els.progressBar.value = percent;
    els.progressDetail.textContent = detail;
  }

  // === Descarga ZIP ===

  async function handleDownload() {
    var visible = Gallery.getVisibleMatches(state.allResults, state.threshold);
    if (visible.length === 0) return;

    var originalText = els.downloadBtn.textContent;
    els.downloadBtn.disabled = true;
    els.downloadBtn.textContent = 'Preparando ZIP...';

    try {
      await ZipExport.downloadMatches(visible, function (current, total) {
        els.downloadBtn.textContent = 'Empaquetando ' + current + '/' + total + '...';
      });
    } catch (err) {
      console.error('Error creando ZIP:', err);
      showError('Error al crear el archivo ZIP: ' + err.message);
    }

    els.downloadBtn.disabled = false;
    els.downloadBtn.textContent = originalText;
  }

  // === Errores ===

  function showError(message) {
    // Remover error previo si existe
    var prev = document.querySelector('.error-message');
    if (prev) prev.remove();

    var div = document.createElement('div');
    div.className = 'error-message';
    div.innerHTML = '<p>' + escapeHtml(message) + '</p>';

    var btn = document.createElement('button');
    btn.textContent = 'Cerrar';
    btn.addEventListener('click', function () { div.remove(); });
    div.appendChild(btn);

    var main = document.querySelector('main');
    main.insertBefore(div, els.progressSection);
  }

  function escapeHtml(text) {
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // === Iniciar ===
  document.addEventListener('DOMContentLoaded', init);
})();
