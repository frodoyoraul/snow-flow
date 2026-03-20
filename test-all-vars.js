const snow = require('./skills/snowflow/snowflow');

async function testAllVariables() {
  try {
    const catItemSysId = '68a7f85d472f7290a3978f59e16d43af';
    const requestedFor = 'abraham.lincoln';
    const variables = {
      first_name: 'Abraham',
      last_name: 'Lincoln',
      personal_email: 'abraham.personal@example.com',
      corporate_email: 'abraham.lincoln@example.com',
      department: 'a581ab703710200044e0bfc8bcbe5de8',
      location: '0002c0a93790200044e0bfc8bcbe5df5',
      job_title: 'CEO',
      manager: '6816f79cc0a8016401c5a33be04be441',
      start_date: '2026-01-15',
      needs_laptop: 'true',
      laptop_type: 'macbook-pro',
      needs_mobile: 'true',
      mobile_type: 'iphone-15',
      required_software: 'Office, VS Code',
      comments: 'Test completo de 19 variables',
      formatter: '',
      formatter2: '',
      main: ''
    };

    console.log('=== Creando orden con 19 variables ===');
    const result = await snow.orderCatalogItem(catItemSysId, requestedFor, variables);
    console.log('\n✅ Orden creada:', result);

    // Esperar 2 segundos por si ServiceNow necesita tiempo
    console.log('\nEsperando 3 segundos...');
    await new Promise(r => setTimeout(r, 3000));

    // Leer valores
    console.log('\n=== Leyendo valores de sc_item_option ===');
    const values = await snow.getRITMVariableValues(result.ritm_sys_id);
    console.log(`Variables encontradas: ${values.length}/${Object.keys(variables).length}`);
    values.forEach(v => console.log(`  ${v.variable_name}: ${v.value}`));

  } catch (err) {
    console.error('\n❌ ERROR:', err.message);
    console.error(err.stack);
  }
}

testAllVariables();
