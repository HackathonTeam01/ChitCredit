export function createAutoPayNotification({ amount = 500, date, language = 'en' } = {}) {
  const amountText = `Rs ${amount.toLocaleString('en-IN')}`
  const messages = {
    en: `Your chit payment of ${amountText} was auto-paid from your savings wallet on time.`,
    ta: `உங்கள் ${amountText} சிட் கட்டணம் சேமிப்பு பணப்பையிலிருந்து சரியான நேரத்தில் செலுத்தப்பட்டது.`,
  }
  return { type: 'auto-pay', date: date || new Date().toISOString().slice(0, 10), amount, language, message: messages[language] || messages.en }
}

export function notificationsForSmoothing(smoothingResult, options = {}) {
  if (!smoothingResult?.targetReachedDate) return []
  return [createAutoPayNotification({ ...options, date: smoothingResult.targetReachedDate, amount: smoothingResult.targetAmount })]
}
