const snow = require('./skills/snowflow/snowflow');

async function testFullCycle() {
  try {
    //CREAR ORDEN
    const result = await snow.orderCatalogItem(
      '68a7f85d472f7290a3978f59e16d43af',
      'test.user',
      {
        first_name: 'Test',
        last_name: 'User',
        personal_email: 'test.user@example.com',
        department: 'a581ab703710200044e0bfc8bcbe5de8',
        location: '0002c0a93790200044e0bfc8bcbe5df5',
        job_title: 'Engineer',
        manager: '6816f79cc0a8016401c5a33be04be441',
        start_date: '2025-06-01'
      }
    );
    console.log('\n✅ ORDEN CREADA:', result);

    // Esperar un momento por si ServiceNow necesita tiempo
    await new Promise(r => setTimeout(r, 2000));

    // LEER VALORES
    console.log('\n🔍 Leyendo valores de sc_item_option para el RITM...');
    const values = await snow.getRITMVariableValues(result.ritm_sys_id);
    console.log(`Variables encontradas: ${values.length}`);
    values.forEach(v => console.log(`  ${v.variable_name}: ${v.value}`));

  } catch (err) {
    console.error('\n❌ ERROR:', err.message);
    console.error(err.stack);
  }
}

testFullCycle();
