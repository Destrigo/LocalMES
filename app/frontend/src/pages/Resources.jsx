import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import api from '../utils/api'

function asList(data) {
  if (Array.isArray(data)) return data
  if (data?.items) return data.items
  return []
}

function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg">
        <div className="flex justify-between items-center border-b px-4 py-3">
          <h3 className="font-semibold text-slate-800">{title}</h3>
          <button type="button" onClick={onClose} className="text-slate-400 hover:text-slate-700">×</button>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <label className="block text-sm mb-3">
      <span className="text-slate-600">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  )
}

const inputCls = 'w-full border rounded-lg px-3 py-2 text-sm'

export function Dashboard() {
  const { t } = useTranslation()
  const [data, setData] = useState(null)
  useEffect(() => {
    api.get('/dashboard').then((r) => setData(r.data)).catch(() => toast.error('Dashboard error'))
  }, [])
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">{t('nav.dashboard')}</h1>
      {!data ? <p className="text-slate-400">{t('common.loading')}</p> : (
        <div className="grid md:grid-cols-3 gap-4">
          <div className="bg-white rounded-xl border p-4"><div className="text-sm text-slate-500">{t('dashboard.live')}</div><div className="text-3xl font-semibold">{data.live_instance_count}</div></div>
          <div className="bg-white rounded-xl border p-4"><div className="text-sm text-slate-500">{t('dashboard.openOrders')}</div><div className="text-3xl font-semibold">{data.open_production_orders}</div></div>
          <div className="bg-white rounded-xl border p-4"><div className="text-sm text-slate-500">{t('dashboard.lines')}</div><div className="text-3xl font-semibold">{data.lines?.length ?? 0}</div></div>
        </div>
      )}
    </div>
  )
}

