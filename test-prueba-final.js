const snow = require('./skills/snowflow/snowflow');

async function pruebaCompleta() {
  try {
    const variables = {
      first_name: 'Maria',
      last_name: 'Garcia',
      personal_email: 'maria.garcia@example.com',
      job_title: 'Senior Product Designer',
      start_date: '2025-08-15'
    };

    console.log('=== PRUEBA COMPLETA ===');
    const res = await snow.orderCatalogItem(
      '68a7f85d472f7290a3978f59e16d43af',
      'maria.garcia',
      variables
    );
    console.log('\n✅ ORDEN CREADA:');
    console.log(`   RITM: ${res.ritm_number}`);
    console.log(`   RITM sys_id: ${res.ritm_sys_id}`);
    console.log(`   Variables procesadas: ${res.variables_processed}`);

    // Leer valores (esperar 2s por si ServiceNow tarda)
    await new Promise(r => setTimeout(r, 2000));
    console.log('\n🔍 Leyendo valores almacenados...');
    const vals = await snow.getRITMVariableValues(res.ritm_sys_id);
    console.log(`   Variables encontradas en sc_item_option: ${vals.length}`);
    vals.forEach(v => console.log(`     ${v.variable_name}: ${v.value}`));

    console.log('\n✅ PRUEBA COMPLETADA CON ÉXITO');
  } catch (err) {
    console.error('\n❌ ERROR:', err.message);
    console.error(err.stack);
  }
}

pruebaCompleta();
