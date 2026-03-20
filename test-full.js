const snow = require('./skills/snowflow/snowflow');

async function testFull() {
  try {
    const catItemSysId = '68a7f85d472f7290a3978f59e16d43af';
    const requestedFor = 'test.user';
    const variables = {
      first_name: 'Test',
      last_name: 'User',
      personal_email: 'test.user@example.com',
      corporate_email: 'test.user@example.com',
      department: 'a581ab703710200044e0bfc8bcbe5de8',
      location: '0002c0a93790200044e0bfc8bcbe5df5',
      job_title: 'Test Engineer',
      manager: '6816f79cc0a8016401c5a33be04be441',
      start_date: '2025-12-01',
      needs_laptop: 'true',
      laptop_type: 'standard',
      needs_mobile: 'true',
      mobile_type: 'iphone'
    };

    console.log('=== Creando orden completa ===');
    const result = await snow.orderCatalogItem(catItemSysId, requestedFor, variables);
    console.log('\n✅ Resultado:', result);

    // Verificar sc_item_option
    console.log('\n=== Verificando sc_item_option para el RITM ===');
    const values = await snow.getRITMVariableValues(result.ritm_sys_id);
    console.log(`Variables encontradas: ${values.length}`);
    values.forEach(v => console.log(`  ${v.variable_name}: ${v.value}`));

  } catch (err) {
    console.error('\n❌ ERROR:', err.message);
    console.error(err.stack);
  }
}

testFull();
