import pdfMakeModule from 'pdfmake/build/pdfmake'
import pdfFontsModule from 'pdfmake/build/vfs_fonts'

const pdfMake = pdfMakeModule?.default || pdfMakeModule
const pdfFonts = pdfFontsModule?.default || pdfFontsModule

if (pdfFonts?.pdfMake?.vfs) {
  pdfMake.vfs = pdfFonts.pdfMake.vfs
} else if (pdfFonts?.vfs) {
  pdfMake.vfs = pdfFonts.vfs
}

pdfMake.fonts = {
  Roboto: {
    normal: 'Roboto-Regular.ttf',
    bold: 'Roboto-Medium.ttf',
    italics: 'Roboto-Italic.ttf',
    bolditalics: 'Roboto-MediumItalic.ttf'
  }
}

export default pdfMake
