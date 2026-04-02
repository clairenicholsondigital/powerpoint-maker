'use client'

import { useMemo, useState } from 'react'
import { toast } from 'sonner'

import MasterGovernanceApi, { MasterGovernanceInspectResponse } from '@/app/(presentation-generator)/services/api/master-governance'

export default function MasterGovernancePanel() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<MasterGovernanceInspectResponse | null>(null)
  const [majorLatin, setMajorLatin] = useState('')
  const [minorLatin, setMinorLatin] = useState('')
  const [accent1, setAccent1] = useState('')

  const firstThemePath = useMemo(() => data?.state?.themes?.[0]?.path ?? '', [data])

  const inspect = async () => {
    if (!file) {
      toast.error('Upload a PPTX first')
      return
    }
    setLoading(true)
    try {
      const result = await MasterGovernanceApi.inspect(file)
      setData(result)

      const currentTheme = result.state.themes?.[0]?.path
      if (currentTheme) {
        setMajorLatin(result.state.font_schemes[currentTheme]?.major_latin ?? '')
        setMinorLatin(result.state.font_schemes[currentTheme]?.minor_latin ?? '')
        const accent = result.state.color_schemes[currentTheme]?.colors.find((c) => c.key === 'accent1')?.value
        setAccent1(accent ?? '')
      }
      toast.success('Master governance model loaded')
    } catch (error: any) {
      toast.error(error?.message || 'Failed to inspect PPTX')
    } finally {
      setLoading(false)
    }
  }

  const apply = async () => {
    if (!file || !firstThemePath) {
      toast.error('Inspect a PPTX first')
      return
    }
    setLoading(true)
    try {
      const patch = {
        font_schemes: [
          {
            theme_path: firstThemePath,
            major_latin: majorLatin,
            minor_latin: minorLatin,
          },
        ],
        color_schemes: [
          {
            theme_path: firstThemePath,
            colors: accent1 ? { accent1: accent1.replace('#', '').toUpperCase() } : {},
          },
        ],
        placeholder_defaults: [],
        master_objects: [],
      }
      const blob = await MasterGovernanceApi.apply(file, patch)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `master-governance-${file.name}`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('Updated PPTX downloaded')
    } catch (error: any) {
      toast.error(error?.message || 'Failed to apply patch')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Master & Template Governance</h1>
        <p className="text-sm text-slate-600 mt-2">Separate milestone surface for editing slide masters, layouts, and theme schemas.</p>
      </div>

      <div className="bg-white border rounded-lg p-4 space-y-4 max-w-3xl">
        <input type="file" accept=".pptx,application/vnd.openxmlformats-officedocument.presentationml.presentation" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />

        <div className="flex gap-3">
          <button onClick={inspect} disabled={loading} className="px-4 py-2 rounded bg-indigo-600 text-white text-sm disabled:opacity-50">Inspect master parts</button>
          <button onClick={apply} disabled={loading || !data} className="px-4 py-2 rounded border text-sm disabled:opacity-50">Apply governance patch</button>
        </div>

        {data && (
          <div className="space-y-4 text-sm">
            <p className="text-slate-700"><b>Dependency:</b> {data.round_trip_dependency}</p>
            <p className="text-slate-700"><b>Themes:</b> {data.state.themes.length} | <b>Masters:</b> {data.state.slide_masters.length} | <b>Layouts:</b> {data.state.slide_layouts.length}</p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <label className="space-y-1">
                <span className="text-slate-600">Major latin font</span>
                <input value={majorLatin} onChange={(e) => setMajorLatin(e.target.value)} className="w-full border rounded px-2 py-1" />
              </label>
              <label className="space-y-1">
                <span className="text-slate-600">Minor latin font</span>
                <input value={minorLatin} onChange={(e) => setMinorLatin(e.target.value)} className="w-full border rounded px-2 py-1" />
              </label>
              <label className="space-y-1">
                <span className="text-slate-600">Accent1 color (hex)</span>
                <input value={accent1} onChange={(e) => setAccent1(e.target.value)} className="w-full border rounded px-2 py-1" />
              </label>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
