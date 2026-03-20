const snow = require('./skills/snowflow/snowflow');

async function prueba19Variables() {
  try {
    console.log('=== PRUEBA CON 19 VARIABLES (completas) ===\n');
    
    const result = await snow.orderCatalogItem(
      '68a7f85d472f7290a3978f59e16d43af',
      'maria.garcia',
      {
        first_name: 'Maria',
        last_name: 'Garcia',
        personal_email: 'maria.garcia@example.com',
        corporate_email: 'maria.garcia@example.com',
        department: 'a581ab703710200044e0bfc8bcbe5de8',
        location: '0002c0a93790200044e0bfc8bcbe5df5',
        job_title: 'Senior Product Designer',
        manager: '6816f79cc0a8016401c5a33be04be441',
        start_date: '2025-08-15',
        needs_laptop: 'true',
        laptop_type: 'macbook-pro',
        needs_mobile: 'true',
        mobile_type: 'iphone-15',
        required_software: 'Figma, Slack, Office 365',
        comments: 'Onboarding completo con todas las variables',
        formatter: '',
        formatter2: '',
        main: '',
        system_access: 'internal'
      }
    );
    
    console.log('✅ ORDEN CREADA:');
    console.log(`   RITM: ${result.ritm_number}`);
    console.log(`   sys_id: ${result.ritm_sys_id}`);
    console.log(`   Variables procesadas: ${result.variables_processed}`);
    
    // Esperar 2s
    await new Promise(r => setTimeout(r, 2000));
    
    // Leer valores
    console.log('\n🔍 Leyiendo valores almacenados...');
    const vals = await snow.getRITMVariableValues(result.ritm_sys_id);
    console.log(`   Variables encontradas en sc_item_option: ${vals.length}`);
    vals.forEach(v => console.log(`     ${v.variable_name}: ${v.value}`));
    
    console.log('\n✅ PRUEBA DE 19 VARIABLES COMPLETADA CON ÉXITO');
  } catch (err) {
    console.error('\n❌ ERROR:', err.message);
    console.error(err.stack);
  }
}

prueba19Variables();
