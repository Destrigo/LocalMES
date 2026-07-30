import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import api from '../utils/api'

export function asList(data) {
  if (Array.isArray(data)) return data
  if (data?.items) return data.items
  return []
}

export function Modal({ title, onClose, children, wide }) {
  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
      <div className={`bg-white rounded-t-2xl sm:rounded-xl shadow-xl w-full ${wide ? 'max-w-2xl' : 'max-w-lg'} max-h-[92vh] overflow-auto`}>
        <div className="sticky top-0 bg-white flex justify-between items-center border-b px-4 py-3">
          <h3 className="font-semibold text-slate-800 text-base sm:text-lg">{title}</h3>
          <button type="button" onClick={onClose} className="text-slate-400 hover:text-slate-700 text-2xl leading-none px-2">×</button>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  )
}

export function Field({ label, children }) {
  return (
    <label className="block text-sm mb-3">
      <span className="text-slate-600 font-medium">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  )
}

export const inputCls = 'w-full border border-slate-300 rounded-lg px-3 py-2.5 text-base sm:text-sm min-h-11'

/** Load active field definitions for an entity. */
export function useFieldDefinitions(entity) {
  const [defs, setDefs] = useState([])
  useEffect(() => {
    if (!entity) {
      setDefs([])
      return
    }
    api.get('/field-definitions', { params: { entity } })
      .then((r) => setDefs(asList(r.data)))
      .catch(() => setDefs([]))
  }, [entity])
  return defs
}

/** Render + edit custom_fields object driven by definitions. */
export function CustomFieldsEditor({ defs, values, onChange }) {
  if (!defs?.length) return null
  const setKey = (key, val) => onChange({ ...(values || {}), [key]: val })
  return (
    <div className="border-t pt-3 mt-2 space-y-1">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-2">Custom fields</p>
      {defs.map((d) => {
        const v = values?.[d.key]
        const label = `${d.label}${d.required ? ' *' : ''}`
        if (d.field_type === 'boolean') {
          return (
            <Field key={d.key} label={label}>
              <input
                type="checkbox"
                className="w-5 h-5"
                checked={!!v}
                onChange={(e) => setKey(d.key, e.target.checked)}
              />
            </Field>
          )
        }
        if (d.field_type === 'select') {
          return (
            <Field key={d.key} label={label}>
              <select
                className={inputCls}
                required={!!d.required}
                value={v ?? ''}
                onChange={(e) => setKey(d.key, e.target.value)}
              >
                <option value="">…</option>
                {(d.options || []).map((o) => (
                  <option key={o} value={o}>{o}</option>
                ))}
              </select>
            </Field>
          )
        }
        const type = d.field_type === 'number' ? 'number' : d.field_type === 'date' ? 'date' : 'text'
        return (
          <Field key={d.key} label={label}>
            <input
              className={inputCls}
              type={type}
              required={!!d.required}
              value={v ?? ''}
              onChange={(e) => setKey(d.key, type === 'number' ? (e.target.value === '' ? '' : Number(e.target.value)) : e.target.value)}
            />
          </Field>
        )
      })}
    </div>
  )
}

function prepareBody(form, fields, endpoint) {
  const body = { ...form }
  for (const f of fields) {
    if (f.type === 'number') {
      if (body[f.key] === '' || body[f.key] == null) {
        if (!f.required) delete body[f.key]
      } else body[f.key] = Number(body[f.key])
    }
    if (f.type === 'checkbox') body[f.key] = !!body[f.key]
  }
  if (body.compatible_line_ids == null) body.compatible_line_ids = []
  if (endpoint === '/cycles' && body.steps == null) body.steps = []
  if (body.custom_fields && typeof body.custom_fields === 'object') {
    const cleaned = { ...body.custom_fields }
    for (const [k, v] of Object.entries(cleaned)) {
      if (v === '') delete cleaned[k]
    }
    body.custom_fields = cleaned
  }
  return body
}

