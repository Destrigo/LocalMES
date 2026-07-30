import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import api, { downloadFile } from '../utils/api'
import { asList, CrudList, CustomFieldsEditor, Field, inputCls, Modal, useFieldDefinitions } from './ui'

export function Dashboard() {
  const { t } = useTranslation()
  const [data, setData] = useState(null)
  useEffect(() => {
    api.get('/dashboard').then((r) => setData(r.data)).catch(() => toast.error(t('common.error')))
  }, [t])
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">{t('nav.dashboard')}</h1>
      {!data ? <p className="text-slate-400">{t('common.loading')}</p> : (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white rounded-xl border p-4"><div className="text-sm text-slate-500">{t('dashboard.live')}</div><div className="text-3xl font-semibold">{data.live_instance_count}</div></div>
          <div className="bg-white rounded-xl border p-4"><div className="text-sm text-slate-500">{t('dashboard.openOrders')}</div><div className="text-3xl font-semibold">{data.open_production_orders}</div></div>
          <div className="bg-white rounded-xl border p-4"><div className="text-sm text-slate-500">{t('dashboard.lines')}</div><div className="text-3xl font-semibold">{data.lines?.length ?? 0}</div></div>
        </div>
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
      customEntity="customer"
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
      customEntity="product"
      columns={[{ key: 'id', label: 'ID' }, { key: 'code', label: t('fields.code') }, { key: 'description', label: t('fields.description') }, { key: 'customer_name', label: t('fields.customer') }, { key: 'cycle_id', label: 'Cycle' }]}
      fields={[{ key: 'code', label: t('fields.code'), required: true }, { key: 'description', label: t('fields.description'), required: true }, { key: 'customer_name', label: t('fields.customer'), required: true }, { key: 'cycle_id', label: 'cycle_id', type: 'number' }, { key: 'external_id', label: 'external_id' }]}
      createDefaults={{ code: '', description: '', customer_name: '', cycle_id: '', external_id: '' }}
    />
  )
}

export function Lines() {
  const { t } = useTranslation()
  const [groups, setGroups] = useState([])
  const [lines, setLines] = useState([])
  useEffect(() => {
    api.get('/line-groups').then((r) => setGroups(asList(r.data)))
    api.get('/lines').then((r) => setLines(asList(r.data)))
  }, [])
  const groupOpts = groups.map((g) => ({ value: g.id, label: g.name }))
  return (
    <div className="space-y-8">
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
        fields={[
          { key: 'name', label: t('fields.name'), required: true },
          { key: 'group_id', label: t('fields.group'), type: 'select', required: true, options: groupOpts },
          { key: 'active', label: t('fields.active'), type: 'checkbox' },
        ]}
        createDefaults={{ name: '', group_id: groups[0]?.id || '', active: true }}
      />
      <CrudList
        title={t('nav.operations')}
        endpoint="/operations"
        columns={[{ key: 'id', label: 'ID' }, { key: 'code', label: t('fields.code') }, { key: 'description', label: t('fields.description') }, { key: 'line_group_id', label: 'Group' }, { key: 'active', label: t('fields.active') }]}
        fields={[
          { key: 'code', label: t('fields.code'), required: true },
          { key: 'description', label: t('fields.description'), required: true },
          { key: 'line_group_id', label: t('fields.group'), type: 'select', required: true, options: groupOpts },
          { key: 'pieces_per_hour', label: 'pieces_per_hour', type: 'number' },
          { key: 'active', label: t('fields.active'), type: 'checkbox' },
        ]}
        createDefaults={{ code: '', description: '', line_group_id: groups[0]?.id || '', pieces_per_hour: '', active: true, compatible_line_ids: lines.map((l) => l.id) }}
      />
      <CrudList
        title={t('nav.downtimeReasons')}
        endpoint="/downtime-reasons"
        columns={[{ key: 'id', label: 'ID' }, { key: 'label', label: t('fields.reason') }, { key: 'active', label: t('fields.active') }]}
        fields={[{ key: 'label', label: t('fields.reason'), required: true }, { key: 'active', label: t('fields.active'), type: 'checkbox' }]}
        createDefaults={{ label: '', active: true }}
      />
    </div>
  )
}

export function Cycles() {
  const { t } = useTranslation()
  const [cycles, setCycles] = useState([])
  const [ops, setOps] = useState([])
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState({ name: '', description: '', active: true, steps: [] })

  const load = () => {
    api.get('/cycles').then((r) => setCycles(asList(r.data)))
    api.get('/operations').then((r) => setOps(asList(r.data)))
  }
  useEffect(load, [])

  const opLabel = (id) => {
    const o = ops.find((x) => x.id === id)
    return o ? `${o.code} — ${o.description}` : id
  }

  const openCreate = () => {
    setEditing(null)
    setForm({ name: '', description: '', active: true, steps: [] })
    setOpen(true)
  }

  const openEdit = (c) => {
    setEditing(c)
    setForm({
      name: c.name,
      description: c.description || '',
      active: c.active,
      steps: (c.steps || []).map((s) => ({ operation_id: s.operation_id, position: s.position })),
    })
    setOpen(true)
  }

  const addStep = () => {
    const first = ops[0]?.id
    if (!first) return toast.error(t('cycles.needOps'))
    setForm({
      ...form,
      steps: [...form.steps, { operation_id: first, position: form.steps.length + 1 }],
    })
  }

  const save = async (e) => {
    e.preventDefault()
    if (!form.name.trim()) return toast.error(t('common.error'))
    const payload = {
      name: form.name.trim(),
      description: form.description || null,
      active: !!form.active,
      steps: form.steps.map((s, i) => ({
        operation_id: Number(s.operation_id),
        position: Number(s.position) || i + 1,
      })),
    }
    try {
      if (editing) await api.patch(`/cycles/${editing.id}`, payload)
      else await api.post('/cycles', payload)
      toast.success(t('common.saved'))
      setOpen(false)
      load()
    } catch (err) {
      toast.error(err.response?.data?.detail || t('common.error'))
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center gap-2">
        <h1 className="text-xl font-semibold">{t('nav.cycles')}</h1>
        <button type="button" className="px-3 py-2 bg-slate-900 text-white rounded-lg text-sm min-h-11" onClick={openCreate}>{t('common.create')}</button>
      </div>
      <div className="space-y-3">
        {cycles.map((c) => (
          <div key={c.id} className="bg-white border rounded-xl p-4">
            <div className="flex justify-between gap-2 items-start">
              <div>
                <div className="font-medium">{c.name}</div>
                <div className="text-sm text-slate-500">{c.description || '—'}</div>
                <ol className="mt-2 text-sm list-decimal list-inside space-y-1">
                  {(c.steps || []).sort((a, b) => a.position - b.position).map((s) => (
                    <li key={s.id}>{opLabel(s.operation_id)}</li>
                  ))}
                </ol>
              </div>
              <div className="flex gap-2">
                <button type="button" className="text-blue-700 text-sm font-medium" onClick={() => openEdit(c)}>{t('common.edit')}</button>
                <button type="button" className="text-red-600 text-sm" onClick={async () => {
                  if (!confirm(t('common.confirmDelete'))) return
                  await api.delete(`/cycles/${c.id}`); load()
                }}>{t('common.delete')}</button>
              </div>
            </div>
          </div>
        ))}
        {cycles.length === 0 && <p className="text-slate-400">{t('common.empty')}</p>}
      </div>

      {open && (
        <Modal title={editing ? t('common.edit') : t('common.create')} onClose={() => setOpen(false)} wide>
          <form onSubmit={save} className="space-y-3">
            <Field label={t('fields.name')}><input className={inputCls} required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></Field>
            <Field label={t('fields.description')}><input className={inputCls} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></Field>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.active} onChange={(e) => setForm({ ...form, active: e.target.checked })} /> {t('fields.active')}</label>
            <div className="border rounded-lg p-3 space-y-2">
              <div className="flex justify-between items-center">
                <span className="font-medium text-sm">{t('cycles.steps')}</span>
                <button type="button" className="text-sm text-blue-700" onClick={addStep}>{t('cycles.addStep')}</button>
              </div>
              {form.steps.map((s, idx) => (
                <div key={idx} className="flex flex-col sm:flex-row gap-2">
                  <select className={inputCls} value={s.operation_id} onChange={(e) => {
                    const steps = [...form.steps]
                    steps[idx] = { ...steps[idx], operation_id: Number(e.target.value) }
                    setForm({ ...form, steps })
                  }}>
                    {ops.map((o) => <option key={o.id} value={o.id}>{o.code} — {o.description}</option>)}
                  </select>
                  <input className={`${inputCls} sm:w-24`} type="number" min={1} value={s.position} onChange={(e) => {
                    const steps = [...form.steps]
                    steps[idx] = { ...steps[idx], position: Number(e.target.value) }
                    setForm({ ...form, steps })
                  }} />
                  <button type="button" className="text-red-600 text-sm px-2" onClick={() => setForm({ ...form, steps: form.steps.filter((_, i) => i !== idx) })}>{t('common.delete')}</button>
                </div>
              ))}
            </div>
            <button type="submit" className="w-full bg-slate-900 text-white rounded-lg py-3 min-h-12">{t('common.save')}</button>
          </form>
        </Modal>
      )}
    </div>
  )
}

export function ProductionOrders() {
  const { t } = useTranslation()
  const nav = useNavigate()
  const defs = useFieldDefinitions('production_order')
  const [rows, setRows] = useState([])
  const [q, setQ] = useState('')
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ order_number: '', customer_name: '', product_description: '', quantity_ordered: 1, custom_fields: {} })
  const load = () => api.get('/production-orders').then((r) => setRows(asList(r.data)))
  useEffect(() => { load() }, [])
  const filtered = rows.filter((r) => {
    const s = q.toLowerCase()
    if (!s) return true
    return [r.order_number, r.customer_name, r.product_description, r.status].join(' ').toLowerCase().includes(s)
  })
  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row justify-between gap-2">
        <h1 className="text-xl font-semibold">{t('nav.productionOrders')}</h1>
        <div className="flex gap-2">
          <input className={`${inputCls} sm:w-48`} placeholder={t('common.search')} value={q} onChange={(e) => setQ(e.target.value)} />
          <button type="button" className="px-3 py-2 bg-slate-900 text-white rounded-lg text-sm min-h-11" onClick={() => { setForm({ order_number: '', customer_name: '', product_description: '', quantity_ordered: 1, custom_fields: {} }); setOpen(true) }}>{t('common.create')}</button>
        </div>
      </div>
      <div className="overflow-auto bg-white rounded-xl border">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left"><tr><th className="px-3 py-3">#</th><th className="px-3 py-3">{t('fields.customer')}</th><th className="px-3 py-3">{t('fields.description')}</th><th className="px-3 py-3">Qty</th><th className="px-3 py-3">{t('fields.status')}</th></tr></thead>
          <tbody>
            {filtered.map((r) => (
              <tr key={r.id} className="border-t hover:bg-slate-50 cursor-pointer" onClick={() => nav(`/production-orders/${r.id}`)}>
                <td className="px-3 py-3">{r.order_number}</td><td className="px-3 py-3">{r.customer_name}</td><td className="px-3 py-3">{r.product_description}</td><td className="px-3 py-3">{r.quantity_ordered}</td><td className="px-3 py-3">{r.status}</td>
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
            } catch (err) { toast.error(err.response?.data?.detail || t('common.error')) }
          }}>
            {['order_number', 'customer_name', 'product_description'].map((k) => (
              <Field key={k} label={k}><input className={inputCls} required value={form[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })} /></Field>
            ))}
            <Field label="quantity_ordered"><input className={inputCls} type="number" min={1} value={form.quantity_ordered} onChange={(e) => setForm({ ...form, quantity_ordered: e.target.value })} /></Field>
            <CustomFieldsEditor defs={defs} values={form.custom_fields || {}} onChange={(custom_fields) => setForm({ ...form, custom_fields })} />
            <button className="w-full bg-slate-900 text-white rounded-lg py-3 min-h-12">{t('common.save')}</button>
          </form>
        </Modal>
      )}
    </div>
  )
}

