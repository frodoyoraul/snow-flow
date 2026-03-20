const snow = require('./skills/snowflow/snowflow');

async function listExactNames() {
  const result = await snow.queryRecords('item_option_new', 'cat_item=68a7f85d472f7290a3978f59e16d43af', {
    fields: 'name',
    limit: 100
  });
  
  const names = result.records.map(r => {
    const n = r.name?.value || r.name || '';
    return n;
  });
  
  console.log('Nombres exactos de variables en el catálogo (ordenados):');
  names.sort().forEach(n => console.log('- ' + n));
  console.log('\nTotal:', names.length);
}

listExactNames().catch(console.error);