function CrudList({ title, endpoint, columns, fields, createDefaults = {} }) {
  const { t } = useTranslation()
  const [rows, setRows] = useState([])
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(createDefaults)
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    api.get(endpoint).then((r) => setRows(asList(r.data))).catch(() => toast.error('Load failed')).finally(() => setLoading(false))
  }
  useEffect(load, [endpoint])

  const submit = async (e) => {
    e.preventDefault()
    try {
      const body = { ...form }
      for (const f of fields) {
        if (f.type === 'number') {
          if (body[f.key] === '' || body[f.key] == null) {
            if (!f.required) delete body[f.key]
          } else {
            body[f.key] = Number(body[f.key])
          }
        }
        if (f.type === 'checkbox') body[f.key] = !!body[f.key]
      }
      if (Array.isArray(body.compatible_line_ids) === false && body.compatible_line_ids == null) {
        body.compatible_line_ids = []
      }
      if (body.steps == null && endpoint === '/cycles') body.steps = []
      await api.post(endpoint, body)
      toast.success(t('common.saved'))
      setOpen(false)
      setForm(createDefaults)
      load()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error')
    }
  }

  const remove = async (id) => {
    if (!confirm(t('common.confirmDelete'))) return
    try {
      await api.delete(`${endpoint}/${id}`)
      toast.success(t('common.deleted'))
      load()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error')
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center gap-2">
        <h1 className="text-xl font-semibold">{title}</h1>
        <div className="flex gap-2">
          <button type="button" onClick={load} className="px-3 py-1.5 text-sm rounded-lg border">{t('common.refresh')}</button>
          <button type="button" onClick={() => setOpen(true)} className="px-3 py-1.5 text-sm rounded-lg bg-slate-900 text-white">{t('common.create')}</button>
        </div>
      </div>
      {loading ? <p className="text-slate-400">{t('common.loading')}</p> : rows.length === 0 ? <p className="text-slate-400">{t('common.empty')}</p> : (
        <div className="overflow-auto bg-white rounded-xl border">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-left"><tr>{columns.map((c) => <th key={c.key} className="px-3 py-2">{c.label}</th>)}<th className="px-3 py-2" /></tr></thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-t">
                  {columns.map((c) => <td key={c.key} className="px-3 py-2">{String(row[c.key] ?? '')}</td>)}
                  <td className="px-3 py-2 text-right">
                    {row.id != null && <button type="button" className="text-red-600 text-xs" onClick={() => remove(row.id)}>{t('common.delete')}</button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {open && (
        <Modal title={title} onClose={() => setOpen(false)}>
          <form onSubmit={submit} className="space-y-1">
            {fields.map((f) => (
              <Field key={f.key} label={f.label}>
                {f.type === 'checkbox' ? (
                  <input type="checkbox" checked={!!form[f.key]} onChange={(e) => setForm({ ...form, [f.key]: e.target.checked })} />
                ) : (
                  <input className={inputCls} type={f.type || 'text'} required={!!f.required} value={form[f.key] ?? ''} onChange={(e) => setForm({ ...form, [f.key]: e.target.value })} />
                )}
              </Field>
            ))}
            <button type="submit" className="w-full bg-slate-900 text-white rounded-lg py-2">{t('common.save')}</button>
          </form>
        </Modal>
      )}
    </div>
  )
}

export function Customers() {
  const { t } = useTranslation()
  return (
    <CrudList
      title={t('nav.customers')}
      endpoint="/customers"
      columns={[{ key: 'id', label: 'ID' }, { key: 'company_name', label: t('fields.company') }, { key: 'customer_code', label: t('fields.code') }, { key: 'email', label: 'Email' }, { key: 'active', label: t('fields.active') }]}
      fields={[{ key: 'company_name', label: t('fields.company'), required: true }, { key: 'customer_code', label: t('fields.code') }, { key: 'email', label: 'Email' }, { key: 'phone', label: t('fields.phone') }, { key: 'external_id', label: 'external_id' }, { key: 'active', label: t('fields.active'), type: 'checkbox' }]}
      createDefaults={{ company_name: '', customer_code: '', email: '', phone: '', external_id: '', active: true }}
    />
  )
}

export function Products() {
  const { t } = useTranslation()
  return (
    <CrudList
      title={t('nav.products')}
      endpoint="/products"
      columns={[{ key: 'id', label: 'ID' }, { key: 'code', label: t('fields.code') }, { key: 'description', label: t('fields.description') }, { key: 'customer_name', label: t('fields.customer') }, { key: 'cycle_id', label: 'Cycle' }]}
      fields={[{ key: 'code', label: t('fields.code'), required: true }, { key: 'description', label: t('fields.description'), required: true }, { key: 'customer_name', label: t('fields.customer'), required: true }, { key: 'cycle_id', label: 'cycle_id', type: 'number' }, { key: 'external_id', label: 'external_id' }]}
      createDefaults={{ code: '', description: '', customer_name: '', cycle_id: '', external_id: '' }}
    />
  )
}

export function Lines() {
  const { t } = useTranslation()
  const [groups, setGroups] = useState([])
  useEffect(() => { api.get('/line-groups').then((r) => setGroups(asList(r.data))) }, [])
  return (
    <div className="space-y-6">
      <CrudList
        title={t('nav.lineGroups')}
        endpoint="/line-groups"
        columns={[{ key: 'id', label: 'ID' }, { key: 'name', label: t('fields.name') }, { key: 'active', label: t('fields.active') }]}
        fields={[{ key: 'name', label: t('fields.name'), required: true }, { key: 'active', label: t('fields.active'), type: 'checkbox' }]}
        createDefaults={{ name: '', active: true }}
      />
      <CrudList
        title={t('nav.lines')}
        endpoint="/lines"
        columns={[{ key: 'id', label: 'ID' }, { key: 'name', label: t('fields.name') }, { key: 'group_id', label: 'Group' }, { key: 'active', label: t('fields.active') }]}
        fields={[{ key: 'name', label: t('fields.name'), required: true }, { key: 'group_id', label: `group_id (${groups.map((g) => `${g.id}:${g.name}`).join(', ')})`, type: 'number', required: true }, { key: 'active', label: t('fields.active'), type: 'checkbox' }]}
        createDefaults={{ name: '', group_id: groups[0]?.id || '', active: true }}
      />
      <CrudList
        title="Operations"
        endpoint="/operations"
        columns={[{ key: 'id', label: 'ID' }, { key: 'code', label: t('fields.code') }, { key: 'description', label: t('fields.description') }, { key: 'line_group_id', label: 'Group' }, { key: 'active', label: t('fields.active') }]}
        fields={[{ key: 'code', label: t('fields.code'), required: true }, { key: 'description', label: t('fields.description'), required: true }, { key: 'line_group_id', label: 'line_group_id', type: 'number', required: true }, { key: 'pieces_per_hour', label: 'pieces_per_hour', type: 'number' }, { key: 'active', label: t('fields.active'), type: 'checkbox' }]}
        createDefaults={{ code: '', description: '', line_group_id: groups[0]?.id || '', pieces_per_hour: '', active: true, compatible_line_ids: [] }}
      />
      <CrudList
        title="Downtime reasons"
        endpoint="/downtime-reasons"
        columns={[{ key: 'id', label: 'ID' }, { key: 'label', label: 'Label' }, { key: 'active', label: t('fields.active') }]}
        fields={[{ key: 'label', label: 'Label', required: true }, { key: 'active', label: t('fields.active'), type: 'checkbox' }]}
        createDefaults={{ label: '', active: true }}
      />
    </div>
  )
}

export function Cycles() {
  const { t } = useTranslation()
  return (
    <CrudList
      title={t('nav.cycles')}
      endpoint="/cycles"
      columns={[{ key: 'id', label: 'ID' }, { key: 'name', label: t('fields.name') }, { key: 'description', label: t('fields.description') }, { key: 'active', label: t('fields.active') }]}
      fields={[{ key: 'name', label: t('fields.name'), required: true }, { key: 'description', label: t('fields.description') }, { key: 'active', label: t('fields.active'), type: 'checkbox' }]}
      createDefaults={{ name: '', description: '', active: true, steps: [] }}
    />
  )
}

export function ProductionOrders() {
  const { t } = useTranslation()
  const nav = useNavigate()
  const [rows, setRows] = useState([])
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ order_number: '', customer_name: '', product_description: '', quantity_ordered: 1 })
  const load = () => api.get('/production-orders').then((r) => setRows(asList(r.data)))
  useEffect(() => { load() }, [])
  return (
    <div className="space-y-4">
      <div className="flex justify-between"><h1 className="text-xl font-semibold">{t('nav.productionOrders')}</h1>
        <button type="button" className="px-3 py-1.5 bg-slate-900 text-white rounded-lg text-sm" onClick={() => setOpen(true)}>{t('common.create')}</button></div>
      <div className="overflow-auto bg-white rounded-xl border">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left"><tr><th className="px-3 py-2">#</th><th className="px-3 py-2">{t('fields.customer')}</th><th className="px-3 py-2">{t('fields.description')}</th><th className="px-3 py-2">Qty</th><th className="px-3 py-2">{t('fields.status')}</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-t hover:bg-slate-50 cursor-pointer" onClick={() => nav(`/production-orders/${r.id}`)}>
                <td className="px-3 py-2">{r.order_number}</td><td className="px-3 py-2">{r.customer_name}</td><td className="px-3 py-2">{r.product_description}</td><td className="px-3 py-2">{r.quantity_ordered}</td><td className="px-3 py-2">{r.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {open && (
        <Modal title={t('nav.productionOrders')} onClose={() => setOpen(false)}>
          <form onSubmit={async (e) => {
            e.preventDefault()
            try {
              await api.post('/production-orders', { ...form, quantity_ordered: Number(form.quantity_ordered), operation_ids: [] })
              toast.success(t('common.saved')); setOpen(false); load()
            } catch (err) { toast.error(err.response?.data?.detail || 'Error') }
          }}>
            {['order_number', 'customer_name', 'product_description'].map((k) => (
              <Field key={k} label={k}><input className={inputCls} required value={form[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })} /></Field>
            ))}
            <Field label="quantity_ordered"><input className={inputCls} type="number" min={1} value={form.quantity_ordered} onChange={(e) => setForm({ ...form, quantity_ordered: e.target.value })} /></Field>
            <button className="w-full bg-slate-900 text-white rounded-lg py-2">{t('common.save')}</button>
          </form>
        </Modal>
      )}
    </div>
  )
}

export function WorkOrders() {
  const { t } = useTranslation()
  const nav = useNavigate()
  const [rows, setRows] = useState([])
  const [customers, setCustomers] = useState([])
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ customer_id: '', customer_reference: '', comment: '' })
  const load = () => api.get('/work-orders').then((r) => setRows(asList(r.data)))
  useEffect(() => {
    load()
    api.get('/customers').then((r) => setCustomers(asList(r.data)))
  }, [])
  return (
    <div className="space-y-4">
      <div className="flex justify-between"><h1 className="text-xl font-semibold">{t('nav.workOrders')}</h1>
        <button type="button" className="px-3 py-1.5 bg-slate-900 text-white rounded-lg text-sm" onClick={() => setOpen(true)}>{t('common.create')}</button></div>
      <div className="overflow-auto bg-white rounded-xl border">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left"><tr><th className="px-3 py-2">#</th><th className="px-3 py-2">Customer</th><th className="px-3 py-2">Ref</th><th className="px-3 py-2">{t('fields.status')}</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-t hover:bg-slate-50 cursor-pointer" onClick={() => nav(`/work-orders/${r.id}`)}>
                <td className="px-3 py-2">{r.sequence_number}</td><td className="px-3 py-2">{r.customer_id}</td><td className="px-3 py-2">{r.customer_reference}</td><td className="px-3 py-2">{r.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {open && (
        <Modal title={t('nav.workOrders')} onClose={() => setOpen(false)}>
          <form onSubmit={async (e) => {
            e.preventDefault()
            try {
              await api.post('/work-orders', { ...form, customer_id: Number(form.customer_id), lines: [] })
              toast.success(t('common.saved')); setOpen(false); load()
            } catch (err) { toast.error(err.response?.data?.detail || 'Error') }
          }}>
            <Field label={t('fields.customer')}>
              <select className={inputCls} required value={form.customer_id} onChange={(e) => setForm({ ...form, customer_id: e.target.value })}>
                <option value="">…</option>
                {customers.map((c) => <option key={c.id} value={c.id}>{c.company_name}</option>)}
              </select>
            </Field>
            <Field label="customer_reference"><input className={inputCls} value={form.customer_reference} onChange={(e) => setForm({ ...form, customer_reference: e.target.value })} /></Field>
            <Field label="comment"><input className={inputCls} value={form.comment} onChange={(e) => setForm({ ...form, comment: e.target.value })} /></Field>
            <button className="w-full bg-slate-900 text-white rounded-lg py-2">{t('common.save')}</button>
          </form>
        </Modal>
      )}
    </div>
  )
}

