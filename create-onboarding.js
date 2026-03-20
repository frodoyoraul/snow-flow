#!/usr/bin/env node

/**
 * Wrapper para crear órdenes de User Onboarding usando snowflow skill
 * Uso: node create-onboarding.js <username> <first_name> <last_name> <email> <job_title> [start_date]
 *
 * Ejemplo:
 *   node create-onboarding.js jane.doe Jane Doe jane.doe@example.com "Product Manager" 2025-06-01
 *
 * NOTA: Todas las variables del catálogo se rellenan automáticamente.
 * Variables opcionales tienen valores por defecto.
 */

const snow = require('./skills/snowflow/snowflow');

// Configuración del catálogo
const CATALOG_SYS_ID = '68a7f85d472f7290a3978f59e16d43af';

// Referencias (sys_ids) - estas pueden venir de configuración o BD
const COMMON_REFERENCES = {
  DEPARTMENT_FINANCE: 'a581ab703710200044e0bfc8bcbe5de8',
  LOCATION_HEADQUARTERS: '0002c0a93790200044e0bfc8bcbe5df5',
  MANAGER_ADMIN: '6816f79cc0a8016401c5a33be04be441'
};

/**
 * Genera un objeto de variables completo para el catálogo "User Onboarding"
 * Incluye todas las variables definidas en item_option_new para este catálogo.
 *
 * @param {Object} overrides - Valores específicos para sobrescribir
 * @returns {Object} variables listas para orderCatalogItem
 */
function buildOnboardingVariables(overrides = {}) {
  const defaults = {
    // Campos obligatorios
    first_name: overrides.first_name || '',
    last_name: overrides.last_name || '',
    personal_email: overrides.personal_email || '',
    corporate_email: overrides.corporate_email || '',
    department: overrides.department || COMMON_REFERENCES.DEPARTMENT_FINANCE,
    location: overrides.location || COMMON_REFERENCES.LOCATION_HEADQUARTERS,
    job_title: overrides.job_title || '',
    manager: overrides.manager || COMMON_REFERENCES.MANAGER_ADMIN,
    start_date: overrides.start_date || new Date().toISOString().split('T')[0],

    // Campos opcionales
    needs_laptop: overrides.needs_laptop !== undefined ? String(overrides.needs_laptop) : 'true',
    laptop_type: overrides.laptop_type || 'standard',
    needs_mobile: overrides.needs_mobile !== undefined ? String(overrides.needs_mobile) : 'true',
    mobile_type: overrides.mobile_type || 'iphone',
    required_software: overrides.required_software || '',
    comments: overrides.comments || '',
    formatter: overrides.formatter || '',
    formatter2: overrides.formatter2 || '',
    main: overrides.main || '',
    system_access: overrides.system_access || 'internal' // nuevo
  };

  return { ...defaults, ...overrides };
}

/**
 * Crea una orden de onboarding con los datos proporcionados
 * @param {Object} params - { username, firstName, lastName, corporateEmail, jobTitle, startDate, [manager], ...otherVariables }
 */
async function createOnboardingOrder(params) {
  const {
    username,
    firstName,
    lastName,
    corporateEmail,
    jobTitle,
    startDate,
    manager, // sys_id del manager, opcional
    ...restOverrides
  } = params;

  if (!username || !firstName || !lastName || !corporateEmail || !jobTitle) {
    console.error('Faltan parámetros obligatorios: username, firstName, lastName, corporateEmail, jobTitle');
    process.exit(1);
  }

  // Validar fecha
  const fecha = startDate || new Date().toISOString().split('T')[0];
  if (!/^\d{4}-\d{2}-\d{2}$/.test(fecha)) {
    console.error('Error: start_date debe ser formato YYYY-MM-DD');
    process.exit(1);
  }

  // Construir variables base
  const personalEmail = `personal.${username}@example.com`;

  const variables = buildOnboardingVariables({
    first_name: firstName,
    last_name: lastName,
    personal_email: personalEmail,
    corporate_email: corporateEmail,
    job_title: jobTitle,
    start_date: fecha,
    manager: manager || COMMON_REFERENCES.MANAGER_ADMIN,
    ...restOverrides
  });

  console.log(`Creando orden de onboarding para ${firstName} ${lastName} (${username})...`);
  console.log(`Manager: ${manager || 'admin'}`);
  console.log(`Job Title: ${jobTitle}`);
  console.log(`Start Date: ${fecha}`);

  try {
    const result = await snow.orderCatalogItem(CATALOG_SYS_ID, username, variables);

    if (result.success) {
      console.log('✅ Orden creada exitosamente:');
      console.log(`   RITM: ${result.ritm_number}`);
      console.log(`   sys_id: ${result.ritm_sys_id}`);
      console.log(`   Variables enviadas:`, Object.keys(variables).join(', '));
    } else {
      console.error('❌ Falló la creación:', result.raw);
    }

    return result;
  } catch (error) {
    console.error('❌ Error creando orden:', error.message);
    throw error;
  }
}

