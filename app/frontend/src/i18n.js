import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './locales/en.json'
import it from './locales/it.json'

const saved = localStorage.getItem('localmes_lang')
const browser = (navigator.language || 'en').slice(0, 2)

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    it: { translation: it },
  },
  lng: saved || (['en', 'it'].includes(browser) ? browser : 'en'),
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
})

export default i18n