export function WorkOrderDetail() {
  const { id } = useParams()
  const { t } = useTranslation()
  const [wo, setWo] = useState(null)
  const [line, setLine] = useState({ description: '', quantity: 1, free_code: '' })
  const load = () => api.get(`/work-orders/${id}`).then((r) => setWo(r.data))
  useEffect(() => { load() }, [id])
  if (!wo) return <p>{t('common.loading')}</p>
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-semibold">WO #{wo.sequence_number} · {wo.status}</h1>
        <div className="flex gap-2">
          <button type="button" className="px-3 py-1.5 border rounded-lg text-sm" onClick={async () => {
            try { await api.patch(`/work-orders/${id}/status`, { status: 'confirmed' }); toast.success('OK'); load() } catch (e) { toast.error(e.response?.data?.detail || 'Error') }
          }}>Confirm</button>
          <button type="button" className="px-3 py-1.5 bg-emerald-700 text-white rounded-lg text-sm" onClick={async () => {
            try {
              const r = await api.post(`/work-orders/${id}/generate-production-orders`)
              toast.success(`Created: ${(r.data.created_production_order_ids || []).join(', ') || 'none'}`)
            } catch (e) { toast.error(e.response?.data?.detail || 'Error') }
          }}>{t('actions.generatePO')}</button>
        </div>
      </div>
      <div className="bg-white border rounded-xl p-4 text-sm space-y-1">
        <div>Customer ID: {wo.customer_id}</div>
        <div>Ref: {wo.customer_reference || '—'}</div>
        <div>Comment: {wo.comment || '—'}</div>
      </div>
      <h2 className="font-medium">{t('fields.lines')}</h2>
      <div className="bg-white border rounded-xl overflow-auto">
        <table className="min-w-full text-sm"><thead className="bg-slate-50"><tr><th className="px-3 py-2">ID</th><th className="px-3 py-2">{t('fields.description')}</th><th className="px-3 py-2">Qty</th><th className="px-3 py-2">Code</th></tr></thead>
          <tbody>{(wo.lines || []).map((l) => <tr key={l.id} className="border-t"><td className="px-3 py-2">{l.id}</td><td className="px-3 py-2">{l.description}</td><td className="px-3 py-2">{l.quantity}</td><td className="px-3 py-2">{l.free_code}</td></tr>)}</tbody>
        </table>
      </div>
      <form className="bg-white border rounded-xl p-4 grid md:grid-cols-4 gap-2 items-end" onSubmit={async (e) => {
        e.preventDefault()
        try {
          await api.post(`/work-orders/${id}/lines`, { ...line, quantity: Number(line.quantity), components: [] })
          toast.success(t('common.saved')); setLine({ description: '', quantity: 1, free_code: '' }); load()
        } catch (err) { toast.error(err.response?.data?.detail || 'Error') }
      }}>
        <Field label={t('fields.description')}><input className={inputCls} required value={line.description} onChange={(e) => setLine({ ...line, description: e.target.value })} /></Field>
        <Field label="Qty"><input className={inputCls} type="number" min={1} value={line.quantity} onChange={(e) => setLine({ ...line, quantity: e.target.value })} /></Field>
        <Field label="free_code"><input className={inputCls} value={line.free_code} onChange={(e) => setLine({ ...line, free_code: e.target.value })} /></Field>
        <button className="bg-slate-900 text-white rounded-lg py-2 text-sm h-10">{t('common.addLine')}</button>
      </form>
    </div>
  )
}