export function WorkOrders() {
  const { t } = useTranslation()
  const nav = useNavigate()
  const defs = useFieldDefinitions('work_order')
  const [rows, setRows] = useState([])
  const [customers, setCustomers] = useState([])
  const [q, setQ] = useState('')
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ customer_id: '', customer_reference: '', comment: '', custom_fields: {} })
  const load = () => api.get('/work-orders').then((r) => setRows(asList(r.data)))
  useEffect(() => {
    load()
    api.get('/customers').then((r) => setCustomers(asList(r.data)))
  }, [])
  const filtered = rows.filter((r) => {
    const s = q.toLowerCase()
    if (!s) return true
    return [r.sequence_number, r.customer_name, r.customer_reference, r.status].join(' ').toLowerCase().includes(s)
  })
  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row justify-between gap-2">
        <h1 className="text-xl font-semibold">{t('nav.workOrders')}</h1>
        <div className="flex gap-2">
          <input className={`${inputCls} sm:w-48`} placeholder={t('common.search')} value={q} onChange={(e) => setQ(e.target.value)} />
          <button type="button" className="px-3 py-2 bg-slate-900 text-white rounded-lg text-sm min-h-11" onClick={() => { setForm({ customer_id: '', customer_reference: '', comment: '', custom_fields: {} }); setOpen(true) }}>{t('common.create')}</button>
        </div>
      </div>
      <div className="overflow-auto bg-white rounded-xl border">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left"><tr><th className="px-3 py-3">#</th><th className="px-3 py-3">{t('fields.customer')}</th><th className="px-3 py-3">Ref</th><th className="px-3 py-3">{t('fields.status')}</th></tr></thead>
          <tbody>
            {filtered.map((r) => (
              <tr key={r.id} className="border-t hover:bg-slate-50 cursor-pointer" onClick={() => nav(`/work-orders/${r.id}`)}>
                <td className="px-3 py-3">{r.sequence_number}</td>
                <td className="px-3 py-3">{r.customer_name || r.customer_id}</td>
                <td className="px-3 py-3">{r.customer_reference}</td>
                <td className="px-3 py-3">{r.status}</td>
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
            } catch (err) { toast.error(err.response?.data?.detail || t('common.error')) }
          }}>
            <Field label={t('fields.customer')}>
              <select className={inputCls} required value={form.customer_id} onChange={(e) => setForm({ ...form, customer_id: e.target.value })}>
                <option value="">…</option>
                {customers.map((c) => <option key={c.id} value={c.id}>{c.company_name}</option>)}
              </select>
            </Field>
            <Field label="customer_reference"><input className={inputCls} value={form.customer_reference} onChange={(e) => setForm({ ...form, customer_reference: e.target.value })} /></Field>
            <Field label="comment"><input className={inputCls} value={form.comment} onChange={(e) => setForm({ ...form, comment: e.target.value })} /></Field>
            <CustomFieldsEditor defs={defs} values={form.custom_fields || {}} onChange={(custom_fields) => setForm({ ...form, custom_fields })} />
            <button className="w-full bg-slate-900 text-white rounded-lg py-3 min-h-12">{t('common.save')}</button>
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
  const [comp, setComp] = useState({ line_id: '', code: '', description: '', quantity: '1' })

  const load = () => api.get(`/work-orders/${id}`).then((r) => setWo(r.data))
  useEffect(() => { load() }, [id])
  if (!wo) return <p>{t('common.loading')}</p>

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row justify-between gap-2 items-start">
        <div>
          <h1 className="text-xl font-semibold">WO #{wo.sequence_number} · {wo.status}</h1>
          <p className="text-sm text-slate-500">{wo.customer_name || `Customer #${wo.customer_id}`}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="px-3 py-2 border rounded-lg text-sm min-h-11" onClick={async () => {
            try { await api.patch(`/work-orders/${id}/status`, { status: 'confirmed' }); toast.success(t('common.saved')); load() } catch (e) { toast.error(e.response?.data?.detail || t('common.error')) }
          }}>{t('actions.confirm')}</button>
          <button type="button" className="px-3 py-2 bg-emerald-700 text-white rounded-lg text-sm min-h-11" onClick={async () => {
            try {
              const r = await api.post(`/work-orders/${id}/generate-production-orders`)
              toast.success(`PO: ${(r.data.created_production_order_ids || []).join(', ') || '—'}`)
            } catch (e) { toast.error(e.response?.data?.detail || t('common.error')) }
          }}>{t('actions.generatePO')}</button>
        </div>
      </div>

      <div className="bg-white border rounded-xl p-4 text-sm space-y-1">
        <div>Ref: {wo.customer_reference || '—'}</div>
        <div>Comment: {wo.comment || '—'}</div>
      </div>

      <h2 className="font-medium">{t('fields.lines')}</h2>
      <div className="space-y-3">
        {(wo.lines || []).map((l) => (
          <div key={l.id} className="bg-white border rounded-xl p-4">
            <div className="font-medium text-sm">{l.description} · qty {l.quantity} · {l.free_code || '—'}</div>
            <ul className="mt-2 text-sm text-slate-600 space-y-1">
              {(l.components || []).map((c) => (
                <li key={c.id} className="flex justify-between gap-2">
                  <span>{c.code || '—'} {c.description} × {c.quantity}</span>
                  <button type="button" className="text-red-600 text-xs" onClick={async () => {
                    await api.delete(`/work-orders/${id}/lines/${l.id}/components/${c.id}`); load()
                  }}>{t('common.delete')}</button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <form className="bg-white border rounded-xl p-4 grid sm:grid-cols-4 gap-2 items-end" onSubmit={async (e) => {
        e.preventDefault()
        try {
          await api.post(`/work-orders/${id}/lines`, { ...line, quantity: Number(line.quantity), components: [] })
          toast.success(t('common.saved')); setLine({ description: '', quantity: 1, free_code: '' }); load()
        } catch (err) { toast.error(err.response?.data?.detail || t('common.error')) }
      }}>
        <Field label={t('fields.description')}><input className={inputCls} required value={line.description} onChange={(e) => setLine({ ...line, description: e.target.value })} /></Field>
        <Field label="Qty"><input className={inputCls} type="number" min={1} value={line.quantity} onChange={(e) => setLine({ ...line, quantity: e.target.value })} /></Field>
        <Field label="free_code"><input className={inputCls} value={line.free_code} onChange={(e) => setLine({ ...line, free_code: e.target.value })} /></Field>
        <button className="bg-slate-900 text-white rounded-lg py-2.5 text-sm min-h-11">{t('common.addLine')}</button>
      </form>

      <form className="bg-white border rounded-xl p-4 grid sm:grid-cols-5 gap-2 items-end" onSubmit={async (e) => {
        e.preventDefault()
        try {
          await api.post(`/work-orders/${id}/lines/${comp.line_id}/components`, {
            code: comp.code || null,
            description: comp.description,
            quantity: comp.quantity,
          })
          toast.success(t('common.saved'))
          setComp({ line_id: '', code: '', description: '', quantity: '1' })
          load()
        } catch (err) { toast.error(err.response?.data?.detail || t('common.error')) }
      }}>
        <Field label={t('fields.line')}>
          <select className={inputCls} required value={comp.line_id} onChange={(e) => setComp({ ...comp, line_id: e.target.value })}>
            <option value="">…</option>
            {(wo.lines || []).map((l) => <option key={l.id} value={l.id}>#{l.id} {l.description}</option>)}
          </select>
        </Field>
        <Field label={t('fields.code')}><input className={inputCls} value={comp.code} onChange={(e) => setComp({ ...comp, code: e.target.value })} /></Field>
        <Field label={t('fields.description')}><input className={inputCls} required value={comp.description} onChange={(e) => setComp({ ...comp, description: e.target.value })} /></Field>
        <Field label="Qty"><input className={inputCls} required value={comp.quantity} onChange={(e) => setComp({ ...comp, quantity: e.target.value })} /></Field>
        <button className="bg-slate-900 text-white rounded-lg py-2.5 text-sm min-h-11">{t('actions.addComponent')}</button>
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
      <Link className="inline-block text-sm text-blue-700 font-medium py-2" to="/shop-floor">{t('nav.shopFloor')} →</Link>
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
  const [opsModal, setOpsModal] = useState(null)
  const [opCount, setOpCount] = useState(1)

  const opMap = useMemo(() => Object.fromEntries(ops.map((o) => [o.id, o])), [ops])

  const compatibleLines = (operationId) => {
    const op = opMap[operationId]
    if (!op) return lines.filter((l) => l.active)
    const ids = op.compatible_line_ids || []
    if (ids.length) return lines.filter((l) => l.active && ids.includes(l.id))
    return lines.filter((l) => l.active && l.group_id === op.line_group_id)
  }

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
  useEffect(() => { load().catch(() => toast.error(t('common.loadFailed'))) }, [t])

  const openStart = (orderId, operationId) => {
    const compat = compatibleLines(operationId)
    setStart({ order_id: orderId, operation_id: operationId })
    setForm({ line_id: compat[0]?.id || '', operator_count: 1 })
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center gap-2">
        <h1 className="text-xl font-semibold">{t('nav.shopFloor')}</h1>
        <button type="button" className="px-3 py-2 border rounded-lg text-sm min-h-11" onClick={load}>{t('common.refresh')}</button>
      </div>

      <section className="space-y-2">
        <h2 className="font-medium">{t('shopFloor.live')}</h2>
        {live.length === 0 ? <p className="text-slate-400 text-sm">{t('common.empty')}</p> : live.map((i) => (
          <div key={i.id} className="bg-white border rounded-xl p-4 space-y-3">
            <div className="text-sm">#{i.id} · order {i.order_id} · {opMap[i.operation_id]?.code || i.operation_id} · line {i.line_id} · ops {i.operator_count} · <b>{i.status}</b></div>
            <div className="flex flex-wrap gap-2">
              {i.status === 'in_progress' && <button type="button" className="px-3 py-2 text-sm border rounded-lg min-h-11" onClick={async () => { await api.post(`/operation-instances/${i.id}/pause`); load() }}>{t('shopFloor.pause')}</button>}
              {i.status === 'paused' && <button type="button" className="px-3 py-2 text-sm border rounded-lg min-h-11" onClick={async () => { await api.post(`/operation-instances/${i.id}/resume`); load() }}>{t('shopFloor.resume')}</button>}
              <button type="button" className="px-3 py-2 text-sm border rounded-lg min-h-11" onClick={() => { setOpsModal(i); setOpCount(i.operator_count) }}>{t('shopFloor.operators')}</button>
              <button type="button" className="px-3 py-2 text-sm border rounded-lg min-h-11" onClick={() => { setDowntime(i); setReasonId(reasons[0]?.id || '') }}>{t('shopFloor.downtime')}</button>
              {(i.downtimes || []).filter((d) => !d.ended_at).map((d) => (
                <button key={d.id} type="button" className="px-3 py-2 text-sm bg-amber-100 text-amber-900 rounded-lg min-h-11" onClick={async () => {
                  await api.post(`/operation-instances/${i.id}/downtimes/${d.id}/resolve`); toast.success(t('common.saved')); load()
                }}>{t('shopFloor.resolveDowntime')} #{d.id}</button>
              ))}
              <button type="button" className="px-3 py-2 text-sm bg-emerald-700 text-white rounded-lg min-h-11" onClick={() => { setComplete(i); setQty({ quantity_produced: 0, lot_code: '' }) }}>{t('shopFloor.complete')}</button>
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
                <button key={oid} type="button" className="px-3 py-2 text-sm bg-slate-900 text-white rounded-lg min-h-11" onClick={() => openStart(row.order.id, oid)}>
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
              toast.success(t('common.saved')); setStart(null); load()
            } catch (err) { toast.error(err.response?.data?.detail || t('common.error')) }
          }}>
            <Field label={t('fields.line')}>
              <select className={inputCls} required value={form.line_id} onChange={(e) => setForm({ ...form, line_id: e.target.value })}>
                {compatibleLines(start.operation_id).map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
              </select>
            </Field>
            {compatibleLines(start.operation_id).length === 0 && (
              <p className="text-sm text-red-600 mb-3">{t('shopFloor.noCompatibleLines')}</p>
            )}
            <Field label={t('fields.operators')}><input className={inputCls} type="number" min={1} value={form.operator_count} onChange={(e) => setForm({ ...form, operator_count: e.target.value })} /></Field>
            <button className="w-full bg-emerald-700 text-white rounded-lg py-3 min-h-12" disabled={!form.line_id}>{t('shopFloor.start')}</button>
          </form>
        </Modal>
      )}

      {complete && (
        <Modal title={t('shopFloor.complete')} onClose={() => setComplete(null)}>
          <form onSubmit={async (e) => {
            e.preventDefault()
            try {
              await api.post(`/operation-instances/${complete.id}/complete`, { quantity_produced: Number(qty.quantity_produced), lot_code: qty.lot_code || null })
              toast.success(t('common.saved')); setComplete(null); load()
            } catch (err) { toast.error(err.response?.data?.detail || t('common.error')) }
          }}>
            <Field label="quantity_produced"><input className={inputCls} type="number" min={0} value={qty.quantity_produced} onChange={(e) => setQty({ ...qty, quantity_produced: e.target.value })} /></Field>
            <Field label="lot_code"><input className={inputCls} value={qty.lot_code} onChange={(e) => setQty({ ...qty, lot_code: e.target.value })} /></Field>
            <button className="w-full bg-emerald-700 text-white rounded-lg py-3 min-h-12">{t('shopFloor.complete')}</button>
          </form>
        </Modal>
      )}

      {downtime && (
        <Modal title={t('shopFloor.downtime')} onClose={() => setDowntime(null)}>
          <form onSubmit={async (e) => {
            e.preventDefault()
            try {
              await api.post(`/operation-instances/${downtime.id}/downtimes`, { reason_id: Number(reasonId) })
              toast.success(t('common.saved')); setDowntime(null); load()
            } catch (err) { toast.error(err.response?.data?.detail || t('common.error')) }
          }}>
            <Field label={t('fields.reason')}>
              <select className={inputCls} value={reasonId} onChange={(e) => setReasonId(e.target.value)}>
                {reasons.map((r) => <option key={r.id} value={r.id}>{r.label}</option>)}
              </select>
            </Field>
            <button className="w-full bg-amber-600 text-white rounded-lg py-3 min-h-12">{t('common.save')}</button>
          </form>
        </Modal>
      )}

      {opsModal && (
        <Modal title={t('shopFloor.operators')} onClose={() => setOpsModal(null)}>
          <form onSubmit={async (e) => {
            e.preventDefault()
            try {
              await api.patch(`/operation-instances/${opsModal.id}/operators`, { operator_count: Number(opCount) })
              toast.success(t('common.saved')); setOpsModal(null); load()
            } catch (err) { toast.error(err.response?.data?.detail || t('common.error')) }
          }}>
            <Field label={t('fields.operators')}><input className={inputCls} type="number" min={1} value={opCount} onChange={(e) => setOpCount(e.target.value)} /></Field>
            <button className="w-full bg-slate-900 text-white rounded-lg py-3 min-h-12">{t('common.save')}</button>
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
  const [fieldDefs, setFieldDefs] = useState([])
  const [backupDir, setBackupDir] = useState('')
  const [backupEnabled, setBackupEnabled] = useState(false)
  const [companyName, setCompanyName] = useState('')
  const [userForm, setUserForm] = useState({ username: '', password: '', role: 'operator' })
  const [keyForm, setKeyForm] = useState({ name: '', role: 'backoffice' })
  const [newKey, setNewKey] = useState('')
  const [fdForm, setFdForm] = useState({
    entity: 'customer',
    label: '',
    key: '',
    field_type: 'string',
    required: false,
    options: '',
    sort_order: 0,
  })

  const load = async () => {
    const [s, u, k, fd] = await Promise.all([
      api.get('/settings'),
      api.get('/users'),
      api.get('/api-keys'),
      api.get('/field-definitions', { params: { include_inactive: true } }),
    ])
    setSettings(asList(s.data))
    setUsers(asList(u.data))
    setKeys(asList(k.data))
    setFieldDefs(asList(fd.data))
    const map = Object.fromEntries(asList(s.data).map((x) => [x.key, x.value]))
    setBackupDir(map.backup_dir || '')
    setBackupEnabled(map.backup_enabled === 'true')
    setCompanyName(map.company_name || '')
  }
  useEffect(() => { load().catch(() => toast.error(t('settings.superadminOnly'))) }, [t])

  const saveSetting = async (key, value) => {
    await api.put(`/settings/${key}`, { value })
  }

  const upload = async (path, file) => {
    const fd = new FormData()
    fd.append('file', file)
    const r = await api.post(path, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    toast.success(`${t('common.saved')} · ${JSON.stringify(r.data)}`)
  }

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-semibold">{t('nav.settings')}</h1>

      <section className="bg-white border rounded-xl p-4 space-y-3">
        <h2 className="font-medium">{t('settings.company')}</h2>
        <Field label={t('settings.companyName')}><input className={inputCls} value={companyName} onChange={(e) => setCompanyName(e.target.value)} /></Field>
        <button type="button" className="px-3 py-2 bg-slate-900 text-white rounded-lg text-sm min-h-11" onClick={async () => {
          await saveSetting('company_name', companyName); toast.success(t('common.saved')); load()
        }}>{t('common.save')}</button>
      </section>

      <section className="bg-white border rounded-xl p-4 space-y-3">
        <h2 className="font-medium">{t('settings.customFields')}</h2>
        <p className="text-sm text-slate-500">{t('settings.customFieldsHint')}</p>
        <div className="overflow-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-left">
              <tr>
                <th className="px-2 py-2">{t('settings.entity')}</th>
                <th className="px-2 py-2">key</th>
                <th className="px-2 py-2">{t('fields.name')}</th>
                <th className="px-2 py-2">type</th>
                <th className="px-2 py-2">{t('fields.active')}</th>
                <th className="px-2 py-2" />
              </tr>
            </thead>
            <tbody>
              {fieldDefs.map((d) => (
                <tr key={d.id} className="border-t">
                  <td className="px-2 py-2">{d.entity}</td>
                  <td className="px-2 py-2 font-mono text-xs">{d.key}</td>
                  <td className="px-2 py-2">{d.label}</td>
                  <td className="px-2 py-2">{d.field_type}{d.required ? ' *' : ''}</td>
                  <td className="px-2 py-2">{d.active ? 'yes' : 'off'}</td>
                  <td className="px-2 py-2 text-right space-x-2 whitespace-nowrap">
                    {d.field_type === 'select' && (
                      <button
                        type="button"
                        className="text-blue-700 text-xs"
                        onClick={async () => {
                          const next = window.prompt(t('settings.addOption'), '')
                          if (!next?.trim()) return
                          try {
                            await api.patch(`/field-definitions/${d.id}`, { options: [...(d.options || []), next.trim()] })
                            toast.success(t('common.saved')); load()
                          } catch (err) { toast.error(err.response?.data?.detail || t('common.error')) }
                        }}
                      >+ option</button>
                    )}
                    <button
                      type="button"
                      className="text-sm"
                      onClick={async () => {
                        try {
                          await api.patch(`/field-definitions/${d.id}`, { active: !d.active })
                          toast.success(t('common.saved')); load()
                        } catch (err) { toast.error(err.response?.data?.detail || t('common.error')) }
                      }}
                    >{d.active ? t('settings.deactivate') : t('settings.reactivate')}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <form
          className="grid sm:grid-cols-2 gap-2 border-t pt-3"
          onSubmit={async (e) => {
            e.preventDefault()
            const payload = {
              entity: fdForm.entity,
              label: fdForm.label,
              field_type: fdForm.field_type,
              required: fdForm.required,
              sort_order: Number(fdForm.sort_order) || 0,
            }
            if (fdForm.key.trim()) payload.key = fdForm.key.trim()
            if (fdForm.field_type === 'select') {
              payload.options = fdForm.options.split(',').map((x) => x.trim()).filter(Boolean)
            }
            try {
              await api.post('/field-definitions', payload)
              toast.success(t('common.saved'))
              setFdForm({ entity: fdForm.entity, label: '', key: '', field_type: 'string', required: false, options: '', sort_order: 0 })
              load()
            } catch (err) { toast.error(err.response?.data?.detail || t('common.error')) }
          }}
        >
          <Field label={t('settings.entity')}>
            <select className={inputCls} value={fdForm.entity} onChange={(e) => setFdForm({ ...fdForm, entity: e.target.value })}>
              {['customer', 'product', 'work_order', 'work_order_line', 'production_order', 'operation_instance'].map((e) => (
                <option key={e} value={e}>{e}</option>
              ))}
            </select>
          </Field>
          <Field label={t('fields.name')}>
            <input className={inputCls} required value={fdForm.label} onChange={(e) => setFdForm({ ...fdForm, label: e.target.value })} />
          </Field>
          <Field label="key (optional)">
            <input className={inputCls} placeholder="auto from label" value={fdForm.key} onChange={(e) => setFdForm({ ...fdForm, key: e.target.value })} />
          </Field>
          <Field label="type">
            <select className={inputCls} value={fdForm.field_type} onChange={(e) => setFdForm({ ...fdForm, field_type: e.target.value })}>
              {['string', 'number', 'boolean', 'date', 'select'].map((x) => <option key={x} value={x}>{x}</option>)}
            </select>
          </Field>
          {fdForm.field_type === 'select' && (
            <Field label={t('settings.selectOptions')}>
              <input className={inputCls} placeholder="A, B, C" value={fdForm.options} onChange={(e) => setFdForm({ ...fdForm, options: e.target.value })} />
            </Field>
          )}
          <label className="flex items-center gap-2 text-sm self-end mb-3">
            <input type="checkbox" className="w-5 h-5" checked={fdForm.required} onChange={(e) => setFdForm({ ...fdForm, required: e.target.checked })} />
            {t('settings.required')}
          </label>
          <button className="sm:col-span-2 bg-slate-900 text-white rounded-lg py-3 min-h-12">{t('settings.addField')}</button>
        </form>
      </section>

      <section className="bg-white border rounded-xl p-4 space-y-3">
        <h2 className="font-medium">{t('settings.backup')}</h2>
        <Field label="backup_dir"><input className={inputCls} value={backupDir} onChange={(e) => setBackupDir(e.target.value)} placeholder="C:\\Backup\\LocalMES" /></Field>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" className="w-5 h-5" checked={backupEnabled} onChange={(e) => setBackupEnabled(e.target.checked)} /> backup_enabled</label>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="px-3 py-2 bg-slate-900 text-white rounded-lg text-sm min-h-11" onClick={async () => {
            await saveSetting('backup_dir', backupDir)
            await saveSetting('backup_enabled', backupEnabled ? 'true' : 'false')
            toast.success(t('common.saved')); load()
          }}>{t('common.save')}</button>
          <button type="button" className="px-3 py-2 border rounded-lg text-sm min-h-11" onClick={async () => {
            try { const r = await api.post('/settings/backup/run'); toast.success(r.data.path || 'OK') } catch (e) { toast.error(e.response?.data?.detail || t('common.error')) }
          }}>{t('settings.runBackup')}</button>
        </div>
      </section>

      <section className="bg-white border rounded-xl p-4 space-y-3">
        <h2 className="font-medium">{t('settings.imports')}</h2>
        {[['customers', '/imports/customers'], ['products', '/imports/products'], ['boms', '/imports/boms'], ['production-orders', '/imports/production-orders']].map(([label, path]) => (
          <Field key={path} label={label}>
            <input type="file" accept=".csv,.xlsx,.xlsm" className="text-sm" onChange={(e) => e.target.files?.[0] && upload(path, e.target.files[0]).catch((err) => toast.error(err.response?.data?.detail || t('common.error')))} />
          </Field>
        ))}
      </section>

      <section className="bg-white border rounded-xl p-4 space-y-3">
        <h2 className="font-medium">{t('settings.reports')}</h2>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="px-3 py-2 border rounded-lg text-sm min-h-11" onClick={() => downloadFile('/reports/export-excel', 'localmes_report.xlsx').catch(() => toast.error(t('common.error')))}>Excel</button>
          <button type="button" className="px-3 py-2 border rounded-lg text-sm min-h-11" onClick={() => downloadFile('/reports/export-pdf', 'localmes_report.pdf').catch(() => toast.error(t('common.error')))}>PDF</button>
        </div>
      </section>

      <section className="bg-white border rounded-xl p-4 space-y-3">
        <h2 className="font-medium">{t('settings.users')}</h2>
        <ul className="text-sm divide-y">{users.map((u) => <li key={u.id} className="py-2">{u.username} · {u.role} · {u.active ? 'active' : 'off'}</li>)}</ul>
        <form className="grid sm:grid-cols-4 gap-2" onSubmit={async (e) => {
          e.preventDefault()
          try { await api.post('/users', userForm); toast.success(t('common.saved')); setUserForm({ username: '', password: '', role: 'operator' }); load() } catch (err) { toast.error(err.response?.data?.detail || t('common.error')) }
        }}>
          <input className={inputCls} placeholder="username" required value={userForm.username} onChange={(e) => setUserForm({ ...userForm, username: e.target.value })} />
          <input className={inputCls} placeholder="password" type="password" required value={userForm.password} onChange={(e) => setUserForm({ ...userForm, password: e.target.value })} />
          <select className={inputCls} value={userForm.role} onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}>
            <option value="operator">operator</option><option value="backoffice">backoffice</option><option value="superadmin">superadmin</option>
          </select>
          <button className="bg-slate-900 text-white rounded-lg text-sm min-h-11">{t('common.create')}</button>
        </form>
      </section>

      <section className="bg-white border rounded-xl p-4 space-y-3">
        <h2 className="font-medium">API keys</h2>
        <ul className="text-sm divide-y">{keys.map((k) => <li key={k.id} className="py-2">{k.name} · {k.role} · {k.active ? 'active' : 'off'}</li>)}</ul>
        {newKey && <p className="text-xs bg-amber-50 border border-amber-200 rounded p-2 break-all">Copy now: {newKey}</p>}
        <form className="grid sm:grid-cols-3 gap-2" onSubmit={async (e) => {
          e.preventDefault()
          try {
            const r = await api.post('/api-keys', keyForm)
            setNewKey(r.data.key)
            toast.success(t('common.saved')); load()
          } catch (err) { toast.error(err.response?.data?.detail || t('common.error')) }
        }}>
          <input className={inputCls} placeholder="name" required value={keyForm.name} onChange={(e) => setKeyForm({ ...keyForm, name: e.target.value })} />
          <select className={inputCls} value={keyForm.role} onChange={(e) => setKeyForm({ ...keyForm, role: e.target.value })}>
            <option value="backoffice">backoffice</option><option value="operator">operator</option><option value="superadmin">superadmin</option>
          </select>
          <button className="bg-slate-900 text-white rounded-lg text-sm min-h-11">{t('common.create')}</button>
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
    <div className="min-h-screen bg-slate-950 text-white p-6 sm:p-8">
      <h1 className="text-2xl sm:text-3xl font-semibold mb-6">LocalMES Signage</h1>
      {!data ? <p>Loading…</p> : (
        <div className="grid sm:grid-cols-2 gap-4">
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
