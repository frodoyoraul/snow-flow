const snow = require('./skills/snowflow/snowflow');

async function getNames() {
  try {
    const res = await snow.queryRecords('item_option_new', 'cat_item=68a7f85d472f7290a3978f59e16d43af', { fields: 'name', limit: 100 });
    const names = res.records.map(r => {
      const n = r.name;
      if (n && typeof n === 'object') return n.value || n.display_value || '';
      return n || '';
    }).filter(Boolean);
    console.log(names.sort().join('\n'));
    console.log('\nTotal:', names.length);
  } catch (e) {
    console.error(e.message);
  }
}

getNames();
