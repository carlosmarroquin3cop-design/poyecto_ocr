
const input     = document.getElementById('inputArchivo');
const btnP      = document.getElementById('btnProcesar');
const spinner   = document.getElementById('spinner');
const resultado = document.getElementById('resultado');
const previewC  = document.getElementById('preview-container');
const previewI  = document.getElementById('preview-img');

// Muestra preview de la imagen seleccionada
input.addEventListener('change', () => {
    const file = input.files[0];
    if (!file) return;

    // Mostrar preview solo si es imagen
    if (file.type.startsWith('image/')) {
        previewI.src = URL.createObjectURL(file);
        previewC.style.display = 'block';
    } else {
        previewC.style.display = 'none';
    }

    btnP.style.display = 'block';
    resultado.style.display = 'none';
});

// Envía el archivo a la API
btnP.addEventListener('click', async () => {
    const file = input.files[0];
    if (!file) return;

    btnP.style.display  = 'none';
    spinner.style.display = 'block';
    resultado.style.display = 'none';

    const formData = new FormData();
    formData.append('archivo', file);

    try {
        const res  = await fetch('/api/procesar', { method: 'POST', body: formData });
        const json = await res.json();

        spinner.style.display = 'none';
        resultado.style.display = 'block';

        if (json.ok) {
            const d = json.datos;
            resultado.className = 'resultado exito';
            resultado.innerHTML = `
                <strong>✅ Procesado</strong><br>
                <b>Proveedor:</b> ${d.proveedor || '—'}<br>
                <b>Total:</b> ${d.total || '—'}<br>
                <b>Fecha:</b> ${d.fecha || '—'}<br>
                <b>Banco:</b> ${d.banco || '—'}
            `;
            // Recarga el historial después de 1.5s
            setTimeout(() => location.reload(), 1500);
        } else {
            resultado.className = 'resultado error';
            resultado.innerHTML = `❌ Error: ${json.error}`;
            btnP.style.display = 'block';
        }
    } catch (e) {
        spinner.style.display = 'none';
        resultado.className = 'resultado error';
        resultado.innerHTML = '❌ No se pudo conectar al servidor.';
        resultado.style.display = 'block';
        btnP.style.display = 'block';
    }
});
