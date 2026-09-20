import { expect, test, type Page } from '@playwright/test';

async function login(page: Page, username: string) {
  await page.goto('/#/staff');
  await page.getByLabel('Usuario', { exact: true }).fill(username);
  await page.getByLabel('Contraseña', { exact: true }).fill('Solo-Pruebas-2026!');
  await page.getByRole('button', { name: 'Ingresar', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Cerrar sesión' })).toBeVisible();
}

test('kiosk, cash payment, live kitchen, close shift and admin reports', async ({ browser }) => {
  const customerContext = await browser.newContext();
  const employeeContext = await browser.newContext();
  const kitchenContext = await browser.newContext();
  const adminContext = await browser.newContext();
  const customer = await customerContext.newPage();
  const cashier = await employeeContext.newPage();
  const kitchen = await kitchenContext.newPage();
  const admin = await adminContext.newPage();
  const errors: string[] = [];
  for (const page of [customer, cashier, kitchen, admin]) {
    page.on('pageerror', error => errors.push(error.message));
  }

  await customer.goto('/');
  await expect(customer.getByRole('heading', { name: 'Tu antojo, recién hecho.' })).toBeVisible();
  await customer.screenshot({ path: 'test-results/autoservicio.png', fullPage: true });
  await customer.getByRole('button', { name: 'Agregar Casado con pollo', exact: true }).click();
  await customer.getByRole('button', { name: 'Comer aquí', exact: true }).click();
  await customer.getByLabel('Mesa (opcional)').fill('7');
  await customer.getByLabel('¿Algo que debamos saber?').fill('Sin cebolla');
  await customer.getByRole('button', { name: 'Confirmar pedido', exact: true }).click();
  await expect(customer.getByRole('heading', { name: 'Pasá a caja a pagar.' })).toBeVisible();
  await expect(customer.locator('.ticket-number')).toContainText(/#\d{4,}/);

  await login(kitchen, 'cocina');
  await expect(kitchen.locator('.kitchen-ticket')).toHaveCount(0);

  await login(cashier, 'caja');
  await cashier.getByRole('button', { name: 'Turno de caja', exact: true }).click();
  await cashier.getByLabel('Fondo inicial en efectivo (₡)').fill('10000');
  await cashier.getByRole('button', { name: 'Abrir caja', exact: true }).click();
  await expect(cashier.getByRole('heading', { name: /^Caja abierta · #\d+$/ })).toBeVisible();
  await cashier.getByRole('button', { name: 'Caja', exact: true }).click();
  await cashier.locator('.order-summary').first().click();
  await cashier.getByLabel('Efectivo recibido (₡)').fill('5000');
  await expect(cashier.locator('.change-box')).toContainText('800');
  await cashier.getByRole('button', { name: 'Confirmar pago y enviar a cocina' }).click();
  await expect(cashier.getByText('Pago registrado. Ya está en cocina.')).toBeVisible();

  await expect(kitchen.locator('.kitchen-ticket')).toHaveCount(1, { timeout: 10000 });
  await expect(kitchen.locator('.kitchen-ticket')).toContainText('Mesa 7');
  await expect(kitchen.locator('.kitchen-ticket')).toContainText('Sin cebolla');
  await kitchen.screenshot({ path: 'test-results/cocina.png', fullPage: true });
  await kitchen.getByRole('button', { name: 'Comenzar', exact: true }).click();
  await kitchen.getByRole('button', { name: 'Marcar listo', exact: true }).click();
  await kitchen.getByRole('button', { name: 'Entregado', exact: true }).click();
  await expect(kitchen.locator('.kitchen-ticket')).toHaveCount(0);
  await expect(kitchen.getByRole('button', { name: 'Productos', exact: true })).toHaveCount(0);

  await cashier.getByRole('button', { name: 'Turno de caja', exact: true }).click();
  await cashier.getByLabel('Efectivo contado al cierre (₡)').fill('14200');
  await cashier.getByRole('button', { name: 'Confirmar cierre de caja' }).click();
  await expect(cashier.getByText('Cuadra', { exact: true }).first()).toBeVisible();

  await login(admin, 'admin');
  await expect(admin.locator('.metric').first()).toContainText('4');
  await admin.screenshot({ path: 'test-results/administracion.png', fullPage: true });
  const downloadPromise = admin.waitForEvent('download');
  await admin.getByRole('button', { name: 'Exportar', exact: true }).click();
  expect((await downloadPromise).suggestedFilename()).toMatch(/^ventas-.*\.csv$/);
  await admin.getByRole('button', { name: 'Productos', exact: true }).click();
  await admin.getByRole('button', { name: 'Nuevo producto', exact: true }).click();
  await admin.getByLabel('Nombre', { exact: true }).fill('Prueba empanada');
  await admin.getByLabel('Descripción', { exact: true }).fill('Queso y frijoles.');
  await admin.getByLabel('Precio final (₡)').fill('1250.50');
  await admin.getByRole('button', { name: 'Guardar producto', exact: true }).click();
  await expect(admin.getByText('Prueba empanada', { exact: true })).toBeVisible();
  await admin.getByRole('button', { name: 'Mi negocio', exact: true }).click();
  await admin.getByLabel('Nombre del local').fill('Soda La Esquina');
  await admin.getByRole('button', { name: 'Guardar cambios', exact: true }).click();
  await expect(admin.getByText('Configuración guardada.')).toBeVisible();
  await customer.getByRole('button', { name: 'Hacer otro pedido' }).click();
  await customer.reload();
  await expect(customer.locator('.brand strong')).toHaveText('Soda La Esquina');
  await expect(customer.getByRole('heading', { name: 'Prueba empanada' })).toBeVisible();

  await customer.setViewportSize({ width: 390, height: 844 });
  await customer.screenshot({ path: 'test-results/movil.png', fullPage: true });
  expect(await customer.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(errors).toEqual([]);
  await Promise.all([customerContext.close(), employeeContext.close(), kitchenContext.close(), adminContext.close()]);
});
