// End-to-end drive of the single-file build under file:// —
// loads fixtures, walks the validation flow, exports the Excel report.
//
// Usage: npm run build && python3 scripts/gen_fixtures.py && node scripts/e2e.mjs
import { chromium } from 'playwright-core'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import { existsSync, mkdirSync } from 'node:fs'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const fixtures = join(root, 'tests', 'fixtures', 'e2e')
const outDir = process.env.E2E_OUT || join(root, 'e2e-out')
mkdirSync(outDir, { recursive: true })

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' })
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
const errors = []
page.on('pageerror', (err) => errors.push(String(err)))
page.on('console', (m) => m.type() === 'error' && errors.push(m.text()))

let failed = 0
function check(label, ok) {
  console.log(`${ok ? '✅' : '❌'} ${label}`)
  if (!ok) failed++
}

await page.goto('file://' + join(root, 'dist', 'index.html'))

// 0. First visit: the onboarding tour must show — dismiss it
await page.waitForSelector('text=Choisissez votre marque', { timeout: 10000 })
check('onboarding tour shows on first visit', true)
await page.locator('button:has-text("Passer")').click()

// 1. Load PDFs via the hidden multi-file input
const pdfInput = page.locator('input[type=file][accept=".pdf"]')
await pdfInput.setInputFiles([
  join(fixtures, 'YCA12345.pdf'),
  join(fixtures, 'YCA12346_v2.pdf'),
  join(fixtures, 'YCA12347.pdf'),
  join(fixtures, 'badname.pdf'),
  join(fixtures, 'YCA99999.pdf'),
])
await page.waitForSelector('text=4 PDF(s) chargé(s)', { timeout: 20000 })
check('4 valid PDFs ingested', true)
check('invalid filename flagged', (await page.locator('text=badname.pdf').count()) > 0)

// 2. Load the Excel brief — the app switches to the validation view once both
// inputs are ready
await page.screenshot({ path: join(outDir, '1-files.png') })
await page.locator('input[type=file][accept=".xlsx"]').setInputFiles(join(fixtures, 'brief_mny.xlsx'))
await page.waitForSelector('text=1 / 4', { timeout: 10000 })
check('Excel brief accepted, validation view opens on litho 1/4', true)
check('results table shows FOREST BROWN OK', (await page.locator('tr.bg-emerald-50').count()) === 1)
check('results table shows MISSING SHADE error', (await page.locator('tr.bg-red-50').count()) === 1)
await page.screenshot({ path: join(outDir, '2-validation.png') })

// 4. Approve litho 1 (auto-advance)
await page.locator('button:has-text("✅ Approuver")').click()
await page.waitForSelector('text=2 / 4')
check('approve auto-advances to 2/4', true)

// 5. Litho 2 is the CUBBY
check('CUBBY matrix displayed', (await page.locator('text=CUBBY 3F × 2T').count()) === 1)
check('CUBBY tier rows present', (await page.locator('text=TIER 2').count()) >= 1)
await page.screenshot({ path: join(outDir, '3-cubby.png') })

// 6. Reject with a comment
await page.locator('textarea').fill('Test de refus E2E')
await page.locator('button:has-text("❌ Refuser")').click()
await page.waitForSelector('text=3 / 4')
check('reject auto-advances to 3/4', true)

// 7. Litho 3: MIXED badge + WTP equivalence must pass
check('MIXED badge shown', (await page.locator('text=MIXED FACINGS').count()) >= 1)
check('WTP shade validated via WATERPROOF', (await page.locator('tr.bg-emerald-50').count()) === 2)

// 8. Litho 4 (scanned): manual review badge
await page.locator('button:has-text("Suivant ▶")').click()
await page.waitForSelector('text=4 / 4')
check('manual review badge on scanned PDF', (await page.locator('text=Revue manuelle requise').count()) === 1)
await page.screenshot({ path: join(outDir, '4-scanned.png') })

// 9. Overview
await page.keyboard.press('Control+1')
await page.waitForSelector('text=Approuvées')
check('overview shows approved=1', (await page.locator('div:has(> div:text-is("Approuvées")) >> text=1').count()) >= 1)
await page.screenshot({ path: join(outDir, '5-overview.png') })