// ============================================
// PRUEBAS: 5 órdenes con datos diferentes
// ============================================

async function runFiveTests() {
  const testData = [
    {
      username: 'maria.garcia',
      firstName: 'Maria',
      lastName: 'Garcia',
      corporateEmail: 'maria.garcia@example.com',
      jobTitle: 'Senior Product Designer',
      startDate: '2025-08-15',
      manager: 'a8f98bb0eb32010045e1a5115206fe3a' // Abraham Lincoln (del RITM anterior)
    },
    {
      username: 'david.johnson',
      firstName: 'David',
      lastName: 'Johnson',
      corporateEmail: 'david.johnson@example.com',
      jobTitle: 'DevOps Engineer',
      startDate: '2025-09-01',
      manager: COMMON_REFERENCES.MANAGER_ADMIN // admin
    },
    {
      username: 'sophie.muller',
      firstName: 'Sophie',
      lastName: 'Müller',
      corporateEmail: 'sophie.muller@example.com',
      jobTitle: 'Data Analyst',
      startDate: '2025-10-20',
      manager: 'a8f98bb0eb32010045e1a5115206fe3a' // Abraham
    },
    {
      username: 'roberto.fernandez',
      firstName: 'Roberto',
      lastName: 'Fernández',
      corporateEmail: 'roberto.fernandez@example.com',
      jobTitle: 'Backend Developer',
      startDate: '2025-11-05',
      manager: COMMON_REFERENCES.MANAGER_ADMIN
    },
    {
      username: 'lisa.simpson',
      firstName: 'Lisa',
      lastName: 'Simpson',
      corporateEmail: 'lisa.simpson@example.com',
      jobTitle: 'QA Engineer',
      startDate: '2025-12-01',
      manager: 'a8f98bb0eb32010045e1a5115206fe3a'
    }
  ];

  console.log('=== INICIANDO 5 PRUEBAS DE ÓRDENES DE ONBOARDING ===\n');

  for (let i = 0; i < testData.length; i++) {
    console.log(`\n[PRUEBA ${i + 1}/5]`);
    try {
      await createOnboardingOrder(testData[i]);
      console.log(`   ✅ Prueba ${i + 1} completada`);
    } catch (err) {
      console.error(`   ❌ Prueba ${i + 1} falló:`, err.message);
    }
    // Esperar breve intervalo entre órdenes
    await new Promise(res => setTimeout(res, 2000));
  }

  console.log('\n=== TODAS LAS PRUEBAS FINALIZADAS ===');
}

// Ejecutar desde CLI
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    // Si no hay argumentos, ejecutar las 5 pruebas
    runFiveTests()
      .then(() => console.log('\n✅ Proceso completado'))
      .catch(err => {
        console.error('\n❌ Falló:', err.message);
        process.exit(1);
      });
  } else {
    // Modo compatibility: crear una orden con argumentos
    const [username, firstName, lastName, corporateEmail, jobTitle, startDate] = args;
    createOnboardingOrder({ username, firstName, lastName, corporateEmail, jobTitle, startDate })
      .then(() => console.log('\n✅ Orden creada'))
      .catch(err => {
        console.error('\n❌ Falló:', err.message);
        process.exit(1);
      });
  }
}

module.exports = {
  createOnboardingOrder,
  buildOnboardingVariables,
  CATALOG_SYS_ID,
  COMMON_REFERENCES
};
