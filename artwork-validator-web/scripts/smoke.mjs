// Smoke test: open dist/index.html via file://, check render + console errors.
import { chromium } from 'playwright-core'

const executablePath = '/opt/pw-browsers/chromium'
const browser = await chromium.launch({ executablePath })
const page = await browser.newPage()

const errors = []
page.on('console', (msg) => {
  if (msg.type() === 'error') errors.push(msg.text())
})
page.on('pageerror', (err) => errors.push(String(err)))

await page.goto('file:///home/user/proofreading/artwork-validator-web/dist/index.html')
await page.waitForTimeout(1500)

const title = await page.title()
const headerText = await page.textContent('header').catch(() => null)
const dropZones = await page.locator('text=Dossier de lithos PDF').count()

console.log('TITLE:', title)
console.log('HEADER:', headerText?.slice(0, 120))
console.log('DROPZONE COUNT:', dropZones)
console.log('CONSOLE ERRORS:', errors.length ? errors : 'none')

await page.screenshot({ path: process.env.SCRATCH + '/smoke-startup.png' })
await browser.close()
