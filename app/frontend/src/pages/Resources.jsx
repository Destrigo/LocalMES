import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import api from '../utils/api'

function ResourcePage({ title, endpoint, columns }) {
  const { t } = useTranslation()
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    api.get(endpoint)
      .then((r) => setRows(Array.isArray(r.data) ? r.data : []))
      .catch(() => setRows([]))
      .finally(() => setLoading(false))
  }

  useEffect(load, [endpoint])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-800">{title}</h1>
        <button type="button" onClick={load} className="text-sm px-3 py-1.5 rounded-lg bg-slate-800 text-white">
          {t('common.refresh')}
        </button>
      </div>
      {loading ? (
        <p className="text-slate-400">{t('common.loading')}</p>
      ) : rows.length === 0 ? (
        <p className="text-slate-400">{t('common.empty')}</p>
      ) : (
        <div className="overflow-auto bg-white rounded-xl border">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-left">
              <tr>
                {columns.map((c) => (
                  <th key={c.key} className="px-3 py-2 font-medium text-slate-600">{c.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id ?? JSON.stringify(row)} className="border-t">
                  {columns.map((c) => (
                    <td key={c.key} className="px-3 py-2 text-slate-700">
                      {String(row[c.key] ?? '')}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export function Dashboard() {
  const { t } = useTranslation()
  const [data, setData] = useState(null)
  useEffect(() => {
    api.get('/dashboard').then((r) => setData(r.data)).catch(() => setData(null))
  }, [])
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">{t('nav.dashboard')}</h1>
      {!data ? (
        <p className="text-slate-400">{t('common.loading')}</p>
      ) : (
        <div className="grid md:grid-cols-3 gap-4">
          <div className="bg-white rounded-xl border p-4">
            <div className="text-slate-500 text-sm">Live instances</div>
            <div className="text-3xl font-semibold">{data.live_instance_count}</div>
          </div>
          <div className="bg-white rounded-xl border p-4">
            <div className="text-slate-500 text-sm">Open production orders</div>
            <div className="text-3xl font-semibold">{data.open_production_orders}</div>
          </div>
          <div className="bg-white rounded-xl border p-4">
            <div className="text-slate-500 text-sm">Active lines</div>
            <div className="text-3xl font-semibold">{data.lines?.length ?? 0}</div>
          </div>
        </div>
      )}
    </div>
  )
}

export function Customers() {
  const { t } = useTranslation()
  return (
    <ResourcePage
      title={t('nav.customers')}
      endpoint="/customers"
      columns={[
        { key: 'id', label: 'ID' },
        { key: 'company_name', label: 'Company' },
        { key: 'customer_code', label: 'Code' },
        { key: 'email', label: 'Email' },
        { key: 'active', label: 'Active' },
      ]}
    />
  )
}

export function WorkOrders() {
  const { t } = useTranslation()
  return (
    <ResourcePage
      title={t('nav.workOrders')}
      endpoint="/work-orders"
      columns={[
        { key: 'id', label: 'ID' },
        { key: 'sequence_number', label: '#' },
        { key: 'customer_id', label: 'Customer' },
        { key: 'status', label: 'Status' },
        { key: 'customer_reference', label: 'Reference' },
      ]}
    />
  )
}

export function ProductionOrders() {
  const { t } = useTranslation()
  return (
    <ResourcePage
      title={t('nav.productionOrders')}
      endpoint="/production-orders"
      columns={[
        { key: 'id', label: 'ID' },
        { key: 'order_number', label: 'Number' },
        { key: 'customer_name', label: 'Customer' },
        { key: 'product_description', label: 'Product' },
        { key: 'quantity_ordered', label: 'Qty' },
        { key: 'status', label: 'Status' },
      ]}
    />
  )
}

export function Products() {
  const { t } = useTranslation()
  return (
    <ResourcePage
      title={t('nav.products')}
      endpoint="/products"
      columns={[
        { key: 'id', label: 'ID' },
        { key: 'code', label: 'Code' },
        { key: 'description', label: 'Description' },
        { key: 'customer_name', label: 'Customer' },
        { key: 'cycle_id', label: 'Cycle' },
      ]}
    />
  )
}

export function Cycles() {
  const { t } = useTranslation()
  return (
    <ResourcePage
      title={t('nav.cycles')}
      endpoint="/cycles"
      columns={[
        { key: 'id', label: 'ID' },
        { key: 'name', label: 'Name' },
        { key: 'description', label: 'Description' },
        { key: 'active', label: 'Active' },
      ]}
    />
  )
}

export function Lines() {
  const { t } = useTranslation()
  return (
    <ResourcePage
      title={t('nav.lines')}
      endpoint="/lines"
      columns={[
        { key: 'id', label: 'ID' },
        { key: 'name', label: 'Name' },
        { key: 'group_id', label: 'Group' },
        { key: 'active', label: 'Active' },
      ]}
    />
  )
}

export function ShopFloor() {
  const { t } = useTranslation()
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    api.get('/operation-instances/todo')
      .then((r) => setRows(r.data || []))
      .catch(() => setRows([]))
      .finally(() => setLoading(false))
  }, [])
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">{t('nav.shopFloor')}</h1>
      {loading ? (
        <p className="text-slate-400">{t('common.loading')}</p>
      ) : rows.length === 0 ? (
        <p className="text-slate-400">{t('common.empty')}</p>
      ) : (
        <div className="overflow-auto bg-white rounded-xl border">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-left">
              <tr>
                <th className="px-3 py-2">Order</th>
                <th className="px-3 py-2">Customer</th>
                <th className="px-3 py-2">Product</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Pending ops</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => (
                <tr key={row.order?.id ?? idx} className="border-t">
                  <td className="px-3 py-2">{row.order?.order_number}</td>
                  <td className="px-3 py-2">{row.order?.customer_name}</td>
                  <td className="px-3 py-2">{row.order?.product_description}</td>
                  <td className="px-3 py-2">{row.order?.status}</td>
                  <td className="px-3 py-2">{(row.pending_operation_ids || []).join(', ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export function SettingsPage() {
  const { t } = useTranslation()
  return (
    <ResourcePage
      title={t('nav.settings')}
      endpoint="/settings"
      columns={[
        { key: 'key', label: 'Key' },
        { key: 'value', label: 'Value' },
      ]}
    />
  )
}

export function Signage() {
  const [data, setData] = useState(null)
  useEffect(() => {
    const load = () => api.get('/dashboard').then((r) => setData(r.data)).catch(() => {})
    load()
    const id = setInterval(load, 5000)
    return () => clearInterval(id)
  }, [])
  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      <h1 className="text-3xl font-semibold mb-6">LocalMES Signage</h1>
      {!data ? (
        <p>Loading…</p>
      ) : (
        <div className="grid md:grid-cols-2 gap-4">
          {(data.lines || []).map((line) => (
            <div key={line.id} className="border border-slate-700 rounded-xl p-4">
              <div className="text-xl font-medium mb-2">{line.name}</div>
              {(line.active_instances || []).length === 0 ? (
                <div className="text-slate-400">Idle</div>
              ) : (
                line.active_instances.map((i) => (
                  <div key={i.id} className="text-sm text-emerald-300">
                    Order #{i.order_id} · op {i.operation_id} · {i.status}
                  </div>
                ))
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
