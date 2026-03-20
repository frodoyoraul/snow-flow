const snow = require('./skills/snowflow/snowflow');

async function testCreateAndRead() {
  try {
    // Crear orden con 2 variables
    console.log('Creando orden...');
    const result = await snow.orderCatalogItem(
      '68a7f85d472f7290a3978f59e16d43af',
      'test.user',
      {
        first_name: 'Test',
        last_name: 'User'
      }
    );
    console.log('Orden creada:', result);

    // Leer valores
    console.log('\nLeyendo sc_item_option_mtom...');
    const mtom = await snow.queryRecords('sc_item_option_mtom', `request_item=${result.ritm_sys_id}`, { fields: 'sys_id,sc_item_option', limit: 10 });
    console.log('  Relaciones encontradas:', mtom.records.length);
    mtom.records.forEach(r => console.log(`    ${r.sys_id} -> ${r.sc_item_option?.value || r.sc_item_option}`));

    console.log('\nLeyendo sc_item_option directamente...');
    const values = await snow.getRITMVariableValues(result.ritm_sys_id);
    console.log('  Variables encontradas:', values.length);
    values.forEach(v => console.log(`    ${v.variable_name}: ${v.value}`));

  } catch (err) {
    console.error('ERROR:', err.message);
    console.error(err.stack);
  }
}

testCreateAndRead();