export function ProductionOrderDetail() {
  const { id } = useParams()
  const { t } = useTranslation()
  const [order, setOrder] = useState(null)
  useEffect(() => { api.get(`/production-orders/${id}`).then((r) => setOrder(r.data)) }, [id])
  if (!order) return <p>{t('common.loading')}</p>
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">{order.order_number}</h1>
      <div className="bg-white border rounded-xl p-4 text-sm space-y-1">
        <div>{order.customer_name}</div>
        <div>{order.product_description}</div>
        <div>Qty {order.quantity_ordered} · {order.status}</div>
      </div>
      <h2 className="font-medium">Timeline</h2>
      <ul className="bg-white border rounded-xl divide-y text-sm">
        {(order.timeline || []).map((e) => <li key={e.id} className="px-3 py-2">{e.timestamp} · {e.event_type} · {e.text}</li>)}
      </ul>
      <Link className="text-sm text-blue-700" to="/shop-floor">{t('nav.shopFloor')} →</Link>
    </div>
  )
}

export function ShopFloor() {
  const { t } = useTranslation()
  const [todo, setTodo] = useState([])
  const [live, setLive] = useState([])
  const [lines, setLines] = useState([])
  const [ops, setOps] = useState([])
  const [reasons, setReasons] = useState([])
  const [start, setStart] = useState(null)
  const [form, setForm] = useState({ line_id: '', operator_count: 1 })
  const [complete, setComplete] = useState(null)
  const [qty, setQty] = useState({ quantity_produced: 0, lot_code: '' })
  const [downtime, setDowntime] = useState(null)
  const [reasonId, setReasonId] = useState('')

  const opMap = useMemo(() => Object.fromEntries(ops.map((o) => [o.id, o])), [ops])

  const load = async () => {
    const [a, b, c, d, e] = await Promise.all([
      api.get('/operation-instances/todo'),
      api.get('/operation-instances'),
      api.get('/lines'),
      api.get('/operations'),
      api.get('/downtime-reasons'),
    ])
    setTodo(asList(a.data))
    setLive(asList(b.data).filter((i) => i.status === 'in_progress' || i.status === 'paused'))
    setLines(asList(c.data))
    setOps(asList(d.data))
    setReasons(asList(e.data))
  }
  useEffect(() => { load().catch(() => toast.error('Load failed')) }, [])

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-semibold">{t('nav.shopFloor')}</h1>
        <button type="button" className="px-3 py-1.5 border rounded-lg text-sm" onClick={load}>{t('common.refresh')}</button>
      </div>

      <section className="space-y-2">
        <h2 className="font-medium">{t('shopFloor.live')}</h2>
        {live.length === 0 ? <p className="text-slate-400 text-sm">{t('common.empty')}</p> : live.map((i) => (
          <div key={i.id} className="bg-white border rounded-xl p-4 flex flex-wrap gap-2 items-center justify-between">
            <div className="text-sm">#{i.id} · order {i.order_id} · {opMap[i.operation_id]?.code || i.operation_id} · line {i.line_id} · <b>{i.status}</b></div>
            <div className="flex gap-2">
              {i.status === 'in_progress' && <button type="button" className="px-2 py-1 text-xs border rounded" onClick={async () => { await api.post(`/operation-instances/${i.id}/pause`); load() }}>{t('shopFloor.pause')}</button>}
              {i.status === 'paused' && <button type="button" className="px-2 py-1 text-xs border rounded" onClick={async () => { await api.post(`/operation-instances/${i.id}/resume`); load() }}>{t('shopFloor.resume')}</button>}
              <button type="button" className="px-2 py-1 text-xs border rounded" onClick={() => { setDowntime(i); setReasonId(reasons[0]?.id || '') }}>{t('shopFloor.downtime')}</button>
              <button type="button" className="px-2 py-1 text-xs bg-emerald-700 text-white rounded" onClick={() => { setComplete(i); setQty({ quantity_produced: 0, lot_code: '' }) }}>{t('shopFloor.complete')}</button>
            </div>
          </div>
        ))}
      </section>

      <section className="space-y-2">
        <h2 className="font-medium">{t('shopFloor.todo')}</h2>
        {todo.length === 0 ? <p className="text-slate-400 text-sm">{t('common.empty')}</p> : todo.map((row) => (
          <div key={row.order.id} className="bg-white border rounded-xl p-4">
            <div className="font-medium text-sm mb-2">{row.order.order_number} · {row.order.customer_name} · {row.order.product_description}</div>
            <div className="flex flex-wrap gap-2">
              {(row.pending_operation_ids || []).map((oid) => (
                <button key={oid} type="button" className="px-3 py-1.5 text-xs bg-slate-900 text-white rounded-lg" onClick={() => {
                  setStart({ order_id: row.order.id, operation_id: oid })
                  setForm({ line_id: lines[0]?.id || '', operator_count: 1 })
                }}>
                  {t('shopFloor.start')} {opMap[oid]?.code || oid}
                </button>
              ))}
            </div>
          </div>
        ))}
      </section>

      {start && (
        <Modal title={t('shopFloor.start')} onClose={() => setStart(null)}>
          <form onSubmit={async (e) => {
            e.preventDefault()
            try {
              await api.post('/operation-instances/start', { ...start, line_id: Number(form.line_id), operator_count: Number(form.operator_count) })
              toast.success('OK'); setStart(null); load()
            } catch (err) { toast.error(err.response?.data?.detail || 'Error') }
          }}>
            <Field label={t('fields.line')}>
              <select className={inputCls} required value={form.line_id} onChange={(e) => setForm({ ...form, line_id: e.target.value })}>
                {lines.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
              </select>
            </Field>
            <Field label={t('fields.operators')}><input className={inputCls} type="number" min={1} value={form.operator_count} onChange={(e) => setForm({ ...form, operator_count: e.target.value })} /></Field>
            <button className="w-full bg-emerald-700 text-white rounded-lg py-2">{t('shopFloor.start')}</button>
          </form>
        </Modal>
      )}

      {complete && (
        <Modal title={t('shopFloor.complete')} onClose={() => setComplete(null)}>
          <form onSubmit={async (e) => {
            e.preventDefault()
            try {
              await api.post(`/operation-instances/${complete.id}/complete`, { quantity_produced: Number(qty.quantity_produced), lot_code: qty.lot_code || null })
              toast.success('OK'); setComplete(null); load()
            } catch (err) { toast.error(err.response?.data?.detail || 'Error') }
          }}>
            <Field label="quantity_produced"><input className={inputCls} type="number" min={0} value={qty.quantity_produced} onChange={(e) => setQty({ ...qty, quantity_produced: e.target.value })} /></Field>
            <Field label="lot_code"><input className={inputCls} value={qty.lot_code} onChange={(e) => setQty({ ...qty, lot_code: e.target.value })} /></Field>
            <button className="w-full bg-emerald-700 text-white rounded-lg py-2">{t('shopFloor.complete')}</button>
          </form>
        </Modal>
      )}

      {downtime && (
        <Modal title={t('shopFloor.downtime')} onClose={() => setDowntime(null)}>
          <form onSubmit={async (e) => {
            e.preventDefault()
            try {
              await api.post(`/operation-instances/${downtime.id}/downtimes`, { reason_id: Number(reasonId) })
              toast.success('OK'); setDowntime(null); load()
            } catch (err) { toast.error(err.response?.data?.detail || 'Error') }
          }}>
            <Field label={t('fields.reason')}>
              <select className={inputCls} value={reasonId} onChange={(e) => setReasonId(e.target.value)}>
                {reasons.map((r) => <option key={r.id} value={r.id}>{r.label}</option>)}
              </select>
            </Field>
            <button className="w-full bg-amber-600 text-white rounded-lg py-2">{t('common.save')}</button>
          </form>
        </Modal>
      )}
    </div>
  )
}