// 10. Export the Excel report (Ctrl+E download)
const downloadPromise = page.waitForEvent('download', { timeout: 15000 })
await page.keyboard.press('Control+e')
const download = await downloadPromise
const reportPath = join(outDir, download.suggestedFilename())
await download.saveAs(reportPath)
check(`report downloaded (${download.suggestedFilename()})`, existsSync(reportPath))

// 11. Export session JSON
const sessionDl = page.waitForEvent('download', { timeout: 15000 })
await page.keyboard.press('Control+s')
const sessionFile = await sessionDl
const sessionPath = join(outDir, 'session-export.json')
await sessionFile.saveAs(sessionPath)
check('session JSON downloaded', existsSync(sessionPath))

// 12. Switch brand to ESSIE → all MNY files become invalid
await page.locator('select').first().selectOption('ESSIE')
await page.waitForTimeout(500)
const bodyText = await page.textContent('body')
check('brand switch to ESSIE invalidates MNY files', bodyText.includes('format de nom invalide'))

// ===== v1.1: brand wizard, JSON brands, template download =====

// 13. Create a custom NYX brand through the wizard
await page.keyboard.press('Control+3') // Paramètres
await page.waitForSelector('text=Nouvelle marque')
await page.locator('button:has-text("+ Nouvelle marque")').click()
await page.locator('input[placeholder="NYX, OAP, GARNIER…"]').fill('NYX')
await page.locator('input[placeholder="NYX Professional Makeup"]').fill('NYX Professional Makeup')
await page.locator('button:has-text("Suivant →")').click()
// Step 2: prefix rule + live filename test
await page.locator('input[placeholder="YCA"]').fill('NYX')
await page.locator('input[type="number"]').fill('6')
await page.locator('textarea[placeholder*="Un nom de fichier par ligne"]').fill('NYX123456_v2.pdf\nmauvais_nom.pdf')
await page.waitForTimeout(300)
const wizardBody = await page.textContent('body')
check('wizard live-test validates NYX123456_v2.pdf', wizardBody.includes('code NYX123456'))
await page.locator('button:has-text("Suivant →")').click() // columns
await page.locator('button:has-text("Suivant →")').click() // options
await page.locator('button:has-text("Suivant →")').click() // recap
await page.waitForSelector('text=Définition valide')
check('wizard recap shows a valid definition', true)
await page.locator('button:has-text("💾 Enregistrer la marque")').click()
await page.waitForTimeout(400)
check('NYX appears in the brand list', (await page.locator('text=NYX Professional Makeup').count()) >= 1)

// 14. The new brand is selectable in the header and validates NYX filenames
const headerOptions = await page.locator('header select option').allTextContents()
check('header brand select contains NYX', headerOptions.some((o) => o.includes('NYX')))

// 15. Download the Excel template for the custom brand
const nyxCard = page
  .locator('div.rounded-lg.border')
  .filter({ hasText: 'NYX Professional Makeup' })
  .first()
const templateDl = page.waitForEvent('download', { timeout: 15000 })
await nyxCard.locator('button:has-text("📄 Template Excel")').click()
const template = await templateDl
check(`brand template downloads (${template.suggestedFilename()})`, template.suggestedFilename().includes('NYX'))

// 16. Export the brand JSON
const brandJsonDl = page.waitForEvent('download', { timeout: 15000 })
await nyxCard.locator('button:has-text("⬇ JSON")').click()
const brandJson = await brandJsonDl
check('brand JSON exports', brandJson.suggestedFilename() === 'brand_NYX.json')

// 17. AI settings section is present (no network test without a key)
check('AI settings section present', (await page.locator('text=Intelligence artificielle').count()) >= 1)

check('no console/page errors', errors.length === 0)
if (errors.length) console.log('ERRORS:', errors)

await browser.close()
console.log(failed ? `\n${failed} CHECK(S) FAILED` : '\nALL E2E CHECKS PASSED')
process.exit(failed ? 1 : 0)