/** Generic list with search, create, edit, delete — tablet-friendly. */
export function CrudList({ title, endpoint, columns, fields, createDefaults = {}, searchParam = 'q', customEntity }) {
  const { t } = useTranslation()
  const defs = useFieldDefinitions(customEntity)
  const [rows, setRows] = useState([])
  const [total, setTotal] = useState(0)
  const [q, setQ] = useState('')
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState({ ...createDefaults, custom_fields: {} })
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    const params = { limit: 200, offset: 0 }
    if (q.trim()) params[searchParam] = q.trim()
    api.get(endpoint, { params })
      .then((r) => {
        const list = asList(r.data)
        setRows(list)
        setTotal(r.data?.total ?? list.length)
      })
      .catch(() => toast.error(t('common.loadFailed')))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [endpoint])

  const openCreate = () => {
    setEditing(null)
    setForm({ ...createDefaults, custom_fields: {} })
    setOpen(true)
  }

  const openEdit = (row) => {
    setEditing(row)
    const next = { ...createDefaults, custom_fields: { ...(row.custom_fields || {}) } }
    for (const f of fields) next[f.key] = row[f.key] ?? createDefaults[f.key] ?? ''
    if (row.compatible_line_ids) next.compatible_line_ids = row.compatible_line_ids
    setForm(next)
    setOpen(true)
  }

  const submit = async (e) => {
    e.preventDefault()
    try {
      const body = prepareBody(form, fields, endpoint)
      if (!customEntity) delete body.custom_fields
      if (editing) await api.patch(`${endpoint}/${editing.id}`, body)
      else await api.post(endpoint, body)
      toast.success(t('common.saved'))
      setOpen(false)
      load()
    } catch (err) {
      toast.error(err.response?.data?.detail || t('common.error'))
    }
  }

  const remove = async (id) => {
    if (!confirm(t('common.confirmDelete'))) return
    try {
      await api.delete(`${endpoint}/${id}`)
      toast.success(t('common.deleted'))
      load()
    } catch (err) {
      toast.error(err.response?.data?.detail || t('common.error'))
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <h1 className="text-xl font-semibold">{title}</h1>
        <div className="flex flex-wrap gap-2">
          <input
            className={`${inputCls} sm:w-48`}
            placeholder={t('common.search')}
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && load()}
          />
          <button type="button" onClick={load} className="px-3 py-2 text-sm rounded-lg border min-h-11">{t('common.refresh')}</button>
          <button type="button" onClick={openCreate} className="px-3 py-2 text-sm rounded-lg bg-slate-900 text-white min-h-11">{t('common.create')}</button>
        </div>
      </div>
      <p className="text-xs text-slate-400">{total} {t('common.results')}</p>
      {loading ? <p className="text-slate-400">{t('common.loading')}</p> : rows.length === 0 ? <p className="text-slate-400">{t('common.empty')}</p> : (
        <div className="overflow-auto bg-white rounded-xl border -mx-1">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-left sticky top-0">
              <tr>
                {columns.map((c) => <th key={c.key} className="px-3 py-3 font-medium text-slate-600 whitespace-nowrap">{c.label}</th>)}
                <th className="px-3 py-3" />
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-t">
                  {columns.map((c) => <td key={c.key} className="px-3 py-3">{String(row[c.key] ?? '')}</td>)}
                  <td className="px-3 py-3 text-right whitespace-nowrap space-x-2">
                    <button type="button" className="text-blue-700 text-sm font-medium" onClick={() => openEdit(row)}>{t('common.edit')}</button>
                    <button type="button" className="text-red-600 text-sm" onClick={() => remove(row.id)}>{t('common.delete')}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {open && (
        <Modal title={editing ? t('common.edit') : t('common.create')} onClose={() => setOpen(false)}>
          <form onSubmit={submit} className="space-y-1">
            {fields.map((f) => (
              <Field key={f.key} label={f.label}>
                {f.type === 'checkbox' ? (
                  <input type="checkbox" className="w-5 h-5" checked={!!form[f.key]} onChange={(e) => setForm({ ...form, [f.key]: e.target.checked })} />
                ) : f.type === 'select' ? (
                  <select className={inputCls} required={!!f.required} value={form[f.key] ?? ''} onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}>
                    <option value="">…</option>
                    {(f.options || []).map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                ) : (
                  <input className={inputCls} type={f.type || 'text'} required={!!f.required} value={form[f.key] ?? ''} onChange={(e) => setForm({ ...form, [f.key]: e.target.value })} />
                )}
              </Field>
            ))}
            {customEntity && (
              <CustomFieldsEditor
                defs={defs}
                values={form.custom_fields || {}}
                onChange={(custom_fields) => setForm({ ...form, custom_fields })}
              />
            )}
            <button type="submit" className="w-full bg-slate-900 text-white rounded-lg py-3 font-medium min-h-12">{t('common.save')}</button>
          </form>
        </Modal>
      )}
    </div>
  )
}
