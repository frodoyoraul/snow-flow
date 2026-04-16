/**
 * Modulo de galeria - Renderiza resultados, maneja slider de umbral y overlays.
 */
window.Gallery = (function () {

  /**
   * Renderiza las cards de la galeria filtrando por umbral.
   * @param {Array} matches - Todos los resultados de la busqueda
   * @param {number} threshold - Umbral actual (distancia maxima)
   */
  function render(matches, threshold) {
    var gallery = document.getElementById('gallery');
    var noResults = document.getElementById('no-results');
    var matchCount = document.getElementById('match-count');

    gallery.innerHTML = '';

    var visible = matches.filter(function (m) { return m.score <= threshold; });

    matchCount.textContent = visible.length === 1
      ? 'Se encontro 1 coincidencia'
      : 'Se encontraron ' + visible.length + ' coincidencias';

    if (visible.length === 0) {
      noResults.classList.remove('hidden');
      return;
    }

    noResults.classList.add('hidden');

    visible.forEach(function (match, index) {
      var card = createCard(match);
      card.style.animationDelay = Math.min(index * 50, 500) + 'ms';
      gallery.appendChild(card);
    });
  }

  /**
   * Crea un elemento DOM de card para un resultado.
   */
  function createCard(match) {
    var card = document.createElement('div');
    card.className = 'match-card';

    // Contenedor de imagen
    var imgContainer = document.createElement('div');
    imgContainer.className = 'match-image-container';

    var img = document.createElement('img');
    img.src = match.imageUrl;
    img.alt = match.file.name;
    img.loading = 'lazy';
    imgContainer.appendChild(img);

    // Face overlay (bounding box)
    if (match.faceBox && match.imgWidth && match.imgHeight) {
      var overlay = document.createElement('div');
      overlay.className = 'face-overlay';
      overlay.style.left = (match.faceBox.x / match.imgWidth * 100) + '%';
      overlay.style.top = (match.faceBox.y / match.imgHeight * 100) + '%';
      overlay.style.width = (match.faceBox.width / match.imgWidth * 100) + '%';
      overlay.style.height = (match.faceBox.height / match.imgHeight * 100) + '%';
      imgContainer.appendChild(overlay);
    }

    // Badge de similitud
    var badge = document.createElement('span');
    badge.className = 'similarity-badge';
    badge.textContent = match.similarity + '%';
    imgContainer.appendChild(badge);

    card.appendChild(imgContainer);

    // Info
    var info = document.createElement('div');
    info.className = 'match-info';

    var filename = document.createElement('span');
    filename.className = 'match-filename';
    filename.textContent = match.file.name;
    filename.title = match.file.name;
    info.appendChild(filename);

    var score = document.createElement('span');
    score.className = 'match-score';
    score.textContent = 'Distancia: ' + match.score.toFixed(3);
    info.appendChild(score);

    card.appendChild(info);

    return card;
  }

  /**
   * Configura el slider de umbral para re-filtrar la galeria sin re-procesar.
   * @param {Array} allMatches - Todos los resultados
   * @param {function} onThresholdChange - callback(newThreshold) para actualizar estado
   */
  function setupThresholdSlider(allMatches, onThresholdChange) {
    var slider = document.getElementById('threshold-slider');
    var valueDisplay = document.getElementById('threshold-value');
    var rafId = null;

    slider.addEventListener('input', function () {
      var newThreshold = parseFloat(slider.value);
      valueDisplay.textContent = newThreshold.toFixed(2);

      if (onThresholdChange) onThresholdChange(newThreshold);

      // Debounce con requestAnimationFrame
      if (rafId) cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(function () {
        render(allMatches, newThreshold);
      });
    });
  }

  /**
   * Muestra miniaturas circulares de las fotos de referencia.
   * @param {File[]} files
   */
  function showReferencePreview(files) {
    var container = document.getElementById('reference-previews');
    container.innerHTML = '';

    Array.from(files).forEach(function (file) {
      if (!file.type.startsWith('image/')) return;
      var img = document.createElement('img');
      img.src = URL.createObjectURL(file);
      img.alt = file.name;
      img.title = file.name;
      container.appendChild(img);
    });
  }

  /**
   * Muestra el conteo de fotos en la zona de busqueda.
   * @param {number} count
   */
  function showSearchCount(count) {
    var el = document.getElementById('search-count');
    el.textContent = count + (count === 1 ? ' foto cargada' : ' fotos cargadas');
  }

  /**
   * Obtiene las coincidencias visibles con el umbral actual.
   */
  function getVisibleMatches(allMatches, threshold) {
    return allMatches.filter(function (m) { return m.score <= threshold; });
  }

  return {
    render: render,
    setupThresholdSlider: setupThresholdSlider,
    showReferencePreview: showReferencePreview,
    showSearchCount: showSearchCount,
    getVisibleMatches: getVisibleMatches
  };
})();
