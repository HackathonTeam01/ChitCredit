import { useState } from 'react'
import { ArrowRight, Banknote, CheckCircle2, CreditCard, LockKeyhole, Smartphone, WalletCards } from 'lucide-react'

const methods = [
  { id: 'upi', label: 'UPI', hint: 'Instant · recommended', icon: Smartphone },
  { id: 'wallet', label: 'Savings wallet', hint: 'Balance ₹12,400', icon: WalletCards },
  { id: 'bank', label: 'Bank account', hint: 'HDFC •••• 2048', icon: Banknote },
]

export default function PaymentCenter({ onAutoPayment }) {
  const [method, setMethod] = useState('upi')
  const [amount, setAmount] = useState(500)
  const [stage, setStage] = useState('choose')
  const [reference, setReference] = useState('')
  const [error, setError] = useState('')

  const confirm = async () => {
    setError('')
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'}/contribution`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ member_id: 1, chit_group_id: 101, due_date: new Date().toISOString().slice(0, 10), amount_due: amount, amount_paid: amount, paid_on_time: true }),
      })
      const result = await response.json()
      if (!response.ok) throw new Error(result.error || 'Payment failed')
      setReference(result.contribution?.id ? `IP-${result.contribution.id}` : 'IP-confirmed')
      if (result.auto_payment_event) onAutoPayment?.(result.auto_payment_event)
      setStage('success')
    } catch {
      setError('Payment could not be confirmed. Start the backend and try again.')
    }
  }

  return <section className="bg-white rounded-2xl shadow-soft overflow-hidden">
    <div className="p-5 md:p-7 border-b border-[#eee7e1] flex justify-between items-start">
      <div><p className="text-xs uppercase tracking-widest text-[#9b4c4a] font-bold">Contribution payments</p><h2 className="serif text-2xl text-[#4b2635] mt-2">Keep your circle moving.</h2><p className="text-sm text-[#907f7d] mt-2">Choose how you want to pay your ₹500 chit contribution.</p></div>
      <LockKeyhole className="text-[#3f8d72]" size={20} />
    </div>
    {error && <p role="alert" className="px-5 md:px-7 pt-4 text-sm text-[#c65d4c]">{error}</p>}
    {stage === 'choose' && <div className="p-5 md:p-7">
      <p className="text-xs font-bold text-[#907f7d] uppercase tracking-widest">1. Select amount</p>
      <div className="grid grid-cols-3 gap-2 mt-3">{[500, 1000, 1500].map(value => <button key={value} onClick={() => setAmount(value)} className={`rounded-xl py-3 text-sm font-bold border ${amount === value ? 'border-[#9b4c4a] bg-[#f1e4d5] text-[#4b2635]' : 'border-[#ded4ce] text-[#907f7d]'}`}>₹{value.toLocaleString('en-IN')}</button>)}</div>
      <p className="text-xs font-bold text-[#907f7d] uppercase tracking-widest mt-7">2. Choose payment method</p>
      <div className="space-y-2 mt-3">{methods.map(({ id, label, hint, icon: Icon }) => <button key={id} onClick={() => setMethod(id)} className={`w-full text-left rounded-xl border p-3 flex items-center gap-3 ${method === id ? 'border-[#9b4c4a] bg-[#fbf8f3]' : 'border-[#eee7e1]'}`}><span className={`w-9 h-9 rounded-lg grid place-items-center ${method === id ? 'bg-[#4b2635] text-[#e4aa57]' : 'bg-[#f1e4d5] text-[#9b4c4a]'}`}><Icon size={17} /></span><span className="flex-1"><b className="block text-sm text-[#4b2635]">{label}</b><small className="text-xs text-[#907f7d]">{hint}</small></span><span className={`w-4 h-4 rounded-full border-2 ${method === id ? 'border-[#9b4c4a] bg-[#9b4c4a]' : 'border-[#ded4ce]'}`} /></button>)}</div>
      <button onClick={() => setStage('review')} className="w-full bg-[#4b2635] text-white rounded-xl py-3.5 mt-7 font-bold">Review payment <ArrowRight className="inline ml-2" size={16} /></button>
    </div>}
    {stage === 'review' && <div className="p-5 md:p-7"><p className="text-sm text-[#907f7d]">You are paying ₹{amount.toLocaleString('en-IN')} using {methods.find(item => item.id === method)?.label}.</p><button onClick={confirm} className="w-full bg-[#9b4c4a] text-white rounded-xl py-3.5 mt-6 font-bold">Confirm contribution <CreditCard className="inline ml-2" size={16} /></button></div>}
    {stage === 'success' && <div className="p-8 text-center"><CheckCircle2 className="mx-auto text-[#3f8d72]" size={42} /><h3 className="serif text-2xl text-[#4b2635] mt-4">Contribution recorded.</h3><p className="text-sm text-[#907f7d] mt-2">Reference {reference}</p><button onClick={() => { setStage('choose'); setError('') }} className="mt-6 text-sm font-bold text-[#9b4c4a]">Make another payment</button></div>}
  </section>
}
