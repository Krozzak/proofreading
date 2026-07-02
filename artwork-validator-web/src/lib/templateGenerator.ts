// Generates a downloadable Excel brief template for a brand: a BRIEF sheet
// with the exact expected headers + example rows, and a French INSTRUCTIONS
// sheet so anyone can build a valid brief from scratch.
import ExcelJS from 'exceljs'
import type { BrandDefinition } from '../core/brandConfigs'
import { describeBrandDefinition } from '../core/brandConfigs'
import { downloadBlob } from './excelIO'

function exampleCode(def: BrandDefinition): string {
  if (def.filename.type === 'prefix') {
    return def.filename.literal + '1'.padEnd(def.filename.digits, '2').slice(0, def.filename.digits)
  }
  return def.examples?.valid_filenames?.[0]?.replace(/\.pdf$/i, '') ?? 'CODE_EXEMPLE'
}

function exampleValue(columnName: string, def: BrandDefinition, row: number): string | number {
  switch (columnName) {
    case 'LITHO':
      return exampleCode(def)
    case 'DECRIPTION':
      return row === 0 ? `${def.brand_name.toUpperCase()} DISPLAY EXEMPLE` : ''
    case 'UPC':
      return `1234567890${row}`
    case 'UPC SEQUENCE':
      return ''
    case 'UPC POSITION':
      return row + 1
    case 'PRODUCT DESCRIPTION':
      return 'DESCRIPTION PRODUIT'
    case 'SHADE NAME':
      return row === 0 ? 'FOREST BROWN' : 'CRIMSON RED'
    case 'SHADE NUMBER':
      return def.columns.find((c) => c.name === 'SHADE NUMBER')?.type === 'numeric' ? 110 + row * 10 : 'BASE COAT'
    case 'PRODUCT FACING SL':
      return 2
    case '4 DIGITS':
      return 4501 + row
    default:
      return ''
  }
}

export async function buildTemplateWorkbook(def: BrandDefinition): Promise<ArrayBuffer> {
  const workbook = new ExcelJS.Workbook()
  workbook.created = new Date()

  // --- BRIEF sheet ---
  const brief = workbook.addWorksheet('BRIEF')
  const headers = def.columns.map((c) => c.name)
  const headerRow = brief.addRow(headers)
  headerRow.font = { bold: true }
  headerRow.eachCell((cell, colNumber) => {
    const column = def.columns[colNumber - 1]
    cell.fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: column.required ? 'FFFFE0E0' : 'FFF0F0F0' },
    }
  })

  // Two example rows the user can overwrite
  for (let r = 0; r < 2; r++) {
    brief.addRow(def.columns.map((c) => exampleValue(c.name, def, r)))
  }

  headers.forEach((h, i) => {
    brief.getColumn(i + 1).width = Math.min(Math.max(h.length + 4, 12), 30)
  })

  // --- INSTRUCTIONS sheet ---
  const info = workbook.addWorksheet('INSTRUCTIONS')
  info.getColumn(1).width = 34
  info.getColumn(2).width = 90
  const addLine = (a: string, b = '', bold = false) => {
    const row = info.addRow([a, b])
    if (bold) row.font = { bold: true }
  }

  addLine(`Template de brief — ${def.brand_name} (${def.brand_code})`, '', true)
  addLine('')
  addLine('Comment utiliser ce fichier :', '', true)
  addLine('1.', "Remplissez la feuille BRIEF — une ligne par produit, sans modifier les en-têtes.")
  addLine('2.', 'Les deux lignes d\'exemple sont à remplacer par vos données.')
  addLine('3.', "La colonne LITHO relie chaque ligne au fichier PDF correspondant (même code).")
  addLine('4.', "Colonnes en rouge clair = obligatoires ; en gris = optionnelles.")
  addLine('5.', "⚠️ L'en-tête « DECRIPTION » est volontairement orthographié ainsi — ne pas corriger.")
  addLine('')
  addLine('Format des noms de fichiers PDF :', '', true)
  for (const line of describeBrandDefinition(def).split('\n')) {
    addLine('', line)
  }
  addLine('')
  addLine('Colonnes :', '', true)
  for (const c of def.columns) {
    addLine(
      c.name,
      `${c.required ? 'OBLIGATOIRE' : 'optionnelle'} — type ${c.type === 'numeric' ? 'numérique' : 'texte'}`,
    )
  }
  addLine('')
  addLine('Types spéciaux reconnus :', '', true)
  addLine('CUBBY', "Description contenant « [faces]F[tiers]T » (ex: 10F2T) → validation en matrice.")
  addLine('FRAME', "PRODUCT FACING SL = FRAME → ligne non validée (cadre).")
  addLine('SPACE_SAVER', 'UPC, PRODUCT DESCRIPTION ou SHADE NAME = SPACE_SAVER → ligne non validée.')
  addLine('MIXED', 'Plusieurs valeurs de facing différentes → badge MIXED (à confirmer au planogramme).')

  return workbook.xlsx.writeBuffer() as Promise<ArrayBuffer>
}

export async function downloadTemplate(def: BrandDefinition): Promise<void> {
  const buffer = await buildTemplateWorkbook(def)
  downloadBlob(
    buffer,
    `Template_Brief_${def.brand_code}.xlsx`,
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  )
}
