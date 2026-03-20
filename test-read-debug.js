const snow = require('./skills/snowflow/snowflow');

async function testRead() {
  const ritmSysId = '77054cbc47773654a3978f59e16d431a'; // RITM0010074
  console.log('Leyendo valores para RITM sys_id:', ritmSysId);
  
  try {
    // Paso 1: obtener sc_item_option_mtom
    const mtom = await snow.queryRecords('sc_item_option_mtom', `request_item=${ritmSysId}`, {
      fields: 'sys_id,sc_item_option',
      limit: 100
    });
    console.log('Relaciones encontradas:', mtom.records.length);
    
    // Extraer sys_ids de sc_item_option
    const optionSysIds = mtom.records
      .map(r => r.sc_item_option?.value || r.sc_item_option)
      .filter(Boolean);
    console.log('Option sys_ids:', optionSysIds);
    
    // Paso 2: obtener sc_item_option
    if (optionSysIds.length > 0) {
      const query = optionSysIds.map(id => `sys_id=${id}`).join('^');
      console.log('Query para sc_item_option:', query);
      const options = await snow.queryRecords('sc_item_option', query, {
        fields: 'item_option_new,value',
        limit: 100
      });
      console.log('Registros sc_item_option:', options.records.length);
      options.records.forEach(rec => {
        const varName = rec.item_option_new?.display_value || rec.item_option_new?.value || 'Unknown';
        const val = rec.value?.display_value || rec.value?.value || '';
        console.log(`  ${varName}: ${val}`);
      });
    }
  } catch (err) {
    console.error('ERROR:', err.message);
    console.error(err.stack);
  }
}

testRead();