export function SettingsPage() {
  const { t } = useTranslation()
  const [settings, setSettings] = useState([])
  const [users, setUsers] = useState([])
  const [keys, setKeys] = useState([])
  const [backupDir, setBackupDir] = useState('')
  const [backupEnabled, setBackupEnabled] = useState(false)
  const [userForm, setUserForm] = useState({ username: '', password: '', role: 'operator' })
  const [keyForm, setKeyForm] = useState({ name: '', role: 'backoffice' })
  const [newKey, setNewKey] = useState('')

  const load = async () => {
    const [s, u, k] = await Promise.all([api.get('/settings'), api.get('/users'), api.get('/api-keys')])
    setSettings(asList(s.data))
    setUsers(asList(u.data))
    setKeys(asList(k.data))
    const map = Object.fromEntries(asList(s.data).map((x) => [x.key, x.value]))
    setBackupDir(map.backup_dir || '')
    setBackupEnabled(map.backup_enabled === 'true')
  }
  useEffect(() => { load().catch(() => toast.error('Settings require superadmin')) }, [])

  const saveSetting = async (key, value) => {
    await api.put(`/settings/${key}`, { value })
    toast.success(t('common.saved'))
    load()
  }

  const upload = async (path, file) => {
    const fd = new FormData()
    fd.append('file', file)
    await api.post(path, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    toast.success(t('common.saved'))
  }

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-semibold">{t('nav.settings')}</h1>

      <section className="bg-white border rounded-xl p-4 space-y-3">
        <h2 className="font-medium">{t('settings.backup')}</h2>
        <Field label="backup_dir"><input className={inputCls} value={backupDir} onChange={(e) => setBackupDir(e.target.value)} /></Field>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={backupEnabled} onChange={(e) => setBackupEnabled(e.target.checked)} /> backup_enabled</label>
        <div className="flex gap-2">
          <button type="button" className="px-3 py-1.5 bg-slate-900 text-white rounded-lg text-sm" onClick={async () => {
            await saveSetting('backup_dir', backupDir)
            await saveSetting('backup_enabled', backupEnabled ? 'true' : 'false')
          }}>{t('common.save')}</button>
          <button type="button" className="px-3 py-1.5 border rounded-lg text-sm" onClick={async () => {
            try { const r = await api.post('/settings/backup/run'); toast.success(r.data.path || 'OK') } catch (e) { toast.error(e.response?.data?.detail || 'Error') }
          }}>{t('settings.runBackup')}</button>
        </div>
      </section>

      <section className="bg-white border rounded-xl p-4 space-y-3">
        <h2 className="font-medium">{t('settings.imports')}</h2>
        {[['customers', '/imports/customers'], ['products', '/imports/products'], ['boms', '/imports/boms'], ['production-orders', '/imports/production-orders']].map(([label, path]) => (
          <Field key={path} label={label}>
            <input type="file" accept=".csv,.xlsx,.xlsm" onChange={(e) => e.target.files?.[0] && upload(path, e.target.files[0]).catch((err) => toast.error(err.response?.data?.detail || 'Error'))} />
          </Field>
        ))}
      </section>

      <section className="bg-white border rounded-xl p-4 space-y-3">
        <h2 className="font-medium">{t('settings.reports')}</h2>
        <div className="flex gap-2">
          <a className="px-3 py-1.5 border rounded-lg text-sm" href="/api/v1/reports/export-excel" target="_blank" rel="noreferrer">Excel</a>
          <a className="px-3 py-1.5 border rounded-lg text-sm" href="/api/v1/reports/export-pdf" target="_blank" rel="noreferrer">PDF</a>
        </div>
      </section>

      <section className="bg-white border rounded-xl p-4 space-y-3">
        <h2 className="font-medium">{t('settings.users')}</h2>
        <ul className="text-sm divide-y">{users.map((u) => <li key={u.id} className="py-1">{u.username} · {u.role} · {u.active ? 'active' : 'off'}</li>)}</ul>
        <form className="grid md:grid-cols-4 gap-2" onSubmit={async (e) => {
          e.preventDefault()
          try { await api.post('/users', userForm); toast.success('OK'); setUserForm({ username: '', password: '', role: 'operator' }); load() } catch (err) { toast.error(err.response?.data?.detail || 'Error') }
        }}>
          <input className={inputCls} placeholder="username" required value={userForm.username} onChange={(e) => setUserForm({ ...userForm, username: e.target.value })} />
          <input className={inputCls} placeholder="password" type="password" required value={userForm.password} onChange={(e) => setUserForm({ ...userForm, password: e.target.value })} />
          <select className={inputCls} value={userForm.role} onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}>
            <option value="operator">operator</option><option value="backoffice">backoffice</option><option value="superadmin">superadmin</option>
          </select>
          <button className="bg-slate-900 text-white rounded-lg text-sm">{t('common.create')}</button>
        </form>
      </section>

      <section className="bg-white border rounded-xl p-4 space-y-3">
        <h2 className="font-medium">API keys</h2>
        <ul className="text-sm divide-y">{keys.map((k) => <li key={k.id} className="py-1">{k.name} · {k.role} · {k.active ? 'active' : 'off'}</li>)}</ul>
        {newKey && <p className="text-xs bg-amber-50 border border-amber-200 rounded p-2 break-all">Copy now: {newKey}</p>}
        <form className="grid md:grid-cols-3 gap-2" onSubmit={async (e) => {
          e.preventDefault()
          try {
            const r = await api.post('/api-keys', keyForm)
            setNewKey(r.data.key)
            toast.success('OK'); load()
          } catch (err) { toast.error(err.response?.data?.detail || 'Error') }
        }}>
          <input className={inputCls} placeholder="name" required value={keyForm.name} onChange={(e) => setKeyForm({ ...keyForm, name: e.target.value })} />
          <select className={inputCls} value={keyForm.role} onChange={(e) => setKeyForm({ ...keyForm, role: e.target.value })}>
            <option value="backoffice">backoffice</option><option value="operator">operator</option><option value="superadmin">superadmin</option>
          </select>
          <button className="bg-slate-900 text-white rounded-lg text-sm">{t('common.create')}</button>
        </form>
      </section>

      <section className="bg-white border rounded-xl p-4">
        <h2 className="font-medium mb-2">Raw settings</h2>
        <pre className="text-xs overflow-auto">{JSON.stringify(settings, null, 2)}</pre>
      </section>
    </div>
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
      {!data ? <p>Loading…</p> : (
        <div className="grid md:grid-cols-2 gap-4">
          {(data.lines || []).map((line) => (
            <div key={line.id} className="border border-slate-700 rounded-xl p-4">
              <div className="text-xl font-medium mb-2">{line.name}</div>
              {(line.active_instances || []).length === 0 ? <div className="text-slate-400">Idle</div> : line.active_instances.map((i) => (
                <div key={i.id} className="text-sm text-emerald-300">Order #{i.order_id} · op {i.operation_id} · {i.status}</div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
