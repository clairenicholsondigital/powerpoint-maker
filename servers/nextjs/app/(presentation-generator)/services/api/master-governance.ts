import { ApiResponseHandler } from './api-error-handler'
import { getHeaderForFormData } from './header'

export type MasterGovernanceInspectResponse = {
  success: boolean
  milestone: string
  round_trip_dependency: string
  state: {
    themes: { path: string; name: string }[]
    slide_masters: { path: string; name: string }[]
    slide_layouts: { path: string; name: string }[]
    font_schemes: Record<string, { name?: string; major_latin?: string; minor_latin?: string }>
    color_schemes: Record<string, { name?: string; colors: { key: string; value: string }[] }>
    placeholder_defaults: any[]
    master_objects: any[]
  }
}

class MasterGovernanceApi {
  static async inspect(pptxFile: File): Promise<MasterGovernanceInspectResponse> {
    const formData = new FormData()
    formData.append('pptx_file', pptxFile)

    const response = await fetch('/api/v1/ppt/pptx-masters/inspect', {
      method: 'POST',
      headers: getHeaderForFormData(),
      body: formData,
      cache: 'no-store',
    })

    return ApiResponseHandler.handleResponse(response, 'Failed to inspect master-level parts')
  }

  static async apply(pptxFile: File, patch: unknown): Promise<Blob> {
    const formData = new FormData()
    formData.append('pptx_file', pptxFile)
    formData.append('patch', JSON.stringify(patch))

    const response = await fetch('/api/v1/ppt/pptx-masters/apply', {
      method: 'POST',
      headers: getHeaderForFormData(),
      body: formData,
      cache: 'no-store',
    })

    if (!response.ok) {
      await ApiResponseHandler.handleResponse(response, 'Failed to apply master governance patch')
    }

    return response.blob()
  }
}

export default MasterGovernanceApi
