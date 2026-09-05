import { useState } from 'react'
import PaymentCenter from './PaymentCenter'
import { ProductDemoPanel } from './ProductDemoPanel'

export default function MemberProductArea() {
  const [notification, setNotification] = useState(null)
  return <div className="px-5 md:px-10 pb-10 mt-6 space-y-6">
    <PaymentCenter onAutoPayment={setNotification} />
    <ProductDemoPanel notification={notification} />
  </div>
}
