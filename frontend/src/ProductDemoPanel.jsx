import { useEffect, useState } from 'react'
import { Bell, TrendingDown, WalletCards } from 'lucide-react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'
const earnings = [420, 280, 650, 190, 780, 340, 520, 610, 220, 480, 760, 310, 590, 700]

async function postJson(path, body) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) throw new Error((await response.json()).error || 'Calculation unavailable')
  return response.json()
}

export function ProductDemoPanel({ notification }) {
  const [reserve, setReserve] = useState(null)
  const [repayment, setRepayment] = useState(null)
  const [offer, setOffer] = useState(null)
  const [earning, setEarning] = useState(850)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    Promise.all([
      postJson('/smoothing/reserve', { daily_earnings: earnings, amount_due: 500 }),
      postJson('/member/1/forecast', { daily_earnings: earnings }),
    ]).then(([smoothing, forecast]) => {
      if (active) setReserve({ ...smoothing, forecast })
    }).catch(() => { if (active) setError('Connect the backend to load the live reserve forecast.') })
    return () => { active = false }
  }, [])

  useEffect(() => {
    let active = true
    Promise.all([
      fetch(`${API_BASE_URL}/member/1/credit-offer`).then(response => {
        if (!response.ok) throw new Error('Credit offer unavailable')
        return response.json()
      }),
    ]).then(([creditOffer]) => {
      if (active) setOffer(creditOffer)
      return postJson('/repayment/simulate', {
        daily_earnings: [earning],
        loan_balance: creditOffer.eligible_amount,
        deduction_pct: 0.12,
      })
    }).then(result => { if (active) setRepayment(result.schedule[0]) })
      .catch(() => { if (active) setError('Connect the backend to run repayment calculations.') })
    return () => { active = false }
  }, [earning])

  return <section className="grid xl:grid-cols-[1.25fr_.75fr] gap-6 mt-6">
    <div className="bg-[#4b2635] rounded-2xl p-6 text-white">
      <div className="flex justify-between items-start gap-4"><div><p className="text-xs uppercase tracking-widest text-[#e4aa57] font-bold">C · Income smoothing</p><h2 className="serif text-2xl mt-2">A steadier month from uneven days.</h2></div><WalletCards className="text-[#e4aa57]" /></div>
      <div className="grid sm:grid-cols-3 gap-3 mt-7"><div><p className="text-xs text-white/55">Wallet balance</p><p className="serif text-2xl mt-1">₹{reserve?.days.at(-1)?.wallet_balance?.toLocaleString('en-IN') || '—'}</p></div><div><p className="text-xs text-white/55">Target date</p><p className="serif text-2xl mt-1">{reserve?.target_reached_date || 'Building'}</p></div><div><p className="text-xs text-white/55">Forecast</p><p className="serif text-2xl mt-1">{reserve?.forecast?.slow_period_predicted ? 'Slow' : 'Stable'}</p></div></div>
      <p className="text-sm text-white/65 mt-6">{reserve?.auto_payment ? `Auto-payment ready from ${reserve.auto_payment.source.replace('_', ' ')}.` : 'Reserve is accumulating toward the next contribution.'}</p>
    </div>
    <div className="bg-[#f1e4d5] rounded-2xl p-6 text-[#4b2635]"><div className="flex justify-between"><div><p className="text-xs uppercase tracking-widest text-[#9b4c4a] font-bold">C · Elastic repayment</p><h2 className="serif text-2xl mt-2">Pay with the day you had.</h2></div><TrendingDown className="text-[#9b4c4a]" /></div><p className="text-xs text-[#907f7d] mt-4">Live offer balance: ₹{offer?.eligible_amount?.toLocaleString('en-IN') || '—'}</p><label className="block text-sm font-bold mt-4" htmlFor="today-earnings">Today's earnings · ₹{earning}</label><input id="today-earnings" type="range" min="0" max="1800" step="50" value={earning} onChange={event => setEarning(Number(event.target.value))} className="w-full accent-[#9b4c4a] mt-4" /><div className="flex justify-between items-end mt-6"><span className="text-sm text-[#614b4a]">Today's deduction</span><b className="serif text-4xl text-[#9b4c4a]">₹{repayment?.deduction_amount ?? '—'}</b></div><p className="text-xs text-[#907f7d] mt-2">{repayment?.slow_period_predicted ? 'Reduced automatically for a slow period.' : 'Standard percentage of today\'s earnings.'}</p></div>
    <div className="xl:col-span-2 bg-white rounded-2xl p-5 shadow-soft"><div className="flex items-center gap-2"><Bell size={17} className="text-[#9b4c4a]" /><p className="text-xs uppercase tracking-widest text-[#9b4c4a] font-bold">WhatsApp-style notifications</p></div>{notification ? <div className="max-w-xl bg-[#e5f2e8] rounded-2xl rounded-tl-none p-4 mt-4 text-sm text-[#315c43]">{notification.message}<p className="text-[11px] mt-2 opacity-60">Live contribution event · {notification.source.replace('_', ' ')}</p></div> : <p className="text-sm text-[#907f7d] mt-4">Notifications appear here after a contribution is auto-paid from the wallet.</p>}{error && <p className="text-xs text-[#c65d4c] mt-4">{error}</p>}</div>
  </section>
}
