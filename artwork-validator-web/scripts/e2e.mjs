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

check('no console/page errors', errors.length === 0)
if (errors.length) console.log('ERRORS:', errors)

await browser.close()
console.log(failed ? `\n${failed} CHECK(S) FAILED` : '\nALL E2E CHECKS PASSED')
process.exit(failed ? 1 : 0)
